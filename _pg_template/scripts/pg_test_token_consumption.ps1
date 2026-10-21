<#
.SYNOPSIS
  Testes do registo de consumo de tokens: resolucao de session_id no logger e
  severidade do validador.

.DESCRIPTION
  Cobre os tres defeitos encontrados na auditoria da frota (9 de 23 repos com o
  log invalido):
  - o logger inventava um session_id novo em eventos que nao sao 'session_open',
    criando sessoes orfas permanentes;
  - o validador tratava essa orfandade -- irreparavel, por o log ser append-only
    -- como erro, reprovando o repo para sempre;
  - JSON escrito a mao com paths do Windows produz escapes invalidos (\U, \D).

  Cobre tambem o defeito de contabilidade corrigido na v2.22.0: o hook do Claude
  somava `cache_read_input_tokens` -- o contexto inteiro relido em cada turno -- ao
  input, e a frota chegou a declarar 3 676 354 561 tokens numa sessao. O validador
  aceitava-os porque so olhava para a forma do schema, nunca para a grandeza.
#>
param()

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Assert-True {
  param(
    [bool]$Condition,
    [string]$Message
  )

  if (-not $Condition) {
    throw $Message
  }
}

function Assert-Contains {
  param(
    [string]$Text,
    [string]$Expected,
    [string]$Message
  )

  $haystack = if ($null -eq $Text) { '' } else { $Text }
  if (-not $haystack.Contains($Expected)) {
    throw "$Message (texto: $haystack)"
  }
}

function Invoke-PowerShellScript {
  param(
    [string]$ScriptPath,
    [string[]]$Arguments
  )

  # Ver nota em pg_test_context_hygiene.ps1: com Stop, o 2>&1 sobre um
  # executavel nativo abortaria o harness antes de a assercao mostrar o output.
  $savedPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $savedPreference
  }

  return [pscustomobject]@{
    Output = ($output | Out-String)
    ExitCode = $exitCode
  }
}

function Invoke-HookWithStdin {
  param(
    [string]$ScriptPath,
    [string]$JsonPayload
  )

  $savedPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = $JsonPayload | & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 2>&1
    $exitCode = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $savedPreference
  }

  return [pscustomobject]@{
    Output = ($output | Out-String)
    ExitCode = $exitCode
  }
}

function New-TokenFixtureRepo {
  param(
    [string]$RootPath,
    [string]$Name
  )

  $repo = Join-Path $RootPath $Name
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg/tokens') -Force | Out-Null
  return $repo
}

