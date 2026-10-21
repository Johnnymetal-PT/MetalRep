"""
Coerência entre os documentos que declaram o estado do `_pg_template`.

PORQUE EXISTE
    O `PG_CURRENT_WORKING_STATE.md` é o ponto de entrada operativo declarado, e chegou
    a anunciar a release `v2.9.1` com o `CHANGELOG.md` em `v2.21.2` — doze releases de
    atraso, num ficheiro lido por agentes. O `BLK-000` do backlog existiu para corrigir
    exactamente essa divergência, foi dado por fechado, e ela regressou.

    A causa não foi desleixo: foi guardar o mesmo facto em dois sítios e confiar em que
    alguém se lembrasse dos dois. Aqui a duplicação é eliminada num caso (o estado
    operativo deixa de declarar versão) e policiada no outro (o registo de versionamento
    tem de coincidir com o CHANGELOG, porque é para isso que existe).

Correr da raiz do repositório:
    python -m unittest scripts.tests.test_pg_docs_coerencia
"""

import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VERSAO = re.compile(r"v\d+\.\d+\.\d+")

# Uma *declaração* é uma entrada de registo: a linha existe para dizer qual é a release.
# Distingue-se de uma menção narrativa -- "resumo da release fechada: ... (v2.22.0) ..."
# menciona versões a contar o que aconteceu, e isso é legítimo em qualquer documento.
# Sem esta distinção o teste reprovava os próprios resumos que descrevem a história.
DECLARACAO = re.compile(
    r"^-\s*(última|ultima)?\s*(release\s+fechada|release\s+mais\s+recente"
    r"|vers[ãa]o\s+atual|vers[ãa]o\s+corrente)[^:]*:",
    re.IGNORECASE,
)


def ler(*partes):
    with open(os.path.join(RAIZ, *partes), encoding="utf-8") as fh:
        return fh.read()


def versao_do_changelog():
    """A primeira entrada `## vX.Y.Z` do CHANGELOG é a release fechada."""
    for linha in ler("CHANGELOG.md").splitlines():
        if linha.startswith("## v"):
            achado = VERSAO.search(linha)
            if achado:
                return achado.group(0)
    raise AssertionError("CHANGELOG.md sem nenhuma entrada '## vX.Y.Z'")


class TestEstadoOperativo(unittest.TestCase):
    def setUp(self):
        self.texto = ler("docs", "PG_CURRENT_WORKING_STATE.md")

    def test_nao_declara_a_versao_da_release(self):
        # O defeito original: uma linha a afirmar qual é a release fechada. Mencionar
        # versões a contar o que aconteceu é legítimo; declarar a corrente não é, porque
        # é um facto que vive no CHANGELOG e que aqui envelhece em silêncio.
        ofensivas = [
            linha.strip()
            for linha in self.texto.splitlines()
            if VERSAO.search(linha) and DECLARACAO.search(linha)
        ]
        self.assertEqual(
            [], ofensivas,
            "PG_CURRENT_WORKING_STATE.md voltou a declarar a versao da release; "
            "esse facto vive no CHANGELOG.md. Linhas: %s" % ofensivas,
        )

    def test_aponta_para_o_changelog(self):
        # Se o documento não diz a versão, tem de dizer onde ela está.
        self.assertIn("CHANGELOG.md", self.texto)

    def test_tem_data_visivel_no_estado(self):
        # O juízo (frente dominante, bloqueio, próximo passo) decai. A data é o que
        # permite a quem lê decidir se ainda pode confiar nele.
        self.assertRegex(
            self.texto, r"##\s+Estado atual\s+[—-]\s+\d{4}-\d{2}-\d{2}",
            "o bloco de estado tem de trazer a data a que se refere",
        )


class TestRegistoDeVersionamento(unittest.TestCase):
    def test_coincide_com_o_changelog(self):
        # Aqui a duplicação é deliberada -- é um registo -- por isso é policiada em vez
        # de eliminada. Foi assim que 'v2.21.2' ficou registado enquanto o CHANGELOG
        # ja ia noutra versao.
        esperada = versao_do_changelog()
        texto = ler("docs", "PG_TEMPLATE_VERSIONING.md")
        declaradas = {
            achado.group(0)
            for linha in texto.splitlines()
            if DECLARACAO.search(linha)
            for achado in [VERSAO.search(linha)]
            if achado
        }
        self.assertTrue(
            declaradas,
            "PG_TEMPLATE_VERSIONING.md deixou de declarar a release fechada",
        )
        self.assertEqual(
            {esperada}, declaradas,
            "PG_TEMPLATE_VERSIONING.md declara %s e o CHANGELOG esta em %s"
            % (sorted(declaradas), esperada),
        )


