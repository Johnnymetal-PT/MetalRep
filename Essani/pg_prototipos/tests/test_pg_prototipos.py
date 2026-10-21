# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPgPrototipos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categoria_raiz = cls.env["product.category"].create({
            "name": "Protótipos",
        })
        cls.categoria = cls.env["product.category"].create({
            "name": "Fontes de alimentação",
            "parent_id": cls.categoria_raiz.id,
        })
        cls.modelo = cls.env["project.project"].create({
            "name": "Produto Novo",
            "is_template": True,
        })
        cls.gestor = cls.env.user
        cls.parceiro = cls.env["res.partner"].create({"name": "Cliente piloto"})
        cls.lead = cls.env["crm.lead"].create({
            "name": "Fonte 48 V",
            "partner_id": cls.parceiro.id,
            "user_id": cls.gestor.id,
        })
        cls.sequencia = cls.env.ref("pg_prototipos.seq_pg_prototipo_ref")
        cls.sequencia.write({
            "prefix": "PROT-2099-",
            "number_next_actual": 1,
        })

    def _criar_prototipo(self):
        assistente = self.env["pg.prototipo.criar"].create({
            "lead_id": self.lead.id,
            "partner_id": self.parceiro.id,
            "nome": "Fonte 48 V",
            "categoria_id": self.categoria.id,
            "categoria_raiz_id": self.categoria_raiz.id,
            "gestor_id": self.gestor.id,
            "modelo_projeto_id": self.modelo.id,
        })
        # Guardada para os testes que verificam a própria ação devolvida, e não só
        # o projeto que dela sai.
        self._ultima_accao = assistente.action_criar()
        return self.env["project.project"].browse(self._ultima_accao["res_id"])

    def test_assistente_cria_artigo_e_projeto_ligados(self):
        projeto = self._criar_prototipo()

        self.assertTrue(projeto.exists())
        self.assertFalse(projeto.is_template)
        self.assertEqual(projeto.user_id, self.gestor)
        self.assertEqual(projeto.partner_id, self.parceiro)
        self.assertEqual(projeto.pg_artigo_prototipo.default_code, "PROT-2099-0001")
        self.assertEqual(projeto.pg_artigo_prototipo.categ_id, self.categoria)

    def test_nova_versao_herda_artigo_e_linhagem(self):
        projeto = self._criar_prototipo()

        acao = projeto.action_pg_nova_versao()
        nova_versao = self.env["project.project"].browse(acao["res_id"])

        self.assertEqual(nova_versao.pg_versao_origem, projeto)
        self.assertEqual(nova_versao.pg_artigo_prototipo.default_code, "PROT-2099-0002")
        self.assertNotEqual(
            nova_versao.pg_artigo_prototipo,
            projeto.pg_artigo_prototipo,
        )
        self.assertFalse(nova_versao.is_template)

    def test_nova_versao_recusa_projeto_sem_artigo(self):
        projeto = self.env["project.project"].create({"name": "Projeto normal"})

        with self.assertRaises(UserError):
            projeto.action_pg_nova_versao()

    def test_alteracao_de_especificacoes_cria_atividade(self):
        projeto = self._criar_prototipo()
        artigo = projeto.pg_artigo_prototipo
        atividades_antes = self.env["mail.activity"].search_count([
            ("res_model", "=", "project.project"),
            ("res_id", "=", projeto.id),
        ])

        artigo.write({"product_properties": {}})

        atividades_depois = self.env["mail.activity"].search_count([
            ("res_model", "=", "project.project"),
            ("res_id", "=", projeto.id),
        ])
        self.assertEqual(atividades_depois, atividades_antes + 1)

    def test_accao_devolvida_nao_volta_para_tras(self):
        """O sintoma que a cliente reportou: o protótipo aparecia e desaparecia.

        Com `target: 'current'` a ação entrava por cima da oportunidade e o
        formulário que lançou o botão recarregava-se logo a seguir, voltando a ficar
        por cima. Com `'main'` não há nada atrás para voltar.

        As vistas vão explícitas para o Odoo não escolher sozinho: abrir um
        `project.project` sem as indicar pode cair na vista de tarefas.
        """
        self._criar_prototipo()
        acao = self._ultima_accao

        self.assertEqual(acao["target"], "main")
        self.assertEqual(acao["res_model"], "project.project")
        self.assertTrue(acao.get("res_id"))
        self.assertEqual(acao.get("views"), [(False, "form")])

    def test_nova_versao_abre_da_mesma_maneira(self):
        """As duas portas de entrada partilham o mesmo caminho, e o mesmo defeito
        corrigido — senão uma fica boa e a outra volta a fechar-se sozinha."""
        projeto = self._criar_prototipo()
        acao = projeto.action_pg_nova_versao()

        self.assertEqual(acao["target"], "main")
        self.assertEqual(acao.get("views"), [(False, "form")])

    def test_botao_do_crm_so_aparece_em_modo_programador(self):
        """A condição que a cliente pôs para os módulos irem para produção.

        O circuito vai para lá pronto, mas fechado a quem usa o CRM todos os dias,
        até a Essani dizer que está pronto para os comerciais. Sem este teste, uma
        alteração de vista publicava o botão sem ninguém dar por isso — e a condição
        que destravou a passagem a produção caía em silêncio.
        """
        vista = self.env.ref("pg_prototipos.view_crm_lead_form_pg_prototipo")
        self.assertIn(
            'groups="base.group_no_one"', vista.arch,
            "O botão Criar protótipo deixou de estar restrito ao modo programador.")

    def test_especificacoes_vem_preenchidas_ao_escolher_a_categoria(self):
        """Os campos tinham de aparecer de imediato, não três segundos depois.

        Medido a 30/09 por gravação de ecrã: a categoria era escolhida aos 3,5s e os
        campos só surgiam aos 6,5s. Nesse intervalo a secção mostra-se vazia, quem
        preenche conclui que não há nada e carrega em criar. Ficaram 24 protótipos
        sem uma única especificação.
        """
        self.categoria.product_properties_definition = [
            {"name": "req_tensao_entrada", "type": "char",
             "string": "Tensão de entrada"},
            {"name": "req_potencia_w", "type": "float", "string": "Potência (W)"},
        ]
        assistente = self.env["pg.prototipo.criar"].create({
            "nome": "Ensaio das especificações",
            "categoria_id": self.categoria.id,
            "modelo_projeto_id": self.modelo.id,
            "gestor_id": self.env.user.id,
        })
        assistente._onchange_categoria_id()

        nomes = {p.get("name") for p in (assistente.especificacoes or [])}
        self.assertEqual(
            nomes, {"req_tensao_entrada", "req_potencia_w"},
            "O assistente não devolveu as especificações da categoria escolhida.")

    def test_tarefa_mostra_o_artigo_do_prototipo(self):
        """Pedido da Ana Valente na reunião de 30/09.

        Quem está a trabalhar uma tarefa quer chegar às especificações sem voltar
        ao projeto. O campo é relacionado e não copiado: o artigo vive no projeto
        e um protótipo tem dezenas de tarefas, todas a apontar para o mesmo.
        """
        projeto = self._criar_prototipo()
        tarefa = self.env["project.task"].create(
            {"name": "Desenhar o esquema", "project_id": projeto.id})

        self.assertTrue(projeto.pg_artigo_prototipo)
        self.assertEqual(tarefa.pg_artigo_prototipo, projeto.pg_artigo_prototipo)

    def test_o_artigo_na_tarefa_acompanha_o_projeto(self):
        """Relacionado, não copiado: mudar no projeto muda em todas as tarefas.

        Se fosse copiado, ficavam duas verdades e bastava alguém corrigir o artigo
        no projeto para as tarefas passarem a apontar para o anterior, em silêncio.
        """
        projeto = self._criar_prototipo()
        tarefa = self.env["project.task"].create(
            {"name": "Montar o ensaio", "project_id": projeto.id})
        outro = self.env["product.template"].create({
            "name": "Outro artigo", "categ_id": self.categoria.id})

        projeto.pg_artigo_prototipo = outro
        tarefa.invalidate_recordset(["pg_artigo_prototipo"])

        self.assertEqual(tarefa.pg_artigo_prototipo, outro)

    def test_tarefa_fora_de_prototipo_nao_tem_artigo(self):
        """O campo existe em todas as tarefas; só tem valor nas que são protótipo."""
        projeto = self.env["project.project"].create({"name": "Projeto normal"})
        tarefa = self.env["project.task"].create(
            {"name": "Tarefa normal", "project_id": projeto.id})
        self.assertFalse(tarefa.pg_artigo_prototipo)


    def _atividades(self, projeto):
        return self.env["mail.activity"].search([
            ("res_model", "=", "project.project"),
            ("res_id", "=", projeto.id),
        ])

    def test_aviso_chega_a_todos_os_gestores(self):
        """Pedido da Ana Valente na reunião de 30/09: mais do que um gestor.

        Decidido com a equipa: o aviso de alteração de especificações vai para todos
        os gestores, não só para o principal.
        """
        extra = self.env["res.users"].create({
            "name": "Segundo gestor", "login": "pg_segundo_gestor"})
        projeto = self._criar_prototipo()
        projeto.pg_gestor_ids = extra

        projeto.pg_artigo_prototipo.write({"product_properties": {}})

        self.assertEqual(
            self._atividades(projeto).mapped("user_id"), self.gestor | extra)

    def test_projeto_so_com_gestor_principal_avisa_como_antes(self):
        """Os projetos que já existem só têm `user_id`: nada muda para eles."""
        projeto = self._criar_prototipo()
        self.assertFalse(projeto.pg_gestor_ids)

        projeto.pg_artigo_prototipo.write({"product_properties": {}})

        atividades = self._atividades(projeto)
        self.assertEqual(len(atividades), 1)
        self.assertEqual(atividades.user_id, self.gestor)

    def test_gestor_repetido_recebe_um_so_aviso(self):
        """Se o principal também estiver na lista dos outros, não recebe dois."""
        projeto = self._criar_prototipo()
        projeto.pg_gestor_ids = self.gestor

        projeto.pg_artigo_prototipo.write({"product_properties": {}})

        self.assertEqual(len(self._atividades(projeto)), 1)

    def test_assistente_grava_os_outros_gestores(self):
        extra = self.env["res.users"].create({
            "name": "Segundo gestor", "login": "pg_segundo_gestor"})
        assistente = self.env["pg.prototipo.criar"].create({
            "lead_id": self.lead.id,
            "partner_id": self.parceiro.id,
            "nome": "Fonte com dois gestores",
            "categoria_id": self.categoria.id,
            "categoria_raiz_id": self.categoria_raiz.id,
            "gestor_id": self.gestor.id,
            # O principal vem também na lista: não deve ficar duplicado em `pg_gestor_ids`.
            "gestor_ids": [(6, 0, (self.gestor | extra).ids)],
            "modelo_projeto_id": self.modelo.id,
        })
        projeto = self.env["project.project"].browse(
            assistente.action_criar()["res_id"])

        self.assertEqual(projeto.user_id, self.gestor)
        self.assertEqual(projeto.pg_gestor_ids, extra)
