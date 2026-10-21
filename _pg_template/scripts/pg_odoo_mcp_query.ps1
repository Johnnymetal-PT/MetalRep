<#
.SYNOPSIS
  Consulta uniforme ao Odoo via protocolo nativo MCP (Model Context Protocol).
  Suporta Odoo 19+ / SaaS 19.4+ (endpoint POST /mcp com Authorization Bearer).

.DESCRIPTION
  Wrapper PowerShell para `scripts/pg_odoo_mcp_query.py`.
  Permite executar `search`, `read_group`, `get_fields`, `get_models`, `context`
  ou chamadas de ferramentas diretamente contra qualquer instancia Odoo com suporte MCP.

.PARAMETER BaseUrl
  URL base da instancia (ex.: 'https://urbansofa.odoo.com' ou 'https://urbansofa.odoo.com/mcp').

.PARAMETER ApiKey
  Chave de API / Bearer Token para o endpoint MCP.

.PARAMETER Action
  Acao a executar: 'search', 'read_group', 'get_fields', 'get_models', 'context', 'list_tools', 'call_tool', 'ping'. Default: 'search'.

.PARAMETER Model
  Modelo Odoo (ex.: 'crm.lead', 'res.partner'). Obrigatorio para 'search', 'read_group', 'get_fields'.

.PARAMETER Domain
  Dominio de pesquisa em JSON (ex.: '[["stage_id","=",1]]'). Default: '[]'.

.PARAMETER Fields
  Campos a devolver (array de strings ou string separada por virgulas).

.PARAMETER Limit
  Limite maximo de registos.

.PARAMETER Order
  Ordenacao dos registos (ex.: 'id desc').

.PARAMETER GroupBy
  Campos de agrupamento para read_group.

.PARAMETER Aggregates
  Agregacoes para read_group (ex.: 'expected_revenue:sum').

.PARAMETER ToolName
  Nome da ferramenta para action='call_tool'.

.PARAMETER ToolArgs
  Argumentos em JSON para action='call_tool'.

.EXAMPLE
  pg_odoo_mcp_query.ps1 -BaseUrl https://urbansofa.odoo.com -ApiKey "..." -Model crm.lead -Fields name,stage_id -Limit 5

.EXAMPLE
  pg_odoo_mcp_query.ps1 -BaseUrl https://urbansofa.odoo.com -ApiKey "..." -Action context
#>
param(
  [Parameter(Mandatory = $true)][string]$BaseUrl,
  [Parameter(Mandatory = $true)][string]$ApiKey,
  [ValidateSet('search', 'read_group', 'get_fields', 'get_models', 'context', 'list_tools', 'call_tool', 'ping')][string]$Action = 'search',
  [string]$Model,
  [string]$Domain = '[]',
  [string[]]$Fields,
  [int]$Limit = 0,
  [int]$Offset = 0,
  [string]$Order,
  [string[]]$GroupBy,
  [string[]]$Aggregates,
  [string]$Having,
  [string]$ToolName,
  [string]$ToolArgs = '{}',
  [int]$Timeout = 30
)

$ErrorActionPreference = 'Stop'

$pyScript = Join-Path $PSScriptRoot 'pg_odoo_mcp_query.py'
if (-not (Test-Path $pyScript)) {
  throw "Script Python nao encontrado em '$pyScript'."
}

# Normalizar arrays passados via powershell -File
if ($Fields) { $Fields = @($Fields | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
if ($GroupBy) { $GroupBy = @($GroupBy | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
if ($Aggregates) { $Aggregates = @($Aggregates | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }

$pyArgs = @($pyScript, '--url', $BaseUrl, '--key', $ApiKey, '--action', $Action, '--timeout', [string]$Timeout)

if ($Model) { $pyArgs += @('--model', $Model) }
if ($Domain) { $pyArgs += @('--domain', $Domain) }
if ($Fields -and $Fields.Count -gt 0) { $pyArgs += @('--fields', ($Fields -join ',')) }
if ($Limit -gt 0) { $pyArgs += @('--limit', [string]$Limit) }
if ($Offset -gt 0) { $pyArgs += @('--offset', [string]$Offset) }
if ($Order) { $pyArgs += @('--order', $Order) }
if ($GroupBy -and $GroupBy.Count -gt 0) { $pyArgs += @('--groupby', ($GroupBy -join ',')) }
if ($Aggregates -and $Aggregates.Count -gt 0) { $pyArgs += @('--aggregates', ($Aggregates -join ',')) }
if ($Having) { $pyArgs += @('--having', $Having) }
if ($ToolName) { $pyArgs += @('--tool-name', $ToolName) }
if ($ToolArgs -and $ToolArgs -ne '{}') { $pyArgs += @('--tool-args', $ToolArgs) }

# Localizar executavel python
$pythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { throw "Python nao encontrado no PATH." }

$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName = $pythonExe
$pinfo.Arguments = ($pyArgs | ForEach-Object {
    if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
}) -join ' '
$pinfo.UseShellExecute = $false
$pinfo.RedirectStandardOutput = $true
$pinfo.RedirectStandardError = $true
$pinfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$pinfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8

$process = [System.Diagnostics.Process]::Start($pinfo)
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()

if ($process.ExitCode -ne 0) {
  $errMsg = if ($stderr) { $stderr.Trim() } else { "Processo Python terminou com codigo $($process.ExitCode)" }
  throw $errMsg
}

if ($stdout) {
  Write-Output $stdout.Trim()
}
exit 0
