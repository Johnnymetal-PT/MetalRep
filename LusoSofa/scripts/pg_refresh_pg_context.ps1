param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  # Modo multi-projeto: chave do projeto cujo snapshot de ambito alimenta o
  # PG_CONTEXT.md da raiz. Quando ha um so projeto ativo no PG_PROJECT_INDEX.json,
  # e resolvida automaticamente.
  [string]$ProjectKey,

  [switch]$SkipIntakeFallback
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Get-JsonDataOrNull {
  param([string]$Path)

  try {
    return (Read-Utf8JsonFile -Path $Path)
  } catch {
    return $null
  }
}

function Test-ScopeSnapshotReady {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    return $false
  }

  $data = Get-JsonDataOrNull -Path $Path
  if (-not $data) {
    return $false
  }

  return (
    -not [string]::IsNullOrWhiteSpace([string]$data.project_name) -and
    $data.source_metadata -and
    -not [string]::IsNullOrWhiteSpace([string]$data.source_metadata.sync_published_at) -and
    -not [string]::IsNullOrWhiteSpace([string]$data.source_metadata.payload_hash)
  )
}

# ---------------------------------------------------------------------------
# Modo multi-projeto: o espelho publica o contexto real em
# projects/<key>/PG_CONTEXT.md e os snapshots em .pg/projects/<key>/, enquanto os
# ficheiros da RAIZ (.pg/PG_SCOPE_SYNC.json, .pg/PG_EFFORT_SYNC.json) ficam nos
# placeholders do bootstrap, todos a null.
#
# Este script so conhecia os da raiz. Resultado observado no PRIacademia: o
# PG_CONTEXT.md da raiz -- o unico que o AGENTS.md manda ler -- continuava com
# "Cliente: [PREENCHER]" enquanto o namespaced tinha 142 linhas de contexto real.
# Pior no esforco: o global declarava 0h contra 31,75h reais, e um ponto de
# situacao construido a partir dele diria ao cliente que nao houve trabalho.
#
# Passa a resolver-se a chave do projeto e a usar o snapshot namespaced. O
# placeholder da raiz nunca e usado como fonte em modo multi-projeto: encher o
# contexto com zeros e pior do que deixa-lo declaradamente vazio.
# ---------------------------------------------------------------------------
function Resolve-PgProjectKey {
  param([string]$Repo, [string]$Explicit)

  if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
    return $Explicit.Trim()
  }

  $indexPath = Join-Path $Repo ".pg\PG_PROJECT_INDEX.json"
  if (-not (Test-Path $indexPath)) {
    return $null
  }

  $index = Get-JsonDataOrNull -Path $indexPath
  if (-not $index -or -not $index.registry) {
    return $null
  }

  $active = @(
    $index.registry |
      Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.project_key) } |
      Where-Object { [string]$_.status -ne 'archived' }
  )

  if ($active.Count -eq 1) {
    return [string]$active[0].project_key
  }

  if ($active.Count -gt 1) {
    $keys = (($active | ForEach-Object { [string]$_.project_key }) -join ', ')
    throw "Modo multi-projeto com $($active.Count) projetos ativos ($keys). Indicar -ProjectKey: o .pg/PG_SCOPE_SYNC.json da raiz nao serve como fonte principal (regra de multi-projeto do AGENTS_SHARED.md)."
  }

  return $null
}

