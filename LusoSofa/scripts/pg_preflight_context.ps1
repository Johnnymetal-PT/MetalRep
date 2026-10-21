<#
.SYNOPSIS
  Gate de arranque (AUD-01): garante que as fontes de verdade estao presentes e
  coerentes ANTES de o agente iniciar analise consultiva.

.DESCRIPTION
  Verifica, para o repositorio de projeto indicado:
    - versao Odoo confirmada no PG_CONTEXT.md (nao [PONTO POR VALIDAR]);
    - vendor/odoo_src presente e coerente com a serie (community + enterprise se aplicavel);
    - saude do espelho (.pg/MIRROR_HEALTH.json) - informativo, quando existir.
  Deriva o URL da documentacao oficial da serie e escreve tudo em .pg/PREFLIGHT.json,
  legivel pelo agente. Falha (exit 1) em pre-condicoes bloqueantes.

.NOTES
  Script de framework, corre no repositorio de PROJETO (nao no _pg_template).
#>
param(
  [string]$RepoPath = (Get-Location).Path,
  [string]$Series,
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

function Get-ContextValue {
  param([string]$Content, [string]$Label)
  $escaped = [regex]::Escape($Label)
  $match = [regex]::Match($Content, "(?im)^\s*$escaped\s*:\s*(.+?)\s*$")
  if ($match.Success) { return $match.Groups[1].Value.Trim() }
  return $null
}

function Test-Unresolved {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return $true }
  return ($Value -match '^\[.*\]$')
}

function Resolve-Series {
  param([string]$VersionRaw)
  if ([string]::IsNullOrWhiteSpace($VersionRaw)) { return $null }
  $match = [regex]::Match($VersionRaw, '(\d+)(?:\.(\d+))?')
  if (-not $match.Success) { return $null }
  $major = $match.Groups[1].Value
  $minor = if ($match.Groups[2].Success) { $match.Groups[2].Value } else { "0" }
  return "$major.$minor"
}

function Get-ProjectGovernance {
  # Le a governance do espelho (project.json) - fonte de verdade da versao/edicao
  # quando o PG_CONTEXT.md e o formato derivado do espelho (sem rotulo "Versao do Odoo:").
  #
  # A versao anterior percorria TODOS os project.json e ficava com o ULTIMO que tivesse
  # versao preenchida: num repositorio multi-projeto a ordem de travessia decidia a versao.
  # `FACTO OBSERVADO` (givachoice): dois projetos espelhados, um em 17.0 e outro em 19.0;
  # o preflight ficou com o de 17.0 e derivou dai a documentacao oficial de 17.0 num
  # projeto que corria 19.0. Onze dias assim.
  # Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achado D3.
  #
  # Passa a preferir o NAMESPACED (`.pg/projects/**`) sobre o legacy da raiz -- que e o que
  # o AGENTS_SHARED manda em multi-projeto -- e a sinalizar divergencia em vez de a esconder.
  param([string]$Repo)

  $namespaced = @()
  $legacy = @()

  Get-ChildItem -Path (Join-Path $Repo ".pg") -Recurse -Filter "project.json" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
      $pj = Get-Content -Path $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
      $gov = if ($pj.project -and $pj.project.governance) { $pj.project.governance } elseif ($pj.governance) { $pj.governance } else { $null }
      if ($gov -and $gov.odoo_version -and -not [string]::IsNullOrWhiteSpace([string]$gov.odoo_version)) {
        if ($_.FullName -match '\\\.pg\\projects\\') { $namespaced += $gov } else { $legacy += $gov }
      }
    }
    catch { }
  }

  $candidatos = if ($namespaced.Count -gt 0) { $namespaced } else { $legacy }
  if ($candidatos.Count -eq 0) { return $null }

  $versoes = @($candidatos | ForEach-Object { [string]$_.odoo_version } | Sort-Object -Unique)
  if ($versoes.Count -gt 1) {
    $script:GovernanceVersoesEmDesacordo = $versoes
  }

  return $candidatos[0]
}

