#!/usr/bin/env python3
"""
Converte o rascunho markdown de um email ao cliente em HTML colável no Odoo.

O problema que resolve: colar markdown no compositor do Odoo não produz
formatação — os `**`, `-` e `|` chegam como texto literal e obrigam a formatar
tudo à mão. Este script produz o HTML que o editor do Odoo aceita, para a
colagem ficar formatada sem edição posterior.

Porque é que o HTML sai **sem CSS**:
o editor do Odoo filtra tudo o que é colado contra uma lista branca. Só
sobrevivem as etiquetas de `CLIPBOARD_WHITELISTS.nodes` e os atributos
`class`, `href`, `src` e `target` — o atributo `style` é sempre removido, tal
como as etiquetas `<div>`, `<span>`, `<hr>` e `<code>`. Evidência (idêntica em
Odoo 17, 18 e 19):

- Odoo 19: `addons/html_editor/static/src/core/clipboard_plugin.js`
  (`CLIPBOARD_WHITELISTS`, `cleanForPaste`)
- Odoo 17/18: `addons/web_editor/static/src/js/editor/odoo-editor/src/OdooEditor.js`
  (mesmas constantes)

Logo, qualquer tentativa de fixar tipos de letra, cores ou margens no HTML é
trabalho perdido: o Odoo deita fora o `style` e aplica a sua própria folha de
estilo. É isso que se quer — o email fica com o aspecto nativo do Odoo.

Uso:
    python pg_build_email_cliente.py --md email.md                # escreve email.html
    python pg_build_email_cliente.py --md email.md --fragmento    # só o HTML colável (stdout)
    python pg_build_email_cliente.py --md email.md --texto        # alternativa em texto simples

O assunto e os destinatários vêm de um bloco de cabeçalho opcional no topo do
`.md` (delimitado por `---`) ou, em alternativa, de uma primeira linha
`Assunto:` / `**Assunto:**`. Nunca entram no corpo colável.

O fecho e a assinatura são **retirados** do corpo: o compositor do Odoo insere a
assinatura do utilizador (`res.users.signature`), que já traz saudação de fecho,
nome, cargo e rodapé da marca. Repeti-los obrigava a apagá-los à mão em cada
envio. `--manter-assinatura` mantém-nos, para destinos sem assinatura configurada.

Sem dependências externas. Mesmo markdown => mesmo HTML, byte a byte.
"""

from __future__ import annotations

import argparse
import html as _html
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# Lista branca do editor do Odoo (ver evidência na docstring do módulo)
# ---------------------------------------------------------------------------

TAGS_PERMITIDAS = frozenset(
    """
    p h1 h2 h3 h4 h5 h6 blockquote pre
    ul ol li
    i b u s em font strong
    table thead th tbody tr td
    img br a
    """.split()
)

ATRIBUTOS_PERMITIDOS = frozenset({"class", "href", "src", "target"})

CLASSES_PERMITIDAS = frozenset(
    {
        "table", "table-bordered", "o_table",
        "oe-nested", "o_checklist", "o_checked",
        "d-block", "mx-auto", "img-fluid", "img-thumbnail",
        "rounded", "rounded-circle",
    }
)

CLASSES_PERMITIDAS_PREFIXO = ("float-", "padding-", "shadow", "text-o-", "bg-o-", "btn", "fa")

ESQUEMAS_URL_PERMITIDOS = ("http://", "https://", "mailto:", "tel:", "#", "/")
ESQUEMAS_URL_PROIBIDOS = ("javascript:", "data:", "vbscript:", "file:")

CHAVES_CABECALHO = ("assunto", "para", "cc", "bcc")

# Etiquetas cruas que o autor pode escrever no markdown e que passam intactas
# (sem atributos, por isso não há nada para sanear).
TAGS_CRUAS_PERMITIDAS = ("br", "b", "strong", "i", "em", "u", "s")


# ---------------------------------------------------------------------------
# Expressões do markdown suportado
# ---------------------------------------------------------------------------

