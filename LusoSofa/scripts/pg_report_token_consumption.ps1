<#
.SYNOPSIS
  AUD-03: agrega o consumo de tokens registado em .pg/tokens/consumption.jsonl e
  produz um relatorio por projeto/agente/modelo, distinguindo medido vs estimado e
  comparando o custo por modo de leitura (mirror vs api).

.DESCRIPTION
  Torna o objetivo primario (reduzir custo/tempo) mensuravel. Le um repositorio
  (-RepoPath) ou varre uma raiz de repositorios (-RootPath, procura .pg/tokens/
  consumption.jsonl em cada subpasta). Metrica-alvo: tokens por sessao por modo de
  leitura - permite provar que ler do espelho custa menos do que ir a API.

.NOTES
  Records legado (sem event_type) sao contados a parte e nao entram na agregacao por sessao.

  DUAS CONTABILIDADES, NUNCA MISTURADAS. Ate a v2.22.0 o hook do Claude somava
  `cache_read_input_tokens` ao input -- ou seja, o contexto inteiro relido em cada
  turno -- e as sessoes apareciam com centenas de milhoes de tokens. Esses registos
  nao sao comparaveis entre si (o erro cresce com o numero de turnos) nem com os
  actuais. A metrica-alvo passa a ser calculada exclusivamente sobre registos com
  token_accounting = 'unique_input_v2'; o resto e reportado a parte, com o aviso.
#>
param(
  [string]$RepoPath,
  [string]$RootPath,
  [switch]$AsJson,
  [string]$OutputFile
)

$ErrorActionPreference = "Stop"

function Get-ConsumptionFiles {
  param([string]$RepoPath, [string]$RootPath)
  $files = @()
  if (-not [string]::IsNullOrWhiteSpace($RootPath)) {
    $root = [System.IO.Path]::GetFullPath($RootPath)
    if (-not (Test-Path $root)) { throw "RootPath nao encontrado: $root" }
    $files = Get-ChildItem -Path $root -Recurse -Filter "consumption.jsonl" -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match '[\\/]\.pg[\\/]tokens[\\/]consumption\.jsonl$' } |
      ForEach-Object { $_.FullName }
  }
  else {
    $repo = if ([string]::IsNullOrWhiteSpace($RepoPath)) { (Get-Location).Path } else { $RepoPath }
    $repo = [System.IO.Path]::GetFullPath($repo)
    $path = Join-Path $repo ".pg\tokens\consumption.jsonl"
    if (Test-Path $path) { $files = @($path) }
  }
  return $files
}

function ConvertTo-Int {
  param($Value)
  [long]$number = 0
  if ($null -ne $Value -and [long]::TryParse([string]$Value, [ref]$number)) { return $number }
  return [long]0
}

function Get-ObjectValue {
  param($Object, [string]$Name, $Default = $null)
  if ($null -eq $Object) { return $Default }
  $property = $Object.PSObject.Properties[$Name]
  if ($null -eq $property -or $null -eq $property.Value) { return $Default }
  return $property.Value
}

$files = Get-ConsumptionFiles -RepoPath $RepoPath -RootPath $RootPath
if (-not $files -or $files.Count -eq 0) {
  throw "Nenhum consumption.jsonl encontrado (usar -RepoPath ou -RootPath)."
}

$records = @()
$legacyCount = 0
$parseErrors = 0

