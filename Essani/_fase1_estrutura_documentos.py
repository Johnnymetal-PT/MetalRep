#!/usr/bin/env python3
r"""
Estrutura da pasta de documentos de artigo (Essani).

O que cria: a pasta `Artigos`, uma sub-pasta por familia de produto que tenha
documentos, e as duas etiquetas de tipo que faltavam. Nada mais.

O QUE NAO FAZ, E PORQUE — isto e o essencial deste ficheiro:

  Nao copia para a pasta os documentos que ja estao nos artigos. Testou-se, e o
  resultado foi o pior possivel: `documents.document` e `product.document` podem
  apontar ao mesmo `ir.attachment`, e apagar o documento da pasta **destruiu o
  anexo e, com ele, o documento do artigo**. A pasta passaria a ser um sitio onde
  arrumar ficheiros apaga fichas tecnicas do catalogo.

  Os atalhos (`shortcut_document_id`) sao seguros — apagar o atalho nao toca no
  original, e apagar o original nao toca no documento do artigo — mas so apontam
  para documentos da propria pasta. Para os usar seria preciso criar primeiro 672
  copias, que e o problema de volta noutra forma.

  Por isso os documentos do catalogo ficam onde estao: no artigo, que e de onde o
  site os le e de onde seguem nos orcamentos. A pasta serve o que nasce nela.

Idempotente. Dry-run por defeito; escrita exige --confirm e, em producao,
--allow-prod. Conta os documentos antes e depois: se o numero mudar, avisa.
"""
import argparse, sys
sys.path.insert(0, "/Users/laracunha/Documents/Parametro/_pg_template/scripts")
from pg_odoo_migration_guard import Guard, resolver_alvo, resolver_alvo_por_projeto

PROJECT_KEY = "web-essani-intranet-extranet"
NOME_PASTA = "Artigos"
ETIQUETAS_NOVAS = ["Product > Certificates", "Product > Manuals"]


def familias_com_documentos(kw):
    """Familias de primeiro nivel que tem documentos em artigos ativos."""
    cats = {c["id"]: c for c in kw("product.category", "search_read",
                                   [[], ["complete_name"]], {"limit": 0})}

    def familia(cid):
        partes = (cats.get(cid, {}).get("complete_name") or "").split(" / ")
        if len(partes) > 1 and partes[0] == "All":
            return partes[1]
        return partes[0] if partes and partes[0] else None

    ativos = {t["id"]: familia(t["categ_id"][0]) if t["categ_id"] else None
              for t in kw("product.template", "search_read", [[], ["categ_id"]], {"limit": 0})}
    contagem = {}
    for d in kw("product.document", "search_read",
                [[["res_model", "=", "product.template"]], ["res_id"]], {"limit": 0}):
        fam = ativos.get(d["res_id"])
        if fam:
            contagem[fam] = contagem.get(fam, 0) + 1
    return dict(sorted(contagem.items(), key=lambda x: -x[1]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--allow-prod", action="store_true")
    p.add_argument("--conn", help="ficheiro de ligacao, para apontar a staging")
    a = p.parse_args()
    alvo = resolver_alvo(a.conn) if a.conn else resolver_alvo_por_projeto(
        PROJECT_KEY, "production")
    g = Guard(alvo, confirmed=a.confirm, allow_prod=a.allow_prod)
    kw = g.kw
    escrever = a.confirm and (a.allow_prod or alvo.purpose != "production")
    print("alvo: %s | base=%s | finalidade=%s" % (alvo.base_url, alvo.database, alvo.purpose))
    print("modo: %s\n" % ("ESCRITA" if escrever else "DRY-RUN"))

    # Testemunha: nenhum documento de artigo pode desaparecer por causa disto.
    antes_pd = kw("product.document", "search_count", [[]])
    antes_dd = kw("documents.document", "search_count", [[]])
    print("antes: %d documentos de artigo | %d documentos na app Documentos"
          % (antes_pd, antes_dd))

    raiz = kw("documents.document", "search_read",
              [[["type", "=", "folder"], ["name", "in", ["Products", NOME_PASTA]],
                ["folder_id", "=", False]], ["id", "name"]])
    if not raiz:
        print("ABORTADO: nao existe a pasta de artigos. Ativar Definicoes > Documentos > Produto.")
        return
    raiz = raiz[0]
    print("\n=== Passo 1: nome da pasta ===")
    if raiz["name"] != NOME_PASTA:
        print("  * renomear '%s' -> '%s' (id=%s)" % (raiz["name"], NOME_PASTA, raiz["id"]))
        if escrever:
            kw("documents.document", "write", [[raiz["id"]], {"name": NOME_PASTA}],
               allow_write=True)
    else:
        print("  = ja se chama '%s'" % NOME_PASTA)

    print("\n=== Passo 2: sub-pastas por familia ===")
    familias = familias_com_documentos(kw)
    existentes = {f["name"]: f["id"] for f in kw("documents.document", "search_read",
                  [[["type", "=", "folder"], ["folder_id", "=", raiz["id"]]], ["id", "name"]])}
    criar = [(f, n) for f, n in familias.items() if f not in existentes]
    print("  familias com documentos: %d | sub-pastas ja existentes: %d | a criar: %d"
          % (len(familias), len(existentes), len(criar)))
    for fam, n in criar:
        print("     * %-46s (%d documentos no artigo)" % (fam[:46], n))
    if criar and escrever:
        for fam, _ in criar:
            kw("documents.document", "create",
               [{"name": fam, "type": "folder", "folder_id": raiz["id"]}], allow_write=True)
        n = kw("documents.document", "search_count",
               [[["type", "=", "folder"], ["folder_id", "=", raiz["id"]]]])
        print("  reconciliacao: %d sub-pastas (esperado %d)" % (n, len(familias)))

    print("\n=== Passo 3: etiquetas de tipo ===")
    for etiqueta in ETIQUETAS_NOVAS:
        if kw("documents.tag", "search_count", [[["name", "=", etiqueta]]]):
            print("  = existe: %s" % etiqueta)
        else:
            print("  * a criar: %s" % etiqueta)
            if escrever:
                kw("documents.tag", "create", [{"name": etiqueta}], allow_write=True)

    print("\n=== Testemunha final ===")
    depois_pd = kw("product.document", "search_count", [[]])
    print("  documentos de artigo: %d -> %d  %s"
          % (antes_pd, depois_pd,
             "INALTERADO" if depois_pd == antes_pd else ">>> MUDOU, INVESTIGAR <<<"))
    print("  documentos na app Documentos: %d -> %d (pastas novas contam aqui)"
          % (antes_dd, kw("documents.document", "search_count", [[]])))


if __name__ == "__main__":
    main()
