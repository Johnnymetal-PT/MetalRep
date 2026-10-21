<#
.SYNOPSIS
  Testes do pg_ensure_framework_current.ps1 -- em especial, que a arvore suja nao trava o pull.

.DESCRIPTION
  O que se testa e a diferenca entre "o git recusa este ficheiro" e "nao puxo de todo".
  Ate 2026-09-28 o script recusava o pull so por haver alteracoes locais, e como trabalhar
  na framework escreve no log de tokens dela -- que e versionado -- a arvore suja-se
  sozinha: 17 dias sem uma unica atualizacao nesta maquina, por causa de tres ficheiros
  em que nenhum commit tocava.

  Monta um origin de mentira (bare), um clone que faz de framework e um projeto com a
  junction .pg_framework. O passo 2 (sync) e neutralizado por um pg_sync_shared_assets.ps1
  vazio dentro do clone, para o teste nao ir buscar o do framework verdadeiro.
#>

$ErrorActionPreference = 'Stop'
$script:Total = 0
$alvo = Join-Path $PSScriptRoot 'pg_ensure_framework_current.ps1'

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:Total += 1
  if (-not $Condition) { throw ("FALHA: $Message`n--- ultima saida ---`n" + $script:UltimaSaida) }
  Write-Host "  OK   $Message"
}

function Git-Silencioso {
  param([string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & git @Arguments 2>&1 | Out-Null }
  finally { $ErrorActionPreference = $anterior }
}

function Invoke-Alvo {
  param([string]$Projeto)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $alvo -RepoPath $Projeto 2>&1
    $script:UltimaSaida = (($saida | ForEach-Object { "$_" }) -join "`n")
    return @{ Exit = $LASTEXITCODE; Texto = $script:UltimaSaida }
  }
  finally { $ErrorActionPreference = $anterior }
}

$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_test_ensure_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $raiz -Force | Out-Null