_RE_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_RE_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+(.*)$")
_RE_CITACAO = re.compile(r"^\s*>\s?(.*)$")
_RE_CERCA = re.compile(r"^\s*(```|~~~)\s*[\w+-]*\s*$")
_RE_REGUA = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
_RE_SEPARADOR_TABELA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_RE_ASSUNTO_SOLTO = re.compile(r"^\s*\**\s*assunto\s*\**\s*:\s*\**\s*(.+?)\s*\**\s*$", re.I)

_RE_CODIGO = re.compile(r"`([^`]+)`")
_RE_LINK = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+)\s*\)")
_RE_TAG_CRUA = re.compile(r"<(/?)(%s)\s*/?>" % "|".join(TAGS_CRUAS_PERMITIDAS), re.I)
_RE_NEGRITO_A = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.S)
_RE_NEGRITO_B = re.compile(r"__(?=\S)(.+?)(?<=\S)__", re.S)
_RE_ITALICO_A = re.compile(r"(?<![\w*])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![\w*])")
_RE_ITALICO_B = re.compile(r"(?<![\w_])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w_])")
_RE_RISCADO = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.S)
_RE_PLACEHOLDER = re.compile(r"\[([A-Za-zÀ-ÿ][^\]\n]{1,60})\](?!\()")

# Fecho do email. O compositor do Odoo acrescenta a assinatura do utilizador
# (`res.users.signature`), que já traz a saudação de fecho, o nome, o cargo e o
# rodapé da marca — repetir isso no corpo obriga a apagar à mão em cada envio.
_RE_FECHO = re.compile(
    r"^(com (os )?melhores cumprimentos|melhores cumprimentos|cumprimentos"
    r"|atentamente|com (os )?melhores votos|com estima|best regards"
    r"|kind regards|warm regards|regards)\s*[,.!]?$",
    re.I,
)
_RE_SEPARADOR_ASSINATURA = re.compile(r"^--\s?$")
_MAX_LINHAS_ASSINATURA = 10

_RE_MARCA = re.compile("\x00(\\d+)\x00")


# ---------------------------------------------------------------------------
# Resultado e recolha de avisos
# ---------------------------------------------------------------------------


@dataclass
class Resultado:
    """Tudo o que o conversor produz a partir de um `.md`."""

    fragmento: str = ""
    texto: str = ""
    cabecalho: dict = field(default_factory=dict)
    avisos: list = field(default_factory=list)

    @property
    def assunto(self) -> str:
        return self.cabecalho.get("assunto", "")


class _Contexto:
    """Acumula avisos sem os repetir para o mesmo motivo."""

    def __init__(self) -> None:
        self.avisos: list = []
        self._vistos: set = set()

    def avisar(self, motivo: str, mensagem: str) -> None:
        if motivo in self._vistos:
            return
        self._vistos.add(motivo)
        self.avisos.append(mensagem)


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def _escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _limpar_url(url: str, ctx: _Contexto) -> str | None:
    """Devolve o URL pronto para `href`, ou `None` se não for aceitável."""
    valor = url.strip()
    baixo = valor.lower()
    if baixo.startswith(ESQUEMAS_URL_PROIBIDOS):
        ctx.avisar(
            "url-proibido",
            "Link com esquema não permitido removido (mantido apenas o texto): %s" % valor,
        )
        return None
    if not baixo.startswith(ESQUEMAS_URL_PERMITIDOS):
        if "@" in valor and " " not in valor:
            valor = "mailto:" + valor
        elif re.match(r"^[\w.-]+\.[a-z]{2,}(/|$)", baixo):
            valor = "https://" + valor
        else:
            ctx.avisar(
                "url-relativo",
                "Link sem esquema mantido como está ('%s'); num email só funciona URL absoluto." % valor,
            )
    return _html.escape(valor, quote=True)


# ---------------------------------------------------------------------------
# Conversão de texto corrido (inline)
# ---------------------------------------------------------------------------


