<#
.SYNOPSIS
  Testes do hook do Antigravity (pg_hook_antigravity.ps1).

.DESCRIPTION
  O Antigravity tem um contrato de hooks diferente do Claude e do Codex: nao ha
  SessionStart, o payload vem em camelCase, o hook corre a partir de `.agents/` e o
  stdout tem de ser um objeto JSON. Estes testes correm o hook como o Antigravity o
  corre e verificam:
  - a primeira PreInvocation de uma conversa corre o passo 2 do ritual, abre a sessao
    no log e injeta o resultado no contexto;
  - as PreInvocation seguintes nao fazem nada (dispara antes de cada chamada ao modelo);
  - o Stop mantem um unico session_close por sessao, e o log continua valido;
  - fora de um repositorio da framework, ou com stdin invalido, sai um JSON valido e
    nada e escrito.
#>
param()

$ErrorActionPreference = "Stop"

function Assert-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { throw $Message }
}

$hookSource = Join-Path $PSScriptRoot "pg_hook_antigravity.ps1"
$loggerSource = Join-Path $PSScriptRoot "pg_log_token_consumption.ps1"
$validator = Join-Path $PSScriptRoot "pg_validate_token_consumption.ps1"

function New-TestRepo {
  param([string]$Root, [switch]$SemPg)
  $repo = Join-Path $Root ([guid]::NewGuid().ToString('N').Substring(0, 8))
  $scripts = Join-Path $repo ".pg_framework\scripts"
  New-Item -ItemType Directory -Path $scripts -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $repo ".agents") -Force | Out-Null
  if (-not $SemPg) { New-Item -ItemType Directory -Path (Join-Path $repo ".pg") -Force | Out-Null }
  Copy-Item $hookSource $scripts
  Copy-Item $loggerSource $scripts
  # O passo 2 real faz git pull do _pg_template; aqui so interessa que corre e que o
  # que escreve (Write-Host incluido) chega ao contexto sem sujar o stdout do hook.
  Set-Content -Path (Join-Path $scripts "pg_ensure_framework_current.ps1") -Encoding ASCII -Value @'
param([string]$RepoPath)
Write-Host "ENSURE-STUB host $RepoPath"
Write-Output "ENSURE-STUB output"
'@
  return $repo
}

function Invoke-Hook {
  param([string]$Repo, [string]$Evento, [string]$Stdin)
  $saved = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  Push-Location (Join-Path $Repo ".agents")
  try {
    $out = ($Stdin | & powershell -NoProfile -ExecutionPolicy Bypass -File "..\.pg_framework\scripts\pg_hook_antigravity.ps1" -Evento $Evento | Out-String).Trim()
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Stdout = $out }
  }
  finally {
    Pop-Location
    $ErrorActionPreference = $saved
  }
}

function New-Payload {
  param([string]$ConversationId, [string]$Repo)
  return (@{ conversationId = $ConversationId; workspacePaths = @($Repo); transcriptPath = ""; modelName = "auto" } | ConvertTo-Json -Compress)
}

