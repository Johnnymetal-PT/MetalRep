from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    scrap_transformation_line_id = fields.Many2one(
        'stock.scrap.transformation.line',
        string='Linha de Remediação',
        ondelete='set null',
        help='Linha de transformação de scrap que originou este move. '
             'Garante que duas linhas distintas (mesmo com dimensões iguais) '
             'não sejam fundidas pelo merge automático do Odoo.',
    )

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        """Adiciona scrap_transformation_line_id aos campos distintos.

        Sem isto, duas linhas de remediação com iguais lot_name+dimensões
        seriam fundidas num único move, perdendo-se uma das peças.
        """
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append('scrap_transformation_line_id')
        return distinct_fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    mh_account_move_count = fields.Integer(
        string='Nº Lançamentos', compute='_compute_mh_account_move_count')

    def _compute_mh_account_move_count(self):
        # Contador presente nas linhas de movimento. A leitura atravessa dois
        # modelos restritos — stock.move e depois account.move — e qualquer um
        # deles chega para rebentar a ficha. Quem trabalha no armazem nao tem
        # acesso a contabilidade, e e' o perfil que mais usa esta ficha.
        if not (self.env['stock.move'].has_access('read')
                and self.env['account.move'].has_access('read')):
            for line in self:
                line.mh_account_move_count = 0
            return
        for line in self:
            line.mh_account_move_count = len(line.move_id.account_move_ids)

    def action_get_account_moves(self):
        """Abre o lançamento contabilístico do movimento desta linha."""
        self.ensure_one()
        return self.move_id.action_get_account_moves()
