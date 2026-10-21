from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Campos totais da entrega
    total_packing_volumes = fields.Integer(
        string='Total Volumes',
        compute='_compute_packing_totals',
        store=True,
        help='Total de volumes de todos os produtos na entrega',
    )

    total_packing_gross_weight = fields.Float(
        string='Total Peso Bruto (Kg)',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Peso bruto total de todos os produtos na entrega',
    )

    total_packing_net_weight = fields.Float(
        string='Total Peso Líquido (Kg)',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Peso líquido total de todos os produtos na entrega',
    )

    total_packing_cubicagem = fields.Float(
        string='Total Cubicagem',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Cubicagem total de todos os produtos na entrega',
    )

    total_comprimento = fields.Float(
        string='Comprimento Total',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Soma dos comprimentos de todas as linhas',
    )

    total_largura = fields.Float(
        string='Largura Total',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Soma das larguras de todas as linhas',
    )

    total_altura = fields.Float(
        string='Altura Total',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Soma das alturas de todas as linhas',
    )

    # Auxiliares de exibição: ocultar peso líquido quando vazio e padronizar dimensões
    show_total_net_weight = fields.Boolean(
        string='Mostrar Peso Líquido',
        compute='_compute_display_helpers',
        help='Verdadeiro quando existe peso líquido total (> 0) para exibir',
    )

    # Dimensões totais no formato W x D x H (Largura x Comprimento x Altura)
    total_dimensions_wdh = fields.Char(
        string='Dimensões Totais (W x D x H)',
        compute='_compute_display_helpers',
        help='Dimensões totais formatadas como W x D x H',
    )

    @api.depends(
        'move_ids_without_package.move_packing_volumes',
        'move_ids_without_package.move_packing_gross_weight',
        'move_ids_without_package.move_packing_net_weight',
        'move_ids_without_package.move_packing_cubicagem',
        'move_ids_without_package.total_comprimento',
        'move_ids_without_package.total_largura',
        'move_ids_without_package.total_altura'
    )
    def _compute_packing_totals(self):
        """Calcula os totais de packing baseados nos produtos da entrega"""
        for picking in self:
            total_volumes = int(sum(picking.move_ids_without_package.mapped('move_packing_volumes')))
            total_gross = sum(picking.move_ids_without_package.mapped('move_packing_gross_weight'))
            total_net = sum(picking.move_ids_without_package.mapped('move_packing_net_weight'))
            total_cubicagem = sum(picking.move_ids_without_package.mapped('move_packing_cubicagem'))
            total_comprimento = sum(picking.move_ids_without_package.mapped('total_comprimento'))
            total_largura = sum(picking.move_ids_without_package.mapped('total_largura'))
            total_altura = sum(picking.move_ids_without_package.mapped('total_altura'))

            picking.total_packing_volumes = total_volumes
            picking.total_packing_gross_weight = total_gross
            picking.total_packing_net_weight = total_net
            picking.total_packing_cubicagem = total_cubicagem
            picking.total_comprimento = total_comprimento
            picking.total_largura = total_largura
            picking.total_altura = total_altura

    def _format_float(self, value):
        """Formata floats com duas casas decimais; vazio quando zero."""
        try:
            v = float(value or 0.0)
        except Exception:
            v = 0.0
        return f"{v:.2f}" if v else ""

    @api.depends('total_packing_net_weight', 'total_largura', 'total_comprimento', 'total_altura')
    def _compute_display_helpers(self):
        for picking in self:
            picking.show_total_net_weight = bool(picking.total_packing_net_weight and picking.total_packing_net_weight > 0)
            # Ordem W x D x H = Largura x Comprimento x Altura
            w = picking._format_float(picking.total_largura)
            d = picking._format_float(picking.total_comprimento)
            h = picking._format_float(picking.total_altura)
            picking.total_dimensions_wdh = f"{w} x {d} x {h}" if any([w, d, h]) else ""

    def action_open_cubicagem_wizard(self):
        """Abre o wizard de cubicagem geral"""
        return {
            'name': 'Cubicagem Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            }
        }


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Campos de packing list por linha de movimento
    move_packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Volumes para esta linha baseado no produto e quantidade',
    )

    move_packing_gross_weight = fields.Float(
        string='Peso Bruto (Kg)',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Peso bruto para esta linha baseado no produto e quantidade',
    )

    move_packing_net_weight = fields.Float(
        string='Peso Líquido (Kg)',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Peso líquido para esta linha baseado no produto e quantidade',
    )

    move_packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Cubicagem para esta linha baseado no produto e quantidade',
    )

    move_gross_weight_1 = fields.Float(string='Peso Bruto 1', digits=(4, 2), default=0.0)
    move_gross_weight_2 = fields.Float(string='Peso Bruto 2', digits=(4, 2), default=0.0)
    move_gross_weight_3 = fields.Float(string='Peso Bruto 3', digits=(4, 2), default=0.0)
    move_gross_weight_4 = fields.Float(string='Peso Bruto 4', digits=(4, 2), default=0.0)
    move_gross_weight_5 = fields.Float(string='Peso Bruto 5', digits=(4, 2), default=0.0)
    move_gross_weight_6 = fields.Float(string='Peso Bruto 6', digits=(4, 2), default=0.0)

    move_net_weight_1 = fields.Float(string='Peso Líquido 1', digits=(4, 2), default=0.0)
    move_net_weight_2 = fields.Float(string='Peso Líquido 2', digits=(4, 2), default=0.0)
    move_net_weight_3 = fields.Float(string='Peso Líquido 3', digits=(4, 2), default=0.0)
    move_net_weight_4 = fields.Float(string='Peso Líquido 4', digits=(4, 2), default=0.0)
    move_net_weight_5 = fields.Float(string='Peso Líquido 5', digits=(4, 2), default=0.0)
    move_net_weight_6 = fields.Float(string='Peso Líquido 6', digits=(4, 2), default=0.0)

    # Dimensões informadas manualmente
    move_comprimento_1 = fields.Float(string='Comprimento 1', digits=(4, 2), default=0.0)
    move_altura_1 = fields.Float(string='Altura 1', digits=(4, 2), default=0.0)
    move_largura_1 = fields.Float(string='Largura 1', digits=(4, 2), default=0.0)

    move_comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), default=0.0)
    move_altura_2 = fields.Float(string='Altura 2', digits=(4, 2), default=0.0)
    move_largura_2 = fields.Float(string='Largura 2', digits=(4, 2), default=0.0)

    move_comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), default=0.0)
    move_altura_3 = fields.Float(string='Altura 3', digits=(4, 2), default=0.0)
    move_largura_3 = fields.Float(string='Largura 3', digits=(4, 2), default=0.0)

    move_comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), default=0.0)
    move_altura_4 = fields.Float(string='Altura 4', digits=(4, 2), default=0.0)
    move_largura_4 = fields.Float(string='Largura 4', digits=(4, 2), default=0.0)

    move_comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), default=0.0)
    move_altura_5 = fields.Float(string='Altura 5', digits=(4, 2), default=0.0)
    move_largura_5 = fields.Float(string='Largura 5', digits=(4, 2), default=0.0)

    move_comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), default=0.0)
    move_altura_6 = fields.Float(string='Altura 6', digits=(4, 2), default=0.0)
    move_largura_6 = fields.Float(string='Largura 6', digits=(4, 2), default=0.0)

    # Número de volumes por tipo (para reconstruir por-volume no relatório)
    move_number_1 = fields.Integer(string='Nº Volumes Tipo 1', default=0)
    move_number_2 = fields.Integer(string='Nº Volumes Tipo 2', default=0)
    move_number_3 = fields.Integer(string='Nº Volumes Tipo 3', default=0)
    move_number_4 = fields.Integer(string='Nº Volumes Tipo 4', default=0)
    move_number_5 = fields.Integer(string='Nº Volumes Tipo 5', default=0)
    move_number_6 = fields.Integer(string='Nº Volumes Tipo 6', default=0)

    @api.depends('product_id.packing_volumes',
                 'product_id.packing_gross_weight', 'product_id.packing_gross_weight_2',
                 'product_id.packing_gross_weight_3', 'product_id.packing_gross_weight_4',
                 'product_id.packing_gross_weight_5', 'product_id.packing_gross_weight_6',
                 'product_id.packing_net_weight', 'product_id.packing_net_weight_2',
                 'product_id.packing_net_weight_3', 'product_id.packing_net_weight_4',
                 'product_id.packing_net_weight_5', 'product_id.packing_net_weight_6',
                 'product_id.packing_cubicagem',
                 'product_uom_qty')
    def _compute_move_packing(self):
        """Calcula os valores de packing para cada linha de movimento"""
        for move in self:
            if move.product_id:
                qty = move.product_uom_qty or 0.0
                # Tolerante a valores não preenchidos no produto (None/False)
                move.move_packing_volumes = (move.product_id.packing_volumes or 0.0) * qty
                used_volumes = int(min(6, move.move_packing_volumes or 0))
                gross_weights = [
                    (move.product_id.packing_gross_weight or 0.0),
                    (move.product_id.packing_gross_weight_2 or 0.0),
                    (move.product_id.packing_gross_weight_3 or 0.0),
                    (move.product_id.packing_gross_weight_4 or 0.0),
                    (move.product_id.packing_gross_weight_5 or 0.0),
                    (move.product_id.packing_gross_weight_6 or 0.0),
                ]
                net_weights = [
                    (move.product_id.packing_net_weight or 0.0),
                    (move.product_id.packing_net_weight_2 or 0.0),
                    (move.product_id.packing_net_weight_3 or 0.0),
                    (move.product_id.packing_net_weight_4 or 0.0),
                    (move.product_id.packing_net_weight_5 or 0.0),
                    (move.product_id.packing_net_weight_6 or 0.0),
                ]
                for i in range(1, 7):
                    gw = (gross_weights[i - 1] * qty) if i <= used_volumes else 0.0
                    nw = (net_weights[i - 1] * qty) if i <= used_volumes else 0.0
                    setattr(move, f'move_gross_weight_{i}', gw)
                    setattr(move, f'move_net_weight_{i}', nw)
                    if i > used_volumes:
                        setattr(move, f'move_comprimento_{i}', 0.0)
                        setattr(move, f'move_largura_{i}', 0.0)
                        setattr(move, f'move_altura_{i}', 0.0)
                move.move_packing_gross_weight = sum(
                    getattr(move, f'move_gross_weight_{i}') for i in range(1, used_volumes + 1)
                )
                move.move_packing_net_weight = sum(
                    getattr(move, f'move_net_weight_{i}') for i in range(1, used_volumes + 1)
                )
                move.move_packing_cubicagem = (move.product_id.packing_cubicagem or 0.0) * qty
            else:
                move.move_packing_volumes = 0.0
                move.move_packing_gross_weight = 0.0
                move.move_packing_net_weight = 0.0
                move.move_packing_cubicagem = 0.0
                for i in range(1, 7):
                    setattr(move, f'move_gross_weight_{i}', 0.0)
                    setattr(move, f'move_net_weight_{i}', 0.0)
                    setattr(move, f'move_comprimento_{i}', 0.0)
                    setattr(move, f'move_largura_{i}', 0.0)
                    setattr(move, f'move_altura_{i}', 0.0)

    # Exibição auxiliar em W x D x H (Largura x Comprimento x Altura)
    dimensions_wdh_display = fields.Char(
        string='Dimensões (W x D x H)',
        compute='_compute_dimensions_wdh_display',
        help='Dimensões informadas nesta linha formatadas como W x D x H',
    )

    def _format_dim(self, v):
        try:
            val = float(v or 0.0)
        except Exception:
            val = 0.0
        return f"{val:.2f}" if val else ""

    @api.depends(
        'move_comprimento_1', 'move_largura_1', 'move_altura_1',
        'move_comprimento_2', 'move_largura_2', 'move_altura_2',
        'move_comprimento_3', 'move_largura_3', 'move_altura_3',
        'move_comprimento_4', 'move_largura_4', 'move_altura_4',
        'move_comprimento_5', 'move_largura_5', 'move_altura_5',
        'move_comprimento_6', 'move_largura_6', 'move_altura_6',
        'move_packing_volumes')
    def _compute_dimensions_wdh_display(self):
        for move in self:
            used_volumes = int(min(6, move.move_packing_volumes or 0))
            parts = []
            for i in range(1, used_volumes + 1):
                w = move._format_dim(getattr(move, f'move_largura_{i}', 0.0))
                d = move._format_dim(getattr(move, f'move_comprimento_{i}', 0.0))
                h = move._format_dim(getattr(move, f'move_altura_{i}', 0.0))
                if any([w, d, h]):
                    parts.append(f"{w} x {d} x {h}")
            move.dimensions_wdh_display = ", ".join(parts) if parts else ""

    def action_open_move_calc_wizard(self):
        """Abre o wizard de cubicagem para esta linha de stock.move"""
        self.ensure_one()
        return {
            'name': 'Cálculo de Cubicagem da Linha',
            'type': 'ir.actions.act_window',
            'res_model': 'cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            }
        }

    total_comprimento = fields.Float(string="Comprimento Total", compute="_compute_totalidade_dimensoes", store=True)
    total_largura = fields.Float(string="Largura Total", compute="_compute_totalidade_dimensoes", store=True)
    total_altura = fields.Float(string="Altura Total", compute="_compute_totalidade_dimensoes", store=True)

    @api.depends(
        'move_comprimento_1', 'move_largura_1', 'move_altura_1',
        'move_comprimento_2', 'move_largura_2', 'move_altura_2',
        'move_comprimento_3', 'move_largura_3', 'move_altura_3',
        'move_comprimento_4', 'move_largura_4', 'move_altura_4',
        'move_comprimento_5', 'move_largura_5', 'move_altura_5',
        'move_comprimento_6', 'move_largura_6', 'move_altura_6',
        'product_id.packing_comprimento', 'product_id.packing_largura', 'product_id.packing_altura',
        'product_id.packing_comprimento_2', 'product_id.packing_largura_2', 'product_id.packing_altura_2',
        'product_id.packing_comprimento_3', 'product_id.packing_largura_3', 'product_id.packing_altura_3',
        'product_id.packing_comprimento_4', 'product_id.packing_largura_4', 'product_id.packing_altura_4',
        'product_id.packing_comprimento_5', 'product_id.packing_largura_5', 'product_id.packing_altura_5',
        'product_id.packing_comprimento_6', 'product_id.packing_largura_6', 'product_id.packing_altura_6',
        'product_uom_qty'
    )
    def _compute_totalidade_dimensoes(self):
        for move in self:
            # Determina o número de volumes usados (máximo 6)
            used_volumes = int(min(6, move.move_packing_volumes or 0))

            # Soma apenas os blocos realmente utilizados
            total_comprimento = sum(
                getattr(move, f'move_comprimento_{i}', 0.0)
                for i in range(1, used_volumes + 1)
            )
            total_largura = sum(
                getattr(move, f'move_largura_{i}', 0.0)
                for i in range(1, used_volumes + 1)
            )
            total_altura = sum(
                getattr(move, f'move_altura_{i}', 0.0)
                for i in range(1, used_volumes + 1)
            )

            move.total_comprimento = total_comprimento
            move.total_largura = total_largura
            move.total_altura = total_altura