class TestChangelog(unittest.TestCase):
    def test_a_entrada_do_topo_e_a_versao_mais_alta(self):
        # Uma entrada nova inserida abaixo de outra passa despercebida e faz o registo de
        # versão apontar para o lado errado. Verifica-se a versão e não a data: o
        # histórico tem entradas antigas fora de ordem cronológica, e reescrever o
        # passado de outra pessoa para satisfazer um teste seria trocar o problema.
        versoes = re.findall(r"^## v(\d+)\.(\d+)\.(\d+)", ler("CHANGELOG.md"), re.M)
        self.assertGreater(len(versoes), 1, "CHANGELOG com menos de duas entradas")
        numericas = [tuple(int(parte) for parte in v) for v in versoes]
        self.assertEqual(max(numericas), numericas[0],
                         "a entrada do topo do CHANGELOG nao e a versao mais alta")


if __name__ == "__main__":
    unittest.main()


class TestStudioProibido(unittest.TestCase):
    """
    O Odoo Studio deixou de ser um passo da ordem de decisão (decisão de Bruno Pinheiro,
    2026-09-11). A proibição está escrita como proibição e não como omissão, de propósito:
    apagar a menção faria o Studio parecer esquecido, e reentraria como «opção leve» — que
    é exactamente como entrou no givachoice, onde criou quatro registos
    `ir.actions.act_window.view` e pôs a aplicação do cliente a abrir no formulário de
    criação.

    Estes testes travam a reintrodução silenciosa. Não policiam o texto todo: policiam os
    dois sítios onde o Studio voltaria a ser uma escolha legítima — a ordem de decisão e a
    lista de classificações da recomendação final.
    """

    def setUp(self):
        caminho = os.path.join(RAIZ, "templates", "AGENTS_SHARED.md")
        with open(caminho, encoding="utf-8") as fh:
            self.contrato = fh.read()

    def test_a_proibicao_esta_escrita(self):
        self.assertIn("O Odoo Studio não é um passo desta ordem", self.contrato)
        self.assertIn("Proibido criar", self.contrato)

    def test_a_ordem_de_decisao_nao_tem_studio(self):
        inicio = self.contrato.index("## Ordem obrigatória de decisão")
        fim = self.contrato.index("### O Odoo Studio não é um passo desta ordem")
        ordem = self.contrato[inicio:fim]
        self.assertNotIn("Studio", ordem, "o Studio voltou a ser um passo da ordem de decisão")
        self.assertIn("3. desenvolvimento custom", ordem, "a ordem tem de terminar em custom")

    def test_nao_e_categoria_de_recomendacao(self):
        inicio = self.contrato.index("## Classificação obrigatória da recomendação final")
        bloco = self.contrato[inicio:inicio + 700]
        self.assertNotIn("`Odoo Studio`", bloco,
                         "o Studio voltou a ser uma classificação de recomendação final")

    def test_lidar_com_o_studio_existente_continua_permitido(self):
        # A proibição é de CRIAR. Se isto falhar, a regra passou a impedir o trabalho
        # legítimo de migrar o Studio que os clientes já têm.
        self.assertIn("nunca apagar", self.contrato)
        self.assertIn("migrá-lo para standard", self.contrato)

    def test_os_prompts_de_apoio_nao_contradizem_o_contrato(self):
        # Um documento de apoio que ainda mande avaliar Studio como opção manda o agente
        # fazer o contrário do contrato -- e o agente lê os dois.
        for nome in ("PG_DECISION_ENGINE_PROMPT.md", "PG_CHALLENGER_PROMPT.md",
                     "PG_PRE_RESPONSE_CHECKLIST.md", "PG_FIT_GAP_FRAMING_PROMPT.md"):
            caminho = os.path.join(RAIZ, "docs", nome)
            with open(caminho, encoding="utf-8") as fh:
                texto = fh.read()
            if "Studio" not in texto:
                continue
            self.assertIn("proibido", texto,
                          "%s fala de Studio sem dizer que está proibido" % nome)