def _inline(texto: str, ctx: _Contexto) -> str:
    """Converte a marcação de texto corrido, preservando o que já é HTML válido."""
    guardados: list = []

    def guardar(fragmento: str) -> str:
        guardados.append(fragmento)
        return "\x00%d\x00" % (len(guardados) - 1)

    def _codigo(m: "re.Match") -> str:
        ctx.avisar(
            "codigo-inline",
            "`código` entre crases fica texto simples: a etiqueta <code> não sobrevive à colagem no Odoo.",
        )
        return guardar(_escapar(m.group(1)))

    texto = _RE_CODIGO.sub(_codigo, texto)

    def _link(m: "re.Match") -> str:
        etiqueta = _inline(m.group(1), ctx) or _escapar(m.group(2))
        url = _limpar_url(m.group(2), ctx)
        if url is None:
            return guardar(etiqueta)
        return guardar('<a href="%s" target="_blank">%s</a>' % (url, etiqueta))

    texto = _RE_LINK.sub(_link, texto)

    def _tag_crua(m: "re.Match") -> str:
        fecho, nome = m.group(1), m.group(2).lower()
        if nome == "br":
            return guardar("<br>")
        return guardar("</%s>" % nome if fecho else "<%s>" % nome)

    texto = _RE_TAG_CRUA.sub(_tag_crua, texto)

    if re.search(r"<[a-zA-Z/!][^>]*>", texto):
        ctx.avisar(
            "html-cru",
            "HTML no markdown que não está na lista de etiquetas aceites foi escapado e vai aparecer como texto.",
        )

    for m in _RE_PLACEHOLDER.finditer(texto):
        rotulo = m.group(1)
        if rotulo[:1].isupper():
            ctx.avisar(
                "placeholder",
                "Ficou um marcador de template por preencher no corpo (ex.: [%s])." % rotulo,
            )
            break

    texto = _escapar(texto)

    texto = _RE_NEGRITO_A.sub(r"<strong>\1</strong>", texto)
    texto = _RE_NEGRITO_B.sub(r"<strong>\1</strong>", texto)
    texto = _RE_RISCADO.sub(r"<s>\1</s>", texto)
    texto = _RE_ITALICO_A.sub(r"<em>\1</em>", texto)
    texto = _RE_ITALICO_B.sub(r"<em>\1</em>", texto)

    return _RE_MARCA.sub(lambda m: guardados[int(m.group(1))], texto)


def _inline_texto(texto: str) -> str:
    """Versão em texto simples da mesma linha, para a alternativa `text/plain`."""
    texto = _RE_CODIGO.sub(r"\1", texto)
    texto = _RE_LINK.sub(lambda m: "%s (%s)" % (m.group(1), m.group(2)), texto)
    texto = _RE_TAG_CRUA.sub("", texto)
    texto = _RE_NEGRITO_A.sub(r"\1", texto)
    texto = _RE_NEGRITO_B.sub(r"\1", texto)
    texto = _RE_RISCADO.sub(r"\1", texto)
    texto = _RE_ITALICO_A.sub(r"\1", texto)
    texto = _RE_ITALICO_B.sub(r"\1", texto)
    return texto


# ---------------------------------------------------------------------------
# Cabeçalho (assunto e destinatários)
# ---------------------------------------------------------------------------


def _extrair_cabecalho(linhas: list, ctx: _Contexto) -> tuple:
    """Retira do topo o bloco de metadados, se existir. Devolve (cabecalho, linhas)."""
    cabecalho: dict = {}
    indice = 0
    while indice < len(linhas) and not linhas[indice].strip():
        indice += 1

    if indice < len(linhas) and linhas[indice].strip() == "---":
        fim = None
        for j in range(indice + 1, len(linhas)):
            if linhas[j].strip() in ("---", "..."):
                fim = j
                break
            if not linhas[j].strip():
                continue
            if ":" not in linhas[j]:
                break
        if fim is not None:
            for linha in linhas[indice + 1 : fim]:
                if not linha.strip():
                    continue
                chave, _, valor = linha.partition(":")
                chave = chave.strip().lower()
                if chave not in CHAVES_CABECALHO:
                    ctx.avisar(
                        "cabecalho-desconhecido",
                        "Chave de cabeçalho ignorada: '%s' (aceites: %s)."
                        % (chave, ", ".join(CHAVES_CABECALHO)),
                    )
                    continue
                cabecalho[chave] = valor.strip()
            return cabecalho, linhas[fim + 1 :]

    # Sem bloco de metadados: aceitar uma primeira linha "Assunto: ..."
    for j in range(indice, min(indice + 3, len(linhas))):
        if not linhas[j].strip():
            continue
        m = _RE_ASSUNTO_SOLTO.match(linhas[j])
        if m:
            cabecalho["assunto"] = m.group(1).strip()
            return cabecalho, linhas[:j] + linhas[j + 1 :]
        break

    ctx.avisar(
        "sem-assunto",
        "Sem assunto: acrescenta um bloco '---' no topo com 'assunto: ...' ou uma linha 'Assunto: ...'.",
    )
    return cabecalho, linhas


