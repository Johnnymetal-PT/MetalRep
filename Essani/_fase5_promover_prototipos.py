#!/usr/bin/env python3
r"""
Promoção do módulo pg_prototipos para produção.

O módulo substitui o que foi construído à mão durante a configuração. Se as duas
camadas ficarem activas ao mesmo tempo, o gestor de projeto recebe cada alteração
de especificação em duplicado e o formulário do protótipo mostra dois pares de
campos iguais. Daí este script: instala o módulo e desliga a camada anterior, por
esta ordem e só depois de confirmar que a migração correu.

O que desativa (nunca apaga — tudo reversível):
  - a regra de automatização do circuito de alterações, substituída pelo override
    de `write()` em product.template;
  - a ação de servidor "nova versão", substituída pelo botão do módulo;
  - a vista herdada criada por API, que mostra os campos manuais `x_pg_*`.

O que NÃO toca: os campos manuais `x_pg_artigo_prototipo` e `x_pg_versao_origem`.
Campos manuais não têm indicador de arquivo — desativá-los seria apagá-los, e os
valores originais são a única prova de que a migração está certa. Ficam como estão;
removem-se noutro dia, com a migração confirmada há tempo suficiente.

Idempotente. Dry-run por defeito; escrita exige --confirm e --allow-prod.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
MODULO = "pg_prototipos"
NOME_REGRA = "PG Protótipos: alteração de especificações → gestor de projeto"
NOME_ACAO = "PG Protótipos: nova versão"
NOME_VISTA = "pg.project.prototipo.ligacao"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--allow-prod", action="store_true")
    p.add_argument("--conn", help="ficheiro de ligação, para ensaiar noutra base")
    a = p.parse_args()
    alvo = resolver_alvo(a.conn) if a.conn else resolver_alvo_por_projeto(
        PROJECT_KEY, "production")
    g = Guard(alvo, confirmed=a.confirm, allow_prod=a.allow_prod)
    kw = g.kw
    escrever = a.confirm and (a.allow_prod or alvo.purpose != "production")
    print("alvo: %s | base=%s | finalidade=%s" % (alvo.base_url, alvo.database, alvo.purpose))
    print("modo: %s\n" % ("ESCRITA" if escrever else "DRY-RUN"))

    # ---- Passo 1: instalar ----
    print("=== Passo 1: instalar %s ===" % MODULO)
    mods = kw("ir.module.module", "search_read",
              [[["name", "=", MODULO]], ["id", "state"]],
              {"context": {"active_test": False}})
    if not mods:
        print("  módulo não consta da lista. A atualizar...")
        if not escrever:
            print("  (dry-run) faria update_list; sem isso não se sabe o resto.")
            return
        kw("ir.module.module", "update_list", [], allow_write=True)
        mods = kw("ir.module.module", "search_read",
                  [[["name", "=", MODULO]], ["id", "state"]],
                  {"context": {"active_test": False}})
        if not mods:
            print("  ABORTADO: o código ainda não chegou a esta base. "
                  "Confirmar que a branch foi publicada e o build terminou.")
            return
    modulo = mods[0]
    print("  estado: %s" % modulo["state"])
    if modulo["state"] != "installed":
        print("  * a instalar")
        if escrever:
            kw("ir.module.module", "button_immediate_install", [[modulo["id"]]],
               allow_write=True)
            print("  instalado: %s" % kw("ir.module.module", "read",
                  [[modulo["id"]], ["state"]])[0]["state"])
    else:
        print("  = já instalado")

    # ---- Passo 2: a migração correu? ----
    # Sem isto, desligar a camada antiga podia deixar protótipos sem ligação e
    # ninguem dava por falta ate alguem procurar o artigo de um projeto.
    print("\n=== Passo 2: verificar a migração ===")
    try:
        antigos = kw("project.project", "search_count",
                     [[["x_pg_artigo_prototipo", "!=", False]]],
                     {"context": {"active_test": False}})
        novos = kw("project.project", "search_count",
                   [[["pg_artigo_prototipo", "!=", False]]],
                   {"context": {"active_test": False}})
    except Exception as erro:
        print("  não foi possível comparar (%s)." % str(erro)[:90])
        print("  ABORTADO: sem esta prova não desligo a camada anterior.")
        return
    print("  projetos com o campo manual : %d" % antigos)
    print("  projetos com o campo novo   : %d" % novos)
    if novos < antigos:
        print("  ABORTADO: a migração não cobriu tudo. Nada será desativado.")
        return
    print("  migração coberta.")

    # ---- Passo 3: desligar a camada anterior ----
    print("\n=== Passo 3: desativar o que o módulo substitui ===")
    for modelo, dominio, etiqueta in (
        ("base.automation", [["name", "=", NOME_REGRA]], "regra de alterações"),
        ("ir.actions.server", [["name", "=", NOME_ACAO]], "ação nova versão"),
        ("ir.ui.view", [["name", "=", NOME_VISTA]], "vista dos campos manuais"),
    ):
        regs = kw(modelo, "search_read", [dominio, ["id", "active"]],
                  {"context": {"active_test": False}})
        if not regs:
            print("  %-26s não existe — nada a fazer" % etiqueta)
            continue
        ativos = [r["id"] for r in regs if r["active"]]
        if not ativos:
            print("  %-26s já desativada" % etiqueta)
            continue
        print("  %-26s * a desativar %s" % (etiqueta, ativos))
        if escrever:
            kw(modelo, "write", [ativos, {"active": False}], allow_write=True)
            resta = kw(modelo, "search_count", [dominio + [["active", "=", True]]])
            print("  %-26s reconciliação: activos = %d (esperado 0)" % ("", resta))

    print("\n  Os campos manuais x_pg_* ficam como estão, de propósito: são a prova")
    print("  de que a migração está certa e não têm indicador de arquivo.")


if __name__ == "__main__":
    main()
