param(
  [Parameter(Mandatory = $true)]
  [string]$RepoName,

  [string]$RepoPath,

  [switch]$Force
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

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

function Copy-SharedFile {
  param(
    [string]$Source,
    [string]$Destination,
    # AGENTS.md e CLAUDE.md anunciam-se como sitio para overrides locais. Ver a nota
    # em Merge-PgLocalOverrides (pg_file_io_common.ps1): o sync apagava-os.
    [switch]$PreserveOverrides
  )

  if (-not (Test-Path $Source)) {
    throw "Ficheiro partilhado nao encontrado: $Source"
  }

  Ensure-ParentDirectory -FilePath $Destination

  if ($PreserveOverrides) {
    $frameworkContent = Read-Utf8TextFile -Path $Source
    $existingContent = if (Test-Path $Destination) { Read-Utf8TextFile -Path $Destination } else { $null }
    $merged = Merge-PgLocalOverrides -ExistingContent $existingContent -FrameworkContent $frameworkContent
    Write-Utf8NoBomFile -Path $Destination -Content $merged
    if ($merged -ne $frameworkContent) {
      Write-Host "OK: synced $Destination (overrides locais preservados)"
    }
    else {
      Write-Host "OK: synced $Destination"
    }
    return
  }

  Copy-Item -Path $Source -Destination $Destination -Force
  Write-Host "OK: synced $Destination"
}

function Convert-ToRelativePath {
  param(
    [string]$BasePath,
    [string]$TargetPath
  )

  $baseUri = [System.Uri]([System.IO.Path]::GetFullPath($BasePath).TrimEnd('\') + '\')
  $targetUri = [System.Uri]([System.IO.Path]::GetFullPath($TargetPath))
  return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace('/', '\')
}

function Get-TemplateGitHead {
  param([string]$TemplateRootPath)

  try {
    $head = (& git -C $TemplateRootPath rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($head -join "").Trim())) {
      return ($head -join "").Trim()
    }
  } catch {
    return $null
  }

  return $null
}

$templateRoot = Resolve-TemplateRoot
$templatesDir = Join-Path $templateRoot "templates"
$repo = Resolve-TargetRepo -Name $RepoName -ExplicitPath $RepoPath -TemplateRoot $templateRoot

if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

# O proprio _pg_template tem um .pg_framework que aponta para si mesmo, pelo que qualquer
# deteccao de projeto por presenca do symlink tambem o apanha. Sincroniza-lo seria copiar
# os ficheiros por cima deles proprios: falha em "Cannot overwrite the item ... with itself"
# depois de ja ter substituido o CLAUDE.md do template pelo wrapper de projeto e de ter
# criado AGENTS.md, .agents/, .claude/, .codex/ e .github/ na raiz do framework.
# A guarda fica aqui, no ponto unico de passagem, para valer para todos os chamadores.
$repoNormalized = ([System.IO.Path]::GetFullPath($repo)).TrimEnd([char]92, [char]47)
$templateNormalized = ([System.IO.Path]::GetFullPath($templateRoot)).TrimEnd([char]92, [char]47)
if ($repoNormalized -ieq $templateNormalized) {
  throw "Alvo do sync e o proprio _pg_template ($repo). O framework nao se sincroniza a si mesmo; indicar um repositorio de projeto."
}

$sharedFiles = @(
  @{ Source = Join-Path $templatesDir ".editorconfig"; Destination = Join-Path $repo ".editorconfig" },
  @{ Source = Join-Path $templatesDir ".gitattributes"; Destination = Join-Path $repo ".gitattributes" },
  @{ Source = Join-Path $templatesDir ".github\workflows\pg_refresh_pg_context.yml"; Destination = Join-Path $repo ".github\workflows\pg_refresh_pg_context.yml" },
  @{ Source = Join-Path $templatesDir ".claude\settings.json"; Destination = Join-Path $repo ".claude\settings.json" },
  @{ Source = Join-Path $templatesDir ".codex\hooks.json"; Destination = Join-Path $repo ".codex\hooks.json" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\SKILL.md"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\agents\openai.yaml"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\agents\openai.yaml" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md"; Destination = Join-Path $repo ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\SKILL.md"; Destination = Join-Path $repo ".claude\skills\pg-odoo-navigator\SKILL.md" },
  @{ Source = Join-Path $templatesDir ".agents\skills\pg-odoo-navigator\references\odoo-navigation.md"; Destination = Join-Path $repo ".claude\skills\pg-odoo-navigator\references\odoo-navigation.md" },
  @{ Source = Join-Path $templatesDir "AGENTS.md"; Destination = Join-Path $repo "AGENTS.md" },
  @{ Source = Join-Path $templatesDir "CLAUDE.md"; Destination = Join-Path $repo "CLAUDE.md" },
  @{ Source = Join-Path $templateRoot "config.toml"; Destination = Join-Path $repo "config.toml" }
)

$comOverrides = @('AGENTS.md', 'CLAUDE.md')
foreach ($item in $sharedFiles) {
  $nome = Split-Path -Leaf $item.Destination
  if ($comOverrides -contains $nome) {
    Copy-SharedFile -Source $item.Source -Destination $item.Destination -PreserveOverrides
  }
  else {
    Copy-SharedFile -Source $item.Source -Destination $item.Destination
  }
}

# .gitignore: merge, nunca overwrite. As regras da framework vivem num bloco
# delimitado; o que esta fora e do projeto e sobrevive ao sync. Ver
# Merge-PgGitignoreContent em pg_file_io_common.ps1.
$gitignoreTemplate = Join-Path $templatesDir ".gitignore"
$gitignoreDest = Join-Path $repo ".gitignore"
if (-not (Test-Path $gitignoreTemplate)) {
  throw "Ficheiro partilhado nao encontrado: $gitignoreTemplate"
}

$frameworkGitignore = Read-Utf8TextFile -Path $gitignoreTemplate
$existingGitignore = if (Test-Path $gitignoreDest) { Read-Utf8TextFile -Path $gitignoreDest } else { $null }
$hadBlock = $null -ne (Get-PgGitignoreBlockRules -Content $existingGitignore)
$mergedGitignore = Merge-PgGitignoreContent -ExistingContent $existingGitignore -FrameworkContent $frameworkGitignore

if ($existingGitignore -eq $mergedGitignore) {
  Write-Host "SKIP: $gitignoreDest ja alinhado (bloco da framework sem alteracoes)"
}
else {
  Write-Utf8NoBomFile -Path $gitignoreDest -Content $mergedGitignore
  if (-not $existingGitignore) {
    Write-Host "OK: synced $gitignoreDest (criado com o bloco da framework)"
  }
  elseif ($hadBlock) {
    Write-Host "OK: synced $gitignoreDest (bloco da framework atualizado; regras do projeto preservadas)"
  }
  else {
    Write-Host "OK: synced $gitignoreDest (regras existentes preservadas; bloco da framework acrescentado)"
  }
}

$frameworkLinkScript = Join-Path $PSScriptRoot "pg_link_framework.ps1"
if (Test-Path $frameworkLinkScript) {
  & $frameworkLinkScript -RepoPath $repo
}

$claudeGlobalTemplate = Join-Path $templatesDir "CLAUDE_GLOBAL.md"
$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
$claudeGlobalDest = Join-Path $homeDir ".claude\CLAUDE.md"
if (Test-Path $claudeGlobalTemplate) {
  if (-not (Test-Path $claudeGlobalDest)) {
    Ensure-ParentDirectory -FilePath $claudeGlobalDest
    Copy-Item -Path $claudeGlobalTemplate -Destination $claudeGlobalDest -Force
    Write-Host "OK: $claudeGlobalDest (CLAUDE global do utilizador criado)"
  } else {
    Write-Host "SKIP: $claudeGlobalDest ja existe (CLAUDE global do utilizador)"
  }
}

$docTemplatesSource = Join-Path $templateRoot "doc_templates"
$docTemplatesDest = Join-Path $repo "doc_templates"
if (Test-Path $docTemplatesSource) {
  if (Test-Path $docTemplatesDest) {
    Remove-Item -Path $docTemplatesDest -Recurse -Force
  }
  Copy-Item -Path $docTemplatesSource -Destination $docTemplatesDest -Recurse
  Write-Host "OK: synced doc_templates"
} else {
  Write-Host "SKIP: doc_templates nao encontrado no template"
}

$pgDirectory = Join-Path $repo ".pg"
if (-not (Test-Path $pgDirectory)) {
  New-Item -ItemType Directory -Path $pgDirectory -Force | Out-Null
}

$effortTemplateSource = Join-Path $templatesDir ".pg\PG_EFFORT_SYNC.json"
$effortTemplateDest = Join-Path $repo ".pg\PG_EFFORT_SYNC.json"
if (Test-Path $effortTemplateSource) {
  if (-not (Test-Path $effortTemplateDest)) {
    Copy-Item -Path $effortTemplateSource -Destination $effortTemplateDest -Force
    Write-Host "OK: criado $effortTemplateDest"
  } else {
    Write-Host "SKIP: $effortTemplateDest ja existe"
  }
}

$tokensDirectory = Join-Path $repo ".pg\tokens"
if (-not (Test-Path $tokensDirectory)) {
  New-Item -ItemType Directory -Path $tokensDirectory -Force | Out-Null
}

$tokenConsumptionPath = Join-Path $tokensDirectory "consumption.jsonl"
if (-not (Test-Path $tokenConsumptionPath)) {
  Write-Utf8NoBomFile -Path $tokenConsumptionPath -Content ""
  Write-Host "OK: criado $tokenConsumptionPath"
}

$syncStatePath = Join-Path $repo ".pg\PG_TEMPLATE_SYNC_STATE.json"
$syncState = [ordered]@{
  schema_version = '1.0'
  synced_at = (Get-Date).ToString('o')
  template_root = [System.IO.Path]::GetFullPath($templateRoot)
  template_git_head = (Get-TemplateGitHead -TemplateRootPath $templateRoot)
  framework_link_path = '.pg_framework'
  shared_files = @(
    $sharedFiles | ForEach-Object {
      [ordered]@{
        source = Convert-ToRelativePath -BasePath $templateRoot -TargetPath $_.Source
        destination = Convert-ToRelativePath -BasePath $repo -TargetPath $_.Destination
      }
    }
  )
  doc_templates_synced = [bool](Test-Path $docTemplatesSource)
}

Write-Utf8NoBomFile -Path $syncStatePath -Content (($syncState | ConvertTo-Json -Depth 6) + "`n")
Write-Host "OK: estado de sync atualizado em $syncStatePath"

# A regra no .gitignore e o desversionamento andam juntos: sem isto o ficheiro fica
# ignorado E seguido, e continua a entrar em conflito em cada merge da frota.
Remove-PgTrackedLocalState -RepoPath $repo | Out-Null

Write-Host "OK: sincronizacao de assets partilhados concluida"