function Get-SourceSeries {
  # A serie REAL do source, lida do release.py do core.
  #
  # O preflight validava a PRESENCA do source e nunca a sua coerencia com a versao
  # declarada -- e foi essa lacuna que deixou passar onze dias de documentacao de 17.0
  # num projeto em 19.0. O source sabia; ninguem lhe perguntou.
  param([string]$CommunityPath)

  if ([string]::IsNullOrWhiteSpace($CommunityPath)) { return $null }
  $release = Join-Path $CommunityPath "odoo\release.py"
  if (-not (Test-Path $release)) { return $null }

  try { $texto = Get-Content -Path $release -Raw -Encoding UTF8 } catch { return $null }
  if ($texto -match 'version_info\s*=\s*\(\s*[''"]?(\d+)[''"]?\s*,\s*(\d+)') {
    return ("{0}.{1}" -f $Matches[1], $Matches[2])
  }
  return $null
}

function Get-CorePathInfo {
  # Extrai serie/edicao do 'Path do core: ...\<serie>\<edicao>' (cache global do source)
  param([string]$Content, [string]$Label)
  $val = Get-ContextValue -Content $Content -Label $Label
  if ([string]::IsNullOrWhiteSpace($val)) { return $null }
  $m = [regex]::Match($val, '(?i)[\\/](\d+\.\d+)[\\/](community|enterprise)')
  $series = if ($m.Success) { $m.Groups[1].Value } else { $null }
  return [ordered]@{ path = $val; series = $series }
}

$repo = [System.IO.Path]::GetFullPath($RepoPath)
$errors = @()
$warnings = @()

