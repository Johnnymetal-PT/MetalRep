$ErrorActionPreference = 'Stop'
$repoPath = 'C:\Users\Utilizador\Desktop\Repos\Chapatim'
$queryScript = Join-Path $repoPath '.pg_framework\scripts\pg_odoo_client_query.ps1'

function Invoke-Query([string]$Model, [string]$Method, [string]$ArgumentsJson) {
    & $queryScript -ProjectKey 'odoo-chapatim' -Purpose 'production' -Model $Model -Method $Method -ArgsJson $ArgumentsJson
    if ($LASTEXITCODE -ne 0) { throw "$Model.$Method failed" }
}

Write-Output 'MODEL'
Invoke-Query 'ir.model' 'search_read' '[[["model","=","product.template"]],["id","model","name"]]'
Write-Output 'MANUAL_FIELDS'
Invoke-Query 'ir.model.fields' 'search_read' '[[["model","=","product.template"],["state","=","manual"]],["id","name","field_description","ttype","state"]]'
Write-Output 'FORM_VIEWS'
Invoke-Query 'ir.ui.view' 'search_read' '[[["model","=","product.template"],["type","=","form"]],["id","name","key","inherit_id","priority","active"]]'
Write-Output 'CUSTOM_WEBSITE_VIEW'
Invoke-Query 'ir.ui.view' 'search_read' '[[["id","=",5892]],["id","name","key","arch_db","website_id","active"]]'
Write-Output 'WEBSITE_PRODUCT_FORM'
Invoke-Query 'ir.ui.view' 'search_read' '[[["id","=",2540]],["id","name","arch_db"]]'
Write-Output 'SPEC_VIEWS'
Invoke-Query 'ir.ui.view' 'search_read' '[[["key","in",["website_sale_comparison.product_attributes_body","pg_chapatim.remove_bottom_product_specifications"]]],["id","name","key","inherit_id","website_id","active","arch_db"]]'
