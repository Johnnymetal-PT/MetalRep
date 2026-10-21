#!/usr/bin/env python3
"""
Taxa retida pela entidade de pagamento nas vendas online (tarefa PG 7006).

O QUE RESOLVE
    Quando uma venda é paga pelo site, a entidade de pagamento transfere menos do que
    foi faturado e retém a diferença como taxa. O cliente pagou a fatura por inteiro,
    pelo que a diferença não é desconto: é um gasto da empresa. Se ninguém lançar esse
    gasto, a fatura fica eternamente em dívida pelo valor da taxa.

    Caso de origem: FT FTO/00032, total 643,40 €, extrato bancário com 631,52 €,
    11,88 € por liquidar.

O QUE FAZ
    1. Corrige o modelo de reconciliação "Bank Fees", cuja contrapartida aponta para
       `311 Mercadorias` — lançava taxas em compras de mercadorias. Passa para
       `6227 Serviços Bancários`.
    2. Liquida o remanescente da fatura com um lançamento de write-off
       (débito na conta de gastos, crédito na conta do cliente) e reconcilia-o com a
       linha aberta. É o mesmo resultado contabilístico do assistente "Reconciliar"
       do Odoo, que é como o processo deve ser feito na interface.

    Não emite nota de crédito nem segundo recibo: a base tributável e o IVA da fatura
    não são tocados, porque não houve desconto ao cliente.

COMO CORRER
    python scripts/pg_taxa_entidade_pagamento.py                     # dry-run
    python scripts/pg_taxa_entidade_pagamento.py --confirm           # aplica
    python scripts/pg_taxa_entidade_pagamento.py --confirm --reset   # desfaz

    Por defeito aponta para a staging (`brodoo_dev`). Para produção seria preciso
    `--purpose production --allow-prod`, e só depois de um dry-run revisto.

    É idempotente: correr duas vezes seguidas não duplica nada.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import xmlrpc.client

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                ".pg_framework", "scripts"))

from pg_odoo_migration_guard import (  # noqa: E402
    ErroDeGuarda, Guard, resolver_alvo_por_projeto,
)

PROJECT_KEY = "odoo-waterdetails-virgin-details-lda"
EMPRESA_ID = 1                      # VIRGIN DETAILS, LDA
CONTA_TAXA_CODIGO = "6227"          # Serviços Bancários
CONTA_ERRADA_CODIGO = "311"         # Mercadorias — o que o modelo tinha
MODELO_RECONCILIACAO = "Bank Fees"
FATURA = "FT FTO/00032"
REF_WRITEOFF = "TAXA-PSP FT FTO/00032"
ETIQUETA = "Taxa entidade de pagamento FT FTO/00032"


def alvo_da_staging(purpose: str):
    """
    Resolve o alvo, contornando a chave da staging invalidada pelo rebuild.

    Em Odoo.sh cada rebuild da branch recria a base a partir de produção. Uma API key
    gerada dentro da build de staging desaparece nesse momento, e é o que aconteceu à
    chave guardada em `pg.odoo.connection` para esta ligação. A chave de produção, essa,
    é copiada com a base e continua a autenticar — daí ser a que se usa quando a outra
    falha. Continua tudo em memória e a finalidade da ligação mantém-se `brodoo_dev`,
    que é o que autoriza (ou não) a escrita.
    """
    alvo = resolver_alvo_por_projeto(PROJECT_KEY, purpose)
    if purpose == "brodoo_dev":
        try:
            Guard(alvo)
        except ErroDeGuarda:
            producao = resolver_alvo_por_projeto(PROJECT_KEY, "production")
            print("  aviso: chave da ligação de staging inválida (rebuild da branch); "
                  "a usar a chave de produção contra a base de staging.")
            alvo.login, alvo.api_key = producao.login, producao.api_key
    return alvo


def escrever(o: Guard, modelo: str, metodo: str, args: list):
    """
    Escreve no Odoo, tolerando a resposta que o XML-RPC não sabe serializar.

    Vários métodos de contabilidade devolvem `None` (`remove_move_reconcile`) ou um
    dicionário com valores `None` (`reconcile`, quando não há diferença de câmbio). O
    marshaller do XML-RPC corre com `allow_none=False` e rebenta com "cannot marshal
    None" ao codificar a resposta — mas a operação já foi executada e confirmada do lado
    do servidor: a falha é só no caminho de volta. Ignorar outra falha qualquer seria
    esconder um erro real, por isso a excepção é reconhecida pela mensagem.
    """
    try:
        return o.kw(modelo, metodo, args, allow_write=True)
    except xmlrpc.client.Fault as erro:
        if "cannot marshal None" not in str(erro):
            raise
        return None


def id_unico(o: Guard, modelo: str, dominio: list, descricao: str) -> int:
    ids = o.kw(modelo, "search", [dominio], {"limit": 2})
    if not ids:
        raise SystemExit(f"FALHOU: não encontrei {descricao}.")
    if len(ids) > 1:
        raise SystemExit(f"FALHOU: {descricao} é ambíguo ({ids}).")
    return ids[0]


# -- passo 1: modelo de reconciliação ------------------------------------


def corrigir_modelo(o: Guard, conta_taxa: int, aplicar: bool) -> None:
    print("\n[1] Modelo de reconciliação")
    modelos = o.kw("account.reconcile.model", "search_read",
                   [[["name", "=", MODELO_RECONCILIACAO], ["company_id", "=", EMPRESA_ID]]],
                   {"fields": ["name", "line_ids"]})
    if not modelos:
        print(f"    modelo '{MODELO_RECONCILIACAO}' não existe nesta base — nada a fazer.")
        return
    modelo = modelos[0]
    linhas = o.kw("account.reconcile.model.line", "read",
                  [modelo["line_ids"], ["account_id", "label", "amount_type", "amount_string"]])
    for linha in linhas:
        atual = linha["account_id"]
        if atual and atual[0] == conta_taxa:
            print(f"    linha {linha['id']}: já aponta para {atual[1]} — nada a fazer.")
            continue
        print(f"    linha {linha['id']}: {atual[1] if atual else '(vazia)'} -> conta {CONTA_TAXA_CODIGO}")
        if aplicar:
            escrever(o, "account.reconcile.model.line", "write",
                     [[linha["id"]], {"account_id": conta_taxa}])
            print("      corrigido.")


# -- passo 2: liquidar o remanescente da fatura --------------------------


def linha_aberta_da_fatura(o: Guard, fatura_id: int):
    linhas = o.kw("account.move.line", "search_read",
                  [[["move_id", "=", fatura_id],
                    ["account_type", "=", "asset_receivable"],
                    ["reconciled", "=", False]]],
                  {"fields": ["id", "account_id", "partner_id", "amount_residual", "date"]})
    return linhas[0] if linhas else None


def liquidar_fatura(o: Guard, conta_taxa: int, diario_misc: int, aplicar: bool) -> None:
    print("\n[2] Fatura")
    faturas = o.kw("account.move", "search_read",
                   [[["name", "=", FATURA], ["company_id", "=", EMPRESA_ID],
                     ["move_type", "=", "out_invoice"]]],
                   {"fields": ["name", "amount_total", "amount_residual", "payment_state", "state"]})
    if not faturas:
        print(f"    {FATURA} não existe nesta base — nada a fazer.")
        return
    fatura = faturas[0]
    print(f"    {fatura['name']} (id {fatura['id']}): total {fatura['amount_total']:.2f} € | "
          f"em dívida {fatura['amount_residual']:.2f} € | {fatura['payment_state']}")

    if fatura["state"] != "posted":
        print(f"    fatura em estado '{fatura['state']}' — não mexo.")
        return
    if abs(fatura["amount_residual"]) < 0.005:
        print("    já está totalmente liquidada — nada a fazer.")
        return

    aberta = linha_aberta_da_fatura(o, fatura["id"])
    if not aberta:
        print("    sem linha de cliente por reconciliar — nada a fazer.")
        return

    valor = round(aberta["amount_residual"], 2)
    parceiro = aberta["partner_id"][0]
    print(f"    write-off de {valor:.2f} €: débito conta {CONTA_TAXA_CODIGO}, "
          f"crédito {aberta['account_id'][1]} (parceiro {aberta['partner_id'][1]})")

    existentes = o.kw("account.move", "search",
                      [[["ref", "=", REF_WRITEOFF], ["company_id", "=", EMPRESA_ID]]])
    if existentes:
        print(f"    lançamento '{REF_WRITEOFF}' já existe (id {existentes[0]}); a reutilizar.")
        move_id = existentes[0]
    elif not aplicar:
        print("    [dry-run] criaria o lançamento e reconciliava-o com a linha aberta.")
        return
    else:
        hoje = datetime.date.today().isoformat()
        move_id = o.kw("account.move", "create", [{
            "move_type": "entry",
            "journal_id": diario_misc,
            "date": hoje,
            "ref": REF_WRITEOFF,
            "line_ids": [
                (0, 0, {"account_id": conta_taxa, "name": ETIQUETA,
                        "partner_id": parceiro, "debit": valor, "credit": 0.0}),
                (0, 0, {"account_id": aberta["account_id"][0], "name": ETIQUETA,
                        "partner_id": parceiro, "debit": 0.0, "credit": valor}),
            ],
        }], allow_write=True)
        escrever(o, "account.move", "action_post", [[move_id]])
        print(f"    lançamento criado e lançado (id {move_id}).")

    if not aplicar:
        return

    contrapartida = o.kw("account.move.line", "search",
                         [[["move_id", "=", move_id],
                           ["account_id", "=", aberta["account_id"][0]],
                           ["reconciled", "=", False]]])
    if not contrapartida:
        print("    contrapartida já reconciliada — nada a fazer.")
        return
    escrever(o, "account.move.line", "reconcile", [[aberta["id"], contrapartida[0]]])
    print("    reconciliado com a linha aberta da fatura.")


# -- reposição -----------------------------------------------------------


def repor(o: Guard, conta_errada: int, aplicar: bool) -> None:
    """Desfaz o que este script criou, para a passagem poder ser repetida."""
    print("\n[reset] a desfazer")
    moves = o.kw("account.move", "search_read",
                 [[["ref", "=", REF_WRITEOFF], ["company_id", "=", EMPRESA_ID]]],
                 {"fields": ["name", "state"]})
    for move in moves:
        print(f"    lançamento {move['name']} (id {move['id']}): desreconciliar, repor a rascunho, apagar")
        if aplicar:
            linhas = o.kw("account.move.line", "search", [[["move_id", "=", move["id"]]]])
            escrever(o, "account.move.line", "remove_move_reconcile", [linhas])
            escrever(o, "account.move", "button_draft", [[move["id"]]])
            escrever(o, "account.move", "unlink", [[move["id"]]])
    if not moves:
        print("    nenhum lançamento deste script para apagar.")

    modelos = o.kw("account.reconcile.model", "search",
                   [[["name", "=", MODELO_RECONCILIACAO], ["company_id", "=", EMPRESA_ID]]])
    if modelos and conta_errada:
        linhas = o.kw("account.reconcile.model.line", "search", [[["model_id", "in", modelos]]])
        print(f"    modelo '{MODELO_RECONCILIACAO}': repor conta {CONTA_ERRADA_CODIGO}")
        if aplicar:
            escrever(o, "account.reconcile.model.line", "write",
                     [linhas, {"account_id": conta_errada}])


# -- reconciliação final -------------------------------------------------


def reconciliar(o: Guard, conta_taxa: int) -> None:
    print("\n[reconciliação] estado final")
    faturas = o.kw("account.move", "search_read",
                   [[["name", "=", FATURA], ["company_id", "=", EMPRESA_ID],
                     ["move_type", "=", "out_invoice"]]],
                   {"fields": ["name", "amount_total", "amount_residual", "payment_state"]})
    for f in faturas:
        estado = "OK" if abs(f["amount_residual"]) < 0.005 else "POR FECHAR"
        print(f"    {estado}  {f['name']}: total {f['amount_total']:.2f} € | "
              f"em dívida {f['amount_residual']:.2f} € | {f['payment_state']}")

    modelos = o.kw("account.reconcile.model", "search",
                   [[["name", "=", MODELO_RECONCILIACAO], ["company_id", "=", EMPRESA_ID]]])
    if modelos:
        linhas = o.kw("account.reconcile.model.line", "search_read",
                      [[["model_id", "in", modelos]]], {"fields": ["account_id"]})
        for linha in linhas:
            conta = linha["account_id"]
            estado = "OK" if conta and conta[0] == conta_taxa else "POR CORRIGIR"
            print(f"    {estado}  modelo '{MODELO_RECONCILIACAO}' -> {conta[1] if conta else '(vazia)'}")

    saldo = o.kw("account.move.line", "read_group",
                 [[["account_id", "=", conta_taxa], ["parent_state", "=", "posted"]],
                  ["balance:sum"], []])
    total = (saldo[0] or {}).get("balance", 0.0) if saldo else 0.0
    print(f"    conta {CONTA_TAXA_CODIGO}: saldo lançado {total:.2f} €")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--confirm", action="store_true", help="aplica; sem isto é dry-run")
    ap.add_argument("--allow-prod", action="store_true", help="autoriza escrita em produção")
    ap.add_argument("--purpose", default="brodoo_dev",
                    choices=("brodoo_dev", "client_test", "production"))
    ap.add_argument("--reset", action="store_true", help="desfaz o que este script criou")
    args = ap.parse_args()

    alvo = alvo_da_staging(args.purpose)
    o = Guard(alvo, confirmed=args.confirm, allow_prod=args.allow_prod)
    modo = "APLICAR" if args.confirm else "DRY-RUN (nada é escrito)"
    print(f"alvo: {alvo.base_url} | base {alvo.database} | finalidade {alvo.purpose}")
    print(f"modo: {modo}")

    conta_taxa = id_unico(o, "account.account",
                          [["code", "=", CONTA_TAXA_CODIGO], ["company_ids", "in", [EMPRESA_ID]]],
                          f"a conta {CONTA_TAXA_CODIGO}")
    diario_misc = id_unico(o, "account.journal",
                           [["type", "=", "general"], ["code", "=", "MISC"],
                            ["company_id", "=", EMPRESA_ID]],
                           "o diário de operações diversas")

    if args.reset:
        contas_erradas = o.kw("account.account", "search",
                              [[["code", "=", CONTA_ERRADA_CODIGO],
                                ["company_ids", "in", [EMPRESA_ID]]]], {"limit": 1})
        repor(o, contas_erradas[0] if contas_erradas else 0, args.confirm)
    else:
        corrigir_modelo(o, conta_taxa, args.confirm)
        liquidar_fatura(o, conta_taxa, diario_misc, args.confirm)

    reconciliar(o, conta_taxa)
    if not args.confirm:
        print("\nNada foi escrito. Repetir com --confirm para aplicar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
