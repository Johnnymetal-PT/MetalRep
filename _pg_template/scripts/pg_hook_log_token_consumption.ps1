<#
.SYNOPSIS
  AUD-03: hook do Claude Code (SessionStart / Stop / SessionEnd) que regista o consumo
  de tokens automaticamente em .pg/tokens/consumption.jsonl, sem intervencao humana.

.DESCRIPTION
  Le o payload do hook no stdin (JSON com session_id, transcript_path, cwd,
  hook_event_name, model). Em SessionStart regista session_open; em Stop (fim de TURNO)
  ou SessionEnd le o transcript, soma os tokens (APROXIMADOS, por isso 'estimated'),
  infere read_mode por heuristica e faz UPSERT de um unico session_close por session_id.

  CONTABILIDADE DE TOKENS (schema 1.2, token_accounting = 'unique_input_v2'):
  o transcript traz quatro contadores de uso por mensagem e eles NAO se somam todos
  como input. Ver a nota extensa no sitio do calculo, mais abaixo.

  O Stop e usado porque o SessionEnd NAO e fiavel no extension do VS Code (nao dispara
  em /clear, fecho de painel, etc. - issues publicos do Claude Code). Como o Stop dispara
  por turno, faz-se upsert (um session_close por sessao, cumulativo).

  Reutiliza pg_log_token_consumption.ps1 para o session_open (append). A prova de falhas:
  qualquer erro e engolido e o script sai com 0 para NUNCA quebrar a sessao do agente.
  So regista em repos elegiveis (com .pg/ ou PG_CONTEXT.md).

.NOTES
  Registado em .claude/settings.json para SessionStart, Stop e SessionEnd.
  Os numeros sao aproximados (limitacao do transcript do Claude Code); para custo
  autoritario usar o dashboard/limites da conta Anthropic. read_mode e heuristico.
  Registos escritos antes da v2.22.0 nao trazem `token_accounting`, somavam as
  releituras de cache e NAO sao comparaveis com estes.
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
  # (FileShare.ReadWrite), evitando IOException quando o transcript ainda esta a ser escrito.
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

function Set-ClaudeSessionClose {
  # Como o Stop dispara por TURNO, mantem-se UM unico session_close por session_id
  # (o mais recente/cumulativo), substituindo o anterior em vez de acumular linhas.
  param([string]$ConsumptionPath, [string]$SessionId, [string]$Line)
  $existing = @()
  if (Test-Path $ConsumptionPath) { $existing = [System.IO.File]::ReadAllLines($ConsumptionPath) }
  $kept = New-Object System.Collections.Generic.List[string]
  foreach ($l in $existing) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    $drop = $false
    try {
      $o = $l | ConvertFrom-Json
      if (([string]$o.agent -eq 'claude') -and ([string]$o.event_type -eq 'session_close') -and ([string]$o.session_id -eq $SessionId)) { $drop = $true }
    }
    catch { }
    if (-not $drop) { $kept.Add($l) }
  }
  $kept.Add($Line)
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($ConsumptionPath, ([string]::Join([Environment]::NewLine, $kept) + [Environment]::NewLine), $encoding)
}

function Get-FirstUserSummary {
  param([object[]]$Lines)
  foreach ($line in $Lines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $obj = $line | ConvertFrom-Json } catch { continue }
    if ($obj.type -ne 'user') { continue }
    $content = $obj.message.content
    $text = ''
    if ($content -is [string]) { $text = $content }
    elseif ($content) { foreach ($part in $content) { if ($part.type -eq 'text' -and $part.text) { $text = [string]$part.text; break } } }
    $text = ($text -replace '\s+', ' ').Trim()
    if ($text) { if ($text.Length -gt 120) { $text = $text.Substring(0, 120) }; return $text }
  }
  return ''
}

