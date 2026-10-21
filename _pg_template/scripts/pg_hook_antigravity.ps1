<#
.SYNOPSIS
  Hook do Antigravity (Google): leva ao Antigravity o mesmo contrato de arranque e de
  registo de tokens que o Claude Code e o Codex ja tinham.

.DESCRIPTION
  O Antigravity nao tem SessionStart nem SessionEnd. Os eventos que existem, e que este
  script usa, sao (fonte: ~/.gemini/antigravity/builtin/skills/agy-customizations/docs/hooks.md,
  versao instalada a 2026-10-07):
    - PreInvocation : antes de CADA chamada ao modelo. Pode injetar mensagens no contexto
                      ({"injectSteps":[{"ephemeralMessage":"..."}]}).
    - Stop          : quando o ciclo do agente termina (por turno, como o Stop do Codex).

  O SessionStart dos outros dois agentes reconstroi-se assim: na PRIMEIRA PreInvocation
  de cada conversa (conversationId), e so nessa, corre-se o que o SessionStart corria --
  o passo 2 do ritual (pg_ensure_framework_current.ps1) e o session_open -- e injeta-se
  o resultado no contexto. As invocacoes seguintes saem logo, porque a PreInvocation
  dispara antes de cada chamada ao modelo e um `git pull` por chamada seria inaceitavel.

  Tres diferencas de contrato face aos hooks do Claude e do Codex:
    - o payload nao traz o nome do evento: vem no parametro -Evento, posto em hooks.json;
    - o payload usa camelCase (conversationId, workspacePaths, transcriptPath, modelName);
    - o stdout TEM de ser um objeto JSON. Tudo o que os scripts chamados escrevem e
      capturado; o unico texto que sai e o JSON final.

  O hook corre com o diretorio de trabalho na pasta do hooks.json (`.agents/`), e nao na
  raiz do repositorio. Por isso o repositorio resolve-se a partir dai, e cada script e
  chamado com -RepoPath explicito.

  Modo utilizador (-Modo utilizador): instalado em ~/.gemini/config/hooks.json por
  pg_install_user_hooks.py. Equivale ao hook de utilizador do Claude e do Codex: num
  repositorio ainda sem framework, corre o pg_auto_bootstrap.ps1 e injeta as linhas
  `PG AUTO-BOOTSTRAP:` no contexto. Num repositorio ja bootstrapado nao faz nada, porque
  o hook do projeto trata disso.

  A prova de falhas: sai sempre com 0 e com um JSON valido. Um hook nunca estraga a
  sessao de quem esta a trabalhar.

  Tokens: lidos do transcript (transcriptPath), no formato observado na primeira sessao
  real (2026-10-07). Contabilidade unique_input_v2, como o Claude: ver a nota junto a
  leitura. Se o formato mudar e nao houver PLANNER_RESPONSE com contadores, o
  session_close regista token_measurement 'unknown' em vez de adivinhar -- somar
  contadores de um formato desconhecido foi o defeito que inflacionou o log da frota
  ate a v2.22.0.
#>
param(
  [ValidateSet('PreInvocation', 'Stop')]
  [string]$Evento = 'PreInvocation',
  [ValidateSet('projeto', 'utilizador')]
  [string]$Modo = 'projeto'
)

$ErrorActionPreference = 'Stop'

function Write-HookJson {
  param([object]$Objeto)
  try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
  [Console]::Out.Write(($Objeto | ConvertTo-Json -Compress -Depth 6))
}

function Exit-Hook {
  param([object]$Objeto)
  if ($null -eq $Objeto) {
    $Objeto = if ($Evento -eq 'Stop') { @{ decision = 'allow' } } else { @{} }
  }
  Write-HookJson -Objeto $Objeto
  exit 0
}