# ---------------------------------------------------------------------------
# Pasta de trabalho declarada: nao e repositorio, e tem factos proprios.
#
# Boa parte do trabalho de Odoo acontece fora de repositorios -- pastas de servidor,
# arvores de addons, copias de migracao. Ate 2026-09-11 o ritual nao tinha resposta para
# isso: o agente procurava o AGENTS.md, nao encontrava, respondia "nao existe, continuo",
# e seguia sem os factos do projeto. `FACTO OBSERVADO` (givachoice): 7 procuras em 46
# conversas, nenhuma com resultado, e seis incidentes de confusao de versao depois --
# incluindo um deploy de codigo v17 sobre o servidor de testes v19.
#
# Com o bloco declarado por pg_init_work_folder.ps1, o passo deixa de ser inerte: diz o
# que a pasta e, e recita os factos que tem precedencia sobre qualquer suposicao.
#
# Como no PROJECT_PROFILE.json, e por DECLARACAO EXPLICITA: sem o marcador, nada muda.
# E nao se escreve .pg/PREFLIGHT.json -- a pasta nao e repositorio e nao leva estrutura
# da framework so por ter sido inspeccionada.
# ---------------------------------------------------------------------------
$agentsDaPasta = Join-Path $repo 'AGENTS.md'
if ((Test-Path $agentsDaPasta) -and
    -not (Test-Path (Join-Path $repo '.pg')) -and
    -not (Test-Path (Join-Path $repo 'PG_CONTEXT.md'))) {

  $textoAgents = Get-Content -Path $agentsDaPasta -Raw -Encoding UTF8
  if ($textoAgents -match 'PG_WORK_FOLDER:START') {

    function Get-FactoDeclarado {
      param([string]$Texto, [string]$Rotulo)
      $m = [regex]::Match($Texto, "(?m)^" + [regex]::Escape($Rotulo) + "\s*:\s*(.+?)\s*$")
      if ($m.Success) { return $m.Groups[1].Value }
      return $null
    }

    $wfVersao = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Versao do Odoo'
    $wfEdicao = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Edicao'
    $wfServidor = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Servidor'
    $wfBase = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Base de dados'
    $wfCore = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Path do core'
    $wfRepo = Get-FactoDeclarado -Texto $textoAgents -Rotulo 'Repositorio do projeto'

    $wfSerie = if ($wfVersao) { Resolve-Series -VersionRaw $wfVersao } else { $null }
    $wfDocs = if ($wfSerie) { "https://www.odoo.com/documentation/$wfSerie/" } else { $null }

    Write-Host "=== PG PREFLIGHT (pasta de trabalho) ==="
    Write-Host "  Pasta       : $repo"
    Write-Host "  Natureza    : pasta de trabalho declarada -- NAO e repositorio da framework"
    if ($wfVersao) { Write-Host "  Versao Odoo : $wfVersao$(if ($wfSerie) { " (serie $wfSerie)" })" }
    if ($wfEdicao) { Write-Host "  Edicao      : $wfEdicao" }
    if ($wfServidor) { Write-Host "  Servidor    : $wfServidor" }
    if ($wfBase) { Write-Host "  Base dados  : $wfBase" }
    if ($wfCore) { Write-Host "  Path do core: $wfCore" }
    if ($wfDocs) { Write-Host "  Docs oficial: $wfDocs" }
    if ($wfRepo) { Write-Host "  Projeto em  : $wfRepo" }

    if (-not $wfVersao) {
      Write-Host "  AVISO: a pasta nao declara a versao do Odoo -- e o facto que mais custa quando falta. Correr pg_init_work_folder.ps1 com -OdooVersion ou -OdooSourcePath."
    }

    # Coerencia com o source declarado: e a mesma verificacao que se faz nos
    # repositorios, e e a que teria evitado o deploy de v17 sobre o servidor v19.
    if ($wfCore -and $wfSerie) {
      $serieDoSource = Get-SourceSeries -CommunityPath $wfCore
      if ($serieDoSource -and ($serieDoSource -ne $wfSerie)) {
        Write-Host "  ERRO: a pasta declara a serie $wfSerie mas o source em '$wfCore' e $serieDoSource."
        throw "Preflight falhou: os factos declarados contradizem o source. Corrigir o AGENTS.md da pasta, ou apontar o source a serie certa."
      }
    }

    Write-Host ""
    Write-Host "  Os factos acima tem precedencia sobre qualquer suposicao, incluindo a de um"
    Write-Host "  resumo automatico de sessao retomada."
    exit 0
  }
}

# ---------------------------------------------------------------------------
# Perfil do projeto: ha projetos na frota que NAO sao de Odoo (ex.: PRIacademia,
# de Primavera, gerido no mesmo Odoo da PG). Nesses, "versao Odoo confirmada" e
# "vendor/odoo_src presente" sao pre-condicoes impossiveis, e o preflight ficava
# em 'fail' para sempre -- o que, pela regra bloqueante do AGENTS_SHARED, impedia
# qualquer trabalho num repo que estava perfeitamente saudavel.
#
# A tolerancia e por DECLARACAO EXPLICITA em .pg/PROJECT_PROFILE.json, nunca por
# inferencia (uma etiqueta no Odoo a desligar um gate de qualidade seria pior do
# que o gate errado). O default e Odoo: sem ficheiro, nada muda.
# ---------------------------------------------------------------------------
$projectProfilePath = Join-Path $repo ".pg\PROJECT_PROFILE.json"
$odooApplicable = $true
$projectErp = "odoo"
if (Test-Path $projectProfilePath) {
  try {
    $profileData = Read-Utf8JsonFile -Path $projectProfilePath
    if ($null -ne $profileData.erp -and -not [string]::IsNullOrWhiteSpace([string]$profileData.erp)) {
      $projectErp = ([string]$profileData.erp).ToLowerInvariant()
    }
    if ($profileData.PSObject.Properties.Name -contains 'odoo_applicable') {
      $odooApplicable = [bool]$profileData.odoo_applicable
    }
    elseif ($projectErp -ne 'odoo') {
      $odooApplicable = $false
    }
  }
  catch {
    $warnings += "PROJECT_PROFILE.json ilegivel ($($_.Exception.Message)); a assumir projeto Odoo."
  }
}

