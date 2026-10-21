param(
  [Parameter(Mandatory = $true)]
  [string]$RepoName,

  [string]$RepoPath,

  [switch]$Force,

  [switch]$RefreshDocTemplatesFromOdoo,
  [string]$OdooBaseUrl,
  [string]$OdooDatabase,
  [string]$OdooLogin,
  [string]$OdooWorkspaceXmlId = "pg_doc_templates.workspace_doc_templates",
  [string]$PythonExe = "py"
)

$ErrorActionPreference = "Stop"

function Resolve-TemplateRoot {
  return (Split-Path -Parent $PSScriptRoot)
}

function Resolve-TargetRepo {
  param(
    [string]$Name,
    [string]$ExplicitPath,
    [string]$TemplateRoot
  )

  if ($ExplicitPath) {
    return [System.IO.Path]::GetFullPath($ExplicitPath)
  }

  $reposRoot = Split-Path -Parent $TemplateRoot
  return Join-Path $reposRoot $Name
}

function Ensure-ParentDirectory {
  param([string]$FilePath)

  $parent = Split-Path -Parent $FilePath
  if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
  }
}

$templateRoot = Resolve-TemplateRoot
$templatesDir = Join-Path $templateRoot "templates"
$repo = Resolve-TargetRepo -Name $RepoName -ExplicitPath $RepoPath -TemplateRoot $templateRoot

if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

$contextPath = Join-Path $repo "PG_CONTEXT.md"
$intakePath = Join-Path $repo "PG_SCOPE_INTAKE.yaml"
$contextExistedBeforeBootstrap = Test-Path $contextPath
$intakeExistedBeforeBootstrap = Test-Path $intakePath

