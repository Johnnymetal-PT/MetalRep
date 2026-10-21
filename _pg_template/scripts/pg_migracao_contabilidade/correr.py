#!/usr/bin/env python3
"""Corre a migração completa, pela ordem do método, numa base de ensaio ou em produção.

Motor genérico do método TPL_MIGRACAO_CONTABILIDADE_MEIO_ANO (doc_templates). Encadeia os passos
do motor.py, espera pela importação da Exo, e pára ao primeiro erro ou se a verificação falhar
(saldos, parceiros, IVA, fichas duplicadas, fichas da contabilidade e retenções). É a mesma
sequência no ensaio final e no dia da passagem, para em produção só correr o que foi ensaiado.

    preparar (comandos do projeto, ex.: tabelas de grelhas e do plano) -> importar -> ignorar ->
    gravar -> fundir_parceiros -> parceiros_em_falta -> parceiros -> faltas -> grelhas ->
    config_extra -> impostos -> recodificar -> juntar -> reclassificar -> abertura -> limpar ->
    extratos -> taxonomia -> config_fiscal -> VERIFICAR -> natureza -> bloqueio (véspera da
    abertura) -> lancar -> VERIFICAR -> bloqueio (data de corte) -> resumo_grelhas

Os módulos da Exo, o utilizador da contabilidade, o código da Exo e as séries ficam fora: são
passos do dia da passagem (ver o template), depois desta sequência.

Uso (a partir da raiz do repositório do projeto):
    python .pg_framework\\scripts\\pg_migracao_contabilidade\\correr.py <config.json> <ligação>
    python .pg_framework\\scripts\\pg_migracao_contabilidade\\correr.py <config.json> producao --producao
    --desde <passo>   retoma a partir de um passo (ex.: depois de uma falha de rede)
"""
import argparse
import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
MOTOR = os.path.join(AQUI, 'motor.py')
VERIFICAR = os.path.join(AQUI, 'verificar.py')

ap = argparse.ArgumentParser()
ap.add_argument('config')
ap.add_argument('conn', help='ficheiro de ligação da base de ensaio, ou "producao"')
ap.add_argument('--producao', action='store_true', help='escreve em produção (passa --allow-prod a cada passo)')
ap.add_argument('--desde', default=None, help='retoma a partir deste passo')
args = ap.parse_args()
if (args.conn == 'producao') != args.producao:
    sys.exit('Em produção usar a ligação "producao" e --producao; num ensaio, nenhum dos dois.')
CFG = json.load(open(args.config, encoding='utf-8'))
ESPERADO = CFG.get('esperado', {})
AMBIENTE = dict(os.environ, PYTHONIOENCODING='utf-8')

SEQUENCIA = (['preparar', 'importar', 'ignorar', 'gravar', 'fundir_parceiros', 'parceiros_em_falta', 'parceiros', 'faltas',
              'grelhas', 'config_extra', 'impostos', 'recodificar', 'juntar', 'reclassificar', 'abertura', 'limpar',
              'extratos', 'taxonomia', 'config_fiscal', 'VERIFICAR antes de lançar', 'natureza', 'bloqueio vespera',
              'lancar', 'VERIFICAR depois de lançar', 'bloqueio corte', 'resumo_grelhas'])
if args.desde and args.desde not in SEQUENCIA:
    sys.exit(f'--desde: passo desconhecido. Passos: {SEQUENCIA}')


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=AMBIENTE)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def passo(nome, *extra):
    print(f'===== {nome} {" ".join(extra)} ({time.strftime("%H:%M:%S")})', flush=True)
    cmd = [sys.executable, MOTOR, args.config, args.conn, nome, *extra, '--confirm']
    if args.producao:
        cmd.append('--allow-prod')
    rc, saida = correr(cmd)
    print('\n'.join(saida.rstrip().splitlines()[-12:]), flush=True)
    if rc != 0 or 'Traceback' in saida or 'Fault' in saida:
        sys.exit(f'FALHOU em: {nome} (retomar com --desde {nome}, depois de ver a causa)')


def esperar():
    for _ in range(80):
        rc, saida = correr([sys.executable, MOTOR, args.config, args.conn, 'estado'])
        linha = saida.strip().splitlines()[0] if saida.strip() else ''
        print(f'  {time.strftime("%H:%M:%S")} {linha}', flush=True)
        if 'a correr False' in linha:
            return
        time.sleep(30)
    sys.exit('FALHOU: a importação não terminou')


def verificar(fase):
    print(f'== verificação {fase}', flush=True)
    rc, saida = correr([sys.executable, VERIFICAR, args.config, args.conn])
    chaves = ('linhas até', 'sem parceiro', 'natureza', 'grelha', 'parceiro diferente', 'IVA sem correspond',
              'mais de uma ficha', 'lista da contabilidade', 'Modelo 10 com parceiro', 'comparadas', 'RESULTADO')
    print('\n'.join(l for l in saida.splitlines() if any(c in l for c in chaves)), flush=True)
    exigir = [('RESULTADO: BATE CERTO', 'saldos, linhas de IVA ou equilíbrio automático'),
              ('subconta no SAF-T (tem de ser 0): 0', 'parceiros diferentes do SAF-T'),
              ('mais de uma ficha de parceiro (tem de ser 0): 0', 'fichas duplicadas')]
    if 'lista da contabilidade' in saida:
        exigir.append(('lista da contabilidade com mais de uma ficha ou saldo diferente (tem de ser 0): 0', 'fichas da contabilidade'))
    if 'retencoes_modelo10' in ESPERADO:
        exigir.append((f"retenções da Modelo 10 com parceiro: {ESPERADO['retencoes_modelo10']} | "
                       'retenções que não levam NIF com parceiro (tem de ser 0): 0', 'retenções'))
    for texto, nome in exigir:
        if not any(l.rstrip().endswith(texto) or l.strip() == texto for l in saida.splitlines()):
            sys.exit(f'FALHOU: verificação {fase} ({nome})')


ativo = args.desde is None
for p in SEQUENCIA:
    ativo = ativo or p == args.desde
    if not ativo:
        continue
    if p == 'preparar':
        for cmd in CFG.get('preparar', []):
            print(f'===== preparar: {cmd}', flush=True)
            rc, saida = correr([sys.executable] + cmd.split('|'))
            print('\n'.join(saida.rstrip().splitlines()[-3:]), flush=True)
            if rc != 0:
                sys.exit(f'FALHOU a preparar: {cmd}')
    elif p in ('importar', 'gravar'):
        passo(p)
        esperar()
    elif p.startswith('VERIFICAR'):
        verificar(p.split(' ', 1)[1])
    elif p == 'bloqueio vespera':
        passo('bloqueio')
    elif p == 'bloqueio corte':
        passo('bloqueio', '--data', 'corte')
    else:
        passo(p)
print(f'CONCLUÍDO {time.strftime("%H:%M:%S")}')
