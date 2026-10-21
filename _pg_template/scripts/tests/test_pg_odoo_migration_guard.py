"""
Testes do guard de migração — o componente cuja função é impedir uma escrita não
autorizada na produção de um cliente, e que até 2026-09-10 não tinha nenhum.

O que se testa aqui é a decisão, não a rede: `_validar`, `_verificar_coerencia`,
a normalização do URL e a leitura do ficheiro de ligação são puros. As instâncias
são construídas com `__new__` para saltar o `__init__`, que autentica.

Correr da raiz do repositório:
    python -m unittest scripts.tests.test_pg_odoo_migration_guard
"""

import json
import os
import tempfile
import unittest

from scripts import pg_odoo_migration_guard as mod


def guarda(purpose, confirmed=False, allow_prod=False, database=""):
    """Guard sem `__init__`: sem autenticação, sem rede, só a máquina de decisão."""
    g = mod.Guard.__new__(mod.Guard)
    g.alvo = mod.Alvo(purpose=purpose, base_url="https://exemplo.odoo.com",
                      database=database, login="utilizador", api_key="chave")
    g.confirmed = confirmed
    g.allow_prod = allow_prod
    g.log_path = os.devnull
    return g


class TestClassificacaoDeMetodos(unittest.TestCase):
    def test_nenhum_metodo_esta_nas_duas_listas(self):
        # Um método classificado como leitura E escrita passaria pela porta errada.
        # Vale sobretudo depois de fundir listas brancas de dois lados à mão, que foi
        # o que aconteceu em 2026-09-10.
        self.assertEqual(set(), mod.METODOS_LEITURA & mod.METODOS_ESCRITA)

    def test_metodo_desconhecido_e_bloqueado(self):
        # A regra que torna a lista branca uma lista branca: o que não está
        # classificado não passa, porque pode escrever sem se saber.
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("brodoo_dev", confirmed=True)._validar("action_misteriosa", True)
        self.assertIn("desconhecido", str(ctx.exception))

    def test_os_dois_lados_da_fusao_de_2026_09_10_sobreviveram(self):
        # A resolução do conflito foi manual; se um dos lados tivesse caído, o guard
        # passaria a bloquear trabalho legítimo ou, pior, ninguém daria por isso.
        for metodo in ("try_loading", "action_refresh", "action_rebuild_all",
                       "action_replenish_selected", "button_draft"):
            self.assertIn(metodo, mod.METODOS_ESCRITA, metodo)

    def test_leitura_nao_exige_confirmacao(self):
        # Uma passagem de dry-run tem de correr sem --confirm; se não corresse,
        # ninguém faria dry-run.
        guarda("production")._validar("search_read", False)
        guarda("brodoo_dev")._validar("read", False)


class TestCamadasDeEscrita(unittest.TestCase):
    def test_sem_confirmacao_e_bloqueado(self):
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("brodoo_dev", confirmed=False)._validar("write", True)
        self.assertIn("--confirm", str(ctx.exception))

    def test_sem_allow_write_na_chamada_e_bloqueado(self):
        # O consentimento é por chamada: uma passagem de leitura que engane e chame
        # `write` não escreve só porque a execução foi confirmada.
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("brodoo_dev", confirmed=True)._validar("write", False)
        self.assertIn("allow_write", str(ctx.exception))

    def test_com_confirmacao_e_allow_write_passa(self):
        guarda("brodoo_dev", confirmed=True)._validar("write", True)
        guarda("client_test", confirmed=True)._validar("create", True)

    def test_finalidade_sem_escrita_bloqueia_mesmo_com_tudo_o_resto(self):
        # Uma finalidade fora do conjunto conhecido não ganha escrita por omissão.
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("qualquer_coisa", confirmed=True, allow_prod=True)._validar("write", True)
        self.assertIn("BLOQUEADO", str(ctx.exception))


class TestProducao(unittest.TestCase):
    def test_producao_exige_allow_prod(self):
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("production", confirmed=True, allow_prod=False)._validar("write", True)
        self.assertIn("--allow-prod", str(ctx.exception))

    def test_producao_com_allow_prod_passa(self):
        guarda("production", confirmed=True, allow_prod=True)._validar("write", True)

    def test_allow_prod_nao_dispensa_a_confirmacao(self):
        # As camadas são cumulativas, não alternativas.
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            guarda("production", confirmed=False, allow_prod=True)._validar("write", True)
        self.assertIn("--confirm", str(ctx.exception))

    def test_allow_prod_nao_dispensa_o_allow_write(self):
        with self.assertRaises(mod.ErroDeGuarda):
            guarda("production", confirmed=True, allow_prod=True)._validar("write", False)


