<#
.SYNOPSIS
  Alinha os ficheiros geridos pela framework em toda a frota de repositorios de projeto,
  fazendo commit e push na branch Brodoo de cada um.

.DESCRIPTION
  O publisher do espelho escreve os dados do projeto (.pg/projects/**, projects/**,
  PG_CONTEXT.md) mas NUNCA os ficheiros da framework. A cada release do _pg_template os
  repositorios da frota ficam desalinhados e o alinhamento tem de ser feito repositorio a
  repositorio. Este script faz esse trabalho de forma repetivel, com as guardas que a
  operacao manual de 2026-08-24 mostrou serem necessarias.

  Sequencia por repositorio:
    1. resolve a branch Brodoo declarada (namespaced primeiro, legacy so como fallback)
    2. `git fetch` IMEDIATAMENTE antes do merge -- o publisher escreve durante a execucao
    3. faz commit do estado local dos ficheiros de framework
    4. faz `git merge origin/<branch>` (merge real: nao descarta nenhum dos dois lados)
    5. corre pg_sync_shared_assets.ps1, que e idempotente
    6. faz commit e push, com retentativas em caso de corrida com o publisher

  Audit-first: sem -Apply nada e escrito. O relatorio sai em JSON com -ReportPath.

.PARAMETER ReposRoot   Raiz dos repositorios (default: pasta-mae do _pg_template).
.PARAMETER RepoNames   Subconjunto de repositorios; por omissao, todos os bootstrapados.
.PARAMETER Apply       Executa. Sem este switch o script so relata o que faria.
.PARAMETER NoPush      Faz commit mas nao publica.
.PARAMETER MaxAttempts Tentativas por repositorio quando o push perde a corrida (default 4).
.PARAMETER ReportPath  Caminho para escrever o relatorio JSON.

.EXAMPLE
  # auditoria, sem escrever nada
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_align_fleet_framework.ps1

.EXAMPLE
  # alinhar e publicar
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_align_fleet_framework.ps1 -Apply
#>
param(
  [string]$ReposRoot,
  [string[]]$RepoNames,
  [switch]$Apply,
  [switch]$NoPush,
  [int]$MaxAttempts = 4,
  [string]$ReportPath
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "pg_file_io_common.ps1")

# ---------------------------------------------------------------------------
# Ambito
# ---------------------------------------------------------------------------

# Ficheiros geridos pela framework. Sao os unicos que este script faz stage.
$script:FrameworkPaths = @(
  'AGENTS.md', 'CLAUDE.md', 'config.toml',
  '.gitignore', '.editorconfig', '.gitattributes',
  '.claude', '.codex', '.agents', '.github',
  'doc_templates',
  '.pg/PG_TEMPLATE_SYNC_STATE.json',
  '.pg/tokens/consumption.jsonl'
)

# O mesmo ambito como regex, para classificar conflitos de merge. Um conflito FORA
# deste ambito aborta o repositorio: nao ha resolucao automatica segura para ficheiros
# do projeto nem para os que o publisher do espelho escreve.
$script:FrameworkPathPattern =
  '^(AGENTS\.md|CLAUDE\.md|config\.toml|\.gitignore|\.editorconfig|\.gitattributes)$' +
  '|^\.pg/(PG_TEMPLATE_SYNC_STATE\.json|PREFLIGHT\.json|tokens/consumption\.jsonl)$' +
  '|^(\.claude|\.codex|\.agents|\.github|doc_templates)/'

# Ficheiros que este script NUNCA toca, porque pertencem ao publisher do espelho.
# Fazer stage destes reverteria dados do espelho publicados entretanto pelo Odoo.
$script:PublisherPathPattern = '^\.pg/projects?/|^projects/|^PG_CONTEXT\.md$'

$script:CommitMessageLocal = @'
chore(framework): estado local do sync antes do merge com a origin

Commit intermedio, para o merge com a origin poder ser resolvido sem
descartar ficheiros locais.
'@

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Invoke-Git {
  # O ErrorActionPreference do script e Stop, mas em Windows PowerShell 5.1 redirecionar
  # o stderr de um executavel nativo embrulha cada linha num ErrorRecord (NativeCommandError)
  # e, com Stop, isso aborta o script -- mesmo quando o git devolveu 0. E o git escreve no
  # stderr rotineiramente (avisos de CRLF, progresso do push). Sem esta guarda o modo -Apply
  # morria a meio da frota, antes de escrever o relatorio.
  param(
    [string]$RepoPath,
    [string[]]$Arguments
  )

  # core.quotepath=false: por omissao o git cita caminhos com bytes nao-ASCII, ex.:
  #   "doc_templates/assets/NÃ£o confirmado 93645.crdownload"
  # A aspa inicial rebenta qualquer ancora ^ nas expressoes de ambito, e ficheiros com
  # nomes em portugues passavam a ser classificados como fora do ambito da framework.
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = & git -C $RepoPath -c core.quotepath=false @Arguments 2>&1
    $code = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $anterior
  }

  return [pscustomobject]@{
    ExitCode = $code
    Output   = (($output | ForEach-Object { "$_" }) -join "`n")
  }
}

function Invoke-GitStdout {
  # Para comandos cuja saida e PARSEADA (listas de ficheiros, contagens), o stderr tem
  # de ficar de fora: o git escreve avisos rotineiros ali ("warning: ... CRLF will be
  # replaced ...") e, misturados com o stdout, esses avisos entravam na lista de
  # conflitos e eram classificados como caminhos fora do ambito da framework.
  param(
    [string]$RepoPath,
    [string[]]$Arguments
  )

  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = & git -C $RepoPath -c core.quotepath=false @Arguments 2> $null
    $code = $LASTEXITCODE
  }
  finally {
    $ErrorActionPreference = $anterior
  }

  return [pscustomobject]@{
    ExitCode = $code
    Output   = (($output | ForEach-Object { "$_" }) -join "`n")
  }
}

function Get-GitValue {
  param(
    [string]$RepoPath,
    [string[]]$Arguments
  )

  $r = Invoke-GitStdout -RepoPath $RepoPath -Arguments $Arguments
  if ($r.ExitCode -ne 0) { return $null }
  return $r.Output.Trim()
}

function Get-GitLines {
  param(
    [string]$RepoPath,
    [string[]]$Arguments
  )

  $value = Get-GitValue -RepoPath $RepoPath -Arguments $Arguments
  if ([string]::IsNullOrWhiteSpace($value)) { return @() }
  return @($value -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
}

function Get-DeclaredBrodooBranch {
  # A fonte ATUAL e .pg/projects/<key>/project/project.json. O legacy
  # .pg/project/project.json pode estar desatualizado (ex.: dizer "main" quando a branch
  # Brodoo real ja e outra), pelo que so serve de fallback.
  param([string]$RepoPath)

  $projectsDir = Join-Path $RepoPath ".pg\projects"
  if (Test-Path $projectsDir) {
    foreach ($dir in (Get-ChildItem $projectsDir -Directory -ErrorAction SilentlyContinue)) {
      $candidate = Join-Path $dir.FullName "project\project.json"
      if (-not (Test-Path $candidate)) { continue }
      try {
        $branch = (Read-Utf8JsonFile -Path $candidate).project.repository_branch
        if ($branch) { return "$branch" }
      }
      catch { }
    }
  }

  $legacy = Join-Path $RepoPath ".pg\project\project.json"
  if (Test-Path $legacy) {
    try {
      $branch = (Read-Utf8JsonFile -Path $legacy).project.repository_branch
      if ($branch) { return "$branch" }
    }
    catch { }
  }

  return $null
}

function Get-SyncedTemplateHead {
  # Versao da framework com que o repositorio foi sincronizado pela ultima vez.
  # Sem isto a auditoria diz o que FARIA, mas nao diz o que interessa a uma release:
  # quantos repositorios ja correm a versao corrente.
  param([string]$RepoPath)

  $estado = Join-Path $RepoPath ".pg\PG_TEMPLATE_SYNC_STATE.json"
  if (-not (Test-Path $estado)) { return $null }

  try {
    $json = (Get-Content -LiteralPath $estado -Raw -Encoding UTF8) | ConvertFrom-Json
  }
  catch {
    return $null
  }

  $head = [string]$json.template_git_head
  if ([string]::IsNullOrWhiteSpace($head)) { return $null }
  return $head
}

function Get-MirrorNotApplicable {
  # Ha repositorios na raiz da frota que tem .pg/ mas NAO sao projetos de cliente: o
  # repositorio do produto (`parametro-odoo/Parametro_Global`, onde vivem o pg_brodoo e
  # os outros addons da casa) e o exemplo. Nao tem branch Brodoo porque nao ha espelho a
  # publicar -- e o codigo do proprio Brodoo.
  #
  # Ate 2026-09-11 apareciam na lista de nao-alinhados como "branch Brodoo nao declarada",
  # ao lado de casos que sao mesmo defeitos. Uma lista de excepcoes so vale enquanto cada
  # linha merecer atencao; ruido nela ensina a ignora-la toda.
  #
  # Como no PROJECT_PROFILE.json de onde isto herda, e por DECLARACAO EXPLICITA e nunca
  # por inferencia: um repositorio nao sai do perimetro por um script achar que sim.
  param([string]$RepoPath)

  $caminho = Join-Path $RepoPath '.pg\PROJECT_PROFILE.json'
  if (-not (Test-Path $caminho)) { return $null }
  try {
    $dados = Get-Content -Path $caminho -Raw -Encoding UTF8 | ConvertFrom-Json
  }
  catch {
    # Um perfil ilegivel nao pode dispensar nada: seria um gate desligado por um ficheiro
    # partido. O repositorio continua a ser avaliado normalmente.
    return $null
  }
  if ($dados.PSObject.Properties.Name -notcontains 'brodoo_mirror_applicable') { return $null }
  if ([bool]$dados.brodoo_mirror_applicable) { return $null }

  $razao = [string]$dados.reason
  if ([string]::IsNullOrWhiteSpace($razao)) { $razao = 'sem razao declarada no PROJECT_PROFILE.json' }
  return $razao
}

function Get-UnpublishedNonFrameworkCommits {
  # Commits locais que mexem em algo fora do ambito da framework. Se existirem, o push
  # publicaria trabalho de terceiros que ninguem reviu -- e o que protegeu o givachoice
  # (86 commits) e o Hipermercado (232) na operacao manual.
  param(
    [string]$RepoPath,
    [string]$Branch
  )

  $shas = Get-GitLines -RepoPath $RepoPath -Arguments @('rev-list', "origin/$Branch..HEAD")
  $alheios = @()
  foreach ($sha in $shas) {
    $files = Get-GitLines -RepoPath $RepoPath -Arguments @('show', '--name-only', '--format=', $sha)
    $foraDoAmbito = @($files | Where-Object { $_ -notmatch $script:FrameworkPathPattern })
    if ($foraDoAmbito.Count -gt 0) { $alheios += $sha }
  }
  return $alheios
}

function Add-FrameworkPaths {
  param([string]$RepoPath)

  $existentes = @($script:FrameworkPaths | Where-Object {
      Test-Path (Join-Path $RepoPath ($_ -replace '/', '\'))
    })
  if ($existentes.Count -eq 0) { return @() }

  Invoke-Git -RepoPath $RepoPath -Arguments (@('add', '--') + $existentes) | Out-Null
  return (Get-GitLines -RepoPath $RepoPath -Arguments @('diff', '--cached', '--name-only'))
}

function Reset-StagedPublisherPaths {
  # Rede de seguranca: se algum caminho do publisher tiver ficado em stage, retira-o.
  param([string]$RepoPath)

  $staged = Get-GitLines -RepoPath $RepoPath -Arguments @('diff', '--cached', '--name-only')
  $indevidos = @($staged | Where-Object { $_ -match $script:PublisherPathPattern })
  if ($indevidos.Count -eq 0) { return @() }

  Invoke-Git -RepoPath $RepoPath -Arguments (@('restore', '--staged', '--') + $indevidos) | Out-Null
  return $indevidos
}

function Clear-PendingMerge {
  param([string]$RepoPath)

  if (Test-Path (Join-Path $RepoPath '.git\MERGE_HEAD')) {
    Invoke-Git -RepoPath $RepoPath -Arguments @('merge', '--abort') | Out-Null
  }
}

# ---------------------------------------------------------------------------
# Descoberta de repositorios
# ---------------------------------------------------------------------------

$templateRoot = Split-Path -Parent $PSScriptRoot
$reposRootPath = if ([string]::IsNullOrWhiteSpace($ReposRoot)) {
  Split-Path -Parent $templateRoot
}
else {
  [System.IO.Path]::GetFullPath($ReposRoot)
}

if (-not (Test-Path $reposRootPath)) {
  throw "ReposRoot nao encontrado: $reposRootPath"
}

$syncScript = Join-Path $PSScriptRoot "pg_sync_shared_assets.ps1"
if (-not (Test-Path $syncScript)) {
  throw "Script em falta: $syncScript"
}

$templateRootNormalized = ([System.IO.Path]::GetFullPath($templateRoot)).TrimEnd([char]92, [char]47)

$candidatos = if ($RepoNames -and $RepoNames.Count -gt 0) {
  @($RepoNames | ForEach-Object { Join-Path $reposRootPath $_ })
}
else {
  @(Get-ChildItem -Path $reposRootPath -Directory | ForEach-Object { $_.FullName })
}

$repos = @()
$semFramework = @()
foreach ($path in $candidatos) {
  if (-not (Test-Path $path)) {
    Write-Host "AVISO: repo ignorado (nao encontrado): $path"
    continue
  }
  # O proprio _pg_template tem um .pg_framework que aponta para si mesmo (ver a guarda
  # em pg_sync_shared_assets.ps1); nunca e alvo de alinhamento.
  if ((([System.IO.Path]::GetFullPath($path)).TrimEnd([char]92, [char]47)) -ieq $templateRootNormalized) { continue }
  if (-not (Test-Path (Join-Path $path ".git"))) { continue }

  if (-not (Test-Path (Join-Path $path ".pg_framework"))) {
    # Descobrir a frota pela presenca do symlink torna INVISIVEL o repositorio que o
    # perdeu: em vez de aparecer avariado, desaparece da auditoria, do smoke test e
    # deste alinhador ao mesmo tempo -- os tres descobrem-na da mesma maneira.
    # `FACTO OBSERVADO` em 2026-09-10: o `artful` e o `domusacropoles`, ambos com
    # espelho publicado pelo Brodoo, estavam fora do perimetro de tudo sem que nada o
    # dissesse. Um repositorio ELEGIVEL (com `.pg/` ou `PG_CONTEXT.md`) sem o link
    # passa a ser reportado; um que nao seja elegivel continua a nao ser da conta
    # deste script.
    if ((Test-Path (Join-Path $path ".pg")) -or (Test-Path (Join-Path $path "PG_CONTEXT.md"))) {
      $semFramework += [pscustomobject]@{ Name = (Split-Path -Leaf $path); Path = $path }
    }
    continue
  }

  $repos += [pscustomobject]@{ Name = (Split-Path -Leaf $path); Path = $path }
}

if ($repos.Count -eq 0 -and $semFramework.Count -eq 0) {
  if ($RepoNames -and $RepoNames.Count -gt 0) {
    # Um pedido explicito que nao resolve NADA e um erro, nao um silencio.
    #
    # A invocacao que o ritual manda usar -- `powershell -File <script> -RepoNames a,b,c`
    # -- entrega a lista como UM unico nome ("a,b,c"), o caminho nao existe, e o script
    # saia com 0 e sem relatorio: exactamente o que se le como "correu bem, nada a fazer".
    # Aconteceu em 2026-09-10 ao repetir o alinhamento de quatro repositorios.
    # Para passar um array, invocar em processo: `& <script> -RepoNames @('a','b')`.
    Write-Host "ERRO: nenhum dos repositorios pedidos em -RepoNames existe em $reposRootPath."
    Write-Host "      Pedidos: $($RepoNames -join ', ')"
    Write-Host "      Com 'powershell -File' a lista chega como um unico nome; invocar em processo: & <script> -RepoNames @('a','b')"
    exit 1
  }
  Write-Host "AVISO: nenhum repositorio bootstrapado encontrado em $reposRootPath"
  exit 0
}

$frameworkHead = Get-GitValue -RepoPath $templateRoot -Arguments @('rev-parse', 'HEAD')
$frameworkBranch = Get-GitValue -RepoPath $templateRoot -Arguments @('rev-parse', '--abbrev-ref', 'HEAD')

Write-Host "=== pg_align_fleet_framework ==="
Write-Host "  framework : $frameworkBranch @ $($frameworkHead.Substring(0, 7))"
Write-Host "  modo      : $(if ($Apply) { if ($NoPush) { 'APPLY (sem push)' } else { 'APPLY (com push)' } } else { 'AUDITORIA (nada e escrito)' })"
Write-Host "  repos     : $($repos.Count)"
if ($semFramework.Count -gt 0) {
  Write-Host "  sem link  : $($semFramework.Count) (elegiveis, fora do perimetro)"
}
Write-Host ""

# ---------------------------------------------------------------------------
# Alinhamento
# ---------------------------------------------------------------------------

$resultados = @()

foreach ($repo in $repos) {
  $p = $repo.Path
  $registo = [ordered]@{
    repo             = $repo.Name
    declared_branch  = $null
    current_branch   = (Get-GitValue -RepoPath $p -Arguments @('rev-parse', '--abbrev-ref', 'HEAD'))
    synced_head      = (Get-SyncedTemplateHead -RepoPath $p)
    synced_current   = $false
    status           = 'pendente'
    reason           = $null
    attempts         = 0
    files_committed  = 0
    resolved_conflicts = 0
    pushed           = $false
  }

  $registo.synced_current = ($registo.synced_head -eq $frameworkHead)

  # Guarda 0: o repositorio declarou que nao lhe aplica espelho Brodoo. Vem ANTES da
  # exigencia de branch declarada, porque e precisamente essa exigencia que nao se lhe
  # aplica.
  $razaoForaPerimetro = Get-MirrorNotApplicable -RepoPath $p
  if ($razaoForaPerimetro) {
    $registo.status = 'fora_do_perimetro'
    $registo.reason = "declarado sem espelho Brodoo em .pg/PROJECT_PROFILE.json: $razaoForaPerimetro"
    $resultados += [pscustomobject]$registo
    Write-Host ("{0,-22} FORA DO PERIMETRO: {1}" -f $repo.Name, $razaoForaPerimetro)
    continue
  }

  $declarada = Get-DeclaredBrodooBranch -RepoPath $p
  $registo.declared_branch = $declarada

  # Guarda 1: branch Brodoo declarada. Sem declaracao nao ha destino legitimo.
  if ([string]::IsNullOrWhiteSpace($declarada)) {
    $registo.status = 'saltado'
    $registo.reason = 'branch Brodoo nao declarada em project.json'
    $resultados += [pscustomobject]$registo
    Write-Host ("{0,-22} SALTADO: {1}" -f $repo.Name, $registo.reason)
    continue
  }

  # Guarda 2: main e a producao do cliente. Ficheiros de framework nao vao para la.
  if ($declarada -ieq 'main' -or $declarada -ieq 'master') {
    # A declaracao sai do `project.json` do espelho LOCAL, que pode estar meses atrasado:
    # o publisher escreve na branch Brodoo e um clone parado em `main` nunca a viu. Sem
    # esta distincao o alinhador acusava o Odoo de ter a declaracao errada quando o Odoo
    # estava certo. `FACTO OBSERVADO` em 2026-09-10: dos sete repositorios reportados
    # como "declarados main", SEIS ja estavam declarados `brodoo` no Odoo havia meses --
    # com o espelho a publicar sem falhas -- e o que estava velho era o clone local.
    # Mandar corrigir o sitio errado custa mais tempo do que nao dizer nada.
    Invoke-Git -RepoPath $p -Arguments @('fetch', 'origin', '--quiet') | Out-Null
    $brodooRemota = Get-GitValue -RepoPath $p -Arguments @('rev-parse', '--verify', '--quiet', 'refs/remotes/origin/brodoo')

    $registo.status = 'saltado'
    if (-not [string]::IsNullOrWhiteSpace($brodooRemota)) {
      $registo.reason = "o espelho local declara '$declarada', mas o remoto ja tem origin/brodoo: o clone esta desatualizado, nao a declaracao. Correr pg_checkout_brodoo_branch.ps1 e voltar a alinhar"
      Write-Host ("{0,-22} SALTADO: clone desatualizado (declara '{1}', existe origin/brodoo)" -f $repo.Name, $declarada)
    }
    else {
      $registo.reason = "branch Brodoo declarada e '$declarada' (producao do cliente) e nao existe origin/brodoo; migrar a declaracao no Odoo antes de alinhar"
      Write-Host ("{0,-22} SALTADO: branch declarada e '{1}'" -f $repo.Name, $declarada)
    }
    $resultados += [pscustomobject]$registo
    continue
  }

  # Guarda 3: o repositorio tem de estar na branch declarada.
  if ($registo.current_branch -ne $declarada) {
    $registo.status = 'saltado'
    $registo.reason = "esta em '$($registo.current_branch)' e nao na branch Brodoo declarada '$declarada'; correr pg_checkout_brodoo_branch.ps1"
    $resultados += [pscustomobject]$registo
    Write-Host ("{0,-22} SALTADO: esta em '{1}', declarada '{2}'" -f $repo.Name, $registo.current_branch, $declarada)
    continue
  }

  Clear-PendingMerge -RepoPath $p
  Invoke-Git -RepoPath $p -Arguments @('fetch', 'origin', $declarada, '--quiet') | Out-Null

  # Guarda 4: commits locais nao publicados que nao sao de framework.
  #
  # Dizer so quantos commits estao a FRENTE descreve metade do estado, e a metade que
  # falta muda a accao. Uma branch 43 a frente e 0 atras publica-se com um push; 43 a
  # frente e 272 atras nao se publica de todo sem reconciliar primeiro, e o push e
  # recusado pelo git. Ate 2026-09-11 as duas apareciam com o mesmo texto
  # ("publicar ou rever"), e a leitura errada foi feita a partir dele.
  $alheios = Get-UnpublishedNonFrameworkCommits -RepoPath $p -Branch $declarada
  if ($alheios.Count -gt 0) {
    $atrasDiv = Get-GitValue -RepoPath $p -Arguments @('rev-list', '--count', "HEAD..origin/$declarada")
    if ($null -eq $atrasDiv) { $atrasDiv = 0 }
    $registo.status = 'saltado'
    if ([int]$atrasDiv -gt 0) {
      $registo.reason = "DIVERGENTE: $($alheios.Count) commit(s) local(is) fora do ambito da framework e $atrasDiv commit(s) da origin por integrar; reconciliar (merge/rebase) antes de alinhar -- um push seria recusado"
      Write-Host ("{0,-22} SALTADO: DIVERGENTE ({1} a frente, {2} atras)" -f $repo.Name, $alheios.Count, $atrasDiv)
    }
    else {
      $registo.reason = "$($alheios.Count) commit(s) locais nao publicados fora do ambito da framework; publicar ou rever antes de alinhar"
      Write-Host ("{0,-22} SALTADO: {1} commit(s) locais por publicar de outro trabalho" -f $repo.Name, $alheios.Count)
    }
    $resultados += [pscustomobject]$registo
    continue
  }

  if (-not $Apply) {
    $registo.status = 'alinharia'
    $atras = Get-GitValue -RepoPath $p -Arguments @('rev-list', '--count', "HEAD..origin/$declarada")
    $registo.reason = "pronto a alinhar (a $atras commit(s) da origin)"
    $resultados += [pscustomobject]$registo
    Write-Host ("{0,-22} ALINHARIA em '{1}' (a {2} commit(s) da origin)" -f $repo.Name, $declarada, $atras)
    continue
  }

  $sucesso = $false
  for ($tentativa = 1; $tentativa -le $MaxAttempts; $tentativa++) {
    $registo.attempts = $tentativa

    # (2) fetch imediatamente antes do merge: o publisher do espelho escreve nesta branch
    # durante a execucao, e um merge contra uma referencia velha faz o push ser rejeitado.
    Invoke-Git -RepoPath $p -Arguments @('fetch', 'origin', $declarada, '--quiet') | Out-Null

    # (3) desversionar o estado local ANTES do merge. O `.pg/PREFLIGHT.json` e
    # regenerado a cada arranque e esta seguido em varios repositorios da frota; se ficar
    # no indice, modificado localmente e tambem alterado pelos commits a entrar, o git
    # RECUSA-SE a comecar o merge. A v2.21.1 pos este desversionamento no sync, que corre
    # DEPOIS do merge -- pelo que nunca chegava a desbloquear nada. Tem de ser aqui.
    Remove-PgTrackedLocalState -RepoPath $p | Out-Null

    # Sair do indice nao basta: o ficheiro fica no disco como NAO seguido, e o git
    # recusa-se igualmente a sobrepor um ficheiro nao seguido durante o merge
    # ("untracked working tree file would be overwritten"). Como e estado local
    # regenerado pelo pg_preflight_context.ps1 no arranque seguinte, aqui sai do disco.
    # (O sync, ao contrario, mantem-no: la nao ha merge a desbloquear.)
    foreach ($relativo in $script:PgLocalStatePaths) {
      # String.Replace e nao -replace: o operador trata a substituicao como padrao
      $absoluto = Join-Path $p ($relativo.Replace([string][char]47, [string][char]92))
      if (Test-Path $absoluto) { Remove-Item $absoluto -Force -ErrorAction SilentlyContinue }
    }

    # (4) commit do estado local dos ficheiros de framework (inclui a saida do indice)
    $staged = Add-FrameworkPaths -RepoPath $p
    Reset-StagedPublisherPaths -RepoPath $p | Out-Null
    if ((Get-GitLines -RepoPath $p -Arguments @('diff', '--cached', '--name-only')).Count -gt 0) {
      Invoke-Git -RepoPath $p -Arguments @('commit', '-q', '-m', $script:CommitMessageLocal) | Out-Null
    }

    # (4) merge real
    $merge = Invoke-Git -RepoPath $p -Arguments @('merge', "origin/$declarada", '--no-edit')
    $conflitos = Get-GitLines -RepoPath $p -Arguments @('diff', '--name-only', '--diff-filter=U')

    # Um merge RECUSADO nao produz conflitos: o git aborta antes de comecar (ex.: "Your
    # local changes to the following files would be overwritten by merge"). Sem verificar
    # o codigo de saida, o script seguia, commitava e tentava publicar uma branch que
    # continuava centenas de commits atras -- e cada retentativa juntava um commit
    # redundante. Verificar o exit code e obrigatorio, e nao se retenta: a causa e local
    # e nao se resolve por repetir.
    if ($merge.ExitCode -ne 0 -and $conflitos.Count -eq 0) {
      Clear-PendingMerge -RepoPath $p
      # A mensagem util do git vem em varias linhas: o cabecalho "error: Your local
      # changes ... would be overwritten by merge:" seguido da LISTA de ficheiros. Guardar
      # so a primeira linha dava um diagnostico sem o dado que interessa.
      $linhasUteis = @($merge.Output -split "`n" |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -ne '' -and $_ -notmatch '^(Aborting|Please commit|Please move|hint:)' })
      $registo.status = 'merge_recusado'
      $registo.reason = "o git recusou o merge: $($linhasUteis -join ' | ') -- resolver o estado local antes de alinhar"
      Write-Host ("{0,-22} MERGE RECUSADO: {1}" -f $repo.Name, $registo.reason)
      break
    }

    if ($conflitos.Count -gt 0) {
      $foraDoAmbito = @($conflitos | Where-Object { $_ -notmatch $script:FrameworkPathPattern })

      # Fora do ambito nao ha resolucao automatica segura: aborta e reporta.
      if ($foraDoAmbito.Count -gt 0) {
        Clear-PendingMerge -RepoPath $p
        $registo.status = 'conflito'
        $registo.reason = "conflito fora do ambito da framework: $($foraDoAmbito -join ', ')"
        Write-Host ("{0,-22} CONFLITO: {1}" -f $repo.Name, $registo.reason)
        break
      }

      # Conflito SO em ficheiros de framework resolve-se: o conteudo destes ficheiros nao
      # se negocia entre lados, e regenerado a partir do template pelo sync idempotente
      # do passo seguinte. Ficar pelo nosso lado e apenas o que faz o merge fechar.
      foreach ($f in $conflitos) {
        if ($script:PgLocalStatePaths -contains $f) {
          # Conflito delete/modify: nos apagamos o estado local, o lado remoto alterou-o.
          # `checkout --ours` nao serve para um ficheiro apagado; manter a remocao e o
          # resultado certo -- e estado da maquina e o preflight regenera-o.
          Invoke-Git -RepoPath $p -Arguments @('rm', '-q', '-f', '--ignore-unmatch', '--', $f) | Out-Null
          continue
        }
        Invoke-Git -RepoPath $p -Arguments @('checkout', '--ours', '--', $f) | Out-Null
        Invoke-Git -RepoPath $p -Arguments @('add', '--', $f) | Out-Null
      }
      $conclusao = Invoke-Git -RepoPath $p -Arguments @('commit', '-q', '--no-edit')
      if ($conclusao.ExitCode -ne 0) {
        Clear-PendingMerge -RepoPath $p
        $registo.status = 'conflito'
        $registo.reason = "conflito em ficheiros de framework que nao foi possivel fechar: $($conflitos -join ', ')"
        Write-Host ("{0,-22} CONFLITO: {1}" -f $repo.Name, $registo.reason)
        break
      }
      $registo.resolved_conflicts = $conflitos.Count
      Write-Host ("{0,-22} conflito de framework resolvido em {1} ficheiro(s); o sync regenera o conteudo" -f $repo.Name, $conflitos.Count)
    }

    # (5) sync idempotente: garante o conteudo da versao atual da framework
    $anteriorSync = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $syncScript -RepoName $repo.Name -RepoPath $p *> $null
      $syncCode = $LASTEXITCODE
    }
    finally {
      $ErrorActionPreference = $anteriorSync
    }
    if ($syncCode -ne 0) {
      $registo.status = 'erro'
      $registo.reason = 'pg_sync_shared_assets.ps1 falhou'
      Write-Host ("{0,-22} ERRO: sync falhou" -f $repo.Name)
      break
    }

    # (6) commit final
    Add-FrameworkPaths -RepoPath $p | Out-Null
    Reset-StagedPublisherPaths -RepoPath $p | Out-Null
    $final = Get-GitLines -RepoPath $p -Arguments @('diff', '--cached', '--name-only')
    if ($final.Count -gt 0) {
      $mensagem = @"
chore(framework): sincronizar com _pg_template $($frameworkHead.Substring(0, 7))

Alinha os ficheiros geridos pela framework com a versao atual do
_pg_template. Nao toca em .pg/projects/**, projects/** nem
PG_CONTEXT.md, que sao escritos pelo publisher do espelho.
"@
      Invoke-Git -RepoPath $p -Arguments @('commit', '-q', '-m', $mensagem) | Out-Null
      $registo.files_committed = $final.Count
    }

    $porPublicar = Get-GitLines -RepoPath $p -Arguments @('rev-list', "origin/$declarada..HEAD")
    if ($porPublicar.Count -eq 0) {
      $registo.status = 'alinhado'
      $registo.reason = 'ja estava alinhado; nada a publicar'
      $sucesso = $true
      Write-Host ("{0,-22} ja alinhado" -f $repo.Name)
      break
    }

    if ($NoPush) {
      $registo.status = 'commitado'
      $registo.reason = 'commit feito; push nao pedido (-NoPush)'
      $sucesso = $true
      Write-Host ("{0,-22} {1,-10} {2} ficheiros commitados (sem push)" -f $repo.Name, $declarada, $registo.files_committed)
      break
    }

    $push = Invoke-Git -RepoPath $p -Arguments @('push', 'origin', $declarada)
    if ($push.ExitCode -eq 0) {
      $registo.status = 'publicado'
      $registo.pushed = $true
      $sucesso = $true
      Write-Host ("{0,-22} {1,-10} {2} ficheiros -> {3} PUBLICADO (tentativa {4})" -f `
          $repo.Name, $declarada, $registo.files_committed, (Get-GitValue -RepoPath $p -Arguments @('rev-parse', '--short', 'HEAD')), $tentativa)
      break
    }

    # push rejeitado: o publisher escreveu entretanto. A tentativa seguinte volta a
    # buscar e a fazer merge. Nada e forcado.
    if ($tentativa -eq $MaxAttempts) {
      $registo.status = 'nao_publicado'
      $registo.reason = "push rejeitado em $MaxAttempts tentativas (corrida com o publisher do espelho); os commits ficam locais"
      Write-Host ("{0,-22} NAO PUBLICADO apos {1} tentativas (corrida com o publisher)" -f $repo.Name, $MaxAttempts)
    }
  }

  if (-not $sucesso -and $registo.status -eq 'pendente') {
    $registo.status = 'erro'
    $registo.reason = 'terminou sem estado conclusivo'
  }

  $resultados += [pscustomobject]$registo
}

# Repositorios elegiveis sem `.pg_framework`: entram no relatorio para deixarem de ser
# invisiveis, mas NAO contam para o codigo de saida. Resolve-los exige uma decisao
# humana -- ligar a framework, ou tirar a pasta da raiz da frota -- e um check
# permanentemente vermelho treina qualquer pessoa a ignorar o resultado (a licao do
# emparelhamento de eventos em pg_validate_token_consumption.ps1).
foreach ($orfao in $semFramework) {
  $resultados += [pscustomobject]([ordered]@{
    repo             = $orfao.Name
    declared_branch  = (Get-DeclaredBrodooBranch -RepoPath $orfao.Path)
    current_branch   = (Get-GitValue -RepoPath $orfao.Path -Arguments @('rev-parse', '--abbrev-ref', 'HEAD'))
    synced_head      = (Get-SyncedTemplateHead -RepoPath $orfao.Path)
    synced_current   = $false
    status           = 'sem_framework'
    reason           = 'elegivel (tem .pg/ ou PG_CONTEXT.md) mas sem .pg_framework ligado; correr pg_link_framework.ps1, ou tirar a pasta da raiz da frota se for um clone duplicado'
    attempts         = 0
    files_committed  = 0
    resolved_conflicts = 0
    pushed           = $false
  })
}

# O `synced_head` de cada registo foi lido ANTES do sync desse repositorio. Em modo
# -Apply isso torna-o obsoleto no momento de contar: o resumo anunciava "0 de 33"
# imediatamente a seguir a alinhar 25 repositorios com sucesso. Reler do disco antes
# de somar -- um numero que contradiz o que o proprio relatorio acabou de listar e
# pior do que numero nenhum, porque ensina a nao acreditar no relatorio.
foreach ($registo in $resultados) {
  $caminhoRepo = Join-Path $reposRootPath $registo.repo
  if (Test-Path $caminhoRepo) {
    $registo.synced_head = Get-SyncedTemplateHead -RepoPath $caminhoRepo
    $registo.synced_current = ($registo.synced_head -eq $frameworkHead)
  }
}

# ---------------------------------------------------------------------------
# Relatorio
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "=== Resumo ==="
$porEstado = $resultados | Group-Object status | Sort-Object Name
foreach ($grupo in $porEstado) {
  Write-Host ("  {0,-16} {1}" -f $grupo.Name, $grupo.Count)
}

$naVersao = @($resultados | Where-Object { $_.synced_current })
Write-Host ""
Write-Host ("  na versao corrente ({0}): {1} de {2} repositorios" -f $frameworkHead.Substring(0, 7), $naVersao.Count, $resultados.Count)

# 'fora_do_perimetro' fica FORA desta lista de proposito: nao e um problema por
# resolver, e uma decisao ja tomada e declarada. Continua no relatorio JSON e na
# contagem do resumo, para nao desaparecer em silencio.
$saltados = @($resultados | Where-Object { $_.status -in @('saltado', 'conflito', 'merge_recusado', 'nao_publicado', 'erro', 'sem_framework') })
if ($saltados.Count -gt 0) {
  Write-Host ""
  Write-Host "Nao alinhados (com a razao, para nao passarem por cobertura silenciosa):"
  foreach ($r in $saltados) {
    Write-Host ("  {0,-22} {1}: {2}" -f $r.repo, $r.status, $r.reason)
  }
}

if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
  $relatorio = [ordered]@{
    schema_version   = '1.0'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    framework_head   = $frameworkHead
    framework_branch = $frameworkBranch
    mode             = if ($Apply) { if ($NoPush) { 'apply_no_push' } else { 'apply' } } else { 'audit' }
    repos_total      = $resultados.Count
    repos_na_versao  = $naVersao.Count
    repos            = $resultados
  }
  Write-Utf8NoBomFile -Path $ReportPath -Content (($relatorio | ConvertTo-Json -Depth 6))
  Write-Host ""
  Write-Host "Relatorio escrito em $ReportPath"
}

$falhas = @($resultados | Where-Object { $_.status -in @('erro', 'conflito', 'merge_recusado') })
if ($falhas.Count -gt 0) { exit 1 }
exit 0
