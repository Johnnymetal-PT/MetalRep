$allNoCatJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.template -Method search_read -Domain '[["categ_id","=",false]]' -Fields id,name,default_code,type
$allNoCat = $allNoCatJson | ConvertFrom-Json
Write-Output "Total product templates without category: $($allNoCat.Count)"
$allNoCat | ForEach-Object { Write-Output " - ID: $($_.id) | Ref: $($_.default_code) | Name: $($_.name)" }
