#!/usr/bin/env python3
"""
Compara os módulos instalados no Odoo do cliente com as árvores de addons do repositório.

PORQUE EXISTE

    A framework manda o agente ler «o código do projeto» para estabelecer o que o sistema
    faz. Isso pressupõe que o código do repositório é o código que está a correr — e essa
    suposição pode ser falsa sem que nada o denuncie.

    `FACTO OBSERVADO` (givachoice, 2026-09-11): o repositório tem **doze** árvores de
    addons de gerações diferentes em `addons_giva_v19/`, e a melhor acerta em **10 de 29**
    módulos instalados em produção. Um agente que leia aquelas pastas para «estabelecer o
    comportamento atual» conclui sobre código que não está a correr.

    No mesmo repositório, a branch de espelho `origin/live/producao` acerta em **29 de 29**.
    A verdade estava lá; o que faltava era alguém dizer ao agente que existe.

    Este script responde a uma pergunta e só a essa: **o que estou a ler corresponde ao que
    está instalado?** Não sincroniza, não escreve, não corrige.

DOIS USOS

    1. **Escolher a fonte** -- comparar as árvores do repositório e ver qual (se alguma)
       corresponde ao instalado.
    2. **Vigiar o espelho** (`--ref`) -- confirmar que a branch de espelho do código vivo
       continua a corresponder. É a rede que apanha o dia em que o mecanismo que o alimenta
       parar: um espelho parado não avisa que envelheceu, e continua a parecer a fonte.

O QUE COMPARA

    versão do manifest (`__manifest__.py`, chave `version`) contra `latest_version` do
    `ir.module.module` na base do cliente.

    **As duas não vêm no mesmo formato, e isso é uma armadilha.** O Odoo prefixa a versão
    com a série quando o manifest a omite: um manifest com `1.0.84` aparece instalado como
    `19.0.1.0.84`. Comparar em bruto dá 20 divergências falsas em 29 módulos — foi
    exactamente o que aconteceu na primeira execução deste código, a 2026-09-11, e quase
    se reportou um espelho saudável como avariado.

    Um comparador com falsos positivos é pior do que não existir: ensina a ignorar o
    alarme. Por isso a normalização acontece dos dois lados antes de comparar.

O QUE NÃO PROVA

    Versões iguais **não** provam código igual: nada obriga a subir a versão ao alterar
    um ficheiro, e no givachoice há registo de patches aplicados sem bump. Uma divergência
    é prova de que difere; uma coincidência é apenas ausência de prova do contrário.

Uso (da raiz do repositório do projeto):
    py .pg_framework/scripts/pg_compare_client_addons.py --project-key <key> --purpose production
    py .pg_framework/scripts/pg_compare_client_addons.py --project-key <key> --ref origin/live/producao --serie 19.0

Dependências: nenhuma além da biblioteca standard (invoca o helper PowerShell do canal).
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import subprocess
import sys

PURPOSES = ("production", "client_test", "brodoo_dev")


def encontrar_helper() -> str:
    """O helper do canal vive ao lado deste ficheiro, no framework."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(aqui, "pg_odoo_client_query.ps1")
    if not os.path.isfile(caminho):
        raise SystemExit("Helper nao encontrado: %s" % caminho)
    return caminho


def modulos_instalados(project_key: str, purpose: str, prefixos: list) -> dict:
    """{nome: versao} do que está instalado na base do cliente."""
    dominio = ["&", ["state", "=", "installed"]]
    if len(prefixos) == 1:
        dominio.append(["name", "like", prefixos[0]])
    else:
        dominio.extend(["|"] * (len(prefixos) - 1))
        dominio.extend([["name", "like", p] for p in prefixos])

    comando = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", encontrar_helper(),
        "-ProjectKey", project_key, "-Purpose", purpose,
        "-Model", "ir.module.module",
        "-Domain", json.dumps(dominio),
        "-Fields", "name,latest_version",
    ]
    proc = subprocess.run(comando, capture_output=True)

    # O stdout do PowerShell não vem em UTF-8 nesta plataforma, e decodificá-lo como tal
    # rebenta em nomes acentuados. Aqui só se leem nomes técnicos e versões (ASCII), pelo
    # que latin-1 é seguro e não perde nada -- não faça isto com conteúdo de utilizador.
    saida = proc.stdout.decode("latin-1", errors="replace")
    if proc.returncode != 0:
        erro = proc.stderr.decode("latin-1", errors="replace")
        raise SystemExit("A consulta ao Odoo do cliente falhou (purpose=%s):\n%s\n%s"
                         % (purpose, saida.strip()[:800], erro.strip()[:800]))

    inicio = saida.find("[")
    if inicio < 0:
        inicio = saida.find("{")
    if inicio < 0:
        raise SystemExit("Resposta sem JSON reconhecivel:\n%s" % saida.strip()[:800])

    dados = json.loads(saida[inicio:], strict=False)
    if isinstance(dados, dict):
        dados = [dados]
    return {m["name"]: str(m.get("latest_version") or "") for m in dados}