try {
  Write-Host "=== pg_test_ensure_framework_current ==="

  $origem = Join-Path $raiz 'origem.git'
  Git-Silencioso @('init', '--bare', '-q', $origem)

  $semear = Join-Path $raiz 'semear'
  Git-Silencioso @('clone', '-q', $origem, $semear)
  Git-Silencioso @('-C', $semear, 'config', 'user.email', 'teste@parametro.global')
  Git-Silencioso @('-C', $semear, 'config', 'user.name', 'Teste')
  New-Item -ItemType Directory -Path (Join-Path $semear 'scripts') -Force | Out-Null
  # Neutraliza o passo 2: o sync do framework verdadeiro nao deve correr num teste.
  # O stub deixa uma marca no projeto, para o teste saber se o passo 2 re-sincronizou.
  [System.IO.File]::WriteAllText((Join-Path $semear 'scripts\pg_sync_shared_assets.ps1'), "param([string]`$RepoName, [string]`$RepoPath)`nSet-Content -Path (Join-Path `$RepoPath 'sync_correu.txt') -Value x`nexit 0`n")
  [System.IO.File]::WriteAllText((Join-Path $semear 'a.txt'), "a1`n")
  [System.IO.File]::WriteAllText((Join-Path $semear 'b.txt'), "b1`n")
  Git-Silencioso @('-C', $semear, 'add', '-A')
  Git-Silencioso @('-C', $semear, 'commit', '-q', '-m', 'inicial')
  Git-Silencioso @('-C', $semear, 'push', '-q', 'origin', 'HEAD:refs/heads/main')

  $framework = Join-Path $raiz 'framework'
  Git-Silencioso @('clone', '-q', '-b', 'main', $origem, $framework)
  Git-Silencioso @('-C', $framework, 'config', 'user.email', 'teste@parametro.global')
  Git-Silencioso @('-C', $framework, 'config', 'user.name', 'Teste')

  $projeto = Join-Path $raiz 'projeto'
  New-Item -ItemType Directory -Path $projeto -Force | Out-Null
  New-Item -ItemType Junction -Path (Join-Path $projeto '.pg_framework') -Target $framework | Out-Null

  # --- 1. arvore suja num ficheiro em que o commit novo NAO toca: puxa na mesma ------
  [System.IO.File]::WriteAllText((Join-Path $semear 'a.txt'), "a2`n")
  Git-Silencioso @('-C', $semear, 'commit', '-q', '-am', 'mexe no a')
  Git-Silencioso @('-C', $semear, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
  [System.IO.File]::WriteAllText((Join-Path $framework 'b.txt'), "b local`n")

  $r = Invoke-Alvo -Projeto $projeto
  Assert-True ($r.Texto -match 'framework atualizado ao origin') "arvore suja num ficheiro que o pull nao pisa: atualiza na mesma"
  Assert-True ((Get-Content (Join-Path $framework 'a.txt') -Raw).Trim() -eq 'a2') "o conteudo novo chegou ao framework"
  Assert-True ((Get-Content (Join-Path $framework 'b.txt') -Raw).Trim() -eq 'b local') "a alteracao local ficou intacta"

  # --- 2. arvore suja no MESMO ficheiro que o commit novo toca: git recusa -----------
  [System.IO.File]::WriteAllText((Join-Path $semear 'b.txt'), "b2`n")
  Git-Silencioso @('-C', $semear, 'commit', '-q', '-am', 'mexe no b')
  Git-Silencioso @('-C', $semear, 'push', '-q', 'origin', 'HEAD:refs/heads/main')

  $r = Invoke-Alvo -Projeto $projeto
  Assert-True ($r.Exit -eq 0) "pull recusado nao quebra a sessao"
  Assert-True ($r.Texto -match "falhou com 1 ficheiro") "diz que a causa sao ficheiros por commitar"
  Assert-True ($r.Texto -match 'b\.txt') "nomeia o ficheiro que trava o pull"
  Assert-True ($r.Texto -match 'Commitar ou guardar') "diz o que fazer para o pull passar"

  # --- 3. arvore limpa e ja atualizada ----------------------------------------------
  Git-Silencioso @('-C', $framework, 'checkout', '--', 'b.txt')
  $r = Invoke-Alvo -Projeto $projeto
  Assert-True ($r.Texto -match 'framework atualizado ao origin|framework ja estava atualizado') "arvore limpa: puxa sem ruido"

  # --- 4. drift so quando mudam ficheiros que o sync copia (tarefa 8014) -------------
  # Ate 2026-10-08 qualquer commit na framework punha a frota em drift: o passo 2
  # re-sincronizava em todos os projetos e deixava-os com ficheiros por commitar.
  function Set-EstadoSync {
    $head = ((& git -C $framework rev-parse HEAD) -join '').Trim()
    New-Item -ItemType Directory -Path (Join-Path $projeto '.pg') -Force | Out-Null
    Set-Content -Path (Join-Path $projeto '.pg\PG_TEMPLATE_SYNC_STATE.json') -Value ('{ "template_git_head": "' + $head + '" }') -Encoding ascii
    Remove-Item (Join-Path $projeto 'sync_correu.txt') -ErrorAction SilentlyContinue
  }
  Set-EstadoSync
  [System.IO.File]::WriteAllText((Join-Path $semear 'a.txt'), "a3`n")
  Git-Silencioso @('-C', $semear, 'commit', '-q', '-am', 'documentacao: nada que o sync copie')
  Git-Silencioso @('-C', $semear, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
  $r = Invoke-Alvo -Projeto $projeto
  Assert-True ($r.Texto -match 'projeto sincronizado com o framework') "commit fora das fontes do sync: o projeto continua sincronizado"
  Assert-True (-not (Test-Path (Join-Path $projeto 'sync_correu.txt'))) "e o sync nao corre (a frota nao fica com ficheiros por commitar)"

  Set-EstadoSync
  New-Item -ItemType Directory -Path (Join-Path $semear 'templates') -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $semear 'templates\AGENTS.md'), "contrato novo`n")
  Git-Silencioso @('-C', $semear, 'add', '-A')
  Git-Silencioso @('-C', $semear, 'commit', '-q', '-m', 'muda um ficheiro sincronizado')
  Git-Silencioso @('-C', $semear, 'push', '-q', 'origin', 'HEAD:refs/heads/main')
  $r = Invoke-Alvo -Projeto $projeto
  Assert-True ($r.Texto -match 'DRIFT') "commit em templates/: e drift"
  Assert-True (Test-Path (Join-Path $projeto 'sync_correu.txt')) "e o sync corre"

  Set-Content -Path (Join-Path $projeto '.pg\PG_TEMPLATE_SYNC_STATE.json') -Value '{ "template_git_head": "0000000000000000000000000000000000000000" }' -Encoding ascii
  Remove-Item (Join-Path $projeto 'sync_correu.txt') -ErrorAction SilentlyContinue
  $r = Invoke-Alvo -Projeto $projeto
  Assert-True (Test-Path (Join-Path $projeto 'sync_correu.txt')) "head registado desconhecido neste clone: na duvida re-sincroniza"

  Write-Host ""
  Write-Host "OK: $script:Total verificacoes."
}
finally {
  Remove-Item -Recurse -Force $raiz -ErrorAction SilentlyContinue
}
