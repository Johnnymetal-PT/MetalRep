import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

PARAM_MAX_DIMENSAO = 'pg_sale_by_square_meter.max_dimensao_m'
# 20 m é generoso de propósito: na base de produção, das 60 linhas com
# dimensões plausíveis a maior tem 5,4 m. As quatro que passam deste valor
# (267, 220, 220 e 80) são todas centímetros escritos como metros.
DEFAULT_MAX_DIMENSAO = 20.0


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Nomes herdados da V17 (sem prefixo pg_) de propósito: as colunas já
    # existem na base migrada, com dados em 64 linhas. Renomeá-las obrigaria a
    # uma migração de dados sem ganho nenhum.
    comprimento = fields.Float(string="Comprimento (m)")
    largura = fields.Float(string="Largura (m)")
    area = fields.Float(
        string="Área (m²)",
        compute='_compute_area',
        store=True,
        readonly=True,
        # Calculada logo na criação, para a linha nascer com a área correcta
        # em vez de a ganhar num segundo tempo.
        precompute=True,
    )

    @api.depends('comprimento', 'largura')
    def _compute_area(self):
        for line in self:
            line.area = (line.comprimento or 0.0) * (line.largura or 0.0)

    @api.model
    def _pg_max_dimensao(self):
        valor = self.env['ir.config_parameter'].sudo().get_param(PARAM_MAX_DIMENSAO)
        try:
            return float(valor) if valor not in (None, False, '') else DEFAULT_MAX_DIMENSAO
        except ValueError:
            _logger.warning(
                "pg_sale_by_square_meter: parâmetro '%s' com valor inválido (%r); "
                "a usar %s.", PARAM_MAX_DIMENSAO, valor, DEFAULT_MAX_DIMENSAO,
            )
            return DEFAULT_MAX_DIMENSAO

    @api.constrains('comprimento', 'largura')
    def _check_dimensoes(self):
        """Recusa dimensões fora de escala.

        Existe porque nada impedia o disparate: na base de produção há uma
        linha de 267 m por 260 m — 69 420 m² — e mais três com 220 ou 80 m de
        comprimento. São centímetros escritos como metros, e só se dão pela
        falta na fatura.
        """
        maximo = self._pg_max_dimensao()
        if maximo <= 0:
            return
        for linha in self:
            for campo, etiqueta in (('comprimento', "comprimento"), ('largura', "largura")):
                valor = linha[campo] or 0.0
                if valor > maximo:
                    raise ValidationError(_(
                        "O %(campo)s indicado (%(valor).2f m) passa o máximo admitido"
                        " de %(maximo).2f m.\n\n"
                        "Confirme se o valor não está em centímetros: %(valor).0f cm"
                        " escrevem-se %(convertido).2f.\n"
                        "O máximo altera-se em Vendas > Definições.",
                        campo=etiqueta, valor=valor, maximo=maximo,
                        convertido=valor / 100.0,
                    ))

    @api.model_create_multi
    def create(self, vals_list):
        """Semeia a quantidade quando a linha nasce já com dimensões.

        Só na criação é preciso este passo: `product_uom_qty` tem valor por
        omissão 1, que o ORM aplica **antes** de correr o cálculo, pelo que o
        compute não chega a intervir. A partir daqui a quantidade é derivada —
        qualquer alteração das dimensões volta a passar pelo cálculo.
        """
        for vals in vals_list:
            if 'product_uom_qty' in vals:
                continue
            area = (vals.get('comprimento') or 0.0) * (vals.get('largura') or 0.0)
            if area > 0:
                vals['product_uom_qty'] = area
        return super().create(vals_list)

    @api.depends('display_type', 'product_id', 'area')
    def _compute_product_uom_qty(self):
        """Faz a quantidade **derivar** da área, em vez de lhe ser escrita.

        Esta é a correcção de fundo face à V17. Lá, a área era copiada para a
        quantidade por um sincronismo imperativo que só corria no `create` e num
        `write` que tocasse nas dimensões; qualquer outro caminho — importação,
        alteração em massa, API — deixava a quantidade desactualizada, e a
        fatura, que copia fielmente a quantidade da encomenda, saía errada.

        Em v19 a quantidade é um campo calculado e gravado, editável
        (`sale/models/sale_order_line.py`). Acrescentar a área às suas
        dependências põe o recálculo a cargo do ORM: passa a acontecer por
        qualquer caminho, e deixa de haver estado a dessincronizar.

        Uma quantidade escrita à mão continua a valer — o campo é editável —,
        até que as dimensões mudem.
        """
        super()._compute_product_uom_qty()
        for line in self:
            if not line.display_type and line.area > 0:
                line.product_uom_qty = line.area

    @api.model
    def _pg_report_area_mismatch(self):
        """Lista as linhas cuja quantidade não corresponde à área.

        Não corrige nada: numa base migrada estas linhas podem ter faturas
        emitidas, e reescrever a quantidade mudaria documentos já lançados. O
        objectivo é dar a lista a quem decide, caso a caso.

        :return: recordset das linhas divergentes
        """
        candidatas = self.search([('area', '>', 0)])
        divergentes = candidatas.filtered(
            lambda l: abs(l.product_uom_qty - l.area) > 0.005
        )
        for linha in divergentes:
            _logger.warning(
                "pg_sale_by_square_meter: %s linha %s — área %.4f, quantidade %.4f, faturado %.4f",
                linha.order_id.name, linha.id, linha.area,
                linha.product_uom_qty, linha.qty_invoiced,
            )

        maximo = self._pg_max_dimensao()
        fora_de_escala = self.search([
            '|', ('comprimento', '>', maximo), ('largura', '>', maximo),
        ]) if maximo > 0 else self.browse()
        for linha in fora_de_escala:
            _logger.warning(
                "pg_sale_by_square_meter: %s linha %s — dimensões fora de escala "
                "(%.2f x %.2f m); provável introdução em centímetros.",
                linha.order_id.name, linha.id, linha.comprimento, linha.largura,
            )

        _logger.info(
            "pg_sale_by_square_meter: %s linha(s) com área, %s divergente(s), "
            "%s com dimensões fora de escala.",
            len(candidatas), len(divergentes), len(fora_de_escala),
        )
        return divergentes
