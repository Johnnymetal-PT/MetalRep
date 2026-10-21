# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """
    Migração para converter contas por empresa em contas globais compartilhadas
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Busca todas as contas existentes
    cr.execute("""
        SELECT DISTINCT prefix, name, partner_limite, country_id
        FROM company_chart_account
        WHERE company_id IS NOT NULL
    """)
    
    existing_accounts = cr.fetchall()
    
    # Para cada conta única, cria uma versão global
    for prefix, name, partner_limite, country_id in existing_accounts:
        # Verifica se já existe uma conta global com este prefixo
        cr.execute("""
            SELECT id FROM company_chart_account 
            WHERE prefix = %s AND company_id IS NULL
        """, (prefix,))
        
        if not cr.fetchone():
            # Cria a conta global
            cr.execute("""
                INSERT INTO company_chart_account (prefix, name, partner_limite, country_id, active, create_uid, create_date, write_uid, write_date)
                VALUES (%s, %s, %s, %s, true, %s, NOW(), %s, NOW())
                RETURNING id
            """, (prefix, name, partner_limite, country_id, SUPERUSER_ID, SUPERUSER_ID))
            
            global_account_id = cr.fetchone()[0]
            
            # Associa a conta global a todas as empresas que tinham esta conta
            cr.execute("""
                SELECT DISTINCT company_id 
                FROM company_chart_account 
                WHERE prefix = %s AND company_id IS NOT NULL
            """, (prefix,))
            
            for company_id, in cr.fetchall():
                cr.execute("""
                    INSERT INTO company_chart_account_rel (company_id, account_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (company_id, global_account_id))
    
    # Remove as contas antigas que tinham company_id
    cr.execute("""
        DELETE FROM company_chart_account 
        WHERE company_id IS NOT NULL
    """)
    
    # Remove a coluna company_id se ainda existir
    cr.execute("""
        ALTER TABLE company_chart_account 
        DROP COLUMN IF EXISTS company_id CASCADE
    """)