function Get-ConsumptionEvents {
  param([string]$RepoPath)

  $path = Join-Path $RepoPath '.pg/tokens/consumption.jsonl'
  if (-not (Test-Path $path)) {
    return @()
  }

  return @([System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    ForEach-Object { $_ | ConvertFrom-Json })
}

$logger = Join-Path $PSScriptRoot 'pg_log_token_consumption.ps1'
$validator = Join-Path $PSScriptRoot 'pg_validate_token_consumption.ps1'

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('pg_tokens_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
  # --- Logger: session_id ---------------------------------------------------
  $repo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'sessao_normal'

  $open = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $repo, '-EventType', 'session_open', '-Agent', 'claude')
  Assert-True -Condition ($open.ExitCode -eq 0) -Message "session_open falhou: $($open.Output)"

  $progress = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $repo, '-EventType', 'session_progress', '-Agent', 'claude', '-SessionSummary', 'checkpoint')
  Assert-True -Condition ($progress.ExitCode -eq 0) -Message "session_progress sem -SessionId falhou: $($progress.Output)"

  $events = Get-ConsumptionEvents -RepoPath $repo
  Assert-True -Condition ($events.Count -eq 2) -Message "esperados 2 eventos, obtidos $($events.Count)"
  Assert-True -Condition ($events[0].session_id -eq $events[1].session_id) -Message 'session_progress sem -SessionId nao reutilizou a sessao aberta (era isto que criava sessoes orfas permanentes).'

  # O par existe, logo o validador nao tem nada a assinalar.
  $validOk = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $repo)
  Assert-True -Condition ($validOk.ExitCode -eq 0) -Message "validador reprovou um log valido: $($validOk.Output)"
  Assert-Contains -Text $validOk.Output -Expected 'validado com sucesso' -Message 'validador nao confirmou log valido.'

  # O path do repo tem '\' e tem de sobreviver ao round-trip (defeito real da frota).
  Assert-True -Condition ($events[0].repo_path -eq ([System.IO.Path]::GetFullPath($repo))) -Message 'repo_path nao sobreviveu ao round-trip JSON.'

  # --- Logger: progress sem sessao aberta tem de falhar ---------------------
  $orphanRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'sessao_orfa'
  $orphan = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $orphanRepo, '-EventType', 'session_progress', '-Agent', 'claude', '-SessionSummary', 'checkpoint sem abertura')
  Assert-True -Condition ($orphan.ExitCode -ne 0) -Message 'session_progress sem session_open anterior devia falhar, mas passou (voltaria a criar sessoes orfas).'
  Assert-Contains -Text $orphan.Output -Expected "Nao ha 'session_open'" -Message 'mensagem de falha nao e accionavel.'
  Assert-True -Condition ((Get-ConsumptionEvents -RepoPath $orphanRepo).Count -eq 0) -Message 'evento orfao foi escrito no ficheiro apesar da falha.'

  # Um agente diferente nao herda a sessao aberta de outro.
  $codexOrphan = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $repo, '-EventType', 'session_close', '-Agent', 'codex', '-SessionSummary', 'fecho de outro agente')
  Assert-True -Condition ($codexOrphan.ExitCode -ne 0) -Message 'session_close do codex reutilizou a sessao aberta do claude.'

  # --- Validador: orfandade historica e AVISO, nao erro ---------------------
  $legacyRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'historico_orfao'
  $legacyLine = ([ordered]@{
      schema_version = '1.1'
      event_type = 'session_close'
      occurred_at_utc = '2026-06-25T14:29:05Z'
      session_id = '11abb9a8-feb0-44f4-99da-240b47310d17'
      agent = 'claude'
      model = 'modelo-teste'
      repo_name = 'historico_orfao'
      repo_path = $legacyRepo
      session_summary = 'fecho sem abertura, escrito antes do fecho da causa raiz'
      estimated_input_tokens = 10
      estimated_output_tokens = 20
      token_measurement = 'estimated'
      read_mode = 'mirror'
      notes = ''
    } | ConvertTo-Json -Compress -Depth 6)
  Write-Utf8NoBomFile -Path (Join-Path $legacyRepo '.pg/tokens/consumption.jsonl') -Content ($legacyLine + [Environment]::NewLine)

  $legacyValidation = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $legacyRepo)
  Assert-True -Condition ($legacyValidation.ExitCode -eq 0) -Message "orfandade historica devia ser aviso, mas reprovou: $($legacyValidation.Output)"
  Assert-Contains -Text $legacyValidation.Output -Expected 'sem session_open' -Message 'validador nao avisou da sessao sem session_open.'

  # --- Validador: JSON invalido continua a ser ERRO ------------------------
  $brokenRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'json_invalido'
  # Escapes invalidos por path do Windows escrito a mao: foi o que corrompeu o log do Sofmovel.
  $brokenLine = '{"schema_version":"1.0","event_type":"session_open","occurred_at_utc":"2026-06-25T14:29:05Z","session_id":"aaa","agent":"claude","repo_path":"C:\Users\Utilizador\Desktop\Repos\Sofmovel","estimated_input_tokens":0,"estimated_output_tokens":0}'
  Write-Utf8NoBomFile -Path (Join-Path $brokenRepo '.pg/tokens/consumption.jsonl') -Content ($brokenLine + [Environment]::NewLine)

  $brokenValidation = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $brokenRepo)
  Assert-True -Condition ($brokenValidation.ExitCode -ne 0) -Message 'JSON nao parseavel devia continuar a ser erro.'
  Assert-Contains -Text $brokenValidation.Output -Expected 'Linha 1 invalida' -Message 'erro de parsing nao identifica a linha.'

  # --- Hook: releituras de cache NAO entram no input -----------------------
  #
  # O teste que faltava. Sem ele o defeito volta na primeira vez que alguem
  # "simplificar" a soma dos quatro contadores do transcript.
  $hook = Join-Path $PSScriptRoot 'pg_hook_log_token_consumption.ps1'
  $hookRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'hook_cache'
  $transcript = Join-Path $hookRepo 'transcript.jsonl'

  # Tres turnos iguais. O contexto relido do cache (50 000/turno) e o mesmo material
  # em cada turno; o material distinto sao os 100 novos + os 200 escritos no cache.
  $turnos = @()
  for ($i = 0; $i -lt 3; $i++) {
    $turnos += (([ordered]@{
      type = 'assistant'
      message = [ordered]@{
        model = 'modelo-teste'
        usage = [ordered]@{
          input_tokens = 100
          cache_creation_input_tokens = 200
          cache_read_input_tokens = 50000
          output_tokens = 10
        }
      }
    }) | ConvertTo-Json -Compress -Depth 6)
  }
  Write-Utf8NoBomFile -Path $transcript -Content (($turnos -join [Environment]::NewLine) + [Environment]::NewLine)

  $hookPayload = ([ordered]@{
    hook_event_name = 'Stop'
    session_id = 'd4f1c2b0-0000-4000-8000-000000000001'
    cwd = $hookRepo
    transcript_path = $transcript
  } | ConvertTo-Json -Compress -Depth 4)

  $hookRun = Invoke-HookWithStdin -ScriptPath $hook -JsonPayload $hookPayload
  Assert-True -Condition ($hookRun.ExitCode -eq 0) -Message "hook devia sair sempre com 0: $($hookRun.Output)"

  # @(...) no sitio da chamada: o PowerShell desembrulha um array de UM elemento
  # devolvido por uma funcao, e $hookEvents.Count passaria a $null.
  $hookEvents = @(Get-ConsumptionEvents -RepoPath $hookRepo)
  Assert-True -Condition ($hookEvents.Count -eq 1) -Message "esperado 1 session_close do hook, obtidos $($hookEvents.Count)"
  $fecho = $hookEvents[0]

  Assert-True -Condition ([long]$fecho.estimated_input_tokens -eq 900) -Message "estimated_input_tokens devia ser 900 (3 x (100 novos + 200 de escrita de cache)); obtido $($fecho.estimated_input_tokens). Se der 150900, as releituras de cache voltaram a ser somadas ao input."
  Assert-True -Condition ([long]$fecho.cache_read_input_tokens -eq 150000) -Message "as releituras de cache tem de ficar registadas em campo proprio; obtido $($fecho.cache_read_input_tokens)"
  Assert-True -Condition ([long]$fecho.estimated_output_tokens -eq 30) -Message "estimated_output_tokens devia ser 30; obtido $($fecho.estimated_output_tokens)"
  Assert-True -Condition ($fecho.token_accounting -eq 'unique_input_v2') -Message 'o fecho tem de declarar a contabilidade usada, senao o relatorio nao distingue os registos bons dos inflacionados.'
  Assert-True -Condition ($fecho.schema_version -eq '1.3') -Message "schema do fecho devia ser 1.3; obtido $($fecho.schema_version)"

  # --- Logger: campos 1.2 e valores acima do limite do [int] ----------------
  $bigRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'valores_grandes'
  $bigOpen = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $bigRepo, '-EventType', 'session_open', '-Agent', 'claude')
  Assert-True -Condition ($bigOpen.ExitCode -eq 0) -Message "session_open falhou: $($bigOpen.Output)"

  # 3 000 000 000 > [int]::MaxValue: com [int] o PowerShell promovia a [double] e
  # escrevia o valor arredondado.
  $bigClose = Invoke-PowerShellScript -ScriptPath $logger -Arguments @(
    '-RepoPath', $bigRepo, '-EventType', 'session_close', '-Agent', 'claude',
    '-SessionSummary', 'sessao com contadores grandes',
    '-EstimatedInputTokens', '3000000000', '-CacheReadInputTokens', '4000000000',
    '-TokenAccounting', 'unique_input_v2')
  Assert-True -Condition ($bigClose.ExitCode -eq 0) -Message "session_close com valores grandes falhou: $($bigClose.Output)"

  $bigEvents = @(Get-ConsumptionEvents -RepoPath $bigRepo)
  $bigFecho = @($bigEvents | Where-Object { $_.event_type -eq 'session_close' })[0]
  Assert-True -Condition ([long]$bigFecho.estimated_input_tokens -eq 3000000000) -Message "contador acima do [int] foi corrompido: $($bigFecho.estimated_input_tokens)"
  Assert-True -Condition ([long]$bigFecho.cache_read_input_tokens -eq 4000000000) -Message "cache_read_input_tokens acima do [int] foi corrompido: $($bigFecho.cache_read_input_tokens)"

  # --- Validador: grandeza implausivel e AVISO, nao erro --------------------
  $bigValidation = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $bigRepo)
  Assert-True -Condition ($bigValidation.ExitCode -eq 0) -Message "grandeza implausivel devia ser aviso: $($bigValidation.Output)"
  Assert-Contains -Text $bigValidation.Output -Expected 'limite de plausibilidade' -Message 'validador nao assinalou a contagem implausivel -- era exactamente isto que deixava passar 3 676 354 561 tokens numa sessao.'

  # E o schema 1.2 do logger continua a passar no validador.
  $okValidation = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $hookRepo)
  Assert-True -Condition ($okValidation.ExitCode -eq 0) -Message "validador reprovou um registo 1.2 valido: $($okValidation.Output)"

  # --- Validador: token_accounting invalido continua a ser ERRO -------------
  $badAccountingRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'contabilidade_invalida'
  $badLine = ([ordered]@{
      schema_version = '1.2'
      event_type = 'session_close'
      occurred_at_utc = '2026-09-10T09:00:00Z'
      session_id = 'c0ffee00-0000-4000-8000-000000000002'
      agent = 'claude'
      model = 'modelo-teste'
      repo_name = 'contabilidade_invalida'
      repo_path = $badAccountingRepo
      session_summary = 'contabilidade fora do conjunto'
      estimated_input_tokens = 10
      estimated_output_tokens = 20
      token_measurement = 'estimated'
      token_accounting = 'inventada'
      read_mode = 'mirror'
      notes = ''
    } | ConvertTo-Json -Compress -Depth 6)
  Write-Utf8NoBomFile -Path (Join-Path $badAccountingRepo '.pg/tokens/consumption.jsonl') -Content ($badLine + [Environment]::NewLine)

  $badAccounting = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $badAccountingRepo)
  Assert-True -Condition ($badAccounting.ExitCode -ne 0) -Message 'token_accounting fora do conjunto devia ser erro.'
  Assert-Contains -Text $badAccounting.Output -Expected 'token_accounting' -Message 'erro nao identifica o campo.'

  # --- Relatorio: contabilidades nunca se misturam --------------------------
  #
  # O repo de fixture tem uma sessao v2 pequena (do hook) e uma legada gigante.
  # A metrica-alvo tem de sair apenas da v2, e a gigante tem de ficar em quarentena.
  $reporter = Join-Path $PSScriptRoot 'pg_report_token_consumption.ps1'
  $reportRun = Invoke-PowerShellScript -ScriptPath $reporter -Arguments @('-RootPath', $tempRoot)
  Assert-True -Condition ($reportRun.ExitCode -eq 0) -Message "relatorio falhou: $($reportRun.Output)"
  Assert-Contains -Text $reportRun.Output -Expected 'EM QUARENTENA' -Message 'relatorio nao poe a sessao implausivel em quarentena.'
  Assert-Contains -Text $reportRun.Output -Expected 'so contabilidade v2' -Message 'relatorio nao declara que a metrica-alvo e so da contabilidade v2.'

  # --- Identidade: quem fez a sessao, e em que maquina ----------------------
  #
  # O log e commitado e agrega todas as maquinas, mas nao dizia QUEM: o repo_path e
  # identico em toda a frota. Foi isso que obrigou a auditoria do givachoice a pedir
  # extracoes a colegas, maquina a maquina.
  $identRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'identidade'
  & git -C $identRepo init -q 2>$null
  & git -C $identRepo config user.email 'operador.de.teste@parametro.global' 2>$null

  $identOpen = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $identRepo, '-EventType', 'session_open', '-Agent', 'claude')
  Assert-True -Condition ($identOpen.ExitCode -eq 0) -Message "session_open falhou: $($identOpen.Output)"

  $identEvt = @(Get-ConsumptionEvents -RepoPath $identRepo)[0]
  Assert-True -Condition ($identEvt.schema_version -eq '1.3') -Message "schema devia ser 1.3; obtido $($identEvt.schema_version)"
  Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($identEvt.machine)) -Message 'a maquina tem de ficar registada -- e o unico discriminador fiavel entre maquinas'
  Assert-True -Condition ($identEvt.operator -eq 'operador.de.teste@parametro.global') -Message "o operador vem do git do repositorio; obtido '$($identEvt.operator)'"

  # Sem git configurado, 'unknown' -- nunca vazio, que o validador recusa.
  $semGit = New-TokenFixtureRepo -RootPath $tempRoot -Name 'sem_git'
  $semGitOpen = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $semGit, '-EventType', 'session_open', '-Agent', 'claude')
  Assert-True -Condition ($semGitOpen.ExitCode -eq 0) -Message 'sem git configurado o registo nao pode falhar'
  $semGitEvt = @(Get-ConsumptionEvents -RepoPath $semGit)[0]
  Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($semGitEvt.operator)) -Message 'sem git, o operador fica preenchido (unknown) e nao vazio'

  # Identidade explicita tem precedencia sobre a deteccao.
  $expl = Invoke-PowerShellScript -ScriptPath $logger -Arguments @('-RepoPath', $identRepo, '-EventType', 'session_progress', '-Agent', 'claude', '-SessionSummary', 'checkpoint', '-Machine', 'MAQUINA-X', '-Operator', 'outra.pessoa@parametro.global')
  Assert-True -Condition ($expl.ExitCode -eq 0) -Message "session_progress com identidade explicita falhou: $($expl.Output)"
  $explEvt = @(Get-ConsumptionEvents -RepoPath $identRepo | Where-Object { $_.event_type -eq 'session_progress' })[0]
  Assert-True -Condition ($explEvt.machine -eq 'MAQUINA-X') -Message 'a maquina passada explicitamente manda sobre a detectada'
  Assert-True -Condition ($explEvt.operator -eq 'outra.pessoa@parametro.global') -Message 'o operador passado explicitamente manda sobre o detectado'

  # O validador recusa identidade vazia (pior do que ausente: parece preenchida).
  $vazioRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'identidade_vazia'
  $linhaVazia = ([ordered]@{
      schema_version = '1.3'
      event_type = 'session_close'
      occurred_at_utc = '2026-09-11T09:00:00Z'
      session_id = 'ffffffff-0000-4000-8000-000000000003'
      agent = 'claude'
      model = 'modelo-teste'
      repo_name = 'identidade_vazia'
      repo_path = $vazioRepo
      machine = ''
      operator = 'alguem@parametro.global'
      session_summary = 'identidade por preencher'
      estimated_input_tokens = 10
      estimated_output_tokens = 20
    } | ConvertTo-Json -Compress -Depth 6)
  Write-Utf8NoBomFile -Path (Join-Path $vazioRepo '.pg/tokens/consumption.jsonl') -Content ($linhaVazia + [Environment]::NewLine)
  $vazioVal = Invoke-PowerShellScript -ScriptPath $validator -Arguments @('-RepoPath', $vazioRepo)
  Assert-True -Condition ($vazioVal.ExitCode -ne 0) -Message 'machine vazio devia ser erro'
  Assert-Contains -Text $vazioVal.Output -Expected 'machine presente mas vazio' -Message 'o erro nomeia o campo'


  # -------------------------------------------------------------------------
  # Pastas de trabalho declaradas (PG-010 F4)
  # -------------------------------------------------------------------------
  # Boa parte do trabalho de Odoo acontece fora de repositorios. Ate 2026-09-11 esse
  # trabalho era INVISIVEL a medicao, e foi isso que obrigou a auditoria do givachoice a
  # pedir extraccoes maquina a maquina. Uma pasta declarada passa a contar -- mas o log vai
  # para o repositorio do projeto, e nao para a pasta: a pasta nao leva estrutura da
  # framework, que e o desenho do pg_init_work_folder.ps1.
  Write-Host ''
  Write-Host '--- pastas de trabalho declaradas ---'

  $repoDestinoF4 = New-TokenFixtureRepo -RootPath $tempRoot -Name 'repo_destino_f4'
  $pastaDeclarada = Join-Path $tempRoot 'pasta_declarada_f4'
  New-Item -ItemType Directory -Path $pastaDeclarada -Force | Out-Null
  @(
    '# Pasta de trabalho',
    '',
    '<!-- PG_WORK_FOLDER:START (bloco gerido por pg_init_work_folder.ps1 - nao editar aqui) -->',
    'Versao do Odoo: 19.0',
    ('Repositorio do projeto: ' + $repoDestinoF4),
    '<!-- PG_WORK_FOLDER:END (o que estiver fora deste bloco e seu e sobrevive) -->'
  ) | Set-Content -Path (Join-Path $pastaDeclarada 'AGENTS.md') -Encoding utf8

  $payloadF4 = ([ordered]@{
    hook_event_name = 'SessionStart'
    session_id = 'f4decl00-0000-4000-8000-000000000001'
    cwd = $pastaDeclarada
    model = 'claude-opus-5'
  } | ConvertTo-Json -Compress -Depth 4)
  $runF4 = Invoke-HookWithStdin -ScriptPath $hook -JsonPayload $payloadF4
  Assert-True -Condition ($runF4.ExitCode -eq 0) -Message 'hook numa pasta declarada sai com 0'

  $eventosF4 = @(Get-ConsumptionEvents -RepoPath $repoDestinoF4)
  Assert-True -Condition ($eventosF4.Count -eq 1) -Message 'trabalho numa pasta declarada e registado (era invisivel a medicao)'
  if ($eventosF4.Count -eq 1) {
    # O evento e ESCRITO no repositorio mas REGISTA a pasta. Sem esta separacao, o
    # session_open dizia o repositorio e o session_close dizia a pasta: dois eventos da
    # mesma sessao a discordar um do outro.
    Assert-True -Condition ($eventosF4[0].repo_name -eq 'pasta_declarada_f4') -Message 'o evento regista a PASTA onde o trabalho aconteceu'
    Assert-True -Condition ($eventosF4[0].work_folder -eq $true) -Message 'o evento marca-se como trabalho de pasta'
  }
  Assert-True -Condition (-not (Test-Path (Join-Path $pastaDeclarada '.pg'))) -Message 'a pasta NAO ganha estrutura .pg da framework'

  # Sem bloco declarado continua fora: a cobertura e por declaracao explicita, como no
  # PROJECT_PROFILE.json. Uma pasta nao entra na medicao por um script achar que sim.
  $pastaAnonima = Join-Path $tempRoot 'pasta_anonima_f4'
  New-Item -ItemType Directory -Path $pastaAnonima -Force | Out-Null
  $payloadAnon = ([ordered]@{
    hook_event_name = 'SessionStart'
    session_id = 'f4anon000-0000-4000-8000-000000000001'
    cwd = $pastaAnonima
    model = 'claude-opus-5'
  } | ConvertTo-Json -Compress -Depth 4)
  $null = Invoke-HookWithStdin -ScriptPath $hook -JsonPayload $payloadAnon
  Assert-True -Condition ((@(Get-ConsumptionEvents -RepoPath $repoDestinoF4)).Count -eq 1) -Message 'pasta sem bloco declarado nao regista nada'

  # Declarado mas a apontar para um repositorio inexistente: nao regista e NAO rebenta.
  # Um hook que rebente estraga a sessao de quem esta a trabalhar.
  $pastaOrfa = Join-Path $tempRoot 'pasta_orfa_f4'
  New-Item -ItemType Directory -Path $pastaOrfa -Force | Out-Null
  @(
    '<!-- PG_WORK_FOLDER:START -->',
    'Repositorio do projeto: Z:\INEXISTENTE_F4',
    '<!-- PG_WORK_FOLDER:END -->'
  ) | Set-Content -Path (Join-Path $pastaOrfa 'AGENTS.md') -Encoding utf8
  $payloadOrfa = ([ordered]@{
    hook_event_name = 'SessionStart'
    session_id = 'f4orfa000-0000-4000-8000-000000000001'
    cwd = $pastaOrfa
    model = 'claude-opus-5'
  } | ConvertTo-Json -Compress -Depth 4)
  $runOrfa = Invoke-HookWithStdin -ScriptPath $hook -JsonPayload $payloadOrfa
  Assert-True -Condition ($runOrfa.ExitCode -eq 0) -Message 'repositorio declarado inexistente nao faz o hook rebentar'
  Assert-True -Condition ((@(Get-ConsumptionEvents -RepoPath $repoDestinoF4)).Count -eq 1) -Message 'repositorio inexistente nao regista nada'

  Write-Host ""
  Write-Host "--- hook do Codex: releituras de cache fora do input ---"
  # No Codex, `input_tokens` inclui `cached_input_tokens`. Valores de uma sessao real
  # (2026-10-02): 8 711 496 de entrada, dos quais 8 260 992 do cache.
  $codexHook = Join-Path $PSScriptRoot 'pg_hook_codex_log_token_consumption.ps1'
  $codexRepo = New-TokenFixtureRepo -RootPath $tempRoot -Name 'hook_codex'
  $codexRollout = Join-Path $codexRepo 'rollout.jsonl'
  @(
    '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":40,"output_tokens":5}}}}',
    '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":8711496,"cached_input_tokens":8260992,"cache_write_input_tokens":0,"output_tokens":47162}}}}'
  ) | Set-Content -Path $codexRollout -Encoding utf8
  $codexPayload = ([ordered]@{
    hook_event_name = 'Stop'
    session_id = 'c0dex000-0000-4000-8000-000000000001'
    transcript_path = $codexRollout
    cwd = $codexRepo
    model = 'gpt-5'
  } | ConvertTo-Json -Compress -Depth 4)
  $null = Invoke-HookWithStdin -ScriptPath $codexHook -JsonPayload $codexPayload
  $codexFecho = @(Get-ConsumptionEvents -RepoPath $codexRepo)[0]
  Assert-True -Condition ([long]$codexFecho.estimated_input_tokens -eq 450504) -Message "input do Codex devia excluir o cache (450504), veio $($codexFecho.estimated_input_tokens)"
  Assert-True -Condition ([long]$codexFecho.cache_read_input_tokens -eq 8260992) -Message "cache_read do Codex: $($codexFecho.cache_read_input_tokens)"
  Assert-True -Condition ($codexFecho.token_accounting -eq 'unique_input_v2') -Message "token_accounting do Codex: $($codexFecho.token_accounting)"
  Assert-True -Condition ($codexFecho.token_measurement -eq 'measured') -Message "token_measurement do Codex: $($codexFecho.token_measurement)"

  Write-Host 'OK: testes de consumo de tokens concluidos com sucesso'
}
finally {
  if (Test-Path $tempRoot) {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force
  }
}

# Explicito: sem isto o script herdaria o $LASTEXITCODE do ultimo subprocesso
# (que e, de proposito, um validador que falha), reportando 1 apesar de passar.
exit 0
