<#
.SYNOPSIS
  Gera e valida a configuracao local do Odoo Language Server para um repositorio PG.

.DESCRIPTION
  Resolve a versao a partir de PG_CONTEXT.md ou do source ligado em vendor/odoo_src,
  descobre roots de addons versionados e escreve odools.toml com paths locais. O
  ficheiro e deliberadamente local/ignorado porque contem paths absolutos da maquina.
#>
param(
  [string]$RepoPath = (Get-Location).Path,
  [string]$OdooLsBinary,
  [switch]$Force,
  [switch]$CheckOnly,
  [switch]$InstallVsCodeExtension,
  [switch]$AsJson
)

$ErrorActionPreference = 'Stop'

function Convert-ToTomlPath {
  param([string]$Path)
  return ([System.IO.Path]::GetFullPath($Path).Replace('\', '/').Replace('"', '\"'))
}

function Get-OdooVersion {
  param([string]$RepoRoot, [string]$SourceRoot)

  $contextPath = Join-Path $RepoRoot 'PG_CONTEXT.md'
  if (Test-Path $contextPath) {
    $context = Get-Content -Path $contextPath -Raw -ErrorAction SilentlyContinue
    $patterns = @(
      '(?im)^\s*[-*]?\s*Vers[aã]o\s+do\s+Odoo\s*:\s*([0-9]{2})(?:\.0|e)?\s*$',
      '(?im)^\s*[-*]?\s*(?:Odoo\s+)?(?:version|vers[aã]o|s[eé]rie|series?)\s*[:=]\s*["'']?([0-9]{2})(?:\.0|e)?'
    )
    foreach ($pattern in $patterns) {
      $match = [regex]::Match($context, $pattern)
      if ($match.Success) { return ($match.Groups[1].Value + '.0') }
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($SourceRoot)) {
    $target = Get-Item -LiteralPath $SourceRoot -Force -ErrorAction SilentlyContinue
    if ($target) {
      $candidate = if ($target.ResolvedTarget) { Split-Path -Leaf $target.ResolvedTarget } else { Split-Path -Leaf $target.FullName }
      if ($candidate -match '^([0-9]{2})(?:\.0|e)?$') { return ($Matches[1] + '.0') }
    }

    $releasePath = Join-Path $SourceRoot 'community\odoo\release.py'
    if (Test-Path $releasePath) {
      $release = Get-Content -Path $releasePath -Raw -ErrorAction SilentlyContinue
      $match = [regex]::Match($release, '(?m)^\s*version_info\s*=\s*\(\s*([0-9]{2})\s*,')
      if ($match.Success) { return ($match.Groups[1].Value + '.0') }
    }
  }

  return $null
}

function Resolve-OdooSource {
  param([string]$RepoRoot)

  $candidates = @(
    (Join-Path $RepoRoot 'vendor\odoo_src'),
    (Join-Path $RepoRoot 'vendor\odoo_core')
  )
  foreach ($candidate in $candidates) {
    if (-not (Test-Path $candidate)) { continue }
    $community = Join-Path $candidate 'community'
    if ((Test-Path (Join-Path $community 'odoo')) -and (Test-Path (Join-Path $community 'addons'))) {
      return [pscustomobject]@{ Root = $candidate; Community = $community; Enterprise = (Join-Path $candidate 'enterprise') }
    }
    if ((Test-Path (Join-Path $candidate 'odoo')) -and (Test-Path (Join-Path $candidate 'addons'))) {
      return [pscustomobject]@{ Root = $candidate; Community = $candidate; Enterprise = $null }
    }
  }
  return $null
}

function Get-AddonRoots {
  param([string]$RepoRoot, [object]$Source)

  $roots = New-Object System.Collections.Generic.HashSet[string] ([System.StringComparer]::OrdinalIgnoreCase)
  [void]$roots.Add([System.IO.Path]::GetFullPath($RepoRoot))
  [void]$roots.Add([System.IO.Path]::GetFullPath((Join-Path $Source.Community 'addons')))
  $odooAddons = Join-Path $Source.Community 'odoo\addons'
  if (Test-Path $odooAddons) { [void]$roots.Add([System.IO.Path]::GetFullPath($odooAddons)) }
  if ($Source.Enterprise -and (Test-Path $Source.Enterprise)) { [void]$roots.Add([System.IO.Path]::GetFullPath($Source.Enterprise)) }

  try {
    $manifestFiles = @(& git -C $RepoRoot ls-files '*__manifest__.py' 2>$null)
    foreach ($relative in $manifestFiles) {
      if ([string]::IsNullOrWhiteSpace($relative) -or $relative -match '^(vendor|\.pg_framework|\.pg)/') { continue }
      $moduleDir = Split-Path -Parent (Join-Path $RepoRoot $relative)
      $addonRoot = Split-Path -Parent $moduleDir
      if ($addonRoot -and (Test-Path $addonRoot)) { [void]$roots.Add([System.IO.Path]::GetFullPath($addonRoot)) }
    }
  }
  catch { }

  return @($roots | Sort-Object)
}

function Resolve-OdooLsBinary {
  param([string]$ExplicitPath)

  if ($ExplicitPath) {
    $resolved = [System.IO.Path]::GetFullPath($ExplicitPath)
    if (Test-Path $resolved) { return $resolved }
    throw "Binario OdooLS nao encontrado: $resolved"
  }
  $command = Get-Command 'odoo_ls_server' -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }

  $profileRoot = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
  $extensionsRoot = Join-Path $profileRoot '.vscode\extensions'
  if (Test-Path $extensionsRoot) {
    $binary = Get-ChildItem -Path $extensionsRoot -Directory -Filter 'odoo.odoo-*' -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending |
      ForEach-Object { Join-Path $_.FullName 'odoo_ls_server.exe' } |
      Where-Object { Test-Path $_ } |
      Select-Object -First 1
    if ($binary) { return $binary }
  }
  return $null
}

function Ensure-LocalGitExcludes {
  param([string]$RepoRoot)

  $excludePath = Join-Path $RepoRoot '.git\info\exclude'
  if (-not (Test-Path (Split-Path -Parent $excludePath))) { return }
  $existing = if (Test-Path $excludePath) { Get-Content -Path $excludePath -Raw -ErrorAction SilentlyContinue } else { '' }
  $lines = New-Object System.Collections.Generic.List[string]
  if ($existing -notmatch '(?m)^/odools\.toml\s*$') { $lines.Add('/odools.toml') }
  if ($existing -notmatch '(?m)^/\.pg/odools/\s*$') { $lines.Add('/.pg/odools/') }
  if ($lines.Count -eq 0) { return }
  $prefix = if ([string]::IsNullOrWhiteSpace($existing) -or $existing.EndsWith("`n")) { '' } else { "`r`n" }
  $addition = $prefix + "# PG OdooLS local files`r`n" + (($lines -join "`r`n") + "`r`n")
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  if (Test-Path $excludePath) { [System.IO.File]::AppendAllText($excludePath, $addition, $utf8) }
  else { [System.IO.File]::WriteAllText($excludePath, $addition, $utf8) }
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repo)) { throw "Repositorio nao encontrado: $repo" }

if ($InstallVsCodeExtension) {
  $code = Get-Command 'code' -ErrorAction SilentlyContinue
  if (-not $code) { throw 'VS Code CLI nao encontrado; nao foi possivel instalar Odoo.odoo' }
  & $code.Source --install-extension Odoo.odoo | Out-Host
  if ($LASTEXITCODE -ne 0) { throw 'Falhou a instalacao da extensao Odoo.odoo' }
}

$source = Resolve-OdooSource -RepoRoot $repo
if (-not $source) { throw "Source Odoo nao encontrado em vendor/odoo_src ou vendor/odoo_core: $repo" }
$version = Get-OdooVersion -RepoRoot $repo -SourceRoot $source.Root
if (-not $version) { throw "Versao Odoo nao resolvida para $repo" }
$addonRoots = @(Get-AddonRoots -RepoRoot $repo -Source $source)
$binary = Resolve-OdooLsBinary -ExplicitPath $OdooLsBinary

$configPath = Join-Path $repo 'odools.toml'
$statePath = Join-Path $repo '.pg\odools\setup.json'
$existingGenerated = $false
if (Test-Path $configPath) {
  $firstLine = Get-Content -Path $configPath -TotalCount 1 -ErrorAction SilentlyContinue
  $existingGenerated = ($firstLine -eq '# Generated by pg_setup_odools.ps1; local machine paths; do not commit.')
  if (-not $existingGenerated -and -not $Force) {
    throw "odools.toml existente nao foi gerado pela framework; usar -Force apenas se pretender substitui-lo: $configPath"
  }
}

$result = [ordered]@{
  schema_version = '1.0'
  repo_path = $repo
  version = $version
  community_path = [System.IO.Path]::GetFullPath($source.Community)
  enterprise_path = if ($source.Enterprise -and (Test-Path $source.Enterprise)) { [System.IO.Path]::GetFullPath($source.Enterprise) } else { $null }
  addons_paths = $addonRoots
  config_path = $configPath
  binary_path = $binary
  binary_available = [bool]$binary
  vscode_extension_installed = [bool](Get-ChildItem (Join-Path ($(if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME })) '.vscode\extensions') -Directory -Filter 'odoo.odoo-*' -ErrorAction SilentlyContinue | Select-Object -First 1)
  check_only = [bool]$CheckOnly
}