$contextPath = Join-Path $repo "PG_CONTEXT.md"
$version = $null
$edition = $null
$isEnterprise = $false
$coreInfo = $null

if (-not (Test-Path $contextPath)) {
  $errors += "PG_CONTEXT.md nao encontrado em $repo - repositorio nao bootstrapado."
}
else {
  $content = Read-Utf8TextFile -Path $contextPath

  # 1) formato template: rotulo "Versao do Odoo:" (com/sem acento) + "Edicao:"
  $version = Get-ContextValue -Content $content -Label "Versao do Odoo"
  if (Test-Unresolved -Value $version) {
    $version = Get-ContextValue -Content $content -Label ([char]0x0056 + "ers" + [char]0x00E3 + "o do Odoo")
  }
  $edition = Get-ContextValue -Content $content -Label ("Edi" + [char]0x00E7 + [char]0x00E3 + "o")

  # 2) formato espelho: governance do project.json (fonte de verdade quando o PG_CONTEXT vem do espelho)
  $gov = Get-ProjectGovernance -Repo $repo
  $versaoVeioDaGovernance = $false
  if ((Test-Unresolved -Value $version) -and $gov -and -not [string]::IsNullOrWhiteSpace([string]$gov.odoo_version)) {
    $version = [string]$gov.odoo_version
    $versaoVeioDaGovernance = $true
  }
  if ((Test-Unresolved -Value $edition) -and $gov -and $gov.odoo_edition -and (@('', 'unknown') -notcontains ([string]$gov.odoo_edition).ToLower())) {
    $edition = [string]$gov.odoo_edition
  }

  # 3) fallback: linha 'Path do core: ...\<serie>\community' (cache global do source)
  $coreInfo = Get-CorePathInfo -Content $content -Label "Path do core"
  if ((Test-Unresolved -Value $version) -and $coreInfo -and $coreInfo.series) {
    $version = $coreInfo.series
  }

  if (Test-Unresolved -Value $version) {
    if ($odooApplicable) {
      $errors += "Versao do Odoo nao confirmada (nem rotulo no PG_CONTEXT.md, nem governance do espelho, nem Path do core). Confirmar a versao no onboarding/Odoo."
    }
    $version = $null
  }
  if (Test-Unresolved -Value $edition) {
    if ($odooApplicable) {
      $warnings += "Edicao Odoo nao confirmada; a assumir Community para verificacao de source."
    }
    $edition = $null
  }
  elseif ($edition -match '(?i)enterprise') {
    $isEnterprise = $true
  }
}

# Serie: argumento tem prioridade; senao deriva da versao.
$resolvedSeries = if (-not [string]::IsNullOrWhiteSpace($Series)) { $Series } else { Resolve-Series -VersionRaw $version }
if ([string]::IsNullOrWhiteSpace($resolvedSeries) -and $version) {
  $errors += "Nao foi possivel derivar a serie Odoo de '$version'."
}

# Source Odoo: vendor/odoo_src (junction) OU cache global referenciado no 'Path do core'
$communityPath = Join-Path $repo "vendor\odoo_src\community"
$enterprisePath = Join-Path $repo "vendor\odoo_src\enterprise"
$corePathPresent = ($coreInfo -and $coreInfo.path -and (Test-Path $coreInfo.path))
$communityPresent = (Test-Path $communityPath) -or $corePathPresent
$enterprisePresent = (Test-Path $enterprisePath)

