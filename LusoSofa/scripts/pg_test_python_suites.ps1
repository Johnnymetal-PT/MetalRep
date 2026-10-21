<#
.SYNOPSIS
  Corre todas as suites de testes Python de scripts/tests.

.DESCRIPTION
  Ate 2026-09-10 os testes Python do repositorio nao eram corridos por nada: existiam
  cinco ficheiros em scripts/tests e so um deles tinha invocador proprio
  (pg_test_mcp_query.ps1). Um teste que ninguem corre e documentacao, nao e rede -- e
  foi por isso que o guard de migracao pode ser alterado a vontade sem nada acusar.

  Cada suite corre em processo proprio (`python -m unittest scripts.tests.<modulo>`),
  a partir da raiz do repositorio, para que o import `from scripts import ...` resolva.
  Uma suite que falhe nao impede as restantes de correr: o objetivo e ver o estado
  todo de uma vez, nao parar na primeira.

.PARAMETER Suite
  Correr apenas as suites cujo nome contenha este texto.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_test_python_suites.ps1
#>
param(
  [string]$Suite
)

$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent $PSScriptRoot
$pastaTestes = Join-Path $raiz 'scripts\tests'

if (-not (Test-Path $pastaTestes)) {
  Write-Host "AVISO: nao ha pasta de testes em $pastaTestes"
  exit 0
}

$modulos = @(
  Get-ChildItem -Path $pastaTestes -Filter 'test_*.py' -File |
    Sort-Object Name |
    ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) }
)

if ($Suite) {
  $modulos = @($modulos | Where-Object { $_ -like "*$Suite*" })
}

if ($modulos.Count -eq 0) {
  # Um pedido explicito que nao resolve nada e erro, nao silencio -- a mesma licao do
  # -RepoNames em pg_align_fleet_framework.ps1.
  if ($Suite) {
    Write-Host "ERRO: nenhuma suite corresponde a '$Suite' em $pastaTestes"
    exit 1
  }
  Write-Host "AVISO: nao ha suites de teste em $pastaTestes"
  exit 0
}

$python = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }

Write-Host "=== pg_test_python_suites ==="
Write-Host ("  interpretador : {0}" -f $python)
Write-Host ("  suites        : {0}" -f $modulos.Count)
Write-Host ""

$falhadas = New-Object System.Collections.Generic.List[string]
$totalTestes = 0

foreach ($modulo in $modulos) {
  # ErrorActionPreference isolado: em Windows PowerShell 5.1 o stderr de um executavel
  # nativo vem embrulhado em ErrorRecord e, com Stop, abortaria o runner -- e o unittest
  # escreve TODO o seu relatorio no stderr, mesmo quando passa.
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    Push-Location $raiz
    $saida = & $python -m unittest "scripts.tests.$modulo" 2>&1
    $codigo = $LASTEXITCODE
  }
  finally {
    Pop-Location
    $ErrorActionPreference = $anterior
  }

  $texto = ($saida | ForEach-Object { "$_" }) -join "`n"
  $quantos = 0
  if ($texto -match 'Ran (\d+) test') { $quantos = [int]$Matches[1] }
  $totalTestes += $quantos

  if ($codigo -eq 0) {
    Write-Host ("  OK    {0,-42} {1} teste(s)" -f $modulo, $quantos)
  }
  else {
    $falhadas.Add($modulo)
    Write-Host ("  FALHA {0,-42} {1} teste(s)" -f $modulo, $quantos)
    foreach ($linha in ($texto -split "`n" | Where-Object { $_ -match '^(FAIL|ERROR|AssertionError|\s+File )' } | Select-Object -First 8)) {
      Write-Host ("        {0}" -f $linha.TrimEnd())
    }
  }
}

Write-Host ""
if ($falhadas.Count -gt 0) {
  Write-Host ("FALHOU: {0} de {1} suite(s) com erros ({2} testes corridos)" -f $falhadas.Count, $modulos.Count, $totalTestes)
  Write-Host ("        {0}" -f ($falhadas -join ', '))
  exit 1
}

Write-Host ("OK: {0} suite(s) e {1} testes passaram." -f $modulos.Count, $totalTestes)
exit 0
