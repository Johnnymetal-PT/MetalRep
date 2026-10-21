#!/usr/bin/env python3
"""Arruma o portugues que esta guardado debaixo da chave da lingua-base.

O QUE SE PASSA
--------------
No Odoo 19 um campo traduzivel e uma coluna jsonb com uma chave por lingua. Na base
da Essani ha milhares de valores sem chave `pt_PT` — mas o texto que la esta, na
chave `en_US`, ja e portugues:

    CONNECT, 2X TOMADAS + 1X USB A+C CR
    Preto
    Branco

O site mostra-os em portugues por *fallback*, e por isso parece que esta tudo bem.
Nao esta: qualquer escrita futura na lingua-base passa a aparecer no site portugues,
que foi exactamente a armadilha apanhada em agosto nos nomes de produto. Escrever o
`pt_PT` explicitamente fecha essa porta.

Nao e trabalho de traducao, e de arrumacao.

O QUE NAO SE MEXE
-----------------
Boa parte dos valores sem `pt_PT` sao referencias — `EFP2.12651.2700-05`,
`EF22.12-V1-4000`, `IP65`. Essas nao se traduzem nem se copiam: sem chave `pt_PT` o
*fallback* mostra o codigo, que e o que se quer. Copia-las so acrescentava ruido e
escondia, no futuro, o que falta mesmo traduzir.

A lingua-base NUNCA e escrita. Este script so escreve `pt_PT`, e so onde essa chave
nao existe de todo — nunca por cima de uma traducao que alguem ja fez.

USO (no shell da build: `odoo-bin shell`)
-----------------------------------------
    exec(open('/home/odoo/src/user/scripts/pg_arrumar_traducoes_pt.py').read())
    censo(env)              # so le e conta
    aplicar(env)            # escreve, depois de pedir confirmacao

Correr o `censo` depois do `aplicar` nao e cerimonia: a primeira versao usava `write`
e falhou em silencio num dos quatro modelos, dizendo "223 arrumados" com os 223 por
arrumar. Confirmar que ficou a zero e o que apanha isso.
"""

import re

BASE = "en_US"
DESTINO = "pt_PT"

ALVOS = [
    ("product.attribute.value", "name"),
    ("product.template", "name"),
    ("product.attribute", "name"),
    ("product.public.category", "name"),
]

# Uma referencia nao tem espacos e nao tem minusculas: 'EF22.12-V1-4000', 'IP65'.
# 'Preto' tem minusculas -> texto. 'CONNECT, 2X TOMADAS' tem espacos -> texto.
PADRAO_REFERENCIA = re.compile(r"^[A-Z0-9][A-Z0-9._/+\-]*$")


def e_referencia(texto):
    texto = (texto or "").strip()
    return bool(texto) and bool(PADRAO_REFERENCIA.match(texto))


def _por_arrumar(env, modelo, campo):
    """Registos com valor na lingua-base e sem chave na lingua de destino."""
    tabela = env[modelo]._table
    env.cr.execute(
        f"select id, {campo}->>%s from {tabela} "
        f"where {campo} is not null and not ({campo} ? %s)",
        (BASE, DESTINO),
    )
    return [(rid, valor) for rid, valor in env.cr.fetchall() if valor]


def censo(env):
    """So le e conta. Nao escreve nada."""
    total_texto = 0
    for modelo, campo in ALVOS:
        if modelo not in env:
            continue
        linhas = _por_arrumar(env, modelo, campo)
        textos = [(i, v) for i, v in linhas if not e_referencia(v)]
        referencias = len(linhas) - len(textos)
        total_texto += len(textos)
        print(f"{modelo}.{campo}")
        print(f"   sem {DESTINO} .......... {len(linhas)}")
        print(f"   a arrumar (texto) ..... {len(textos)}")
        print(f"   referencias (deixar) .. {referencias}")
        for _i, v in textos[:5]:
            print(f"      ex: {v[:70]}")
    print()
    print(f"TOTAL a arrumar: {total_texto}")
    print("(nada foi escrito — usar aplicar(env) para escrever)")
    return total_texto


def aplicar(env, confirmado=False):
    """Escreve o `pt_PT` com o texto que ja la esta na lingua-base."""
    if not confirmado:
        total = censo(env)
        print()
        print(f"Para escrever estes {total}, correr: aplicar(env, confirmado=True)")
        return 0

    escritos = 0
    for modelo, campo in ALVOS:
        if modelo not in env:
            continue
        linhas = [(i, v) for i, v in _por_arrumar(env, modelo, campo)
                  if not e_referencia(v)]
        if not linhas:
            continue
        Modelo = env[modelo].with_context(active_test=False)
        for rid, valor in linhas:
            registo = Modelo.browse(rid)
            if registo.exists():
                # `write` com lang=pt_PT NAO serve aqui, e foi assim que a primeira
                # passagem falhou nos nomes de produto sem dar erro. O ORM descarta
                # escritas cujo valor seja igual ao que o registo ja mostra naquela
                # lingua (`_filter_not_equal`, odoo/orm/fields_textual.py) — e o que
                # ele mostra em pt_PT e precisamente o valor da lingua-base, por
                # fallback. Escrever "o mesmo" e, para o ORM, nao escrever nada.
                # `_update_field_translations` e a API que existe para isto e nao
                # passa por esse filtro.
                registo._update_field_translations(campo, {DESTINO: valor})
                escritos += 1
        print(f"{modelo}.{campo}: {len(linhas)} arrumados")
    env.cr.commit()
    print(f"\nFeito: {escritos} valores com {DESTINO} proprio. "
          f"A lingua-base nao foi tocada.")
    return escritos
