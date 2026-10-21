param(
  [string]$RepoPath = "",
  [string]$TemplatesDir = "doc_templates",
  [string]$Pattern = "TPL_*.md"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
  $RepoPath = Split-Path -Parent $PSScriptRoot
}

$targetDir = Join-Path $RepoPath $TemplatesDir
if (-not (Test-Path -LiteralPath $targetDir)) {
  throw "Diretorio de templates nao encontrado: $targetDir"
}

$patterns = @(
  "\u00C3[\u0080-\u00BF]",
  "\u00E2[\u0080-\u00BF]{1,2}"
)

$files = Get-ChildItem -LiteralPath $targetDir -File -Filter $Pattern | Sort-Object Name
if (-not $files) {
  Write-Host "Nenhum ficheiro encontrado em $targetDir com filtro $Pattern"
  exit 0
}

$hits = @()
foreach ($file in $files) {
  $lineNo = 0
  foreach ($line in [System.IO.File]::ReadLines($file.FullName, [System.Text.Encoding]::UTF8)) {
    $lineNo++
    foreach ($pattern in $patterns) {
      if ([regex]::IsMatch($line, $pattern)) {
        $hits += [pscustomobject]@{
          File    = $file.Name
          Line    = $lineNo
          Marker  = $pattern
          Content = $line
        }
      }
    }
  }
}

if (-not $hits) {
  Write-Host "OK: nenhum marcador suspeito de encoding encontrado."
  exit 0
}

Write-Host ("Foram encontrados {0} registos suspeitos." -f $hits.Count)
$hits |
  Sort-Object File, Line, Marker |
  Format-Table -AutoSize File, Line, Marker, Content

exit 1
