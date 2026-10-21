$catsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.category -Method search_read -Domain '[]' -Fields id,name,complete_name,parent_id
$cats = $catsJson | ConvertFrom-Json
$cats | ForEach-Object { Write-Output "Cat ID: $($_.id) | Name: '$($_.name)' | Complete: '$($_.complete_name)'" }
