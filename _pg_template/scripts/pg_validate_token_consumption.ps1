param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  [string]$ConsumptionPath
)

$ErrorActionPreference = "Stop"

# System.Web.Extensions so existe no .NET Framework (Windows PowerShell 5.1); em
# PowerShell 7 (macOS/Linux e Windows) o bootstrap falhava ao carregar a assembly.
# Em 7+ usa-se ConvertFrom-Json -AsHashtable, que devolve o mesmo contrato
# (ContainsKey + indexador); o 5.1 nao tem -AsHashtable e mantem o serializer.
$jsonSerializer = $null
if ($PSVersionTable.PSVersion.Major -lt 6) {
  Add-Type -AssemblyName System.Web.Extensions
  $jsonSerializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
}

function ConvertFrom-JsonLine {
  param([string]$Line)
  if ($jsonSerializer) {
    return $jsonSerializer.DeserializeObject($Line)
  }
  $parsed = ConvertFrom-Json -InputObject $Line -AsHashtable
  if ($parsed -isnot [System.Collections.IDictionary]) {
    throw "JSON nao e um objecto."
  }
  return $parsed
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

if ([string]::IsNullOrWhiteSpace($ConsumptionPath)) {
  $ConsumptionPath = Join-Path $repo ".pg/tokens/consumption.jsonl"
}
else {
  $ConsumptionPath = [System.IO.Path]::GetFullPath($ConsumptionPath)
}

if (-not (Test-Path $ConsumptionPath)) {
  throw "Ficheiro de consumo nao encontrado: $ConsumptionPath"
}

# Limite de plausibilidade de uma sessao.
#
# Nao e um numero de gosto: a janela de contexto maior em uso tem 1 milhao de tokens,
# e mesmo uma sessao muito longa, com varias compactacoes, nao processa 20 milhoes de
# tokens DISTINTOS. Um valor acima disto nao e uma sessao pesada -- e um erro de
# contagem, tipicamente a soma das releituras de cache turno a turno.
#
# Isto existe porque o validador ja tinha visto o sintoma e concluiu o contrario: em
# 2026-08 apanhou 2 676 726 927 tokens numa linha do givachoice, diagnosticou o
# problema como sendo o cast [int] do proprio validador, alargou-o para [long] e deu
# a linha por valida. O formato estava certo; o numero e que era impossivel. Validar
# a forma sem validar a grandeza deixa passar exactamente este tipo de defeito.
$maxPlausibleSessionTokens = 20000000

$lines = [System.IO.File]::ReadAllLines($ConsumptionPath, [System.Text.Encoding]::UTF8)
$lineNumber = 0
$eventsBySession = @{}
$validCount = 0
$implausible = New-Object System.Collections.Generic.List[string]

foreach ($rawLine in $lines) {
  $lineNumber += 1
  $line = $rawLine.Trim()
  if ([string]::IsNullOrWhiteSpace($line)) {
    continue
  }

  try {
    $obj = ConvertFrom-JsonLine -Line $line
  }
  catch {
    throw "Linha $lineNumber invalida: JSON nao parseavel."
  }

  $isLegacyRecord = (
    (-not $obj.ContainsKey("schema_version")) -and
    $obj.ContainsKey("date") -and
    $obj.ContainsKey("agent") -and
    $obj.ContainsKey("model") -and
    $obj.ContainsKey("session_summary")
  )

  if ($isLegacyRecord) {
    $agentLegacy = [string]$obj["agent"]
    if (@("codex", "claude", "gemini", "antigravity") -notcontains $agentLegacy) {
      throw "Linha $lineNumber invalida: agent '$agentLegacy' invalido no formato legado."
    }

    $summaryLegacy = [string]$obj["session_summary"]
    if ([string]::IsNullOrWhiteSpace($summaryLegacy)) {
      throw "Linha $lineNumber invalida: session_summary vazio no formato legado."
    }

    $inputLegacy = 0
    $outputLegacy = 0
    try { $inputLegacy = [int]$obj["estimated_input_tokens"] } catch { throw "Linha $lineNumber invalida: estimated_input_tokens nao inteiro no formato legado." }
    try { $outputLegacy = [int]$obj["estimated_output_tokens"] } catch { throw "Linha $lineNumber invalida: estimated_output_tokens nao inteiro no formato legado." }
    if ($inputLegacy -lt 0 -or $outputLegacy -lt 0) {
      throw "Linha $lineNumber invalida: tokens negativos no formato legado."
    }

    $validCount += 1
    continue
  }

  if (-not $obj.ContainsKey("schema_version")) { throw "Linha $lineNumber invalida: schema_version em falta." }
  if (-not $obj.ContainsKey("event_type")) { throw "Linha $lineNumber invalida: event_type em falta." }
  if (-not $obj.ContainsKey("occurred_at_utc")) { throw "Linha $lineNumber invalida: occurred_at_utc em falta." }
  if (-not $obj.ContainsKey("session_id")) { throw "Linha $lineNumber invalida: session_id em falta." }
  if (-not $obj.ContainsKey("agent")) { throw "Linha $lineNumber invalida: agent em falta." }
  if (-not $obj.ContainsKey("estimated_input_tokens")) { throw "Linha $lineNumber invalida: estimated_input_tokens em falta." }
  if (-not $obj.ContainsKey("estimated_output_tokens")) { throw "Linha $lineNumber invalida: estimated_output_tokens em falta." }

  $schemaVersion = [string]$obj["schema_version"]
  $eventType = [string]$obj["event_type"]
  $occurredAtRaw = $obj["occurred_at_utc"]
  $occurredAt = [string]$occurredAtRaw
  $sessionId = [string]$obj["session_id"]
  $agent = [string]$obj["agent"]
  $summary = if ($obj.ContainsKey("session_summary")) { [string]$obj["session_summary"] } else { "" }

  if (@("1.0", "1.1", "1.2", "1.3") -notcontains $schemaVersion) { throw "Linha $lineNumber invalida: schema_version '$schemaVersion' nao suportada." }
  if (@("session_open", "session_progress", "session_close") -notcontains $eventType) { throw "Linha $lineNumber invalida: event_type '$eventType' invalido." }
  if ([string]::IsNullOrWhiteSpace($sessionId)) { throw "Linha $lineNumber invalida: session_id vazio." }
  if (@("codex", "claude", "gemini", "antigravity") -notcontains $agent) { throw "Linha $lineNumber invalida: agent '$agent' invalido." }

  # Campos opcionais (schema 1.1): validar valor apenas se presentes
  if ($obj.ContainsKey("token_measurement")) {
    $tm = [string]$obj["token_measurement"]
    if (@("estimated", "measured", "unknown") -notcontains $tm) { throw "Linha $lineNumber invalida: token_measurement '$tm' invalido." }
  }
  if ($obj.ContainsKey("read_mode")) {
    $rm = [string]$obj["read_mode"]
    if (@("mirror", "api", "mixed", "unknown") -notcontains $rm) { throw "Linha $lineNumber invalida: read_mode '$rm' invalido." }
  }

  # Campos do schema 1.3: identidade. Sao texto livre (nome de maquina, email do git),
  # por isso valida-se que existem e nao sao vazios -- nao o seu conteudo.
  foreach ($campoIdentidade in @("machine", "operator")) {
    if ($obj.ContainsKey($campoIdentidade)) {
      if ([string]::IsNullOrWhiteSpace([string]$obj[$campoIdentidade])) {
        throw "Linha $lineNumber invalida: $campoIdentidade presente mas vazio (usar 'unknown' quando nao se sabe)."
      }
    }
  }

  # Campos do schema 1.2
  $accounting = "legado"
  if ($obj.ContainsKey("token_accounting")) {
    $accounting = [string]$obj["token_accounting"]
    if (@("unique_input_v2", "cache_summed_v1", "unknown") -notcontains $accounting) {
      throw "Linha $lineNumber invalida: token_accounting '$accounting' invalido."
    }
  }
  foreach ($cacheField in @("cache_read_input_tokens", "cache_creation_input_tokens")) {
    if ($obj.ContainsKey($cacheField)) {
      $cacheValue = [long]0
      try { $cacheValue = [long]$obj[$cacheField] } catch { throw "Linha $lineNumber invalida: $cacheField nao inteiro." }
      if ($cacheValue -lt 0) { throw "Linha $lineNumber invalida: $cacheField negativo." }
    }
  }

  # Em PowerShell 7 o ConvertFrom-Json ja converte datas ISO em DateTime; voltar a
  # fazer parse do texto dependeria da cultura da maquina (ex.: pt-PT e 09/28).
  if ($occurredAtRaw -isnot [DateTime] -and $occurredAtRaw -isnot [DateTimeOffset]) {
    try {
      [void][DateTimeOffset]::Parse($occurredAt)
    }
    catch {
      throw "Linha $lineNumber invalida: occurred_at_utc invalido."
    }
  }

  # [long] e nao [int]: um [int] do PowerShell vai ate 2 147 483 647 e um contador de tokens
  # ultrapassa-o com facilidade. Um log real da frota (givachoice, 03/08) tinha 2 676 726 927 em
  # `estimated_input_tokens` e o validador rejeitava a linha com "nao inteiro" — a linha era valida
  # e o defeito era do cast. Uma mensagem de erro que acusa os dados de um problema do validador
  # manda quem a le procurar no sitio errado.
  $inputTokens = [long]0
  $outputTokens = [long]0
  try { $inputTokens = [long]$obj["estimated_input_tokens"] } catch { throw "Linha $lineNumber invalida: estimated_input_tokens nao inteiro." }
  try { $outputTokens = [long]$obj["estimated_output_tokens"] } catch { throw "Linha $lineNumber invalida: estimated_output_tokens nao inteiro." }
  if ($inputTokens -lt 0 -or $outputTokens -lt 0) { throw "Linha $lineNumber invalida: tokens negativos." }

  if (($eventType -eq "session_progress" -or $eventType -eq "session_close") -and [string]::IsNullOrWhiteSpace($summary)) {
    throw "Linha $lineNumber invalida: session_summary obrigatorio para $eventType."
  }

  # Grandeza: AVISO e nao erro, pela mesma razao que a orfandade -- o ficheiro e
  # append-only e o passado nao se reescreve. O que interessa e que deixe de passar
  # despercebido, e que um valor destes escrito HOJE (ja com contabilidade v2) seja
  # nomeado como defeito e nao como sessao pesada.
  if (($inputTokens + $outputTokens) -gt $maxPlausibleSessionTokens) {
    $implausible.Add(("linha {0}: {1} tokens (contabilidade: {2})" -f $lineNumber, ($inputTokens + $outputTokens), $accounting))
  }

  if (-not $eventsBySession.ContainsKey($sessionId)) {
    $eventsBySession[$sessionId] = @()
  }
  $eventsBySession[$sessionId] += $eventType
  $validCount += 1
}

# Emparelhamento de eventos: AVISO, nao erro.
#
# Um 'session_progress'/'session_close' sem 'session_open' e um defeito de
# HISTORICO: o ficheiro e append-only, pelo que nao ha correccao possivel sem
# reescrever o passado. Tratado como erro, reprovava o smoke test do repo para
# sempre -- 9 dos 23 repos da frota estavam nesse estado, e um check
# permanentemente vermelho treina qualquer pessoa a ignorar o resultado. Os
# eventos continuam utilizaveis para agregacao de consumo; o que falta e o par.
# A causa raiz (o logger inventar um session_id novo) esta fechada em
# pg_log_token_consumption.ps1, logo isto nao volta a acumular.
# Erros de formato/schema continuam a ser erros, porque esses sim sao corrigiveis.
$warningCount = 0
foreach ($sessionId in $eventsBySession.Keys) {
  $events = @($eventsBySession[$sessionId])
  if (($events -contains "session_progress" -or $events -contains "session_close") -and -not ($events -contains "session_open")) {
    $warningCount += 1
    Write-Warning "Sessao $sessionId sem session_open (eventos: $($events -join ', ')). Historico anterior ao fecho da causa raiz; registar sempre o session_open ou passar -SessionId em pg_log_token_consumption.ps1."
  }
}

if ($implausible.Count -gt 0) {
  Write-Warning ("{0} evento(s) acima do limite de plausibilidade ({1} tokens numa sessao). Acima deste valor nao e uma sessao pesada, e um erro de contagem -- tipicamente a soma das releituras de cache turno a turno, corrigida na v2.22.0. Registos com token_accounting 'cache_summed_v1' ou sem o campo sao historico e nao se corrigem (log append-only); um registo 'unique_input_v2' nesta lista e um defeito activo no hook." -f $implausible.Count, $maxPlausibleSessionTokens)
  foreach ($item in ($implausible | Select-Object -First 10)) { Write-Warning "  $item" }
  if ($implausible.Count -gt 10) { Write-Warning ("  (mais {0} nao listados)" -f ($implausible.Count - 10)) }
}

$summaryParts = New-Object System.Collections.Generic.List[string]
if ($warningCount -gt 0) { $summaryParts.Add("$warningCount sessao(oes) sem session_open") }
if ($implausible.Count -gt 0) { $summaryParts.Add("$($implausible.Count) evento(s) com contagem implausivel") }

if ($summaryParts.Count -gt 0) {
  Write-Host ("OK: consumption.jsonl validado com $validCount eventos e " + ($summaryParts -join ' e ') + ".")
}
else {
  Write-Host "OK: consumption.jsonl validado com sucesso ($validCount eventos)."
}
