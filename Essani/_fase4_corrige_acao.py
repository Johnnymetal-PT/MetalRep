#!/usr/bin/env python3
r"""
Correções da ação da regra 17 (circuito de alterações de especificação).

v1 — leitura das propriedades
  O código lia `produto.product_properties` directamente. Acedido por ORM, um campo
  `properties` devolve o dicionário cru {nome: valor}; iterá-lo dá as CHAVES (texto),
  e `prop.get("type")` rebentava com `AttributeError: 'str' object has no attribute
  'get'` — o que anulava a gravação do artigo. A representação completa, com
  `string`, `type` e `value` já fundidos com a definição da categoria, obtém-se por
  `read()`.

v2 — HTML da nota (nunca chegou a correr)
  `message_post(body=<str>)` escapa a cadeia: a nota saía com as etiquetas à vista.
  A tentativa foi usar `Markup` com um `except NameError` como rede. Não existe
  nenhum dos dois no `safe_eval` do Odoo — nem `Markup`, nem `NameError` — pelo que
  a própria rede rebentou. Segundo bloqueio de gravação em produção.

v3 — sem HTML de todo
  A correção é tirar as etiquetas em vez de as proteger. `message_post`, ao receber
  texto simples, passa-o por `plaintext2html`, que escapa o que for etiqueta e
  converte as quebras de linha. Sem negrito, mas com as linhas certas e sem depender
  de nada que possa não existir no contexto restrito.

  NOTA A QUEM MEXER: `CODIGO` é uma cadeia *raw* (r'''...''') de propósito. Sem o
  prefixo, as sequências de escape do corpo e dos comentários são interpretadas aqui
  e chegam ao Odoo como quebras de linha reais, partindo o código gerado — foi o que
  aconteceu na primeira tentativa de publicar a v3.

Idempotente pelo marcador de versão. Dry-run por defeito; escrita exige --confirm
e --allow-prod. `--desativar` é a saída de emergência: desliga a regra 17 e devolve
a gravação de artigos ao normal, sem tocar em mais nada.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
NOME_REGRA = "PG Protótipos: alteração de especificações → gestor de projeto"
MARCADOR = "# pg-circuito-especificacoes v4"

CODIGO = r'''# pg-circuito-especificacoes v4
# Avisa o gestor de projeto de que as especificacoes do prototipo mudaram.
#
# As propriedades leem-se por read(), nunca por acesso directo ao campo: o acesso
# directo devolve o dicionario cru {nome: valor}, sem rotulos nem tipos.
#
# O corpo vai numa unica linha, com " · " a separar. Nao ha alternativa util:
# o safe_eval do Odoo nao expoe Markup (nem NameError, pelo que nem um
# try/except serve de rede), e o message_post, ao receber texto simples,
# envolve-o em <p> e escapa etiquetas, mas NAO converte quebras de linha em
# <br>. Etiquetas aparecem literais; \n desaparece. Sobra o separador.
for produto in records:
    projetos = env["project.project"].search(
        [("x_pg_artigo_prototipo", "=", produto.id)])
    if not projetos:
        continue

    linhas = []
    for prop in (produto.read(["product_properties"])[0].get("product_properties") or []):
        if not isinstance(prop, dict) or prop.get("type") == "separator":
            continue
        valor = prop.get("value")
        if valor not in (None, False, "", 0, 0.0):
            linhas.append("%s: %s" % (prop.get("string"), valor))

    corpo = "As especifica\u00e7\u00f5es do artigo %s foram alteradas. %s" % (
        produto.display_name, " \u00b7 ".join(linhas) or "(sem valores preenchidos)")

    for projeto in projetos:
        projeto.message_post(body=corpo, subtype_xmlid="mail.mt_note")
        if projeto.user_id:
            projeto.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=projeto.user_id.id,
                summary="Especifica\u00e7\u00f5es alteradas",
                note=("As especifica\u00e7\u00f5es de %s mudaram. Rever o impacto "
                      "na produ\u00e7\u00e3o do prot\u00f3tipo." % produto.display_name),
            )
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--allow-prod", action="store_true")
    p.add_argument("--conn", help="ficheiro de ligacao a usar em vez do canal "
                                   "Brodoo; serve para apontar a staging")
    p.add_argument("--desativar", action="store_true",
                   help="apenas desativa a regra 17 (saída de emergência)")
    a = p.parse_args()
    alvo = resolver_alvo(a.conn) if a.conn else resolver_alvo_por_projeto(
        PROJECT_KEY, "production")
    g = Guard(alvo, confirmed=a.confirm, allow_prod=a.allow_prod)
    kw = g.kw
    escrever = a.confirm and (a.allow_prod or alvo.purpose != "production")
    print("alvo: %s | base=%s" % (alvo.base_url, alvo.database))
    print("modo: %s\n" % ("ESCRITA" if escrever else "DRY-RUN"))

    # A regra e a acao resolvem-se pelo NOME, nunca por id: os ids de producao nao
    # existem na staging nem em nenhuma base recriada, e este script tem de poder
    # correr em qualquer uma delas.
    regra = kw("base.automation", "search_read",
               [[["name", "=", NOME_REGRA]], ["id", "active", "action_server_ids"]],
               {"context": {"active_test": False}})
    if not regra:
        print("ABORTADO: regra '%s' não existe nesta base." % NOME_REGRA)
        return
    regra = regra[0]

    if a.desativar:
        print("=== desativar a regra (id=%s) ===" % regra["id"])
        if escrever:
            kw("base.automation", "write", [[regra["id"]], {"active": False}], allow_write=True)
            v = kw("base.automation", "read", [[regra["id"]], ["active"]],
                   {"context": {"active_test": False}})[0]
            print("  regra activa=%s" % v["active"])
        else:
            print("  (dry-run) desativaria a regra")
        return

    if not regra["action_server_ids"]:
        print("ABORTADO: a regra não tem ação associada.")
        return
    acao_id = regra["action_server_ids"][0]

    # Validacao local antes de falar com o Odoo: um erro de sintaxe no codigo
    # gerado so se descobria com o write a rebentar do outro lado.
    try:
        compile(CODIGO, "<codigo da acao>", "exec")
        print("sintaxe do código a publicar: OK")
    except SyntaxError as erro:
        print("ABORTADO — o código a publicar não compila: %s (linha %s)"
              % (erro.msg, erro.lineno))
        return

    print("\n=== corrigir a ação %d ===" % acao_id)
    act = kw("ir.actions.server", "read", [[acao_id], ["name", "state", "code"]])[0]
    print("  ação: %s (state=%s)" % (act["name"][:52], act["state"]))
    if MARCADOR in (act["code"] or ""):
        print("  já está na v4 — nada a fazer.")
        return
    print("  * a substituir o código (%d -> %d caracteres)" % (len(act["code"] or ""), len(CODIGO)))
    if escrever:
        kw("ir.actions.server", "write", [[acao_id], {"code": CODIGO}], allow_write=True)
        v = kw("ir.actions.server", "read", [[acao_id], ["code"]])[0]
        print("  reconciliação: marcador v4 presente = %s" % (MARCADOR in v["code"]))
        r = kw("base.automation", "read", [[regra["id"]], ["active"]],
               {"context": {"active_test": False}})[0]
        print("  regra activa=%s" % r["active"])


if __name__ == "__main__":
    main()
