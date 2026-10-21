"""Helper no stock.move para a coluna "Material em Falta" do report Listagem.

O QWeb (report_picking_grouped_inherit.xml) chama
``move._pg_listagem_material_pronto()`` por cada linha da listagem para
decidir a mensagem da coluna "Material em Falta".

Controlo manual: o estado depende do campo Studio booleano
``x_studio_pronto``, preenchido pelo utilizador em cada componente
(``move_raw_ids``) da MO de origem. Assim o controlo fica integralmente
do lado do cliente, como pedido — sem inferencia automatica por
fornecedor ou por receecao de PO.
"""
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _pg_listagem_get_mo(self):
        """Devolve a MO de origem deste move (match por ``origin`` + produto).

        Restringe a MO que produziu este move: mesmo ``origin`` (tipicamente
        o nome da SO) e mesmo ``product_id``, ignorando MOs canceladas.
        """
        self.ensure_one()
        if not self.origin or not self.product_id:
            return self.env['mrp.production']
        return self.env['mrp.production'].search(
            [
                ('origin', '=', self.origin),
                ('product_id', '=', self.product_id.id),
                ('state', '!=', 'cancel'),
            ],
            limit=1,
            order='create_date desc',
        )

    def _pg_listagem_material_pronto(self):
        """True quando TODO o material da MO esta marcado como pronto.

        O material esta pronto quando **todas** as linhas de componente da
        MO (``move_raw_ids``) tem o campo manual ``x_studio_pronto`` a True.
        Se nao houver MO de origem ou componentes, devolve False (material
        por validar -> tratado como "em falta" no report).
        """
        self.ensure_one()
        mo = self._pg_listagem_get_mo()
        if not mo or not mo.move_raw_ids:
            return False
        return all(raw.x_studio_pronto for raw in mo.move_raw_ids)

    # Grupos de material, por ordem de apresentacao no report.
    _PG_LISTAGEM_GRUPOS = ('TECIDO', 'ESTRUTURA', 'ACABAMENTO')

    # Mapa: tipo de fornecedor (res.partner.pg_componente_tipo) -> grupo
    # apresentado no report. Decisao do cliente: manter os valores do campo
    # (casco/tecido/polimento) e mapear os nomes de grupo aqui.
    _PG_LISTAGEM_TIPO_TO_GRUPO = {
        'tecido': 'TECIDO',
        'casco': 'ESTRUTURA',
        'polimento': 'ACABAMENTO',
    }

    def _pg_listagem_material_falta_por_grupo(self):
        """Componentes em falta da MO, agrupados por TECIDO/ESTRUTURA/ACABAMENTO.

        "Em falta" = linha de componente (``move_raw_ids``) com
        ``x_studio_pronto`` a False. A atribuicao ao grupo e feita pelo
        **fornecedor principal** do componente
        (``product_id.seller_ids[:1].partner_id``) e o campo
        ``pg_componente_tipo`` desse fornecedor, via
        ``_PG_LISTAGEM_TIPO_TO_GRUPO``.

        Componentes cujo fornecedor nao tenha ``pg_componente_tipo``
        preenchido (ou sem fornecedor configurado) NAO sao listados -
        assume-se que sao de outro tipo ou nem sequer material relevante
        (decisao do cliente).

        Devolve uma lista de tuplos ``(grupo, [nomes])`` pela ordem de
        ``_PG_LISTAGEM_GRUPOS``, para o QWeb iterar. Grupos sem componentes
        em falta vem com lista vazia (o template ignora-os).
        """
        self.ensure_one()
        grupos = {g: [] for g in self._PG_LISTAGEM_GRUPOS}
        mo = self._pg_listagem_get_mo()
        if mo:
            for raw in mo.move_raw_ids:
                if raw.x_studio_pronto:
                    continue
                supplier = raw.product_id.seller_ids[:1].partner_id
                tipo = supplier.pg_componente_tipo if supplier else False
                grupo = self._PG_LISTAGEM_TIPO_TO_GRUPO.get(tipo)
                if grupo:
                    grupos[grupo].append(raw.product_id.display_name)
        return [(grupo, grupos[grupo]) for grupo in self._PG_LISTAGEM_GRUPOS]
