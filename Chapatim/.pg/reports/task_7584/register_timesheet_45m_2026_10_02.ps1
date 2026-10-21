$ErrorActionPreference = 'Stop'

$repoPath = 'C:\Users\Utilizador\Desktop\Repos\Chapatim'
$queryScript = Join-Path $repoPath '.pg_framework\scripts\pg_odoo_query.ps1'

function Invoke-PgOdoo {
    param([string]$Model, [string]$Method, [string]$ArgumentsJson)
    $raw = & $queryScript -Model $Model -Method $Method -ArgsJson $ArgumentsJson
    if ($LASTEXITCODE -ne 0) { throw "$Model.$Method failed" }
    return ($raw | Out-String).Trim()
}

function Convert-ResultArray([string]$Raw) {
    $parsed = $Raw | ConvertFrom-Json
    return @($parsed | ForEach-Object { $_ })
}

$taskRows = @(Convert-ResultArray (Invoke-PgOdoo -Model 'project.task' -Method 'read' -ArgumentsJson '[[7584],["id","name","project_id"]]'))
if ($taskRows.Count -ne 1) { throw 'Task 7584 was not found.' }
$task = $taskRows[0]

# Reuse the employee and analytic account from the last confirmed entry made for this user on this task.
$referenceRows = @(Convert-ResultArray (Invoke-PgOdoo -Model 'account.analytic.line' -Method 'read' -ArgumentsJson '[[44041],["id","employee_id","user_id","project_id","task_id","account_id","company_id"]]'))
if ($referenceRows.Count -ne 1 -or [int]$referenceRows[0].task_id[0] -ne 7584) {
    throw 'Reference timesheet 44041 is missing or no longer belongs to task 7584.'
}
$reference = $referenceRows[0]

$description = '"Afina\u00e7\u00f5es finais do website Chapatim: remo\u00e7\u00e3o de especifica\u00e7\u00f5es e separadores redundantes na p\u00e1gina de produto, ajuste do bot\u00e3o Adicionar ao carrinho, alinhamento responsivo dos mega menus com o cabe\u00e7alho e auditoria mobile integral do website (137 URLs), com identifica\u00e7\u00e3o de overflow na loja e categorias e de rotas inv\u00e1lidas."' | ConvertFrom-Json
$descriptionJson = ConvertTo-Json -InputObject $description -Compress
$employeeId = [int]$reference.employee_id[0]
$domainJson = '[[["task_id","=",7584],["employee_id","=",' + $employeeId + '],["date","=","2026-10-02"],["name","=",' + $descriptionJson + ']],["id","unit_amount","employee_id","date","name"]]'
$existingRows = @(Convert-ResultArray (Invoke-PgOdoo -Model 'account.analytic.line' -Method 'search_read' -ArgumentsJson $domainJson))

if ($existingRows.Count -gt 0 -and $existingRows[0] -and [int]$existingRows[0].id -gt 0) {
    $lineId = [int]$existingRows[0].id
}
else {
    $values = [ordered]@{
        name = $description
        date = '2026-10-02'
        unit_amount = 0.75
        task_id = 7584
        project_id = [int]$reference.project_id[0]
        employee_id = $employeeId
        account_id = [int]$reference.account_id[0]
        company_id = [int]$reference.company_id[0]
    }
    if ($reference.user_id) { $values.user_id = [int]$reference.user_id[0] }
    $valuesJson = ConvertTo-Json -InputObject $values -Depth 20 -Compress
    $lineId = [int](Invoke-PgOdoo -Model 'account.analytic.line' -Method 'create' -ArgumentsJson ('[' + $valuesJson + ']'))
}

$checkRows = @(Convert-ResultArray (Invoke-PgOdoo -Model 'account.analytic.line' -Method 'read' -ArgumentsJson ('[[' + $lineId + '],["id","name","date","unit_amount","employee_id","project_id","task_id"]]')))
if ($checkRows.Count -ne 1 -or [double]$checkRows[0].unit_amount -ne 0.75 -or [int]$checkRows[0].task_id[0] -ne 7584) {
    throw ('Timesheet validation failed: ' + (ConvertTo-Json -InputObject $checkRows -Depth 10 -Compress))
}

$check = $checkRows[0]
Write-Output (ConvertTo-Json -InputObject ([ordered]@{
    id = [int]$check.id
    task = [string]$task.name
    employee = [string]$check.employee_id[1]
    date = [string]$check.date
    hours = [double]$check.unit_amount
    description = [string]$check.name
}) -Depth 10)