def normalizar(versao, serie=None):
    """
    Tira o prefixo da série, para `1.0.84` e `19.0.1.0.84` compararem iguais.

    Sem série conhecida, cai num heurístico conservador: retira um prefixo `<n>.<n>.`
    apenas quando o que sobra ainda tem pelo menos dois componentes -- para não destruir
    uma versão que seja mesmo `19.0` ou `2.0`.
    """
    v = (versao or "").strip()
    if not v:
        return v
    if serie:
        prefixo = serie if serie.endswith(".") else serie + "."
        if v.startswith(prefixo):
            return v[len(prefixo):]
        return v
    partes = v.split(".")
    if len(partes) >= 4:
        return ".".join(partes[2:])
    return v


def versao_do_manifest(caminho: str):
    try:
        with io.open(caminho, encoding="utf-8", errors="replace") as fh:
            dados = ast.literal_eval(fh.read())
    except Exception:
        return None
    if not isinstance(dados, dict):
        return None
    return str(dados.get("version") or "")


def serie_do_destino(project_key: str, purpose: str) -> str:
    """
    Série do Odoo que corre MESMO na base-alvo, lida da versão do módulo `base`.

    Existe para o passo 1 da regra de implantação: confirmar a série do destino contra o
    próprio destino, e não contra o que se julga. `FACTO OBSERVADO` (givachoice): código
    v17 foi implantado sobre o servidor de testes v19, e só um backup manual feito por
    sorte o desfez. A pergunta que teria evitado isso é esta, e custa uma chamada.
    """
    instalados = modulos_instalados(project_key, purpose, ["base"])
    versao = instalados.get("base")
    if not versao:
        return ""
    partes = versao.split(".")
    return ".".join(partes[:2]) if len(partes) >= 2 else versao