class TestComparadorDeAddons(unittest.TestCase):
    """
    A normalização de versões existe porque a primeira execução deste comparador reportou
    20 divergências falsas em 29 módulos: o Odoo prefixa `latest_version` com a série
    quando o manifest a omite, pelo que `1.0.84` e `19.0.1.0.84` são a mesma versão.

    Um comparador com falsos positivos é pior do que não existir — ensina a ignorar o
    alarme. Estes testes travam a regressão nos dois sentidos: o que deve normalizar, e o
    que NÃO deve (senão passa a esconder divergências verdadeiras, que é pior ainda).
    """

    @classmethod
    def setUpClass(cls):
        import importlib.util
        caminho = os.path.join(RAIZ, "scripts", "pg_compare_client_addons.py")
        spec = importlib.util.spec_from_file_location("pg_compare", caminho)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def iguais(self, a, b, serie=None):
        return self.mod.normalizar(a, serie) == self.mod.normalizar(b, serie)

    def test_prefixo_da_serie_nao_conta_como_divergencia(self):
        self.assertTrue(self.iguais("1.0.84", "19.0.1.0.84", "19.0"))
        self.assertTrue(self.iguais("1.0", "19.0.1.0", "19.0"))
        self.assertTrue(self.iguais("2.0.0", "19.0.2.0.0", "19.0"))

    def test_manifest_que_ja_traz_a_serie_continua_igual(self):
        self.assertTrue(self.iguais("19.0.1.0", "19.0.1.0", "19.0"))

    def test_divergencia_verdadeira_continua_a_ser_detectada(self):
        # O risco de normalizar de mais: esconder o que interessa.
        self.assertFalse(self.iguais("1.0.5", "19.0.1.0.6", "19.0"))
        self.assertFalse(self.iguais("2.0", "3.0"))

    def test_sem_serie_o_heuristico_nao_destroi_versoes_curtas(self):
        self.assertTrue(self.iguais("1.0.84", "19.0.1.0.84"))
        self.assertTrue(self.iguais("19.0", "19.0"))
        self.assertFalse(self.iguais("19.0", "17.0"))

    def test_serie_diferente_nao_e_removida(self):
        # Um modulo de 17.0 comparado com serie 19.0 nao pode passar por igual: foi
        # exactamente assim que se descobriu que a base client_test do givachoice corria
        # Odoo 17 contra os 19 da producao.
        self.assertFalse(self.iguais("1.0", "17.0.1.0", "19.0"))


class TestGateDaSerieDoDestino(unittest.TestCase):
    """
    O passo 1 da regra de implantação: confirmar a série do destino contra o próprio
    destino, e não contra o que se julga.

    `FACTO OBSERVADO` (givachoice): código v17 foi implantado sobre o servidor de testes
    v19, e só um backup manual feito por sorte o desfez. A pergunta que teria evitado isso
    custa uma chamada, e estes testes garantem que continua a ser feita.
    """

    @classmethod
    def setUpClass(cls):
        import importlib.util
        caminho = os.path.join(RAIZ, "scripts", "pg_compare_client_addons.py")
        spec = importlib.util.spec_from_file_location("pg_compare_serie", caminho)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _com_base(self, versao_base):
        """Substitui a chamada ao Odoo por um valor conhecido."""
        original = self.mod.modulos_instalados
        self.mod.modulos_instalados = lambda k, p, pref: ({"base": versao_base}
                                                         if versao_base else {})
        self.addCleanup(setattr, self.mod, "modulos_instalados", original)
        return self.mod.serie_do_destino("qualquer", "production")

    def test_extrai_a_serie_da_versao_do_modulo_base(self):
        self.assertEqual("19.0", self._com_base("19.0.1.3"))
        self.assertEqual("17.0", self._com_base("17.0.1.3"))
        self.assertEqual("18.0", self._com_base("18.0.1.0.2"))

    def test_sem_resposta_devolve_vazio_e_nao_adivinha(self):
        # Vazio faz o chamador abortar. Adivinhar aqui seria pior do que falhar: o
        # objectivo do gate é não prosseguir às cegas.
        self.assertEqual("", self._com_base(None))

    def test_a_regra_de_implantacao_esta_no_contrato(self):
        caminho = os.path.join(RAIZ, "templates", "AGENTS_SHARED.md")
        with open(caminho, encoding="utf-8") as fh:
            contrato = fh.read()
        self.assertIn("Implantar código no servidor de um cliente", contrato)
        # os cinco passos têm de estar todos: sem o resguardo ou sem a verificação
        # posterior, a regra deixa de cobrir os dois incidentes que a originaram
        self.assertIn("Resguardo antes de tocar", contrato)
        self.assertIn("Verificar depois", contrato)
        self.assertIn("Dry-run primeiro", contrato)

    def test_o_contrato_exige_prova_de_codigo_e_nao_so_de_versao(self):
        caminho = os.path.join(RAIZ, "templates", "AGENTS_SHARED.md")
        with open(caminho, encoding="utf-8") as fh:
            contrato = fh.read()
        # A versão do manifest não prova o código: no GBUK a 18.0.2.8.3 nomeou dois
        # códigos diferentes. Se esta exigência cair, "verificado" volta a valer nada.
        self.assertIn("não prova", contrato)
        self.assertIn("18.0.2.8.3", contrato)
