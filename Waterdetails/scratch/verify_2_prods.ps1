$prodsJson = & .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey odoo-waterdetails-virgin-details-lda -Purpose production -Model product.template -Method search_read -Domain '[["id","in",[11685,11686]]]' -Fields id,name,default_code,categ_id,type
$prods = $prodsJson | ConvertFrom-Json
$baseUrl = "https://virgin-details.odoo.com"
$prods | ForEach-Object {
    $cat = if ($_.categ_id) { $_.categ_id[1] } else { "--- SEM CATEGORIA ---" }
    Write-Output "ID: $($_.id) | Ref: $($_.default_code) | Categ: $cat | Nome: $($_.name) | URL: $baseUrl/web#id=$($_.id)&model=product.template"
}
