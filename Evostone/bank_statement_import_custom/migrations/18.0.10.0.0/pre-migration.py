# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """
    Pre-migração para adicionar coluna accg_nr_order se não existir
    """
    # Adiciona a coluna accg_nr_order se não existir
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_partner' AND column_name='accg_nr_order'
    """)
    
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE res_partner 
            ADD COLUMN accg_nr_order INTEGER
        """)
        
        # Gera valores para registros existentes
        cr.execute("""
            UPDATE res_partner 
            SET accg_nr_order = id 
            WHERE accg_nr_order IS NULL
        """)
    
    # Garante que todos os parceiros tenham company_id
    cr.execute("""
        UPDATE res_partner 
        SET company_id = 1 
        WHERE company_id IS NULL
    """)