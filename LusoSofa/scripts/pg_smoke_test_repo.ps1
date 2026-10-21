param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  [switch]$RequireOdooSource,

  [switch]$CheckPgAiDevAssistant
)

$ErrorActionPreference = "Stop"

$script:ErrorCount = 0
$script:WarningCount = 0

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Write-CheckResult {
  param(
    [ValidateSet('OK', 'WARN', 'ERROR')]
    [string]$Level,
    [string]$Message
  )

  Write-Host "$Level`: $Message"
}

function Add-Error {
  param([string]$Message)

  $script:ErrorCount += 1
  Write-CheckResult -Level 'ERROR' -Message $Message
}

function Add-Warning {
  param([string]$Message)

  $script:WarningCount += 1
  Write-CheckResult -Level 'WARN' -Message $Message
}

function Test-RequiredPath {
  param(
    [string]$Path,
    [string]$Label
  )

  if (Test-Path $Path) {
    Write-CheckResult -Level 'OK' -Message $Label
    return $true
  }

  Add-Error -Message "$Label em falta: $Path"
  return $false
}

function Test-OptionalPath {
  param(
    [string]$Path,
    [string]$Label
  )

  if (Test-Path $Path) {
    Write-CheckResult -Level 'OK' -Message $Label
    return $true
  }

  Add-Warning -Message "$Label em falta: $Path"
  return $false
}

function Get-JsonDataOrNull {
  param([string]$Path)

  try {
    return (Read-Utf8JsonFile -Path $Path)
  }
  catch {
    return $null
  }
}

function Test-JsonDocument {
  param(
    [string]$Path,
    [string]$Label
  )

  $data = Get-JsonDataOrNull -Path $Path
  if ($data) {
    Write-CheckResult -Level 'OK' -Message "$Label parseado com sucesso"
    return $data
  }

  Add-Error -Message "$Label invalido ou nao parseavel: $Path"
  return $null
}

