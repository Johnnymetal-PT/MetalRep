# Vendas (invoices)
$invLinesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model account.move.line -Method search_read -Domain '[["company_id","=",1],["move_id.invoice_date",">=","2026-08-01"],["move_id.invoice_date","<=","2026-08-31"],["move_id.state","=","posted"],["move_id.move_type","in",["out_invoice","out_refund"]],["display_type","=","product"]]' -Fields product_id
$invLines = $invLinesJson | ConvertFrom-Json
$invProdIds = $invLines | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] }

# Guias de transporte / Stock pickings em Agosto
$stockMovesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model stock.move -Method search_read -Domain '[["company_id","=",1],["date",">=","2026-08-01"],["date","<=","2026-08-31"],["state","=","done"]]' -Fields product_id
$stockMoves = if ($stockMovesJson) { $stockMovesJson | ConvertFrom-Json } else { @() }
$stockProdIds = $stockMoves | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] }

# Encomendas de venda em Agosto
$saleLinesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model sale.order.line -Method search_read -Domain '[["company_id","=",1],["order_id.date_order",">=","2026-08-01"],["order_id.date_order","<=","2026-08-31"],["order_id.state","in",["sale","done"]],["display_type","=",false]]' -Fields product_id
$saleLines = if ($saleLinesJson) { $saleLinesJson | ConvertFrom-Json } else { @() }
$saleProdIds = $saleLines | Where-Object { $_.product_id } | ForEach-Object { $_.product_id[0] }

$allUsedProdIds = @($invProdIds + $stockProdIds + $saleProdIds) | Select-Object -Unique

$usedProdsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain ('[["id","in",[' + ($allUsedProdIds -join ',') + ']]]') -Fields id,name,default_code,categ_id,product_tmpl_id
$usedProds = $usedProdsJson | ConvertFrom-Json

Write-Output "Total de produtos movimentados em Agosto (Faturas + Stock + Vendas): $($usedProds.Count)"
$noCat = $usedProds | Where-Object { -not $_.categ_id }
Write-Output "Produtos sem categoria ($($noCat.Count)):"
$noCat | ForEach-Object {
    $tmplId = if ($_.product_tmpl_id) { $_.product_tmpl_id[0] } else { $_.id }
    Write-Output " - ID Prod: $($_.id) | ID Tmpl: $tmplId | Ref: $($_.default_code) | Nome: $($_.name)"
}
