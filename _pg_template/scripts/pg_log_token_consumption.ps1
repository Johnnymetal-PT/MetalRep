param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,

  # ONDE o trabalho aconteceu, quando nao foi no proprio repositorio. Serve as pastas de
  # trabalho declaradas (pg_init_work_folder.ps1), que nao tem .pg/ nem levam estrutura da
  # framework: o evento e ESCRITO no repositorio do projeto (-RepoPath) mas REGISTA a pasta
  # onde o trabalho se fez. Sem esta separacao, o session_open dizia o repositorio e o
  # session_close dizia a pasta -- dois eventos da mesma sessao a discordar um do outro.
  [string]$CaminhoDoTrabalho,

  [Parameter(Mandatory = $true)]
  [ValidateSet('session_open', 'session_progress', 'session_close')]
  [string]$EventType,

  [string]$SessionId,
  [ValidateSet('codex', 'claude', 'antigravity', 'gemini')]
  [string]$Agent = 'codex',
  [string]$Model = '',
  [string]$SessionSummary = '',
  # [long] e nao [int]: um contador de tokens passa dos 2 147 483 647 com facilidade
  # e um [int] que transborda e promovido a [double], que escreve valores arredondados.
  [long]$EstimatedInputTokens = 0,
  [long]$EstimatedOutputTokens = 0,

  # Releituras do contexto a partir do cache. Contam para CUSTO, nunca para volume:
  # sao o mesmo material lido outra vez em cada turno. Campo proprio, fora do input.
  [long]$CacheReadInputTokens = 0,
  [long]$CacheCreationInputTokens = 0,

  # Como e que EstimatedInputTokens foi contado. Sem isto nao se distingue um numero
  # correcto de um numero inflacionado pela soma das releituras de cache, e o
  # relatorio mistura as duas coisas na mesma media.
  #   unique_input_v2  - entrada nova + escrita de cache; exclui releituras (correcto)
  #   cache_summed_v1  - soma tudo, incluindo releituras (contabilidade anterior a v2.22.0)
  #   unknown          - origem do numero desconhecida
  [ValidateSet('unique_input_v2', 'cache_summed_v1', 'unknown')]
  [string]$TokenAccounting = 'unknown',

  [ValidateSet('estimated', 'measured', 'unknown')]
  [string]$TokenMeasurement = 'estimated',
  [ValidateSet('mirror', 'api', 'mixed', 'unknown')]
  [string]$ReadMode = 'unknown',

  # Identidade: ver a nota junto a resolucao, mais abaixo. Por omissao sao detectadas.
  [string]$Machine = '',
  [string]$Operator = '',
  [string]$Notes = ''
)

$ErrorActionPreference = "Stop"

if (($EventType -eq 'session_progress' -or $EventType -eq 'session_close') -and [string]::IsNullOrWhiteSpace($SessionSummary)) {
  throw "SessionSummary e obrigatorio para event_type '$EventType'."
}

if ($EstimatedInputTokens -lt 0 -or $EstimatedOutputTokens -lt 0) {
  throw "EstimatedInputTokens e EstimatedOutputTokens nao podem ser negativos."
}

if ($CacheReadInputTokens -lt 0 -or $CacheCreationInputTokens -lt 0) {
  throw "CacheReadInputTokens e CacheCreationInputTokens nao podem ser negativos."
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
$registado = if ([string]::IsNullOrWhiteSpace($CaminhoDoTrabalho)) { $repo }
             else { [System.IO.Path]::GetFullPath($CaminhoDoTrabalho) }
if (-not (Test-Path $repo)) {
  throw "Repositorio nao encontrado: $repo"
}

$tokensDir = Join-Path $repo ".pg\tokens"
$consumptionPath = Join-Path $tokensDir "consumption.jsonl"
if (-not (Test-Path $tokensDir)) {
  New-Item -ItemType Directory -Path $tokensDir -Force | Out-Null
}

# Resolucao do session_id.
#
# Inventar um GUID para um 'session_progress'/'session_close' cria, POR
# CONSTRUCAO, uma sessao sem 'session_open'. Como o log e historico append-only,
# o defeito fica no ficheiro para sempre e o validador reprova o repo todo -- era
# esta a causa de 8 dos 23 repos da frota terem o log invalido. So o
# 'session_open' pode gerar id novo; os restantes eventos reutilizam a ultima
# sessao aberta do mesmo agente (regra "session_id deve ser reutilizado em todos
# os eventos da mesma sessao", AGENTS_SHARED.md) e, na falta dela, falham com
# mensagem accionavel em vez de escreverem lixo permanente.
function Get-LastOpenSessionId {
  param(
    [string]$Path,
    [string]$AgentName
  )

  if (-not (Test-Path $Path)) {
    return $null
  }

  $lines = [System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8)
  for ($i = $lines.Count - 1; $i -ge 0; $i--) {
    $line = $lines[$i].Trim()
    if ([string]::IsNullOrWhiteSpace($line)) {
      continue
    }

    try { $obj = $line | ConvertFrom-Json } catch { continue }
    if (
      ([string]$obj.event_type -eq 'session_open') -and
      ([string]$obj.agent -eq $AgentName) -and
      (-not [string]::IsNullOrWhiteSpace([string]$obj.session_id))
    ) {
      return [string]$obj.session_id
    }
  }

  return $null
}

if ([string]::IsNullOrWhiteSpace($SessionId)) {
  if ($EventType -eq 'session_open') {
    $SessionId = [guid]::NewGuid().ToString()
  }
  else {
    $SessionId = Get-LastOpenSessionId -Path $consumptionPath -AgentName $Agent
    if ([string]::IsNullOrWhiteSpace($SessionId)) {
      throw "Nao ha 'session_open' do agente '$Agent' em $consumptionPath. Registar primeiro o session_open, ou passar -SessionId da sessao em curso: um '$EventType' com id novo criaria uma sessao invalida de forma permanente."
    }
    Write-Host "INFO: -SessionId omitido; a reutilizar a ultima sessao aberta do agente '$Agent' ($SessionId)."
  }
}

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
try { $identidadeOperador = (& git -C $repo config user.email 2>$null | Out-String).Trim() } catch { }
$ErrorActionPreference = $eapIdentidade
if ([string]::IsNullOrWhiteSpace($identidadeOperador)) { $identidadeOperador = 'unknown' }
if (-not [string]::IsNullOrWhiteSpace($Machine)) { $identidadeMaquina = $Machine }
if (-not [string]::IsNullOrWhiteSpace($Operator)) { $identidadeOperador = $Operator }

$event = [ordered]@{
  schema_version = "1.3"
  event_type = $EventType
  occurred_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  session_id = $SessionId
  agent = $Agent
  model = $Model
  repo_name = (Split-Path -Leaf $registado)
  repo_path = $registado
  work_folder = ($registado -ne $repo)
  machine = $identidadeMaquina
  operator = $identidadeOperador
  session_summary = $SessionSummary
  estimated_input_tokens = $EstimatedInputTokens
  estimated_output_tokens = $EstimatedOutputTokens
  cache_read_input_tokens = $CacheReadInputTokens
  cache_creation_input_tokens = $CacheCreationInputTokens
  token_measurement = $TokenMeasurement
  token_accounting = $TokenAccounting
  read_mode = $ReadMode
  notes = $Notes
}

$line = ($event | ConvertTo-Json -Compress -Depth 6)
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::AppendAllText($consumptionPath, $line + [Environment]::NewLine, $encoding)

Write-Host "OK: evento de tokens registado em $consumptionPath"
Write-Host "OK: session_id=$SessionId event_type=$EventType"
