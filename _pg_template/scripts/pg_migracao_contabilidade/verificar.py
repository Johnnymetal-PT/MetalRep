#!/usr/bin/env python3
"""Verifica uma base de ensaio (ou produção) contra o SAF-T de contabilidade, em qualquer fase.

Motor genérico do método TPL_MIGRACAO_CONTABILIDADE_MEIO_ANO (doc_templates); a configuração é a
mesma do motor.py (ficheiro JSON do projeto). Só leitura.

Porque existe
    O SAF-T traz o saldo de fecho de cada conta à data de corte. Somados pela tabela de
    correspondência (folha Tabela do plano), dão o saldo que cada conta final tem de ter no Odoo.
    O saldo do Odoo é agregado pela mesma tabela, por isso a comparação serve logo a seguir à
    importação e depois de cada recodificação, junção ou reclassificação. Conta os lançamentos em
    rascunho e exclui tudo o que é posterior à data de corte.

    Além dos saldos, compara cada linha de terceiros com a entidade da subconta no SAF-T, cada
    linha de IVA com o SAF-T (apanha o IVA refeito pelo Odoo), conta as linhas de equilíbrio
    automático, os NIF com mais de uma ficha e, se houver, os saldos das fichas indicadas pela
    contabilidade. As linhas "tem de ser 0" são as que o correr.py exige.

Uso (a partir da raiz do repositório do projeto):
    python .pg_framework\\scripts\\pg_migracao_contabilidade\\verificar.py <config.json> <ligação | producao>
"""
import argparse
import collections
import json
import os
import sys

import openpyxl

sys.path.insert(0, os.path.join('.pg_framework', 'scripts'))
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('config', help='configuração do projeto (JSON)')
ap.add_argument('conn', help='ficheiro de ligação da base de ensaio, ou "producao" (só leitura)')
ap.add_argument('--log', default=None)
args = ap.parse_args()
CFG = json.load(open(args.config, encoding='utf-8'))
F = {k: os.path.join(CFG['pasta'], v) for k, v in CFG.get('ficheiros', {}).items()}
args.plano, args.ate, args.saft, args.empresa = F['plano'], CFG['data_corte'], CFG['saft'], CFG['empresa']
args.fichas = F.get('fichas_contabilidade', '')
PREFIXO_OUTROS = CFG.get('prefixo_outros_devedores_credores', '278')
RET = CFG.get('retencoes', {})
RET_PREFIXO, RET_MODELO10 = RET.get('prefixo', '242'), RET.get('contas_modelo10', [])
DIFER = CFG.get('contas_diferimentos_por_cliente', [])

wb = openpyxl.load_workbook(args.plano, read_only=True)
MAPA = {str(r[0]): str(r[2]) for r in wb['Tabela'].iter_rows(min_row=2, values_only=True) if r[0]}
ESPERADO = {str(r[0]): float(r[1]) for r in wb['Esperado'].iter_rows(min_row=2, values_only=True) if r[0]}

# "producao" liga pelo canal do projeto; só leitura, por isso não precisa de --allow-prod
g = Guard(resolver_alvo_por_projeto(CFG['project_key'], 'production') if args.conn == 'producao'
          else resolver_alvo(args.conn), log_path=args.log)
dom = [['company_id', '=', args.empresa], ['parent_state', 'in', ['draft', 'posted']], ['date', '<=', args.ate]]
grupos = g.kw('account.move.line', 'read_group', [dom, ['balance:sum'], ['account_id']], {'lazy': False})
contas = {a['id']: a['code'] for a in g.kw('account.account', 'search_read',
                                             [[['company_ids', 'in', [args.empresa]], ['active', 'in', [True, False]]]],
                                             {'fields': ['code']})}
real = collections.defaultdict(float)
for gr in grupos:
    cod = contas.get(gr['account_id'][0], '?')
    real[MAPA.get(cod, cod)] += gr['balance'] or 0.0

