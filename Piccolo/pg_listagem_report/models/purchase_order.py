"""Travessia PO -> MO -> SO para obter o cliente no report Listagem Compras.

Em Piccolo a encomenda de compra (PO) de componentes nao tem o cliente:
o ``partner_id`` da PO e o fornecedor. O cliente vem da encomenda de
venda (SO) que originou a ordem de producao (MO) dos componentes.

A ligacao e reconstruida espelhando ``pg_sale_purchase_link``:
- PO -> MO: por procurement group (``PO.group_id`` ==
  ``MO.procurement_group_id``) e por ``origin`` (``MO.name`` == ``PO.origin``);
- MO -> SO: por ``origin`` (``SO.name`` == ``MO.origin``).

Validado em producao: o caminho fiavel e PO.origin/group -> MO ->
MO.origin -> SO, porque a SO tem o seu proprio procurement group e o
match SO<->MO so resolve por ``origin``.

Este mesmo caminho serve a coluna "Imagem" do report. Nos produtos
especiais (cascos), a linha da PO aponta para um produto generico
("Produto Especial Estrutura", "ESTRUTURA ESPECIAL") que nao tem - nem
pode ter - foto no catalogo: cada pedido e uma peca diferente. A foto
do artigo e carregada pelo comercial na **linha da encomenda de venda**,
no campo Studio ``x_studio_imagem_produto_especial``. Sem esse fallback
a coluna sai vazia exatamente nos casos em que a foto e mais necessaria.
"""
import base64
import logging

