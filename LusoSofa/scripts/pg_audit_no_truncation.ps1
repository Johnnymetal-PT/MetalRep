[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$ReposRoot,
  [string[]]$RepoNames = @(),
  [switch]$IncludeLegacyPaths,
  [string]$ReportPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Path([string]$path) {
  return [System.IO.Path]::GetFullPath($path)
}

function Read-JsonFile([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) {
    return $null
  }
  $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  $data = $null
  try {
    $data = $raw | ConvertFrom-Json -Depth 100
  } catch {
    $data = $raw | ConvertFrom-Json
  }
  return @{
    Raw = $raw
    Data = $data
  }
}

function New-Result([string]$repo, [string]$projectKey, [string]$artifact, [bool]$ok, [string]$detail) {
  return [PSCustomObject]@{
    repo = $repo
    project_key = $projectKey
    artifact = $artifact
    status = $(if ($ok) { "PASS" } else { "FAIL" })
    detail = $detail
  }
}

function Test-ContainsTruncationMarker([string]$text) {
  if (-not $text) { return $false }
  return $text.Contains("...[truncated]...")
}

function Get-StringProp($obj, [string]$name) {
  if ($null -eq $obj) { return "" }
  $prop = $obj.PSObject.Properties[$name]
  if ($null -eq $prop) { return "" }
  return [string]$prop.Value
}

function Audit-TasksPayload($doc, [string]$repo, [string]$projectKey, [string]$artifactLabel) {
  $results = @()
  if ($null -eq $doc) {
    $results += New-Result $repo $projectKey $artifactLabel $false "ficheiro em falta"
    return $results
  }
  $tasks = @($doc.Data.tasks)
  if (@($tasks).Count -eq 0) {
    $results += New-Result $repo $projectKey $artifactLabel $false "sem tasks"
    return $results
  }

  $withDescriptionText = @($tasks | Where-Object { $_.PSObject.Properties.Name -contains "description_text" }).Count
  $missingDescriptionText = @($tasks).Count - $withDescriptionText
  $results += New-Result $repo $projectKey "${artifactLabel}:description_text" ($missingDescriptionText -eq 0) "$withDescriptionText/$(@($tasks).Count) com description_text"

  $truncMarkers = 0
  foreach ($task in $tasks) {
    if (Test-ContainsTruncationMarker(Get-StringProp $task "description")) { $truncMarkers++ }
    if (Test-ContainsTruncationMarker(Get-StringProp $task "description_text")) { $truncMarkers++ }
  }
  $results += New-Result $repo $projectKey "${artifactLabel}:truncation_marker" ($truncMarkers -eq 0) "ocorrencias=$truncMarkers"
  return $results
}

function Audit-ScopePayload($doc, [string]$repo, [string]$projectKey, [string]$artifactLabel) {
  $results = @()
  if ($null -eq $doc) {
    $results += New-Result $repo $projectKey $artifactLabel $false "ficheiro em falta"
    return $results
  }
  $items = @($doc.Data.scope_items)
  if (@($items).Count -eq 0) {
    $results += New-Result $repo $projectKey $artifactLabel $false "sem scope_items"
    return $results
  }

  $withTaskDescription = @($items | Where-Object { $_.PSObject.Properties.Name -contains "task_description" }).Count
  $withTaskDescriptionText = @($items | Where-Object { $_.PSObject.Properties.Name -contains "task_description_text" }).Count
  $results += New-Result $repo $projectKey "${artifactLabel}:task_description" ($withTaskDescription -eq @($items).Count) "$withTaskDescription/$(@($items).Count) com task_description"
  $results += New-Result $repo $projectKey "${artifactLabel}:task_description_text" ($withTaskDescriptionText -eq @($items).Count) "$withTaskDescriptionText/$(@($items).Count) com task_description_text"

  $truncMarkers = 0
  foreach ($item in $items) {
    if (Test-ContainsTruncationMarker(Get-StringProp $item "task_description")) { $truncMarkers++ }
    if (Test-ContainsTruncationMarker(Get-StringProp $item "task_description_text")) { $truncMarkers++ }
  }
  $results += New-Result $repo $projectKey "${artifactLabel}:truncation_marker" ($truncMarkers -eq 0) "ocorrencias=$truncMarkers"
  return $results
}

function Audit-GenericJsonPayload($doc, [string]$repo, [string]$projectKey, [string]$artifactLabel) {
  $results = @()
  if ($null -eq $doc) {
    $results += New-Result $repo $projectKey $artifactLabel $false "ficheiro em falta"
    return $results
  }
  $hasTrunc = Test-ContainsTruncationMarker($doc.Raw)
  $results += New-Result $repo $projectKey "${artifactLabel}:truncation_marker" (-not $hasTrunc) "marker=$hasTrunc"
  return $results
}

$resolvedRoot = Normalize-Path $ReposRoot
if (-not (Test-Path -LiteralPath $resolvedRoot)) {
  throw "ReposRoot nao existe: $resolvedRoot"
}

$repos = @()
if (@($RepoNames).Count -gt 0) {
  foreach ($name in $RepoNames) {
    $path = Join-Path $resolvedRoot $name
    if (Test-Path -LiteralPath $path) {
      $repos += Get-Item -LiteralPath $path
    } else {
      Write-Warning "Repo nao encontrado: $name"
    }
  }
} else {
  $repos = @(Get-ChildItem -LiteralPath $resolvedRoot -Directory)
}

$allResults = @()

foreach ($repoDir in $repos) {
  $repoName = $repoDir.Name
  $repoPath = $repoDir.FullName
  $pgRoot = Join-Path $repoPath ".pg"
  if (-not (Test-Path -LiteralPath $pgRoot)) {
    $allResults += New-Result $repoName "-" ".pg" $false "diretorio .pg em falta"
    continue
  }

  $indexPath = Join-Path $pgRoot "PG_PROJECT_INDEX.json"
  $indexDoc = Read-JsonFile $indexPath

  $projectKeys = @()
  if ($null -ne $indexDoc -and $null -ne $indexDoc.Data.registry) {
    foreach ($item in @($indexDoc.Data.registry)) {
      if ($item.project_key) {
        $projectKeys += [string]$item.project_key
      }
    }
  }

  if (@($projectKeys).Count -eq 0) {
    $projectsDir = Join-Path $pgRoot "projects"
    if (Test-Path -LiteralPath $projectsDir) {
      $projectKeys = @(
        Get-ChildItem -LiteralPath $projectsDir -Directory | ForEach-Object { $_.Name }
      )
    }
  }

  if (@($projectKeys).Count -eq 0) {
    $projectKeys = @("-legacy-")
  }

  foreach ($projectKey in $projectKeys) {
    $isLegacy = $projectKey -eq "-legacy-"
    $base = if ($isLegacy) { $pgRoot } else { Join-Path $pgRoot ("projects\" + $projectKey) }

    if (-not (Test-Path -LiteralPath $base)) {
      $allResults += New-Result $repoName $projectKey "project_base" $false "diretorio em falta: $base"
      continue
    }

    $tasksPath = Join-Path $base "tasks\tasks.json"
    $scopePath = Join-Path $base "PG_SCOPE_SYNC.json"

    $allResults += Audit-TasksPayload (Read-JsonFile $tasksPath) $repoName $projectKey "tasks/tasks.json"
    $allResults += Audit-ScopePayload (Read-JsonFile $scopePath) $repoName $projectKey "PG_SCOPE_SYNC.json"

    $genericArtifacts = @(
      "PG_EFFORT_SYNC.json"
    )

    foreach ($fileName in $genericArtifacts) {
      $primaryPath = Join-Path $base $fileName
      $doc = Read-JsonFile $primaryPath
      if ($null -eq $doc -and -not $isLegacy -and $IncludeLegacyPaths.IsPresent) {
        $doc = Read-JsonFile (Join-Path $pgRoot $fileName)
      }
      $allResults += Audit-GenericJsonPayload $doc $repoName $projectKey $fileName
    }
  }
}

$fails = @($allResults | Where-Object { $_.status -eq "FAIL" })
$passes = @($allResults | Where-Object { $_.status -eq "PASS" })

Write-Host ""
Write-Host "== Auditoria No-Truncation =="
Write-Host ("Repos auditados: {0}" -f (@($repos).Count))
Write-Host ("PASS: {0} | FAIL: {1} | TOTAL: {2}" -f @($passes).Count, @($fails).Count, @($allResults).Count)
Write-Host ""

foreach ($row in $allResults) {
  $line = "{0} | repo={1} | project={2} | artifact={3} | {4}" -f $row.status, $row.repo, $row.project_key, $row.artifact, $row.detail
  if ($row.status -eq "FAIL") {
    Write-Host $line -ForegroundColor Red
  } else {
    Write-Host $line
  }
}

if ($ReportPath) {
  $reportFullPath = Normalize-Path $ReportPath
  $dir = Split-Path -Parent $reportFullPath
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $allResults | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportFullPath -Encoding UTF8
  Write-Host ""
  Write-Host "Relatorio JSON gravado em: $reportFullPath"
}

if (@($fails).Count -gt 0) {
  exit 1
}
exit 0