function Test-TextEncodingNoise {
  param(
    [string]$Text,
    [string]$Label
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  if ((Get-PgTextMojibakeScore -Text $Text) -gt 0 -or (Test-PgSuspiciousMojibake -Text $Text)) {
    Add-Warning -Message "$Label contem padroes compativeis com mojibake ou ruido de encoding"
  }
}

function Test-TextPortugueseAccentNoise {
  param(
    [string]$Text,
    [string]$Label
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  $result = Get-PgPortugueseAccentFindings -Text $Text
  $high = @($result.Findings | Where-Object { $_.Confidence -eq 'high' })
  if ($high.Count -gt 0) {
    $sample = (($high | Select-Object -First 5 | ForEach-Object { "$($_.Word) -> $($_.Suggestion)" }) -join ', ')
    Add-Warning -Message "$Label tem $($high.Count) palavra(s) em portugues-ASCII (acentuacao em falta): $sample. Correr scripts/pg_validate_pt_accents.ps1 -Fix"
  }
}

function Test-TextPlaceholderNoise {
  param(
    [string]$Text,
    [string]$Label
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  if ((Test-PgPlaceholderText -Text $Text) -or $Text.Contains('[PONTO POR VALIDAR]') -or $Text.Contains('[PREENCHER]')) {
    Add-Warning -Message "$Label contem placeholders que deviam ter sido substituidos"
  }
}

function Test-TextQuotedReplyNoise {
  param(
    [string]$Text,
    [string]$Label
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  if (Test-PgQuotedReplyText -Text $Text) {
    Add-Warning -Message "$Label contem quoted replies ou headers de email que nao deviam ser materializados"
  }
}

function Test-TextSignatureNoise {
  param(
    [string]$Text,
    [string]$Label
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  if (Test-PgSignatureText -Text $Text) {
    Add-Warning -Message "$Label contem assinatura ou boilerplate de email"
  }
}

function Test-TextLengthHealth {
  param(
    [string]$Text,
    [string]$Label,
    [int]$MaxChars = 260
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  if ($Text.Length -gt $MaxChars) {
    Add-Warning -Message "$Label excede $MaxChars caracteres e pode indicar reaproveitamento defensivo insuficiente"
  }
}

function Get-NormalizedSemanticText {
  param([string]$Text)

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return ''
  }

  $normalized = $Text.ToLowerInvariant().Trim()
  $normalized = [regex]::Replace($normalized, '\s+', ' ')
  return $normalized.Trim(" .,:;!?()[]{}'`"")
}

function Test-ListSemanticHealth {
  param(
    [string]$Label,
    [string[]]$Items,
    [switch]$WarnIfEmpty,
    [string]$EmptyWarningMessage
  )

  $cleanItems = @($Items | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  if ($cleanItems.Count -eq 0) {
    if ($WarnIfEmpty) {
      if ([string]::IsNullOrWhiteSpace($EmptyWarningMessage)) {
        Add-Warning -Message "$Label nao contem itens factuais publicados"
      }
      else {
        Add-Warning -Message $EmptyWarningMessage
      }
    }
    return
  }

  foreach ($item in $cleanItems) {
    Test-TextEncodingNoise -Text $item -Label "$Label item"
    Test-TextPlaceholderNoise -Text $item -Label "$Label item"
    Test-TextQuotedReplyNoise -Text $item -Label "$Label item"
    Test-TextSignatureNoise -Text $item -Label "$Label item"
    Test-TextLengthHealth -Text $item -Label "$Label item"
  }

  $seen = @{}
  foreach ($item in $cleanItems) {
    $normalized = Get-NormalizedSemanticText -Text $item
    if ([string]::IsNullOrWhiteSpace($normalized)) {
      continue
    }

    if ($seen.ContainsKey($normalized)) {
      Add-Warning -Message "$Label contem itens duplicados ou semanticamente identicos"
      break
    }

    $seen[$normalized] = $true
  }
}

function Test-CrossListOverlap {
  param(
    [string]$LeftLabel,
    [string[]]$LeftItems,
    [string]$RightLabel,
    [string[]]$RightItems
  )

  $leftSet = @{}
  foreach ($item in @($LeftItems | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
    $normalized = Get-NormalizedSemanticText -Text $item
    if (-not [string]::IsNullOrWhiteSpace($normalized)) {
      $leftSet[$normalized] = $true
    }
  }

  if ($leftSet.Count -eq 0) {
    return
  }

  foreach ($item in @($RightItems | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
    $normalized = Get-NormalizedSemanticText -Text $item
    if ([string]::IsNullOrWhiteSpace($normalized)) {
      continue
    }

    if ($leftSet.ContainsKey($normalized)) {
      Add-Warning -Message "$LeftLabel e $RightLabel contem pelo menos um item semanticamente igual; rever classificacao do conteudo"
      return
    }
  }
}

function Test-ScopeSnapshotReady {
  param([pscustomobject]$Data)

  if (-not $Data) {
    return $false
  }

  return (
    -not [string]::IsNullOrWhiteSpace([string]$Data.project_name) -and
    $Data.source_metadata -and
    -not [string]::IsNullOrWhiteSpace([string]$Data.source_metadata.sync_published_at) -and
    -not [string]::IsNullOrWhiteSpace([string]$Data.source_metadata.payload_hash)
  )
}

function Test-EffortSnapshotReady {
  param([pscustomobject]$Data)

  if (-not $Data) {
    return $false
  }

  return (
    -not [string]::IsNullOrWhiteSpace([string]$Data.project_name) -and
    $Data.source_metadata -and
    -not [string]::IsNullOrWhiteSpace([string]$Data.source_metadata.sync_published_at) -and
    -not [string]::IsNullOrWhiteSpace([string]$Data.source_metadata.payload_hash)
  )
}

function Test-ManifestVersion {
  param(
    [string]$ManifestPath
  )

  if (-not (Test-Path $ManifestPath)) {
    Add-Error -Message "Manifest do addon em falta: $ManifestPath"
    return $false
  }

  $content = Read-Utf8TextFile -Path $ManifestPath
  $versionMatch = [regex]::Match($content, "'version'\s*:\s*'([^']+)'")
  $summaryMatch = [regex]::Match($content, "'summary'\s*:\s*'([^']+)'")

  if (-not $versionMatch.Success) {
    Add-Error -Message "Nao foi possivel detetar a versao no manifest: $ManifestPath"
    return $false
  }

  $version = $versionMatch.Groups[1].Value
  Write-CheckResult -Level 'OK' -Message "Versao do addon detetada: $version"

  if ($summaryMatch.Success) {
    Write-CheckResult -Level 'OK' -Message "Summary do addon: $($summaryMatch.Groups[1].Value)"
  }

  return $true
}

function Get-MarkedBlock {
  param(
    [string]$Text,
    [string]$Marker
  )

  $pattern = "(?s)<!-- PG_AUTO:$Marker`:START -->\s*(.*?)\s*<!-- PG_AUTO:$Marker`:END -->"
  $match = [regex]::Match($Text, $pattern)
  if (-not $match.Success) {
    return $null
  }

  return $match.Groups[1].Value
}

function Test-PgContextMarkers {
  param([string]$ContextText)

  if (-not ($ContextText -match "<!-- PG_AUTO:IDENTIFICACAO:START -->")) {
    Add-Warning -Message "PG_CONTEXT.md nao tem marcadores PG_AUTO (ficheiro gerado pelo mirror - checks de marcadores ignorados)"
    return $false
  }

  $markers = @(
    'IDENTIFICACAO',
    'RESTRICOES',
    'PEDIDO_ATUAL',
    'PROCESSO_ATUAL',
    'PROBLEMA_DOR',
    'IMPACTO_NEGOCIO',
    'SCOPE_ITEMS'
  )

  foreach ($marker in $markers) {
    $start = "<!-- PG_AUTO:$marker`:START -->"
    $end = "<!-- PG_AUTO:$marker`:END -->"

    if ($ContextText.Contains($start) -and $ContextText.Contains($end)) {
      Write-CheckResult -Level 'OK' -Message "Marcadores PG_AUTO presentes para $marker"
    }
    else {
      Add-Error -Message "Marcadores PG_AUTO em falta para $marker no PG_CONTEXT.md"
    }
  }

  return $true
}

function Test-WorkflowSemantics {
  param([string]$WorkflowText)

  if ([string]::IsNullOrWhiteSpace($WorkflowText)) {
    Add-Error -Message 'Workflow de refresh de contexto vazio ou nao legivel'
    return
  }

  $checks = @(
    @{ Needle = '.pg/PG_SCOPE_SYNC.json'; Label = 'Workflow observa alteracoes de PG_SCOPE_SYNC.json' },
    @{ Needle = 'pg_refresh_pg_context.ps1'; Label = 'Workflow chama pg_refresh_pg_context.ps1' },
    @{ Needle = 'PG_TEMPLATE_REPO_TOKEN'; Label = 'Workflow documenta o secret PG_TEMPLATE_REPO_TOKEN' }
  )

  foreach ($check in $checks) {
    if ($WorkflowText.Contains($check.Needle)) {
      Write-CheckResult -Level 'OK' -Message $check.Label
    }
    else {
      Add-Warning -Message "Workflow de refresh nao contem a referencia esperada: $($check.Needle)"
    }
  }
}

function Get-FileSha256 {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    return $null
  }

  return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-SharedFileParity {
  param(
    [string]$FrameworkPath,
    [string]$RepoPath,
    [string]$Label
  )

  if (-not (Test-Path $FrameworkPath)) {
    Add-Warning -Message "$Label nao pode ser comparado porque a origem no framework nao existe: $FrameworkPath"
    return
  }

  if (-not (Test-Path $RepoPath)) {
    Add-Warning -Message "$Label nao pode ser comparado porque o ficheiro local nao existe: $RepoPath"
    return
  }

  $frameworkHash = Get-FileSha256 -Path $FrameworkPath
  $repoHash = Get-FileSha256 -Path $RepoPath
  if ($frameworkHash -eq $repoHash) {
    Write-CheckResult -Level 'OK' -Message "$Label alinhado com o framework partilhado"
  }
  else {
    Add-Warning -Message "$Label desfasado do framework partilhado; correr pg_sync_shared_assets.ps1"
  }
}

# O .gitignore e o unico asset partilhado com merge (regras do projeto fora do
# bloco gerido), pelo que a paridade nao pode ser do ficheiro inteiro: seria drift
# falso em qualquer repo que tenha regras proprias. Compara-se o BLOCO.
function Test-ManagedGitignoreParity {
  param(
    [string]$FrameworkPath,
    [string]$RepoPath
  )

  if (-not (Test-Path $FrameworkPath)) {
    Add-Warning -Message ".gitignore nao pode ser comparado porque a origem no framework nao existe: $FrameworkPath"
    return
  }

  if (-not (Test-Path $RepoPath)) {
    Add-Warning -Message ".gitignore nao pode ser comparado porque o ficheiro local nao existe: $RepoPath"
    return
  }

  $expected = (Get-PgGitignoreManagedBlock -FrameworkContent (Read-Utf8TextFile -Path $FrameworkPath))
  $expectedRules = Get-PgGitignoreBlockRules -Content $expected
  $actualRules = Get-PgGitignoreBlockRules -Content (Read-Utf8TextFile -Path $RepoPath)

  if ($null -eq $actualRules) {
    Add-Warning -Message '.gitignore sem o bloco da framework (formato antigo); correr pg_sync_shared_assets.ps1 para o acrescentar sem perder as regras do projeto'
    return
  }

  if ($expectedRules -eq $actualRules) {
    Write-CheckResult -Level 'OK' -Message '.gitignore com o bloco da framework alinhado (regras do projeto preservadas)'
  }
  else {
    Add-Warning -Message '.gitignore com o bloco da framework desfasado; correr pg_sync_shared_assets.ps1'
  }
}

function Test-SharedDirectoryParity {
  param(
    [string]$FrameworkDirectory,
    [string]$RepoDirectory,
    [string]$Label
  )

  if (-not (Test-Path $FrameworkDirectory)) {
    Add-Warning -Message "$Label nao pode ser comparado porque a origem no framework nao existe: $FrameworkDirectory"
    return
  }

  if (-not (Test-Path $RepoDirectory)) {
    Add-Warning -Message "$Label nao existe no repositorio bootstrapado: $RepoDirectory"
    return
  }

  $frameworkFiles = @(Get-ChildItem -Path $FrameworkDirectory -File -Recurse | ForEach-Object {
      @{
        RelativePath = $_.FullName.Substring($FrameworkDirectory.Length).TrimStart('\')
        Hash = Get-FileSha256 -Path $_.FullName
      }
    })
  $repoFiles = @(Get-ChildItem -Path $RepoDirectory -File -Recurse | ForEach-Object {
      @{
        RelativePath = $_.FullName.Substring($RepoDirectory.Length).TrimStart('\')
        Hash = Get-FileSha256 -Path $_.FullName
      }
    })

  if ($frameworkFiles.Count -ne $repoFiles.Count) {
    Add-Warning -Message "$Label desfasado do framework partilhado; numero de ficheiros diferente"
    return
  }

  $repoMap = @{}
  foreach ($file in $repoFiles) {
    $repoMap[$file.RelativePath] = $file.Hash
  }

  foreach ($file in $frameworkFiles) {
    if (-not $repoMap.ContainsKey($file.RelativePath)) {
      Add-Warning -Message "$Label desfasado do framework partilhado; ficheiro em falta: $($file.RelativePath)"
      return
    }
    if ($repoMap[$file.RelativePath] -ne $file.Hash) {
      Add-Warning -Message "$Label desfasado do framework partilhado; conteudo divergente em $($file.RelativePath)"
      return
    }
  }

  Write-CheckResult -Level 'OK' -Message "$Label alinhado com o framework partilhado"
}

function Test-SharedAssetParity {
  param(
    [string]$RepoRoot,
    [string]$FrameworkRoot,
    [string]$StatePath
  )

  if (Test-Path $StatePath) {
    $state = Test-JsonDocument -Path $StatePath -Label 'PG_TEMPLATE_SYNC_STATE.json'
    if ($state) {
      if (-not [string]::IsNullOrWhiteSpace([string]$state.synced_at)) {
        Write-CheckResult -Level 'OK' -Message "Estado de sync registado em $([string]$state.synced_at)"
      }
    }
  }
  else {
    Add-Warning -Message 'Estado de sync dos assets partilhados em falta; correr pg_sync_shared_assets.ps1 para registar e alinhar o repo bootstrapado'
  }

  $sharedFileChecks = @(
    @{ Framework = Join-Path $FrameworkRoot 'templates\.editorconfig'; Repo = Join-Path $RepoRoot '.editorconfig'; Label = '.editorconfig' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\.gitattributes'; Repo = Join-Path $RepoRoot '.gitattributes'; Label = '.gitattributes' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\AGENTS.md'; Repo = Join-Path $RepoRoot 'AGENTS.md'; Label = 'AGENTS.md' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\CLAUDE.md'; Repo = Join-Path $RepoRoot 'CLAUDE.md'; Label = 'CLAUDE.md' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\.github\workflows\pg_refresh_pg_context.yml'; Repo = Join-Path $RepoRoot '.github\workflows\pg_refresh_pg_context.yml'; Label = 'Workflow GitHub de refresh de contexto' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\.agents\skills\pg-odoo-navigator\SKILL.md'; Repo = Join-Path $RepoRoot '.agents\skills\pg-odoo-navigator\SKILL.md'; Label = 'Skill PG Odoo Navigator (Codex/agentes)' },
    @{ Framework = Join-Path $FrameworkRoot 'templates\.agents\skills\pg-odoo-navigator\SKILL.md'; Repo = Join-Path $RepoRoot '.claude\skills\pg-odoo-navigator\SKILL.md'; Label = 'Skill PG Odoo Navigator (Claude)' },
    @{ Framework = Join-Path $FrameworkRoot 'config.toml'; Repo = Join-Path $RepoRoot 'config.toml'; Label = 'config.toml' }
  )

  foreach ($check in $sharedFileChecks) {
    Test-SharedFileParity -FrameworkPath $check.Framework -RepoPath $check.Repo -Label $check.Label
  }

  Test-ManagedGitignoreParity `
    -FrameworkPath (Join-Path $FrameworkRoot 'templates\.gitignore') `
    -RepoPath (Join-Path $RepoRoot '.gitignore')

  Test-SharedDirectoryParity `
    -FrameworkDirectory (Join-Path $FrameworkRoot 'doc_templates') `
    -RepoDirectory (Join-Path $RepoRoot 'doc_templates') `
    -Label 'doc_templates'
}

function Test-DocTemplatesManifestIntegrity {
  param(
    [string]$RepoRoot
  )

  $manifestPath = Join-Path $RepoRoot 'doc_templates\MANIFEST.json'
  if (-not (Test-Path $manifestPath)) {
    Add-Error -Message "doc_templates/MANIFEST.json em falta: $manifestPath"
    return
  }

  $manifest = Test-JsonDocument -Path $manifestPath -Label 'doc_templates/MANIFEST.json'
  if (-not $manifest) {
    return
  }

  if (-not $manifest.templates) {
    Add-Error -Message 'doc_templates/MANIFEST.json sem objeto templates'
    return
  }

  $tplFiles = @(Get-ChildItem -Path (Join-Path $RepoRoot 'doc_templates') -File -Filter 'TPL_*.md')
  if ($tplFiles.Count -eq 0) {
    Add-Error -Message 'doc_templates nao contem ficheiros TPL_*.md'
    return
  }

  foreach ($tplFile in $tplFiles) {
    $code = [System.IO.Path]::GetFileNameWithoutExtension($tplFile.Name)
    $entry = $manifest.templates.$code
    if (-not $entry) {
      Add-Error -Message "Template $code existe no disco mas nao existe no MANIFEST.json"
      continue
    }

    if ([string]::IsNullOrWhiteSpace([string]$entry.sha256)) {
      Add-Error -Message "Template $code no MANIFEST.json sem sha256"
      continue
    }

    $actualSha = (Get-FileHash -Path $tplFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $declaredSha = ([string]$entry.sha256).ToLowerInvariant()
    if ($actualSha -ne $declaredSha) {
      Add-Error -Message "Hash mismatch em doc_templates/$($tplFile.Name): ficheiro editado sem refresh de MANIFEST.json"
      continue
    }

    Write-CheckResult -Level 'OK' -Message "Template $code alinhado com MANIFEST.json"
  }
}

function Test-ContextContains {
  param(
    [string]$Haystack,
    [string]$Needle,
    [string]$SuccessLabel,
    [string]$WarningMessage
  )

  if ([string]::IsNullOrWhiteSpace($Needle)) {
    return
  }

  if ($Haystack -like "*$Needle*") {
    Write-CheckResult -Level 'OK' -Message $SuccessLabel
  }
  else {
    Add-Warning -Message $WarningMessage
  }
}

function Test-ScopeContextSemantics {
  param(
    [string]$ContextText,
    [pscustomobject]$ScopeData,
    [bool]$HasPgAutoMarkers = $true
  )

  if (-not $HasPgAutoMarkers) {
    Add-Warning -Message 'PG_CONTEXT.md gerado pelo mirror sem marcadores PG_AUTO; checks de materializacao de scope no contexto foram ignorados'
    return
  }

  $identificationBlock = Get-MarkedBlock -Text $ContextText -Marker 'IDENTIFICACAO'
  $requestBlock = Get-MarkedBlock -Text $ContextText -Marker 'PEDIDO_ATUAL'
  $processBlock = Get-MarkedBlock -Text $ContextText -Marker 'PROCESSO_ATUAL'
  $problemBlock = Get-MarkedBlock -Text $ContextText -Marker 'PROBLEMA_DOR'
  $impactBlock = Get-MarkedBlock -Text $ContextText -Marker 'IMPACTO_NEGOCIO'
  $scopeItemsBlock = Get-MarkedBlock -Text $ContextText -Marker 'SCOPE_ITEMS'

  if (-not $identificationBlock) {
    Add-Error -Message 'Bloco IDENTIFICACAO nao encontrado no PG_CONTEXT.md'
    return
  }
  if (-not $scopeItemsBlock) {
    Add-Error -Message 'Bloco SCOPE_ITEMS nao encontrado no PG_CONTEXT.md'
    return
  }

  foreach ($block in @(
    @{ Label = 'Bloco IDENTIFICACAO'; Text = $identificationBlock },
    @{ Label = 'Bloco PEDIDO_ATUAL'; Text = $requestBlock },
    @{ Label = 'Bloco PROCESSO_ATUAL'; Text = $processBlock },
    @{ Label = 'Bloco PROBLEMA_DOR'; Text = $problemBlock },
    @{ Label = 'Bloco IMPACTO_NEGOCIO'; Text = $impactBlock },
    @{ Label = 'Bloco SCOPE_ITEMS'; Text = $scopeItemsBlock }
  )) {
    Test-TextQuotedReplyNoise -Text $block.Text -Label $block.Label
    Test-TextSignatureNoise -Text $block.Text -Label $block.Label
  }

  $sourceReference = "{0} / {1} / {2}" -f `
    [string]$ScopeData.source_metadata.source_system, `
    [string]$ScopeData.source_metadata.source_model, `
    [string]$ScopeData.source_metadata.source_record_id

  Test-ContextContains -Haystack $identificationBlock `
    -Needle ("Nome do projeto: " + [string]$ScopeData.project_name) `
    -SuccessLabel 'PG_CONTEXT.md reflete project_name do scope sync' `
    -WarningMessage 'PG_CONTEXT.md nao reflete o project_name atual do snapshot de scope'

  Test-ContextContains -Haystack $identificationBlock `
    -Needle ("Fase atual do projeto: " + [string]$ScopeData.project_phase) `
    -SuccessLabel 'PG_CONTEXT.md reflete project_phase do scope sync' `
    -WarningMessage 'PG_CONTEXT.md nao reflete a fase atual do snapshot de scope'

  Test-ContextContains -Haystack $ContextText `
    -Needle ("Ultima sincronizacao de ambito: " + [string]$ScopeData.source_metadata.sync_published_at) `
    -SuccessLabel 'PG_CONTEXT.md reflete a data do ultimo scope sync' `
    -WarningMessage 'PG_CONTEXT.md nao reflete a data do ultimo scope sync'

  Test-ContextContains -Haystack $ContextText `
    -Needle ("Fonte do ambito sincronizado: " + $sourceReference) `
    -SuccessLabel 'PG_CONTEXT.md reflete a origem do ultimo scope sync' `
    -WarningMessage 'PG_CONTEXT.md nao reflete a origem atual do snapshot de scope'

  Test-ContextContains -Haystack $scopeItemsBlock `
    -Needle ("- Itens ativos: " + [string]$ScopeData.scope_summary.active_scope_item_count) `
    -SuccessLabel 'PG_CONTEXT.md reflete a contagem de itens ativos do scope sync' `
    -WarningMessage 'PG_CONTEXT.md nao reflete a contagem atual de itens ativos do scope sync'

  $scopeItems = @($ScopeData.scope_items)
  if ($scopeItems.Count -gt 0) {
    $firstItem = $scopeItems[0]
    Test-ContextContains -Haystack $scopeItemsBlock `
      -Needle ([string]$firstItem.task_name) `
      -SuccessLabel 'PG_CONTEXT.md materializa pelo menos uma task do scope sync' `
      -WarningMessage 'PG_CONTEXT.md nao materializa a task esperada do snapshot de scope'

    Test-ContextContains -Haystack $scopeItemsBlock `
      -Needle ([string]$firstItem.scope_summary) `
      -SuccessLabel 'PG_CONTEXT.md materializa o resumo de task do scope sync' `
      -WarningMessage 'PG_CONTEXT.md nao materializa o resumo atual da task em scope'
  }

  if ($scopeItemsBlock.Contains('[PREENCHER]')) {
    Add-Warning -Message 'Bloco SCOPE_ITEMS ainda contem placeholders [PREENCHER]'
  }
}

function Test-ScopeSnapshotContentSemantics {
  param([pscustomobject]$ScopeData)

  $overview = $ScopeData.scope_overview
  if ($overview) {
    Test-TextEncodingNoise -Text ([string]$overview.business_goal) -Label 'scope_overview.business_goal'
    Test-TextEncodingNoise -Text ([string]$overview.current_request) -Label 'scope_overview.current_request'
    Test-TextPlaceholderNoise -Text ([string]$overview.business_goal) -Label 'scope_overview.business_goal'
    Test-TextPlaceholderNoise -Text ([string]$overview.current_request) -Label 'scope_overview.current_request'
    Test-TextQuotedReplyNoise -Text ([string]$overview.business_goal) -Label 'scope_overview.business_goal'
    Test-TextQuotedReplyNoise -Text ([string]$overview.current_request) -Label 'scope_overview.current_request'
    Test-TextSignatureNoise -Text ([string]$overview.business_goal) -Label 'scope_overview.business_goal'
    Test-TextSignatureNoise -Text ([string]$overview.current_request) -Label 'scope_overview.current_request'
    Test-TextLengthHealth -Text ([string]$overview.business_goal) -Label 'scope_overview.business_goal'
    Test-TextLengthHealth -Text ([string]$overview.current_request) -Label 'scope_overview.current_request'
    Test-ListSemanticHealth `
      -Label 'scope_overview.acceptance_criteria' `
      -Items @($overview.acceptance_criteria) `
      -WarnIfEmpty `
      -EmptyWarningMessage 'scope_overview.acceptance_criteria vazio; o ambito publicado ainda nao consolidou criterios factuais'
  }

  foreach ($item in @($ScopeData.scope_items)) {
    Test-TextEncodingNoise -Text ([string]$item.task_name) -Label 'scope_items.task_name'
    Test-TextEncodingNoise -Text ([string]$item.scope_summary) -Label 'scope_items.scope_summary'
    Test-TextPlaceholderNoise -Text ([string]$item.scope_summary) -Label 'scope_items.scope_summary'
    Test-TextQuotedReplyNoise -Text ([string]$item.scope_summary) -Label 'scope_items.scope_summary'
    Test-TextSignatureNoise -Text ([string]$item.scope_summary) -Label 'scope_items.scope_summary'
    Test-TextLengthHealth -Text ([string]$item.scope_summary) -Label 'scope_items.scope_summary'
    Test-ListSemanticHealth `
      -Label "scope_items.acceptance_criteria task $([string]$item.task_id)" `
      -Items @($item.acceptance_criteria) `
      -WarnIfEmpty `
      -EmptyWarningMessage "scope_items.acceptance_criteria task $([string]$item.task_id) vazio; falta consolidar criterios factuais"
  }
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

$frameworkScriptsRoot = Join-Path $repo '.pg_framework\scripts'
$contextPath = Join-Path $repo 'PG_CONTEXT.md'
$scopePath = Join-Path $repo '.pg\PG_SCOPE_SYNC.json'
$effortPath = Join-Path $repo '.pg\PG_EFFORT_SYNC.json'
$tokenConsumptionPath = Join-Path $repo '.pg\tokens\consumption.jsonl'
$sharedAssetStatePath = Join-Path $repo '.pg\PG_TEMPLATE_SYNC_STATE.json'
$workflowPath = Join-Path $repo '.github\workflows\pg_refresh_pg_context.yml'

$requiredPaths = @(
  @{ Path = Join-Path $repo '.pg_framework'; Label = 'Framework partilhado acessivel via .pg_framework' },
  @{ Path = Join-Path $repo '.editorconfig'; Label = '.editorconfig presente na raiz' },
  @{ Path = Join-Path $repo '.gitignore'; Label = '.gitignore presente na raiz' },
  @{ Path = Join-Path $repo '.gitattributes'; Label = '.gitattributes presente na raiz' },
  @{ Path = $workflowPath; Label = 'Workflow GitHub de refresh de contexto presente' },
  @{ Path = Join-Path $repo 'AGENTS.md'; Label = 'AGENTS.md presente' },
  @{ Path = Join-Path $repo 'CLAUDE.md'; Label = 'CLAUDE.md presente' },
  @{ Path = $contextPath; Label = 'PG_CONTEXT.md presente' },
  @{ Path = Join-Path $repo 'PG_SCOPE_INTAKE.yaml'; Label = 'PG_SCOPE_INTAKE.yaml presente' },
  @{ Path = Join-Path $repo 'config.toml'; Label = 'config.toml presente' },
  @{ Path = $scopePath; Label = '.pg/PG_SCOPE_SYNC.json presente' },
  @{ Path = $effortPath; Label = '.pg/PG_EFFORT_SYNC.json presente' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_refresh_pg_context.ps1'; Label = 'Script pg_refresh_pg_context.ps1 acessivel' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_validate_scope_sync.ps1'; Label = 'Script pg_validate_scope_sync.ps1 acessivel' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_apply_scope_sync.ps1'; Label = 'Script pg_apply_scope_sync.ps1 acessivel' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_validate_effort_sync.ps1'; Label = 'Script pg_validate_effort_sync.ps1 acessivel' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_validate_token_consumption.ps1'; Label = 'Script pg_validate_token_consumption.ps1 acessivel' },
  @{ Path = Join-Path $frameworkScriptsRoot 'pg_validate_pt_accents.ps1'; Label = 'Script pg_validate_pt_accents.ps1 acessivel' }
)

foreach ($item in $requiredPaths) {
  [void](Test-RequiredPath -Path $item.Path -Label $item.Label)
}

Test-SharedAssetParity `
  -RepoRoot $repo `
  -FrameworkRoot (Join-Path $repo '.pg_framework') `
  -StatePath $sharedAssetStatePath

Test-DocTemplatesManifestIntegrity -RepoRoot $repo

$communitySource = Join-Path $repo 'vendor\odoo_src\community'
if ($RequireOdooSource) {
  [void](Test-RequiredPath -Path $communitySource -Label 'Source Community do Odoo presente')
}
else {
  [void](Test-OptionalPath -Path $communitySource -Label 'Source Community do Odoo presente')
}

if ($CheckPgAiDevAssistant) {
  $addonRoot = Join-Path $repo 'pg_brodoo'
  if (Test-RequiredPath -Path $addonRoot -Label 'Addon pg_brodoo presente') {
    [void](Test-ManifestVersion -ManifestPath (Join-Path $addonRoot '__manifest__.py'))

    $addonRequired = @(
      'models\project_project.py',
      'models\project_milestone.py',
      'models\pg_project_scope_sync_run.py',
      'models\pg_project_effort_sync_run.py',
      'models\pg_project_mirror_sync_run.py',
      'views\project_project_views.xml',
      'views\project_task_scope_views.xml',
      'views\pg_project_scope_sync_run_views.xml',
      'views\pg_project_effort_sync_run_views.xml',
      'views\pg_project_mirror_sync_run_views.xml'
    )

    foreach ($relativePath in $addonRequired) {
      [void](Test-RequiredPath -Path (Join-Path $addonRoot $relativePath) -Label "Addon: $relativePath")
    }
  }
}

$contextText = $null
if (Test-Path $contextPath) {
  $contextText = Read-Utf8TextFile -Path $contextPath
  Test-TextEncodingNoise -Text $contextText -Label 'PG_CONTEXT.md'
  Test-TextPortugueseAccentNoise -Text $contextText -Label 'PG_CONTEXT.md'
  $hasPgAutoMarkers = Test-PgContextMarkers -ContextText $contextText
}

if (Test-Path $workflowPath) {
  Test-WorkflowSemantics -WorkflowText (Read-Utf8TextFile -Path $workflowPath)
}

$scopeData = $null
if (Test-Path $scopePath) {
  $scopeText = Read-Utf8TextFile -Path $scopePath
  Test-TextEncodingNoise -Text $scopeText -Label 'PG_SCOPE_SYNC.json'
  Test-TextQuotedReplyNoise -Text $scopeText -Label 'PG_SCOPE_SYNC.json'
  Test-TextSignatureNoise -Text $scopeText -Label 'PG_SCOPE_SYNC.json'
  $scopeData = Test-JsonDocument -Path $scopePath -Label 'PG_SCOPE_SYNC.json'
}

$effortData = $null
if (Test-Path $effortPath) {
  $effortText = Read-Utf8TextFile -Path $effortPath
  Test-TextEncodingNoise -Text $effortText -Label 'PG_EFFORT_SYNC.json'
  Test-TextQuotedReplyNoise -Text $effortText -Label 'PG_EFFORT_SYNC.json'
  Test-TextSignatureNoise -Text $effortText -Label 'PG_EFFORT_SYNC.json'
  $effortData = Test-JsonDocument -Path $effortPath -Label 'PG_EFFORT_SYNC.json'
}

if ($scopeData) {
  if (Test-ScopeSnapshotReady -Data $scopeData) {
    Test-ScopeSnapshotContentSemantics -ScopeData $scopeData

    try {
      & (Join-Path $frameworkScriptsRoot 'pg_validate_scope_sync.ps1') -RepoPath $repo -ScopePath $scopePath | Out-Null
      Write-CheckResult -Level 'OK' -Message 'Contrato do PG_SCOPE_SYNC.json validado'
    }
    catch {
      Add-Error -Message "PG_SCOPE_SYNC.json publicado mas invalido: $($_.Exception.Message)"
    }

    if ($contextText) {
      Test-ScopeContextSemantics -ContextText $contextText -ScopeData $scopeData -HasPgAutoMarkers $hasPgAutoMarkers
    }
  }
  else {
    Add-Warning -Message 'PG_SCOPE_SYNC.json existe mas ainda esta em estado placeholder ou sem publish real'
  }
}

if ($effortData) {
  if (Test-EffortSnapshotReady -Data $effortData) {
    try {
      & (Join-Path $frameworkScriptsRoot 'pg_validate_effort_sync.ps1') -RepoPath $repo -EffortPath $effortPath | Out-Null
      Write-CheckResult -Level 'OK' -Message 'Contrato do PG_EFFORT_SYNC.json validado'
    }
    catch {
      Add-Error -Message "PG_EFFORT_SYNC.json publicado mas invalido: $($_.Exception.Message)"
    }
  }
  else {
    Add-Warning -Message 'PG_EFFORT_SYNC.json existe mas ainda esta em estado placeholder ou sem publish real'
  }
}

if (Test-Path $tokenConsumptionPath) {
  try {
    # 3>&1 traz o stream de avisos para o pipeline: sem isto, as sessoes sem
    # session_open que o validador sinaliza ficariam invisiveis (o Out-Null
    # engolia-as) e nao entrariam na contagem de warnings deste smoke test.
    $tokenValidation = @(& (Join-Path $frameworkScriptsRoot 'pg_validate_token_consumption.ps1') -RepoPath $repo -ConsumptionPath $tokenConsumptionPath 3>&1)
    Write-CheckResult -Level 'OK' -Message 'Contrato do .pg/tokens/consumption.jsonl validado'
    foreach ($record in @($tokenValidation | Where-Object { $_ -is [System.Management.Automation.WarningRecord] })) {
      Add-Warning -Message ([string]$record.Message)
    }
  }
  catch {
    Add-Error -Message ".pg/tokens/consumption.jsonl invalido: $($_.Exception.Message)"
  }
}
else {
  Add-Warning -Message '.pg/tokens/consumption.jsonl em falta; registar session_open/session_progress/session_close por sessao'
}

$preflightScript = Join-Path $frameworkScriptsRoot 'pg_preflight_context.ps1'
if (Test-Path $preflightScript) {
  try {
    & $preflightScript -RepoPath $repo -Quiet | Out-Null
    Write-CheckResult -Level 'OK' -Message 'Preflight de contexto (AUD-01): status pass'
  }
  catch {
    if ($RequireOdooSource) {
      Add-Error -Message "Preflight de contexto falhou: $($_.Exception.Message)"
    }
    else {
      Add-Warning -Message "Preflight de contexto com pendencias (ver .pg/PREFLIGHT.json): $($_.Exception.Message)"
    }
  }
}

if ($script:ErrorCount -gt 0) {
  throw "Smoke test falhou com $($script:ErrorCount) erro(s) e $($script:WarningCount) warning(s)."
}

if ($script:WarningCount -gt 0) {
  Write-Host "OK: smoke test do repositorio concluido sem erros e com $($script:WarningCount) warning(s)"
}
else {
  Write-Host 'OK: smoke test do repositorio concluido sem erros'
}