function Read-SharedText {
  # Leitura tolerante a outro processo ter o ficheiro aberto para escrita: o agente
  # mantem o transcript aberto enquanto a sessao esta ativa.
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

function Resolve-Repo {
  param([object]$Payload)
  if ($Modo -eq 'projeto') {
    $aqui = (Get-Location).Path
    if ((Split-Path -Leaf $aqui) -match '^[._]agents?$') { return (Split-Path -Parent $aqui) }
  }
  foreach ($p in @($Payload.workspacePaths)) {
    if (-not [string]::IsNullOrWhiteSpace([string]$p) -and (Test-Path ([string]$p))) {
      return [System.IO.Path]::GetFullPath([string]$p)
    }
  }
  if ($Modo -eq 'projeto') { return (Get-Location).Path }
  return $null
}

function Test-RepoElegivel {
  param([string]$Repo)
  return ((Test-Path (Join-Path $Repo '.pg')) -or (Test-Path (Join-Path $Repo 'PG_CONTEXT.md')))
}

function Test-PrimeiraInvocacao {
  # Marca por conversa, fora do repositorio, para que so a primeira PreInvocation faca
  # o trabalho de arranque.
  param([string]$ConversationId)
  $dir = Join-Path ([System.IO.Path]::GetTempPath()) 'pg_antigravity'
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $nome = ($ConversationId -replace '[^A-Za-z0-9_-]', '_') + '.' + $Modo
  $marca = Join-Path $dir $nome
  if (Test-Path $marca) { return $false }
  Set-Content -Path $marca -Value ((Get-Date).ToUniversalTime().ToString('o')) -Encoding ASCII
  return $true
}

function Invoke-Capturado {
  # Corre um script e devolve TODO o texto que produziu (incluindo Write-Host), para que
  # nada chegue ao stdout do hook fora do JSON.
  param([string]$Script, [hashtable]$Parametros)
  $eap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { return ((& $Script @Parametros *>&1 | ForEach-Object { "$_" }) -join "`n").Trim() }
  catch { return ("ERRO: " + $_.Exception.Message) }
  finally { $ErrorActionPreference = $eap }
}

function Get-Cauda {
  param([string]$Texto, [int]$Linhas = 25)
  if ([string]::IsNullOrWhiteSpace($Texto)) { return '' }
  $todas = $Texto -split "\r?\n"
  if ($todas.Count -le $Linhas) { return $Texto }
  return (($todas | Select-Object -Last $Linhas) -join "`n")
}

function Set-AntigravitySessionClose {
  # O Stop dispara por turno: um unico session_close por sessao, substituido a cada turno.
  param([string]$ConsumptionPath, [string]$SessionId, [string]$Line)
  $existing = @()
  if (Test-Path $ConsumptionPath) { $existing = [System.IO.File]::ReadAllLines($ConsumptionPath) }
  $kept = New-Object System.Collections.Generic.List[string]
  foreach ($l in $existing) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    $drop = $false
    try {
      $o = $l | ConvertFrom-Json
      if (([string]$o.agent -eq 'antigravity') -and ([string]$o.event_type -eq 'session_close') -and ([string]$o.session_id -eq $SessionId)) { $drop = $true }
    }
    catch { }
    if (-not $drop) { $kept.Add($l) }
  }
  $kept.Add($Line)
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($ConsumptionPath, ([string]::Join([Environment]::NewLine, $kept) + [Environment]::NewLine), $encoding)
}

