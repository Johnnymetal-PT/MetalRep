$pg = Get-Content -Path .pg_framework\credentials\brodoo_credentials.json -Raw | ConvertFrom-Json
$body = @{ jsonrpc = '2.0'; method = 'call'; params = @{ service = 'common'; method = 'authenticate'; args = @($pg.db, $pg.login, $pg.api_key, @{}) } } | ConvertTo-Json -Compress
$resp = Invoke-RestMethod -Method Post -Uri (($pg.url.TrimEnd('/')) + '/jsonrpc') -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$uid = [int]$resp.result

$body2 = @{ jsonrpc = '2.0'; method = 'call'; params = @{ service = 'object'; method = 'execute_kw'; args = @($pg.db, $uid, $pg.api_key, 'project.project', 'search_read', @(@(@('pg_project_key','=','odoo-waterdetails-virgin-details-lda'))), @{ fields = @('pg_repository_id'); limit = 1 }) } } | ConvertTo-Json -Depth 5 -Compress
$resp2 = Invoke-RestMethod -Method Post -Uri (($pg.url.TrimEnd('/')) + '/jsonrpc') -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body2))
$repoId = $resp2.result[0].pg_repository_id[0]

$body3 = @{ jsonrpc = '2.0'; method = 'call'; params = @{ service = 'object'; method = 'execute_kw'; args = @($pg.db, $uid, $pg.api_key, 'pg.odoo.connection', 'search_read', @(@(@('repository_id','=',$repoId), @('purpose','=','production'), @('active','=', $true))), @{ fields = @('base_url','database'); limit = 1 }) } } | ConvertTo-Json -Depth 5 -Compress
$resp3 = Invoke-RestMethod -Method Post -Uri (($pg.url.TrimEnd('/')) + '/jsonrpc') -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body3))
$baseUrl = $resp3.result[0].base_url
Write-Output "Client Base URL: $baseUrl"
