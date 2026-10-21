# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """
    Adiciona os novos campos accg_nr_order_customer e accg_nr_order_supplier
    """
    _logger.info("Adicionando campos de numeração separada para clientes e fornecedores...")
    
    # Adicionar campo para numeração de clientes
    cr.execute("""
        ALTER TABLE res_partner 
        ADD COLUMN IF NOT EXISTS accg_nr_order_customer INTEGER
    """)
    _logger.info("Campo accg_nr_order_customer adicionado")
    
    # Adicionar campo para numeração de fornecedores
    cr.execute("""
        ALTER TABLE res_partner 
        ADD COLUMN IF NOT EXISTS accg_nr_order_supplier INTEGER
    """)
    _logger.info("Campo accg_nr_order_supplier adicionado")
    
    # Popular os novos campos com base nos dados existentes
    # Clientes
    cr.execute("""
        WITH clientes_numerados AS (
            SELECT id, 
                   ROW_NUMBER() OVER (ORDER BY accg_nr_order, id) as novo_numero
            FROM res_partner
            WHERE customer_rank > 0 AND supplier_rank = 0
        )
        UPDATE res_partner
        SET accg_nr_order_customer = cn.novo_numero
        FROM clientes_numerados cn
        WHERE res_partner.id = cn.id
    """)
    clientes = cr.rowcount
    _logger.info(f"Numerados {clientes} clientes")
    
    # Fornecedores
    cr.execute("""
        WITH fornecedores_numerados AS (
            SELECT id, 
                   ROW_NUMBER() OVER (ORDER BY accg_nr_order, id) as novo_numero
            FROM res_partner
            WHERE supplier_rank > 0 AND customer_rank = 0
        )
        UPDATE res_partner
        SET accg_nr_order_supplier = fn.novo_numero
        FROM fornecedores_numerados fn
        WHERE res_partner.id = fn.id
    """)
    fornecedores = cr.rowcount
    _logger.info(f"Numerados {fornecedores} fornecedores")
    
    _logger.info("Migração concluída com sucesso")