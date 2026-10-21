# -*- coding: utf-8 -*-

from odoo import models, fields

class SnippetCollection(models.Model):
    _name = 'snippet.collection'
    _description = 'Dynamic Snippet Collection'

    name = fields.Char(string='Collection Name', required=True)
    snippet_key = fields.Char(string='Snippet Technical Name', required=True)
    config_data = fields.Json(string='Configuration Data', required=True)
    user_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    preview_image = fields.Char(string='Preview Image')
