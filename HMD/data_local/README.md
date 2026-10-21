# data_local — extrações com PII (NÃO versionado)

Esta pasta está em `.gitignore`. Serve para colocar as extrações brutas PHC/Odoo
para análise local. **Nunca commitar** — contém dados pessoais de clientes (RGPD).

## Ficheiros esperados

### `odoo_partners.csv` (ou `.xlsx`) — `res.partner` SEM filtro
Colunas (cabeçalho na 1.ª linha):
`id, name, parent_id, company_type, customer_rank, supplier_rank, vat, email, phone, mobile, street, city, country_id`

Importante: extração **sem domínio/filtro** — incluir contactos-filho e `customer_rank = 0`.

### `phc_clientes.csv` (ou `.xlsx`) — clientes PHC
Colunas: `Nº Cliente, Nome, NIF, Email, Telefone, Telemóvel, Morada, Localidade, País`

## Resultado
A análise (matching determinístico por VAT/email, sem duplicar) é gerada em
`comparacao_phc_odoo_vat_email.xlsx` na raiz da repo.
