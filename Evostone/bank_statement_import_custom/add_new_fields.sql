-- Script SQL para adicionar os novos campos de numeração separada
-- Execute com: docker exec claude-code-postgres-1 psql -U odoo -d teste2 -f /mnt/extra-addons/bank_statement_import_custom/add_new_fields.sql

-- Adicionar campos
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS accg_nr_order_customer INTEGER;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS accg_nr_order_supplier INTEGER;

-- Popular campos para clientes existentes
WITH clientes_numerados AS (
    SELECT id, 
           ROW_NUMBER() OVER (ORDER BY COALESCE(accg_nr_order, 999999), id) as novo_numero
    FROM res_partner
    WHERE customer_rank > 0 AND supplier_rank = 0
)
UPDATE res_partner
SET accg_nr_order_customer = cn.novo_numero
FROM clientes_numerados cn
WHERE res_partner.id = cn.id
  AND res_partner.accg_nr_order_customer IS NULL;

-- Popular campos para fornecedores existentes
WITH fornecedores_numerados AS (
    SELECT id, 
           ROW_NUMBER() OVER (ORDER BY COALESCE(accg_nr_order, 999999), id) as novo_numero
    FROM res_partner
    WHERE supplier_rank > 0 AND customer_rank = 0
)
UPDATE res_partner
SET accg_nr_order_supplier = fn.novo_numero
FROM fornecedores_numerados fn
WHERE res_partner.id = fn.id
  AND res_partner.accg_nr_order_supplier IS NULL;

-- Verificar resultado
SELECT 'Estatísticas após adicionar campos:' as info;
SELECT 
    CASE 
        WHEN customer_rank > 0 AND supplier_rank = 0 THEN 'Cliente'
        WHEN supplier_rank > 0 AND customer_rank = 0 THEN 'Fornecedor'
        ELSE 'Outro'
    END as tipo,
    COUNT(*) as total,
    MIN(accg_nr_order_customer) as min_cliente,
    MAX(accg_nr_order_customer) as max_cliente,
    MIN(accg_nr_order_supplier) as min_fornecedor,
    MAX(accg_nr_order_supplier) as max_fornecedor
FROM res_partner
GROUP BY 1
ORDER BY 1;