"""Pipeline MRP especifico Piccolo: BoM duplicada com componentes
"Tecido X" / "Acabamento Y" gerados a partir da descricao da SO.

Fluxo de ``create``:
1. Le ``product_description_variants`` (ou copia do
   ``sale.order.line.name``).
2. Extrai termos no formato ``"TERMO: valor"`` (ver _TERMS).
3. Duplica a BoM principal (a mais antiga do template).
4. Aplica consumos do ``pg_price_table`` (``price_1..price_10``).
5. Substitui componentes genericos por copias com o nome exato.
6. Cria a MO em ``state=draft`` e atribui a BoM duplicada.

Termos suportados (HARDCODED, com acentos literais):
- TECIDO / TECIDO CIMA / TECIDO BAIXO / TECIDO COSTAS FRENTE + ASSENTO
- TECIDO COSTAS TRAS  (case-insensitive)
- ACABAMENTO / ACABAMENTO com Ponteira
- ARO
- ALTERACAO COR DOS PES
- DIMENSOES DO COLCHAO (lido de product_template_attribute_value_ids)
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_description_variants = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="['|', ('company_id', '=', company_id), ('company_id', 'parent_of', company_id)]",
    )

    @api.model
    def create(self, vals):
        # Fallback: se nao veio descricao no MO, copia do nome da
        # primeira sale.order.line do produto. NOTA: usa apenas o
        # `product_id` para procurar; se houver multiplas SO lines do
        # mesmo produto, apanha a primeira (pode nao ser a desejada).
        description = str(vals.get('product_description_variants') or '').strip()
        if not description:
            sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
            if sale_order_line:
                description = sale_order_line.name
                vals['product_description_variants'] = description

        # Lista de termos suportados na descricao. Os acentos sao
        # **literais** - ver "Pontos de atencao" no manifest.
        terms = {
            'ACABAMENTO': '',
            'ACABAMENTO com Ponteira': '',
            'TECIDO COSTAS FRENTE + ASSENTO': '',
            'TECIDO COSTAS TRÁS': '',
            'TECIDO CIMA': '',
            'TECIDO BAIXO': '',
            'TECIDO': '',
            'ARO': '',
            'ALTERAÇÃO COR DOS PÉS': '',
        }

        # Para cada termo, captura o texto entre `TERMO:` e o proximo
        # ` TERMO:` (qualquer outro). Procura a posicao de cada termo
        # em case-insensitive.
        for term in terms:
            start_index = description.lower().find(f"{term.lower()}:")
            if start_index != -1:
                end_index = len(description)
                for next_term in terms:
                    if next_term != term:
                        next_start = description.lower().find(f"{next_term.lower()}:", start_index + len(term) + 1)
                        if next_start != -1:
                            end_index = min(end_index, next_start)
                terms[term] = description[start_index + len(term) + 1:end_index].strip()

        # DIMENSOES DO COLCHAO vem das product_template_attribute_value_ids,
        # NAO da descricao - so e injetado se a SO line existir.
        sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
        if sale_order_line:
            dimensoes_value = sale_order_line.product_template_attribute_value_ids.filtered(
                lambda ptav: ptav.attribute_id.name == 'DIMENSÕES DO COLCHÃO'
            ).name
            if dimensoes_value:
                terms['DIMENSÕES DO COLCHÃO'] = dimensoes_value

        # Merge dos termos existentes (re-create se a MO ja tinha
        # descricao) com os novos, mantendo a ordem do dict Python 3.7+.
        existing_description = vals.get('product_description_variants', '').strip()

        existing_terms = {}
        if existing_description:
            for item in existing_description.split(', '):
                if ': ' in item:
                    key, value = item.split(': ', 1)
                    existing_terms[key] = value

        for term, value in terms.items():
            if value:
                existing_terms[term] = value

        vals['product_description_variants'] = ', '.join(f"{key}: {value}" for key, value in existing_terms.items())

        product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

        # Passo 1: BoM antiga (referencia) + mapeamento termo -> texto.
        oldest_bom, term_to_text = self._search_oldest_bom(vals.get('product_id'), terms)

        # Passo 2: duplicar para nao alterar a BoM partilhada.
        duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

        if duplicated_bom:
            # Passo 3: aplicar consumos do pg_price_table.
            self._apply_consumption_values(duplicated_bom, term_to_text, product_qty)

            # Passo 4: substituir componentes genericos por especificos.
            for term, extracted_text in term_to_text.items():
                if extracted_text:
                    self._duplicate_and_assign_to_bom(duplicated_bom, term, extracted_text)

        # Passo 5: MO criada em draft (utilizador confirma manualmente).
        vals['state'] = 'draft'
        production = super(MrpProduction, self).create(vals)
        if duplicated_bom:
            production.write({'bom_id': duplicated_bom.id})

        return production

    def _search_oldest_bom(self, product_id, terms):
        """Procura a BoM mais antiga e classifica cada linha por termo.

        Os if/elif estao ordenados do mais especifico para o mais
        generico (TECIDO COSTAS TRAS antes de TECIDO) para que a
        substring match nao apanhe o termo errado.
        """
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', product.product_tmpl_id.id)],
            order='create_date asc', limit=1,
        )

        term_to_text = {}
        if bom:
            for line in bom.bom_line_ids:
                product_name = line.product_id.name.lower()
                # ORDEM critica: do mais especifico para o mais generico.
                if 'tecido costas trás' in product_name:
                    term = 'TECIDO COSTAS TRÁS'
                elif 'tecido costas frente + assento' in product_name:
                    term = 'TECIDO COSTAS FRENTE + ASSENTO'
                elif 'tecido cima' in product_name:
                    term = 'TECIDO CIMA'
                elif 'tecido baixo' in product_name:
                    term = 'TECIDO BAIXO'
                elif 'tecido' in product_name:
                    term = 'TECIDO'
                elif 'aro' in product_name:
                    term = 'ARO'
                elif 'alteração cor dos pés' in product_name:
                    term = 'ALTERAÇÃO COR DOS PÉS'
                elif 'acabamento com ponteira' in product_name:
                    term = 'ACABAMENTO com Ponteira'
                elif 'acabamento' in product_name and 'com ponteira' not in product_name:
                    term = 'ACABAMENTO'
                else:
                    continue

                # ACABAMENTO com Ponteira partilha a entrada da
                # descricao com ACABAMENTO normal (sem variante).
                extracted_text = terms.get(term.replace(' com Ponteira', ''))
                term_to_text[term] = extracted_text

        return bom, term_to_text

    def _duplicate_bom(self, bom, product_qty):
        """Duplica a BoM e escala componentes nao-termo por product_qty.

        Componentes de termo (tecido*) ficam intocados aqui porque
        ``_apply_consumption_values`` recalcula-os depois com base na
        tabela de consumo do componente.
        """
        if bom:
            duplicated_bom = bom.copy()

            if duplicated_bom.product_qty != product_qty:
                duplicated_bom.product_qty = product_qty

            for line in duplicated_bom.bom_line_ids:
                product_name = line.product_id.name.lower()

                # Componentes que vao ser recalculados depois.
                is_term_component = any(term.lower() in product_name for term in [
                    'tecido costas trás',
                    'tecido costas frente + assento',
                    'tecido cima',
                    'tecido baixo',
                    'tecido',
                ])

                if not is_term_component:
                    line.product_qty = line.product_qty * product_qty

            return duplicated_bom
        return None

    def _apply_consumption_values(self, bom, term_to_text, product_qty):
        """Aplica consumos do pg_price_table aos componentes de tecido.

        ``price_N`` do **componente** (template do tecido) e a
        quantidade necessaria por unidade. Total = ``price_N * product_qty``.
        """
        if not bom:
            return

        for line in bom.bom_line_ids:
            product_name = line.product_id.name.lower()

            # Mesma ordem do _search_oldest_bom; 'tecido completo' e
            # tratado como equivalente a 'tecido costas frente + assento'.
            if 'tecido costas trás' in product_name:
                term = 'TECIDO COSTAS TRÁS'
            elif 'tecido costas frente + assento' in product_name or 'tecido completo' in product_name:
                term = 'TECIDO COSTAS FRENTE + ASSENTO'
            elif 'tecido cima' in product_name:
                term = 'TECIDO CIMA'
            elif 'tecido baixo' in product_name:
                term = 'TECIDO BAIXO'
            elif 'tecido' in product_name:
                term = 'TECIDO'
            else:
                continue

            if term in term_to_text:
                component_template = line.product_id.product_tmpl_id

                consumption_value_per_unit = self._get_consumption_value(component_template, product_qty)
                total_consumption_value = consumption_value_per_unit * product_qty

                if line.product_qty != total_consumption_value:
                    line.product_qty = total_consumption_value

    def _duplicate_and_assign_to_bom(self, bom, term, extracted_text):
        """Substitui componente generico por um especifico desta MO.

        Cria (ou reaproveita por ``name`` exato) um
        ``product.template`` com o nome calculado, copia ``price_*``
        do generico, atribui o fornecedor por defeito, e troca o
        ``product_id`` da bom_line.
        """
        if bom:
            main_product_name = bom.product_tmpl_id.name
            product_in_bom = bom.bom_line_ids.filtered(
                lambda line: term.lower() in line.product_id.name.lower() or
                            ('tecido completo' in line.product_id.name.lower() and term.lower() in ['tecido costas frente + assento', 'tecido cima'])
            )

            if product_in_bom:
                for line in product_in_bom:
                    product = line.product_id.product_tmpl_id

                    # Nome do duplicado depende do termo. **Importante**:
                    # usar o ``term`` classificado upstream e nao
                    # re-classificar pelo nome do produto, para evitar
                    # colisoes (ex.: 'aro' dentro de 'CAROLINA' apanhava
                    # o branch do acabamento/aro).
                    term_low = term.lower()
                    duplicate_name = extracted_text
                    if term_low == 'acabamento com ponteira':
                        duplicate_name = f"{main_product_name} {extracted_text} com Ponteira"
                    elif term_low in ('acabamento', 'aro', 'alteração cor dos pés'):
                        duplicate_name = f"{main_product_name} {extracted_text}"
                    elif term_low in ('tecido', 'tecido costas frente + assento', 'tecido costas trás', 'tecido cima', 'tecido baixo'):
                        duplicate_name = f"Tecido {extracted_text}"

                    # Reaproveita templates ja criados; desativa
                    # duplicados antigos (gerados antes do reuse logic).
                    existing_product = self.env['product.template'].search(
                        [('name', '=', duplicate_name)], order="create_date desc",
                    )
                    if existing_product:
                        if len(existing_product) > 1:
                            existing_product[1:].write({'active': False})
                        duplicate_product = existing_product[0]
                    else:
                        duplicate_product = product.copy()
                        duplicate_product.name = duplicate_name
                        self._copy_custom_fields(product, duplicate_product)

                        self._assign_vendor_to_product(duplicate_product, term)

                    # Substituir o componente na BoM duplicada.
                    line.write({'product_id': duplicate_product.product_variant_id.id})

    def _assign_vendor_to_product(self, duplicate_product, term):
        """Atribui o fornecedor por defeito ao novo template.

        Nomes de fornecedor HARDCODED por convencao Piccolo:
        - tecidos -> "-Fornecedor de tecidos a definir"
        - acabamento/aro/cor dos pes -> "Polidor C/Arte Mobiliario, Lda"
        """
        vendor_name = None
        if term in ['TECIDO COSTAS FRENTE + ASSENTO', 'TECIDO COSTAS TRÁS', 'TECIDO CIMA', 'TECIDO BAIXO', 'TECIDO']:
            vendor_name = '-Fornecedor de tecidos a definir'
        elif 'ACABAMENTO' in term or term == 'ARO' or term == 'ALTERAÇÃO COR DOS PÉS':
            vendor_name = 'Polidor C/Arte Mobiliario, Lda'

        if vendor_name:
            vendor = self.env['res.partner'].search([('name', '=', vendor_name)], limit=1)
            if vendor:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': duplicate_product.id,
                    'partner_id': vendor.id,
                    'min_qty': 0.00,
                    'price': 0.00,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'delay': 7,
                    'date_start': fields.Date.today(),
                })

    def _get_consumption_value(self, product_template, product_qty):
        """Le ``price_N`` do template para a quantidade pedida.

        Tabela tem 10 linhas (price_1..price_10). qty <= 1 -> price_1;
        qty >= 10 -> price_10. Fracionario truncado por ``int(qty)``.
        """
        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10,
        ]

        if product_qty < 1:
            return consumption_table[0]

        index = min(int(product_qty) - 1, len(consumption_table) - 1)
        return consumption_table[index]

    def _copy_custom_fields(self, original_product, duplicate_product):
        """Copia a tabela de consumo (price_1..10) para o duplicado."""
        try:
            custom_fields = [
                'price_1', 'price_2', 'price_3', 'price_4', 'price_5',
                'price_6', 'price_7', 'price_8', 'price_9', 'price_10',
            ]

            for field in custom_fields:
                setattr(duplicate_product, field, getattr(original_product, field, 0.0))
        except Exception as e:
            _logger.error(
                "[COPY] Failed to copy custom fields from product %s to %s: %s",
                original_product.id, duplicate_product.id, str(e),
            )