foreach ($file in $files) {
  $lines = [System.IO.File]::ReadAllLines($file, [System.Text.Encoding]::UTF8)
  foreach ($rawLine in $lines) {
    $line = $rawLine.Trim()
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $obj = $line | ConvertFrom-Json -ErrorAction Stop }
    catch { $parseErrors += 1; continue }

    if ($null -eq $obj.PSObject.Properties['event_type']) { $legacyCount += 1; continue }

    $records += [pscustomobject]@{
      repo        = [string](Get-ObjectValue $obj 'repo_name' '?')
      agent       = [string](Get-ObjectValue $obj 'agent' '?')
      model       = if (-not [string]::IsNullOrWhiteSpace([string](Get-ObjectValue $obj 'model' ''))) { [string](Get-ObjectValue $obj 'model' '') } else { '(sem modelo)' }
      session_id  = [string](Get-ObjectValue $obj 'session_id' '?')
      event_type  = [string](Get-ObjectValue $obj 'event_type' '')
      input       = ConvertTo-Int (Get-ObjectValue $obj 'estimated_input_tokens' 0)
      output      = ConvertTo-Int (Get-ObjectValue $obj 'estimated_output_tokens' 0)
      cache_read  = ConvertTo-Int (Get-ObjectValue $obj 'cache_read_input_tokens' 0)
      measurement = [string](Get-ObjectValue $obj 'token_measurement' 'unknown')
      accounting  = [string](Get-ObjectValue $obj 'token_accounting' 'legado')
      machine     = [string](Get-ObjectValue $obj 'machine' '(desconhecida)')
      operator    = [string](Get-ObjectValue $obj 'operator' '(desconhecido)')
      read_mode   = [string](Get-ObjectValue $obj 'read_mode' 'unknown')
      navigation_mode = [string](Get-ObjectValue $obj 'navigation_mode' 'unknown')
    }
  }
}

# SessionStart tem zero tokens e o Stop/SessionEnd faz upsert de um session_close
# cumulativo. Agregar linhas diretamente contava a mesma sessao em `unknown` e no modo
# final, e podia duplicar closes/progressos legados. Preferir o ultimo close; quando nao
# existe, agregar os progressos legados numa unica linha de sessao.
$sessionRecords = @(
  $records | Group-Object session_id | ForEach-Object {
    $group = @($_.Group)
    $close = @($group | Where-Object event_type -eq 'session_close' | Select-Object -Last 1)
    if ($close.Count -gt 0) { $close[0]; return }
    $progress = @($group | Where-Object event_type -ne 'session_open')
    if ($progress.Count -eq 0) {
      $group | Select-Object -Last 1
      return
    }
    $last = $progress | Select-Object -Last 1
    [pscustomobject]@{
      repo = $last.repo; agent = $last.agent; model = $last.model; session_id = $last.session_id
      event_type = 'session_progress_aggregate'
      input = ($progress | Measure-Object input -Sum).Sum
      output = ($progress | Measure-Object output -Sum).Sum
      cache_read = ($progress | Measure-Object cache_read -Sum).Sum
      measurement = $last.measurement; accounting = $last.accounting
      machine = $last.machine; operator = $last.operator
      read_mode = $last.read_mode; navigation_mode = $last.navigation_mode
    }
  }
)

# Ver a nota em pg_validate_token_consumption.ps1: acima disto nao e uma sessao
# pesada, e um erro de contagem. Fica fora de todas as medias -- uma unica sessao de
# 3,6 mil milhoes de tokens deslocava sozinha o total da frota inteira.
$maxPlausibleSessionTokens = 20000000

$quarantined = @($sessionRecords | Where-Object { ($_.input + $_.output) -gt $maxPlausibleSessionTokens })
$usableRecords = @($sessionRecords | Where-Object { ($_.input + $_.output) -le $maxPlausibleSessionTokens })
$v2Records = @($usableRecords | Where-Object { $_.accounting -eq 'unique_input_v2' })
$legacyAccounting = @($usableRecords | Where-Object { $_.accounting -ne 'unique_input_v2' })

function Group-Sum {
  param([object[]]$Records, [string]$Key)
  $map = [ordered]@{}
  foreach ($r in $Records) {
    $k = [string]$r.$Key
    if (-not $map.Contains($k)) { $map[$k] = [pscustomobject]@{ tokens = 0; sessions = New-Object System.Collections.Generic.HashSet[string] } }
    $map[$k].tokens += ($r.input + $r.output)
    [void]$map[$k].sessions.Add($r.session_id)
  }
  return $map
}

