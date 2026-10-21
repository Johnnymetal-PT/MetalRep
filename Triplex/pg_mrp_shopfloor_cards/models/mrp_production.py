# -*- coding: utf-8 -*-
"""Dados que o cartão do Chão de Fábrica mostra e que exigem trabalho do lado do servidor.

Ver o __manifest__.py para o contexto. Dois assuntos:
- a imagem a mostrar, resolvida por precedência entre três origens;
- o tecido da peça, procurado nos componentes da própria ordem de fabrico.
"""
from odoo import api, fields, models

# Ordem de precedência das origens da imagem. A mais específica ganha.
IMAGEM_ORDEM_MANUAL = "x_studio_imagem_estofo"  # Studio, em mrp.production
IMAGEM_LINHA_VENDA = "x_studio_foto"            # Studio, em sale.order.line

# Classificação de componentes usada no projeto (Studio, em stock.move). O painel de
# planeamento da oficina usa a mesma para as colunas de componentes.
TIPO_COMPONENTE = "x_supplier_type"
TIPO_TECIDO = "tecido"


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    pg_card_image_url = fields.Char(
        string="URL da imagem do cartão",
        compute="_compute_pg_card_image_url",
        help="Endereço da imagem a mostrar no Chão de Fábrica, já resolvido por "
             "precedência: imagem manual da ordem, foto da linha de venda, imagem de "
             "catálogo do produto. Vazio quando nenhuma existe.",
    )

    pg_fabric_label = fields.Char(
        string="Tecido da peça",
        compute="_compute_pg_fabric_label",
        help="Tecido a mostrar no cartão do Chão de Fábrica, procurado nos componentes "
             "desta ordem de fabrico. Vazio quando nenhum componente identifica o tecido.",
    )

    # ------------------------------------------------------------------ tecido

    def _pg_fabric_from_components(self):
        """Tecido a partir dos componentes desta ordem de fabrico.

        Duas maneiras de o reconhecer, por esta ordem:
        1. o componente está classificado como tecido no `x_supplier_type` — é a
           classificação estruturada que o painel de planeamento também usa;
        2. o nome do produto contém "TECIDO" — rede de segurança para quando a
           classificação não foi preenchida.
        """
        self.ensure_one()
        componentes = self.move_raw_ids
        if not componentes:
            return ""

        if TIPO_COMPONENTE in componentes._fields:
            classificados = componentes.filtered(
                lambda m: m[TIPO_COMPONENTE] == TIPO_TECIDO
            )
        else:
            classificados = componentes.browse()
        if not classificados:
            classificados = componentes.filtered(
                lambda m: "TECIDO" in (m.product_id.display_name or "").upper()
            )
        if not classificados:
            return ""

        partes = []
        for movimento in classificados:
            texto = movimento.product_id.display_name or ""
            if movimento.product_uom_qty:
                texto = (f"{texto} — {movimento.product_uom_qty:g} "
                         f"{movimento.product_uom.name or ''}").strip()
            partes.append(texto)
        return " · ".join(partes)

    # A descrição da venda (`description_sale`) foi deliberadamente deixada de fora, por
    # decisão do cliente a 28/07/2026. Chegou a ser considerada como segunda origem, porque
    # cobria 13 ordens contra 1 dos componentes, mas é texto livre e não é de confiança para
    # este efeito: a medição encontrou lá "Tecido: Prever 12 metros de tecido liso, com
    # largura de 140 cm", que é uma instrução de compra e não um tecido — e iria direta ao
    # cartão do operador. Os componentes são dado estruturado; o que falta preenche-se lá.
    @api.depends("move_raw_ids.product_id", "move_raw_ids.product_uom_qty")
    def _compute_pg_fabric_label(self):
        for production in self:
            production.pg_fabric_label = production._pg_fabric_from_components() or ""

    # ------------------------------------------------------------------ imagem

    def _pg_sale_line(self):
        """Linha de venda de origem desta ordem de fabrico.

        `move_finished_ids.sale_line_id` vem vazio nestas ordens; o caminho que funciona é
        pelo destino do movimento (cadeia de reabastecimento). Confirmado em `triplex_test`
        a 28/07/2026 nas ordens WH/MO/00103-00105, cada uma a resolver para a linha certa
        da S00718.
        """
        self.ensure_one()
        # `sale_line_id` vem do `sale_stock`, que está declarado nas dependências do módulo
        # precisamente por causa desta travessia.
        return self.move_finished_ids.move_dest_ids.sale_line_id[:1]

    def _pg_tem_binario(self, registo, nome_campo):
        """True se o campo binário tiver conteúdo, sem o carregar para memória.

        O contexto `bin_size` faz o Odoo devolver a dimensão do ficheiro em vez do próprio
        ficheiro. Sem isto, verificar a presença de uma imagem trazia a imagem inteira do
        disco para o servidor só para a descartar — vezes o número de cartões no ecrã.
        """
        if not registo or nome_campo not in registo._fields:
            return False
        return bool(registo.with_context(bin_size=True)[nome_campo])

    # O `x_studio_imagem_estofo` e o `x_studio_foto` são campos Studio e ficam de fora do
    # `depends` de propósito: não existem em todas as bases, e declarar dependência de um
    # campo inexistente rebentaria o arranque do registry. Como o campo calculado não é
    # armazenado, é recalculado em cada leitura de qualquer forma, pelo que não se perde
    # nada — o `depends` aqui só serve a invalidação dentro da mesma transação.
    @api.depends("product_id", "move_finished_ids.move_dest_ids.sale_line_id")
    def _compute_pg_card_image_url(self):
        for production in self:
            # 1. Excepção manual na própria ordem de fabrico.
            if production._pg_tem_binario(production, IMAGEM_ORDEM_MANUAL):
                production.pg_card_image_url = (
                    f"/web/image/mrp.production/{production.id}/{IMAGEM_ORDEM_MANUAL}"
                )
                continue

            # 2. Foto da linha de venda. É o caso dos produtos especiais criados na hora ao
            #    preencher a encomenda, em que ninguém carrega imagem na ficha do produto e
            #    a imagem é posta diretamente na linha.
            linha = production._pg_sale_line()
            if production._pg_tem_binario(linha, IMAGEM_LINHA_VENDA):
                production.pg_card_image_url = (
                    f"/web/image/sale.order.line/{linha.id}/{IMAGEM_LINHA_VENDA}"
                )
                continue

            # 3. Imagem de catálogo do produto.
            if production.product_id and production._pg_tem_binario(
                production.product_id, "image_1920"
            ):
                production.pg_card_image_url = (
                    f"/web/image/product.product/{production.product_id.id}/image_1920"
                )
                continue

            production.pg_card_image_url = ""
