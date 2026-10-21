"""Wizard de cálculo de cubicagem e peso para um stock.move.

Recebe até 6 trios "Comprimento x Altura x Largura", soma os 6
produtos para obter a cubicagem (m3), aplica densidade fixa de 80
para estimar o peso (Kg), e grava em campos Studio do move.

Persistência dos inputs (pedido Piccolo): ao "Calcular", o wizard NÃO
grava de volta no produto — os inputs ficam guardados **na própria
Entrega** (``stock.move.pg_cubicagem_inputs``, JSON) e aplicam-se os
totais ao ``stock.move``. As dimensões/volumes do produto só mudam por
edição direta no produto (ou pelas automações Studio próprias do
produto), nunca a partir deste wizard.

Pré-preenchimento ao abrir:
1. se a Entrega já tem inputs guardados (``pg_cubicagem_inputs``),
   reabre com esses valores — o operador retoma o que introduziu para
   aquela Entrega;
2. caso contrário, pré-preenche a partir do produto (só leitura). A
   Piccolo mantém o packing list sobretudo ao nível do
   ``product.template``; alguns produtos multi-dimensão usam o nível
   ``product.product`` (variante). Espelha-se a automação Studio "PG
   Packing List Totals": lê-se da variante quando esta já tem dados
   próprios (``x_studio_volumes_3`` > 0), caso contrário do template.
"""
from odoo import models, fields, api


# Mapas wizard -> campo Studio, por nível. Reutilizam campos já
# existentes em produção; ver memória do projeto
# "cubicagem-packing-studio-automations" para o inventário completo.
_WIZARD_TO_TEMPLATE = {
    'comprimento_1': 'x_studio_comprimento',
    'comprimento_2': 'x_studio_comprimento_2',
    'comprimento_3': 'x_studio_comprimento_3',
    'comprimento_4': 'x_studio_comprimento_4',
    'comprimento_5': 'x_studio_comprimento_5',
    'comprimento_6': 'x_studio_comprimento_6',
    'altura_1': 'x_studio_altura',
    'altura_2': 'x_studio_altura_2',
    'altura_3': 'x_studio_altura_3',
    'altura_4': 'x_studio_altura_4',
    'altura_5': 'x_studio_altura_5',
    'altura_6': 'x_studio_altura_6',
    'largura_1': 'x_studio_largura',
    'largura_2': 'x_studio_largura_2',
    'largura_3': 'x_studio_largura_3',
    'largura_4': 'x_studio_largura_4',
    'largura_5': 'x_studio_largura_5',
    'largura_6': 'x_studio_largura_6',
    'volumes': 'x_studio_volumes_2',
}
_WIZARD_TO_VARIANT = {
    'comprimento_1': 'x_studio_comprimento_1',
    'comprimento_2': 'x_studio_comprimento_2_1',
    'comprimento_3': 'x_studio_comprimento_3_1',
    'comprimento_4': 'x_studio_comprimento_4_1',
    'comprimento_5': 'x_studio_comprimento_5_1',
    'comprimento_6': 'x_studio_comprimento_6_1',
    'altura_1': 'x_studio_altura_1',
    'altura_2': 'x_studio_altura_2_1',
    'altura_3': 'x_studio_altura_3_1',
    'altura_4': 'x_studio_altura_4_1',
    'altura_5': 'x_studio_altura_5_1',
    'altura_6': 'x_studio_altura_6_1',
    'largura_1': 'x_studio_largura_1',
    'largura_2': 'x_studio_largura_2_1',
    'largura_3': 'x_studio_largura_3_1',
    'largura_4': 'x_studio_largura_4_1',
    'largura_5': 'x_studio_largura_5_1',
    'largura_6': 'x_studio_largura_6_1',
    'volumes': 'x_studio_volumes_3',
}

# Campos de input do wizard que se persistem por Entrega no
# ``stock.move.pg_cubicagem_inputs`` (JSON). São as chaves comuns aos
# mapas acima (volumes + 6 trios C/A/L).
_WIZARD_INPUT_FIELDS = tuple(_WIZARD_TO_TEMPLATE)