def modulos_da_ref(ref: str, nomes) -> dict:
    """
    {nome: versao} lido de uma ref git, sem tocar na árvore de trabalho.

    Usa `git show <ref>:<mod>/__manifest__.py`, que lê do objecto e não do disco -- pelo
    que funciona com a branch de espelho por fazer checkout, e sem mexer no que está lá.
    """
    encontrados = {}
    for nome in nomes:
        proc = subprocess.run(["git", "show", "%s:%s/__manifest__.py" % (ref, nome)],
                              capture_output=True)
        if proc.returncode != 0:
            continue
        try:
            dados = ast.literal_eval(proc.stdout.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if isinstance(dados, dict):
            encontrados[nome] = str(dados.get("version") or "")
    return encontrados


def arvores_de_addons(raiz: str) -> list:
    """Pastas que contenham pelo menos um módulo Odoo."""
    encontradas = []
    for atual, subpastas, _ in os.walk(raiz):
        # não descer para dentro dos próprios módulos, nem para o source do Odoo
        subpastas[:] = [s for s in subpastas
                        if s not in (".git", "node_modules", "__pycache__")
                        and not os.path.isfile(os.path.join(atual, s, "__manifest__.py"))
                        and os.path.basename(atual) != "vendor"]
        tem = [s for s in os.listdir(atual)
               if os.path.isfile(os.path.join(atual, s, "__manifest__.py"))]
        if tem:
            encontradas.append(atual)
    return sorted(encontradas)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="O repositorio corresponde ao que esta instalado no cliente?")
    ap.add_argument("--project-key", required=True)
    ap.add_argument("--purpose", default="production", choices=PURPOSES)
    ap.add_argument("--raiz", default=".", help="Onde procurar arvores de addons.")
    ap.add_argument("--ref", default=None,
                    help="Comparar contra uma ref git (ex.: origin/live/producao) em vez das "
                         "arvores do disco. E o modo de vigilancia do espelho.")
    ap.add_argument("--prefixo", action="append", default=None,
                    help="Prefixo dos modulos a comparar (repetivel; por omissao 'pg_').")
    ap.add_argument("--serie", default=None,
                    help="Serie do Odoo (ex.: 19.0) para normalizar as versoes. Sem ela usa-se "
                         "um heuristico conservador.")
    ap.add_argument("--serie-esperada", default=None,
                    help="Falhar se a serie que corre no destino nao for esta. Passo 1 da "
                         "regra de implantacao: confirmar o destino ANTES de copiar nada.")
    ap.add_argument("--detalhe", action="store_true",
                    help="Listar modulo a modulo a arvore que mais se aproxima.")
    args = ap.parse_args()

    # Passo 1 da regra de implantacao, antes de qualquer outra coisa.
    if args.serie_esperada:
        real = serie_do_destino(args.project_key, args.purpose)
        if not real:
            raise SystemExit("Nao foi possivel ler a serie do destino (purpose=%s): o modulo "
                             "'base' nao respondeu. Nao prosseguir as cegas." % args.purpose)
        if real != args.serie_esperada.strip():
            raise SystemExit(
                "SERIE ERRADA. O destino '%s' corre Odoo %s, esperava-se %s. "
                "NAO implantar: e assim que codigo de uma serie vai parar a um servidor de "
                "outra. No givachoice isso aconteceu (v17 sobre v19) e so um backup manual "
                "feito por sorte o desfez." % (args.purpose, real, args.serie_esperada.strip()))
        print("Serie do destino '%s' confirmada: %s" % (args.purpose, real))
        if not args.serie:
            args.serie = real

    prefixos = args.prefixo or ["pg_"]
    instalados = modulos_instalados(args.project_key, args.purpose, prefixos)
    if not instalados:
        print("Nenhum modulo instalado corresponde aos prefixos %s em '%s'."
              % (prefixos, args.purpose))
        return 0

    print("Instalados em '%s': %d modulo(s)" % (args.purpose, len(instalados)))

    # --- modo vigilancia do espelho ----------------------------------------
    if args.ref:
        noRef = modulos_da_ref(args.ref, instalados.keys())
        iguais = difere = 0
        divergentes = []
        for nome, vinst in sorted(instalados.items()):
            v = noRef.get(nome)
            if v is None:
                divergentes.append(("AUSENTE", nome, "-", vinst))
                continue
            if normalizar(v, args.serie) == normalizar(vinst, args.serie):
                iguais += 1
            else:
                difere += 1
                divergentes.append(("DIFERE", nome, v, vinst))
        ausentes = len(instalados) - iguais - difere

        print("Espelho '%s': iguais=%d difere=%d ausentes=%d"
              % (args.ref, iguais, difere, ausentes))
        if not divergentes:
            print("OK: o espelho corresponde ao instalado em '%s'." % args.purpose)
            return 0
        print()
        print("AVISO: o espelho NAO corresponde ao instalado. Verificar se o mecanismo que o")
        print("       alimenta continua a correr -- um espelho parado nao avisa que envelheceu.")
        for e in divergentes[:20]:
            print("  %-8s %-32s espelho: %-14s instalado: %s" % e)
        if len(divergentes) > 20:
            print("  ... e mais %d" % (len(divergentes) - 20))
        return 1

    arvores = arvores_de_addons(args.raiz)
    if not arvores:
        print("Nenhuma arvore de addons encontrada em '%s'." % args.raiz)
        return 0

    print("Arvores de addons no repositorio: %d" % len(arvores))
    print()
    print("  %-44s %6s %6s %6s %7s" % ("arvore", "mods", "igual", "difere", "ausente"))

    melhor = None
    for arvore in arvores:
        modulos = [m for m in os.listdir(arvore)
                   if os.path.isfile(os.path.join(arvore, m, "__manifest__.py"))]
        iguais = difere = 0
        for m in modulos:
            if m not in instalados:
                continue
            v = versao_do_manifest(os.path.join(arvore, m, "__manifest__.py"))
            if v is None:
                continue
            if normalizar(v, args.serie) == normalizar(instalados[m], args.serie):
                iguais += 1
            else:
                difere += 1
        ausentes = len(instalados) - iguais - difere
        rotulo = os.path.relpath(arvore, args.raiz)
        print("  %-44s %6d %6d %6d %7d" % (rotulo[:44], len(modulos), iguais, difere, ausentes))
        if melhor is None or iguais > melhor[1]:
            melhor = (arvore, iguais, difere, ausentes)

    print()
    arvore, iguais, difere, ausentes = melhor
    total = len(instalados)
    print("Melhor correspondencia: %s -- %d de %d modulo(s) na mesma versao."
          % (os.path.relpath(arvore, args.raiz), iguais, total))

    if iguais == total:
        print("O repositorio corresponde ao instalado (pelas versoes; ver 'O QUE NAO PROVA').")
        return 0

    # Uma correspondencia parcial e o caso perigoso: parece codigo do projeto e nao e.
    print()
    print("AVISO: o repositorio NAO corresponde ao que esta a correr em '%s'." % args.purpose)
    print("       Ler estas pastas para estabelecer o comportamento atual da a resposta errada.")
    print("       Usar o canal do cliente para os factos, e marcar PONTO POR VALIDAR o resto.")

    if args.detalhe:
        print()
        print("Detalhe da arvore mais proxima (%s):" % os.path.relpath(arvore, args.raiz))
        for nome in sorted(instalados):
            man = os.path.join(arvore, nome, "__manifest__.py")
            if not os.path.isfile(man):
                print("  AUSENTE  %-34s instalado: %s" % (nome, instalados[nome]))
                continue
            v = versao_do_manifest(man)
            if normalizar(v, args.serie) == normalizar(instalados[nome], args.serie):
                print("  igual    %-34s %s" % (nome, v))
            else:
                print("  DIFERE   %-34s repo: %-14s instalado: %s" % (nome, v, instalados[nome]))

    return 1


if __name__ == "__main__":
    sys.exit(main())
