import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)

# Relatório por tipo de etiqueta em PDF. O ZPL sai por outro caminho (impressora
# térmica via IoT) e por isso não entra nesta tabela.
RELATORIOS_PDF = {
    'A5': 'pg_etiquetas.action_report_pg_etiqueta_a5_move',
    '5x8': 'pg_etiquetas.action_report_pg_etiqueta_5x8',
}


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pg_has_zpl_labels = fields.Boolean(
        string="Tem etiquetas ZPL",
        compute='_compute_pg_has_zpl_labels',
        help="Verdadeiro quando pelo menos um artigo da recepção usa etiqueta ZPL.",
    )

    @api.depends('move_ids.product_id.pg_label_type',
                 'move_line_ids.product_id.pg_label_type')
    def _compute_pg_has_zpl_labels(self):
        for picking in self:
            picking.pg_has_zpl_labels = any(
                move.product_id.pg_label_type == 'ZPL'
                for move in picking._pg_label_moves()
            )

    # -- recolha dos movimentos --------------------------------------------

    def _pg_label_moves(self):
        """Movimentos a etiquetar.

        Num rascunho os movimentos podem ainda não estar em `move_ids`; nesse caso
        recuperam-se pelas linhas de operação, senão o botão não imprimia nada
        precisamente no momento em que a recepção está a ser preparada.
        """
        self.ensure_one()
        movimentos = self.move_ids.filtered(lambda m: m.state != 'cancel')
        if movimentos:
            return movimentos
        return self.move_line_ids.move_id.filtered(lambda m: m and m.state != 'cancel')

    def _pg_label_qty(self, move):
        """Quantas etiquetas para este movimento.

        A quantidade feita ganha à prevista: quem etiqueta faz isso com a
        mercadoria em cima da bancada, não com a que foi encomendada.
        """
        self.ensure_one()
        return int(move.quantity or move.product_uom_qty or 0)

    def _pg_label_move_ids_por_tipo(self):
        """`{tipo: [id de movimento repetido por cada etiqueta]}`.

        O id repete-se tantas vezes quantas as unidades: é assim que o relatório
        imprime uma etiqueta por peça sem precisar de saber quantidades.
        """
        self.ensure_one()
        por_tipo = {}
        for move in self._pg_label_moves():
            tipo = move.product_id.pg_label_type
            if not tipo:
                continue
            quantidade = self._pg_label_qty(move)
            if quantidade > 0:
                por_tipo.setdefault(tipo, []).extend([move.id] * quantidade)
        return por_tipo

    # -- acções ------------------------------------------------------------

    def action_pg_print_pdf_labels(self):
        """Imprime as etiquetas A5 e 5x8 da recepção, num único PDF.

        Os dois formatos vêm de relatórios diferentes; junta-se o resultado para
        quem está a etiquetar não ter de imprimir duas vezes. O ZPL fica de fora
        de propósito — vai para impressora térmica, não para papel.
        """
        self.ensure_one()
        por_tipo = self._pg_label_move_ids_por_tipo()

        Report = self.env['ir.actions.report']
        documentos = []
        for tipo, xmlid in RELATORIOS_PDF.items():
            ids_movimentos = por_tipo.get(tipo)
            if not ids_movimentos:
                continue
            pdf, _formato = Report._render_qweb_pdf(xmlid, ids_movimentos)
            documentos.append(pdf)

        if not documentos:
            raise UserError(_(
                "Nenhum artigo desta recepção usa etiqueta A5 ou 5x8.\n"
                "Confirmar o campo \"Tipo de etiqueta\" nos artigos; as etiquetas "
                "ZPL imprimem-se no botão \"Imprimir ZPL\"."
            ))

        conteudo = merge_pdf(documentos) if len(documentos) > 1 else documentos[0]
        anexo = self.env['ir.attachment'].create({
            'name': _("Etiquetas %s.pdf", self.name),
            'type': 'binary',
            'datas': base64.b64encode(conteudo),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        _logger.info(
            "pg_etiquetas: %s etiquetas PDF geradas para a recepção %s.",
            sum(len(v) for k, v in por_tipo.items() if k in RELATORIOS_PDF), self.name,
        )
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{anexo.id}?download=true',
            'target': 'self',
        }

    def action_pg_print_zpl_labels(self):
        """Envia as etiquetas ZPL para a impressora térmica.

        Não há wizard de escolha de caixa IoT: em v19 o encaminhamento é o do
        standard — o relatório está ligado a um `iot.device` de tipo impressora
        (campo "IoT Devices" no relatório) e, quando há mais do que um, o próprio
        Odoo pergunta qual, com opção de não voltar a perguntar. A V17 tinha aqui
        um wizard que passava `iot_device_id` no contexto com um id de `iot.box`:
        chave que o módulo `iot` não lê e modelo errado, pelo que a escolha do
        utilizador não tinha efeito nenhum — ver alínea (g) do manifest.
        """
        self.ensure_one()
        ids_movimentos = self._pg_label_move_ids_por_tipo().get('ZPL')
        if not ids_movimentos:
            raise UserError(_(
                "Nenhum artigo desta recepção usa etiqueta ZPL."
            ))
        _logger.info(
            "pg_etiquetas: %s etiquetas ZPL para a recepção %s.",
            len(ids_movimentos), self.name,
        )
        relatorio = self.env.ref('pg_etiquetas.action_report_pg_etiqueta_zpl')
        return relatorio.report_action(ids_movimentos)
