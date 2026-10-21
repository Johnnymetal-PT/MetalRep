import unittest

from scripts import pg_build_email_cliente as mod


EMAIL_COMPLETO = """---
assunto: Decisão necessária — Integração faturação — até 30/04
para: cliente@exemplo.pt
cc: pedro@parametro.global
---

Exmo. Sr. António Silva,

Para avançarmos com a **integração de faturação**, necessitamos da vossa decisão
sobre o formato de comunicação à AT.

As opções em análise são:

- **Opção A:** comunicação directa — menos passos manuais
  - requer credenciais de produção
- **Opção B:** ficheiro SAF-T mensal — sem dependência de credenciais

A nossa recomendação é a *Opção A*. Detalhe em [documentação oficial](https://www.odoo.com/documentation/19.0/).

| Opção | Esforço | Risco |
|---|---|---|
| A | 2 dias | Médio |
| B | 1 dia | Baixo |

---

Solicito a vossa indicação até 30/04.

Com os melhores cumprimentos,

Nuno Oliveira
Parâmetro Global — Consultoria Informática
"""


class TestCabecalho(unittest.TestCase):
    def test_bloco_de_metadados_sai_do_corpo(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertEqual(r.assunto, "Decisão necessária — Integração faturação — até 30/04")
        self.assertEqual(r.cabecalho["para"], "cliente@exemplo.pt")
        self.assertEqual(r.cabecalho["cc"], "pedro@parametro.global")
        self.assertNotIn("assunto:", r.fragmento)
        self.assertNotIn("cliente@exemplo.pt", r.fragmento)

    def test_linha_assunto_em_negrito_tambem_e_aceite(self):
        r = mod.converter("**Assunto:** Ponto de situação — Semana 17\n\nBom dia,\n")
        self.assertEqual(r.assunto, "Ponto de situação — Semana 17")
        self.assertNotIn("Assunto", r.fragmento)

    def test_sem_assunto_avisa(self):
        r = mod.converter("Bom dia,\n\nSegue o documento.\n")
        self.assertTrue(any("Sem assunto" in a for a in r.avisos))

    def test_chave_desconhecida_avisa_e_e_ignorada(self):
        r = mod.converter("---\nassunto: X\nprioridade: alta\n---\n\nCorpo.\n")
        self.assertNotIn("prioridade", r.cabecalho)
        self.assertTrue(any("prioridade" in a for a in r.avisos))


class TestTextoCorrido(unittest.TestCase):
    def test_negrito_italico_e_riscado(self):
        r = mod.converter("---\nassunto: X\n---\n\n**forte** _enfase_ ~~fora~~\n")
        self.assertIn("<strong>forte</strong>", r.fragmento)
        self.assertIn("<em>enfase</em>", r.fragmento)
        self.assertIn("<s>fora</s>", r.fragmento)

    def test_link_markdown_abre_em_nova_janela(self):
        r = mod.converter("---\nassunto: X\n---\n\n[Odoo](https://odoo.com)\n")
        self.assertIn('<a href="https://odoo.com" target="_blank">Odoo</a>', r.fragmento)

    def test_email_sem_esquema_vira_mailto(self):
        r = mod.converter("---\nassunto: X\n---\n\n[escrever](nuno@parametro.global)\n")
        self.assertIn('href="mailto:nuno@parametro.global"', r.fragmento)

    def test_url_javascript_e_removido(self):
        r = mod.converter("---\nassunto: X\n---\n\n[clica](javascript:alert(1))\n")
        self.assertNotIn("javascript", r.fragmento)
        self.assertIn("clica", r.fragmento)

    def test_quebra_simples_vira_br(self):
        r = mod.converter("---\nassunto: X\n---\n\nNuno Oliveira\nParâmetro Global\n")
        self.assertIn("Nuno Oliveira<br>Parâmetro Global", r.fragmento)

    def test_acentos_preservados(self):
        r = mod.converter("---\nassunto: X\n---\n\nvalidação, âmbito, decisão, opções\n")
        self.assertIn("validação, âmbito, decisão, opções", r.fragmento)

    def test_html_perigoso_e_escapado(self):
        r = mod.converter("---\nassunto: X\n---\n\n<script>mau()</script>\n")
        self.assertNotIn("<script>", r.fragmento)
        self.assertIn("&lt;script&gt;", r.fragmento)
        self.assertTrue(any("HTML" in a for a in r.avisos))

    def test_codigo_inline_fica_texto_e_avisa(self):
        r = mod.converter("---\nassunto: X\n---\n\nusar `res.partner` aqui\n")
        self.assertIn("res.partner", r.fragmento)
        self.assertNotIn("<code>", r.fragmento)
        self.assertTrue(any("crases" in a for a in r.avisos))

    def test_marcador_de_template_por_preencher_avisa(self):
        r = mod.converter("---\nassunto: X\n---\n\nExmo. Sr. [Nome],\n")
        self.assertTrue(any("marcador de template" in a for a in r.avisos))


class TestBlocos(unittest.TestCase):
    def test_lista_aninhada_usa_formato_do_odoo(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertIn('<li class="oe-nested"><ul>', r.fragmento)
        self.assertIn("<li>requer credenciais de produção</li>", r.fragmento)

    def test_lista_numerada(self):
        r = mod.converter("---\nassunto: X\n---\n\n1. um\n2. dois\n")
        self.assertIn("<ol><li>um</li><li>dois</li></ol>", r.fragmento)

    def test_tabela_com_classes_do_odoo(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertIn('<table class="table table-bordered o_table">', r.fragmento)
        self.assertIn("<thead><tr><th>Opção</th>", r.fragmento)
        self.assertIn("<td>2 dias</td>", r.fragmento)

    def test_regua_horizontal_desaparece_e_avisa(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertNotIn("<hr", r.fragmento)
        self.assertTrue(any("'---'" in a for a in r.avisos))

    def test_titulo_grande_avisa_mas_converte(self):
        r = mod.converter("---\nassunto: X\n---\n\n# Titulo\n\nCorpo.\n")
        self.assertIn("<h1>Titulo</h1>", r.fragmento)
        self.assertTrue(any("muito grande" in a for a in r.avisos))

    def test_citacao(self):
        r = mod.converter("---\nassunto: X\n---\n\n> citado\n")
        self.assertIn("<blockquote><p>citado</p></blockquote>", r.fragmento)

    def test_bloco_de_codigo_fica_pre(self):
        r = mod.converter("---\nassunto: X\n---\n\n```\nlinha 1\nlinha 2\n```\n")
        self.assertIn("<pre>linha 1\nlinha 2</pre>", r.fragmento)


class TestAssinatura(unittest.TestCase):
    """O Odoo insere a assinatura do utilizador: o corpo não a deve repetir."""

    def test_fecho_e_assinatura_saem_do_corpo(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertNotIn("melhores cumprimentos", r.fragmento)
        self.assertNotIn("Nuno Oliveira", r.fragmento)
        self.assertNotIn("Consultoria Informática", r.fragmento)
        # o último parágrafo de conteúdo fica
        self.assertIn("Solicito a vossa indicação até 30/04", r.fragmento)

    def test_o_que_saiu_e_reportado(self):
        r = mod.converter(EMAIL_COMPLETO)
        aviso = next(a for a in r.avisos if "assinatura" in a.lower())
        self.assertIn("Nuno Oliveira", aviso)
        self.assertIn("ManterAssinatura", aviso)

    def test_manter_assinatura_preserva(self):
        r = mod.converter(EMAIL_COMPLETO, manter_assinatura=True)
        self.assertIn("Nuno Oliveira", r.fragmento)
        self.assertFalse(any("assinatura" in a.lower() for a in r.avisos))

    def test_separador_de_assinatura_tambem_corta(self):
        r = mod.converter("---\nassunto: X\n---\n\nCorpo.\n\n--\n\nNuno Oliveira\nDeveloper\n")
        self.assertIn("<p>Corpo.</p>", r.fragmento)
        self.assertNotIn("Developer", r.fragmento)

    def test_nao_corta_conteudo_real_no_fim(self):
        corpo = (
            "---\nassunto: X\n---\n\nBom dia,\n\n"
            "Solicito que percorra a base de testes e nos dê retorno.\n\n"
            "Fico à disposição para uma sessão conjunta, se preferir percorrer a base connosco.\n"
        )
        r = mod.converter(corpo)
        self.assertIn("Fico à disposição para uma sessão conjunta", r.fragmento)
        self.assertFalse(any("assinatura" in a.lower() for a in r.avisos))

    def test_lista_no_fim_trava_a_procura(self):
        corpo = (
            "---\nassunto: X\n---\n\nCumprimentos ao Sr. António pela decisão.\n\n"
            "- primeiro ponto\n- segundo ponto\n"
        )
        r = mod.converter(corpo)
        self.assertIn("primeiro ponto", r.fragmento)
        self.assertIn("Cumprimentos ao Sr. António", r.fragmento)

    def test_saudacao_de_abertura_nao_e_confundida_com_fecho(self):
        r = mod.converter("---\nassunto: X\n---\n\nExmo. Sr. Silva,\n\nSegue o documento.\n")
        self.assertIn("Exmo. Sr. Silva,", r.fragmento)
        self.assertIn("Segue o documento.", r.fragmento)


class TestInvariantesDeColagem(unittest.TestCase):
    """O que garante que a colagem no Odoo não perde nada: nada fora da lista branca."""

    def test_fragmento_respeita_lista_branca(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertEqual(mod.validar_fragmento(r.fragmento), [])

    def test_fragmento_nao_leva_css(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertNotIn("style=", r.fragmento)
        self.assertNotIn("<span", r.fragmento)
        self.assertNotIn("<div", r.fragmento)

    def test_validador_apanha_etiqueta_proibida(self):
        erros = mod.validar_fragmento('<p>ok</p><div style="color:red">mau</div>')
        self.assertTrue(any("<div>" in e for e in erros))
        self.assertTrue(any("style" in e for e in erros))

    def test_validador_apanha_classe_fora_da_lista(self):
        erros = mod.validar_fragmento('<p class="text-center">x</p>')
        self.assertTrue(any("text-center" in e for e in erros))

    def test_conversao_e_determinista(self):
        primeiro = mod.converter(EMAIL_COMPLETO).fragmento
        segundo = mod.converter(EMAIL_COMPLETO).fragmento
        self.assertEqual(primeiro, segundo)


class TestAlternativaEmTexto(unittest.TestCase):
    def test_texto_simples_sem_marcacao(self):
        r = mod.converter(EMAIL_COMPLETO)
        self.assertNotIn("**", r.texto)
        self.assertIn("- Opção A: comunicação directa", r.texto)
        self.assertIn("documentação oficial (https://www.odoo.com/documentation/19.0/)", r.texto)


class TestPrevisualizacao(unittest.TestCase):
    def test_documento_tem_corpo_e_metadados_separados(self):
        r = mod.converter(EMAIL_COMPLETO)
        doc = mod.documento_previsualizacao(r)
        self.assertIn('<article id="corpo">', doc)
        self.assertIn("cliente@exemplo.pt", doc)
        self.assertIn('<button id="copiar"', doc)
        # os metadados ficam fora do corpo colável
        corpo = doc.split('<article id="corpo">')[1]
        self.assertNotIn("cliente@exemplo.pt", corpo)

    def test_aviso_de_nao_copiar_esta_no_topo_do_ficheiro(self):
        """Quem abre o .html num editor tem de ver o aviso antes de copiar em bruto."""
        doc = mod.documento_previsualizacao(mod.converter(EMAIL_COMPLETO))
        linhas = doc.split("\n")
        self.assertEqual(linhas[0], "<!doctype html>")
        self.assertEqual(linhas[1], "<!--")
        self.assertIn("NÃO copiar a partir do editor", linhas[2])
        # o aviso é comentário HTML: não aparece na página nem no corpo colável
        self.assertNotIn("NÃO copiar", doc.split('<article id="corpo">')[1])


if __name__ == "__main__":
    unittest.main()
