<#
.SYNOPSIS
  Testes do bootstrap automatico na primeira sessao (pg_auto_bootstrap.ps1).

.DESCRIPTION
  O hook corre no arranque de TODAS as sessoes da maquina, em qualquer pasta. Por isso
  metade destes testes e sobre o que ele NAO pode fazer: tocar num repositorio que nao
  esta ligado a um projeto no Brodoo, no proprio framework, numa pasta de trabalho, ou
  adivinhar uma versao Odoo que ninguem declarou.

  O Brodoo e substituido por um ficheiro JSON (-BrodooLookupPath) e o source Odoo global
  por uma raiz falsa (PG_ODOO_SOURCE_ROOT), para decidir "ligar" / "adiar" / "clonar"
  sem rede. Os casos de decisao correm com -WhatIf; o ultimo faz um bootstrap real num
  repositorio temporario, contra o source global verdadeiro desta maquina se a serie
  19.0 existir (ligacao sem fetch), e salta-se se nao existir.
#>
param(
  [switch]$SemBootstrapReal
)

$ErrorActionPreference = 'Stop'

$script:Total = 0
$alvo = Join-Path $PSScriptRoot 'pg_auto_bootstrap.ps1'
$templateRoot = Split-Path -Parent $PSScriptRoot

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:Total += 1
  if (-not $Condition) { throw "FALHA: $Message" }
  Write-Host "  OK   $Message"
}

function Invoke-Auto {
  param([string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $alvo @Arguments 2>&1
    $codigo = $LASTEXITCODE
  }
  finally { $ErrorActionPreference = $anterior }
  return [pscustomobject]@{
    Texto = (($saida | ForEach-Object { "$_" }) -join "`n").Trim()
    Exit  = $codigo
  }
}

function Invoke-Git {
  param([string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & git @Arguments 2>&1 | Out-Null }
  finally { $ErrorActionPreference = $anterior }
}

function New-Repo {
  # Repositorio git com um commit e um origin GitHub (nunca contactado: so o URL conta).
  param([string]$Nome, [switch]$SemCommits)
  $p = Join-Path $script:Raiz $Nome
  New-Item -ItemType Directory -Path $p -Force | Out-Null
  Invoke-Git @('-C', $p, 'init', '-b', 'main')
  Invoke-Git @('-C', $p, 'config', 'user.email', 'teste@parametro.global')
  Invoke-Git @('-C', $p, 'config', 'user.name', 'Teste')
  Invoke-Git @('-C', $p, 'remote', 'add', 'origin', "https://github.com/parametroglobaladmin/$Nome.git")
  if (-not $SemCommits) {
    [System.IO.File]::WriteAllText((Join-Path $p 'README.md'), "teste`n")
    Invoke-Git @('-C', $p, 'add', 'README.md')
    Invoke-Git @('-C', $p, 'commit', '-m', 'inicial')
  }
  return $p
}

function New-Lookup {
  param([string]$Nome, [object[]]$Projetos)
  $f = Join-Path $script:Raiz "$Nome.lookup.json"
  $json = if ($Projetos.Count -eq 0) { '[]' } else { ConvertTo-Json -InputObject @($Projetos) -Depth 5 }
  [System.IO.File]::WriteAllText($f, $json, (New-Object System.Text.UTF8Encoding($false)))
  return $f
}

function Projeto {
  param([string]$Key = 'odoo-teste', $Versao = '19.0', [string]$Edicao = 'enterprise', [string]$Branch = 'brodoo')
  return [ordered]@{ id = 1; name = "Odoo - $Key"; pg_project_key = $Key; pg_repo_branch = $Branch; pg_odoo_version = $Versao; pg_odoo_edition = $Edicao }
}

$script:Raiz = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_test_auto_bootstrap_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $script:Raiz -Force | Out-Null

$fonteFalsa = Join-Path $script:Raiz 'odoo_src'
New-Item -ItemType Directory -Path (Join-Path $fonteFalsa '19.0\community\.git') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $fonteFalsa '19.0\enterprise\.git') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $fonteFalsa '18.0\community\.git') -Force | Out-Null