if (-not $communityPresent -and $odooApplicable) {
  $errors += "Source Odoo ausente: nem vendor/odoo_src/community nem o 'Path do core' do PG_CONTEXT existem. Correr pg_clone_odoo_source.ps1 -Series $resolvedSeries."
}
if ($isEnterprise -and -not $enterprisePresent) {
  $errors += "Edicao Enterprise mas vendor/odoo_src/enterprise ausente. Correr pg_clone_odoo_source.ps1 com edicao enterprise."
}
$sourceOk = $communityPresent -and (-not $isEnterprise -or $enterprisePresent)

# Coerencia entre o que o projeto DECLARA e o que o source E. Sem isto o preflight dava
# `pass` a citar a documentacao da versao errada -- ver Get-SourceSeries.
$sourceCommunityPath = if (Test-Path $communityPath) { $communityPath } elseif ($corePathPresent) { $coreInfo.path } else { $null }
$sourceSeries = Get-SourceSeries -CommunityPath $sourceCommunityPath
if ($odooApplicable -and $resolvedSeries -and $sourceSeries -and ($resolvedSeries -ne $sourceSeries)) {
  $errors += "Incoerencia de versao: o projeto declara a serie $resolvedSeries mas o source em '$sourceCommunityPath' e $sourceSeries. Um dos dois esta errado, e citar a documentacao da serie errada engana precisamente onde o comportamento mudou entre versoes. Corrigir o rotulo 'Versao do Odoo:' no PG_CONTEXT.md, ou apontar o source a serie certa."
}

# Governance contra source: sao as duas autoridades INDEPENDENTES.
#
# O rotulo do PG_CONTEXT passou a ser derivado do source (pg_sync_pg_context), pelo que
# deixou de ser testemunha independente: comparar so declarado-vs-source passaria a
# concordar sempre. O que continua a valer a pena confrontar e o que o Odoo diz
# (governance do espelho) contra o que o source e. Foi a divergencia entre estes dois que
# esteve por tras dos onze dias do givachoice.
if ($odooApplicable -and $gov -and $sourceSeries -and -not [string]::IsNullOrWhiteSpace([string]$gov.odoo_version)) {
  $serieGovernance = Resolve-Series -VersionRaw ([string]$gov.odoo_version)
  if ($serieGovernance -and ($serieGovernance -ne $sourceSeries)) {
    $errors += "Incoerencia entre o Odoo e o source: o espelho declara a serie $serieGovernance (governance do project.json) e o source em '$sourceCommunityPath' e $sourceSeries. Sao as duas autoridades independentes e discordam -- corrigir o pg_odoo_version no Odoo, ou apontar o source a serie certa, antes de confiar em qualquer das duas."
  }
}

if ($script:GovernanceVersoesEmDesacordo) {
  # Sem rotulo no PG_CONTEXT, a versao foi buscada a governance -- e se os projetos
  # espelhados declaram versoes diferentes, a que se usou foi a do primeiro que a
  # travessia do disco encontrou. Isso nao e uma versao confirmada: e um palpite com
  # aparencia de facto, e o passo 3 do ritual existe precisamente para o impedir.
  #
  # `FACTO OBSERVADO` (givachoice, 31/07 a 11/08): dois projetos espelhados, 17.0 e 19.0,
  # sem rotulo; o preflight deu `pass` a citar documentacao de 17.0 num projeto em 19.0.
  # `FACTO OBSERVADO` (2026-09-11): 16 dos 32 repositorios da frota nao tem o rotulo.
  $detalhe = "Espelho multi-projeto com versoes Odoo em desacordo ($($script:GovernanceVersoesEmDesacordo -join ', ')). Declarar a versao no rotulo 'Versao do Odoo:' do PG_CONTEXT.md, ou alinhar o pg_odoo_version dos projetos no Odoo."
  if ($versaoVeioDaGovernance) {
    $errors += "Versao do Odoo nao confirmada: $detalhe A versao usada seria a do primeiro project.json que a travessia encontrasse, que e arbitraria."
  }
  else {
    $warnings += $detalhe
  }
}

