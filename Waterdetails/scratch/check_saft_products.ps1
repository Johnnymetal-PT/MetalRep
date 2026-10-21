$linesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model account.move.line -Method search_read -Domain '[["move_id.company_id","=",1],["move_id.invoice_date",">=","2026-08-01"],["move_id.invoice_date","<=","2026-08-31"],["move_id.state","=","posted"],["move_id.move_type","in",["out_invoice","out_refund"]],["display_type","=","product"]]' -Fields product_id
$lines = $linesJson | ConvertFrom-Json
$prodIds = $lines | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] } | Select-Object -Unique
$domain = '[["id","in",[' + ($prodIds -join ',') + ']]]'
$prodsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain $domain -Fields id,name,default_code,categ_id
$prods = $prodsJson | ConvertFrom-Json
$noCat = $prods | Where-Object { -not $_.categ_id }
Write-Output "Total distinct products in August 2026 invoices: $($prods.Count)"
Write-Output "Products without category: $($noCat.Count)"
$noCat | ForEach-Object { Write-Output " - ID: $($_.id) | Code: $($_.default_code) | Name: $($_.name)" }