$totalInput = ($usableRecords | Measure-Object -Property input -Sum).Sum
$totalOutput = ($usableRecords | Measure-Object -Property output -Sum).Sum
if ($null -eq $totalInput) { $totalInput = 0 }
if ($null -eq $totalOutput) { $totalOutput = 0 }
$totalTokens = $totalInput + $totalOutput
$sessionCount = $usableRecords.Count

$byNavigationMode = Group-Sum -Records $usableRecords -Key "navigation_mode"
$byMeasurement = Group-Sum -Records $usableRecords -Key "measurement"
$byRepo = Group-Sum -Records $usableRecords -Key "repo"
$byMachine = Group-Sum -Records $usableRecords -Key "machine"
$byOperator = Group-Sum -Records $usableRecords -Key "operator"
$byAgent = Group-Sum -Records $usableRecords -Key "agent"

# A metrica-alvo so se calcula sobre a contabilidade v2. Misturar as duas produzia um
# racio mirror-vs-api que media o comprimento das sessoes, nao o modo de leitura.
$byReadMode = Group-Sum -Records $v2Records -Key "read_mode"

$v2CacheRead = ($v2Records | Measure-Object -Property cache_read -Sum).Sum
if ($null -eq $v2CacheRead) { $v2CacheRead = 0 }

$measuredTokens = if ($byMeasurement.Contains("measured")) { $byMeasurement["measured"].tokens } else { 0 }
$measuredShare = if ($totalTokens -gt 0) { [math]::Round(100.0 * $measuredTokens / $totalTokens, 1) } else { 0 }

$readModeReport = [ordered]@{}
foreach ($k in $byReadMode.Keys) {
  $s = $byReadMode[$k].sessions.Count
  $t = $byReadMode[$k].tokens
  $readModeReport[$k] = [ordered]@{
    tokens             = $t
    sessions           = $s
    avg_tokens_session = if ($s -gt 0) { [math]::Round($t / $s, 0) } else { 0 }
  }
}

if ($AsJson -or -not [string]::IsNullOrWhiteSpace($OutputFile)) {
  $report = [ordered]@{
    generated_at        = (Get-Date).ToUniversalTime().ToString("o")
    files               = $files
    total_input_tokens  = $totalInput
    total_output_tokens = $totalOutput
    total_tokens        = $totalTokens
    sessions            = $sessionCount
    measured_share_pct  = $measuredShare
    legacy_records      = $legacyCount
    parse_errors        = $parseErrors
    sessions_v2_accounting     = $v2Records.Count
    sessions_legacy_accounting = $legacyAccounting.Count
    sessions_quarantined       = $quarantined.Count
    max_plausible_session_tokens = $maxPlausibleSessionTokens
    v2_cache_read_tokens       = $v2CacheRead
    by_read_mode        = $readModeReport
    by_navigation_mode  = ($byNavigationMode.Keys | ForEach-Object { @{ ($_) = $byNavigationMode[$_].tokens } })
    by_measurement      = ($byMeasurement.Keys | ForEach-Object { @{ ($_) = $byMeasurement[$_].tokens } })
    by_repo             = ($byRepo.Keys | ForEach-Object { @{ ($_) = $byRepo[$_].tokens } })
    by_machine          = ($byMachine.Keys | ForEach-Object { @{ ($_) = $byMachine[$_].sessions.Count } })
    by_operator         = ($byOperator.Keys | ForEach-Object { @{ ($_) = $byOperator[$_].sessions.Count } })
    by_agent            = ($byAgent.Keys | ForEach-Object { @{ ($_) = $byAgent[$_].tokens } })
  }
  $json = ($report | ConvertTo-Json -Depth 8)
  if (-not [string]::IsNullOrWhiteSpace($OutputFile)) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($OutputFile), $json + "`n", $encoding)
    Write-Host "OK: relatorio JSON escrito em $OutputFile"
  }
  else {
    Write-Output $json
  }
  return
}

