# -*- coding: utf-8 -*-
"""Actualiza os modulos de relatorios e prova que o cabecalho mudou.

`PORQUE E' PRECISA UMA ACTUALIZACAO DE MODULO`
As vistas vivem em XML e so' entram na base com `-u`. Nao e' como a alteracao
das guardas de 07/09, que era Python e entrou com o arranque do servidor. E o
Odoo.sh **nao** actualiza sozinho: nesse mesmo dia empurrei uma alteracao ao
manifesto e a base continuou a declarar 12 dependencias ate' eu correr o
`update_list()`.

`E PORQUE NAO CHEGA VER A VISTA`
Depois da actualizacao a vista tem o texto novo — isso prova que o ficheiro foi
lido, nao que o documento imprime bem. A fase `render` gera o HTML real de uma
encomenda e procura la' dentro o nome da empresa. E' a mesma ideia da prova da
factura: a configuracao pode estar certa e o resultado errado.

  FASE=ver          o que as vistas tem agora
  FASE=actualizar   -u mh_stone_reports, mh_layout_pdf (exige ESCREVER=1)
  FASE=render       gera o HTML de uma encomenda de compra, em transaccao revertida
"""
import os

FASE = os.environ.get('FASE', 'ver')
ESCREVER = os.environ.get('ESCREVER') == '1'

MODULOS = ('mh_stone_reports', 'mh_layout_pdf')

# As vistas de documento dos dez modelos corrigidos.
VISTAS = (
    'mh_stone_reports.view_report_purchaseorder_document',
    'mh_stone_reports.view_report_invoice_document',
    'mh_stone_reports.view_report_sale_quotation_document',
    'mh_stone_reports.view_report_sale_proforma_document',
    'mh_stone_reports.view_report_sale_detailed_quotation_document',
    'mh_stone_reports.view_report_credit_note_document',
    'mh_stone_reports.view_report_debit_note_document',
    'mh_stone_reports.view_report_payment_receipt_document',
    'mh_stone_reports.view_report_proforma_payment_document',
    'mh_stone_reports.view_report_delivery_guide_document',
    'mh_layout_pdf.external_layout_stone',
)


def titulo(t):
    print('')
    print('-' * 72)
    print(t)
    print('-' * 72)


def estado_das_vistas():
    print('  %-58s %-8s %s' % ('vista', 'antigo', 'novo'))
    mau = 0
    for xmlid in VISTAS:
        v = env.ref(xmlid, raise_if_not_found=False)
        if not v:
            print('  %-58s (ausente)' % xmlid.split('.')[-1])
            continue
        arch = str(v.arch_db or '')
        antigo = ('STONE TRADING' in arch or 'Matola' in arch
                  or 'Machava' in arch or 'NUIT' in arch)
        novo = 'company_id.name' in arch or 'company.name' in arch
        if antigo:
            mau += 1
        print('  %-58s %-8s %s'
              % (xmlid.split('.')[-1][:58],
                 'SIM' if antigo else 'nao',
                 'sim' if novo else 'NAO'))
    return mau


env.cr.execute('SELECT current_database()')
print('')
print('=' * 72)
print('RELATORIOS: IDENTIDADE DA EMPRESA')
print('=' * 72)
print('  base: %s' % env.cr.fetchone()[0])
print('  empresa: %s' % env.company.name)

if FASE == 'ver':
    titulo('ESTADO DAS VISTAS')
    mau = estado_das_vistas()
    print('')
    print('  vistas ainda com texto mocambicano: %d' % mau)

elif FASE == 'actualizar':
    titulo('ANTES')
    estado_das_vistas()
    M = env['ir.module.module'].with_context(active_test=False)
    alvo = M.search([('name', 'in', list(MODULOS)), ('state', '=', 'installed')])
    print('')
    print('  modulos a actualizar: %s' % ', '.join(alvo.mapped('name')))
    if not alvo:
        print('  PARADO: nenhum instalado')
    elif not ESCREVER:
        print('  (ensaio — ESCREVER=1)')
    else:
        print('  a actualizar... (recarrega o registo, demora)')
        alvo.button_immediate_upgrade()
        env.cr.commit()
        titulo('DEPOIS')
        mau = estado_das_vistas()
        print('')
        print('  vistas ainda com texto mocambicano: %d' % mau)