if (-not $odooApplicable) {
  $warnings += "Projeto declarado como NAO-Odoo (erp=$projectErp) em .pg/PROJECT_PROFILE.json: as pre-condicoes de versao Odoo e de vendor/odoo_src ficam dispensadas. A ordem de decisao 'standard -> modulo adicional -> Studio -> custom' e a consulta a documentacao oficial do Odoo NAO se aplicam a este repo."
}

# Documentacao oficial derivada da serie
$docsBaseUrl = if ($resolvedSeries) { "https://www.odoo.com/documentation/$resolvedSeries/" } else { $null }

# Saude do espelho (AUD-04) - informativo enquanto nao existir
$mirrorHealthPath = Join-Path $repo ".pg\MIRROR_HEALTH.json"
$mirrorHealthPresent = Test-Path $mirrorHealthPath

# ------------------------------------------------------------------
# Dependencias da framework (avisos nao-bloqueantes; sinalizam wiring incompleto)
# ------------------------------------------------------------------
$frameworkLink = Join-Path $repo ".pg_framework"
$frameworkLinkOk = Test-Path $frameworkLink
$docTemplatesOk = (Test-Path (Join-Path $frameworkLink "doc_templates")) -or (Test-Path (Join-Path $repo "doc_templates"))
$claudeHookOk = Test-Path (Join-Path $repo ".claude\settings.json")
$codexHookOk = Test-Path (Join-Path $repo ".codex\hooks.json")
$tokenLogOk = Test-Path (Join-Path $repo ".pg\tokens\consumption.jsonl")

function Get-MirrorArtifactPath {
  param([string]$Repo, [string]$FileName)
  $legacy = Join-Path $Repo ".pg\project\$FileName"
  if (Test-Path $legacy) { return $legacy }
  $projectsDir = Join-Path $Repo ".pg\projects"
  if (Test-Path $projectsDir) {
    $hit = Get-ChildItem -Path $projectsDir -Recurse -Filter $FileName -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.FullName }
  }
  return $null
}
function Test-MirrorArtifact {
  param([string]$Repo, [string]$FileName)
  return [bool](Get-MirrorArtifactPath -Repo $Repo -FileName $FileName)
}

# Estado do inventario do Odoo do cliente (M1). Presenca nao chega: ate 2026-08-10
# o espelho publicava o inventario da base da Parametro Global etiquetado com os
# dados do cliente, e passava neste preflight como valido. Ver PG-007.
function Get-OdooEnvCollectionState {
  param([string]$Path)
  if (-not $Path) { return "absent" }
  try { $env = (Read-Utf8TextFile -Path $Path | ConvertFrom-Json) }
  catch { return "unreadable" }
  # Espelho anterior ao schema 1.1: sem bloco `collection`, a origem do inventario
  # e desconhecida e nao pode ser tratada como inventario do cliente.
  if (-not $env.odoo_env.PSObject.Properties.Name.Contains('collection')) { return "unknown_origin" }
  $status = [string]$env.odoo_env.collection.status
  if ([string]::IsNullOrWhiteSpace($status)) { return "unknown_origin" }
  return $status
}

$odooEnvPath = Get-MirrorArtifactPath -Repo $repo -FileName "odoo_env.json"
$odooEnvPresent = [bool]$odooEnvPath
$odooEnvState = Get-OdooEnvCollectionState -Path $odooEnvPath
$deliverablesPresent = Test-MirrorArtifact -Repo $repo -FileName "deliverables.json"