try {
  $payload = Read-StdinJson
  if ($null -eq $payload) { exit 0 }

  $eventName = [string]$payload.hook_event_name
  $sessionId = [string]$payload.session_id
  $cwd = [string]$payload.cwd
  if ([string]::IsNullOrWhiteSpace($cwd)) { $cwd = (Get-Location).Path }

  # Elegibilidade: repos da framework, ou pastas de trabalho declaradas.
  #
  # Boa parte do trabalho de Odoo acontece fora de repositorios -- pastas de servidor,
  # arvores de addons, copias de migracao. Ate 2026-09-11 esse trabalho era INVISIVEL a
  # medicao: o hook exigia .pg/ ou PG_CONTEXT.md, e uma pasta de servidor nao tem nenhum.
  # Foi isso que obrigou a auditoria do givachoice a pedir extraccoes maquina a maquina
  # para reconstruir o que la tinha acontecido.
  #
  # Uma pasta declarada pelo pg_init_work_folder.ps1 passa a contar. O log NAO vai para a
  # pasta: vai para o repositorio do projeto que ela declara. A pasta continua sem
  # estrutura da framework -- que e o desenho do pg_init_work_folder -- e a medicao agrega
  # no sitio onde alguem a consulta. Sem repositorio declarado nao ha onde registar, e
  # nesse caso nao se regista (em silencio, como antes): um hook nunca estraga a sessao.
  $destinoLog = $cwd
  $isEligible = (Test-Path (Join-Path $cwd '.pg')) -or (Test-Path (Join-Path $cwd 'PG_CONTEXT.md'))
  if (-not $isEligible) {
    $agentsPath = Join-Path $cwd 'AGENTS.md'
    if (Test-Path $agentsPath) {
      try {
        $conteudo = Get-Content -Path $agentsPath -Raw -Encoding UTF8
        if ($conteudo -match 'PG_WORK_FOLDER:START') {
          if ($conteudo -match '(?m)^\s*Repositorio do projeto:\s*(.+?)\s*$') {
            $repoDeclarado = $Matches[1].Trim()
            if ($repoDeclarado -and (Test-Path (Join-Path $repoDeclarado '.pg'))) {
              $destinoLog = $repoDeclarado
              $isEligible = $true
            }
          }
        }
      }
      catch { }
    }
  }
  if (-not $isEligible) { exit 0 }

  $logScript = Join-Path $PSScriptRoot 'pg_log_token_consumption.ps1'
  if (-not (Test-Path $logScript)) { exit 0 }

  if ($eventName -eq 'SessionStart') {
    $model = [string]$payload.model
    & $logScript -RepoPath $destinoLog -CaminhoDoTrabalho $cwd -EventType session_open -Agent claude -Model $model `
      -SessionId $sessionId -ReadMode unknown -TokenMeasurement unknown `
      -Notes 'auto: hook SessionStart' | Out-Null
    exit 0
  }

  if ($eventName -eq 'Stop' -or $eventName -eq 'SessionEnd') {
    $transcriptPath = [string]$payload.transcript_path
    # [long] e nao [int]: um [int] do PowerShell que transborda e promovido a [double]
    # e passa a escrever no log valores arredondados em notacao cientifica.
    $freshInput = [long]0
    $cacheCreation = [long]0
    $cacheRead = [long]0
    $outputTokens = [long]0
    $model = ''
    $summary = ''
    $readMode = 'unknown'
    $navigationMode = 'native'

    if ($transcriptPath -and (Test-Path $transcriptPath)) {
      # Leitura isolada e partilhada: se falhar (transcript bloqueado), degradar mas
      # continuar a escrever o session_close na mesma.
      try {
        $blob = Read-SharedText -Path $transcriptPath
        $lines = $blob -split "\r?\n"
        foreach ($line in $lines) {
          if ([string]::IsNullOrWhiteSpace($line)) { continue }
          try { $obj = $line | ConvertFrom-Json } catch { continue }
          if ($obj.type -eq 'assistant' -and $obj.message) {
            $u = $obj.message.usage
            if ($u) {
              # Os tres contadores de entrada sao somados EM SEPARADO, e so dois deles
              # entram no volume.
              #
              # `cache_read_input_tokens` e o contexto INTEIRO relido do cache em CADA
              # turno. Soma-lo ao input dava contexto x numero de turnos: o log da frota
              # chegou a declarar 3 676 354 561 tokens numa sessao e uma media de 204
              # milhoes por sessao em modo `api` -- varias ordens de grandeza acima do
              # que e fisicamente possivel, quando a janela de contexto tem 1 milhao.
              # Com isso, a metrica-alvo do AUD-03 (provar que o espelho custa menos que
              # a API) media sobretudo o comprimento das sessoes.
              #
              # O volume de material DISTINTO que entrou na sessao e `input_tokens`
              # (entrada nova, fora do cache) mais `cache_creation_input_tokens` (escrito
              # no cache uma unica vez). As releituras sao repeticao do mesmo material:
              # contam para CUSTO -- e por isso ficam num campo proprio -- nunca para
              # volume.
              $freshInput += [long]([math]::Max(0, [long]($u.input_tokens)))
              $cacheCreation += [long]([math]::Max(0, [long]($u.cache_creation_input_tokens)))
              $cacheRead += [long]([math]::Max(0, [long]($u.cache_read_input_tokens)))
              $outputTokens += [long]([math]::Max(0, [long]($u.output_tokens)))
            }
            if ($obj.message.model) { $model = [string]$obj.message.model }
          }
        }
        $summary = Get-FirstUserSummary -Lines $lines

        # read_mode heuristico: marcadores de acesso DIRETO ao Odoo -> api; senao mirror
        if ($blob -match '(?i)xmlrpc|/web/dataset|/json/2/|jsonrpc|odoo-bin|mcp.*odoo|odoo.*api_key') {
          $readMode = 'api'
        }
        else {
          $readMode = 'mirror'
        }
        if ($blob -match '(?i)pg_odools_query|odoo_ls_server|\bOdooLS\b') { $navigationMode = 'odools' }
      }
      catch { $readMode = 'unknown' }
    }

    if ([string]::IsNullOrWhiteSpace($summary)) { $summary = 'Sessao Claude registada automaticamente (hook Stop/SessionEnd)' }

    # O log vai para $destinoLog (o repositorio), mas o `repo_path` do evento continua
    # a ser o $cwd: o registo diz ONDE o trabalho aconteceu, e fica guardado onde
    # alguem o consulta. Num repositorio normal os dois sao o mesmo.
    $tokensDir = Join-Path $destinoLog '.pg\tokens'
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
    # A identidade le-se do repositorio de destino: uma pasta de trabalho pode nao ser
    # sequer um repositorio git, e ai o `git -C` nao devolve nada.
    try { $identidadeOperador = (& git -C $destinoLog config user.email 2>$null | Out-String).Trim() } catch { }
    $ErrorActionPreference = $eapIdentidade
    if ([string]::IsNullOrWhiteSpace($identidadeOperador)) { $identidadeOperador = 'unknown' }

    $evt = [ordered]@{
      schema_version         = '1.3'
      event_type             = 'session_close'
      occurred_at_utc        = (Get-Date).ToUniversalTime().ToString('o')
      session_id             = $sessionId
      agent                  = 'claude'
      model                  = $model
      repo_name              = (Split-Path -Leaf $cwd)
      repo_path              = $cwd
      work_folder            = ($destinoLog -ne $cwd)
      machine                = $identidadeMaquina
      operator               = $identidadeOperador
      session_summary        = $summary
      estimated_input_tokens = $freshInput + $cacheCreation
      estimated_output_tokens = $outputTokens
      input_tokens_fresh     = $freshInput
      cache_creation_input_tokens = $cacheCreation
      cache_read_input_tokens = $cacheRead
      token_measurement      = 'estimated'
      token_accounting       = 'unique_input_v2'
      read_mode              = $readMode
      navigation_mode        = $navigationMode
      notes                  = 'auto: hook Claude Stop/SessionEnd (upsert por sessao); estimated_input_tokens = entrada nova + escrita de cache (volume distinto); releituras de cache em cache_read_input_tokens; usar Console Anthropic para custo autoritario; read_mode heuristico'
    }
    $line = ($evt | ConvertTo-Json -Compress -Depth 6)
    Set-ClaudeSessionClose -ConsumptionPath $consumptionPath -SessionId $sessionId -Line $line
    exit 0
  }

  exit 0
}
catch {
  # Nunca quebrar a sessao do agente por causa do registo
  exit 0
}