try {
  $raw = [Console]::In.ReadToEnd()
  if ([string]::IsNullOrWhiteSpace($raw)) { Exit-Hook }
  $payload = $raw | ConvertFrom-Json
  $sessionId = [string]$payload.conversationId
  if ([string]::IsNullOrWhiteSpace($sessionId)) { Exit-Hook }
  $modelo = [string]$payload.modelName

  $repo = Resolve-Repo -Payload $payload
  if (-not $repo) { Exit-Hook }

  # --- Modo utilizador: so o auto-bootstrap, so em repositorios por bootstrapar ---------
  if ($Modo -eq 'utilizador') {
    if ($Evento -ne 'PreInvocation') { Exit-Hook }
    if (Test-Path (Join-Path $repo '.pg_framework')) { Exit-Hook }
    if (-not (Test-PrimeiraInvocacao -ConversationId $sessionId)) { Exit-Hook }
    $auto = Join-Path $PSScriptRoot 'pg_auto_bootstrap.ps1'
    if (-not (Test-Path $auto)) { Exit-Hook }
    $saida = Invoke-Capturado -Script $auto -Parametros @{ RepoPath = $repo; Hook = $true }
    if ([string]::IsNullOrWhiteSpace($saida)) { Exit-Hook }
    Exit-Hook @{ injectSteps = @(@{ ephemeralMessage = $saida }) }
  }

  # --- Modo projeto -------------------------------------------------------------------
  if (-not (Test-RepoElegivel -Repo $repo)) { Exit-Hook }
  $scripts = Join-Path $repo '.pg_framework\scripts'
  $logger = Join-Path $scripts 'pg_log_token_consumption.ps1'

  if ($Evento -eq 'PreInvocation') {
    if (-not (Test-PrimeiraInvocacao -ConversationId $sessionId)) { Exit-Hook }

    # Passo 2 do ritual, como no SessionStart do Claude e do Codex.
    $ensure = Join-Path $scripts 'pg_ensure_framework_current.ps1'
    $saidaEnsure = ''
    if (Test-Path $ensure) { $saidaEnsure = Invoke-Capturado -Script $ensure -Parametros @{ RepoPath = $repo } }
    else { $saidaEnsure = 'AVISO: .pg_framework\scripts\pg_ensure_framework_current.ps1 nao encontrado; framework nao ligado.' }

    if (Test-Path $logger) {
      Invoke-Capturado -Script $logger -Parametros @{
        RepoPath = $repo; EventType = 'session_open'; Agent = 'antigravity'; Model = $modelo
        SessionId = $sessionId; ReadMode = 'unknown'; TokenMeasurement = 'unknown'
        Notes = 'auto: hook Antigravity PreInvocation (primeira invocacao da conversa)'
      } | Out-Null
    }

    # O AGENTS.md ja e carregado pelo Antigravity. O AGENTS_SHARED.md nao pode ser incluido
    # por @[...]: tem mais de 24 KB, o limite por ficheiro de regras, e seria truncado em
    # silencio. Pede-se a leitura integral, como o AGENTS.md faz para o Codex.
    $mensagem = @"
PG FRAMEWORK (hook Antigravity, arranque da conversa)
Este repositorio usa a framework partilhada da Parametro Global. Antes de qualquer analise, leitura funcional ou proposta:
1. Ler INTEGRALMENTE .pg_framework/templates/AGENTS_SHARED.md com a ferramenta de leitura de ficheiros. Nao confiar num resumo: o ficheiro excede o limite de 24 KB das regras do Antigravity e nao e carregado automaticamente.
2. Executar o ritual de AGENTS.md (passos 1 a 4): pg_checkout_brodoo_branch.ps1, pg_ensure_framework_current.ps1 (ja corrido por este hook, resultado abaixo), versao Odoo confirmada, pg_preflight_context.ps1. Ler .pg/PREFLIGHT.json e agir sobre os avisos.
3. Registo de tokens: este hook ja abriu a sessao (session_id $sessionId, agent antigravity). Escritas manuais so por .pg_framework/scripts/pg_log_token_consumption.ps1 -Agent antigravity -SessionId $sessionId, nunca compondo JSON a mao.

Resultado de pg_ensure_framework_current.ps1:
$(Get-Cauda -Texto $saidaEnsure)
"@
    Exit-Hook @{ injectSteps = @(@{ ephemeralMessage = $mensagem }) }
  }

  if ($Evento -eq 'Stop') {
    $readMode = 'unknown'
    $navigationMode = 'native'
    $freshInput = [long]0
    $cacheRead = [long]0
    $outputTokens = [long]0
    $measurement = 'unknown'
    $accounting = 'unknown'
    $summary = ''
    $transcriptPath = [string]$payload.transcriptPath
    if ($transcriptPath -and (Test-Path $transcriptPath)) {
      try {
        # Formato observado a 2026-10-07 (extensao 1.7.0, conversa 03be5fff no enigmaf):
        # uma linha JSON por passo, com `type`. Cada chamada ao modelo e um
        # PLANNER_RESPONSE com `input_tokens`, `cache_read_tokens` e `output_tokens`.
        #
        # `input_tokens` NAO inclui as releituras de cache: o passo com 29 134 de entrada
        # foi seguido de um com 4 851 novos e 24 485 lidos do cache. E a separacao do
        # Claude, e por isso a mesma contabilidade unique_input_v2: o volume e a soma dos
        # `input_tokens`; as releituras ficam no seu campo, nunca somadas ao input. Nao ha
        # contador de escrita de cache: o cache do Gemini e implicito, e o que entra em
        # cache ja foi contado como entrada nova.
        $blob = Read-SharedText -Path $transcriptPath
        $chamadas = New-Object System.Text.StringBuilder
        foreach ($line in ($blob -split "\r?\n")) {
          if ([string]::IsNullOrWhiteSpace($line)) { continue }
          try { $obj = $line | ConvertFrom-Json } catch { continue }
          $tipo = [string]$obj.type
          if ($tipo -eq 'PLANNER_RESPONSE') {
            $freshInput += [long]([math]::Max(0, [long]($obj.input_tokens)))
            $cacheRead += [long]([math]::Max(0, [long]($obj.cache_read_tokens)))
            $outputTokens += [long]([math]::Max(0, [long]($obj.output_tokens)))
            $measurement = 'estimated'
            $accounting = 'unique_input_v2'
            if ($obj.tool_calls) { [void]$chamadas.AppendLine(($obj.tool_calls | ConvertTo-Json -Compress -Depth 6)) }
          }
          elseif ($tipo -eq 'USER_INPUT' -and -not $summary) {
            $texto = [string]$obj.content
            if ($texto -match '(?s)<USER_REQUEST>(.*?)</USER_REQUEST>') { $texto = $Matches[1] }
            $texto = ($texto -replace '\s+', ' ').Trim()
            if ($texto.Length -gt 120) { $texto = $texto.Substring(0, 120) }
            $summary = $texto
          }
        }

        # read_mode so sobre as CHAMADAS A FERRAMENTAS, e nao sobre o transcript inteiro.
        # O transcript traz o conteudo dos ficheiros lidos, e o AGENTS_SHARED.md -- lido em
        # todas as sessoes por exigencia do ritual -- fala de jsonrpc, xmlrpc e api_key. A
        # heuristica sobre o texto todo marcou como `api` a primeira sessao real, que nunca
        # tocou na API do Odoo; marcaria todas, e a comparacao espelho-vs-API ficava sem
        # sentido para este agente.
        $alvo = $chamadas.ToString()
        if ($measurement -eq 'unknown') { $alvo = $blob }  # formato desconhecido: heuristica antiga
        if ($alvo -match '(?i)xmlrpc|/web/dataset|/json/2/|jsonrpc|odoo-bin|mcp.*odoo|odoo.*api_key|pg_odoo_query|pg_odoo_client_query|pg_odoo_mcp_query') { $readMode = 'api' } else { $readMode = 'mirror' }
        if ($alvo -match '(?i)pg_odools_query|odoo_ls_server|\bOdooLS\b') { $navigationMode = 'odools' }
      }
      catch { $readMode = 'unknown' }
    }
    if ([string]::IsNullOrWhiteSpace($summary)) { $summary = 'Sessao Antigravity registada automaticamente (hook Stop)' }

    $tokensDir = Join-Path $repo '.pg\tokens'
    if (-not (Test-Path $tokensDir)) { New-Item -ItemType Directory -Path $tokensDir -Force | Out-Null }
    $consumptionPath = Join-Path $tokensDir 'consumption.jsonl'

    # Identidade da sessao: a mesma resolucao em linha dos hooks do Claude e do Codex
    # (ver a nota em pg_hook_log_token_consumption.ps1). `machine` diz onde; `operator`
    # e a identidade declarada no git.
    $identidadeMaquina = [System.Environment]::MachineName
    $identidadeOperador = ''
    $eapIdentidade = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $identidadeOperador = (& git -C $repo config user.email 2>$null | Out-String).Trim() } catch { }
    $ErrorActionPreference = $eapIdentidade
    if ([string]::IsNullOrWhiteSpace($identidadeOperador)) { $identidadeOperador = 'unknown' }

    $evt = [ordered]@{
      schema_version          = '1.3'
      event_type              = 'session_close'
      occurred_at_utc         = (Get-Date).ToUniversalTime().ToString('o')
      session_id              = $sessionId
      agent                   = 'antigravity'
      model                   = $modelo
      repo_name               = (Split-Path -Leaf $repo)
      repo_path               = $repo
      machine                 = $identidadeMaquina
      operator                = $identidadeOperador
      session_summary         = $summary
      estimated_input_tokens  = $freshInput
      estimated_output_tokens = $outputTokens
      input_tokens_fresh      = $freshInput
      cache_read_input_tokens = $cacheRead
      token_measurement       = $measurement
      token_accounting        = $accounting
      read_mode               = $readMode
      navigation_mode         = $navigationMode
      notes                   = 'auto: hook Antigravity Stop (upsert por sessao); soma dos PLANNER_RESPONSE do transcript; releituras de cache em cache_read_input_tokens; read_mode heuristico sobre as chamadas a ferramentas'
    }
    Set-AntigravitySessionClose -ConsumptionPath $consumptionPath -SessionId $sessionId -Line ($evt | ConvertTo-Json -Compress -Depth 6)
    Exit-Hook
  }

  Exit-Hook
}
catch {
  # Nunca quebrar a sessao do agente
  Exit-Hook
}
