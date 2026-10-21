# -*- coding: utf-8 -*-
"""A tarefa do protótipo mostra a que artigo pertence, sem o ir buscar ao projeto."""

from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Campo relacionado, não copiado. O artigo já vive no projeto; duplicá-lo na
    # tarefa criava duas verdades que se podiam desencontrar -- e um protótipo
    # tem dezenas de tarefas, todas a apontar para o mesmo artigo.
    #
    # Não é guardado em coluna de propósito: serve para chegar ao artigo a partir
    # de qualquer tarefa, não para filtrar tarefas por artigo. Quem quer as tarefas
    # de um protótipo filtra pelo projeto, que é o que já faz hoje. Guardá-lo
    # obrigaria a recalcular a coluna inteira sempre que um projeto mudasse de
    # artigo, para um ganho que ninguém pediu.
    pg_artigo_prototipo = fields.Many2one(
        related="project_id.pg_artigo_prototipo",
        string="Artigo do protótipo",
        readonly=True,
        help="Artigo onde estão as especificações pedidas pelo cliente e os "
             "documentos deste protótipo. Vem do projeto; não se edita aqui.",
    )