function Get-Events {
  param([string]$Repo)
  $path = Join-Path $Repo ".pg\tokens\consumption.jsonl"
  if (-not (Test-Path $path)) { return @() }
  return @([System.IO.File]::ReadAllLines($path) | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
}

$root = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_test_antigravity_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $root -Force | Out-Null
$failures = 0

function Test-Case {
  param([string]$Name, [scriptblock]$Body)
  try { & $Body; Write-Host "PASS: $Name" }
  catch { $script:failures++; Write-Host "FAIL: $Name -> $($_.Exception.Message)" }
}

try {
  Test-Case "primeira PreInvocation corre o passo 2, abre a sessao e injeta o contexto" {
    $repo = New-TestRepo -Root $root
    $id = [guid]::NewGuid().ToString()
    $r = Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin (New-Payload $id $repo)
    Assert-True ($r.ExitCode -eq 0) "exit code $($r.ExitCode)"
    $json = $r.Stdout | ConvertFrom-Json
    $msg = [string]$json.injectSteps[0].ephemeralMessage
    Assert-True ($msg -match 'ENSURE-STUB host') "o Write-Host do passo 2 nao chegou ao contexto: $msg"
    Assert-True ($msg -match 'AGENTS_SHARED\.md') "a mensagem nao manda ler o AGENTS_SHARED.md"
    Assert-True ($msg -match [regex]::Escape($id)) "a mensagem nao indica o session_id"
    $ev = @(Get-Events $repo)
    Assert-True ($ev.Count -eq 1) "esperado 1 evento, ha $($ev.Count)"
    Assert-True ($ev[0].event_type -eq 'session_open' -and $ev[0].agent -eq 'antigravity' -and $ev[0].session_id -eq $id) "session_open incorreto"
  }

  Test-Case "PreInvocation seguinte da mesma conversa nao faz nada" {
    $repo = New-TestRepo -Root $root
    $id = [guid]::NewGuid().ToString()
    Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin (New-Payload $id $repo) | Out-Null
    $r = Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin (New-Payload $id $repo)
    Assert-True ($r.Stdout -eq '{}') "esperado {}, veio: $($r.Stdout)"
    Assert-True (@(Get-Events $repo).Count -eq 1) "a segunda invocacao escreveu no log"
  }

  Test-Case "Stop mantem um unico session_close por sessao e o log fica valido" {
    $repo = New-TestRepo -Root $root
    $id = [guid]::NewGuid().ToString()
    Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin (New-Payload $id $repo) | Out-Null
    $r1 = Invoke-Hook -Repo $repo -Evento Stop -Stdin (New-Payload $id $repo)
    $r2 = Invoke-Hook -Repo $repo -Evento Stop -Stdin (New-Payload $id $repo)
    Assert-True ((($r2.Stdout | ConvertFrom-Json).decision) -eq 'allow') "Stop devolveu: $($r2.Stdout)"
    $closes = @(Get-Events $repo | Where-Object { $_.event_type -eq 'session_close' })
    Assert-True ($closes.Count -eq 1) "esperado 1 session_close, ha $($closes.Count)"
    Assert-True ($closes[0].token_measurement -eq 'unknown') "tokens declarados sem formato validado"
    $saved = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $v = & powershell -NoProfile -ExecutionPolicy Bypass -File $validator -RepoPath $repo 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = $saved
    Assert-True ($code -eq 0) "validador reprovou o log: $v"
  }

  Test-Case "Stop le os tokens do transcript sem somar releituras e sem falso read_mode api" {
    $repo = New-TestRepo -Root $root
    $id = [guid]::NewGuid().ToString()
    # Formato observado na primeira sessao real (2026-10-07). O passo GENERIC traz o
    # conteudo do AGENTS_SHARED.md, que fala de jsonrpc: nao pode marcar a sessao como api.
    $transcript = Join-Path $repo "transcript.jsonl"
    $linhas = @(
      '{"step_index":0,"type":"USER_INPUT","content":"<USER_REQUEST>\nQual a versao Odoo?\n</USER_REQUEST>\n<ADDITIONAL_METADATA>x</ADDITIONAL_METADATA>"}',
      '{"step_index":1,"type":"EPHEMERAL_MESSAGE","content":"PG FRAMEWORK"}',
      '{"step_index":2,"type":"PLANNER_RESPONSE","input_tokens":29134,"cache_read_tokens":0,"output_tokens":103,"tool_calls":[{"name":"view_file","args":{"AbsolutePath":"AGENTS_SHARED.md"}}]}',
      '{"step_index":3,"type":"GENERIC","content":"Os endpoints /jsonrpc e /xmlrpc saem do core; api_key pessoal"}',
      '{"step_index":4,"type":"PLANNER_RESPONSE","input_tokens":4851,"cache_read_tokens":24485,"output_tokens":134,"content":"Odoo 19.0"}'
    )
    [System.IO.File]::WriteAllLines($transcript, $linhas, (New-Object System.Text.UTF8Encoding($false)))
    $payload = (@{ conversationId = $id; workspacePaths = @($repo); transcriptPath = $transcript; modelName = "gemini-teste" } | ConvertTo-Json -Compress)
    Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin $payload | Out-Null
    Invoke-Hook -Repo $repo -Evento Stop -Stdin $payload | Out-Null
    $close = @(Get-Events $repo | Where-Object { $_.event_type -eq 'session_close' })[0]
    Assert-True ($close.estimated_input_tokens -eq 33985) "input esperado 33985 (sem releituras), veio $($close.estimated_input_tokens)"
    Assert-True ($close.cache_read_input_tokens -eq 24485) "cache_read esperado 24485, veio $($close.cache_read_input_tokens)"
    Assert-True ($close.estimated_output_tokens -eq 237) "output esperado 237, veio $($close.estimated_output_tokens)"
    Assert-True ($close.token_accounting -eq 'unique_input_v2') "token_accounting: $($close.token_accounting)"
    Assert-True ($close.read_mode -eq 'mirror') "read_mode deveria ser mirror (o jsonrpc vem do conteudo lido), veio $($close.read_mode)"
    Assert-True ($close.session_summary -eq 'Qual a versao Odoo?') "resumo: $($close.session_summary)"
  }

  Test-Case "chamada real a API do Odoo marca read_mode api" {
    $repo = New-TestRepo -Root $root
    $id = [guid]::NewGuid().ToString()
    $transcript = Join-Path $repo "transcript.jsonl"
    $linhas = @('{"step_index":0,"type":"PLANNER_RESPONSE","input_tokens":10,"cache_read_tokens":0,"output_tokens":5,"tool_calls":[{"name":"run_command","args":{"CommandLine":"powershell -File .pg_framework\\scripts\\pg_odoo_client_query.ps1 -Model res.partner"}}]}')
    [System.IO.File]::WriteAllLines($transcript, $linhas, (New-Object System.Text.UTF8Encoding($false)))
    $payload = (@{ conversationId = $id; workspacePaths = @($repo); transcriptPath = $transcript; modelName = "m" } | ConvertTo-Json -Compress)
    Invoke-Hook -Repo $repo -Evento Stop -Stdin $payload | Out-Null
    $close = @(Get-Events $repo | Where-Object { $_.event_type -eq 'session_close' })[0]
    Assert-True ($close.read_mode -eq 'api') "read_mode deveria ser api, veio $($close.read_mode)"
  }

  Test-Case "fora de um repositorio da framework nao escreve nada" {
    $repo = New-TestRepo -Root $root -SemPg
    $r = Invoke-Hook -Repo $repo -Evento PreInvocation -Stdin (New-Payload ([guid]::NewGuid().ToString()) $repo)
    Assert-True ($r.Stdout -eq '{}') "esperado {}, veio: $($r.Stdout)"
    Assert-True (-not (Test-Path (Join-Path $repo ".pg"))) "criou .pg num repositorio fora da framework"
  }

  Test-Case "stdin invalido devolve JSON valido e exit 0" {
    $repo = New-TestRepo -Root $root
    $r = Invoke-Hook -Repo $repo -Evento Stop -Stdin "isto nao e json"
    Assert-True ($r.ExitCode -eq 0) "exit code $($r.ExitCode)"
    $null = $r.Stdout | ConvertFrom-Json
  }
}
finally {
  Remove-Item -Recurse -Force $root -ErrorAction SilentlyContinue
}

if ($failures -gt 0) { Write-Host "$failures teste(s) falharam."; exit 1 }
Write-Host "Todos os testes do hook do Antigravity passaram."
exit 0
