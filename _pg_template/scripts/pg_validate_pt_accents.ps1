<#
.SYNOPSIS
  Valida acentuacao de portugues europeu em documentos gerados, detetando
  texto escrito em portugues-ASCII (sem acentos).

.DESCRIPTION
  Apoia a regra "Regras de redacao em portugues europeu" de
  templates/AGENTS_SHARED.md, verificada no PG_PRE_RESPONSE_CHECKLIST.md.

  - Achados de confianca alta (palavra no mapa ineqivoco) => ERRO; fazem o
    script terminar com exit code 1 (gate para CI / pre-commit).
  - Achados heuristicos (sufixos -cao/-coes/-ncia/-avel/-ivel nao verificados)
    => apenas WARN; nunca alteram o exit code nem sao corrigidos.

  Cobre apenas perda de acentos na redacao. Mojibake/encoding tem o seu proprio
  caminho em pg_smoke_test_repo.ps1 (Test-TextEncodingNoise).

  Ficheiros binarios (.docx, .xlsx, .pdf, imagens, ...) sao sempre ignorados,
  mesmo quando passados explicitamente: analisa-los produz achados falsos vindos
  de bytes comprimidos.

.PARAMETER Path
  Um ou mais ficheiros ou diretorios a analisar. Diretorios sao percorridos
  recursivamente por *.md por defeito (ver -Include).

.PARAMETER Include
  Padroes de ficheiro a incluir quando -Path e um diretorio. Default: *.md.
  Aceita varios padroes, separados por virgula: -Include '*.md,*.ps1'.

.PARAMETER Fix
  Aplica as correcoes de confianca alta (apenas as do mapa ineqivoco) e
  reescreve os ficheiros em UTF-8 sem BOM. Achados heuristicos nunca sao tocados.

  Em ficheiros que nao sao de prosa (.md/.txt/.rst/.adoc) o script avisa: a regra
  de redacao cobre comentarios e docstrings, mas uma palavra do mapa pode coincidir
  com um identificador do codigo. Revisar o diff nesses casos.

.PARAMETER WarningsOnly
  Nao falha (exit 0) mesmo com achados de confianca alta; util para inventario.

.EXAMPLE
  pwsh ./scripts/pg_validate_pt_accents.ps1 -Path ./out/parecer.md

.EXAMPLE
  pwsh ./scripts/pg_validate_pt_accents.ps1 -Path ./docs -Fix