# Aponta o leitor do PG_CONTEXT.md da raiz para o contexto real do espelho, em vez
# de o deixar a competir com ele. Bloco delimitado e idempotente.
function Set-PgMirrorContextPointer {
  param([string]$Repo, [string]$Key)

  $rootContext = Join-Path $Repo "PG_CONTEXT.md"
  if (-not (Test-Path $rootContext)) {
    return
  }

  $mirrorContextRelative = "projects/$Key/PG_CONTEXT.md"
  if (-not (Test-Path (Join-Path $Repo $mirrorContextRelative))) {
    return
  }

  $startMarker = '<!-- PG_AUTO:CONTEXTO_ESPELHO:START -->'
  $endMarker = '<!-- PG_AUTO:CONTEXTO_ESPELHO:END -->'

  # Texto destinado a leitura humana: leva acentuacao de portugues europeu (regra
  # de redacao do AGENTS_SHARED.md). Os caracteres acentuados sao construidos por
  # codigo porque este .ps1 tem de ficar em ASCII puro -- o Windows PowerShell 5.1
  # le scripts sem BOM como ANSI e corromperia literais acentuados.
  $eAcute = [string][char]0x00E9        # e com acento agudo
  $aTilde = [string][char]0x00E3        # a com til
  $aTildeUpper = [string][char]0x00C3   # A com til
  $aAcute = [string][char]0x00E1        # a com acento agudo
  $eCirc = [string][char]0x00EA         # e com acento circunflexo
  $bt = [string][char]0x60              # acento grave (code span markdown)
  $dash = [string][char]0x2014          # travessao

  # Interpolacao e nao concatenacao com '+': em PowerShell a virgula liga MAIS que
  # o '+', pelo que "'a' + $x + 'b', 'c'" e lido como "'a' + $x + @('b','c')" e o
  # array de linhas colapsa numa string unica.
  $block = @(
    $startMarker
    "> **Modo multi-projeto.** O contexto factual deste projeto $eAcute publicado pelo espelho em"
    "> [$bt$mirrorContextRelative$bt]($mirrorContextRelative) $dash $eAcute esse o ficheiro a ler."
    '>'
    "> Os snapshots vivem em $bt.pg/projects/$Key/$bt. Os ficheiros da raiz"
    "> $bt.pg/PG_SCOPE_SYNC.json$bt e $bt.pg/PG_EFFORT_SYNC.json$bt s${aTilde}o placeholders do"
    "> bootstrap: em modo multi-projeto n${aTilde}o s${aTilde}o preenchidos, e N${aTildeUpper}O devem ser"
    "> usados como fonte $dash l${eCirc}-los d$aAcute um projeto vazio."
    $endMarker
  ) -join "`r`n"

  $content = Read-Utf8TextFile -Path $rootContext
  $pattern = [regex]::Escape($startMarker) + '.*?' + [regex]::Escape($endMarker)

  if ([regex]::IsMatch($content, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
    $evaluator = { param($m) return $block }
    $updated = [regex]::Replace($content, $pattern, $evaluator, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  }
  else {
    # Depois do titulo H1, para ser a primeira coisa que se le.
    $titleMatch = [regex]::Match($content, '(?m)^#[^\r\n]*(?=\r?$)')
    if ($titleMatch.Success) {
      $insertAt = $titleMatch.Index + $titleMatch.Length
      $updated = $content.Insert($insertAt, "`r`n`r`n" + $block)
    }
    else {
      $updated = $block + "`r`n`r`n" + $content
    }
  }

  if ($updated -ne $content) {
    Write-Utf8NoBomFile -Path $rootContext -Content $updated
    Write-Host "OK: PG_CONTEXT.md da raiz aponta para $mirrorContextRelative"
  }
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

$resolvedKey = Resolve-PgProjectKey -Repo $repo -Explicit $ProjectKey
$intakePath = Join-Path $repo "PG_SCOPE_INTAKE.yaml"

if ($resolvedKey) {
  Write-Host "INFO: modo multi-projeto (project_key=$resolvedKey)"
  $scopePath = Join-Path $repo ".pg\projects\$resolvedKey\PG_SCOPE_SYNC.json"
  Set-PgMirrorContextPointer -Repo $repo -Key $resolvedKey
}
else {
  $scopePath = Join-Path $repo ".pg\PG_SCOPE_SYNC.json"
}

if (Test-ScopeSnapshotReady -Path $scopePath) {
  & (Join-Path $PSScriptRoot "pg_validate_scope_sync.ps1") -RepoPath $repo -ScopePath $scopePath
  & (Join-Path $PSScriptRoot "pg_apply_scope_sync.ps1") -RepoPath $repo -ScopePath $scopePath
}
elseif ($resolvedKey) {
  # Sem snapshot namespaced pronto, NAO se recorre ao placeholder da raiz nem ao
  # intake: em modo multi-projeto o contexto real e o do espelho.
  Write-Host "SKIP: sem snapshot de ambito pronto em .pg/projects/$resolvedKey/PG_SCOPE_SYNC.json; PG_CONTEXT.md da raiz inalterado (o contexto do espelho esta em projects/$resolvedKey/PG_CONTEXT.md)"
}
elseif ((-not $SkipIntakeFallback) -and (Test-Path $intakePath)) {
  & (Join-Path $PSScriptRoot "pg_build_pg_context.ps1") -RepoPath $repo -IntakePath $intakePath
}

Write-Host "OK: refresh do PG_CONTEXT.md concluido"
