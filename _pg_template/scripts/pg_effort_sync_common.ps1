. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Resolve-EffortSyncPath {
  param(
    [string]$RepositoryPath,
    [string]$ExplicitEffortPath
  )

  if ($ExplicitEffortPath) {
    return [System.IO.Path]::GetFullPath($ExplicitEffortPath)
  }

  return Join-Path ([System.IO.Path]::GetFullPath($RepositoryPath)) ".pg\PG_EFFORT_SYNC.json"
}

function Get-EffortSyncData {
  param([string]$Path)

  try {
    return (Read-Utf8JsonFile -Path $Path)
  }
  catch {
    throw "PG_EFFORT_SYNC.json invalido ou com JSON mal formado: $Path"
  }
}

function Assert-EffortRequiredStringProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property -or [string]::IsNullOrWhiteSpace([string]$property.Value)) {
    throw "Campo obrigatorio em falta ou vazio no PG_EFFORT_SYNC.json: $PropertyName"
  }
}

function Assert-EffortRequiredValueProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property -or $null -eq $property.Value -or [string]::IsNullOrWhiteSpace([string]$property.Value)) {
    throw "Campo obrigatorio em falta ou vazio no PG_EFFORT_SYNC.json: $PropertyName"
  }
}

function Assert-EffortObjectProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property -or $null -eq $property.Value) {
    throw "Objeto obrigatorio em falta no PG_EFFORT_SYNC.json: $PropertyName"
  }

  if ($property.Value -isnot [pscustomobject]) {
    throw "Campo com tipo invalido no PG_EFFORT_SYNC.json. Esperado objeto: $PropertyName"
  }

  return [pscustomobject]$property.Value
}

function Assert-EffortArrayProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property) {
    throw "Array obrigatorio em falta no PG_EFFORT_SYNC.json: $PropertyName"
  }

  if ($property.Value -isnot [System.Array]) {
    throw "Campo com tipo invalido no PG_EFFORT_SYNC.json. Esperado array: $PropertyName"
  }

  return @($property.Value)
}

function Assert-EffortNumericProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property -or $null -eq $property.Value) {
    throw "Campo numerico obrigatorio em falta no PG_EFFORT_SYNC.json: $PropertyName"
  }

  if ($property.Value -isnot [byte] -and $property.Value -isnot [int16] -and $property.Value -isnot [int32] -and $property.Value -isnot [int64] -and $property.Value -isnot [decimal] -and $property.Value -isnot [double] -and $property.Value -isnot [single]) {
    throw "Campo numerico com tipo invalido no PG_EFFORT_SYNC.json: $PropertyName"
  }
}

function Assert-EffortDateProperty {
  param(
    [pscustomobject]$Data,
    [string]$PropertyName
  )

  $property = $Data.PSObject.Properties[$PropertyName]
  if (-not $property -or [string]::IsNullOrWhiteSpace([string]$property.Value)) {
    throw "Campo de data obrigatorio em falta ou vazio no PG_EFFORT_SYNC.json: $PropertyName"
  }

  [DateTimeOffset]$parsed = [DateTimeOffset]::MinValue
  if (-not [DateTimeOffset]::TryParse([string]$property.Value, [ref]$parsed)) {
    throw "Campo de data com formato invalido no PG_EFFORT_SYNC.json: $PropertyName"
  }
}

function Assert-EffortSyncContract {
  param([pscustomobject]$Data)

  foreach ($propertyName in @(
      "schema_version",
      "project_name",
      "effort_period_start",
      "effort_period_end",
      "effort_currency"
    )) {
    Assert-EffortRequiredStringProperty -Data $Data -PropertyName $propertyName
  }
  Assert-EffortRequiredValueProperty -Data $Data -PropertyName "project_id"

  $summary = Assert-EffortObjectProperty -Data $Data -PropertyName "summary"
  foreach ($propertyName in @(
      "planned_hours_total",
      "logged_hours_total",
      "remaining_hours_total",
      "variance_hours_total"
    )) {
    Assert-EffortNumericProperty -Data $summary -PropertyName $propertyName
  }

  $workstreams = Assert-EffortArrayProperty -Data $Data -PropertyName "workstreams"
  foreach ($workstream in $workstreams) {
    if ($workstream -isnot [pscustomobject]) {
      throw "Array workstreams com item invalido no PG_EFFORT_SYNC.json. Esperado objeto."
    }

    foreach ($propertyName in @(
        "workstream_id",
        "name"
      )) {
      Assert-EffortRequiredStringProperty -Data $workstream -PropertyName $propertyName
    }

    foreach ($propertyName in @(
        "planned_hours",
        "logged_hours",
        "remaining_hours",
        "variance_hours"
      )) {
      Assert-EffortNumericProperty -Data $workstream -PropertyName $propertyName
    }
  }

  $sourceMetadata = Assert-EffortObjectProperty -Data $Data -PropertyName "source_metadata"
  foreach ($propertyName in @(
      "source_system",
      "source_model",
      "sync_trigger",
      "sync_published_by",
      "repo_branch",
      "payload_hash"
    )) {
    Assert-EffortRequiredStringProperty -Data $sourceMetadata -PropertyName $propertyName
  }
  Assert-EffortRequiredValueProperty -Data $sourceMetadata -PropertyName "source_record_id"
  Assert-EffortDateProperty -Data $sourceMetadata -PropertyName "sync_published_at"

  return $Data
}