#>
param(
  [Parameter(Mandatory = $true)]
  [string[]]$Path,

  [string[]]$Include = @('*.md'),

  [switch]$Fix,

  [switch]$WarningsOnly
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')

# Normalizar -Include: invocado via 'powershell -File', um "*.md,*.ps1" chega como
# um unico elemento do array e nunca corresponde a nada. Mesma convencao do
# -Fields em pg_odoo_query.ps1. O ritual manda invocar sempre com -File, pelo que
# esta normalizacao e o caso normal, nao a excepcao.
if ($Include) {
  $Include = @($Include |
      ForEach-Object { $_ -split ',' } |
      ForEach-Object { $_.Trim() } |
      Where-Object { $_ })
}
if (-not $Include -or $Include.Count -eq 0) {
  $Include = @('*.md')
}

# Extensoes que nunca sao texto: .docx/.xlsx/.pptx sao ZIP, os restantes binarios.
# Analisa-los produz achados falsos vindos de bytes comprimidos (ja aconteceu:
# 24 achados 'So'/'Ja'/'sO' saidos de dois .docx). Sao ignorados mesmo quando o
# caminho e passado explicitamente.
$script:PgAccentBinaryExtensions = @(
  '.docx', '.docm', '.dotx', '.doc',
  '.xlsx', '.xlsm', '.xltx', '.xls',
  '.pptx', '.potx', '.ppt',
  '.odt', '.ods', '.odp',
  '.pdf', '.zip', '.7z', '.gz', '.tar',
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svgz',
  '.mp3', '.mp4', '.avi', '.mov',
  '.ttf', '.otf', '.woff', '.woff2',
  '.exe', '.dll', '.pyc', '.pyd', '.so', '.bin'
)

# Extensoes onde -Fix e seguro sem reservas: texto de prosa. Fora destas (codigo,
# por exemplo) a regra de redacao continua a aplicar-se a comentarios e docstrings,
# mas uma palavra do mapa pode coincidir com um identificador (uma variavel
# chamada 'titulo' viraria 'titulo' acentuado e partiria o codigo). Nesses casos
# o script avisa em vez de bloquear: quem corre decide.
$script:PgAccentProseExtensions = @('.md', '.markdown', '.txt', '.rst', '.adoc')

function Test-PgAccentBinaryFile {
  param([string]$FilePath)
  return ($script:PgAccentBinaryExtensions -contains ([System.IO.Path]::GetExtension($FilePath).ToLowerInvariant()))
}

function Resolve-PgTargetFiles {
  param([string[]]$InputPaths, [string[]]$IncludePatterns)

  $files = New-Object System.Collections.ArrayList
  $skippedBinary = New-Object System.Collections.ArrayList

  foreach ($inputPath in $InputPaths) {
    if (-not (Test-Path $inputPath)) {
      Write-Host "WARN: caminho inexistente ignorado: $inputPath"
      continue
    }

    $item = Get-Item -LiteralPath $inputPath
    if ($item.PSIsContainer) {
      # NAO usar -Include aqui: com -LiteralPath e -Recurse o PowerShell ignora
      # silenciosamente o -Include e devolve TODOS os ficheiros. Era assim que um
      # scan de pasta com o default '*.md' apanhava .py e .docx. Filtrar a mao.
      foreach ($child in (Get-ChildItem -LiteralPath $item.FullName -File -Recurse)) {
        foreach ($pattern in $IncludePatterns) {
          if ($child.Name -like $pattern) {
            [void]$files.Add($child.FullName)
            break
          }
        }
      }
    }
    else {
      [void]$files.Add($item.FullName)
    }
  }

  $kept = New-Object System.Collections.ArrayList
  foreach ($file in @($files | Select-Object -Unique)) {
    if (Test-PgAccentBinaryFile -FilePath $file) {
      [void]$skippedBinary.Add($file)
      continue
    }
    [void]$kept.Add($file)
  }

  if ($skippedBinary.Count -gt 0) {
    Write-Host ("WARN: {0} ficheiro(s) binario(s) ignorado(s) (nao sao texto): {1}" -f
      $skippedBinary.Count, (($skippedBinary | ForEach-Object { Split-Path -Leaf $_ }) -join ', '))
  }

  return @($kept)
}

$targets = Resolve-PgTargetFiles -InputPaths $Path -IncludePatterns $Include
if ($targets.Count -eq 0) {
  Write-Host 'OK: nenhum ficheiro elegivel para analise.'
  exit 0
}

$totalHigh = 0
$totalHeuristic = 0
$filesFixed = 0

foreach ($file in $targets) {
  $text = Read-Utf8TextFile -Path $file
  $result = Get-PgPortugueseAccentFindings -Text $text -ApplyFix:$Fix
  $findings = @($result.Findings)

  if ($findings.Count -eq 0) {
    continue
  }

  $high = @($findings | Where-Object { $_.Confidence -eq 'high' })
  $heuristic = @($findings | Where-Object { $_.Confidence -eq 'heuristic' })
  $totalHigh += $high.Count
  $totalHeuristic += $heuristic.Count

  Write-Host ""
  Write-Host "== $file =="

  foreach ($finding in ($high | Sort-Object LineNumber)) {
    Write-Host ("  ERRO  L{0}: '{1}' -> '{2}'" -f $finding.LineNumber, $finding.Word, $finding.Suggestion)
  }
  foreach ($finding in ($heuristic | Sort-Object LineNumber)) {
    Write-Host ("  WARN  L{0}: '{1}' tem terminacao tipica de palavra acentuada (verificar)" -f $finding.LineNumber, $finding.Word)
  }

  if ($Fix -and $high.Count -gt 0 -and $result.FixedText -ne $text) {
    $extension = ([System.IO.Path]::GetExtension($file)).ToLowerInvariant()
    if ($script:PgAccentProseExtensions -notcontains $extension) {
      Write-Host ("  WARN  '{0}' nao e ficheiro de prosa: confirmar que nenhuma correcao caiu num identificador (variavel/chave chamada como palavra do mapa)." -f $extension)
    }
    Write-Utf8NoBomFile -Path $file -Content $result.FixedText
    $filesFixed += 1
    Write-Host ("  FIX   {0} correcao(oes) de confianca alta aplicada(s)." -f $high.Count)
  }
}

Write-Host ""
Write-Host ("Resumo: {0} achado(s) de confianca alta, {1} aviso(s) heuristico(s) em {2} ficheiro(s) analisado(s)." -f $totalHigh, $totalHeuristic, $targets.Count)

if ($Fix) {
  Write-Host ("Ficheiros corrigidos: {0}." -f $filesFixed)
  Write-Host 'NOTA: avisos heuristicos NAO sao corrigidos automaticamente; rever a mao.'
}

if ($totalHigh -gt 0 -and -not $Fix -and -not $WarningsOnly) {
  Write-Host ""
  Write-Host "ERRO: validacao de acentuacao falhou: $totalHigh palavra(s) em portugues-ASCII detetada(s). Corrigir, ou correr com -Fix."
  exit 1
}

if ($totalHigh -eq 0 -and $totalHeuristic -eq 0) {
  Write-Host 'OK: nenhuma perda de acentuacao detetada.'
}

exit 0
