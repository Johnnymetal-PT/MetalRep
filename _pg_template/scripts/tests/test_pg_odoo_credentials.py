"""
Testes da cascata de credenciais do lado Python.

Espelham, um a um, os do `pg_test_odoo_credentials.ps1`. A razão de existirem os dois é
que os consumidores estão repartidos pelas duas linguagens: se as cascatas divergirem,
quem configurar a chave vê o PowerShell a funcionar e o Python a falhar, sem nada que
ligue uma coisa à outra.

Até 2026-09-28 estes testes tinham de esconder a chave partilhada do repositório, que
ganhava sempre a seguir. Deixou de ser preciso: o degrau legado saiu da cascata quando a
conta de serviço foi arquivada, e o ficheiro da máquina é agora o último.

Correr da raiz do repositório:
    python -m unittest scripts.tests.test_pg_odoo_credentials
"""

import json
import os
import tempfile
import unittest

from scripts import pg_odoo_credentials as mod

VARIAVEIS = ("PG_ODOO_API_KEY", "PG_ODOO_LOGIN", "PG_ODOO_KNOWLEDGE_TOKEN",
             "PG_ODOO_CREDENTIALS_FILE")


class BaseCascata(unittest.TestCase):
    def setUp(self):
        self._ambiente = {k: os.environ.get(k) for k in VARIAVEIS}
        for k in VARIAVEIS:
            os.environ.pop(k, None)

        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def tearDown(self):
        for k, v in self._ambiente.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def escrever(self, nome, conteudo):
        caminho = os.path.join(self._dir.name, nome)
        with open(caminho, "w", encoding="utf-8") as fh:
            if isinstance(conteudo, str):
                fh.write(conteudo)
            else:
                json.dump(conteudo, fh)
        return caminho


class TestCascata(BaseCascata):
    def test_sem_nada_o_erro_nomeia_o_comando(self):
        # Uma mensagem que não diga o que correr manda quem a lê procurar documentação,
        # e é aí que as pessoas desistem e pedem a chave a outra pessoa.
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = os.path.join(self._dir.name, "nada.json")
        with self.assertRaises(mod.ErroDeCredenciais) as ctx:
            mod.resolver_credenciais_pg()
        self.assertIn("pg_init_odoo_credentials.ps1", str(ctx.exception))
        self.assertEqual("nenhuma", mod.origem_das_credenciais()["tipo"])

    def test_ficheiro_da_maquina_so_precisa_de_login_e_chave(self):
        # url e db não são segredo e vêm do endpoint versionado: por máquina ficam dois
        # campos, não quatro.
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "maquina.json", {"login": "pessoa@parametro.global", "api_key": "chave-da-maquina"})
        c = mod.resolver_credenciais_pg()
        self.assertEqual("chave-da-maquina", c["api_key"])
        self.assertEqual("pessoa@parametro.global", c["login"])
        self.assertTrue(c["url"])
        self.assertTrue(c["db"])
        self.assertIn("ficheiro da máquina", c["origem"])

    def test_ambiente_vence_o_ficheiro(self):
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "maquina.json", {"login": "pessoa@parametro.global", "api_key": "chave-da-maquina"})
        os.environ["PG_ODOO_API_KEY"] = "chave-do-ambiente"
        os.environ["PG_ODOO_LOGIN"] = "outra@parametro.global"
        c = mod.resolver_credenciais_pg()
        self.assertEqual("chave-do-ambiente", c["api_key"])
        self.assertEqual("outra@parametro.global", c["login"])
        self.assertEqual("env", mod.origem_das_credenciais()["tipo"])

    def test_caminho_explicito_vence_o_ambiente(self):
        # Mantém o contrato antigo: quem passa o caminho espera que seja usado.
        explicito = self.escrever(
            "explicito.json", {"login": "x@parametro.global", "api_key": "chave-explicita"})
        os.environ["PG_ODOO_API_KEY"] = "chave-do-ambiente"
        os.environ["PG_ODOO_LOGIN"] = "y@parametro.global"
        c = mod.resolver_credenciais_pg(explicito)
        self.assertEqual("chave-explicita", c["api_key"])

    def test_alias_legado_continua_aceite(self):
        # Retirar PG_ODOO_KNOWLEDGE_TOKEN em silêncio partia máquinas sem nenhuma
        # mensagem que ligasse a causa ao efeito.
        os.environ["PG_ODOO_KNOWLEDGE_TOKEN"] = "chave-legada"
        os.environ["PG_ODOO_LOGIN"] = "legado@parametro.global"
        c = mod.resolver_credenciais_pg()
        self.assertEqual("chave-legada", c["api_key"])

    def test_chave_sem_login_da_erro_que_fala_do_login(self):
        # Uma chave de um utilizador com o login de outro não autentica, e o erro do
        # Odoo ("uid vazio") nunca sugere que o problema é o login.
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "sem_login.json", {"api_key": "chave-sem-dono"})
        with self.assertRaises(mod.ErroDeCredenciais) as ctx:
            mod.resolver_credenciais_pg()
        self.assertIn("login", str(ctx.exception).lower())

    def test_placeholder_nao_conta_como_chave(self):
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "placeholder.json", {"login": "x@parametro.global",
                                 "api_key": "COLAR_AQUI_A_API_KEY"})
        with self.assertRaises(mod.ErroDeCredenciais):
            mod.resolver_credenciais_pg()
        self.assertEqual("nenhuma", mod.origem_das_credenciais()["tipo"])

    def test_ficheiro_partido_nao_passa_por_nada_configurado(self):
        # Sem esta distinção, um JSON com uma vírgula a mais mandava a cascata para a
        # chave partilhada em silêncio, e ninguém percebia porque é que a chave pessoal
        # "não pegou".
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "partido.json", '{ "login": "x@parametro.global", "api_key": ')
        with self.assertRaises(mod.ErroDeCredenciais) as ctx:
            mod.resolver_credenciais_pg()
        self.assertIn("ilegíveis", str(ctx.exception))

    def test_origem_nunca_devolve_a_chave(self):
        # É lida para diagnóstico e o resultado do preflight fica versionado em
        # .pg/PREFLIGHT.json: uma chave aqui era uma chave commitada.
        os.environ["PG_ODOO_CREDENTIALS_FILE"] = self.escrever(
            "maquina.json", {"login": "pessoa@parametro.global", "api_key": "chave-secreta"})
        origem = mod.origem_das_credenciais()
        self.assertNotIn("api_key", origem)
        self.assertNotIn("chave-secreta", json.dumps(origem, ensure_ascii=False))


class TestEndpointPartilhado(BaseCascata):
    def test_url_e_db_vem_do_ficheiro_versionado(self):
        # Se este ficheiro desaparecer, toda a frota perde o endereço de uma vez: vale
        # a pena que um teste o diga em vez de o descobrir uma máquina de cada vez.
        endpoint = mod._endpoint_partilhado()
        self.assertTrue(endpoint.get("url"), "credentials/pg_odoo_endpoint.json sem url")
        self.assertTrue(endpoint.get("db"), "credentials/pg_odoo_endpoint.json sem db")


if __name__ == "__main__":
    unittest.main()