# ---------------------------------------------------------------------------
# Divisão em blocos
# ---------------------------------------------------------------------------


def _partir_em_blocos(linhas: list, ctx: _Contexto) -> list:
    """Devolve a lista de blocos como tuplos (tipo, conteúdo)."""
    blocos: list = []
    i = 0
    total = len(linhas)

    while i < total:
        linha = linhas[i]

        if not linha.strip():
            i += 1
            continue

        if _RE_CERCA.match(linha):
            cerca = _RE_CERCA.match(linha).group(1)
            corpo: list = []
            i += 1
            while i < total and not linhas[i].strip().startswith(cerca):
                corpo.append(linhas[i])
                i += 1
            i += 1  # cerca de fecho
            blocos.append(("codigo", corpo))
            continue

        if _RE_REGUA.match(linha):
            ctx.avisar(
                "regua",
                "Linhas '---' de separação foram removidas: <hr> não sobrevive à colagem no Odoo.",
            )
            i += 1
            continue

        m = _RE_TITULO.match(linha)
        if m:
            nivel = len(m.group(1))
            if nivel <= 2:
                ctx.avisar(
                    "titulo-grande",
                    "Título de nível %d convertido para <h%d>: num email o Odoo mostra-o muito grande; considera negrito."
                    % (nivel, nivel),
                )
            blocos.append(("titulo", (nivel, m.group(2))))
            i += 1
            continue

        if _RE_CITACAO.match(linha):
            corpo = []
            while i < total and _RE_CITACAO.match(linhas[i]):
                corpo.append(_RE_CITACAO.match(linhas[i]).group(1))
                i += 1
            blocos.append(("citacao", corpo))
            continue

        if _RE_ITEM.match(linha):
            itens: list = []
            while i < total:
                m_item = _RE_ITEM.match(linhas[i])
                if m_item:
                    indentacao = len(m_item.group(1).replace("\t", "    "))
                    ordenada = not m_item.group(2) in ("-", "*", "+")
                    itens.append([indentacao, ordenada, m_item.group(3)])
                    i += 1
                elif linhas[i].strip() and itens and linhas[i].startswith((" ", "\t")):
                    # continuação do item anterior
                    itens[-1][2] += "\n" + linhas[i].strip()
                    i += 1
                else:
                    break
            blocos.append(("lista", itens))
            continue

        if "|" in linha and i + 1 < total and _RE_SEPARADOR_TABELA.match(linhas[i + 1]):
            cabecalho = _celulas(linha)
            i += 2
            corpo = []
            while i < total and "|" in linhas[i] and linhas[i].strip():
                corpo.append(_celulas(linhas[i]))
                i += 1
            blocos.append(("tabela", (cabecalho, corpo)))
            continue

        paragrafo = []
        while i < total and linhas[i].strip():
            atual = linhas[i]
            if paragrafo and (
                _RE_TITULO.match(atual)
                or _RE_ITEM.match(atual)
                or _RE_CITACAO.match(atual)
                or _RE_CERCA.match(atual)
                or _RE_REGUA.match(atual)
            ):
                break
            paragrafo.append(atual.rstrip())
            i += 1
        blocos.append(("paragrafo", paragrafo))

    return blocos