difs = []
for f in sorted(set(ESPERADO) | set(real)):
    e, r = round(ESPERADO.get(f, 0.0), 2), round(real.get(f, 0.0), 2)
    if abs(e - r) >= 0.01:
        difs.append((f, e, r, round(r - e, 2)))

total = g.kw('account.move.line', 'search_count', [dom])
terc = dom + [['account_id.account_type', 'in', ['asset_receivable', 'liability_payable']]]
sem_parc = g.kw('account.move.line', 'search_count', [terc + [['partner_id', '=', False]]])
print(f'linhas até {args.ate}: {total} | em contas de terceiros sem parceiro: {sem_parc} '
      f'de {g.kw("account.move.line", "search_count", [terc])}')
outros = dom + [['account_id.code', '=like', PREFIXO_OUTROS + '%']]
print(f'linhas {PREFIXO_OUTROS}x (outros devedores e credores) sem parceiro: {g.kw("account.move.line", "search_count", [outros + [["partner_id", "=", False]]])} '
      f'de {g.kw("account.move.line", "search_count", [outros])}')
ret = dom + [['account_id.code', '=like', RET_PREFIXO + '%']]
# Modelo 10: só as retenções a crédito das contas indicadas (trabalho independente, rendas) levam parceiro
M10 = RET_MODELO10 or ['-']
ret_ok = g.kw('account.move.line', 'search_count', [ret + [['account_id.code', 'in', M10], ['credit', '>', 0], ['partner_id', '!=', False]]])
ret_mal = g.kw('account.move.line', 'search_count', [ret + [['partner_id', '!=', False], '|', ['account_id.code', 'not in', M10], ['debit', '>', 0]]]) if RET_MODELO10 else 0
print(f'retenções da Modelo 10 com parceiro: {ret_ok} | retenções que não levam NIF com parceiro (tem de ser 0): {ret_mal}')
print(f'linhas {RET_PREFIXO}x (retenções, Modelo 10) sem parceiro: {g.kw("account.move.line", "search_count", [ret + [["partner_id", "=", False]]])} '
      f'de {g.kw("account.move.line", "search_count", [ret])}')
if DIFER:
    dif = dom + ['|'] * (len(DIFER) - 1) + [['account_id.code', '=like', p + '%'] for p in DIFER]
    print(f'linhas {"/".join(DIFER)} (diferimentos por cliente) sem parceiro: {g.kw("account.move.line", "search_count", [dif + [["partner_id", "=", False]]])} '
          f'de {g.kw("account.move.line", "search_count", [dif])}')
nat = g.kw('account.move.line', 'read_group', [dom + [['account_id.code', '=like', '5%']], ['move_id'], ['move_id', 'l10n_pt_equity_change']],
           {'lazy': False})
print('natureza do capital próprio por lançamento:',
      '; '.join(f"{n['move_id'][1]} = {n['l10n_pt_equity_change'] or 'vazia'}" for n in nat))
print(f'linhas com grelha de IVA (fora os diários de apuramento): '
      f'{g.kw("account.move.line", "search_count", [dom + [["tax_tag_ids", "!=", False]]])}')
# Parceiros: cada linha de terceiros comparada com a entidade da subconta no SAF-T (mesmo
# lançamento, valores e descrição). Apanha o parceiro do cabeçalho posto em todas as linhas dos
# lançamentos de bancos agregados. Tem de dar 0.
import re  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
ns = {'s': 'urn:OECD:StandardAuditFile-Tax:PT_1.04_01'}
raiz = ET.parse(args.saft).getroot()


def tx(e, k):
    x = e.find('s:' + k, ns)
    return x.text.strip() if x is not None and x.text else None


def nif_n(n):  # tira o prefixo do país, também quando o NIF começa por letra (ESB66854530)
    return re.sub(r'^[A-Z]{2}(?=[A-Z0-9]{8,}$)', '', (n or '').replace(' ', '').upper())


