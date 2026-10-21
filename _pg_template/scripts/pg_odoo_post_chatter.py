r"""Publica uma nota no chatter de um registo do Odoo, a partir de um rascunho em markdown.

Existe porque o caminho ingénuo falha em silêncio: o `message_post` chamado por RPC
**escapa** o HTML do corpo. Desde o Odoo 16 só é tratado como HTML um corpo que chegue
como `Markup`, e um `str` vindo de JSON-RPC nunca é — o resultado é uma nota com as
etiquetas `<p>` e `<b>` à vista de toda a gente que abrir a tarefa.

O parâmetro `body_is_html=True` do próprio `message_post` resolve numa só chamada, e é
isso que este script usa. Detalhe e evidência no source: `docs/PG_CHATTER_ODOO_FORMATTING.md`.

O corpo escreve-se em markdown, como os emails ao cliente, e é convertido pelo mesmo
conversor (`pg_build_email_cliente.py`) — o HTML que o Odoo aceita é o mesmo nos dois
sítios, e ter um conversor só evita que divirjam.

Uso:
  py scripts\pg_odoo_post_chatter.py --model project.task --id 7577 --ficheiro nota.md
  py scripts\pg_odoo_post_chatter.py --model project.task --id 7577 --ficheiro nota.md --dry-run
  py scripts\pg_odoo_post_chatter.py --model project.task --id 7577 --ficheiro nota.md --nota-interna
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from pg_build_email_cliente import converter, validar_fragmento  # noqa: E402
from pg_doc_templates_common import OdooKnowledgeClient  # noqa: E402
from pg_odoo_credentials import resolver_credenciais_pg  # noqa: E402


def markdown_para_html(markdown: str) -> tuple[str, list[str]]:
    resultado = converter(markdown, manter_assinatura=True)
    # O aviso do assunto é do contrato dos emails; no chatter não há assunto.
    avisos = [a for a in resultado.avisos if "Sem assunto" not in a]
    # Os restantes avisos justificam-se pela colagem no compositor, que aqui não acontece:
    # o `<code>` e o `<hr>` até sobreviveriam ao chatter, mas o conversor é partilhado com
    # os emails e descarta-os na origem. A perda é real; a razão é que não é essa.
    avisos = [a.replace("não sobrevive à colagem no Odoo",
                        "fica de fora do conversor partilhado com os emails") for a in avisos]
    return resultado.fragmento, avisos + validar_fragmento(resultado.fragmento)


def resolver_destinatarios(cliente, logins: list[str]) -> list[int]:
    """Logins -> partner_ids. Um login que nao resolva e erro, nao silencio: uma mensagem
    entregue a menos pessoas do que se pensa e pior do que uma que falha a dizer porque."""
    if not logins:
        return []
    achados = cliente.call_kw("res.users", "search_read",
                              args=[[["login", "in", logins]]],
                              kwargs={"fields": ["login", "partner_id"]})
    por_login = {u["login"]: u["partner_id"][0] for u in achados}
    em_falta = [l for l in logins if l not in por_login]
    if em_falta:
        raise ValueError("logins sem utilizador no Odoo: " + ", ".join(em_falta))
    return [por_login[l] for l in logins]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", required=True, help="modelo do registo, ex.: project.task")
    ap.add_argument("--id", required=True, type=int, help="id do registo")
    ap.add_argument("--ficheiro", required=True, type=pathlib.Path, help="rascunho .md")
    ap.add_argument("--nota-interna", action="store_true",
                    help="publica como nota interna (mail.mt_note) em vez de mensagem")
    ap.add_argument("--para", default="",
                    help="logins Odoo separados por virgula a notificar (recebem o email do chatter)")
    ap.add_argument("--dry-run", action="store_true", help="mostra o HTML e nao publica nada")
    args = ap.parse_args(argv)

    if not args.ficheiro.exists():
        print(f"ERRO: {args.ficheiro} nao existe", file=sys.stderr)
        return 2

    html, avisos = markdown_para_html(args.ficheiro.read_text(encoding="utf-8"))
    for aviso in avisos:
        print(f"AVISO: {aviso}")

    logins = [l.strip() for l in args.para.split(",") if l.strip()]

    if args.dry_run:
        if logins:
            print("notificaria: " + ", ".join(logins))
        print("--- HTML que seria publicado ---")
        print(html)
        return 0

    cred = resolver_credenciais_pg()
    print(f"autenticado como: {cred['login']} ({cred['origem']})")
    cliente = OdooKnowledgeClient(cred["url"], cred["db"], cred["login"], cred["api_key"])

    try:
        destinatarios = resolver_destinatarios(cliente, logins)
    except ValueError as exc:
        print("ERRO: " + str(exc), file=sys.stderr)
        return 2
    if destinatarios:
        print("a notificar: " + ", ".join(logins))

    devolvido = cliente.call_kw(
        args.model, "message_post",
        args=[[args.id]],
        kwargs={
            "body": html,
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_note" if args.nota_interna else "mail.mt_comment",
            # Sem isto o Odoo escapa o corpo e a nota sai com as etiquetas a vista.
            "body_is_html": True,
            "partner_ids": destinatarios,
        },
    )
    # Conforme o transporte, vem o id ou uma lista com ele.
    mid = devolvido[0] if isinstance(devolvido, list) else devolvido
    print(f"publicado: mail.message {mid}")
    print(f"ver em: {cred['url'].rstrip('/')}/odoo/{args.model}/{args.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