from odoo import models
from odoo.tools import image_process

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _pg_listagem_get_mos(self):
        """Devolve as MOs na origem desta encomenda de compra."""
        self.ensure_one()
        Mo = self.env['mrp.production']

        mos = Mo
        if self.group_id:
            mos |= Mo.search([
                ('procurement_group_id', '=', self.group_id.id),
                ('state', '!=', 'cancel'),
            ])
        if self.origin:
            mos |= Mo.search([
                ('name', '=', self.origin),
                ('state', '!=', 'cancel'),
            ])
        return mos

    def _pg_listagem_get_sale_orders(self):
        """Devolve as SOs (clientes) na origem desta encomenda de compra."""
        self.ensure_one()
        So = self.env['sale.order']

        mos = self._pg_listagem_get_mos()

        sos = So
        mo_origins = [o for o in mos.mapped('origin') if o]
        if mo_origins:
            sos |= So.search([('name', 'in', mo_origins)])
        # Redes de seguranca: a origin da PO pode ser diretamente a SO, ou
        # a SO partilhar o group da PO em fluxos sem MO.
        if self.origin:
            sos |= So.search([('name', '=', self.origin)])
        if self.group_id:
            sos |= So.search([('procurement_group_id', '=', self.group_id.id)])
        return sos

    def _pg_listagem_partner_names(self):
        """Nomes distintos dos clientes na origem, para o cabecalho do report."""
        self.ensure_one()
        partners = self._pg_listagem_get_sale_orders().mapped('partner_id')
        return ', '.join(p.name for p in partners if p.name)

    # Campo Studio na linha de venda onde o comercial carrega a foto do
    # produto especial. Vive so na base de dados (Studio), por isso o
    # acesso e defensivo: numa base sem o campo o report continua a sair.
    _PG_LISTAGEM_CAMPO_IMAGEM_SOL = 'x_studio_imagem_produto_especial'

    def _pg_listagem_get_sale_lines(self):
        """Linhas de venda na origem desta PO (o que foi encomendado pelo cliente).

        Caminho: MO -> ``move_dest_ids`` (o move que entrega o produto
        acabado ao cliente) -> ``sale_line_id``. E mais preciso do que ir
        buscar todas as linhas das SOs de origem, porque isola a linha
        que gerou esta producao.
        """
        self.ensure_one()
        moves = self._pg_listagem_get_mos().mapped('move_dest_ids')
        return moves.mapped('sale_line_id')

    def _pg_listagem_imagem_produto_especial(self):
        """Foto carregada nas linhas de venda na origem, se for inequivoca.

        Devolve a imagem apenas quando existe **uma** foto na origem. Com
        varias linhas de venda com foto diferente nao ha forma de saber a
        qual corresponde cada linha da compra (a linha da PO nao tem
        ligacao directa a linha da venda: ``move_dest_ids`` da PO vem
        vazio neste fluxo). Nesse caso nao se mostra nada, em vez de
        arriscar mostrar a foto do artigo errado ao fornecedor.
        """
        self.ensure_one()
        sale_lines = self._pg_listagem_get_sale_lines()
        campo = self._PG_LISTAGEM_CAMPO_IMAGEM_SOL
        if not sale_lines or campo not in sale_lines._fields:
            return False
        imagens = {sl[campo] for sl in sale_lines if sl[campo]}
        if len(imagens) != 1:
            return False
        return imagens.pop()

    def _pg_listagem_line_images(self):
        """Mapa ``{id da linha da compra: imagem}`` para a coluna "Imagem".

        Por linha:
        1. foto do produto do catalogo (caso normal);
        2. foto do produto especial carregada na linha de venda de origem
           (cascos e afins, cujo produto e generico e nunca tem foto).

        Devolve um mapa - e nao uma imagem por chamada - para a travessia
        ate a venda ser feita **uma vez por encomenda**, e nao uma vez por
        linha: o report imprime dezenas de encomendas de uma so vez.

        A foto do produto especial e reduzida a 256px porque o campo
        Studio guarda o ficheiro original da camara (centenas de KB) e a
        coluna mostra-a a 80px.
        """
        self.ensure_one()
        # bin_size=False e obrigatorio para ler binarios: com ``bin_size``
        # no contexto (o cliente web poe-no ao listar registos, e o report
        # e lancado a partir da List View), um campo binario devolve o
        # **tamanho** do ficheiro - b'98.00 Kb' - em vez do conteudo. Isso
        # fazia ``image_process`` rebentar com "This file could not be
        # decoded as an image file" e impedia a impressao da listagem.
        # Ver ``odoo/fields.py`` Binary.convert_to_cache / read (17.0).
        order = self.with_context(bin_size=False)
        imagens = {}
        especial = None  # travessia adiada: so se alguma linha precisar
        for line in order.order_line.filtered(lambda l: not l.display_type):
            imagem = line.product_id.image_128
            if not imagem:
                if especial is None:
                    especial = order._pg_listagem_resize(
                        order._pg_listagem_imagem_produto_especial())
                imagem = especial
            if imagem:
                imagens[line.id] = imagem
        return imagens

    def _pg_listagem_resize(self, imagem):
        """Reduz a imagem (base64 -> base64); False se nao for imagem.

        ``image_process`` trabalha com os **bytes crus** da imagem, nao
        com base64: e preciso descodificar a entrada e voltar a codificar
        a saida, tal como o proprio Odoo faz em ``fields.Image``
        (``odoo/fields.py``, ``Image._image_process``). Passar-lhe base64
        directamente da "This file could not be decoded as an image file".

        O campo Studio e um binario livre - aceita o que o comercial la
        puser. Se um dia la cair um ficheiro que nao seja imagem, a linha
        sai sem foto e fica o aviso no log, em vez de impedir a impressao
        da listagem **inteira**, incluindo encomendas sem relacao com ele.
        """
        if not imagem:
            return False
        try:
            reduzida = image_process(base64.b64decode(imagem), size=(256, 256))
        except Exception:
            _logger.warning(
                "Listagem Compras: ficheiro nao interpretavel como imagem em "
                "%s da linha de venda na origem da compra %s; linha impressa "
                "sem imagem.", self._PG_LISTAGEM_CAMPO_IMAGEM_SOL, self.name)
            return False
        return base64.b64encode(reduzida) if reduzida else False
