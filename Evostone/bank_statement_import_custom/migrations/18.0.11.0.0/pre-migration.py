# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """
    Migração para converter accg_nr_order de VARCHAR para INTEGER
    """
    # Verifica o tipo da coluna
    cr.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name='res_partner' AND column_name='accg_nr_order'
    """)
    
    result = cr.fetchone()
    if result and result[0] != 'integer':
        # Remove a coluna antiga
        cr.execute("""
            ALTER TABLE res_partner 
            DROP COLUMN IF EXISTS accg_nr_order
        """)
        
        # Adiciona como integer
        cr.execute("""
            ALTER TABLE res_partner 
            ADD COLUMN accg_nr_order INTEGER
        """)
        
        # Preenche com valores baseados no ID
        cr.execute("""
            UPDATE res_partner 
            SET accg_nr_order = id
        """)