if (-not $CheckOnly) {
  Ensure-LocalGitExcludes -RepoRoot $repo
  $tomlPaths = $addonRoots | ForEach-Object { '  "' + (Convert-ToTomlPath $_) + '"' }
  $config = @(
    '# Generated by pg_setup_odools.ps1; local machine paths; do not commit.'
    '# Re-run after changing Odoo version, source links, or addon roots.'
    ''
    '[[config]]'
    'name = "default"'
    ('odoo_path = "' + (Convert-ToTomlPath $source.Community) + '"')
    'addons_paths = ['
    (($tomlPaths -join ",`n"))
    ']'
    'python_path = "python"'
    'diag_missing_imports = "only_odoo"'
    'file_cache = true'
    'auto_refresh_delay = 3000'
    'ac_filter_model_names = true'
  ) -join "`r`n"

  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($configPath, ($config + "`r`n"), $utf8)
  $stateDir = Split-Path -Parent $statePath
  if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
  [System.IO.File]::WriteAllText($statePath, (($result | ConvertTo-Json -Depth 6) + "`n"), $utf8)
}

if ($AsJson) { $result | ConvertTo-Json -Depth 6 }
else {
  Write-Host ("OK: Odoo {0} -> {1}" -f $version, $source.Community)
  Write-Host ("OK: {0} addon roots" -f $addonRoots.Count)
  if ($binary) { Write-Host "OK: OdooLS $binary" } else { Write-Host 'WARN: binario OdooLS nao encontrado; instalar a extensao VS Code Odoo.odoo' }
  if ($CheckOnly) { Write-Host 'OK: validacao concluida sem escrever ficheiros' }
  else { Write-Host "OK: configuracao local escrita em $configPath" }
}