def _remover_assinatura(blocos: list, ctx: _Contexto) -> list:
    """Corta o fecho e a assinatura no fim do corpo, porque o Odoo insere a sua.

    Só olha para a cauda do documento e só corta a partir de uma saudação de
    fecho (ou de um separador `--`), com a cauda limitada a poucas linhas de
    texto corrido. Conteúdo estruturado — listas, tabelas, títulos — trava a
    procura, para não haver forma de isto comer parágrafos com informação.
    """
    inicio = None
    linhas_cauda = 0

    for indice in range(len(blocos) - 1, -1, -1):
        tipo, conteudo = blocos[indice]
        if tipo != "paragrafo":
            break
        linhas_cauda += len(conteudo)
        if linhas_cauda > _MAX_LINHAS_ASSINATURA:
            break
        primeira = conteudo[0].strip() if conteudo else ""
        if _RE_SEPARADOR_ASSINATURA.match(primeira) or _RE_FECHO.match(primeira):
            inicio = indice
            break

    if inicio is None:
        return blocos

    removido = [
        linha.strip()
        for _, conteudo in blocos[inicio:]
        for linha in conteudo
        if linha.strip()
    ]
    ctx.avisar(
        "assinatura",
        "Fecho e assinatura retirados do corpo, porque o compositor do Odoo já insere a "
        "assinatura do utilizador: «%s». Para os manter, correr com -ManterAssinatura."
        % " | ".join(removido),
    )
    return blocos[:inicio]


def _celulas(linha: str) -> list:
    """Parte uma linha de tabela markdown nas suas células."""
    bruto = linha.strip()
    bruto = bruto.replace("\\|", "\x01")
    if bruto.startswith("|"):
        bruto = bruto[1:]
    if bruto.endswith("|"):
        bruto = bruto[:-1]
    return [c.strip().replace("\x01", "|") for c in bruto.split("|")]


# ---------------------------------------------------------------------------
# Renderização em HTML
# ---------------------------------------------------------------------------


def _render_lista(itens: list, ctx: _Contexto) -> str:
    """Constrói a lista respeitando o formato de aninhamento do Odoo (`li.oe-nested`)."""

    def construir(indice: int, nivel_ref: int) -> tuple:
        etiqueta = "ol" if itens[indice][1] else "ul"
        partes = ["<%s>" % etiqueta]
        while indice < len(itens):
            indentacao, ordenada, conteudo = itens[indice]
            if indentacao < nivel_ref:
                break
            if indentacao > nivel_ref:
                aninhada, indice = construir(indice, indentacao)
                partes.append('<li class="oe-nested">%s</li>' % aninhada)
                continue
            if ("ol" if ordenada else "ul") != etiqueta:
                break
            linhas_item = [l for l in conteudo.split("\n") if l.strip()]
            partes.append(
                "<li>%s</li>" % "<br>".join(_inline(l.strip(), ctx) for l in linhas_item)
            )
            indice += 1
        partes.append("</%s>" % etiqueta)
        return "".join(partes), indice

    html, _ = construir(0, itens[0][0] if itens else 0)
    return html


def _render_tabela(cabecalho: list, corpo: list, ctx: _Contexto) -> str:
    colunas = max([len(cabecalho)] + [len(l) for l in corpo]) if corpo else len(cabecalho)

    def linha_html(celulas: list, etiqueta: str) -> str:
        preenchidas = list(celulas) + [""] * (colunas - len(celulas))
        return "<tr>%s</tr>" % "".join(
            "<%s>%s</%s>" % (etiqueta, _inline(c, ctx), etiqueta) for c in preenchidas
        )

    partes = ['<table class="table table-bordered o_table">']
    if any(c.strip() for c in cabecalho):
        partes.append("<thead>%s</thead>" % linha_html(cabecalho, "th"))
    if corpo:
        partes.append("<tbody>%s</tbody>" % "".join(linha_html(l, "td") for l in corpo))
    partes.append("</table>")
    return "".join(partes)


def _render_blocos(blocos: list, ctx: _Contexto) -> str:
    saida: list = []
    for tipo, conteudo in blocos:
        if tipo == "paragrafo":
            saida.append("<p>%s</p>" % "<br>".join(_inline(l, ctx) for l in conteudo))
        elif tipo == "titulo":
            nivel, texto = conteudo
            saida.append("<h%d>%s</h%d>" % (nivel, _inline(texto, ctx), nivel))
        elif tipo == "lista":
            saida.append(_render_lista(conteudo, ctx))
        elif tipo == "citacao":
            saida.append(
                "<blockquote><p>%s</p></blockquote>"
                % "<br>".join(_inline(l, ctx) for l in conteudo)
            )
        elif tipo == "codigo":
            saida.append("<pre>%s</pre>" % _escapar("\n".join(conteudo)))
        elif tipo == "tabela":
            saida.append(_render_tabela(conteudo[0], conteudo[1], ctx))
    return "\n".join(saida)