ent = {}
for tag in ('Customer', 'Supplier'):
    for e in raiz.findall(f'.//s:MasterFiles/s:{tag}', ns):
        ent[tx(e, 'AccountID')] = nif_n(tx(e, f'{tag}TaxID'))
saft_l = collections.defaultdict(list)
for tr in raiz.findall('.//s:GeneralLedgerEntries/s:Journal/s:Transaction', ns):
    for grp in tr.findall('s:Lines', ns):
        for l in grp:
            if tx(l, 'AccountID') in ent:
                saft_l[(tx(tr, 'TransactionID'), round(float(tx(l, 'DebitAmount') or 0), 2),
                        round(float(tx(l, 'CreditAmount') or 0), 2), (tx(l, 'Description') or '').strip())].append(ent[tx(l, 'AccountID')])
TL = g.kw('account.move.line', 'search_read', [terc + [['move_id.ref', '!=', False]]],
          {'fields': ['move_id', 'partner_id', 'debit', 'credit', 'name']})
refs = {m['id']: m['ref'] for m in g.kw('account.move', 'read', [list({l['move_id'][0] for l in TL}), ['ref']])} if TL else {}
vat = {p['id']: nif_n(p['vat']) for p in g.kw('res.partner', 'read', [list({l['partner_id'][0] for l in TL if l['partner_id']}), ['vat']])} if TL else {}
errado = []
for l in TL:
    c = saft_l.get((refs.get(l['move_id'][0]), round(l['debit'], 2), round(l['credit'], 2), (l['name'] or '').strip()))
    if c and len(set(c)) == 1 and l['partner_id'] and vat.get(l['partner_id'][0]) and vat[l['partner_id'][0]] != c[0]:
        errado.append((refs.get(l['move_id'][0]), l['name'], l['partner_id'][1], vat[l['partner_id'][0]], c[0]))
print(f'linhas de terceiros com parceiro diferente da entidade da subconta no SAF-T (tem de ser 0): {len(errado)}')
for ref, nome, parc, nif, nif_saft in errado[:20]:
    print(f'  {ref} | {nome} | no Odoo {parc} ({nif}) | no SAF-T NIF {nif_saft}')
# Linhas de IVA refeitas pelo Odoo: uma escrita sem skip_invoice_sync numa linha com impostos apaga a
# linha de IVA do SAF-T e cria outra com o nome do imposto, sem as grelhas da linha original, e às vezes
# uma "Automatic Balancing Line". O saldo só denuncia quando o valor
# recalculado difere, por isso cada linha 243x tem de existir no SAF-T (lançamento, valores, descrição).
saft_iva = collections.Counter()
for tr in raiz.findall('.//s:GeneralLedgerEntries/s:Journal/s:Transaction', ns):
    for grp in tr.findall('s:Lines', ns):
        for l in grp:
            if (tx(l, 'AccountID') or '').startswith('243'):
                saft_iva[(tx(tr, 'TransactionID'), round(float(tx(l, 'DebitAmount') or 0), 2),
                          round(float(tx(l, 'CreditAmount') or 0), 2), (tx(l, 'Description') or '').strip())] += 1
IL = g.kw('account.move.line', 'search_read', [dom + [['account_id.code', '=like', '243%'], ['move_id.ref', 'in', list({k[0] for k in saft_iva})]]],
          {'fields': ['move_id', 'debit', 'credit', 'name']})
