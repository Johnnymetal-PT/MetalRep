$allNoCatJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.template -Method search_read -Domain '[["categ_id","=",false]]' -Fields id,name,default_code,type
$allNoCat = $allNoCatJson | ConvertFrom-Json

$linesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model account.move.line -Method search_read -Domain '[["move_id.company_id","=",1],["move_id.invoice_date",">=","2026-08-01"],["move_id.invoice_date","<=","2026-08-31"],["move_id.state","=","posted"],["move_id.move_type","in",["out_invoice","out_refund"]],["display_type","=","product"]]' -Fields product_id
$lines = $linesJson | ConvertFrom-Json
$augProdIds = $lines | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] }

$augProdsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain ('[["id","in",[' + ($augProdIds -join ',') + ']],["categ_id","=",false]]') -Fields id,name,default_code,product_tmpl_id
$augProds = $augProdsJson | ConvertFrom-Json

$baseUrl = "https://virgin-details.odoo.com"

Write-Output "--- ARTIGOS FATURADOS AGOSTO ---"
foreach ($p in $augProds) {
    $tmplId = if ($p.product_tmpl_id) { $p.product_tmpl_id[0] } else { $p.id }
    $ref = if ($p.default_code) { $p.default_code } else { "(sem ref)" }
    Write-Output "[$($p.name) - $ref]($baseUrl/web#id=$tmplId&model=product.template)"
}

Write-Output "`n--- RESTANTES ARTIGOS SEM CATEGORIA ---"
$augTmplIds = $augProds | ForEach-Object { if ($_.product_tmpl_id) { $_.product_tmpl_id[0] } else { $_.id } }
foreach ($t in $allNoCat) {
    if ($augTmplIds -contains $t.id) { continue }
    $ref = if ($t.default_code) { $t.default_code } else { "(sem ref)" }
    Write-Output "[$($t.name) - $ref]($baseUrl/web#id=$($t.id)&model=product.template)"
}