def _render_texto(blocos: list) -> str:
    """Alternativa em texto simples, para quem colar num campo sem formatação."""
    saida: list = []
    for tipo, conteudo in blocos:
        if tipo == "paragrafo":
            saida.append("\n".join(_inline_texto(l) for l in conteudo))
        elif tipo == "titulo":
            saida.append(_inline_texto(conteudo[1]))
        elif tipo == "lista":
            linhas = []
            for indentacao, ordenada, texto in conteudo:
                marca = "1." if ordenada else "-"
                prefixo = " " * indentacao + marca + " "
                linhas.append(prefixo + _inline_texto(texto.replace("\n", " ")))
            saida.append("\n".join(linhas))
        elif tipo == "citacao":
            saida.append("\n".join("> " + _inline_texto(l) for l in conteudo))
        elif tipo == "codigo":
            saida.append("\n".join(conteudo))
        elif tipo == "tabela":
            cabecalho, corpo = conteudo
            linhas = [" | ".join(_inline_texto(c) for c in cabecalho)]
            linhas += [" | ".join(_inline_texto(c) for c in l) for l in corpo]
            saida.append("\n".join(linhas))
    return "\n\n".join(p for p in saida if p.strip()) + "\n"


# ---------------------------------------------------------------------------
# Validação contra a lista branca do Odoo
# ---------------------------------------------------------------------------