elif FASE == 'render':
    titulo('O HTML REAL DE UMA ENCOMENDA DE COMPRA')
    # Sem gravar: cria-se numa transaccao e faz-se rollback no fim.
    try:
        # Se houver encomendas reais, imprime-se **a do cliente**. Uma
        # encomenda inventada por mim prova o modelo; a dele prova o que ele
        # vai ver quando voltar a carregar em imprimir.
        real = env['purchase.order'].search([], order='id desc', limit=1)
        if real:
            print('  encomenda REAL do cliente: %s   fornecedor: %s'
                  % (real.name, real.partner_id.name))
            accao = env.ref('mh_stone_reports.action_report_purchaseorder')
            html = accao._render_qweb_html(accao.report_name, real.ids)[0]
            if isinstance(html, bytes):
                html = html.decode('utf-8', 'replace')
            print('  HTML gerado: %d caracteres' % len(html))
            print('')
            for termo in ('STONE TRADING', 'Matola', 'Machava', 'NUIT', 'MOZA',
                          '4381052010001', 'Daf:',
                          'EVOSTONE', 'Famalicao', 'NIF', '516617770',
                          'TOTAIS:', 'unidades', 'peso'):
                print('    %-16s %s' % (termo, 'PRESENTE' if termo in html else '-'))
            i = html.find('EVOSTONE')
            if i > 0:
                import re as _re
                t = _re.sub(r'<[^>]+>', ' ', html[max(0, i - 150):i + 400])
                print('')
                print('  o que sai impresso:')
                print('    %s' % _re.sub(r'\s+', ' ', t).strip()[:400])
            raise SystemExit

        fornecedor = env['res.partner'].search(
            [('id', '!=', env.company.partner_id.id)], limit=1)
        artigo = env['product.product'].search([], limit=1)
        # O `purchase.order` desta base tem um campo obrigatorio proprio,
        # `service_type_id` -> `service.type` («Tipo de Serviço»), vindo dos
        # modulos do parceiro anterior. A criacao falha sem ele, e nao ha forma
        # de o saber sem tentar: nao esta em nenhuma documentacao do Odoo.
        tipo = env['service.type'].search([], limit=1)
        if not tipo:
            print('  PARADO: nao ha nenhum service.type para preencher o campo')
            print('  obrigatorio do purchase.order.')
            raise SystemExit
        enc = env['purchase.order'].create({
            'partner_id': fornecedor.id,
            'service_type_id': tipo.id,
            'order_line': [(0, 0, {
                'product_id': artigo.id,
                'name': artigo.name,
                'product_qty': 1,
                'price_unit': 100.0,
                'date_planned': '2026-09-30',
            })],
        })
        print('  encomenda temporaria: %s   fornecedor: %s'
              % (enc.name, fornecedor.name))
        accao = env.ref('mh_stone_reports.action_report_purchaseorder')
        html = accao._render_qweb_html(accao.report_name, enc.ids)[0]
        if isinstance(html, bytes):
            html = html.decode('utf-8', 'replace')
        print('  HTML gerado: %d caracteres' % len(html))
        print('')
        for termo in ('STONE TRADING', 'Matola', 'Machava', 'NUIT', 'MOZA',
                      '4381052010001', 'Daf:',
                      'EVOSTONE', 'Famalicao', 'NIF', '516617770',
                      'TOTAIS:', 'unidades', 'area', 'peso'):
            print('    %-16s %s' % (termo, 'PRESENTE' if termo in html else '-'))
        # O rodape com os totais fisicos, para se ver com os olhos.
        import re as _r
        j = html.find('TOTAIS:')
        if j > 0:
            bloco = _r.sub(r'\s+', ' ', _r.sub(r'<[^>]+>', ' ', html[j:j + 260]))
            print('')
            print('  totais impressos:')
            print('    %s' % bloco.strip()[:200])
        # O bloco do cabecalho, para se ver com os olhos.
        i = html.find('EVOSTONE')
        if i > 0:
            trecho = html[max(0, i - 200):i + 400]
            import re as _re
            trecho = _re.sub(r'<[^>]+>', ' ', trecho)
            trecho = _re.sub(r'\s+', ' ', trecho)
            print('')
            print('  o que sai impresso, a volta do nome:')
            print('    %s' % trecho.strip()[:420])
    finally:
        env.cr.rollback()
        print('')
        print('  ROLLBACK feito — nada ficou gravado.')
        env.cr.execute('select count(*) from purchase_order')
        print('  purchase_order na base: %s' % env.cr.fetchone()[0])

else:
    print('  FASE desconhecida: %s (ver, actualizar, render)' % FASE)

print('')
print('RELATORIOS=FIM')
