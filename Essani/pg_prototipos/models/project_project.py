# -*- coding: utf-8 -*-
"""O protótipo, do lado do projeto: ligação ao artigo, linhagem de versões e a
criação de uma revisão a partir de uma existente."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Categoria-raiz onde vivem os artigos de protótipo. Sobrepõe-se com o parâmetro
# de sistema `pg_prototipos.categoria_raiz` quando a árvore tiver outro nome.
CATEGORIA_RAIZ_POR_OMISSAO = "Protótipos"


class ProjectProject(models.Model):
    _inherit = "project.project"

    pg_artigo_prototipo = fields.Many2one(
        "product.template",
        string="Artigo do protótipo",
        help="Artigo de catálogo que representa este protótipo. É nele que vivem as "
             "especificações, os documentos e, mais tarde, a lista de materiais.",
        index=True,
    )
    pg_versao_origem = fields.Many2one(
        "project.project",
        string="Versão de origem",
        help="Protótipo a partir do qual esta versão foi criada. É o que constrói a "
             "árvore de versões, em vez de a versão viver no nome do projeto.",
        index=True,
    )
    pg_versoes_ids = fields.One2many(
        "project.project", "pg_versao_origem", string="Versões seguintes",
    )
    pg_versoes_count = fields.Integer(compute="_compute_pg_versoes_count")
    pg_gestor_ids = fields.Many2many(
        "res.users", "pg_project_gestor_rel", "project_id", "user_id",
        string="Outros gestores de projeto",
        domain="[('share', '=', False)]",
        help="Gestores adicionais deste protótipo, além do gestor de projeto. Todos "
             "recebem o aviso quando as especificações mudam.",
    )

    @api.depends("pg_versoes_ids")
    def _compute_pg_versoes_count(self):
        for projeto in self:
            projeto.pg_versoes_count = len(projeto.pg_versoes_ids)

    def _pg_gestores(self):
        """Todos os gestores do protótipo: o gestor de projeto e os restantes.

        O `user_id` do Odoo continua a ser o gestor principal, e por isso um projeto
        que só o tem — todos os que existiam antes dos vários gestores — comporta-se
        exatamente como antes. Os outros juntam-se-lhe, sem repetir ninguém.
        """
        self.ensure_one()
        return self.user_id | self.pg_gestor_ids

    # ------------------------------------------------------------------
    # Nova versão
    # ------------------------------------------------------------------
    def action_pg_nova_versao(self):
        """Cria a revisão seguinte deste protótipo.

        Duplica artigo e projeto: as especificações viajam com o artigo, as etapas e
        tarefas com o projeto. É por isso que a versão nova nasce com o que a anterior
        tinha, em vez de em branco.
        """
        self.ensure_one()

        # Validar ANTES de consumir a sequência. Em PostgreSQL o nextval não volta
        # atrás com o rollback: uma referência gasta numa tentativa falhada fica
        # gasta para sempre, e abre um buraco na numeração que ninguém explica.
        if not self.pg_artigo_prototipo:
            raise UserError(_(
                "O projeto '%s' não é um protótipo: não tem artigo associado.\n\n"
                "Preencha 'Artigo do protótipo' antes de criar uma versão — é daí "
                "que vem a herança das especificações.", self.display_name))

        nova_ref = self.env["ir.sequence"].next_by_code("pg.prototipo.ref")
        if not nova_ref:
            raise UserError(_(
                "Sequência 'pg.prototipo.ref' não encontrada. Sem referência não se "
                "cria a versão."))

        artigo_novo = self.pg_artigo_prototipo.copy({
            "default_code": nova_ref,
            "name": self.pg_artigo_prototipo.name,
        })
        projeto_novo = self.copy({"name": "%s [%s]" % (self.name, nova_ref)})
        # O indicador de modelo sobrevive à cópia e não se deixa limpar nos valores
        # do copy(); sem este write, cada versão nasceria como projeto-modelo e
        # desapareceria da lista de projetos.
        projeto_novo.write({
            "is_template": False,
            "pg_artigo_prototipo": artigo_novo.id,
            "pg_versao_origem": self.id,
        })
        return projeto_novo._pg_accao_abrir(_("Nova versão"))

    def action_pg_ver_versoes(self):
        """Abre a árvore de versões que saíram deste protótipo."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Versões de %s", self.name),
            "res_model": "project.project",
            "domain": [("pg_versao_origem", "=", self.id)],
            "view_mode": "list,form",
        }

    # ------------------------------------------------------------------
    # Auxiliares partilhados com o assistente
    # ------------------------------------------------------------------
    def _pg_accao_abrir(self, titulo=None):
        """Abre este protótipo, e deixa-o aberto.

        `target: 'main'` e não `'current'`, que era o que estava. A cliente
        descreveu o sintoma com precisão: *"aparece efetivamente uma janela, mas não
        fica disponível tempo suficiente para conseguir ver. Automaticamente retorna
        a janela do CRM"* — e confirmou que o projeto era criado à mesma.

        O assistente é aberto por um botão do formulário da oportunidade. Quando ele
        devolve uma ação com `target: 'current'`, essa ação entra por cima da
        oportunidade, mas o formulário que lançou o botão recarrega-se a seguir e
        volta a ficar por cima — o protótipo aparece e desaparece. Com `'main'` a
        ação substitui a pilha inteira e não há nada atrás para voltar.

        As vistas vão explícitas para o Odoo não ter de as adivinhar: sem isso, abrir
        um `project.project` pela ação genérica pode cair na vista de tarefas em vez
        da ficha do projeto.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": titulo or self.display_name,
            "res_model": "project.project",
            "res_id": self.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "main",
        }

    @api.model
    def _pg_categoria_raiz(self):
        """Categoria-raiz dos protótipos, ou um conjunto vazio se não existir."""
        nome = self.env["ir.config_parameter"].sudo().get_param(
            "pg_prototipos.categoria_raiz", CATEGORIA_RAIZ_POR_OMISSAO)
        return self.env["product.category"].search(
            [("name", "=", nome), ("parent_id", "=", False)], limit=1)
