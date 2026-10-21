# 1. Todas as linhas de fatura (vendas e compras) ou movimentos com produto em Agosto
$allLinesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model account.move.line -Method search_read -Domain '[["company_id","=",1],["date",">=","2026-08-01"],["date","<=","2026-08-31"],["product_id","!=",false]]' -Fields product_id,move_id,move_type
$allLines = $allLinesJson | ConvertFrom-Json
$allLineProdIds = $allLines | ForEach-Object { $_.product_id[0] } | Select-Object -Unique

# 2. Produtos com write_date ou create_date em Agosto
$modProdsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain '["|",["write_date",">=","2026-08-01"],["create_date",">=","2026-08-01"]]' -Fields id,name,default_code,categ_id,product_tmpl_id
$modProds = $modProdsJson | ConvertFrom-Json

$allCandidateIds = @($allLineProdIds + ($modProds | ForEach-Object { $_.id })) | Select-Object -Unique

$allCandidatesJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.product -Method search_read -Domain ('[["id","in",[' + ($allCandidateIds -join ',') + ']]]') -Fields id,name,default_code,categ_id,product_tmpl_id
$allCandidates = $allCandidatesJson | ConvertFrom-Json

Write-Output "Total candidatos: $($allCandidates.Count)"
$noCat = $allCandidates | Where-Object { -not $_.categ_id }
Write-Output "Total sem categoria entre candidatos: $($noCat.Count)"
$noCat | ForEach-Object {
    $tmplId = if ($_.product_tmpl_id) { $_.product_tmpl_id[0] } else { $_.id }
    Write-Output " - ID Prod: $($_.id) | ID Tmpl: $tmplId | Ref: $($_.default_code) | Nome: $($_.name)"
}