class StockMoveCubicagemWizard(models.TransientModel):
    _name = 'stock.move.cubicagem.wizard'
    _description = 'Cubicagem Calculation Wizard'

    move_id = fields.Many2one('stock.move', required=True)

    volumes = fields.Float(string="Volumes")

    # 6 conjuntos de dimensoes para acomodar cargas heterogeneas
    # (ex.: A=palete grande, B=caixa media, C=caixa pequena).
    comprimento_1 = fields.Float()
    altura_1 = fields.Float()
    largura_1 = fields.Float()
    comprimento_2 = fields.Float()
    altura_2 = fields.Float()
    largura_2 = fields.Float()
    comprimento_3 = fields.Float()
    altura_3 = fields.Float()
    largura_3 = fields.Float()
    comprimento_4 = fields.Float()
    altura_4 = fields.Float()
    largura_4 = fields.Float()
    comprimento_5 = fields.Float()
    altura_5 = fields.Float()
    largura_5 = fields.Float()
    comprimento_6 = fields.Float()
    altura_6 = fields.Float()
    largura_6 = fields.Float()

    cubicagem = fields.Float(string="Cubicagem", compute="_compute_cubicagem_and_peso", store=False)
    peso_kg = fields.Float(string="Peso (Kg)", compute="_compute_cubicagem_and_peso", store=False)

    @api.depends(
        'comprimento_1', 'altura_1', 'largura_1',
        'comprimento_2', 'altura_2', 'largura_2',
        'comprimento_3', 'altura_3', 'largura_3',
        'comprimento_4', 'altura_4', 'largura_4',
        'comprimento_5', 'altura_5', 'largura_5',
        'comprimento_6', 'altura_6', 'largura_6',
    )
    def _compute_cubicagem_and_peso(self):
        for rec in self:
            cubicagem = (
                (rec.comprimento_1 or 0) * (rec.altura_1 or 0) * (rec.largura_1 or 0) +
                (rec.comprimento_2 or 0) * (rec.altura_2 or 0) * (rec.largura_2 or 0) +
                (rec.comprimento_3 or 0) * (rec.altura_3 or 0) * (rec.largura_3 or 0) +
                (rec.comprimento_4 or 0) * (rec.altura_4 or 0) * (rec.largura_4 or 0) +
                (rec.comprimento_5 or 0) * (rec.altura_5 or 0) * (rec.largura_5 or 0) +
                (rec.comprimento_6 or 0) * (rec.altura_6 or 0) * (rec.largura_6 or 0)
            )
            rec.cubicagem = cubicagem
            # Densidade fixa convencionada com a Piccolo (Kg/m3).
            # Para materiais fora do tipico, corrigir manualmente no move.
            rec.peso_kg = cubicagem * 80

    @api.model
    def _pg_packing_target(self, move):
        """Devolve ``(record, mapa)`` onde ler/gravar os inputs de packing.

        Espelha a automação Studio dos totais: usa a variante
        (``product.product``) quando esta já tem dados próprios
        (``x_studio_volumes_3`` > 0); caso contrário usa o template
        (``product.template``), onde a Piccolo mantém a maioria dos dados.
        """
        product = move.product_id
        if not product:
            return self.env['product.template'], _WIZARD_TO_TEMPLATE
        if (product.x_studio_volumes_3 or 0) > 0:
            return product, _WIZARD_TO_VARIANT
        return product.product_tmpl_id, _WIZARD_TO_TEMPLATE

    @api.model
    def default_get(self, fields_list):
        """Pré-preenche o wizard com as dimensões/volumes já guardados.

        Prioridade:
        1. inputs já guardados **para esta Entrega** no move
           (``pg_cubicagem_inputs``) — é o que o operador introduziu na
           última utilização da calculadora para este ``stock.move``;
        2. se a Entrega ainda não tem inputs próprios, pré-preenche a
           partir do produto (só leitura), escolhendo o nível
           template/variante como antes, para o operador partir de um
           valor de referência.
        """
        defaults = super().default_get(fields_list)
        move_id = defaults.get('move_id') or self.env.context.get('default_move_id')
        if not move_id:
            return defaults
        move = self.env['stock.move'].browse(move_id)

        # 1) valores guardados para esta Entrega têm prioridade
        saved = move.pg_cubicagem_inputs or {}
        if saved:
            for wiz_field in _WIZARD_INPUT_FIELDS:
                if wiz_field in fields_list and wiz_field in saved:
                    defaults[wiz_field] = saved[wiz_field]
            return defaults

        # 2) fallback: pré-preenche a partir do produto (sem escrever)
        record, mapping = self._pg_packing_target(move)
        if not record:
            return defaults
        for wiz_field, src_field in mapping.items():
            # Só preenche o que o formulário pediu e o que existe na BD
            # (os campos Studio podem variar entre ambientes).
            if wiz_field in fields_list and src_field in record._fields:
                defaults[wiz_field] = record[src_field]
        return defaults

    def action_calculate(self):
        self.ensure_one()

        move = self.move_id
        qty = move.product_uom_qty or 0
        volume_per_unit = self.volumes or 0
        peso_per_unit = self.peso_kg or 0
        cubicagem_per_unit = self.cubicagem or 0

        # n.o de caixas necessario:
        # qty / (1 / volume_per_unit) == qty * volume_per_unit
        # (mantido nesta forma porque relatorios externos contam com este
        # arredondamento exato - ceil quando ha resto)
        if volume_per_unit > 0:
            required_boxes = qty / (1 / volume_per_unit)
            required_boxes = int(required_boxes) + (1 if required_boxes % 1 > 0 else 0)
        else:
            required_boxes = 0

        # Totais para o move agregam por quantidade de produto.
        total_peso = peso_per_unit * qty
        total_cubicagem = cubicagem_per_unit * qty

        # NOTA (pedido Piccolo): o wizard deixou de gravar os inputs de
        # packing de volta no produto (template ou variante). As
        # dimensões/volumes do produto não são alteradas a partir daqui.
        # Em vez disso, os inputs ficam guardados nesta Entrega
        # (``move.pg_cubicagem_inputs``), para reabrir a calculadora já
        # preenchida sem tocar no produto.
        packing_inputs = {field: self[field] for field in _WIZARD_INPUT_FIELDS}

        # Os destinos ``x_studio_*`` sao campos Studio - depende destes
        # existirem na BD. Se um upgrade renomear/remover estes campos, este
        # write rebenta.
        move.write({
            'x_studio_volumes_3': required_boxes,
            'x_studio_peso_kg_1': total_peso,
            'x_studio_cubicagem_1': total_cubicagem,
            'pg_cubicagem_inputs': packing_inputs,
        })
