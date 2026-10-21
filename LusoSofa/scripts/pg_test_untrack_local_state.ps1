<#
.SYNOPSIS
  Testes deterministas do desversionamento de estado local em pg_sync_shared_assets.ps1.

.DESCRIPTION
  O `.pg/PREFLIGHT.json` e estado local da maquina: e regenerado a cada arranque e traz
  o path absoluto de quem correu o preflight. A v2.20.0 acrescentou-o ao `.gitignore` do
  template, mas o `.gitignore` nao desversiona o que ja esta seguido -- ficava ignorado
  E seguido ao mesmo tempo, a gerar conflito em cada merge da frota.

  Verifica que o sync o retira do indice sem o apagar do disco, que e idempotente, e que
  nao mexe em ficheiros do projeto.

  Nao toca em repositorios reais nem na rede.
#>
param(
  [switch]$KeepTemp
)

# O git escreve avisos no stderr; com Stop cada aviso virava erro terminante.
$ErrorActionPreference = "Continue"

$script:Falhas = 0
$script:Total = 0

function Assert-Equal {
  param($Esperado, $Obtido, [string]$Mensagem)

  $script:Total++
  if ("$Esperado" -eq "$Obtido") {
    Write-Host "  OK   $Mensagem"
  }
  else {
    Write-Host "  FAIL $Mensagem"
    Write-Host "         esperado: '$Esperado'"
    Write-Host "         obtido  : '$Obtido'"
    $script:Falhas++
  }
}

function Assert-True {
  param([bool]$Condicao, [string]$Mensagem)
  Assert-Equal -Esperado $true -Obtido $Condicao -Mensagem $Mensagem
}

function Invoke-GitQuiet {
  param([string]$RepoPath, [string[]]$Arguments)
  & git -C $RepoPath @Arguments *> $null
}

function Test-Seguido {
  param([string]$RepoPath, [string]$Relativo)
  $r = @(& git -C $RepoPath ls-files $Relativo 2> $null)
  return ($r.Count -gt 0)
}

$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ("pg-untrack-test-" + [Guid]::NewGuid().ToString('N'))
$repo = Join-Path $raiz 'ProjetoFalso'
New-Item -ItemType Directory -Path $repo -Force | Out-Null

try {
  Write-Host "=== andaime em $raiz ==="

  Invoke-GitQuiet -RepoPath $repo -Arguments @('init', '-b', 'brodoo')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'core.autocrlf', 'false')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'user.email', 'teste@parametro.global')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'user.name', 'Teste PG')

  # o estado local versionado, como esta hoje em 11 repositorios da frota
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg') -Force | Out-Null
  Set-Content -Path (Join-Path $repo '.pg\PREFLIGHT.json') -Value '{"repo_path":"C:/caminho/da/outra/maquina"}' -Encoding utf8
  # um ficheiro do projeto que o sync nao pode tocar
  Set-Content -Path (Join-Path $repo 'modulo_do_projeto.py') -Value '# codigo' -Encoding utf8
  # e um .log, que o bloco do .gitignore ignora mas o projeto versiona de proposito:
  # uma varredura pelas regras do bloco desversionaria isto por inferencia
  Set-Content -Path (Join-Path $repo 'auditoria_intencional.log') -Value 'registo que o projeto quer versionado' -Encoding utf8

  Invoke-GitQuiet -RepoPath $repo -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('commit', '-m', 'estado inicial')

  Assert-True (Test-Seguido -RepoPath $repo -Relativo '.pg/PREFLIGHT.json') 'ponto de partida: PREFLIGHT.json versionado'

  $sync = Join-Path $PSScriptRoot 'pg_sync_shared_assets.ps1'
  $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $sync -RepoName 'ProjetoFalso' -RepoPath $repo 2>&1
  $texto = (($saida | ForEach-Object { "$_" }) -join "`n")

  Write-Host ""
  Write-Host "--- desversiona sem apagar ---"
  Assert-True (-not (Test-Seguido -RepoPath $repo -Relativo '.pg/PREFLIGHT.json')) 'PREFLIGHT.json saiu do indice'
  Assert-True (Test-Path (Join-Path $repo '.pg\PREFLIGHT.json')) 'PREFLIGHT.json continua no disco'
  Assert-True ($texto -match 'desversionado') 'o sync reporta o desversionamento'

  Write-Host ""
  Write-Host "--- nao mexe no que e do projeto ---"
  Assert-True (Test-Seguido -RepoPath $repo -Relativo 'modulo_do_projeto.py') 'o codigo do projeto continua versionado'
  Assert-True (Test-Seguido -RepoPath $repo -Relativo 'auditoria_intencional.log') 'um .log versionado de proposito nao e desversionado por inferencia'

  Write-Host ""
  Write-Host "--- idempotente ---"
  Invoke-GitQuiet -RepoPath $repo -Arguments @('commit', '-am', 'aplicar o sync')
  $saida2 = & powershell -NoProfile -ExecutionPolicy Bypass -File $sync -RepoName 'ProjetoFalso' -RepoPath $repo 2>&1
  Assert-Equal 0 $LASTEXITCODE 'segunda passagem termina sem erro'
  Assert-True (-not (Test-Seguido -RepoPath $repo -Relativo '.pg/PREFLIGHT.json')) 'continua fora do indice'
  Assert-True (Test-Path (Join-Path $repo '.pg\PREFLIGHT.json')) 'continua no disco'

  Write-Host ""
  Write-Host "--- o .gitignore passa a ignora-lo ---"
  $ign = @(& git -C $repo check-ignore '.pg/PREFLIGHT.json' 2> $null)
  Assert-True ($ign.Count -gt 0) 'o bloco da framework ignora o PREFLIGHT.json'

  Write-Host ""
  if ($script:Falhas -eq 0) {
    Write-Host "OK: $($script:Total) verificacoes passaram."
  }
  else {
    Write-Host "ERRO: $($script:Falhas) de $($script:Total) verificacoes falharam."
  }
}
catch {
  Write-Host ""
  Write-Host "ERRO no andaime do teste: $($_.Exception.Message)"
  Write-Host "  em: $($_.InvocationInfo.PositionMessage)"
  $script:Falhas++
}
finally {
  if ($KeepTemp) {
    Write-Host "andaime preservado em $raiz"
  }
  else {
    Remove-Item $raiz -Recurse -Force -ErrorAction SilentlyContinue
  }
}

if ($script:Falhas -gt 0) { exit 1 }
exit 0
