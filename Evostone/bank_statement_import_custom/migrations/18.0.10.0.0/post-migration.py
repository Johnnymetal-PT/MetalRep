# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """
    Migração para garantir que todos os parceiros tenham company_id e accg_nr_order
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Busca a empresa padrão
    default_company = env['res.company'].search([], limit=1)
    
    if default_company:
        # Atualiza todos os parceiros sem company_id
        cr.execute("""
            UPDATE res_partner 
            SET company_id = %s 
            WHERE company_id IS NULL
        """, (default_company.id,))
        
        # Gera números de ordem para parceiros existentes sem accg_nr_order
        cr.execute("""
            UPDATE res_partner 
            SET accg_nr_order = id 
            WHERE accg_nr_order IS NULL OR accg_nr_order = 0
        """)