# Frescura da framework: o projeto esta sincronizado com a versao ATUAL do framework?
$frameworkGitHead = $null
$projectSyncedHead = $null
$frameworkSynced = $null
$frameworkBehindUpstream = $null
if ($frameworkLinkOk) {
  try {
    $h = (& git -C $frameworkLink rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0) { $frameworkGitHead = (($h -join '').Trim()) }
  }
  catch { $frameworkGitHead = $null }
  try {
    $b = (& git -C $frameworkLink rev-list --count "HEAD..@{u}" 2>$null)
    if ($LASTEXITCODE -eq 0) { $frameworkBehindUpstream = [int]((($b -join '').Trim())) }
  }
  catch { $frameworkBehindUpstream = $null }
  $syncStatePath = Join-Path $repo ".pg\PG_TEMPLATE_SYNC_STATE.json"
  if (Test-Path $syncStatePath) {
    try { $projectSyncedHead = ([string]((Read-Utf8TextFile -Path $syncStatePath | ConvertFrom-Json).template_git_head)).Trim() }
    catch { $projectSyncedHead = $null }
  }
  if ($frameworkGitHead -and $projectSyncedHead) { $frameworkSynced = ($frameworkGitHead -eq $projectSyncedHead) }
}

# .pg_framework e BLOQUEANTE: sem ele o agente opera sem o contrato/metodo/scripts partilhados
if (-not $frameworkLinkOk) { $errors += ".pg_framework ausente/nao ligado - sem contrato partilhado, metodo nem scripts. Correr pg_link_framework.ps1 (bootstrap)." }
if (-not $docTemplatesOk) { $warnings += "Metodologia (doc_templates) indisponivel; sincronizar assets partilhados / pg_pull_doc_templates.ps1." }
if (-not $claudeHookOk) { $warnings += "Hook de tokens do Claude ausente (.claude/settings.json); registo automatico inativo (correr pg_propagate_agent_hooks.ps1)." }
if (-not $codexHookOk) { $warnings += "Hook de tokens do Codex ausente (.codex/hooks.json); registo automatico inativo (correr pg_propagate_agent_hooks.ps1)." }
if (-not $tokenLogOk) { $warnings += ".pg/tokens/consumption.jsonl ausente." }
# Num projeto nao-Odoo o inventario de modulos do cliente nunca sera recolhido (nao
# existe Odoo do cliente): avisar sobre isso a cada arranque seria ruido permanente
# e treinava o leitor a ignorar os avisos do preflight.
if (-not $odooApplicable) { }
elseif (-not $odooEnvPresent) { $warnings += "Espelho: odoo_env.json (M1) ainda nao publicado; correr Sincronizar Agora no projeto ou, entretanto, determinar os modulos instalados a partir do codigo do projeto / vendor/odoo_src." }
else {
  switch ($odooEnvState) {
    "collected" { }
    "stale" { $warnings += "Espelho: inventario do Odoo do cliente (M1) obsoleto; re-executar a recolha (canal production) antes de decidir standard-ja-instalado vs standard-adicional." }
    "unavailable" { $warnings += "Espelho: inventario do Odoo do cliente (M1) por recolher (collection.status=unavailable); os modulos instalados NAO sao conhecidos - tratar como PONTO POR VALIDAR e usar o canal production (pg_odoo_client_query.ps1), nunca assumir que nada esta instalado." }
    "unknown_origin" { $warnings += "Espelho: odoo_env.json sem bloco 'collection' (schema anterior a 1.1) - a origem do inventario e DESCONHECIDA e pode ser a base da Parametro Global, nao a do cliente (PG-007). Nao usar para a ordem de decisao; re-sincronizar o projeto." }
    "unreadable" { $warnings += "Espelho: odoo_env.json ilegivel (JSON invalido); re-sincronizar o projeto." }
    default { $warnings += "Espelho: odoo_env.json com collection.status desconhecido ('$odooEnvState'); nao usar para a ordem de decisao sem confirmar a origem." }
  }
}
if (-not $deliverablesPresent) { $warnings += "Espelho: deliverables.json (M3) ainda nao publicado; correr Sincronizar Agora no projeto." }
if ($frameworkLinkOk) {
  if ($frameworkBehindUpstream -and $frameworkBehindUpstream -gt 0) { $warnings += "Framework local desatualizada: $frameworkBehindUpstream commit(s) atras do origin. Correr 'git pull' no _pg_template (passo 2 do ritual)." }
  if ($frameworkSynced -eq $false) { $warnings += "Projeto sincronizado numa versao antiga do framework (projeto=$projectSyncedHead, framework=$frameworkGitHead). Re-executar bootstrap/sync para atualizar." }
  if (-not $projectSyncedHead) { $warnings += "PG_TEMPLATE_SYNC_STATE.json ausente/ilegivel; estado de sincronizacao com o framework desconhecido - correr bootstrap." }
}