$copyMap = @(
  @{ Source = Join-Path $templatesDir ".editorconfig"; Destination = Join-Path $repo ".editorconfig" },
  @{ Source = Join-Path $templatesDir ".gitignore"; Destination = Join-Path $repo ".gitignore" },
  @{ Source = Join-Path $templatesDir ".gitattributes"; Destination = Join-Path $repo ".gitattributes" },
  @{ Source = Join-Path $templatesDir ".github\workflows\pg_refresh_pg_context.yml"; Destination = Join-Path $repo ".github\workflows\pg_refresh_pg_context.yml" },
  @{ Source = Join-Path $templatesDir ".claude\settings.json"; Destination = Join-Path $repo ".claude\settings.json" },
  @{ Source = Join-Path $templatesDir ".codex\hooks.json"; Destination = Join-Path $repo ".codex\hooks.json" },
  @{ Source = Join-Path $templatesDir ".agents\hooks.json"; Destination = Join-Path $repo ".agents\hooks.json" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\SKILL.md"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\agents\openai.yaml"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\agents\openai.yaml" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\SKILL.md"; Destination = Join-Path $repo ".claude\skills\pg-odoo-navigator\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md"; Destination = Join-Path $repo ".claude\skills\pg-odoo-navigator\references\odoo-navigation.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-revisao-sexta\SKILL.md"; Destination = Join-Path $repo ".agents\skills\pg-revisao-sexta\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-revisao-sexta\agents\openai.yaml"; Destination = Join-Path $repo ".agents\skills\pg-revisao-sexta\agents\openai.yaml" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-revisao-sexta\references\manual-sexta.md"; Destination = Join-Path $repo ".agents\skills\pg-revisao-sexta\references\manual-sexta.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-revisao-sexta\SKILL.md"; Destination = Join-Path $repo ".claude\skills\pg-revisao-sexta\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-revisao-sexta\references\manual-sexta.md"; Destination = Join-Path $repo ".claude\skills\pg-revisao-sexta\references\manual-sexta.md" },
  @{ Source = Join-Path $templatesDir "AGENTS.md"; Destination = Join-Path $repo "AGENTS.md" },
  @{ Source = Join-Path $templatesDir "CLAUDE.md"; Destination = Join-Path $repo "CLAUDE.md" },
  @{ Source = Join-Path $templatesDir "PG_CONTEXT.md"; Destination = Join-Path $repo "PG_CONTEXT.md" },
  @{ Source = Join-Path $templatesDir "PG_SCOPE_INTAKE.yaml"; Destination = Join-Path $repo "PG_SCOPE_INTAKE.yaml" },
  @{ Source = Join-Path $templateRoot "config.toml"; Destination = Join-Path $repo "config.toml" }
)

foreach ($item in $copyMap) {
  if (-not (Test-Path $item.Source)) {
    throw "Ficheiro de template nao encontrado: $($item.Source)"
  }

  if ((-not (Test-Path $item.Destination)) -or $Force) {
    Ensure-ParentDirectory -FilePath $item.Destination
    Copy-Item -Path $item.Source -Destination $item.Destination -Force:$Force
    Write-Host "OK: $($item.Destination)"
  } else {
    Write-Host "SKIP: $($item.Destination) ja existe"
  }
}

$contextDest = Join-Path $repo "PG_CONTEXT.md"
$contextSrc = Join-Path $templatesDir "PG_CONTEXT.md"
if ((Test-Path $contextDest) -and (Test-Path $contextSrc)) {
  $existingContent = Get-Content -Path $contextDest -Raw -ErrorAction SilentlyContinue
  if ($Force -and ($existingContent -notmatch "<!-- PG_AUTO:IDENTIFICACAO:START -->")) {
    Copy-Item -Path $contextSrc -Destination $contextDest -Force
    Write-Host "OK: PG_CONTEXT.md substituido com -Force (formato sem marcadores PG_AUTO incompativel com o framework)"
  } elseif ($existingContent -notmatch "<!-- PG_AUTO:IDENTIFICACAO:START -->") {
    Write-Host "SKIP: PG_CONTEXT.md sem marcadores PG_AUTO detetado; preservado para evitar perda de contexto (usar -Force para substituir)"
  }
}

$frameworkLinkScript = Join-Path $PSScriptRoot "pg_link_framework.ps1"
if (Test-Path $frameworkLinkScript) {
  & $frameworkLinkScript -RepoPath $repo
}

$directoriesToEnsure = @(
  (Join-Path $repo "vendor"),
  (Join-Path $repo ".pg"),
  (Join-Path $repo ".pg\tokens")
)

foreach ($directory in $directoriesToEnsure) {
  if (-not (Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory | Out-Null
    Write-Host "OK: criada pasta $directory"
  }
}

$tokenConsumptionPath = Join-Path $repo ".pg\tokens\consumption.jsonl"
if ((-not (Test-Path $tokenConsumptionPath)) -or $Force) {
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($tokenConsumptionPath, "", $encoding)
  Write-Host "OK: $tokenConsumptionPath"
}
else {
  Write-Host "SKIP: $tokenConsumptionPath ja existe"
}

$scopeTemplate = Join-Path $templatesDir ".pg\PG_SCOPE_SYNC.json"
$scopeDestination = Join-Path $repo ".pg\PG_SCOPE_SYNC.json"
if (-not (Test-Path $scopeTemplate)) {
  throw "Ficheiro de template nao encontrado: $scopeTemplate"
}

if ((-not (Test-Path $scopeDestination)) -or $Force) {
  Copy-Item -Path $scopeTemplate -Destination $scopeDestination -Force:$Force
  Write-Host "OK: $scopeDestination"
} else {
  Write-Host "SKIP: $scopeDestination ja existe"
}

$effortTemplate = Join-Path $templatesDir ".pg\PG_EFFORT_SYNC.json"
$effortDestination = Join-Path $repo ".pg\PG_EFFORT_SYNC.json"
if (-not (Test-Path $effortTemplate)) {
  throw "Ficheiro de template nao encontrado: $effortTemplate"
}

if ((-not (Test-Path $effortDestination)) -or $Force) {
  Copy-Item -Path $effortTemplate -Destination $effortDestination -Force:$Force
  Write-Host "OK: $effortDestination"
} else {
  Write-Host "SKIP: $effortDestination ja existe"
}

$claudeGlobalTemplate = Join-Path $templatesDir "CLAUDE_GLOBAL.md"
$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
$claudeGlobalDest = Join-Path $homeDir ".claude\CLAUDE.md"
if (Test-Path $claudeGlobalTemplate) {
  if ((-not (Test-Path $claudeGlobalDest)) -or $Force) {
    Ensure-ParentDirectory -FilePath $claudeGlobalDest
    Copy-Item -Path $claudeGlobalTemplate -Destination $claudeGlobalDest -Force:$Force
    Write-Host "OK: $claudeGlobalDest (CLAUDE global do utilizador criado)"
  } else {
    Write-Host "SKIP: $claudeGlobalDest ja existe (CLAUDE global do utilizador)"
  }
} else {
  Write-Host "SKIP: template CLAUDE_GLOBAL.md nao encontrado em $templatesDir"
}

$initScopeScript = Join-Path $PSScriptRoot "pg_init_scope_intake.ps1"
if (Test-Path $initScopeScript) {
  if ($Force -or (-not $intakeExistedBeforeBootstrap)) {
    & $initScopeScript -RepoPath $repo -ProjectName $RepoName -Force:$Force
  } else {
    Write-Host "SKIP: PG_SCOPE_INTAKE.yaml ja existia; preservado para evitar override do intake"
  }
}

$buildContextScript = Join-Path $PSScriptRoot "pg_build_pg_context.ps1"
if (Test-Path $buildContextScript) {
  $contextContent = Get-Content -Path (Join-Path $repo "PG_CONTEXT.md") -Raw -ErrorAction SilentlyContinue
  $shouldBuildContext = $Force -or (-not $contextExistedBeforeBootstrap) -or (-not $intakeExistedBeforeBootstrap)
  if ($contextContent -match "<!-- PG_AUTO:IDENTIFICACAO:START -->") {
    if ($shouldBuildContext) {
      & $buildContextScript -RepoPath $repo
    } else {
      Write-Host "SKIP: PG_CONTEXT.md e PG_SCOPE_INTAKE.yaml ja existiam; materializacao automatica ignorada para preservar dados existentes"
    }
  } else {
    Write-Host "SKIP: PG_CONTEXT.md sem marcadores PG_AUTO; pg_build_pg_context.ps1 nao executado"
  }
}

$vendorPath = Join-Path $repo "vendor"
$communitySourcePath = Join-Path $vendorPath "odoo_src\community"
$legacyCore = Join-Path $vendorPath "odoo_core"
$syncScript = Join-Path $PSScriptRoot "pg_sync_pg_context.ps1"
if (((Test-Path $communitySourcePath) -or (Test-Path $legacyCore)) -and (Test-Path $syncScript)) {
  & $syncScript -RepoPath $repo
}

$pullDocTemplatesScript = Join-Path $PSScriptRoot "pg_pull_doc_templates.ps1"
if ($RefreshDocTemplatesFromOdoo -and (Test-Path $pullDocTemplatesScript)) {
  Write-Host "INFO: a atualizar doc_templates a partir do Odoo antes do sync partilhado..."
  $pullParams = @{
    PythonExe = $PythonExe
    WorkspaceXmlId = $OdooWorkspaceXmlId
  }
  if (-not [string]::IsNullOrWhiteSpace($OdooBaseUrl)) { $pullParams.BaseUrl = $OdooBaseUrl }
  if (-not [string]::IsNullOrWhiteSpace($OdooDatabase)) { $pullParams.Database = $OdooDatabase }
  if (-not [string]::IsNullOrWhiteSpace($OdooLogin)) { $pullParams.Login = $OdooLogin }

  # O refresh a partir do Odoo é uma actualização de frescura, não uma pré-condição: os
  # `TPL_*.md` estão versionados em doc_templates/ e é essa copia que o sync partilhado leva
  # para o projeto. Deixar a falha abortar o bootstrap era pior do que trabalhar com
  # templates de ha uns dias — o projeto ficava sem doc_templates, sem source Odoo e sem
  # smoke test, porque os passos seguintes nunca corriam.
  try {
    & $pullDocTemplatesScript @pullParams
  }
  catch {
    Write-Host "WARN: refresh de doc_templates a partir do Odoo falhou; bootstrap continua com a copia versionada do framework."
    Write-Host "WARN: detalhe -> $($_.Exception.Message)"
    Write-Host "WARN: para actualizar mais tarde, correr scripts\pg_pull_doc_templates.ps1 no _pg_template e voltar a sincronizar o projeto."
  }
}

$sharedAssetsSyncScript = Join-Path $PSScriptRoot "pg_sync_shared_assets.ps1"
if (Test-Path $sharedAssetsSyncScript) {
  Write-Host "INFO: a sincronizar assets partilhados do template (refresh idempotente)..."
  & $sharedAssetsSyncScript -RepoName $RepoName -RepoPath $repo
}
