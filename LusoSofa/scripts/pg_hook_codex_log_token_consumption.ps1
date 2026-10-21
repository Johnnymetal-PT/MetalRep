<#
.SYNOPSIS
  AUD-03 (Codex): hook do Codex CLI (SessionStart / Stop) que regista o consumo de
  tokens em .pg/tokens/consumption.jsonl, com tokens REAIS lidos do rollout da sessao.

.DESCRIPTION
  Le o payload do hook no stdin (JSON: hook_event_name, session_id, transcript_path,
  cwd, model). Diferencas face ao Codex vs Claude Code:
    - o Codex NAO tem evento SessionEnd; o mais proximo e 'Stop' (fim de TURNO).
    - os tokens NAO vem no payload; vem do rollout JSONL (eventos 'token_count' com
      'total_token_usage' cumulativo da sessao).
  Por isso:
    - SessionStart -> regista session_open (append) via pg_log_token_consumption.ps1.
    - Stop -> le o rollout, extrai o ultimo total_token_usage (cumulativo, REAL ->
      token_measurement='measured'), infere read_mode, e faz UPSERT de um unico
      session_close por session_id (o Stop dispara por turno; o total e cumulativo,
      logo substitui-se em vez de somar).

  A prova de falhas: exit 0 sempre. So regista em repos elegiveis (.pg/ ou PG_CONTEXT.md).

.NOTES
  Registado em .codex/hooks.json (SessionStart + Stop). Requer feature 'hooks' do Codex
  (experimental) e codex recente. Windows via command_windows.
#>
param()

$ErrorActionPreference = 'Stop'

function Read-StdinJson {
  $raw = [Console]::In.ReadToEnd()
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  return ($raw | ConvertFrom-Json)
}

function Read-SharedText {
  # Le um ficheiro tolerando que OUTRO processo o tenha aberto para escrita
  # (FileShare.ReadWrite). Necessario porque o Codex mantem o rollout da sessao
  # bloqueado enquanto a sessao esta ativa; um ReadAllLines normal (FileShare.Read)
  # lanca IOException ("... esta a ser utilizado por outro processo").
  param([string]$Path)
  $fs = $null; $sr = $null
  try {
    $fs = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $sr = New-Object System.IO.StreamReader($fs)
    return $sr.ReadToEnd()
  }
  finally {
    if ($sr) { $sr.Dispose() }
    if ($fs) { $fs.Dispose() }
  }
}

function Get-TokenCountInfo {
  # Devolve o ultimo objeto 'info' de eventos token_count encontrados no rollout,
  # tolerante a duas formas de wrapping: {payload:{type:token_count,info:...}} ou {type:token_count,info:...}
  param([object[]]$Lines)
  $last = $null
  foreach ($line in $Lines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $obj = $line | ConvertFrom-Json } catch { continue }
    $info = $null
    if ($obj.payload -and ([string]$obj.payload.type -eq 'token_count') -and $obj.payload.info) { $info = $obj.payload.info }
    elseif (([string]$obj.type -eq 'token_count') -and $obj.info) { $info = $obj.info }
    if ($info -and $info.total_token_usage) { $last = $info.total_token_usage }
  }
  return $last
}

function Upsert-CodexSessionClose {
  param([string]$ConsumptionPath, [string]$SessionId, [string]$Line)
  $existing = @()
  if (Test-Path $ConsumptionPath) {
    $existing = [System.IO.File]::ReadAllLines($ConsumptionPath)
  }
  $kept = New-Object System.Collections.Generic.List[string]
  foreach ($l in $existing) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    $drop = $false
    try {
      $o = $l | ConvertFrom-Json
      if (([string]$o.agent -eq 'codex') -and ([string]$o.event_type -eq 'session_close') -and ([string]$o.session_id -eq $SessionId)) {
        $drop = $true
      }
    }
    catch { }
    if (-not $drop) { $kept.Add($l) }
  }
  $kept.Add($Line)
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($ConsumptionPath, ([string]::Join([Environment]::NewLine, $kept) + [Environment]::NewLine), $encoding)
}

