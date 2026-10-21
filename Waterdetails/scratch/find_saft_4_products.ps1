$baseUrl = "https://virgin-details.odoo.com"

# 1. Obter todas as linhas de fatura/nota de credito em Agosto 2026
$linesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model account.move.line -Method search_read -Domain '[["move_id.company_id","=",1],["move_id.invoice_date",">=","2026-08-01"],["move_id.invoice_date","<=","2026-08-31"],["move_id.state","=","posted"],["move_id.move_type","in",["out_invoice","out_refund"]],["display_type","=","product"]]' -Fields product_id,move_id
$lines = $linesJson | ConvertFrom-Json
$prodIds = $lines | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] } | Select-Object -Unique

# 2. Obter changelog de produtos se existir
$changelogJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model l10n_pt_product_changelog -Method search_read -Domain '[["company_id","=",1],["date",">=","2026-08-01"],["date","<=","2026-08-31"]]' -Fields product_id
if ($changelogJson) {
    $cl = $changelogJson | ConvertFrom-Json
    $clProdIds = $cl | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] }
    $prodIds = @($prodIds + $clProdIds) | Select-Object -Unique
}

# 3. Ler os dados dos produtos
$prodsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain ('[["id","in",[' + ($prodIds -join ',') + ']]]') -Fields id,name,default_code,categ_id,product_tmpl_id
$prods = $prodsJson | ConvertFrom-Json

Write-Output "Total de produtos identificados no periodo: $($prods.Count)"
$noCat = $prods | Where-Object { -not $_.categ_id }
Write-Output "Produtos sem categ_id: $($noCat.Count)"
$noCat | ForEach-Object {
    $tmplId = if ($_.product_tmpl_id) { $_.product_tmpl_id[0] } else { $_.id }
    Write-Output " - ID Prod: $($_.id) | ID Tmpl: $tmplId | Ref: $($_.default_code) | Nome: $($_.name)"
}
