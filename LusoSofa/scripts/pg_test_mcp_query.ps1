<#
.SYNOPSIS
  Executa a suite de testes unitarios e integrados para o suporte MCP do _pg_template.
#>
$ErrorActionPreference = 'Stop'

Write-Host "==> A executar testes unitarios Python para pg_odoo_mcp_query..." -ForegroundColor Cyan

$pyExe = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
& $pyExe -m unittest scripts.tests.test_pg_odoo_mcp_query -v

if ($LASTEXITCODE -ne 0) {
  Write-Error "Testes unitarios Python falharam."
  exit 1
}

Write-Host "==> Testes unitarios concluidos com sucesso!" -ForegroundColor Green
exit 0
