import json
import os
import tempfile
import unittest

from scripts import pg_json_canonical as mod


class TestCanonicalText(unittest.TestCase):
    def test_indenta_com_dois_espacos(self):
        texto = mod.canonical_text({"a": {"b": 1}})
        self.assertIn('\n  "a": {\n    "b": 1\n  }', texto)

    def test_termina_com_uma_linha_em_branco(self):
        self.assertTrue(mod.canonical_text({"a": 1}).endswith("}\n"))

    def test_nao_usa_lf_do_sistema(self):
        # Nunca CRLF, mesmo em Windows: e o LF que o .gitattributes impoe.
        self.assertNotIn("\r", mod.canonical_text({"a": [1, 2]}))

    def test_preserva_nao_ascii_literal(self):
        texto = mod.canonical_text({"nome": "Orçamento à medida"})
        self.assertIn("Orçamento à medida", texto)
        self.assertNotIn("\\u", texto)

    def test_preserva_a_ordem_do_produtor(self):
        # Nao ordena chaves: a ordem do manifest e a que o produtor definiu.
        texto = mod.canonical_text({"zebra": 1, "alfa": 2})
        self.assertLess(texto.index("zebra"), texto.index("alfa"))

    def test_array_vazio_numa_linha(self):
        self.assertIn('"attachments": []', mod.canonical_text({"attachments": []}))

    def test_e_estavel_para_o_mesmo_conteudo(self):
        payload = {"templates": {"TPL_X": {"sha256": "abc", "attachments": []}}}
        self.assertEqual(mod.canonical_text(payload), mod.canonical_text(json.loads(json.dumps(payload))))


class TestCanonicalizeFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.entrada = os.path.join(self.dir, "entrada.json")
        self.saida = os.path.join(self.dir, "saida.json")

    def _bytes_da_saida(self):
        with open(self.saida, "rb") as handle:
            return handle.read()

    def test_escreve_lf_mesmo_em_windows(self):
        with open(self.entrada, "w", encoding="utf-8") as handle:
            handle.write('{"a":1,"b":[2,3]}')

        mod.canonicalize_file(self.entrada, self.saida)

        conteudo = self._bytes_da_saida()
        self.assertNotIn(b"\r\n", conteudo)
        self.assertTrue(conteudo.endswith(b"}\n"))

    def test_aceita_entrada_com_bom(self):
        # O ConvertTo-Json do PowerShell pode chegar com BOM consoante o caminho de escrita.
        with open(self.entrada, "w", encoding="utf-8-sig") as handle:
            handle.write('{"a":1}')

        mod.canonicalize_file(self.entrada, self.saida)

        self.assertEqual(json.loads(self._bytes_da_saida().decode("utf-8")), {"a": 1})

    def test_conteudo_igual_produz_bytes_iguais(self):
        # A garantia que interessa: forma fixada pelo conteudo, nao por quem gerou o JSON.
        compacto = '{"b":2,"a":{"x":[]}}'
        espacado = '{\n  "b": 2,\n  "a": {\n    "x": [\n\n    ]\n  }\n}'

        primeiro = os.path.join(self.dir, "1.json")
        segundo = os.path.join(self.dir, "2.json")
        for origem, destino in ((compacto, primeiro), (espacado, segundo)):
            with open(self.entrada, "w", encoding="utf-8") as handle:
                handle.write(origem)
            mod.canonicalize_file(self.entrada, destino)

        with open(primeiro, "rb") as a, open(segundo, "rb") as b:
            self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
