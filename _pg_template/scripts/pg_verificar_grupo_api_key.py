r"""Verifica, contra a produção, que o grupo das credenciais dos clientes protege mesmo.

Passo 7 da janela `docs/PG_JANELA_PG_BRODOO_1_15_0.md`. Prova as três afirmações que os
testes do PR #20 fazem e que nunca correram:

  1. o campo `api_key` carrega a restrição de grupo;
  2. quem está no grupo lê a chave;
  3. quem NÃO está no grupo não a lê, nem a vê no `fields_get` -- que é o caminho por RPC,
     por onde os helpers da framework falam com o modelo.

O terceiro é o que custa: precisa de uma sessão RPC de alguém fora do grupo, e a chave é
pessoal -- não se fabrica a de outra pessoa nem se lê a dela. A saída é sair do grupo por
instantes, medir com a própria chave, e voltar a entrar. É o operador a testar-se a si
mesmo, sem criar utilizadores nem credenciais na produção só para isto.

Por isso o script sai do grupo e volta a entrar **sempre**, mesmo que a medição do meio
falhe: a reposição está num `finally`. Um operador que fique de fora do grupo por causa de
uma verificação é pior do que a verificação que ele queria fazer.

Uso:
  py scripts\pg_verificar_grupo_api_key.py --dry-run
  py scripts\pg_verificar_grupo_api_key.py --confirmar
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

XMLID_GRUPO = "pg_brodoo.group_pg_odoo_connection_secret"
CAMPO = "api_key"
MODELO = "pg.odoo.connection"


def ligar():
    from pg_doc_templates_common import OdooKnowledgeClient
    from pg_odoo_credentials import resolver_credenciais_pg
    cred = resolver_credenciais_pg()
    return cred, OdooKnowledgeClient(cred["url"], cred["db"], cred["login"], cred["api_key"])


def resolver_xmlid(cliente, xmlid):
    modulo, nome = xmlid.split(".", 1)
    achados = cliente.call_kw("ir.model.data", "search_read",
                              args=[[["module", "=", modulo], ["name", "=", nome]]],
                              kwargs={"fields": ["res_id"]})
    return achados[0]["res_id"] if achados else None


def ve_o_campo(cliente):
    """True se o `fields_get` devolve o campo a quem esta a chamar."""
    campos = cliente.call_kw(MODELO, "fields_get", args=[[CAMPO], ["groups"]])
    return CAMPO in campos, campos.get(CAMPO, {}).get("groups")


def le_a_chave(cliente, ligacao_id):
    """True se o `read` devolve o campo. Nao imprime o valor -- so se ele veio."""
    try:
        linhas = cliente.call_kw(MODELO, "read", args=[[ligacao_id], [CAMPO]])
    except Exception:
        return False
    return bool(linhas) and CAMPO in linhas[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="diz o que faria e nao toca em nada")
    ap.add_argument("--confirmar", action="store_true", help="executa, incluindo sair e voltar ao grupo")
    args = ap.parse_args(argv)

    if not (args.dry_run or args.confirmar):
        print("ERRO: usar --dry-run ou --confirmar", file=sys.stderr)
        return 2

    cred, cliente = ligar()
    print(f"destino   : {cred['url']} / {cred['db']}")
    print(f"operador  : {cred['login']}")

    gid = resolver_xmlid(cliente, XMLID_GRUPO)
    if not gid:
        print(f"ERRO: o grupo {XMLID_GRUPO} nao existe na base -- a janela ainda nao foi aplicada.",
              file=sys.stderr)
        return 1
    print(f"grupo     : id {gid}")

    eu = cliente.call_kw("res.users", "search_read",
                         args=[[["login", "=", cred["login"]]]],
                         kwargs={"fields": ["name", "all_group_ids"]})[0]
    sou_membro = gid in (eu.get("all_group_ids") or [])
    print(f"sou membro: {sou_membro}")

    ligacoes = cliente.call_kw(MODELO, "search", args=[[]], kwargs={"limit": 1})
    if not ligacoes:
        print("ERRO: nao ha ligacoes para testar.", file=sys.stderr)
        return 1
    alvo = ligacoes[0]

    if args.dry_run:
        print()
        print("--- o que faria ---")
        print(f"  1. confirmar que o campo {CAMPO} carrega a restricao de grupo")
        print(f"  2. como MEMBRO: ler {CAMPO} da ligacao {alvo} (sem imprimir o valor)")
        print(f"  3. sair do grupo {gid}, repetir a leitura e o fields_get, voltar a entrar")
        print("     (a reposicao corre num finally, mesmo que o passo falhe)")
        return 0

    if not sou_membro:
        print("ERRO: nao sou membro do grupo -- atribuir primeiro (passo 6 da janela).", file=sys.stderr)
        return 1

    resultados = {}
    ve, grupos = ve_o_campo(cliente)
    resultados["1. o campo carrega a restricao"] = bool(grupos)
    print(f"\n1. fields_get como membro: campo visivel={ve} groups={grupos}")

    resultados["2. membro le a chave"] = le_a_chave(cliente, alvo)
    print(f"2. read como membro: {resultados['2. membro le a chave']}")

    try:
        cliente.call_kw("res.users", "write", args=[[eu["id"]], {"group_ids": [(3, gid)]}])
        ve_fora, _ = ve_o_campo(cliente)
        le_fora = le_a_chave(cliente, alvo)
        resultados["3. nao-membro nao ve o campo no fields_get"] = not ve_fora
        resultados["4. nao-membro nao le a chave"] = not le_fora
        print(f"3. fields_get fora do grupo: campo visivel={ve_fora}")
        print(f"4. read fora do grupo: leu={le_fora}")
    finally:
        cliente.call_kw("res.users", "write", args=[[eu["id"]], {"group_ids": [(4, gid)]}])
        de_volta = gid in (cliente.call_kw("res.users", "read", args=[[eu["id"]], ["all_group_ids"]])[0]
                           .get("all_group_ids") or [])
        print(f"   reposicao no grupo: {'OK' if de_volta else 'FALHOU -- ATRIBUIR A MAO'}")

    print()
    for nome, ok in resultados.items():
        print(f"  {'OK  ' if ok else 'FALHA'}  {nome}")
    tudo = all(resultados.values())
    print()
    print("VERIFICADO: a proteccao funciona nos dois sentidos." if tudo
          else "NAO VERIFICADO: reverter a janela (git revert + build) e reportar.")
    return 0 if tudo else 1


if __name__ == "__main__":
    sys.exit(main())
