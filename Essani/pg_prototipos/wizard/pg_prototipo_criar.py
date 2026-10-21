# -*- coding: utf-8 -*-
"""O formulário do vendedor: cria artigo, projeto e ligação num gesto, a partir da
oportunidade."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

MODELO_PROJETO_POR_OMISSAO = "Produto Novo"


class PgPrototipoCriar(models.TransientModel):
    _name = "pg.prototipo.criar"
    _description = "Criar protótipo a partir de uma oportunidade"

    lead_id = fields.Many2one("crm.lead", string="Oportunidade", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Cliente")
    nome = fields.Char(string="Nome do protótipo", required=True)
    categoria_id = fields.Many2one(
        "product.category", string="Categoria de protótipo", required=True,
        # `child_of` inclui a propria raiz. Escolher a raiz cria um prototipo sem
        # especificacao nenhuma e sem aviso, porque so as familias -- as filhas --
        # tem definicao de propriedades. Tirar a raiz da lista fecha essa armadilha.
        domain="[('id', 'child_of', categoria_raiz_id), "
               "('id', '!=', categoria_raiz_id)]",
        help="Define que especificações são pedidas. Acrescentar uma categoria nova "
             "é configuração, não desenvolvimento.",
    )
    categoria_raiz_id = fields.Many2one("product.category", readonly=True)
    gestor_id = fields.Many2one(
        "res.users", string="Gestor de projeto", required=True,
        domain="[('share', '=', False)]",
        help="Quem gere a produção do protótipo. É quem recebe as alterações de "
             "especificação acordadas com o cliente.",
    )
    gestor_ids = fields.Many2many(
        "res.users", "pg_prototipo_criar_gestor_rel", "wizard_id", "user_id",
        string="Outros gestores",
        domain="[('share', '=', False)]",
        help="Gestores adicionais do protótipo. Recebem, tal como o gestor de "
             "projeto, as alterações de especificação.",
    )
    modelo_projeto_id = fields.Many2one(
        "project.project", string="Modelo de projeto", required=True,
        domain="[('is_template', '=', True)]",
        help="Traz as etapas e as tarefas que todos os protótipos percorrem.",
    )
    # A definição das propriedades vem da categoria escolhida: é isto que faz os
    # campos de especificação mudarem no ecrã conforme a categoria, sem um campo
    # fixo por cada característica de cada família de produto.
    especificacoes = fields.Properties(
        string="Especificações pedidas",
        definition="categoria_id.product_properties_definition",
    )
    notas = fields.Text(
        string="Requisitos do cliente",
        help="O que o cliente pediu por palavras dele. Fica na descrição do projeto.",
    )

    @api.onchange("categoria_id")
    def _onchange_categoria_id(self):
        """Devolve as especificacoes ja preenchidas com a definicao da categoria.

        Sem isto, o ecra so mostra os campos quando o cliente web vai buscar a
        definicao por sua conta, numa segunda ida ao servidor. Medido numa gravacao
        de ecra a 30/09: a categoria e escolhida aos 3,5s e os campos so aparecem
        aos 6,5s. Durante esses tres segundos a seccao "Especificacoes pedidas pelo
        cliente" aparece vazia, quem esta a preencher conclui que nao ha nada para
        preencher, carrega em criar, e os campos surgem no instante em que a janela
        se fecha. Foi isto que a cliente reportou como "nao fica disponivel tempo
        suficiente", e o que deixou 24 prototipos sem uma unica especificacao.

        Devolvendo-as aqui, vem na mesma ida ao servidor que ja acontece ao escolher
        a categoria, e o ecra desenha-as de imediato.
        """
        for registo in self:
            definicao = registo.categoria_id.product_properties_definition
            registo.especificacoes = definicao or []

    @api.model
    def default_get(self, fields_list):
        valores = super().default_get(fields_list)
        lead = self.env["crm.lead"].browse(self.env.context.get("active_id"))
        if lead.exists():
            valores.update({
                "lead_id": lead.id,
                "partner_id": lead.partner_id.id,
                "nome": lead.name,
                "gestor_id": (lead.user_id or self.env.user).id,
            })
        raiz = self.env["project.project"]._pg_categoria_raiz()
        if raiz:
            valores["categoria_raiz_id"] = raiz.id
        modelo = self.env["project.project"].search(
            [("is_template", "=", True), ("name", "=", MODELO_PROJETO_POR_OMISSAO)],
            limit=1)
        if not modelo:
            modelo = self.env["project.project"].search(
                [("is_template", "=", True)], limit=1)
        if modelo:
            valores["modelo_projeto_id"] = modelo.id
        return valores

    def action_criar(self):
        """Atribui a referência, cria artigo e projeto, e devolve o protótipo aberto."""
        self.ensure_one()

        # Validar tudo antes de consumir a sequência: um número gasto numa tentativa
        # falhada não volta atrás e deixa um buraco na numeração.
        if not self.categoria_id:
            raise UserError(_("Escolha a categoria do protótipo."))
        if not self.modelo_projeto_id:
            raise UserError(_(
                "Não há nenhum modelo de projeto para os protótipos herdarem as "
                "etapas. Marque um projeto como modelo primeiro."))

        referencia = self.env["ir.sequence"].next_by_code("pg.prototipo.ref")
        if not referencia:
            raise UserError(_(
                "Sequência 'pg.prototipo.ref' não encontrada. Sem referência não se "
                "cria o protótipo."))

        artigo = self.env["product.template"].create({
            "name": self.nome,
            "default_code": referencia,
            "categ_id": self.categoria_id.id,
            "is_storable": False,
            "product_properties": self.especificacoes,
        })

        projeto = self.modelo_projeto_id.copy({
            "name": "%s [%s]" % (self.nome, referencia),
        })
        # `is_template` sobrevive à cópia e não se deixa limpar nos valores do copy();
        # sem este write o protótipo nasceria como modelo e não apareceria na lista.
        projeto.write({
            "is_template": False,
            "user_id": self.gestor_id.id,
            # O principal já está em `user_id`; não se repete na lista dos outros.
            "pg_gestor_ids": [(6, 0, (self.gestor_ids - self.gestor_id).ids)],
            "partner_id": self.partner_id.id,
            "description": self.notas or False,
            "pg_artigo_prototipo": artigo.id,
        })

        if self.lead_id:
            self.lead_id.message_post(body=_(
                "Protótipo %(ref)s criado a partir desta oportunidade: %(projeto)s",
                ref=referencia, projeto=projeto.display_name))

        return projeto._pg_accao_abrir(_("Protótipo %s", referencia))
