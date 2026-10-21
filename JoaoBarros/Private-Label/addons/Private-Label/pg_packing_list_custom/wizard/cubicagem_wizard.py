from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CubicagemWizard(models.TransientModel):
    _name = 'cubicagem.wizard'
    _description = 'Assistente de Cálculo de Cubicagem'

    picking_id = fields.Many2one('stock.picking', string='Entrega')
    move_id = fields.Many2one('stock.move', string='Linha do Produto')

    volumes = fields.Integer(string='Volumes', default=0)

    @api.onchange('volumes')
    def _onchange_volumes(self):
        used = int(min(6, self.volumes or 0))
        for i in range(used + 1, 7):
            setattr(self, f'comprimento_{i}', 0.0)
            setattr(self, f'altura_{i}', 0.0)
            setattr(self, f'largura_{i}', 0.0)
            setattr(self, f'gross_weight_{i}', 0.0)
            setattr(self, f'net_weight_{i}', 0.0)
            setattr(self, f'number_{i}', 0)
    
    # Títulos de Volume (para exibição como texto nas views)
    dummy_volume_1 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 1</p>")
    dummy_volume_2 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 2</p>")
    dummy_volume_3 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 3</p>")
    dummy_volume_4 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 4</p>")
    dummy_volume_5 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 5</p>")
    dummy_volume_6 = fields.Html(default="<p style='font-size: 16px; white-space: nowrap; font-weight: bold; color: #7388c9;'>Volume 6</p>")

    # Número de volumes por tipo (para agrupar volumes idênticos)
    number_1 = fields.Integer(string='Número 1', default=1, store=True)
    number_2 = fields.Integer(string='Número 2', default=0, store=True)
    number_3 = fields.Integer(string='Número 3', default=0, store=True)
    number_4 = fields.Integer(string='Número 4', default=0, store=True)
    number_5 = fields.Integer(string='Número 5', default=0, store=True)
    number_6 = fields.Integer(string='Número 6', default=0, store=True)



    comprimento_1 = fields.Float(string='Comprimento 1', digits=(4, 2), default=0.0, store=True)
    altura_1 = fields.Float(string='Altura 1', digits=(4, 2), default=0.0, store=True)
    largura_1 = fields.Float(string='Largura 1', digits=(4, 2), default=0.0, store=True)

    comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), default=0.0, store=True)
    altura_2 = fields.Float(string='Altura 2', digits=(4, 2), default=0.0, store=True)
    largura_2 = fields.Float(string='Largura 2', digits=(4, 2), default=0.0, store=True)

    comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), default=0.0, store=True)
    altura_3 = fields.Float(string='Altura 3', digits=(4, 2), default=0.0, store=True)
    largura_3 = fields.Float(string='Largura 3', digits=(4, 2), default=0.0, store=True)

    comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), default=0.0, store=True)
    altura_4 = fields.Float(string='Altura 4', digits=(4, 2), default=0.0, store=True)
    largura_4 = fields.Float(string='Largura 4', digits=(4, 2), default=0.0, store=True)

    comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), default=0.0, store=True)
    altura_5 = fields.Float(string='Altura 5', digits=(4, 2), default=0.0, store=True)
    largura_5 = fields.Float(string='Largura 5', digits=(4, 2), default=0.0, store=True)

    comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), default=0.0, store=True)
    altura_6 = fields.Float(string='Altura 6', digits=(4, 2), default=0.0, store=True)
    largura_6 = fields.Float(string='Largura 6', digits=(4, 2), default=0.0, store=True)

    cubicagem_total = fields.Float(
        string='Cubicagem Total',
        digits=(4, 2),
        compute='_compute_cubicagem_total',
        store=True
    )

    total_comprimento = fields.Float(string="Comprimento Total", compute="_compute_totalidade_comprimentos", store=True)
    total_largura = fields.Float(string="Largura Total", compute="_compute_totalidade_largura", store=True)
    total_altura = fields.Float(string="Altura Total", compute="_compute_totalidade_altura", store=True)

    gross_weight_1 = fields.Float(string='Peso Bruto 1', digits=(4, 2), default=0.0, store=True)
    gross_weight_2 = fields.Float(string='Peso Bruto 2', digits=(4, 2), default=0.0, store=True)
    gross_weight_3 = fields.Float(string='Peso Bruto 3', digits=(4, 2), default=0.0, store=True)
    gross_weight_4 = fields.Float(string='Peso Bruto 4', digits=(4, 2), default=0.0, store=True)
    gross_weight_5 = fields.Float(string='Peso Bruto 5', digits=(4, 2), default=0.0, store=True)
    gross_weight_6 = fields.Float(string='Peso Bruto 6', digits=(4, 2), default=0.0, store=True)

    net_weight_1 = fields.Float(string='Peso Líquido 1', digits=(4, 2), default=0.0, store=True)
    net_weight_2 = fields.Float(string='Peso Líquido 2', digits=(4, 2), default=0.0, store=True)
    net_weight_3 = fields.Float(string='Peso Líquido 3', digits=(4, 2), default=0.0, store=True)
    net_weight_4 = fields.Float(string='Peso Líquido 4', digits=(4, 2), default=0.0, store=True)
    net_weight_5 = fields.Float(string='Peso Líquido 5', digits=(4, 2), default=0.0, store=True)
    net_weight_6 = fields.Float(string='Peso Líquido 6', digits=(4, 2), default=0.0, store=True)

    gross_weight_total = fields.Float(
        string='Peso Bruto Total (Kg)',
        digits=(4, 2),
        compute='_compute_weight_totals',
        store=True,
        readonly=True
    )

    net_weight_total = fields.Float(
        string='Peso Líquido Total (Kg)',
        digits=(4, 2),
        compute='_compute_weight_totals',
        store=True,
        readonly=True
    )

    # Campos para peso manual
    peso_manual = fields.Boolean(
        string='Peso Manual',
        default=True,
        help='Ativar para introduzir peso manualmente em vez de usar cálculo automático'
    )

    @api.depends('volumes', 'comprimento_1', 'altura_1', 'largura_1',
                 'comprimento_2', 'altura_2', 'largura_2',
                 'comprimento_3', 'altura_3', 'largura_3',
                 'comprimento_4', 'altura_4', 'largura_4',
                 'comprimento_5', 'altura_5', 'largura_5',
                 'comprimento_6', 'altura_6', 'largura_6',
                 'number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6')
    def _compute_cubicagem_total(self):
        for wizard in self:
            total = 0.0
            dims = [
                (wizard.comprimento_1, wizard.altura_1, wizard.largura_1),
                (wizard.comprimento_2, wizard.altura_2, wizard.largura_2),
                (wizard.comprimento_3, wizard.altura_3, wizard.largura_3),
                (wizard.comprimento_4, wizard.altura_4, wizard.largura_4),
                (wizard.comprimento_5, wizard.altura_5, wizard.largura_5),
                (wizard.comprimento_6, wizard.altura_6, wizard.largura_6),
            ]
            nums = [wizard.number_1, wizard.number_2, wizard.number_3, wizard.number_4, wizard.number_5, wizard.number_6]
            for i in range(int(min(6, wizard.volumes))):
                c, a, l = dims[i]
                n = int(nums[i] or 0)
                total += (c * a * l) * n
            wizard.cubicagem_total = total

    @api.depends(
        'volumes',
        'comprimento_1', 'comprimento_2', 'comprimento_3',
        'comprimento_4', 'comprimento_5', 'comprimento_6',
        'number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6'
    )
    def _compute_totalidade_comprimentos(self):
        for wizard in self:
            used = int(min(6, wizard.volumes or 0))
            nums = [wizard.number_1, wizard.number_2, wizard.number_3, wizard.number_4, wizard.number_5, wizard.number_6]
            wizard.total_comprimento = sum(
                getattr(wizard, f'comprimento_{i}', 0.0) * int(nums[i-1] or 0)
                for i in range(1, used + 1)
            )

    @api.depends(
        'volumes',
        'largura_1', 'largura_2', 'largura_3',
        'largura_4', 'largura_5', 'largura_6',
        'number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6'
    )
    def _compute_totalidade_largura(self):
        for wizard in self:
            used = int(min(6, wizard.volumes or 0))
            nums = [wizard.number_1, wizard.number_2, wizard.number_3, wizard.number_4, wizard.number_5, wizard.number_6]
            wizard.total_largura = sum(
                getattr(wizard, f'largura_{i}', 0.0) * int(nums[i-1] or 0)
                for i in range(1, used + 1)
            )

    @api.depends(
        'volumes',
        'altura_1', 'altura_2', 'altura_3',
        'altura_4', 'altura_5', 'altura_6',
        'number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6'
    )
    def _compute_totalidade_altura(self):
        for wizard in self:
            used = int(min(6, wizard.volumes or 0))
            nums = [wizard.number_1, wizard.number_2, wizard.number_3, wizard.number_4, wizard.number_5, wizard.number_6]
            wizard.total_altura = sum(
                getattr(wizard, f'altura_{i}', 0.0) * int(nums[i-1] or 0)
                for i in range(1, used + 1)
            )

    @api.depends('gross_weight_1', 'gross_weight_2', 'gross_weight_3', 'gross_weight_4', 'gross_weight_5', 'gross_weight_6',
                 'net_weight_1', 'net_weight_2', 'net_weight_3', 'net_weight_4', 'net_weight_5', 'net_weight_6',
                 'number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6',
                 'cubicagem_total', 'peso_manual', 'volumes')
    def _compute_weight_totals(self):
        for wizard in self:
            used = int(min(6, wizard.volumes or 0))
            nums = [wizard.number_1, wizard.number_2, wizard.number_3, wizard.number_4, wizard.number_5, wizard.number_6]
            if wizard.peso_manual:
                wizard.gross_weight_total = sum(
                    getattr(wizard, f'gross_weight_{i}') * int(nums[i-1] or 0)
                    for i in range(1, used + 1)
                )
                wizard.net_weight_total = sum(
                    getattr(wizard, f'net_weight_{i}') * int(nums[i-1] or 0)
                    for i in range(1, used + 1)
                )
            else:
                total = wizard.cubicagem_total * 80
                wizard.gross_weight_total = total
                wizard.net_weight_total = total

    def action_calcular(self):
        self.ensure_one()
        if not self.move_id:
            raise ValidationError("Linha do produto não encontrada.")

        # Validações adicionais e determinação do peso
        if self.peso_manual:
            gross_weights = [
                self.gross_weight_1,
                self.gross_weight_2,
                self.gross_weight_3,
                self.gross_weight_4,
                self.gross_weight_5,
                self.gross_weight_6,
            ]
            net_weights = [
                self.net_weight_1,
                self.net_weight_2,
                self.net_weight_3,
                self.net_weight_4,
                self.net_weight_5,
                self.net_weight_6,
            ]
            numbers = [
                int(self.number_1 or 0),
                int(self.number_2 or 0),
                int(self.number_3 or 0),
                int(self.number_4 or 0),
                int(self.number_5 or 0),
                int(self.number_6 or 0),
            ]
            used = int(min(6, self.volumes or 0))
            if sum(numbers[:used]) != self.volumes:
                raise ValidationError("A soma dos 'Número' por tipo deve ser igual ao total em 'Volumes'.")
            if any((gross_weights[i] <= 0) for i in range(used) if numbers[i] > 0):
                raise ValidationError("O peso bruto de cada tipo com 'Número' > 0 deve ser maior que zero.")
            for i in range(used, 6):
                gross_weights[i] = 0.0
                net_weights[i] = 0.0
                numbers[i] = 0
        else:
            total = self.cubicagem_total * 80
            used = int(min(6, self.volumes or 0))
            # Distribui igualmente pelos tipos visíveis caso não seja manual
            peso_por_volume = total / (self.volumes or 1) if used else 0.0
            # Se não definidos, assume 1 por tipo até atingir 'volumes'
            base_numbers = [self.number_1 or 0, self.number_2 or 0, self.number_3 or 0, self.number_4 or 0, self.number_5 or 0, self.number_6 or 0]
            if sum(base_numbers[:used]) != self.volumes:
                # preenche automaticamente: 1 por tipo, último ajusta para bater com volumes
                numbers = [0]*6
                remaining = int(self.volumes or 0)
                for i in range(used):
                    assign = 1 if remaining > 0 else 0
                    numbers[i] = assign
                    remaining -= assign
                if remaining > 0 and used:
                    numbers[used-1] += remaining
            else:
                numbers = [int(n or 0) for n in base_numbers]
            gross_weights = [peso_por_volume for _ in range(6)]
            net_weights = [peso_por_volume for _ in range(6)]
            self.gross_weight_total = total
            self.net_weight_total = total

        # Totais considerando quantidades por tipo (usar os números calculados na branch acima)
        numbers_used = numbers
        gross_final = sum((gross_weights[i] or 0.0) * numbers_used[i] for i in range(6))
        net_final = sum((net_weights[i] or 0.0) * numbers_used[i] for i in range(6))
        vals = {
            'move_packing_volumes': self.volumes,
            'move_packing_cubicagem': self.cubicagem_total,
            'move_packing_gross_weight': gross_final,
            'move_packing_net_weight': net_final,
        }
        for i in range(1, 7):
            n = numbers_used[i - 1] if i <= used else 0
            vals[f'move_gross_weight_{i}'] = (gross_weights[i - 1] or 0.0) * n if i <= used else 0.0
            vals[f'move_net_weight_{i}'] = (net_weights[i - 1] or 0.0) * n if i <= used else 0.0
            vals[f'move_comprimento_{i}'] = (getattr(self, f'comprimento_{i}') or 0.0) * n if i <= used else 0.0
            vals[f'move_altura_{i}'] = (getattr(self, f'altura_{i}') or 0.0) * n if i <= used else 0.0
            vals[f'move_largura_{i}'] = (getattr(self, f'largura_{i}') or 0.0) * n if i <= used else 0.0
            # gravar também o número por tipo
            vals[f'move_number_{i}'] = n
        self.move_id.write(vals)

        return {'type': 'ir.actions.act_window_close'}  # <== FECHA imediatamente o wizard

    def action_cancelar(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_id = self.env.context.get('default_move_id')
        if move_id:
            move = self.env['stock.move'].browse(move_id)

            # Ler números gravados; inferir 1 quando existir conteúdo no slot e o número for 0
            numbers = []
            for i in range(1, 7):
                n = int(getattr(move, f'move_number_{i}', 0) or 0)
                if not n:
                    comp_tot = float(getattr(move, f'move_comprimento_{i}', 0.0) or 0.0)
                    larg_tot = float(getattr(move, f'move_largura_{i}', 0.0) or 0.0)
                    alt_tot  = float(getattr(move, f'move_altura_{i}', 0.0) or 0.0)
                    gw_tot   = float(getattr(move, f'move_gross_weight_{i}', 0.0) or 0.0)
                    nw_tot   = float(getattr(move, f'move_net_weight_{i}', 0.0) or 0.0)
                    n = 1 if any([comp_tot, larg_tot, alt_tot, gw_tot, nw_tot]) else 0
                numbers.append(n)

            per_vals = {
                'comprimento': [], 'largura': [], 'altura': [],
                'gross': [], 'net': []
            }
            for i in range(1, 7):
                n = numbers[i-1] or 0
                div = float(n) if n else 0.0
                comp_tot = float(getattr(move, f'move_comprimento_{i}', 0.0) or 0.0)
                larg_tot = float(getattr(move, f'move_largura_{i}', 0.0) or 0.0)
                alt_tot  = float(getattr(move, f'move_altura_{i}', 0.0) or 0.0)
                gw_tot   = float(getattr(move, f'move_gross_weight_{i}', 0.0) or 0.0)
                nw_tot   = float(getattr(move, f'move_net_weight_{i}', 0.0) or 0.0)
                per_vals['comprimento'].append(comp_tot / div if div else 0.0)
                per_vals['largura'].append(larg_tot / div if div else 0.0)
                per_vals['altura'].append(alt_tot / div if div else 0.0)
                per_vals['gross'].append(gw_tot / div if div else 0.0)
                per_vals['net'].append(nw_tot / div if div else 0.0)

            volumes = sum(numbers) or int(move.move_packing_volumes or 0)
            tot_cbm = sum((per_vals['comprimento'][i] * per_vals['largura'][i] * per_vals['altura'][i]) * numbers[i] for i in range(6))
            tot_gross = sum(per_vals['gross'][i] * numbers[i] for i in range(6))
            tot_net = sum(per_vals['net'][i] * numbers[i] for i in range(6))

            res.update({
                'move_id': move.id,
                'volumes': int(volumes or 0),
                'gross_weight_total': tot_gross,
                'net_weight_total': tot_net,
                'cubicagem_total': tot_cbm,
                'peso_manual': True,
                'number_1': numbers[0], 'number_2': numbers[1], 'number_3': numbers[2],
                'number_4': numbers[3], 'number_5': numbers[4], 'number_6': numbers[5],
                'comprimento_1': per_vals['comprimento'][0], 'largura_1': per_vals['largura'][0], 'altura_1': per_vals['altura'][0],
                'comprimento_2': per_vals['comprimento'][1], 'largura_2': per_vals['largura'][1], 'altura_2': per_vals['altura'][1],
                'comprimento_3': per_vals['comprimento'][2], 'largura_3': per_vals['largura'][2], 'altura_3': per_vals['altura'][2],
                'comprimento_4': per_vals['comprimento'][3], 'largura_4': per_vals['largura'][3], 'altura_4': per_vals['altura'][3],
                'comprimento_5': per_vals['comprimento'][4], 'largura_5': per_vals['largura'][4], 'altura_5': per_vals['altura'][4],
                'comprimento_6': per_vals['comprimento'][5], 'largura_6': per_vals['largura'][5], 'altura_6': per_vals['altura'][5],
                'gross_weight_1': per_vals['gross'][0], 'net_weight_1': per_vals['net'][0],
                'gross_weight_2': per_vals['gross'][1], 'net_weight_2': per_vals['net'][1],
                'gross_weight_3': per_vals['gross'][2], 'net_weight_3': per_vals['net'][2],
                'gross_weight_4': per_vals['gross'][3], 'net_weight_4': per_vals['net'][3],
                'gross_weight_5': per_vals['gross'][4], 'net_weight_5': per_vals['net'][4],
                'gross_weight_6': per_vals['gross'][5], 'net_weight_6': per_vals['net'][5],
            })
        return res