Write-Host "=== RELATORIO DE CONSUMO DE TOKENS ==="
Write-Host ("  Ficheiros lidos : {0}" -f $files.Count)
Write-Host ("  Sessoes         : {0} (contabilidade v2: {1} | anterior: {2})" -f $sessionCount, $v2Records.Count, $legacyAccounting.Count)
Write-Host ("  Tokens totais   : {0} (input {1} + output {2})" -f $totalTokens, $totalInput, $totalOutput)
Write-Host ("  Medido vs total : {0}% medido ({1} tokens)" -f $measuredShare, $measuredTokens)
if ($legacyCount -gt 0) { Write-Host ("  Records legado  : {0} (fora da agregacao por sessao)" -f $legacyCount) }
if ($parseErrors -gt 0) { Write-Host ("  WARN linhas nao parseaveis: {0}" -f $parseErrors) }
if ($quarantined.Count -gt 0) {
  Write-Host ("  EM QUARENTENA   : {0} sessao(oes) acima de {1} tokens, fora de todas as medias" -f $quarantined.Count, $maxPlausibleSessionTokens)
}

Write-Host ""
Write-Host "  Por modo de leitura (metrica-alvo: tokens/sessao, so contabilidade v2):"
if ($v2Records.Count -eq 0) {
  Write-Host "    SEM DADOS. Nenhuma sessao foi ainda registada com a contabilidade corrigida"
  Write-Host "    na v2.22.0. Ate haver sessoes v2 suficientes, a comparacao entre ler do"
  Write-Host "    espelho e ir a API NAO esta demonstrada: os registos anteriores somavam a"
  Write-Host "    releitura do contexto em cada turno, logo medem sobretudo a duracao da"
  Write-Host "    sessao. Nao usar o historico para justificar o custo do espelho."
}
else {
  foreach ($k in $readModeReport.Keys) {
    Write-Host ("    {0,-8} tokens={1,-10} sessoes={2,-4} avg/sessao={3}" -f $k, $readModeReport[$k].tokens, $readModeReport[$k].sessions, $readModeReport[$k].avg_tokens_session)
  }
  Write-Host ("    (releituras de cache, fora do volume: {0} tokens)" -f $v2CacheRead)
}

if ($legacyAccounting.Count -gt 0) {
  Write-Host ""
  Write-Host ("  AVISO: {0} sessao(oes) com a contabilidade anterior a v2.22.0. Entram nos totais" -f $legacyAccounting.Count)
  Write-Host "  por projeto e por agente, mas NAO na metrica-alvo: o input inclui as releituras"
  Write-Host "  de cache, logo o erro cresce com o numero de turnos e as sessoes nao sao"
  Write-Host "  comparaveis entre si. O log e append-only e nao se reescreve."
}

Write-Host ""
Write-Host "  Por modo de navegacao:"
foreach ($k in $byNavigationMode.Keys) {
  Write-Host ("    {0,-10} tokens={1,-10} sessoes={2}" -f $k, $byNavigationMode[$k].tokens, $byNavigationMode[$k].sessions.Count)
}

Write-Host ""
Write-Host "  Por projeto:"
foreach ($k in $byRepo.Keys) { Write-Host ("    {0,-28} tokens={1}" -f $k, $byRepo[$k].tokens) }

Write-Host ""
Write-Host "  Por maquina (sessoes):"
foreach ($k in $byMachine.Keys) { Write-Host ("    {0,-28} {1}" -f $k, $byMachine[$k].sessions.Count) }

Write-Host ""
Write-Host "  Por operador declarado no git (sessoes):"
foreach ($k in $byOperator.Keys) { Write-Host ("    {0,-28} {1}" -f $k, $byOperator[$k].sessions.Count) }
if ($byOperator.Contains('(desconhecido)')) {
  Write-Host "    NOTA: sessoes anteriores a v2.25.0 nao registavam identidade; sem ela nao se sabe quem"
  Write-Host "    fez o trabalho, e foi isso que obrigou a auditoria do givachoice a pedir extracoes"
  Write-Host "    maquina a maquina. O operador e a identidade DECLARADA no git, nao prova de autoria."
}

Write-Host ""
Write-Host "  Por agente:"
foreach ($k in $byAgent.Keys) { Write-Host ("    {0,-10} tokens={1}" -f $k, $byAgent[$k].tokens) }
