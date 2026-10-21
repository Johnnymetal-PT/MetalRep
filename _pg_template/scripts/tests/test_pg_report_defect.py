"""Testes do pg_report_defect.py, sem tocar no Odoo.

O cliente Odoo e substituido por um duplo que regista as chamadas. O que importa provar
nao e que o Odoo aceita o pedido -- e que o comando nao duplica tarefas, que escreve o
numero no livro-razao, e que quando nao consegue falar com o Odoo o defeito fica registado
localmente em vez de se perder. Foi um defeito perdido que motivou tudo isto.
"""

import io
import json
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout

from scripts import pg_report_defect as alvo


CONTRATO = """## O que acontece
O bloco fica desatualizado.

## Onde foi observado
givachoice, 2026-08-11.

## Como se reproduz
Mudar a versao no Brodoo e voltar a sincronizar.

## Impacto
Liga o source da serie errada.
"""


class ClienteFalso:
    """Duplo do OdooKnowledgeClient: devolve o combinado e guarda as chamadas."""

    def __init__(self, existente=None, rebenta=False):
        self.existente = existente
        self.rebenta = rebenta
        self.chamadas = []

    def call_kw(self, model, method, args=None, kwargs=None):
        if self.rebenta:
            raise RuntimeError("sem rede")
        self.chamadas.append((model, method, args, kwargs))
        if method == "search_read":
            if self.existente:
                return [{"id": self.existente, "name": "framework - x"}]
            return []
        if method == "create":
            return [4242]
        return True


class RegistoDeDefeitos(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="pg_defeito_")
        self.ficheiro = os.path.join(self.pasta, "defeito.md")
        with io.open(self.ficheiro, "w", encoding="utf-8") as f:
            f.write(CONTRATO)
        self._corpo_original = alvo.corpo_da_tarefa
        alvo.corpo_da_tarefa = lambda md, fp, c: "<p>corpo</p><p>" + fp + "</p>"
        self._modulos = {k: sys.modules.get(k) for k in
                         ("pg_odoo_credentials", "pg_doc_templates_common")}

    def tearDown(self):
        alvo.corpo_da_tarefa = self._corpo_original
        for nome, modulo in self._modulos.items():
            if modulo is None:
                sys.modules.pop(nome, None)
            else:
                sys.modules[nome] = modulo

    def _ligar(self, cliente):
        cred = types.ModuleType("pg_odoo_credentials")
        cred.resolver_credenciais_pg = lambda: {
            "url": "https://x", "db": "d", "login": "a@b.pt", "api_key": "k", "origem": "teste"}
        doc = types.ModuleType("pg_doc_templates_common")
        doc.OdooKnowledgeClient = lambda *a, **k: cliente
        sys.modules["pg_odoo_credentials"] = cred
        sys.modules["pg_doc_templates_common"] = doc

    def _correr(self, extra=None):
        args = ["--titulo", "o bloco nao e regenerado", "--ficheiro", self.ficheiro,
                "--repo", self.pasta] + (extra or [])
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = alvo.main(args)
        return codigo, saida.getvalue(), erro.getvalue()

    def _livro(self):
        caminho = os.path.join(self.pasta, ".pg", "defeitos.jsonl")
        with io.open(caminho, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    def test_impressao_digital_indiferente_a_acentos_e_caixa(self):
        a = alvo.impressao_digital("framework", "O bloco  nao e Regenerado")
        b = alvo.impressao_digital("framework", "o bloco nao e regenerado")
        self.assertEqual(a, b)
        self.assertNotEqual(a, alvo.impressao_digital("pg_brodoo", "o bloco nao e regenerado"))

    def test_contrato_completo_e_incompleto(self):
        self.assertEqual(alvo.seccoes_em_falta(CONTRATO), [])
        falta = alvo.seccoes_em_falta("## O que acontece\nx\n")
        self.assertIn("Como se reproduz", falta)
        self.assertIn("Impacto", falta)

    def test_sem_contrato_nao_cria_e_diz_o_que_falta(self):
        cliente = ClienteFalso()
        self._ligar(cliente)
        with io.open(self.ficheiro, "w", encoding="utf-8") as f:
            f.write("## O que acontece\nx\n")
        codigo, _, erro = self._correr()
        self.assertEqual(codigo, 2)
        self.assertIn("Como se reproduz", erro)
        self.assertEqual(cliente.chamadas, [])

    def test_cria_em_backlog_sem_responsavel_e_escreve_o_livro(self):
        cliente = ClienteFalso()
        self._ligar(cliente)
        codigo, _, _ = self._correr()
        self.assertEqual(codigo, 0)
        valores = [c for c in cliente.chamadas if c[1] == "create"][0][2][0]
        self.assertEqual(valores["project_id"], alvo.PROJETO_BRODOO)
        self.assertEqual(valores["stage_id"], alvo.ETAPA_BACKLOG)
        self.assertEqual(valores["user_ids"], [(6, 0, [])])
        self.assertEqual(valores["name"], "framework - o bloco nao e regenerado")
        linha = self._livro()[0]
        self.assertEqual(linha["task_id"], 4242)
        self.assertEqual(linha["operador"], "a@b.pt")

    def test_ja_registado_acrescenta_ocorrencia_e_nao_duplica(self):
        cliente = ClienteFalso(existente=7585)
        self._ligar(cliente)
        codigo, saida, _ = self._correr()
        self.assertEqual(codigo, 0)
        self.assertEqual([c for c in cliente.chamadas if c[1] == "create"], [])
        post = [c for c in cliente.chamadas if c[1] == "message_post"][0]
        # Sem body_is_html a nota sai com as etiquetas a vista, como aconteceu na 7577.
        self.assertTrue(post[3]["body_is_html"])
        self.assertIn("JA REGISTADO", saida)
        self.assertEqual(self._livro()[0]["ocorrencia_de"], 7585)

    def test_sem_rede_o_defeito_fica_registado_localmente(self):
        cliente = ClienteFalso(rebenta=True)
        self._ligar(cliente)
        codigo, _, erro = self._correr()
        self.assertEqual(codigo, 1)
        self.assertIsNone(self._livro()[0]["task_id"])   # e o preflight avisa ate deixar de o ser
        self.assertIn("sem rede", erro)

    def test_dry_run_nao_fala_com_o_odoo_nem_escreve(self):
        cliente = ClienteFalso()
        self._ligar(cliente)
        codigo, _, _ = self._correr(["--dry-run"])
        self.assertEqual(codigo, 0)
        self.assertEqual(cliente.chamadas, [])
        self.assertFalse(os.path.exists(os.path.join(self.pasta, ".pg", "defeitos.jsonl")))


if __name__ == "__main__":
    unittest.main()
