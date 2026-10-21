<#
.SYNOPSIS
  Testes do validador de acentuacao de portugues europeu.

.DESCRIPTION
  Cobre o comportamento que ja falhou em producao:

  1. o filtro -Include ser efectivo em scans de pasta. Com -LiteralPath e
     -Recurse o PowerShell ignora silenciosamente o -Include e devolve TODOS os
     ficheiros; um scan com o default '*.md' apanhava .py e .docx;
  2. ficheiros binarios serem ignorados mesmo quando passados explicitamente
     (um .docx e um ZIP: lido como texto produz achados de bytes comprimidos);
  3. o mapa nao ter chaves duplicadas;
  4. um conjunto de palavras do mapa ser efectivamente detetado e corrigido.

  Sem dependencias externas. Cria e limpa a sua propria pasta temporaria.

.EXAMPLE
  pwsh ./scripts/pg_test_pt_accents.ps1
#>
param(
  [switch]$KeepTempDir
)

$ErrorActionPreference = 'Stop'

$validator = Join-Path $PSScriptRoot 'pg_validate_pt_accents.ps1'
$mapPath = Join-Path $PSScriptRoot 'pg_pt_accent_map.tsv'

if (-not (Test-Path $validator)) { throw "Validador nao encontrado: $validator" }
if (-not (Test-Path $mapPath)) { throw "Mapa nao encontrado: $mapPath" }

$failures = New-Object System.Collections.ArrayList

function Assert-PgTest {
  param([string]$Name, [bool]$Condition, [string]$Detail = '')
  if ($Condition) {
    Write-Host "  OK   $Name"
  }
  else {
    Write-Host "  FAIL $Name$(if ($Detail) { " - $Detail" })"
    [void]$failures.Add($Name)
  }
}

function Invoke-Validator {
  param([string[]]$Arguments)
  $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $validator @Arguments 2>&1
  return [pscustomobject]@{
    ExitCode = $LASTEXITCODE
    Text     = ($output | Out-String)
  }
}

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_test_accents_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $temp -Force | Out-Null

try {
  Write-Host "=== pg_test_pt_accents ($temp) ==="
  Write-Host ""

  # ------------------------------------------------------------------
  # 1. -Include efectivo em scan de pasta
  # ------------------------------------------------------------------
  Write-Host "1. filtro -Include em scan de pasta"

  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Join-Path $temp 'doc.md'), "Uma decisao por validar.`n", $encoding)
  [System.IO.File]::WriteAllText((Join-Path $temp 'codigo.py'), "# uma decisao no comentario`n", $encoding)

  $result = Invoke-Validator -Arguments @('-Path', $temp, '-WarningsOnly')
  Assert-PgTest -Name "scan de pasta analisa o .md" -Condition ($result.Text -match 'doc\.md')
  Assert-PgTest -Name "scan de pasta NAO analisa o .py com o default '*.md'" `
    -Condition (-not ($result.Text -match 'codigo\.py')) `
    -Detail 'o -Include foi ignorado (regressao do bug -LiteralPath + -Recurse)'

  $result = Invoke-Validator -Arguments @('-Path', $temp, '-Include', '*.md,*.py', '-WarningsOnly')
  Assert-PgTest -Name "-Include explicito com dois padroes apanha ambos" `
    -Condition (($result.Text -match 'doc\.md') -and ($result.Text -match 'codigo\.py'))

  # ------------------------------------------------------------------
  # 2. binarios ignorados mesmo quando explicitos
  # ------------------------------------------------------------------
  Write-Host ""
  Write-Host "2. ficheiros binarios"

  # .docx minimo: um ZIP e suficiente para reproduzir o problema
  $docx = Join-Path $temp 'artefacto.docx'
  $zipSource = Join-Path $temp 'zipsrc'
  New-Item -ItemType Directory -Path $zipSource -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $zipSource 'conteudo.xml'), '<a>So Ja sO texto</a>', $encoding)
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::CreateFromDirectory($zipSource, $docx)

  $result = Invoke-Validator -Arguments @('-Path', $docx, '-WarningsOnly')
  Assert-PgTest -Name ".docx explicito e ignorado" `
    -Condition ($result.Text -match 'binario') `
    -Detail 'um .docx lido como texto gera achados falsos'
  Assert-PgTest -Name ".docx explicito nao produz achados" `
    -Condition (-not ($result.Text -match '  ERRO  '))

  # ------------------------------------------------------------------
  # 3. mapa sem chaves duplicadas
  # ------------------------------------------------------------------
  Write-Host ""
  Write-Host "3. integridade do mapa"

  $entries = @(Get-Content -LiteralPath $mapPath -Encoding UTF8 |
      Where-Object { $_ -and -not $_.StartsWith('#') })
  $keys = @($entries | ForEach-Object { ($_ -split '\s+', 2)[0] })
  $duplicates = @($keys | Group-Object | Where-Object { $_.Count -gt 1 })
  Assert-PgTest -Name "mapa sem chaves duplicadas" -Condition ($duplicates.Count -eq 0) `
    -Detail (($duplicates | ForEach-Object { $_.Name }) -join ', ')

  $malformed = @($entries | Where-Object { (($_ -split '\s+', 2).Count -ne 2) })
  Assert-PgTest -Name "todas as linhas do mapa tem par ascii/acentuado" -Condition ($malformed.Count -eq 0)

  $notAscii = @($keys | Where-Object { $_ -match '[^\x00-\x7F]' })
  Assert-PgTest -Name "chaves do mapa sao ASCII puro" -Condition ($notAscii.Count -eq 0) `
    -Detail ($notAscii -join ', ')

  # ------------------------------------------------------------------
  # 4. deteccao e correccao efectivas
  # ------------------------------------------------------------------
  Write-Host ""
  Write-Host "4. deteccao e -Fix"

  $sample = Join-Path $temp 'amostra.md'
  $ascii = "O guiao tem um paragrafo com cabecalho, titulos e uma citacao a mao. As secoes ficam visiveis no rodape."
  [System.IO.File]::WriteAllText($sample, $ascii + "`n", $encoding)

  $result = Invoke-Validator -Arguments @('-Path', $sample)
  Assert-PgTest -Name "deteccao falha o gate (exit 1)" -Condition ($result.ExitCode -eq 1)
  foreach ($word in @('guiao', 'paragrafo', 'cabecalho', 'titulos', 'citacao', 'mao', 'secoes', 'visiveis', 'rodape')) {
    Assert-PgTest -Name "detecta '$word'" -Condition ($result.Text -match "'$word'")
  }

  $result = Invoke-Validator -Arguments @('-Path', $sample, '-Fix')
  $fixed = [System.IO.File]::ReadAllText($sample)
  Assert-PgTest -Name "-Fix acentua o texto" `
    -Condition ($fixed -match 'gui' + [char]0x00E3 + 'o' -and $fixed -match 'par' + [char]0x00E1 + 'grafo')
  Assert-PgTest -Name "-Fix deixa o ficheiro limpo" `
    -Condition ((Invoke-Validator -Arguments @('-Path', $sample)).ExitCode -eq 0)

  Write-Host ""
  if ($failures.Count -gt 0) {
    Write-Host ("FALHOU: {0} teste(s) - {1}" -f $failures.Count, ($failures -join '; '))
    exit 1
  }
  Write-Host 'OK: todos os testes passaram.'
  exit 0
}
finally {
  if (-not $KeepTempDir -and (Test-Path $temp)) {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
