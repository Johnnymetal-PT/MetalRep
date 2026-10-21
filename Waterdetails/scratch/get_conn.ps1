$c = & .pg_framework\scripts\pg_odoo_query.ps1 -Model pg.odoo.connection -Domain '[["project_key","=","odoo-waterdetails-virgin-details-lda"]]' -Fields project_key,purpose,base_url,database
$conn = $c | ConvertFrom-Json
$conn | ForEach-Object { Write-Output "Purpose: $($_.purpose) | URL: $($_.base_url) | DB: $($_.database)" }
