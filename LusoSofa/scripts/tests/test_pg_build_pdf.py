"""
Testes do conversor Markdown -> PDF e da coerência da paleta da marca.

PORQUE EXISTE
    Até 2026-09-11 havia duas paletas na framework, e divergiam: o azul de acento era
    `#009FE3` no módulo de PowerPoint e `#0094E9` no de Word. Amostrando as cores usadas
    no conteúdo dos ficheiros da marca, o `#009FE3` aparece 30 vezes no template
    PowerPoint e o `#0094E9` não aparece em lado nenhum — era um valor aproximado.

    A regra da identidade visual existe para que dois documentos gerados em projetos
    diferentes saiam iguais. Estes testes são o que a torna verificável em vez de
    declarada.

Correr da raiz do repositório:
    python -m unittest scripts.tests.test_pg_build_pdf
"""

import io
import os
import pathlib
import tempfile
import unittest

from scripts import pg_brand_palette as paleta
from scripts import pg_build_pdf_from_markdown as conversor


class TestPaletaUnica(unittest.TestCase):
    def test_word_e_powerpoint_usam_o_mesmo_azul(self):
        # A regressão que este teste trava: dois geradores com azuis diferentes.
        from scripts import pg_docx_identity as word
        from scripts import pg_pptx_identity as powerpoint
        self.assertEqual(str(word.BLUE), str(powerpoint.ACCENT))
        self.assertEqual(str(word.BLUE), paleta.ACENTO)

    def test_o_azul_e_o_da_marca(self):
        # Verificado no conteúdo de Template_Parametro_PowerPoint_Completo 1.pptx.
        self.assertEqual("009FE3", paleta.ACENTO)

    def test_conversao_de_cor(self):
        self.assertEqual((0, 0x9F, 0xE3), paleta.para_rgb(paleta.ACENTO))
        self.assertEqual("#009FE3", paleta.para_css(paleta.ACENTO))
        self.assertEqual("#009FE3", paleta.para_css("#009fe3"))

    def test_cor_invalida_e_recusada(self):
        with self.assertRaises(ValueError):
            paleta.para_rgb("azul")


class TestCssDeImpressao(unittest.TestCase):
    def setUp(self):
        self.css = conversor.css_do_documento()

    def test_cabecalho_de_tabela_repete_em_cada_pagina(self):
        # Sem isto, uma tabela de 44 linhas parte-se a meio sem cabeçalho e fica inútil.
        # Foi o caso real que deu origem ao conversor.
        self.assertIn("display: table-header-group", self.css)

    def test_linha_de_tabela_nao_se_parte(self):
        self.assertIn("page-break-inside: avoid", self.css)

    def test_titulo_nao_fica_orfao(self):
        self.assertIn("page-break-after: avoid", self.css)

    def test_pagina_e_a4(self):
        self.assertIn("size: A4", self.css)

    def test_as_cores_vem_todas_da_paleta(self):
        self.assertIn(paleta.para_css(paleta.ACENTO), self.css)
        self.assertIn(paleta.para_css(paleta.TINTA), self.css)
        # E nenhuma cor inventada: a que a implementação original usava, escolhida a
        # olho, não pode voltar a entrar.
        self.assertNotIn("#4a1d3f", self.css.lower())


class TestSubtituloAcentuado(unittest.TestCase):
    def test_le_de_ficheiro_com_arroba(self):
        # Passar texto acentuado por argv em Windows perde os acentos: um PDF real saiu
        # com «Mobiliario» em vez de «Mobiliário». O '@ficheiro' existe por isso.
        fh = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        fh.write("ENIGMAF — Mobiliário\n")
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        self.assertEqual("ENIGMAF — Mobiliário", conversor.ler_subtitulo("@" + fh.name))

    def test_texto_directo_passa_tal_e_qual(self):
        self.assertEqual("abc", conversor.ler_subtitulo("abc"))

    def test_vazio_da_vazio(self):
        self.assertEqual("", conversor.ler_subtitulo(""))

    def test_ficheiro_inexistente_falha_com_mensagem(self):
        with self.assertRaises(SystemExit):
            conversor.ler_subtitulo("@nao-existe-de-todo.txt")


class TestHtml(unittest.TestCase):
    def test_tabela_markdown_vira_tabela_html(self):
        try:
            html = conversor.construir_html("| a | b |\n|---|---|\n| 1 | 2 |\n", "")
        except SystemExit:
            self.skipTest("biblioteca 'markdown' nao instalada")
        self.assertIn("<table>", html)
        self.assertIn("<thead>", html)

    def test_subtitulo_entra_no_html(self):
        try:
            html = conversor.construir_html("# T\n", "Mobiliário")
        except SystemExit:
            self.skipTest("biblioteca 'markdown' nao instalada")
        self.assertIn("Mobiliário", html)
        self.assertIn("pg-subtitulo", html)


class TestPdfPontaAPonta(unittest.TestCase):
    """Gera um PDF a sério. Salta se o Chromium nao estiver instalado."""

    def test_tabela_longa_pagina_com_cabecalho_repetido(self):
        linhas = ["# Folha de trabalho", "", "| # | Grupo | Classificação |", "|---|---|---|"]
        linhas += ["| %d | Grupo %d | |" % (i, i) for i in range(1, 45)]
        origem = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        origem.write("\n".join(linhas))
        origem.close()
        self.addCleanup(os.unlink, origem.name)

        destino = origem.name.replace(".md", ".pdf")
        try:
            with io.open(origem.name, encoding="utf-8") as fh:
                html = conversor.construir_html(fh.read(), "ENIGMAF — Mobiliário")
            conversor.escrever_pdf(html, pathlib.Path(destino))
        except SystemExit as erro:
            self.skipTest("motor de PDF indisponivel: %s" % erro)
        self.addCleanup(lambda: os.path.exists(destino) and os.unlink(destino))

        self.assertTrue(os.path.getsize(destino) > 5000, "PDF demasiado pequeno para ser valido")

        try:
            import pypdf
        except ImportError:
            self.skipTest("pypdf nao instalado; saltadas as verificacoes de conteudo")

        leitor = pypdf.PdfReader(destino)
        self.assertGreater(len(leitor.pages), 1, "44 linhas tem de paginar")
        texto = "".join((p.extract_text() or "") for p in leitor.pages)
        self.assertIn("Mobiliário", texto, "os acentos perderam-se")
        self.assertGreaterEqual(texto.count("Classificação"), 2,
                                "o cabecalho da tabela tem de repetir em cada pagina")


if __name__ == "__main__":
    unittest.main()