try {
  $payload = Read-StdinJson
  if ($null -eq $payload) { exit 0 }

  $eventName = [string]$payload.hook_event_name
  $sessionId = [string]$payload.session_id
  $cwd = [string]$payload.cwd
  if ([string]::IsNullOrWhiteSpace($cwd)) { $cwd = (Get-Location).Path }

  $isEligible = (Test-Path (Join-Path $cwd '.pg')) -or (Test-Path (Join-Path $cwd 'PG_CONTEXT.md'))
  if (-not $isEligible) { exit 0 }

  if ($eventName -eq 'SessionStart') {
    $logScript = Join-Path $PSScriptRoot 'pg_log_token_consumption.ps1'
    if (Test-Path $logScript) {
      & $logScript -RepoPath $cwd -EventType session_open -Agent codex -Model ([string]$payload.model) `
        -SessionId $sessionId -ReadMode unknown -TokenMeasurement unknown -Notes 'auto: hook Codex SessionStart' | Out-Null
    }
    exit 0
  }

  if ($eventName -eq 'Stop') {
    $transcriptPath = [string]$payload.transcript_path
    $model = [string]$payload.model
    $inputTokens = 0
    $outputTokens = 0
    $measurement = 'unknown'
    $readMode = 'unknown'
    $navigationMode = 'native'
    $summary = 'Sessao Codex registada automaticamente (hook Stop)'

    if ($transcriptPath -and (Test-Path $transcriptPath)) {
      # Leitura isolada: se falhar (ex.: rollout bloqueado pelo Codex), degradar para
      # tokens 'unknown' MAS continuar a escrever o session_close na mesma.
      try {
        $blob = Read-SharedText -Path $transcriptPath
        $lines = $blob -split "\r?\n"
        $total = Get-TokenCountInfo -Lines $lines
        if ($total) {
          $inputTokens = [int]([math]::Max(0, [int]($total.input_tokens)))
          $outputTokens = [int]([math]::Max(0, [int]($total.output_tokens)))
          $measurement = 'measured'
        }
        if ($blob -match '(?i)xmlrpc|/web/dataset|/json/2/|jsonrpc|odoo-bin|mcp.*odoo|odoo.*api_key') { $readMode = 'api' } else { $readMode = 'mirror' }
        if ($blob -match '(?i)pg_odools_query|odoo_ls_server|\bOdooLS\b') { $navigationMode = 'odools' }
      }
      catch {
        $measurement = 'unknown'
        $readMode = 'unknown'
      }
    }

    $tokensDir = Join-Path $cwd '.pg\tokens'
    if (-not (Test-Path $tokensDir)) { New-Item -ItemType Directory -Path $tokensDir -Force | Out-Null }
    $consumptionPath = Join-Path $tokensDir 'consumption.jsonl'

      # Identidade da sessao.
      #
      # O log e commitado no repositorio e agrega todas as maquinas -- mas ate 2026-09-11 nao
      # dizia QUEM. O `repo_path` e identico em todas (o utilizador local chama-se `Utilizador`
      # em toda a frota) e nao havia campo de operador. Foi isso que obrigou a auditoria do
      # givachoice a pedir extracoes a colegas, maquina a maquina, para reconstruir o que se
      # tinha passado. Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, lacuna L3.
      #
      # `machine` e o discriminador fiavel. `operator` e a identidade DECLARADA no git, e vale
      # o que a configuracao valer: na mesma auditoria, os 205 commits humanos do givachoice
      # saiam todos com o mesmo nome, de tres pessoas diferentes. Um diz onde; o outro diz quem
      # se assumiu ser.
      #
      # Resolvido em linha nos tres escritores, e nao num helper partilhado, porque os hooks
      # sao a prova de falhas por desenho e nao devem ganhar dependencias de ficheiro.
      $identidadeMaquina = [System.Environment]::MachineName
      $identidadeOperador = ''
      $eapIdentidade = $ErrorActionPreference
      $ErrorActionPreference = 'Continue'
      try { $identidadeOperador = (& git -C $cwd config user.email 2>$null | Out-String).Trim() } catch { }
      $ErrorActionPreference = $eapIdentidade
      if ([string]::IsNullOrWhiteSpace($identidadeOperador)) { $identidadeOperador = 'unknown' }

    $event = [ordered]@{
      schema_version = '1.3'
      event_type = 'session_close'
      occurred_at_utc = (Get-Date).ToUniversalTime().ToString('o')
      session_id = $sessionId
      agent = 'codex'
      model = $model
      repo_name = (Split-Path -Leaf $cwd)
      repo_path = $cwd
      machine = $identidadeMaquina
      operator = $identidadeOperador
      session_summary = $summary
      estimated_input_tokens = $inputTokens
      estimated_output_tokens = $outputTokens
      token_measurement = $measurement
      read_mode = $readMode
      navigation_mode = $navigationMode
      notes = 'auto: hook Codex Stop; total_token_usage cumulativo do rollout (upsert por sessao); read_mode heuristico'
    }
    $line = ($event | ConvertTo-Json -Compress -Depth 6)
    Upsert-CodexSessionClose -ConsumptionPath $consumptionPath -SessionId $sessionId -Line $line
    exit 0
  }

  exit 0
}
catch {
  exit 0
}