class TestCoerenciaDaLigacao(unittest.TestCase):
    def test_base_com_main_declarada_como_staging_aborta(self):
        # Convenção do Odoo.sh: a build de produção tem "main" no nome. Uma ligação
        # assim declarada como brodoo_dev é erro de configuração, e apanha-se sem rede.
        g = guarda("brodoo_dev", database="cliente-main-12345")
        with self.assertRaises(mod.ErroDeGuarda) as ctx:
            g._verificar_coerencia()
        self.assertIn("ABORTADO", str(ctx.exception))

    def test_a_deteccao_e_insensivel_a_maiusculas(self):
        g = guarda("client_test", database="CLIENTE-MAIN-12345")
        with self.assertRaises(mod.ErroDeGuarda):
            g._verificar_coerencia()

    def test_base_com_main_declarada_como_producao_e_coerente(self):
        guarda("production", database="cliente-main-12345")._verificar_coerencia()

    def test_base_de_staging_passa(self):
        guarda("brodoo_dev", database="cliente-brodoo-98765")._verificar_coerencia()

    def test_base_vazia_nao_parece_producao(self):
        # O nome pode vir vazio e ser resolvido pelo auto-heal; vazio não é produção.
        guarda("brodoo_dev", database="")._verificar_coerencia()


class TestNormalizacaoDeUrl(unittest.TestCase):
    def test_remove_o_sufixo_odoo_do_backoffice(self):
        # A partir do Odoo 17 é este o URL que se copia do browser, e os endpoints
        # da API vivem na raiz: com o sufixo, a autenticação devolve 400 sem dizer porquê.
        self.assertEqual("https://c.odoo.com", mod.normalizar_base_url("https://c.odoo.com/odoo"))
        self.assertEqual("https://c.odoo.com", mod.normalizar_base_url("https://c.odoo.com/odoo/"))

    def test_remove_barras_finais(self):
        self.assertEqual("https://c.odoo.com", mod.normalizar_base_url("https://c.odoo.com/"))

    def test_tolera_vazio(self):
        self.assertEqual("", mod.normalizar_base_url(""))
        self.assertEqual("", mod.normalizar_base_url(None))

    def test_nao_corta_odoo_a_meio_do_dominio(self):
        self.assertEqual("https://odoo.cliente.pt", mod.normalizar_base_url("https://odoo.cliente.pt"))


class TestFicheiroDeLigacao(unittest.TestCase):
    def escrever(self, dados, encoding="utf-8"):
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding=encoding)
        if isinstance(dados, str):
            fh.write(dados)
        else:
            json.dump(dados, fh)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_finalidade_em_falta_e_recusada(self):
        caminho = self.escrever({"base_url": "https://c.odoo.com", "login": "u", "api_key": "k"})
        with self.assertRaises(ValueError) as ctx:
            mod.resolver_alvo(caminho)
        self.assertIn("purpose", str(ctx.exception))

    def test_finalidade_invalida_e_recusada(self):
        caminho = self.escrever({"purpose": "producao", "base_url": "https://c.odoo.com",
                                 "login": "u", "api_key": "k"})
        with self.assertRaises(ValueError):
            mod.resolver_alvo(caminho)

    def test_campos_obrigatorios_em_falta(self):
        caminho = self.escrever({"purpose": "brodoo_dev", "base_url": "https://c.odoo.com"})
        with self.assertRaises(ValueError) as ctx:
            mod.resolver_alvo(caminho)
        self.assertIn("login", str(ctx.exception))

    def test_ficheiro_inexistente_da_erro_util(self):
        # ValueError e não FileNotFoundError: quem chama trata os dois casos na mesma via.
        with self.assertRaises(ValueError):
            mod.resolver_alvo(os.path.join(tempfile.gettempdir(), "nao-existe-de-todo.json"))

    def test_json_invalido_da_erro_util(self):
        caminho = self.escrever("{ isto nao e json")
        with self.assertRaises(ValueError) as ctx:
            mod.resolver_alvo(caminho)
        self.assertIn("JSON", str(ctx.exception))

    def test_tolera_bom(self):
        # O Notepad, o Set-Content -Encoding utf8 e o VS Code escrevem BOM com facilidade.
        caminho = self.escrever({"purpose": "client_test", "base_url": "https://c.odoo.com/odoo",
                                 "login": "u", "api_key": "k"}, encoding="utf-8-sig")
        alvo = mod.resolver_alvo(caminho)
        self.assertEqual("client_test", alvo.purpose)

    def test_ligacao_valida_normaliza_o_url(self):
        caminho = self.escrever({"purpose": "brodoo_dev", "base_url": "https://c.odoo.com/odoo/",
                                 "database": "c-brodoo-1", "login": "u", "api_key": "k"})
        alvo = mod.resolver_alvo(caminho)
        self.assertEqual("https://c.odoo.com", alvo.base_url)
        self.assertFalse(alvo.parece_producao)


class TestResolverPorProjeto(unittest.TestCase):
    def test_finalidade_invalida_falha_antes_de_tocar_na_rede(self):
        with self.assertRaises(ValueError) as ctx:
            mod.resolver_alvo_por_projeto("um-projeto", "producao")
        self.assertIn("Finalidade", str(ctx.exception))

    def test_credenciais_em_falta_nomeiam_o_ficheiro_pedido(self):
        # Caminho explícito que não existe: o erro tem de dizer QUAL ficheiro faltou,
        # senão quem passou o parâmetro não sabe se foi ignorado.
        inexistente = os.path.join(tempfile.gettempdir(), "sem-credenciais-brodoo.json")
        with self.assertRaises(ValueError) as ctx:
            mod.resolver_alvo_por_projeto("um-projeto", "brodoo_dev", credenciais_brodoo=inexistente)
        self.assertIn("sem-credenciais-brodoo.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