$status = if ($errors.Count -eq 0) { "pass" } else { "fail" }
$checkedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$editionLabel = if ($isEnterprise) { "enterprise" } elseif ($edition) { $edition } else { "community(assumed)" }

$preflight = [ordered]@{
  schema_version        = "1.3"
  status                = $status
  checked_at            = $checkedAt
  repo_path             = $repo
  project_erp           = $projectErp
  odoo_applicable       = $odooApplicable
  odoo_version          = $version
  odoo_series           = $resolvedSeries
  odoo_edition          = $editionLabel
  source_ok             = $sourceOk
  source_series         = $sourceSeries
  community_present     = $communityPresent
  enterprise_present    = $enterprisePresent
  docs_base_url         = $docsBaseUrl
  mirror_health_present = $mirrorHealthPresent
  framework_link_ok     = $frameworkLinkOk
  framework_git_head    = $frameworkGitHead
  project_synced_head   = $projectSyncedHead
  framework_synced      = $frameworkSynced
  framework_behind_upstream = $frameworkBehindUpstream
  doc_templates_ok      = $docTemplatesOk
  claude_hook_ok        = $claudeHookOk
  codex_hook_ok         = $codexHookOk
  token_log_ok          = $tokenLogOk
  odoo_env_present      = $odooEnvPresent
  odoo_env_collection   = $odooEnvState
  deliverables_present  = $deliverablesPresent
  errors                = $errors
  warnings              = $warnings
}

$pgDir = Join-Path $repo ".pg"
if (-not (Test-Path $pgDir)) { New-Item -ItemType Directory -Path $pgDir -Force | Out-Null }
$preflightPath = Join-Path $pgDir "PREFLIGHT.json"
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($preflightPath, (($preflight | ConvertTo-Json -Depth 8) + "`n"), $encoding)

if (-not $Quiet) {
  Write-Host "=== PG PREFLIGHT ($status) ==="
  Write-Host "  Perfil      : erp=$projectErp odoo_aplicavel=$odooApplicable"
  Write-Host "  Versao Odoo : $version (serie $resolvedSeries)"
  Write-Host "  Source OK   : $sourceOk (community=$communityPresent, enterprise=$enterprisePresent)"
  if ($sourceSeries) { Write-Host "  Serie source: $sourceSeries" }
  Write-Host "  Docs oficial: $docsBaseUrl"
  Write-Host "  Framework   : link=$frameworkLinkOk doc_templates=$docTemplatesOk hooks(claude=$claudeHookOk,codex=$codexHookOk) tokenlog=$tokenLogOk"
  Write-Host "  Frescura fw : sincronizado=$frameworkSynced atras_do_origin=$frameworkBehindUpstream"
  Write-Host "  Espelho M1/M3: odoo_env=$odooEnvPresent (inventario cliente=$odooEnvState) deliverables=$deliverablesPresent"
  foreach ($w in $warnings) { Write-Host "  WARN: $w" }
  foreach ($e in $errors) { Write-Host "  ERRO: $e" }
  Write-Host "  Escrito em  : $preflightPath"
}

if ($status -ne "pass") {
  throw "Preflight falhou: pre-condicoes em falta. Ver .pg/PREFLIGHT.json."
}
