from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        help='Documento de transformação relacionado a este picking'
    )

    def button_validate(self):
        """Impede validar directamente um picking gerido por transformação.

        Os pickings de transformação (saída do input, entrada das placas) só
        devem ser validados pelo próprio documento — o OUT no ``action_start`` e
        o IN no ``action_done`` —, que passam o contexto
        ``from_transformation_document=True``. Uma validação directa criaria
        SVL/PCMP fora do fluxo (sem landed cost, sem mudar o documento p/ done).
        """
        if not self.env.context.get('from_transformation_document'):
            bloqueados = self.filtered('transformation_id')
            if bloqueados:
                nomes = ', '.join(bloqueados.mapped('transformation_id.name'))
                raise UserError(_(
                    "Este picking é gerido pelo Documento de Transformação (%s). "
                    "Conclua a transformação através do documento — não valide o "
                    "picking directamente."
                ) % nomes)
        return super().button_validate()

    def _update_move_costs_from_output_lines(self):
        """
        DEPRECADO: Este método foi substituído por:
        - transformation_document._update_move_base_costs() para custo BASE
        - stock.landed.cost para custos adicionais

        O método é mantido por retrocompatibilidade mas não faz nada.
        """
        _logger.warning(
            f"DEPRECADO: _update_move_costs_from_output_lines() chamado em {self.name}. "
            f"Use transformation_document._update_move_base_costs() e stock.landed.cost."
        )