$fonteAnterior = $env:PG_ODOO_SOURCE_ROOT
$desligadoAnterior = $env:PG_AUTO_BOOTSTRAP
$env:PG_ODOO_SOURCE_ROOT = $fonteFalsa
$logsAnterior = $env:PG_AUTO_BOOTSTRAP_LOG_DIR
$env:PG_AUTO_BOOTSTRAP_LOG_DIR = Join-Path $script:Raiz 'logs'
Remove-Item Env:\PG_AUTO_BOOTSTRAP -ErrorAction SilentlyContinue

try {
  Write-Host "=== pg_test_auto_bootstrap ==="

  Write-Host "-- o que nunca se toca"
  $semGit = Join-Path $script:Raiz 'nao_repo'
  New-Item -ItemType Directory -Path $semGit -Force | Out-Null
  $r = Invoke-Auto @('-RepoPath', $semGit, '-Hook')
  Assert-True ($r.Exit -eq 0 -and $r.Texto -eq '') "pasta sem git: hook sai com 0 e em silencio"

  $ja = New-Repo 'ja_bootstrapado'
  New-Item -ItemType Directory -Path (Join-Path $ja '.pg_framework') -Force | Out-Null
  $r = Invoke-Auto @('-RepoPath', $ja, '-Hook', '-BrodooLookupPath', (New-Lookup 'ja' @((Projeto))))
  Assert-True ($r.Exit -eq 0 -and $r.Texto -eq '') "repo ja bootstrapado: silencio"

  $r = Invoke-Auto @('-RepoPath', $templateRoot, '-Hook', '-BrodooLookupPath', (New-Lookup 'tpl' @((Projeto))))
  Assert-True ($r.Exit -eq 0 -and $r.Texto -eq '') "o proprio _pg_template: silencio, mesmo com projeto no Brodoo"

  $r = Invoke-Auto @('-RepoPath', $templateRoot, '-WhatIf', '-BrodooLookupPath', (New-Lookup 'tpl2' @((Projeto))))
  Assert-True ($r.Texto -match 'proprio framework' -and $r.Texto -notmatch 'PLANO') "o proprio _pg_template em modo manual: diz porque e nao planeia"

  $wf = New-Repo 'pasta_trabalho'
  [System.IO.File]::WriteAllText((Join-Path $wf 'AGENTS.md'), "<!-- PG_WORK_FOLDER:START -->`nx`n<!-- PG_WORK_FOLDER:END -->`n")
  $r = Invoke-Auto @('-RepoPath', $wf, '-Hook', '-BrodooLookupPath', (New-Lookup 'wf' @((Projeto))))
  Assert-True ($r.Texto -eq '') "pasta de trabalho declarada: silencio"

  $prod = New-Repo 'repo_produto'
  New-Item -ItemType Directory -Path (Join-Path $prod '.pg') -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $prod '.pg\PROJECT_PROFILE.json'), '{"schema_version":"1.1","brodoo_mirror_applicable":false}')
  $r = Invoke-Auto @('-RepoPath', $prod, '-Hook', '-BrodooLookupPath', (New-Lookup 'prod' @((Projeto))))
  Assert-True ($r.Texto -eq '') "repositorio de produto (brodoo_mirror_applicable false): silencio"

  $semProj = New-Repo 'sem_projeto'
  $vazio = New-Lookup 'vazio' @()
  $r = Invoke-Auto @('-RepoPath', $semProj, '-Hook', '-BrodooLookupPath', $vazio)
  Assert-True ($r.Texto -eq '') "sem projeto no Brodoo, fora da pasta dos repos: hook em silencio"
  Assert-True (-not (Test-Path (Join-Path $semProj 'AGENTS.md'))) "sem projeto no Brodoo: nada escrito"

  $r = Invoke-Auto @('-RepoPath', $semProj, '-BrodooLookupPath', $vazio)
  Assert-True ($r.Texto -match 'nao foi feito nada' -and $r.Texto -match '-SemBrodoo' -and $r.Texto -match '<SERIE>') "sem projeto, modo manual: explica e deixa o comando com a serie por preencher"

  # Sem chave pessoal, o hook nao consulta o Brodoo -- nem com a chave partilhada do
  # utilizador Brodoo, que a cascata ainda aceita. Sem -BrodooLookupPath, e sem rede: a
  # recusa acontece antes de qualquer pedido.
  $credAnterior = $env:PG_ODOO_CREDENTIALS_FILE
  $keyAnterior = $env:PG_ODOO_API_KEY
  $tokAnterior = $env:PG_ODOO_KNOWLEDGE_TOKEN
  $env:PG_ODOO_CREDENTIALS_FILE = Join-Path $script:Raiz 'nao_existe.json'
  Remove-Item Env:\PG_ODOO_API_KEY, Env:\PG_ODOO_KNOWLEDGE_TOKEN -ErrorAction SilentlyContinue
  try {
    $semChave = New-Repo 'sem_chave_pessoal'
    $r = Invoke-Auto @('-RepoPath', $semChave)
    $rSem = Invoke-Auto @('-RepoPath', (New-Repo 'sem_chave_sem_brodoo'), '-SemBrodoo', '-WhatIf', '-Series', '19.0')
  }
  finally {
    $env:PG_ODOO_CREDENTIALS_FILE = $credAnterior
    if ($null -ne $keyAnterior) { $env:PG_ODOO_API_KEY = $keyAnterior }
    if ($null -ne $tokAnterior) { $env:PG_ODOO_KNOWLEDGE_TOKEN = $tokAnterior }
  }
  Assert-True ($r.Texto -match 'nao foi feito nada' -and $r.Texto -match 'pg_init_odoo_credentials\.ps1') "sem chave pessoal: nao consulta o Brodoo e diz como configurar"
  Assert-True (-not (Test-Path (Join-Path $semChave 'AGENTS.md'))) "sem chave pessoal: nada escrito"
  Assert-True ($rSem.Texto -match 'templates=copia versionada') "sem chave pessoal e -SemBrodoo: templates nao vem do Odoo (a cascata cairia na chave partilhada)"

  $env:PG_AUTO_BOOTSTRAP = '0'
  $r = Invoke-Auto @('-RepoPath', (New-Repo 'desligado'), '-Hook', '-BrodooLookupPath', (New-Lookup 'desl' @((Projeto))))
  Remove-Item Env:\PG_AUTO_BOOTSTRAP
  Assert-True ($r.Texto -eq '') "PG_AUTO_BOOTSTRAP=0 desliga"

  Write-Host "-- versao, edicao e branch"
  $a = New-Repo 'normal'
  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'n' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=19\.0 origem=Brodoo') "serie vem do Brodoo"
  Assert-True ($r.Texto -match 'edicao=enterprise') "edicao vem do Brodoo"
  Assert-True ($r.Texto -match 'source=ligar') "serie ja na maquina: liga sem fetch"
  Assert-True ($r.Texto -match 'branch=brodoo') "branch standard"
  Assert-True ($r.Texto -match 'templates=copia versionada') "no arranque, templates da copia versionada (sem ir ao Odoo)"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'n17' @((Projeto -Versao '17.0'))))
  Assert-True ($r.Texto -match 'serie=17\.0' -and $r.Texto -match 'source=adiar') "serie ausente da maquina, no hook: clone adiado"
  $r = Invoke-Auto @('-RepoPath', $a, '-WhatIf', '-BrodooLookupPath', (New-Lookup 'n17b' @((Projeto -Versao '17.0'))))
  Assert-True ($r.Texto -match 'source=clonar') "serie ausente, em modo manual: clona"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'n18c' @((Projeto -Versao '18.0' -Edicao 'enterprise'))))
  Assert-True ($r.Texto -match 'source=adiar') "enterprise pedido mas so community na maquina: nao liga meia instalacao"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'sv' @((Projeto -Versao $false))))
  Assert-True ($r.Texto -match 'serie=desconhecida' -and $r.Texto -match 'nao preenchida no Brodoo' -and $r.Texto -match 'source=nenhum') "versao por preencher no Brodoo: nao adivinha"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'dv' @((Projeto -Key 'p1' -Versao '18.0'), (Projeto -Key 'p2' -Versao '19.0'))))
  Assert-True ($r.Texto -match 'versoes diferentes' -and $r.Texto -match 'source=nenhum') "dois projetos com versoes diferentes: nao escolhe"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-Series', '18.0', '-Edition', 'community', '-BrodooLookupPath', (New-Lookup 'ov' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=18\.0 origem=indicada' -and $r.Texto -match 'edicao=community') "-Series e -Edition mandam sobre o Brodoo"

  $ctx = New-Repo 'com_contexto'
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`nVers$([char]0x00E3)o do Odoo: 17.0`n", (New-Object System.Text.UTF8Encoding($false)))
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=17\.0 origem=PG_CONTEXT') "versao ja escrita no PG_CONTEXT.md manda sobre o Brodoo"

  # As outras duas escritas que existem na frota. A fixture acima usa a do template, e por
  # isso o teste confirmava o que o codigo ja fazia: o espelho do Brodoo escreve em lista e
  # sem o "do", e essa nao era lida em 19 dos 32 PG_CONTEXT.md.
  #
  # Mas o bloco do espelho e uma copia do Brodoo que envelhece (givachoice: 17.0 com o
  # Brodoo ja em 19.0). Com o Brodoo a dar versao unica, vale o Brodoo, e avisa-se.
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`n- Versao Odoo: 17.0`n", $utf8)
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_espelho' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=19\.0 origem=Brodoo') "bloco do espelho velho (17.0) nao manda sobre o Brodoo (19.0)"
  Assert-True ($r.Texto -match 'aviso=.*17\.0.*19\.0') "e a discordancia e avisada, nao engolida"
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_esp_sv' @((Projeto -Versao $false))))
  Assert-True ($r.Texto -match 'serie=17\.0 origem=PG_CONTEXT\.md, bloco do espelho') "Brodoo sem versao: o bloco do espelho serve de recurso"
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_esp_dv' @((Projeto -Key 'p1' -Versao '17.0'), (Projeto -Key 'p2' -Versao '19.0'))))
  Assert-True ($r.Texto -match 'serie=17\.0 origem=PG_CONTEXT\.md, bloco do espelho') "Brodoo com dois projetos em desacordo (o caso do givachoice): o bloco do espelho desempata"
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`n- Versao Odoo: 17.0`n- Versao Odoo: 19.0`n", $utf8)
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_esp_2' @((Projeto -Versao $false))))
  Assert-True ($r.Texto -match 'serie=desconhecida' -and $r.Texto -match 'versoes diferentes') "bloco do espelho com duas versoes, e Brodoo sem versao: nao escolhe"
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`nVers$([char]0x00E3)o do Odoo: 17.0`nVers$([char]0x00E3)o do Odoo: 18.0`n", $utf8)
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_dec_2' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=desconhecida' -and $r.Texto -match 'declara versoes diferentes') "PG_CONTEXT.md a declarar duas versoes: nao escolhe, nem cai no Brodoo"
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`nVers$([char]0x00E3)o do Odoo: 19.0`n- Versao Odoo: 17.0`n", $utf8)
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_dec_esp' @((Projeto -Versao '18.0'))))
  Assert-True ($r.Texto -match 'serie=19\.0 origem=PG_CONTEXT\.md(\s|$)') "a versao declarada manda sobre o bloco do espelho e sobre o Brodoo"
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`nOdoo Version: 17.0`n", (New-Object System.Text.UTF8Encoding($false)))
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx_en' @((Projeto))))
  Assert-True ($r.Texto -match 'serie=17\.0 origem=PG_CONTEXT') "a escrita em ingles ('Odoo Version:') tambem conta"
  [System.IO.File]::WriteAllText((Join-Path $ctx 'PG_CONTEXT.md'), "# x`nVers$([char]0x00E3)o do Odoo: [PONTO POR VALIDAR]`n", (New-Object System.Text.UTF8Encoding($false)))
  $r = Invoke-Auto @('-RepoPath', $ctx, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'ctx2' @((Projeto))))
  Assert-True ($r.Texto -match 'origem=Brodoo') "o marcador do template ('PONTO POR VALIDAR') nao conta como versao"

  $sub = Join-Path $a 'addons\x'
  New-Item -ItemType Directory -Path $sub -Force | Out-Null
  $r = Invoke-Auto @('-RepoPath', $sub, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'sub' @((Projeto))))
  Assert-True ($r.Texto -match [regex]::Escape("($a)")) "sessao aberta numa subpasta: usa a raiz do repositorio"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'bt' @((Projeto -Branch 'Test'))))
  Assert-True ($r.Texto -match 'branch=Test') "branch declarada no Brodoo e respeitada"
  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'bm' @((Projeto -Branch 'main'))))
  Assert-True ($r.Texto -match 'branch=brodoo') "branch declarada 'main' (producao) nao e obedecida"

  $vazioRepo = New-Repo 'sem_commits' -SemCommits
  $r = Invoke-Auto @('-RepoPath', $vazioRepo, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'sc' @((Projeto))))
  Assert-True ($r.Texto -match 'sem commits') "repositorio acabado de criar, sem commits: detetado"

  $semOdoo = New-Repo 'sem_odoo'
  New-Item -ItemType Directory -Path (Join-Path $semOdoo '.pg') -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $semOdoo '.pg\PROJECT_PROFILE.json'), '{"schema_version":"1.0","odoo_applicable":false}')
  $r = Invoke-Auto @('-RepoPath', $semOdoo, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'so' @((Projeto))))
  Assert-True ($r.Texto -match 'source=nenhum' -and $r.Texto -match 'odoo_applicable') "projeto sem Odoo: bootstrap sem source"

  $r = Invoke-Auto @('-RepoPath', $a, '-Hook', '-WhatIf', '-BrodooLookupPath', (New-Lookup 'n2' @((Projeto))))
  Assert-True (-not (Test-Path (Join-Path $a 'AGENTS.md')) -and -not (Test-Path (Join-Path $a '.pg_framework'))) "-WhatIf nao escreve nada"

  if ($SemBootstrapReal) {
    Write-Host "-- bootstrap real: saltado (-SemBootstrapReal)"
  }
  else {
    $env:PG_ODOO_SOURCE_ROOT = $fonteAnterior
    $global19 = if ($fonteAnterior) { Join-Path $fonteAnterior '19.0' } else { Join-Path $HOME '.pg\odoo_src\19.0' }
    if (-not (Test-Path (Join-Path $global19 'community\.git'))) {
      Write-Host "-- bootstrap real: saltado (sem source 19.0 nesta maquina)"
    }
    else {
      Write-Host "-- bootstrap real (repositorio temporario, source 19.0 desta maquina, sem fetch)"
      # origin num repositorio bare local: o checkout do ritual faz fetch e push de verdade,
      # e um URL do GitHub que nao existe fa-lo-ia falhar antes de chegar ao bootstrap.
      $real = New-Repo 'real'
      $bare = Join-Path $script:Raiz 'real_origin.git'
      Invoke-Git @('init', '--bare', '-b', 'main', $bare)
      Invoke-Git @('-C', $real, 'remote', 'set-url', 'origin', $bare)
      Invoke-Git @('-C', $real, 'push', '-u', 'origin', 'main')
      $r = Invoke-Auto @('-RepoPath', $real, '-Hook', '-BrodooLookupPath', (New-Lookup 'real' @((Projeto -Edicao 'community'))))
      Assert-True ($r.Exit -eq 0 -and $r.Texto -match 'bootstrapado automaticamente') "bootstrap real conclui e diz o que fez`n$($r.Texto)"
      Assert-True (Test-Path (Join-Path $real '.pg_framework\scripts\pg_preflight_context.ps1')) ".pg_framework ligado"
      Assert-True ((Test-Path (Join-Path $real 'AGENTS.md')) -and (Test-Path (Join-Path $real '.claude\settings.json'))) "AGENTS.md e hooks do projeto copiados"
      Assert-True (Test-Path (Join-Path $real 'vendor\odoo_src\community\odoo\release.py')) "vendor\odoo_src ligado ao source global"
      $ctxReal = [System.IO.File]::ReadAllText((Join-Path $real 'PG_CONTEXT.md'), [System.Text.Encoding]::UTF8)
      Assert-True ($ctxReal -match "Vers$([char]0x00E3)o do Odoo:\s*19\.0") "PG_CONTEXT.md fica com a versao 19.0"
      $branch = (& git -C $real rev-parse --abbrev-ref HEAD).Trim()
      Assert-True ($branch -eq 'brodoo') "ficheiros de framework escritos na branch brodoo (atual: $branch)"
      $semCommitNovo = (& git -C $real log --oneline main | Measure-Object).Count -eq 1
      Assert-True $semCommitNovo "main (producao do cliente) nao ganhou commits"
      $r = Invoke-Auto @('-RepoPath', $real, '-Hook', '-BrodooLookupPath', (New-Lookup 'real2' @((Projeto))))
      Assert-True ($r.Texto -eq '') "segunda sessao no mesmo repositorio: silencio"

      Write-Host "-- bootstrap real de um clone vazio, seguido do passo 1 do ritual"
      # O cenario de quem cria o repositorio no GitHub, faz `git clone` e abre o VS Code:
      # nem um commit. Ate 2026-09-28 o bootstrap passava e o ritual rebentava a seguir.
      $origemVazia = Join-Path $script:Raiz 'vazio_origin.git'
      Invoke-Git @('init', '--bare', '-b', 'main', $origemVazia)
      $clone = Join-Path $script:Raiz 'clone_vazio'
      Invoke-Git @('clone', $origemVazia, $clone)
      $r = Invoke-Auto @('-RepoPath', $clone, '-Hook', '-BrodooLookupPath', (New-Lookup 'vz' @((Projeto -Edicao 'community'))))
      Assert-True ($r.Texto -match 'bootstrapado automaticamente') "clone vazio: bootstrap conclui"
      Assert-True ($r.Texto -match 'pg_preflight_context\.ps1') "a saida da ao agente os comandos do ritual"
      $passo1 = Join-Path $clone '.pg_framework\scripts\pg_checkout_brodoo_branch.ps1'
      $anterior = $ErrorActionPreference
      $ErrorActionPreference = 'Continue'
      try { & powershell -NoProfile -ExecutionPolicy Bypass -File $passo1 -RepoPath $clone 2>&1 | Out-Null; $codigo = $LASTEXITCODE }
      finally { $ErrorActionPreference = $anterior }
      Assert-True ($codigo -eq 0) "clone vazio: o passo 1 do ritual passa depois do bootstrap"
      $branchVazio = (& git -C $clone symbolic-ref --short HEAD).Trim()
      Assert-True ($branchVazio -eq 'brodoo') "clone vazio: HEAD na branch brodoo (atual: $branchVazio)"
    }
  }

  Write-Host ""
  Write-Host "OK: $($script:Total) verificacoes."
}
finally {
  $env:PG_ODOO_SOURCE_ROOT = $fonteAnterior
  $env:PG_AUTO_BOOTSTRAP_LOG_DIR = $logsAnterior
  if ($null -ne $desligadoAnterior) { $env:PG_AUTO_BOOTSTRAP = $desligadoAnterior }
  # O bootstrap real cria junctions para o _pg_template e para o source Odoo global. No
  # PS 5.1 um Remove-Item -Recurse (ou um Get-ChildItem -Recurse) atravessa-as, e apagar
  # a pasta temporaria apagaria o ALVO. Por isso: percorrer sem nunca descer a um reparse
  # point, desfazer cada um com rmdir (que remove a ligacao, nao o conteudo), e so depois
  # apagar o resto -- e so se ja nao restar nenhuma ligacao.
  function Remove-LinksBelow {
    param([string]$Path)
    foreach ($item in @(Get-ChildItem -LiteralPath $Path -Force -Directory -ErrorAction SilentlyContinue)) {
      if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        cmd /c rmdir "$($item.FullName)" 2>$null | Out-Null
      }
      else { Remove-LinksBelow -Path $item.FullName }
    }
  }
  function Test-LinksBelow {
    param([string]$Path)
    foreach ($item in @(Get-ChildItem -LiteralPath $Path -Force -Directory -ErrorAction SilentlyContinue)) {
      if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return $true }
      if (Test-LinksBelow -Path $item.FullName) { return $true }
    }
    return $false
  }
  if (Test-Path $script:Raiz) {
    Remove-LinksBelow -Path $script:Raiz
    if (Test-LinksBelow -Path $script:Raiz) {
      Write-Host "AVISO: restam ligacoes em $script:Raiz; pasta temporaria NAO apagada, por seguranca."
    }
    else { Remove-Item -LiteralPath $script:Raiz -Recurse -Force -ErrorAction SilentlyContinue }
  }
}
