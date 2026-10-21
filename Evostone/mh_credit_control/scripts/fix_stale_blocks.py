#!/usr/bin/env python3
"""
Script para corrigir bloqueios de crédito obsoletos.
Executar via Odoo shell:
    odoo-bin shell -c odoo.conf -d stone-trading-mhc-main-090126

Depois executar:
    exec(open('custom-addons/ubuntu_server/mh_credit_control/scripts/fix_stale_blocks.py').read())
"""

def fix_stale_credit_blocks():
    """
    Recalcula todos os bloqueios de crédito em ordens de venda em rascunho.
    Útil para corrigir bloqueios que deveriam ter sido removidos quando
    facturas foram pagas.
    """
    print("=" * 60)
    print("CORRECÇÃO DE BLOQUEIOS DE CRÉDITO OBSOLETOS")
    print("=" * 60)

    # Buscar todas as ordens em rascunho que têm bloqueios
    orders_with_blocks = env['sale.order'].search([
        ('state', 'in', ['draft', 'sent']),
        '|', '|',
        ('has_credit_limit_block', '=', True),
        ('has_overdue_block', '=', True),
        ('has_pending_block', '=', True),
    ])

    print(f"\nOrdens com bloqueios activos: {len(orders_with_blocks)}")

    fixed_count = 0

    for order in orders_with_blocks:
        print(f"\n--- Analisando: {order.name} ---")
        print(f"  Cliente: {order.partner_invoice_id.name}")
        print(f"  Bloqueios actuais:")
        print(f"    - Limite crédito: {order.has_credit_limit_block}")
        print(f"    - Vencidas: {order.has_overdue_block}")
        print(f"    - Pendentes: {order.has_pending_block}")

        # Guardar estado anterior
        old_credit = order.has_credit_limit_block
        old_overdue = order.has_overdue_block
        old_pending = order.has_pending_block

        # Forçar recálculo
        order._compute_credit_blocks()

        # Verificar se mudou
        if (old_credit != order.has_credit_limit_block or
            old_overdue != order.has_overdue_block or
            old_pending != order.has_pending_block):

            print(f"  CORRIGIDO! Novos valores:")
            print(f"    - Limite crédito: {order.has_credit_limit_block}")
            print(f"    - Vencidas: {order.has_overdue_block}")
            print(f"    - Pendentes: {order.has_pending_block}")
            fixed_count += 1
        else:
            print(f"  (sem alteração - bloqueios são válidos)")

    print("\n" + "=" * 60)
    print(f"RESUMO: {fixed_count} ordens corrigidas de {len(orders_with_blocks)} analisadas")
    print("=" * 60)

    # Commit das alterações
    env.cr.commit()
    print("\nAlterações gravadas com sucesso!")


def fix_specific_order(order_name):
    """
    Recalcula bloqueios para uma ordem específica.
    Uso: fix_specific_order('S00123')
    """
    order = env['sale.order'].search([('name', '=', order_name)], limit=1)
    if not order:
        print(f"Ordem {order_name} não encontrada!")
        return

    print(f"Ordem: {order.name}")
    print(f"Estado: {order.state}")
    print(f"Cliente: {order.partner_invoice_id.name}")

    partner = order.partner_invoice_id.commercial_partner_id
    print(f"\nEstado actual do cliente:")
    print(f"  - Tem facturas vencidas: {partner.has_overdue_invoices}")
    print(f"  - Tem facturas pendentes: {partner.has_pending_invoices}")
    print(f"  - Total vencido: {partner.overdue_invoice_amount}")
    print(f"  - Total pendente: {partner.pending_invoice_amount}")

    print(f"\nBloqueios na ordem (ANTES):")
    print(f"  - has_credit_limit_block: {order.has_credit_limit_block}")
    print(f"  - has_overdue_block: {order.has_overdue_block}")
    print(f"  - has_pending_block: {order.has_pending_block}")
    print(f"  - credit_blocked: {order.credit_blocked}")

    # Forçar recálculo
    order._compute_credit_blocks()

    print(f"\nBloqueios na ordem (DEPOIS):")
    print(f"  - has_credit_limit_block: {order.has_credit_limit_block}")
    print(f"  - has_overdue_block: {order.has_overdue_block}")
    print(f"  - has_pending_block: {order.has_pending_block}")
    print(f"  - credit_blocked: {order.credit_blocked}")

    env.cr.commit()
    print("\nAlterações gravadas!")


# Menu de opções
print("\nComandos disponíveis:")
print("  fix_stale_credit_blocks()  - Corrigir todas as ordens com bloqueios obsoletos")
print("  fix_specific_order('S00123')  - Corrigir uma ordem específica")
print()
