from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    units_qty = fields.Integer(
        string='Quantidade',
        default=1,
        help='Número de peças/unidades a serem movimentadas'
    )
    # Dimensões
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento em metros'
    )
    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura em metros'
    )
    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura em metros'
    )

    peso = fields.Float(
        string='Peso (kg)',
        compute='_compute_peso',
        store=True,
        digits=(10, 2),
        help='Peso total calculado:\n'
             '- Para produtos dimensionais (block/slab/strip/tiles): '
             'L × W × T × units_qty × densidade\n'
             '- Para produtos sem forma (none): product.weight × product_qty\n'
             'Densidade vem de product.density ou do parâmetro '
             'campo Empresa → Densidade Padrão de Pedra (default 2700 kg/m³).',
    )

    @api.depends('state', 'thickness', 'product_qty', 'product_id',
                 'product_id.density', 'product_id.weight', 'product_id.product_form',
                 'company_id.stone_density')
    def _compute_peso(self):
        """Peso por product_form usando product_qty (mesma fórmula do stock.move):
        - block: product_qty × density (qty é m³)
        - slab/strip/tiles: product_qty × thickness × density (qty é m²)
        - none: product_qty × product.weight

        Quando state in ('purchase','done') E peso já tem valor, preserva.
        """
        for line in self:
            if line.state in ('purchase', 'done') and line.peso:
                continue
            default_density = (line.company_id.stone_density
                               if line.company_id else 0) or 2700
            product_form = getattr(line.product_id, 'product_form', 'none')
            qty = line.product_qty or 0.0
            if product_form == 'block':
                density = (line.product_id.density if line.product_id else 0) or default_density
                line.peso = qty * density
            elif product_form in ('slab', 'strip', 'tiles'):
                density = (line.product_id.density if line.product_id else 0) or default_density
                line.peso = qty * (line.thickness or 0.0) * density
            else:
                line.peso = qty * (line.product_id.weight or 0)

    thickness_readonly = fields.Boolean(
        string='Thickness Readonly',
        compute='_compute_thickness_readonly',
        store=False,
        help='Controla se o campo thickness deve ser readonly'
    )

    dimensions_readonly = fields.Boolean(
        string='Dimensions Readonly',
        compute='_compute_dimensions_readonly',
        store=False,
        help='Controla se os campos de dimensões (length, width) e lote devem ser readonly quando product_form = none'
    )

    # Área/Volume calculado
    area = fields.Float(
        string='Área/Volume',
        compute='_compute_area',
        store=True,
        digits='Product Unit of Measure',
        help='Área (m²) ou Volume (m³) unitário calculado baseado nas dimensões'
    )
    
    lot_required = fields.Boolean(
        string="Lot Required",
        compute="_compute_lot_required",
        store=False,
    )
    
    
    @api.depends('product_id', 'product_id.tracking')
    def _compute_lot_required(self):
        """Computar se o lote é obrigatório baseado no tracking do produto"""
        for line in self:
            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            line.lot_required = line.product_id and line.product_id.tracking in ['lot', 'serial'] and product_form in ['block', 'slab', 'strip', 'tiles']

    @api.depends('product_id', 'product_id.product_form')
    def _compute_thickness_readonly(self):
        """Computar se o campo thickness deve ser readonly

        Readonly quando product_form for diferente de 'block'
        Editável apenas quando product_form = 'block'
        """
        for line in self:
            if not line.product_id:
                line.thickness_readonly = False
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            # Readonly para todos exceto 'block'
            line.thickness_readonly = (product_form != 'block')

    @api.depends('product_id', 'product_id.product_form')
    def _compute_dimensions_readonly(self):
        """Computar se os campos de dimensões e lote devem ser readonly

        Readonly quando product_form = 'none'
        Editável para todos os outros valores (block, slab, strip, tiles)
        """
        for line in self:
            if not line.product_id:
                line.dimensions_readonly = False
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            # Readonly apenas quando product_form = 'none'
            line.dimensions_readonly = (product_form == 'none')

    @api.onchange('product_id')
    def _onchange_product_id_thickness(self):
        """Preencher thickness automaticamente quando produto é selecionado

        Preenche thickness do produto quando product_form for 'slab', 'strip' ou 'tiles'
        (não preenche para 'none' nem 'block')
        """
        if not self.product_id:
            return

        product_form = self.product_id.product_form if hasattr(self.product_id, 'product_form') else 'none'

        # Preencher thickness apenas se product_form não for 'none' e não for 'block'
        if product_form in ['slab', 'strip', 'tiles']:
            # Pegar thickness do produto se disponível
            if hasattr(self.product_id, 'thickness') and self.product_id.thickness:
                self.thickness = self.product_id.thickness

    @api.depends('length', 'width', 'thickness', 'product_id.product_form', 'units_qty')
    def _compute_area(self):
        """Calcula área ou volume unitário baseado no tipo de produto

        Para produtos do tipo block, slab, strip, tiles:
        - O valor calculado representa a área/volume de UMA unidade
        - Este valor será usado para definir automaticamente product_qty
        """
        for line in self:
            if not line.product_id:
                line.area = 0.0
                continue

            product_form = line.product_id.product_form

            if product_form == 'block':
                # Volume unitário (m³) = comprimento × largura × espessura
                if line.length and line.width and line.thickness:
                    calculated = line.length * line.width * line.thickness * line.units_qty
                    line.area = float_round(calculated, precision_rounding=line.product_uom.rounding)
                else:
                    line.area = 0.0
            elif product_form in ['slab', 'strip', 'tiles']:
                # Área unitária (m²) = comprimento × largura
                if line.length and line.width:
                    calculated = line.length * line.width * line.units_qty
                    line.area = float_round(calculated, precision_rounding=line.product_uom.rounding)
                else:
                    line.area = 0.0
            else:
                line.area = float_round(line.units_qty, precision_rounding=line.product_uom.rounding)

    @api.depends('area', 'product_id.product_form', 'units_qty',
                 'product_packaging_qty', 'product_packaging_id')
    def _compute_product_qty(self):
        """Sobrescreve método nativo para sincronizar product_qty com dimensões

        Fluxo:
        1. Executa lógica nativa do Odoo primeiro (packaging, etc)
        2. Se produto tem dimensões, sobrescreve com cálculo de área/volume
        3. Caso contrário, mantém valor calculado pelo Odoo
        """

        # DEPOIS: Aplicar lógica customizada apenas onde aplicável
        for line in self:
            if not line.product_id:
                continue  # Mantém valor do super()

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            # Sobrescrever apenas para produtos com forma específica
            if product_form in ['block', 'slab', 'strip', 'tiles']:
                line.product_qty = float_round(line.area, precision_rounding=line.product_uom.rounding)
            elif product_form == 'none':
                line.product_qty = float_round(line.units_qty, precision_rounding=line.product_uom.rounding)
            # Para outros casos: mantém o valor já calculado pelo super()
        
        # DEPOIS: Executar lógica nativa do Odoo
        super(PurchaseOrderLine, self)._compute_product_qty()

    @api.constrains('length', 'width', 'thickness', 'product_id')
    def _check_dimensions(self):
        """Valida que dimensões obrigatórias estão preenchidas.

        Nota: Só valida quando estado != 'draft' para evitar erros durante edição.
        """
        for line in self:
            # Ignorar validação em rascunho - será validado ao confirmar
            if line.order_id.state == 'draft':
                continue

            if not line.product_id:
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            # Só valida se for um tipo que precisa de dimensões
            if product_form == 'none':
                continue

            if product_form == 'block':
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    raise ValidationError(
                        f"[COMPRA] Produto '{line.product_id.name}' do tipo 'Bloco' requer "
                        "Comprimento, Largura e Espessura preenchidos."
                    )


            elif product_form in ['slab', 'strip', 'tiles']:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product_form, product_form)

                if not (line.length > 0 and line.width > 0):
                    raise ValidationError(
                        f"[COMPRA] Produto '{line.product_id.name}' do tipo '{form_name}' requer "
                        "Comprimento e Largura preenchidos."
                    )

    def _validate_dimensions(self):
        """Validação de dimensões (chamada ao confirmar pedido)"""
        for line in self:
            if not line.product_id:
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            # Só valida se for um tipo que precisa de dimensões
            if product_form == 'none':
                continue

            if product_form == 'block':
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    raise ValidationError(
                        f"[COMPRA] Produto '{line.product_id.name}' do tipo 'Bloco' requer "
                        "Comprimento, Largura e Espessura preenchidos."
                    )


            elif product_form in ['slab', 'strip', 'tiles']:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product_form, product_form)

                if not (line.length > 0 and line.width > 0):
                    raise ValidationError(
                        f"[COMPRA] Produto '{line.product_id.name}' do tipo '{form_name}' requer "
                        "Comprimento e Largura preenchidos."
                    )
                    
    def _prepare_stock_moves(self, picking):
        """Passa dimensões e lot_name para stock moves.

        Nota: stock.move.peso é compute (calcula a partir de quantity × thickness
        × density), por isso não passamos peso aqui.
        """
        res = super()._prepare_stock_moves(picking)

        for move_vals in res:
            move_vals.update({
                'units_qty': self.units_qty,
                'length': self.length,
                'width': self.width,
                'thickness': self.thickness,
                'lot_name': self.lot_name,
            })

        return res

    def _prepare_account_move_line(self, move=False):
        """Override para passar dimensões para a linha da fatura de compra"""
        res = super()._prepare_account_move_line(move=move)
        res.update({
            'units_qty': self.units_qty,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'lot_name': self.lot_name,
            'peso': self.peso,
        })
        return res

    @api.constrains('product_id', 'lot_name')
    def _check_lot_required(self):
        """Validar que lote é obrigatório se produto tem tracking"""
        for record in self:
            product_form = record.product_id.product_form if record.product_id and hasattr(record.product_id, 'product_form') else 'none'
            if record.product_id.tracking in ['lot', 'serial'] and product_form in ['block', 'slab', 'strip', 'tiles'] and not record.lot_name :
                tracking_display = 'Lote' if record.product_id.tracking == 'lot' else 'Número de Série'
                raise ValidationError(
                    f"❌ Lote obrigatório!\n\n"
                    f"Produto: {record.product_id.name}\n"
                    f"Tracking: {tracking_display}\n\n"
                    f"Este produto exige rastreamento por lote/série.\n"
                    f"Por favor, informe o lote antes de continuar."
                )