class _Validador(HTMLParser):
    """Confirma que o fragmento só usa o que sobrevive à colagem no Odoo."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.erros: list = []

    def handle_starttag(self, tag: str, atributos: list) -> None:
        if tag not in TAGS_PERMITIDAS:
            self.erros.append("etiqueta não permitida: <%s>" % tag)
        for nome, valor in atributos:
            if nome not in ATRIBUTOS_PERMITIDOS:
                self.erros.append("atributo não permitido: %s em <%s>" % (nome, tag))
            if nome == "class":
                for classe in (valor or "").split():
                    if classe in CLASSES_PERMITIDAS:
                        continue
                    if classe.startswith(CLASSES_PERMITIDAS_PREFIXO):
                        continue
                    self.erros.append("classe não permitida: %s em <%s>" % (classe, tag))

    def handle_startendtag(self, tag: str, atributos: list) -> None:
        self.handle_starttag(tag, atributos)


def validar_fragmento(fragmento: str) -> list:
    """Devolve a lista de violações da lista branca (vazia = pronto a colar)."""
    validador = _Validador()
    validador.feed(fragmento)
    validador.close()
    return validador.erros


# ---------------------------------------------------------------------------
# Ponto de entrada da conversão
# ---------------------------------------------------------------------------


def converter(markdown: str, manter_assinatura: bool = False) -> Resultado:
    """Converte o markdown do email no fragmento HTML colável no Odoo."""
    ctx = _Contexto()
    texto = markdown.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    linhas = texto.split("\n")

    cabecalho, linhas = _extrair_cabecalho(linhas, ctx)
    blocos = _partir_em_blocos(linhas, ctx)
    if not manter_assinatura:
        blocos = _remover_assinatura(blocos, ctx)

    fragmento = _render_blocos(blocos, ctx)
    erros = validar_fragmento(fragmento)
    if erros:
        raise SystemExit(
            "ERRO: o HTML gerado viola a lista branca do editor do Odoo:\n  - "
            + "\n  - ".join(erros)
        )

    return Resultado(
        fragmento=fragmento,
        texto=_render_texto(blocos),
        cabecalho=cabecalho,
        avisos=ctx.avisos,
    )


# ---------------------------------------------------------------------------
# Documento de pré-visualização
# ---------------------------------------------------------------------------

_CSS_PREVISUALIZACAO = """
:root { color-scheme: light dark; }
body { margin: 0; padding: 24px; background: #f4f6f8;
       font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; color: #111827; }
main { max-width: 760px; margin: 0 auto; }
.meta { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 16px 20px; margin-bottom: 8px; font-size: 13px; }
.meta h1 { font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
           color: #6b7280; margin: 0 0 10px; }
.meta dl { display: grid; grid-template-columns: 90px 1fr; gap: 4px 12px; margin: 0; }
.meta dt { color: #6b7280; } .meta dd { margin: 0; font-weight: 600; }
.avisos { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
          padding: 12px 20px; margin-bottom: 8px; font-size: 13px; color: #92400e; }
.avisos ul { margin: 6px 0 0; padding-left: 18px; }
.barra { display: flex; align-items: center; gap: 12px; margin: 16px 0 8px; }
button { font: inherit; font-weight: 600; padding: 9px 16px; border-radius: 6px;
         border: 0; background: #009fe3; color: #fff; cursor: pointer; }
button:hover { background: #007fb6; }
.dica { font-size: 12px; color: #6b7280; }
#corpo { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
         padding: 24px 28px; font-size: 14px; line-height: 1.55; }
#corpo p { margin: 0 0 12px; }
#corpo table { border-collapse: collapse; width: 100%; margin: 0 0 12px; }
#corpo th, #corpo td { border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; }
#corpo th { background: #f9fafb; }
#corpo blockquote { margin: 0 0 12px; padding-left: 12px; border-left: 3px solid #d1d5db;
                    color: #4b5563; }
#corpo pre { background: #f3f4f6; padding: 12px; overflow-x: auto; }
@media (prefers-color-scheme: dark) {
  body { background: #0b1220; color: #e5e7eb; }
  .meta, #corpo { background: #111827; border-color: #1f2937; }
  #corpo th { background: #1f2937; } #corpo th, #corpo td { border-color: #374151; }
  .avisos { background: #2b2411; border-color: #7c5e10; color: #fcd34d; }
}
"""

_JS_COPIAR = """
document.getElementById('copiar').addEventListener('click', async () => {
  const corpo = document.getElementById('corpo');
  const html = corpo.innerHTML;
  const estado = document.getElementById('estado');
  try {
    await navigator.clipboard.write([new ClipboardItem({
      'text/html': new Blob([html], {type: 'text/html'}),
      'text/plain': new Blob([corpo.innerText], {type: 'text/plain'}),
    })]);
    estado.textContent = 'Copiado. Cola no compositor do Odoo com Ctrl+V.';
  } catch (e) {
    const range = document.createRange();
    range.selectNodeContents(corpo);
    const sel = window.getSelection();
    sel.removeAllRanges(); sel.addRange(range);
    const ok = document.execCommand('copy');
    estado.textContent = ok
      ? 'Copiado. Cola no compositor do Odoo com Ctrl+V.'
      : 'Nao foi possivel copiar: seleciona o corpo e usa Ctrl+C.';
  }
});
"""


# Fica na linha 2 do ficheiro gerado: é o primeiro que se lê quando este `.html`
# é aberto num editor de código, que é exactamente onde alguém seria tentado a
# copiar o HTML em bruto e colar texto literal no Odoo.
_AVISO_NAO_COPIAR = """<!--
  NÃO copiar a partir do editor de código. O que está neste ficheiro é o HTML da
  página de pré-visualização; colado em bruto, o Odoo mostra as etiquetas como texto.

  Para colar no Odoo, dois caminhos:
    1. o pg_copy_email_cliente.ps1 já deixou o corpo do email na área de
       transferência — no compositor do Odoo é só Ctrl+V;
    2. ou abrir este ficheiro no browser (não no editor) e usar o botão
       "Copiar corpo".
-->
"""


def documento_previsualizacao(resultado: Resultado) -> str:
    """HTML completo para abrir no browser: metadados, avisos e botão de copiar."""
    linhas_meta = []
    for chave in CHAVES_CABECALHO:
        valor = resultado.cabecalho.get(chave)
        if valor:
            linhas_meta.append(
                "<dt>%s</dt><dd>%s</dd>" % (chave.capitalize(), _escapar(valor))
            )
    bloco_meta = ""
    if linhas_meta:
        bloco_meta = (
            '<section class="meta"><h1>Email ao cliente</h1><dl>%s</dl></section>'
            % "".join(linhas_meta)
        )

    bloco_avisos = ""
    if resultado.avisos:
        bloco_avisos = (
            '<section class="avisos"><strong>Avisos da conversão</strong><ul>%s</ul></section>'
            % "".join("<li>%s</li>" % _escapar(a) for a in resultado.avisos)
        )

    return (
        "<!doctype html>\n"
        + _AVISO_NAO_COPIAR
        + '<html lang="pt-PT">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n<main>\n"
        "%s%s"
        '<div class="barra"><button id="copiar" type="button">Copiar corpo</button>'
        '<span class="dica" id="estado">Copia apenas o corpo — os metadados acima ficam de fora.</span></div>\n'
        '<article id="corpo">\n%s\n</article>\n'
        "</main>\n<script>%s</script>\n</body>\n</html>\n"
        % (
            _escapar(resultado.assunto or "Email ao cliente"),
            _CSS_PREVISUALIZACAO,
            bloco_meta,
            bloco_avisos,
            resultado.fragmento,
            _JS_COPIAR,
        )
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte o markdown de um email ao cliente em HTML colável no Odoo."
    )
    parser.add_argument("--md", required=True, help="ficheiro markdown do email")
    parser.add_argument("--out", help="ficheiro HTML de saída (por omissão, o mesmo nome com .html)")
    parser.add_argument(
        "--fragmento", action="store_true", help="escrever só o HTML colável para stdout"
    )
    parser.add_argument(
        "--texto", action="store_true", help="escrever só a alternativa em texto simples para stdout"
    )
    parser.add_argument(
        "--assunto", action="store_true", help="escrever só o assunto para stdout"
    )
    parser.add_argument(
        "--manter-assinatura",
        action="store_true",
        help="manter o fecho e a assinatura do rascunho (por omissão são retirados, porque o Odoo insere a sua)",
    )
    parser.add_argument(
        "--json",
        dest="json_para",
        help="escrever o resultado completo em JSON no caminho indicado (consumido pelo wrapper PowerShell)",
    )
    args = parser.parse_args(argv)

    origem = Path(args.md)
    if not origem.is_file():
        print("ERRO: ficheiro nao encontrado: %s" % origem, file=sys.stderr)
        return 2

    resultado = converter(
        origem.read_text(encoding="utf-8"), manter_assinatura=args.manter_assinatura
    )

    if args.assunto:
        sys.stdout.write(resultado.assunto)
        return 0
    if args.fragmento:
        sys.stdout.write(resultado.fragmento)
        return 0
    if args.texto:
        sys.stdout.write(resultado.texto)
        return 0

    destino = Path(args.out) if args.out else origem.with_suffix(".html")
    # Path.write_text() so aceita newline= a partir do Python 3.10, e ha maquinas
    # da frota com o 3.9 do sistema. open() aceita-o desde sempre, com o mesmo
    # resultado, e mantem o script a correr nas duas versoes.
    with open(destino, "w", encoding="utf-8", newline="\n") as _saida:
        _saida.write(documento_previsualizacao(resultado))

    if args.json_para:
        # Ficheiro intermédio para o wrapper PowerShell: passar por ficheiro em UTF-8
        # evita o mojibake que a consola do PS 5.1 introduz ao decodificar stdout.
        with open(args.json_para, "w", encoding="utf-8", newline="\n") as _saida:
            _saida.write(json.dumps(
                {
                    "html": str(destino),
                    "assunto": resultado.assunto,
                    "cabecalho": resultado.cabecalho,
                    "fragmento": resultado.fragmento,
                    "texto": resultado.texto,
                    "avisos": resultado.avisos,
                },
                ensure_ascii=False,
                indent=2,
            ))

    print("HTML colavel: %s" % destino)
    if resultado.assunto:
        print("Assunto: %s" % resultado.assunto)
    for chave in ("para", "cc", "bcc"):
        if resultado.cabecalho.get(chave):
            print("%s: %s" % (chave.upper(), resultado.cabecalho[chave]))
    for aviso in resultado.avisos:
        print("AVISO: %s" % aviso)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
