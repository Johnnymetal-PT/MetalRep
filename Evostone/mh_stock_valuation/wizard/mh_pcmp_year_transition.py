# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MhPcmpYearTransition(models.TransientModel):
    _name = 'mh.pcmp.year.transition'
    _description = 'Transição de Ano Fiscal PCMP'

    from_year = fields.Integer(
        string='De Ano',
        required=True,
        default=lambda self: fields.Date.today().year - 1,
    )
    to_year = fields.Integer(
        string='Para Ano',
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
    )

    # Opções
    include_zero_stock = fields.Boolean(
        string='Incluir Produtos com Stock Zero',
        default=False,
        help="Se ativado, cria pontos de partida mesmo para produtos com stock zero",
    )
    overwrite_existing = fields.Boolean(
        string='Sobrescrever Existentes',
        default=False,
        help="Se ativado, sobrescreve registos PCMP já existentes no ano de destino",
    )

    # Resultado
    products_count = fields.Integer(
        string='Produtos a Processar',
        compute='_compute_products_count',
    )

    @api.depends('from_year', 'company_id', 'include_zero_stock')
    def _compute_products_count(self):
        """Calcula quantos produtos serão processados."""
        for wizard in self:
            products = wizard._get_products_to_transition()
            wizard.products_count = len(products)

    @api.constrains('from_year', 'to_year')
    def _check_years(self):
        for wizard in self:
            if wizard.from_year >= wizard.to_year:
                raise ValidationError(
                    _("O ano de origem deve ser menor que o ano de destino.")
                )
            if wizard.to_year - wizard.from_year != 1:
                raise ValidationError(
                    _("A transição deve ser entre anos consecutivos.")
                )

    def _get_products_to_transition(self):
        """
        Obtém os produtos que devem ser transicionados.

        Retorna produtos com:
        - Método de custo PCMP
        - Tipo armazenável (storable)
        - Com registo PCMP no ano de origem OU com stock > 0
        """
        Product = self.env['product.product']
        PcmpYear = self.env['mh.pcmp.fiscal.year'].sudo()

        # Produtos com método PCMP
        pcmp_products = Product.search([
            ('categ_id.property_cost_method', '=', 'pcmp'),
            ('type', '=', 'product'),  # storable
        ])

        if not pcmp_products:
            return Product

        # Filtrar por produtos com registo PCMP no ano de origem
        products_with_pcmp = PcmpYear.search([
            ('fiscal_year', '=', self.from_year),
            ('company_id', '=', self.company_id.id),
            ('product_id', 'in', pcmp_products.ids),
        ]).mapped('product_id')

        if self.include_zero_stock:
            return products_with_pcmp
        else:
            # Filtrar apenas produtos com stock ou valor > 0
            return products_with_pcmp.filtered(
                lambda p: p.with_company(self.company_id).qty_available > 0 or
                p.with_company(self.company_id).pcmp > 0
            )

    def action_preview(self):
        """Mostra preview dos produtos a serem transicionados."""
        self.ensure_one()
        products = self._get_products_to_transition()

        if not products:
            raise UserError(
                _("Nenhum produto encontrado para transição.\n"
                  "Verifique se existem produtos com método PCMP e "
                  "registos no ano %s.") % self.from_year
            )

        return {
            'name': _('Produtos para Transição PCMP'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', products.ids)],
            'context': {'search_default_group_by_categ_id': 1},
        }

    def action_execute_transition(self):
        """
        Executa a transição de ano fiscal.

        Para cada produto com PCMP no ano de origem:
        1. Calcula o PCMP final do ano de origem
        2. Calcula o stock final do ano de origem
        3. Cria ponto de partida no ano de destino com esses valores
        """
        self.ensure_one()

        products = self._get_products_to_transition()

        if not products:
            raise UserError(
                _("Nenhum produto encontrado para transição.")
            )

        PcmpYear = self.env['mh.pcmp.fiscal.year'].sudo()

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for product in products:
            try:
                result = self._transition_product(product, PcmpYear)
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                errors.append(f"{product.display_name}: {str(e)}")

        # Preparar mensagem de resultado
        message_parts = []
        if created_count:
            message_parts.append(_("%d registos criados") % created_count)
        if updated_count:
            message_parts.append(_("%d registos atualizados") % updated_count)
        if skipped_count:
            message_parts.append(_("%d produtos ignorados") % skipped_count)
        if errors:
            message_parts.append(_("%d erros") % len(errors))

        message = _("Transição PCMP %s → %s concluída.\n%s") % (
            self.from_year,
            self.to_year,
            "\n".join(message_parts)
        )

        if errors:
            message += _("\n\nErros:\n") + "\n".join(errors[:10])
            if len(errors) > 10:
                message += _("\n... e mais %d erros") % (len(errors) - 10)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Transição PCMP'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }

    def _transition_product(self, product, PcmpYear):
        """
        Executa a transição para um produto específico.

        :param product: product.product record
        :param PcmpYear: mh.pcmp.fiscal.year model
        :return: 'created', 'updated', ou 'skipped'
        """
        # Verificar se já existe registo no ano de destino
        existing = PcmpYear.search([
            ('product_id', '=', product.id),
            ('fiscal_year', '=', self.to_year),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

        if existing and not self.overwrite_existing:
            return 'skipped'

        # Obter valores do ano de origem
        from_record = product._get_pcmp_fiscal_year_record(
            self.from_year, self.company_id
        )

        if not from_record:
            return 'skipped'

        # Calcular PCMP e stock final do ano de origem
        final_pcmp = product.with_company(self.company_id)._compute_pcmp(
            self.from_year, self.company_id
        )
        final_stock = self._get_final_stock(product, self.from_year)

        # Valores para o novo ano
        vals = {
            'product_id': product.id,
            'fiscal_year': self.to_year,
            'company_id': self.company_id.id,
            'initial_stock': final_stock,
            'initial_pcmp': final_pcmp,
            'is_new_product': False,
        }

        if existing:
            existing.write(vals)
            return 'updated'
        else:
            PcmpYear.create(vals)
            return 'created'

    def _get_final_stock(self, product, fiscal_year):
        """
        Calcula o stock final de um produto no final do ano fiscal.

        :param product: product.product record
        :param fiscal_year: Ano fiscal
        :return: float quantidade final
        """
        # Obter ponto de partida
        initial = product._get_pcmp_initial_values(fiscal_year, self.company_id)

        # Datas do ano fiscal
        date_from = f'{fiscal_year}-01-01'
        date_to = f'{fiscal_year}-12-31'

        # Movimentos de entrada
        in_moves = product._get_pcmp_moves('in', date_from, date_to, self.company_id)
        in_qty = sum(in_moves.mapped('quantity'))

        # Movimentos de saída
        out_moves = product._get_pcmp_moves('out', date_from, date_to, self.company_id)
        out_qty = sum(out_moves.mapped('quantity'))

        # Stock final = inicial + entradas - saídas
        return initial['stock'] + in_qty - out_qty
