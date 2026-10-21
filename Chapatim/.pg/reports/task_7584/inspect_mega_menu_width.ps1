$ErrorActionPreference = 'Stop'
$repoPath = 'C:\Users\Utilizador\Desktop\Repos\Chapatim'
$queryScript = Join-Path $repoPath '.pg_framework\scripts\pg_odoo_client_query.ps1'
& $queryScript `
    -ProjectKey 'odoo-chapatim' `
    -Purpose 'production' `
    -Model 'ir.ui.view' `
    -Method 'read' `
    -ArgsJson '[[5909],["id","name","key","active","website_id","arch_db"]]'
if ($LASTEXITCODE -ne 0) { throw 'Could not read mega-menu width view 5909.' }