refs_i = {m['id']: m['ref'] for m in g.kw('account.move', 'read', [list({l['move_id'][0] for l in IL}), ['ref']])} if IL else {}
refeitas = [l for l in IL if not saft_iva.get((refs_i[l['move_id'][0]], round(l['debit'], 2), round(l['credit'], 2), (l['name'] or '').strip()))]
equil = g.kw('account.move.line', 'search_count', [dom + [['name', '=', 'Automatic Balancing Line']]])
print(f'linhas de IVA sem correspondência no SAF-T (tem de ser 0): {len(refeitas)} | linhas de equilíbrio automático (tem de ser 0): {equil}')
for l in refeitas[:20]:
    print(f'  {refs_i[l["move_id"][0]]} | {l["name"]} | D {l["debit"]:,.2f} C {l["credit"]:,.2f}')
# Fichas duplicadas: o mesmo NIF (sem espaços nem prefixo de país) em mais de uma ficha principal. Depois do passo fundir_parceiros tem de dar 0, tirando os grupos que o passo
# deixou de fora de propósito (listados no diário).
def nif_chave(v):
    v = re.sub(r'[^A-Z0-9]', '', (v or '').upper())
    v = re.sub(r'^[A-Z]{2}(?=[A-Z0-9]{8,}$)', '', v)
    return v if len(v) >= 8 and v != '999999990' else None


PP = g.kw('res.partner', 'search_read', [[['parent_id', '=', False], ['company_id', 'in', [args.empresa, False]]]],
          {'fields': ['name', 'vat']})
por_nif = collections.defaultdict(list)
for x in PP:
    if nif_chave(x['vat']):
        por_nif[nif_chave(x['vat'])].append(x)
dup_nif = {k: v for k, v in por_nif.items() if len(v) > 1}
print(f'NIF com mais de uma ficha de parceiro (tem de ser 0): {len(dup_nif)}')
for k, v in list(dup_nif.items())[:10]:
    print(f'  {k}: ' + ' | '.join(f"{x['id']} {x['name']}" for x in v))
# Saldo de cada ficha da lista da contabilidade (ficheiro fichas_contabilidade, folha "Fichas duplicadas":
# Tipo, Conta, Nome, Ficha 1, Saldo 1, Ficha 2, Saldo 2, Saldo total) igual ao saldo total, nas 211/221
fichas_dif = []
if os.path.exists(args.fichas):
    ws = openpyxl.load_workbook(args.fichas, read_only=True, data_only=True)['Fichas duplicadas']
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r[0]:
            continue
        # A ficha pelo NIF da subconta no SAF-T: depois da fusão, ou de uma correção de NIF, a ficha que fica
        # pode ter outro nome que não os da lista
        k = nif_chave(ent.get(str(r[1])))
        pid = [x['id'] for x in PP if k and nif_chave(x['vat']) == k] or \
            g.kw('res.partner', 'search', [[['parent_id', '=', False], ['name', 'in', [r[3], r[5]]]]])
        conta = '211%' if r[0] == 'Cliente' else '221%'  # só 211 e 221, sem adiantamentos (218/228)
        sal = g.kw('account.move.line', 'read_group', [dom + [['partner_id', 'in', pid], ['account_id.code', '=like', conta]], ['balance:sum'], []],
                   {'lazy': False})[0]['balance'] or 0.0 if pid else None
        if len(pid) != 1 or sal is None or abs(round(sal, 2) - round(float(r[7]), 2)) >= 0.01:
            fichas_dif.append(f"{r[1]} {r[2]}: {len(pid)} ficha(s), saldo {sal if sal is None else round(sal, 2)}, esperado {r[7]}")
    print(f'fichas da lista da contabilidade com mais de uma ficha ou saldo diferente (tem de ser 0): {len(fichas_dif)}')
    for f in fichas_dif[:30]:
        print('  ' + f)
print(f'contas finais comparadas: {len(set(ESPERADO) | set(real))} | com diferença: {len(difs)}')
for f, e, r, d in difs[:60]:
    print(f'  {f:10} esperado {e:>15,.2f}  no Odoo {r:>15,.2f}  diferença {d:>14,.2f}')
print('RESULTADO:', 'BATE CERTO' if not difs and not refeitas and not equil else 'HÁ DIFERENÇAS')
