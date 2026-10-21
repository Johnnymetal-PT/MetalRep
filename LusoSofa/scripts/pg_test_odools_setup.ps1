param()

$ErrorActionPreference = 'Stop'
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testRoot = Join-Path $tempBase ("pg-odools-test-" + [guid]::NewGuid().ToString('N'))

function Assert-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { throw "ASSERT FAILED: $Message" }
}

try {
  New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $testRoot 'vendor\odoo_src\community\odoo\addons') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $testRoot 'vendor\odoo_src\community\addons') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $testRoot 'vendor\odoo_src\enterprise') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $testRoot 'pg_demo\models') -Force | Out-Null
  Set-Content -Path (Join-Path $testRoot 'PG_CONTEXT.md') -Value "Versao do Odoo: 19.0`n" -Encoding utf8
  Set-Content -Path (Join-Path $testRoot 'pg_demo\__manifest__.py') -Value "{'name': 'PG Demo'}`n" -Encoding utf8
  Set-Content -Path (Join-Path $testRoot 'pg_demo\models\demo.py') -Value "class Demo: pass`n" -Encoding utf8
  & git -C $testRoot init --quiet
  & git -C $testRoot config core.autocrlf false
  & git -C $testRoot add PG_CONTEXT.md pg_demo/__manifest__.py pg_demo/models/demo.py

  $setup = Join-Path $PSScriptRoot 'pg_setup_odools.ps1'
  $testBinary = (Get-Process -Id $PID).Path
  & $setup -RepoPath $testRoot -OdooLsBinary $testBinary | Out-Null
  $configPath = Join-Path $testRoot 'odools.toml'
  Assert-True (Test-Path $configPath) 'odools.toml deve ser criado'
  $config = Get-Content -Path $configPath -Raw
  Assert-True ($config -match 'name = "default"') 'perfil default deve ser gerado'
  Assert-True ($config -match 'vendor/odoo_src/community') 'community path deve ser gerado'
  Assert-True ($config -match 'vendor/odoo_src/enterprise') 'enterprise path deve ser gerado'
  Assert-True ($config -match 'addons_paths') 'addon roots devem ser gerados'
  Assert-True (Test-Path (Join-Path $testRoot '.pg\odools\setup.json')) 'estado local deve ser escrito'

  $before = (Get-FileHash $configPath -Algorithm SHA256).Hash
  & $setup -RepoPath $testRoot -OdooLsBinary $testBinary -CheckOnly | Out-Null
  $after = (Get-FileHash $configPath -Algorithm SHA256).Hash
  Assert-True ($before -eq $after) 'CheckOnly nao deve alterar a configuracao'
  Write-Host 'OK: testes pg_setup_odools passaram'
}
finally {
  $resolved = [System.IO.Path]::GetFullPath($testRoot)
  if ($resolved.StartsWith($tempBase, [System.StringComparison]::OrdinalIgnoreCase) -and (Split-Path -Leaf $resolved).StartsWith('pg-odools-test-')) {
    Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction SilentlyContinue
  }
}
