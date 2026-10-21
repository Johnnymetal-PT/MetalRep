#!/usr/bin/env python3
"""Ativa a manutenção interna standard na base de teste da Essani.

Instala apenas os módulos Odoo necessários ao piloto: ``maintenance`` para
equipamentos, pedidos preventivos/corretivos e recorrência, e
``maintenance_worksheet`` para fichas de execução personalizáveis.

Não cria zonas, equipamentos, responsáveis ou periodicidades fictícias. Esses
dados pertencem ao desenho operacional do cliente e são configurados depois da
validação do piloto.

Idempotente. Dry-run por omissão; escrita exige ``--confirm``. A finalidade
normal é ``brodoo_dev`` e nunca produção.
"""

import argparse
import sys

sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")

from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto


PROJECT_KEY = "web-essani-intranet-extranet"
MODULOS = ("maintenance", "maintenance_worksheet")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--conn", help="ficheiro de ligação para uma base de teste")
    args = parser.parse_args()

    alvo = (
        resolver_alvo(args.conn)
        if args.conn
        else resolver_alvo_por_projeto(PROJECT_KEY, "brodoo_dev")
    )
    if alvo.purpose == "production":
        raise SystemExit("ABORTADO: este piloto só pode ser instalado numa base de teste.")

    guard = Guard(alvo, confirmed=args.confirm)
    kw = guard.kw
    print(
        "alvo: %s | base=%s | finalidade=%s"
        % (alvo.base_url, alvo.database, alvo.purpose)
    )
    print("modo: %s\n" % ("ESCRITA" if args.confirm else "DRY-RUN"))

    encontrados = kw(
        "ir.module.module",
        "search_read",
        [[['name', 'in', list(MODULOS)]], ['id', 'name', 'state']],
        {"context": {"active_test": False}},
    )
    por_nome = {modulo["name"]: modulo for modulo in encontrados}
    em_falta = [nome for nome in MODULOS if nome not in por_nome]
    if em_falta:
        raise SystemExit(
            "ABORTADO: módulos ausentes da lista da base: %s" % ", ".join(em_falta)
        )

    for nome in MODULOS:
        modulo = por_nome[nome]
        print("%-24s estado inicial: %s" % (nome, modulo["state"]))
        if modulo["state"] == "installed":
            print("%-24s = já instalado" % nome)
            continue
        print("%-24s * a instalar" % nome)
        if args.confirm:
            kw(
                "ir.module.module",
                "button_immediate_install",
                [[modulo["id"]]],
                allow_write=True,
            )

    finais = kw(
        "ir.module.module",
        "search_read",
        [[['name', 'in', list(MODULOS)]], ['name', 'state']],
        {"context": {"active_test": False}},
    )
    estados = {modulo["name"]: modulo["state"] for modulo in finais}
    print("\n=== Reconciliação ===")
    for nome in MODULOS:
        esperado = "installed" if args.confirm else por_nome[nome]["state"]
        print("%-24s %s (esperado: %s)" % (nome, estados.get(nome), esperado))
    if args.confirm and any(estados.get(nome) != "installed" for nome in MODULOS):
        raise SystemExit("ABORTADO: a instalação não ficou reconciliada.")


if __name__ == "__main__":
    main()
