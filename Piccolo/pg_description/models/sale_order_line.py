"""Limpeza e formatacao das descricoes das linhas SO/carrinho.

Pipeline em ``_process_name_field``:
1. Extrai conteudo entre parenteses e filtra contra
   ``excluded_terms`` (Categorias, Mesmo Tecido, etc.).
2. Remove o bracketed do nome principal.
3. Normaliza TECIDO COSTAS FRENTE/CIMA para TECIDO quando o par
   correspondente nao esta presente.
4. Concatena termos validos + bracketed validos.

Triggers:
- create / write em ``sale.order.line``: processa o ``name``.
- onchange ``name``: processa a descricao a quente.
- write em ``sale.order`` com state in (sent, sale): re-processa
  TODAS as linhas (caso tenha entrado sem passar pelos hooks).
- action_confirm em ``sale.order``: sincroniza ``move.name``.

BUG: a lista ``terms`` no compute esta em falta uma virgula entre
``'TIPO DE PÉ:'`` e ``'DIMENSÕES DO COLCHÃO:'`` (linha ~58 do
ficheiro original). Resultado: as duas strings concatenam-se.
Mantido literal ate confirmacao do cliente.
"""
import re
from odoo import models, fields, api
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cart_processed_description = fields.Html(
        string="Cart Processed Description",
        compute="_compute_cart_processed_description",
        store=True,
    )

    @api.model
    def create(self, vals):
        """Processa o ``name`` ao criar a linha (configurador, import)."""
        if 'name' in vals and vals['name']:
            vals['name'] = self._process_name_field(vals['name'])
        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        """Idem para alteracoes."""
        if 'name' in vals and vals['name']:
            vals['name'] = self._process_name_field(vals['name'])
        return super(SaleOrderLine, self).write(vals)

    @api.depends('name', 'product_template_id')
    def _compute_cart_processed_description(self):
        """Versao HTML com line breaks para a vista do carrinho."""
        for line in self:
            if line.name and line.name != "Standard":
                processed_description = self._process_name_field(line.name)

                # Injecta <br/> antes de cada termo chave para que o
                # template QWeb renderize uma linha por atributo.
                # NOTA: 'TIPO DE PÉ:' sem virgula a seguir esta a
                # concatenar com 'DIMENSÕES DO COLCHÃO:' - bug
                # conhecido (ver docstring no topo).
                terms = [
                    "ACABAMENTO:",
                    "TECIDO COSTAS FRENTE + ASSENTO:",
                    "TECIDO COSTAS TRÁS:",
                    "TECIDO:",
                    "TECIDO CIMA:",
                    "TECIDO BAIXO:",
                    "ARO:",
                    'ALTERAÇÃO COR DOS PÉS:',
                    'TIPO DE PÉ:'  # BUG: falta a virgula - concatena com o seguinte
                    'DIMENSÕES DO COLCHÃO:',
                    'FURAÇÃO PARA TOMADA COM CAIXA CERTIFICADA:',
                ]
                for term in terms:
                    processed_description = processed_description.replace(term, f"<br/>{term}")

                # Tirar o nome do produto da descricao para nao repetir
                # no carrinho (o nome ja aparece em separado).
                if line.product_template_id.name:
                    processed_description = processed_description.replace(line.product_template_id.name, "").strip()

                # Markup para o Odoo nao escapar os <br/>.
                line.cart_processed_description = Markup(processed_description)
            else:
                line.cart_processed_description = ""

    @api.onchange('name')
    def _onchange_name_process(self):
        """Processa em onchange para preview imediato."""
        for line in self:
            if line.name:
                line.name = self._process_name_field(line.name)

    def _process_name_field(self, name):
        """Limpeza principal: bracketed extraction + filtro + normalize."""
        try:
            # Termos a excluir do output final - lista curada com a Piccolo.
            excluded_terms = {
                'Categoria A', 'Categoria B', 'Categoria C', 'Categoria D', 'Categoria E',
                'Cliente', 'Cat. A', 'Cat. B', 'Cat. C', 'Cat. D', 'Cat. E', 'Matte',
                'Brilho | Lacado ou Verniz', 'Mesmo Tecido', 'Sem', 'Sem Ponteiras',
            }

            if not name:
                return ""

            # 1) Extrair tudo o que esta entre parens (lista de strings).
            bracketed_info = re.findall(r'\((.*?)\)', name)

            # 2) Cada bracketed e split por virgula e cada elemento e
            #    filtrado contra excluded_terms.
            valid_bracketed_terms = []
            for bracketed in bracketed_info:
                terms = [term.strip() for term in bracketed.split(",")]
                filtered_terms = [term for term in terms if term not in excluded_terms]
                valid_bracketed_terms.extend(filtered_terms)

            # 3) Remover bracketed do nome principal.
            name = re.sub(r'\(.*?\)', '', name).strip()

            # 4a) TECIDO COSTAS FRENTE + ASSENTO sem TECIDO COSTAS TRAS
            #     -> renomear para TECIDO (so um tecido em uso).
            if 'TECIDO COSTAS FRENTE + ASSENTO' in name and 'TECIDO COSTAS TRÁS' not in name:
                name = name.replace('TECIDO COSTAS FRENTE + ASSENTO', 'TECIDO')

            # 4b) TECIDO CIMA sem TECIDO BAIXO -> renomear para TECIDO.
            if 'TECIDO CIMA' in name and 'TECIDO BAIXO' not in name:
                name = name.replace('TECIDO CIMA', 'TECIDO')

            # 5) Processar restante texto: por linhas, filtrando vazias
            #    e termos excluidos.
            processed_name_lines = name.split("\n")
            valid_terms = [line.strip() for line in processed_name_lines if line.strip() and line.strip() not in excluded_terms]

            # 6) Concatena texto principal + bracketed validos no fim.
            final_processed_name = "\n".join(valid_terms + valid_bracketed_terms).strip()

            return final_processed_name
        except Exception as e:
            _logger.error("Error processing name field: %s", e, exc_info=True)
            # Fallback ao nome original para nao perder a descricao
            # em caso de regressao.
            return name


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Estado extra para automation rules externas dispararem.
    # Renomear/remover sem cuidado parte essas automations.
    state = fields.Selection(
        selection_add=[('automation_trigger', 'Automation Trigger')],
        ondelete={'automation_trigger': 'set null'},
    )

    def write(self, vals):
        """Re-processa todas as linhas quando o estado vira sent/sale.

        Util quando ha caminhos que setam o ``name`` sem passar pelos
        hooks (ex.: import via XML-RPC).
        """
        result = super(SaleOrder, self).write(vals)

        if 'state' in vals:
            for order in self:
                if order.state in ['sent', 'sale']:
                    for line in order.order_line:
                        original_name = line.name
                        processed_name = line._process_name_field(original_name)
                        if processed_name != original_name:
                            line.name = processed_name

        return result

    def action_confirm(self):
        """Sincroniza move.name com line.name apos confirmacao.

        Importante para Pickings refletirem a descricao limpa que
        ja foi processada na SO.
        """
        res = super().action_confirm()
        for order in self:
            for line in order.order_line:
                for move in line.move_ids:
                    move.name = line.name
        return res
