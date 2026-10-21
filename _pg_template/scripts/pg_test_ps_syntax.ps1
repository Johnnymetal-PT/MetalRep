<#
.SYNOPSIS
  Valida a sintaxe de TODOS os scripts PowerShell do repositorio.

.DESCRIPTION
  Porque existe: a 2026-09-11 uma edicao ao pg_odoo_client_query.ps1 introduziu um
  escape invalido (`\"` onde o PowerShell quer `` ` ``) e NADA no repositorio o teria
  apanhado. O ficheiro so falharia quando alguem o corresse -- tipicamente num projeto
  de cliente, a meio de trabalho, com o erro a apontar para um parentesis em falta
  cinco funcoes acima do problema real.

  Dos 46 scripts .ps1 do repositorio, a maioria nao tem teste de comportamento. Este
  nao substitui esses testes: um script pode ter sintaxe perfeita e estar errado. Mas
  cobre os 46 de uma vez contra a classe de erro que parte o ficheiro INTEIRO, e corre
  em segundos.

  Usa o mesmo parser que o PowerShell usa para executar
  (System.Management.Automation.Language.Parser), por isso nao ha divergencia entre o
  que isto aceita e o que a maquina aceita.

.PARAMETER Scripts
  Validar apenas os scripts cujo nome contenha este texto.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_test_ps_syntax.ps1
#>
param(
  [string]$Scripts
)

$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent $PSScriptRoot

$ficheiros = @(
  Get-ChildItem -Path $raiz -Filter '*.ps1' -File -Recurse |
    Where-Object { $_.FullName -notmatch '\\(vendor|node_modules|\.git)\\' } |
    Sort-Object FullName
)

if ($Scripts) {
  $ficheiros = @($ficheiros | Where-Object { $_.Name -like "*$Scripts*" })
  if ($ficheiros.Count -eq 0) {
    # Um pedido explicito que nao resolve nada e erro, nao silencio.
    Write-Host "ERRO: nenhum script corresponde a '$Scripts'"
    exit 1
  }
}

if ($ficheiros.Count -eq 0) {
  Write-Host "AVISO: nao ha scripts .ps1 em $raiz"
  exit 0
}

Write-Host "=== pg_test_ps_syntax ==="
Write-Host ("  scripts : {0}" -f $ficheiros.Count)
Write-Host ""

$comErro = New-Object System.Collections.Generic.List[string]

foreach ($f in $ficheiros) {
  $erros = $null
  $null = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$null, [ref]$erros)

  $relativo = $f.FullName.Substring($raiz.Length).TrimStart('\')

  if ($erros -and $erros.Count -gt 0) {
    $comErro.Add($relativo)
    Write-Host ("  FALHA {0}" -f $relativo)
    # Ate tres erros: o primeiro e quase sempre o real, os seguintes sao arrasto.
    foreach ($e in ($erros | Select-Object -First 3)) {
      Write-Host ("        linha {0}: {1}" -f $e.Extent.StartLineNumber, $e.Message)
    }
  }
}

Write-Host ""
if ($comErro.Count -gt 0) {
  Write-Host ("FALHOU: {0} de {1} script(s) com erro de sintaxe" -f $comErro.Count, $ficheiros.Count)
  exit 1
}

Write-Host ("OK: {0} script(s) com sintaxe valida." -f $ficheiros.Count)
exit 0
