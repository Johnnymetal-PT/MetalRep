# -*- coding: utf-8 -*-
"""Prova a correccao do `_get_in_svl_vals` contra os dados reais, sem publicar.

`PORQUE ASSIM E NAO NO STAGING`
O host de staging tem o id do build no nome; ao publicar, o build muda de id e o
host antigo deixa de resolver. Nao tenho a interface do Odoo.sh para ler o novo.

`E PORQUE ISTO E' PROVA A SERIO`
A correccao e' aplicada **em memoria, nesta sessao de shell**, sobre a classe do
modulo. O processo do shell e' separado dos trabalhadores que servem o Odoo:
nada disto afecta quem esta a usar o sistema, e acaba quando o processo acaba.
A transaccao e' revertida no fim.

Corre a recepcao da P00002 real, 23 linhas, com a categoria no custo medio que
ela tem hoje em producao — a condicao exacta que faz rebentar a versao actual.

`A ORDEM IMPORTA`
Primeiro **sem** a correccao, para confirmar que rebenta. Se nao rebentar, a
minha explicacao esta errada e nao adianta provar a cura. So' depois com.
"""
import traceback

print('')
print('=' * 74)
print('A CORRECCAO DO SVL, PROVADA NOS DADOS REAIS')
print('=' * 74)

cat = env['product.category'].search([('complete_name', '=', 'Todos / Mercadoria')], limit=1)
print('  categoria %-22s metodo de custo: %s'
      % (cat.complete_name, cat.property_cost_method))

enc = env['purchase.order'].search([('name', '=', 'P00002')], limit=1)
linhas = enc.order_line.filtered(lambda l: not l.display_type)
nao_pcmp = len(linhas.filtered(lambda l: l.product_id.cost_method != 'pcmp'))
print('  %s  %d linhas  %.2f EUR   linhas NAO-PCMP: %d'
      % (enc.name, len(linhas), enc.amount_total, nao_pcmp))


def recebe(etiqueta):
    print('')
    print('-' * 74)
    print(etiqueta)
    print('-' * 74)
    try:
        e = env['purchase.order'].search([('name', '=', 'P00002')], limit=1)
        ls = e.order_line.filtered(lambda l: not l.display_type)
        for i, l in enumerate(ls, 1):
            l.lot_name = 'ENS-%03d' % i
        w = env['purchase.confirm.wizard'].create({'purchase_order_id': e.id})
        w.action_confirm()
        e.invalidate_recordset()
        p = e.picking_ids[0]
        for mv in p.move_ids:
            mv.quantity = mv.product_uom_qty
        p.button_validate()
        p.invalidate_recordset()
        print('  [OK] %s -> %s' % (p.name, p.state))
        print('       existencias            : %d' % env['stock.quant'].search_count([]))
        print('       chapas (stock.lot)     : %d' % env['stock.lot'].search_count([]))
        print('       camadas de valorizacao : %d'
              % env['stock.valuation.layer'].search_count([]))
        print('       lancamentos contabil.  : %d' % env['account.move'].search_count([]))
        return True
    except Exception as ex:
        ls = [l for l in traceback.format_exc().splitlines() if 'Error' in l]
        print('  [!!] %s' % (ls[-1] if ls else str(ex))[:120])
        return False
    finally:
        env.cr.rollback()


# ---------------------------------------------------------------- 1. como esta
antes_ok = recebe('1. CODIGO ACTUAL — tem de rebentar, ou a minha explicacao cai')

# ------------------------------------------------------- 2. com a correccao
import odoo.addons.mh_stock_valuation.models.stock_move as mod
Cls = mod.StockMove


def _get_in_svl_vals_novo(self, forced_quantity):
    pcmp = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
    outros = self - pcmp
    vals = []
    for mv in pcmp:
        vals += mv._get_pcmp_in_svl_vals(forced_quantity)
    if outros:
        vals += super(Cls, outros)._get_in_svl_vals(forced_quantity)
    return vals


def _get_out_svl_vals_novo(self, forced_quantity):
    pcmp = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
    outros = self - pcmp
    vals = []
    for mv in pcmp:
        vals += mv._get_pcmp_out_svl_vals(forced_quantity)
    if outros:
        vals += super(Cls, outros)._get_out_svl_vals(forced_quantity)
    return vals


Cls._get_in_svl_vals = _get_in_svl_vals_novo
Cls._get_out_svl_vals = _get_out_svl_vals_novo
print('')
print('  (correccao aplicada em memoria, so nesta sessao)')

depois_ok = recebe('2. COM A CORRECCAO — tem de passar')

print('')
print('=' * 74)
print('  antes da correccao: %s' % ('passou' if antes_ok else 'REBENTOU'))
print('  com a correccao   : %s' % ('PASSOU' if depois_ok else 'rebentou'))
if not antes_ok and depois_ok:
    print('  -> a correccao resolve, e o problema era mesmo este')
elif antes_ok:
    print('  -> ATENCAO: passou sem a correccao. A minha explicacao esta errada.')
else:
    print('  -> a correccao NAO resolve. Ha outra coisa.')
print('=' * 74)

env.cr.rollback()
env.cr.execute('select count(*) from stock_quant')
print('')
print('  existencias na base: %s' % env.cr.fetchone()[0])
print('')
print('PROVA_SVL=FIM')
