from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def _get_combination_name(self):
        """
        Override para incluir TODOS os valores de atributos no nome da variante.

        O método padrão do Odoo filtra:
        - Atributos com create_variant='no_variant'
        - Valores de linhas com apenas um valor possível

        Esta versão retorna todos os valores de atributos sem filtragem.
        """
        return ", ".join([ptav.name for ptav in self])
