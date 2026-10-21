<#
.SYNOPSIS
  Bootstrap automatico na primeira sessao de um repositorio que ainda nao tem a framework.

.DESCRIPTION
  Ate aqui, cada repositorio novo obrigava alguem a ir as suas notas, copiar o comando do
  pg_bootstrap_assisted.ps1, trocar o nome e o caminho do repositorio, descobrir a versao
  do Odoo e colar no terminal. O ritual nao o podia fazer: o ritual corre a partir de
  `.pg_framework\scripts\`, e num repositorio por bootstrapar esse atalho ainda nao existe.
  Os hooks do projeto tambem nao: o `.claude/settings.json` e copiado PELO bootstrap.

  Por isso este script vive no `_pg_template` e e chamado por um hook do UTILIZADOR
  (~/.claude/settings.json, instalado por pg_install_user_hooks.py), que existe antes de
  qualquer repositorio. Corre no arranque de todas as sessoes, e no caminho normal (repo
  ja bootstrapado, ou pasta que nao e repo) sai logo, em silencio.

  Os dados vem do sitio onde ja estao declarados, e nao de memoria:
    - caminho e nome: a raiz git da pasta onde a sessao abriu;
    - projeto, versao, edicao e branch: o projeto Brodoo ligado a este repositorio GitHub
      (project.project por pg_repository_id.full_name), pelo canal Brodoo;
    - a versao explicita (-Series) ou ja escrita no PG_CONTEXT.md manda sobre o Brodoo.

  So faz bootstrap automatico de repositorios LIGADOS a um projeto no Brodoo. E esse o
  gate: este hook corre em qualquer repositorio que se abra nesta maquina, e um clone de
  um projeto open source nao deve ganhar AGENTS.md, .pg/ nem uma branch brodoo publicada.
  Sem projeto no Brodoo, nao faz nada -- e, se o repositorio estiver na pasta dos repos da
  Parametro, deixa ao agente o comando ja preenchido para perguntar ao utilizador.

  Versao Odoo desconhecida nunca e adivinhada (regra do ritual): faz-se o bootstrap da
  framework, que nao depende da versao, e o clone do source fica por fazer, com o motivo.
  `FACTO OBSERVADO` (2026-09-28): o vendaspp esta ligado ao projeto Paujoba, sem versao.

  Custo no arranque: o source Odoo e global por serie (~/.pg/odoo_src/<serie>). Se a serie
  ja estiver nesta maquina, liga-se sem fetch (segundos). Se nao estiver, o clone sao GB e
  minutos, e isso nao se faz a revelia no arranque de uma sessao: fica adiado, e o agente
  recebe o comando exato para o correr em segundo plano.

  A prova de falhas em modo -Hook: qualquer erro e reportado e o script sai com 0. Um hook
  nunca estraga a sessao de quem esta a trabalhar.

.PARAMETER RepoPath
  Pasta do repositorio (ou uma subpasta). Sem ele: o `cwd` do payload do hook, ou a pasta atual.

.PARAMETER Hook
  Modo hook: le o payload do stdin, fica em silencio quando nao ha nada a fazer, nao corre
  clones longos e guarda o detalhe do bootstrap num log em vez de o despejar na sessao.

.PARAMETER Series
  Forca a serie Odoo (ex.: 19.0). Manda sobre o PG_CONTEXT.md e sobre o Brodoo.

.PARAMETER Edition
  Forca a edicao (community|enterprise). Por omissao, a declarada no Brodoo.

.PARAMETER WhatIf
  Mostra a decisao (PLANO) sem mudar de branch nem escrever nada.

.PARAMETER SemBrodoo
  Manual: bootstrapa mesmo sem projeto no Brodoo. E a decisao que o gate nao toma sozinho,
  e por isso so existe como pedido explicito de quem corre o comando.

.PARAMETER BrodooLookupPath
  Testes: ficheiro JSON com a resposta simulada do Brodoo (lista de projetos), em vez da API.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_auto_bootstrap.ps1 -RepoPath ..\NovoRepo -WhatIf

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_auto_bootstrap.ps1 -RepoPath ..\NovoRepo -Series 19.0
#>
param(
  [string]$RepoPath,
  [switch]$Hook,
  [string]$Series,
  [ValidateSet("auto", "community", "enterprise")]
  [string]$Edition = "auto",
  [switch]$WhatIf,
  [string]$BrodooLookupPath,
  [switch]$SemBrodoo
)

$ErrorActionPreference = "Stop"

$templateRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$prefixo = "PG AUTO-BOOTSTRAP:"

# Ha gente da equipa em macOS. Dois cuidados, os mesmos do pg_odoo_credentials_common.ps1:
# os caminhos montam-se um segmento de cada vez (uma barra invertida dentro de um segmento
# e separador no Windows e um caractere normal no macOS), e o PowerShell dos processos
# filhos e o mesmo que corre este script -- `powershell.exe` so existe no Windows.
$script:EmWindows = if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) { [bool]$IsWindows } else { $true }
$script:PsExe = try { (Get-Process -Id $PID).Path } catch { $null }
if (-not $script:PsExe) { $script:PsExe = if ($script:EmWindows) { "powershell" } else { "pwsh" } }
$script:PsComando = if ($script:EmWindows) { "powershell -NoProfile -ExecutionPolicy Bypass -File" } else { "pwsh -NoProfile -File" }

function Join-Segments {
  param([string]$Base, [string[]]$Segments)
  foreach ($segmento in $Segments) { $Base = Join-Path $Base $segmento }
  return $Base
}
$script:LoginBrodoo = $null

function Say {
  param([string]$Message)
  Write-Host $Message
}

function Stop-Quietly {
  # Em modo hook, "nada a fazer" e silencio; em modo manual, diz porque.
  param([string]$Reason)
  if (-not $Hook -and $Reason) { Say "$prefixo $Reason" }
  exit 0
}

function Invoke-GitText {
  param([string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $saida = & git @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return (($saida | ForEach-Object { "$_" }) -join "`n").Trim()
  }
  catch { return $null }
  finally { $ErrorActionPreference = $anterior }
}

function Get-GitHubFullName {
  # https://github.com/owner/repo(.git) ou git@github.com:owner/repo(.git) -> owner/repo
  # Aceita tambem atalhos SSH do ~/.ssh/config que comecem por "github" (ex.: git@github-pg:owner/repo),
  # usados por quem tem mais de uma conta GitHub na maquina.
  param([string]$Url)
  if ([string]::IsNullOrWhiteSpace($Url)) { return $null }
  if ($Url -match 'github(\.com|[\w-]*)[:/]+([^/]+)/([^/]+?)(\.git)?/?$') {
    return "{0}/{1}" -f $Matches[2], $Matches[3]
  }
  return $null
}

function ConvertTo-SeriesText {
  # "19", "19.0", "19e", "Odoo 19.0 Enterprise" -> "19.0"; "saas~18.4" -> "18.4"
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
  if ($Value -match '(\d{2})(?:\.(\d+))?') {
    $minor = if ($Matches[2]) { $Matches[2] } else { "0" }
    return "{0}.{1}" -f $Matches[1], $minor
  }
  return $null
}

function Get-SeriesFromContext {
  # Tres escritas convivem na frota, e nao valem o mesmo:
  #   - "Versao do Odoo:" (template) e "Odoo Version:" (escrita a mao): DECLARADAS por
  #     alguem, ou pelo pg_sync_pg_context.ps1 a partir do source real. Mandam sobre o Brodoo.
  #   - "- Versao Odoo:" (em lista, sem o "do"): o bloco que o espelho do Brodoo escreve.
  #     E uma copia do Brodoo, e uma copia que envelhece: nao e regenerada quando a versao
  #     muda. `FACTO OBSERVADO` (givachoice, 2026-08-11): o bloco dizia 17.0 com o Brodoo
  #     ja em 19.0. Se mandasse sobre o Brodoo, um bloco velho ligava o source da serie
  #     errada -- a confusao 17/19 que a framework existe para travar. Por isso so conta
  #     quando o Brodoo nao da uma versao unica, que e o caso em que faz falta.
  # Ler so a escrita do template deixava 19 dos 32 PG_CONTEXT.md desta maquina por ler
  # (Bruno Pinheiro, PR #64). Duas linhas da mesma classe com versoes diferentes nao se
  # escolhem, pela mesma razao que dois projetos do Brodoo em desacordo nao se escolhem.
  # O marcador do template ("[PONTO POR VALIDAR]") nao e versao.
  param([string]$Repo)
  $r = @{ Declarada = $null; Espelho = $null; Conflito = $null; ConflitoEspelho = $null }
  $contexto = Join-Path $Repo "PG_CONTEXT.md"
  if (-not (Test-Path $contexto)) { return $r }
  try { $texto = [System.IO.File]::ReadAllText($contexto, [System.Text.Encoding]::UTF8) } catch { return $r }

  $padrao = '^\s*(?:[-*+]\s+)?(Vers(?:ao|\u00e3o)\s+do\s+Odoo|Odoo\s+Version|Vers(?:ao|\u00e3o)\s+Odoo)\s*:\s*(.+?)\s*$'
  $declaradas = @()
  $espelho = @()
  foreach ($m in [regex]::Matches($texto, $padrao, 'IgnoreCase, Multiline')) {
    $valor = $m.Groups[2].Value
    if ($valor -match 'POR VALIDAR') { continue }
    $serieLida = ConvertTo-SeriesText -Value $valor
    if (-not $serieLida) { continue }
    if ($m.Groups[1].Value -match '^Vers(?:ao|\u00e3o)\s+Odoo$') {
      if ($espelho -notcontains $serieLida) { $espelho += $serieLida }
    }
    elseif ($declaradas -notcontains $serieLida) { $declaradas += $serieLida }
  }
  if ($declaradas.Count -eq 1) { $r.Declarada = $declaradas[0] }
  elseif ($declaradas.Count -gt 1) { $r.Conflito = ($declaradas -join ', ') }
  if ($espelho.Count -eq 1) { $r.Espelho = $espelho[0] }
  elseif ($espelho.Count -gt 1) { $r.ConflitoEspelho = ($espelho -join ', ') }
  return $r
}

function ConvertFrom-ProjectsJson {
  # No PS 5.1 o ConvertFrom-Json devolve um array JSON como UM objeto: `@(... | ConvertFrom-Json)`
  # sobre "[]" dava Count 1, e o gate "tem projeto no Brodoo" abria-se para um repositorio
  # sem projeto nenhum. Apanhado pelo pg_test_auto_bootstrap.ps1. Enumerar a partir de uma
  # variavel desfaz o embrulho; e so conta como projeto um registo com id.
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return ,@() }
  $parsed = $Text | ConvertFrom-Json
  $lista = @($parsed | ForEach-Object { $_ } | Where-Object { $null -ne $_ -and $_.PSObject.Properties['id'] -and $_.id })
  return ,$lista
}

function Test-ChavePessoal {
  # Chave desta pessoa (ficheiro da maquina ou variavel de ambiente), e nao a partilhada.
  try {
    . (Join-Path $PSScriptRoot "pg_odoo_credentials_common.ps1")
    return ((Get-PgOdooCredentialSource).kind -in @("maquina", "env"))
  }
  catch { return $false }
}

function Get-BrodooProjects {
  # Devolve @{ Ok = $bool; Projetos = @(...); Erro = "..." }. Ok=$false quer dizer que o
  # Brodoo nao respondeu -- diferente de responder "nenhum projeto".
  param([string]$FullName)

  if ($BrodooLookupPath) {
    $raw = [System.IO.File]::ReadAllText($BrodooLookupPath, [System.Text.Encoding]::UTF8)
    return @{ Ok = $true; Projetos = (ConvertFrom-ProjectsJson -Text $raw); Erro = $null }
  }

  # So com a chave PESSOAL. A cascata de credenciais ainda cai na chave partilhada do
  # utilizador Brodoo quando a maquina nao tem a sua -- e esse utilizador vai deixar de
  # existir, e o que se fizer com ele nao tem dono. Um hook que corre sozinho no arranque
  # nao pode ser a via por onde essa chave continua em uso sem ninguem dar por isso.
  . (Join-Path $PSScriptRoot "pg_odoo_credentials_common.ps1")
  $setup = '{0} "{1}"' -f $script:PsComando, (Join-Path $PSScriptRoot "pg_init_odoo_credentials.ps1")
  $fonte = Get-PgOdooCredentialSource
  if ($fonte.kind -eq 'legado') {
    return @{ Ok = $false; Projetos = @(); Login = $null
      Erro = "esta maquina so tem a chave partilhada do utilizador Brodoo, que o hook nao usa. Configurar a chave pessoal: $setup" }
  }
  if ($fonte.kind -eq 'nenhuma') {
    return @{ Ok = $false; Projetos = @(); Login = $null
      Erro = "sem chave pessoal do Odoo PG nesta maquina. Configurar: $setup" }
  }
  $script:LoginBrodoo = [string]$fonte.login

  $query = Join-Path $PSScriptRoot "pg_odoo_query.ps1"
  $domain = '[["pg_repository_id.full_name","=ilike","' + $FullName + '"]]'
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    # Chamado no mesmo processo: passar JSON com aspas a um powershell.exe filho parte as
    # aspas no PS 5.1. Os Write-Host/avisos do helper (6>, 3>) nao vao parar a sessao.
    $saida = & $query -Model project.project -Method search_read -Domain $domain `
      -Fields name, pg_project_key, pg_repo_branch, pg_odoo_version, pg_odoo_edition 2>&1 3>$null 6>$null
    $codigo = $LASTEXITCODE
  }
  catch {
    return @{ Ok = $false; Projetos = @(); Erro = $_.Exception.Message }
  }
  finally { $ErrorActionPreference = $anterior }

  $texto = (($saida | Where-Object { $_ -is [string] }) -join "`n").Trim()
  if ($codigo -ne 0) {
    $erro = (($saida | Where-Object { $_ -isnot [string] } | ForEach-Object { "$_" }) -join " ").Trim()
    if (-not $erro) { $erro = $texto }
    return @{ Ok = $false; Projetos = @(); Erro = $erro }
  }
  if (-not $texto) { return @{ Ok = $true; Projetos = @(); Erro = $null } }
  return @{ Ok = $true; Projetos = (ConvertFrom-ProjectsJson -Text $texto); Erro = $null }
}

function Get-DistinctValues {
  param([object[]]$Items, [string]$Field)
  $valores = @()
  foreach ($item in $Items) {
    $v = $item.$Field
    if ($null -eq $v -or $v -is [bool]) { continue }   # o Odoo devolve false para vazio
    $v = ([string]$v).Trim()
    if ($v -and $valores -notcontains $v) { $valores += $v }
  }
  return ,$valores
}

function Get-OdooSourceRoot {
  if (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_SOURCE_ROOT)) {
    return [System.IO.Path]::GetFullPath($env:PG_ODOO_SOURCE_ROOT)
  }
  return Join-Segments $HOME @(".pg", "odoo_src")
}

function Format-BootstrapCommand {
  param([string]$Repo, [string]$SeriesText, [string]$EditionText)
  $serieArg = if ($SeriesText) { $SeriesText } else { "<SERIE>" }
  $cmd = '{0} "{1}" -RepoPath "{2}" -Series {3}' -f `
    $script:PsComando, (Join-Path $PSScriptRoot "pg_auto_bootstrap.ps1"), $Repo, $serieArg
  if ($EditionText -and $EditionText -ne "auto") { $cmd += " -Edition $EditionText" }
  return $cmd
}

try {
  if ($env:PG_AUTO_BOOTSTRAP -eq "0") { Stop-Quietly "desligado por PG_AUTO_BOOTSTRAP=0." }

  # --- 1. Onde abriu a sessao -------------------------------------------------------
  $inicio = $RepoPath
  if ($Hook -and -not $inicio) {
    try {
      $raw = [Console]::In.ReadToEnd()
      if (-not [string]::IsNullOrWhiteSpace($raw)) { $inicio = [string](($raw | ConvertFrom-Json).cwd) }
    }
    catch { }
  }
  if (-not $inicio) { $inicio = (Get-Location).Path }
  if (-not (Test-Path $inicio)) { Stop-Quietly "pasta nao encontrada: $inicio" }
  $inicio = [System.IO.Path]::GetFullPath($inicio)

  # Caminho rapido: e o que acontece em quase todas as sessoes. Ser o proprio framework
  # decide-se ANTES do atalho, porque o _pg_template tambem pode ter um .pg_framework a
  # apontar para si mesmo (o .gitignore preve-o) e ai dizia "ja bootstrapado" em vez de
  # "e o proprio framework" -- e era a suite que ficava cega, que e o que custa.
  if ($inicio -eq $templateRoot) { Stop-Quietly "e o proprio framework ($inicio)." }
  if (Test-Path (Join-Path $inicio ".pg_framework")) { Stop-Quietly "ja bootstrapado ($inicio)." }

  $topo = Invoke-GitText -Arguments @("-C", $inicio, "rev-parse", "--show-toplevel")
  if (-not $topo) { Stop-Quietly "nao e um repositorio git: $inicio" }
  $repo = [System.IO.Path]::GetFullPath($topo)   # no Windows normaliza as barras do git
  $repoName = Split-Path -Leaf $repo

  # --- 2. O que nunca se bootstrapa sozinho ----------------------------------------
  if ($repo -eq $templateRoot -or
      ((Test-Path (Join-Segments $repo @("templates", "AGENTS_SHARED.md"))) -and (Test-Path (Join-Segments $repo @("scripts", "pg_bootstrap_repo.ps1"))))) {
    Stop-Quietly "e o proprio framework ($repo)."
  }

  if (Test-Path (Join-Path $repo ".pg_framework")) { Stop-Quietly "ja bootstrapado ($repo)." }

  $agentsPath = Join-Path $repo "AGENTS.md"
  if (Test-Path $agentsPath) {
    $agents = [System.IO.File]::ReadAllText($agentsPath, [System.Text.Encoding]::UTF8)
    if ($agents -match 'PG_WORK_FOLDER:START') { Stop-Quietly "pasta de trabalho declarada (PG_WORK_FOLDER), nao e projeto." }
  }

  $odooAplicavel = $true
  $perfilPath = Join-Segments $repo @(".pg", "PROJECT_PROFILE.json")
  if (Test-Path $perfilPath) {
    try {
      $perfil = [System.IO.File]::ReadAllText($perfilPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
      if ($perfil.brodoo_mirror_applicable -eq $false) {
        Stop-Quietly "repositorio de produto (brodoo_mirror_applicable: false); bootstrap so manual."
      }
      if ($perfil.odoo_applicable -eq $false) { $odooAplicavel = $false }
    }
    catch { }   # perfil ilegivel nao dispensa nada: segue como projeto Odoo
  }

  $irmaoDoTemplate = ((Split-Path -Parent $repo) -eq (Split-Path -Parent $templateRoot))

  # --- 3. O projeto no Brodoo ------------------------------------------------------
  $origin = Invoke-GitText -Arguments @("-C", $repo, "remote", "get-url", "origin")
  $fullName = Get-GitHubFullName -Url $origin

  $consulta = @{ Ok = $false; Projetos = @(); Erro = "sem remoto GitHub em origin" }
  if ($fullName -or $BrodooLookupPath) { $consulta = Get-BrodooProjects -FullName $fullName }
  $projetos = @($consulta.Projetos)

  if ($projetos.Count -eq 0 -and -not ($SemBrodoo -and -not $Hook)) {
    # Sem projeto nao ha gate satisfeito. Fora da pasta dos repos, silencio: pode ser
    # qualquer repositorio do mundo. Dentro dela, o agente recebe o comando pronto.
    if ($Hook -and -not $irmaoDoTemplate) { exit 0 }
    $motivo = if (-not $fullName) { "sem remoto GitHub em origin" }
              elseif (-not $consulta.Ok) { "o Brodoo nao respondeu ($($consulta.Erro))" }
              else { "nenhum projeto do Brodoo esta ligado a $fullName" }
    $lidoLocal = Get-SeriesFromContext -Repo $repo
    $serieLocal = if ($Series) { ConvertTo-SeriesText -Value $Series } elseif ($lidoLocal.Declarada) { $lidoLocal.Declarada } else { $lidoLocal.Espelho }
    Say "$prefixo '$repoName' ainda nao tem a framework, mas nao foi feito nada: $motivo."
    Say "  So se faz bootstrap automatico de repositorios ligados a um projeto no Brodoo."
    Say "  Perguntar ao utilizador se quer bootstrapar este repositorio e qual a versao Odoo; depois correr:"
    Say ("  " + (Format-BootstrapCommand -Repo $repo -SeriesText $serieLocal -EditionText $Edition) + " -SemBrodoo")
    exit 0
  }

  # --- 4. Versao, edicao e branch --------------------------------------------------
  $nomesProjetos = (@($projetos | ForEach-Object { [string]$_.pg_project_key }) -join ", ")
  if (-not $nomesProjetos) { $nomesProjetos = "(sem projeto no Brodoo: -SemBrodoo)" }
  $versoesBrodoo = Get-DistinctValues -Items $projetos -Field "pg_odoo_version"
  $edicoesBrodoo = @((Get-DistinctValues -Items $projetos -Field "pg_odoo_edition") | Where-Object { $_ -in @("community", "enterprise") })
  $branchesBrodoo = @((Get-DistinctValues -Items $projetos -Field "pg_repo_branch") | Where-Object { @("main", "master") -notcontains $_ })

  $serie = $null
  $origemSerie = $null
  $motivoSemSerie = $null
  if ($Series) {
    $serie = ConvertTo-SeriesText -Value $Series
    $origemSerie = "indicada (-Series)"
    if (-not $serie) { throw "Serie Odoo invalida: $Series. Exemplos: 19.0, 18.0." }
  }
  # Ordem: -Series > versao DECLARADA no PG_CONTEXT.md > Brodoo > bloco do espelho no
  # PG_CONTEXT.md (so quando o Brodoo nao da uma versao unica). Ver Get-SeriesFromContext.
  $lido = Get-SeriesFromContext -Repo $repo
  $avisoEspelho = $null
  if (-not $serie) {
    if ($lido.Conflito) {
      $motivoSemSerie = "o PG_CONTEXT.md declara versoes diferentes ($($lido.Conflito)); nao se escolhe"
    }
    elseif ($lido.Declarada) {
      $serie = $lido.Declarada
      $origemSerie = "PG_CONTEXT.md"
    }
    else {
      $serieBrodoo = $null
      $motivoBrodoo = $null
      if ($versoesBrodoo.Count -eq 1) {
        $serieBrodoo = ConvertTo-SeriesText -Value $versoesBrodoo[0]
        if (-not $serieBrodoo) { $motivoBrodoo = "versao declarada no Brodoo ilegivel ('$($versoesBrodoo[0])')" }
      }
      elseif ($versoesBrodoo.Count -gt 1) {
        $motivoBrodoo = "projetos do Brodoo com versoes diferentes ($($versoesBrodoo -join ', '))"
      }
      else {
        $motivoBrodoo = if ($projetos.Count -eq 0) { "versao Odoo nao indicada (-Series)" }
                        else { "versao Odoo nao preenchida no Brodoo (projeto: $nomesProjetos)" }
      }

      if ($serieBrodoo) {
        $serie = $serieBrodoo
        $origemSerie = "Brodoo"
        if ($lido.Espelho -and $lido.Espelho -ne $serie) {
          $avisoEspelho = "o bloco do espelho no PG_CONTEXT.md diz $($lido.Espelho) e o Brodoo diz $serie; vale o Brodoo, porque o bloco nao e regenerado quando a versao muda"
        }
      }
      elseif ($lido.Espelho) {
        $serie = $lido.Espelho
        $origemSerie = "PG_CONTEXT.md, bloco do espelho ($motivoBrodoo)"
      }
      elseif ($lido.ConflitoEspelho) {
        $motivoSemSerie = "$motivoBrodoo; e o bloco do espelho no PG_CONTEXT.md tem versoes diferentes ($($lido.ConflitoEspelho))"
      }
      else { $motivoSemSerie = $motivoBrodoo }
    }
  }
  if (-not $odooAplicavel) {
    $serie = $null
    $origemSerie = $null
    $avisoEspelho = $null
    $motivoSemSerie = "projeto declarado sem Odoo (odoo_applicable: false)"
  }

  $edicao = $Edition
  if ($edicao -eq "auto" -and $edicoesBrodoo.Count -eq 1) { $edicao = $edicoesBrodoo[0] }

  $branchAlvo = if ($branchesBrodoo.Count -eq 1) { $branchesBrodoo[0] } else { "brodoo" }

  # --- 5. Source Odoo: ligar, adiar ou clonar --------------------------------------
  $modoSource = "nenhum"
  $raizSerie = $null
  if ($serie) {
    $raizSerie = Join-Path (Get-OdooSourceRoot) $serie
    $presente = Test-Path (Join-Segments $raizSerie @("community", ".git"))
    if ($edicao -eq "enterprise") { $presente = $presente -and (Test-Path (Join-Segments $raizSerie @("enterprise", ".git"))) }
    if ($presente) { $modoSource = "ligar" }
    elseif ($Hook) { $modoSource = "adiar" }
    else { $modoSource = "clonar" }
  }

  $semCommits = -not (Invoke-GitText -Arguments @("-C", $repo, "rev-parse", "--verify", "HEAD"))

  # O refresh dos templates a partir do Odoo passa pela cascata Python, que ainda cai na
  # chave partilhada do utilizador Brodoo. Com -SemBrodoo numa maquina sem chave pessoal,
  # era por ai que o bootstrap a usaria -- e cada uso adia a retirada dessa chave (o arbitro
  # e o login_date do utilizador de servico, PG-011 F5). No arranque nunca: so atrasa.
  $refreshTemplates = (-not $Hook) -and (Test-ChavePessoal)

  if ($WhatIf) {
    Say "$prefixo PLANO para '$repoName' ($repo)"
    Say "  projeto=$nomesProjetos"
    Say ("  serie={0} origem={1}" -f $(if ($serie) { $serie } else { "desconhecida" }), $(if ($origemSerie) { $origemSerie } else { $motivoSemSerie }))
    if ($avisoEspelho) { Say "  aviso=$avisoEspelho" }
    Say "  edicao=$edicao"
    Say ("  branch={0}{1}" -f $branchAlvo, $(if ($semCommits) { " (repositorio sem commits)" } else { "" }))
    Say "  source=$modoSource"
    Say ("  templates={0}" -f $(if ($refreshTemplates) { "odoo" } else { "copia versionada" }))
    exit 0
  }

  # --- 6. Branch Brodoo primeiro ---------------------------------------------------
  # Os ficheiros de framework pertencem a branch Brodoo (regra de commits). Bootstrapar
  # em main e depois mudar de branch deixa-os la, por rastrear, a espera de um commit errado.
  $logDir = if ($env:PG_AUTO_BOOTSTRAP_LOG_DIR) { $env:PG_AUTO_BOOTSTRAP_LOG_DIR } else { Join-Segments $HOME @(".pg", "logs") }
  if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
  $log = Join-Path $logDir ("auto_bootstrap_{0}_{1}.log" -f $repoName, (Get-Date -Format "yyyyMMdd_HHmmss"))

  # O mesmo script do passo 1 do ritual, tambem para um repositorio sem commits (clone de
  # um remoto vazio): uma so logica de escolha da branch, e nao duas a divergir.
  # Se o checkout falhar, o bootstrap NAO corre: e pre-condicao de todos os outros passos.
  # Processo proprio, como no ritual: no mesmo processo, o stderr do git (ex.: o fetch)
  # vira erro terminante debaixo do ErrorActionPreference=Stop do script.
  $checkout = Join-Path $PSScriptRoot "pg_checkout_brodoo_branch.ps1"
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $saidaCheckout = & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File $checkout -RepoPath $repo 2>&1
    $codigoCheckout = $LASTEXITCODE
  }
  finally { $ErrorActionPreference = $anterior }
  $textoCheckout = ($saidaCheckout | ForEach-Object { "$_" })
  $textoCheckout | Out-File -FilePath $log -Encoding utf8
  if ($codigoCheckout -ne 0) {
    throw ("o checkout da branch Brodoo falhou, e o bootstrap nao correu (os ficheiros de framework " +
      "so vao para a branch Brodoo). Ultimas linhas: " + (($textoCheckout | Select-Object -Last 4) -join " | ") + " -- log: $log")
  }

  # --- 7. Bootstrap ----------------------------------------------------------------

  $params = @{
    RepoName    = $repoName
    RepoPath    = $repo
    SkipGitInit = $true
    # No arranque, o refresh a partir do Odoo so atrasa: o sync leva a copia versionada.
    RefreshDocTemplatesFromOdoo = $refreshTemplates
    # `py` e o lancador do Python no Windows; no macOS nao existe.
    PythonExe   = $(if ($script:EmWindows) { "py" } else { "python3" })
  }
  if ($modoSource -in @("ligar", "clonar")) {
    $params["Series"] = $serie
    $params["Edition"] = $edicao
    if ($modoSource -eq "ligar") { $params["SkipOdooSourceFetch"] = $true }
  }

  $assistido = Join-Path $PSScriptRoot "pg_bootstrap_assisted.ps1"
  $falha = $null
  try {
    if ($Hook) { & $assistido @params *>&1 | ForEach-Object { "$_" } | Out-File -FilePath $log -Encoding utf8 -Append }
    else { & $assistido @params *>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append }
  }
  catch { $falha = $_.Exception.Message }

  # --- 8. O que o agente precisa de saber -----------------------------------------
  if ($falha) {
    Say "$prefixo o bootstrap de '$repoName' falhou: $falha"
    Say "  Detalhe em: $log"
    Say "  Parar e reportar ao utilizador antes de seguir com o ritual."
    exit 0
  }

  Say "$prefixo '$repoName' bootstrapado automaticamente (primeira sessao neste repositorio)."
  Say ("  Projeto Brodoo: {0} | Odoo {1} {2} (versao: {3}) | branch {4}" -f $nomesProjetos,
    $(if ($serie) { $serie } else { "?" }), $edicao,
    $(if ($origemSerie) { $origemSerie } else { "por confirmar" }), $branchAlvo)
  if ($script:LoginBrodoo) { Say "  Consulta ao Brodoo feita como: $($script:LoginBrodoo)" }
  if ($avisoEspelho) { Say "  Aviso: $avisoEspelho. Re-sincronizar o espelho do projeto para o corrigir." }
  switch ($modoSource) {
    "ligar"  { Say "  Source Odoo: vendor/odoo_src ligado a $raizSerie (sem fetch)." }
    "clonar" { Say "  Source Odoo: clonado em $raizSerie." }
    "adiar"  {
      Say "  Source Odoo: a serie $serie ainda nao existe nesta maquina (clone de varios GB); NAO foi feito."
      Say "  Correr em segundo plano e avisar o utilizador:"
      Say ('  {0} "{1}" -RepoName {2} -RepoPath "{3}" -Series {4} -Edition {5}' -f $script:PsComando, `
        (Join-Path $PSScriptRoot "pg_clone_odoo_source.ps1"), $repoName, $repo, $serie, $edicao)
    }
    default  {
      Say "  Source Odoo: NAO ligado -- $motivoSemSerie."
      if ($odooAplicavel) {
        # O repositorio ja esta bootstrapado: falta so o source, e e o clone que o traz.
        Say "  Pedir a versao ao utilizador (e preencher 'Odoo Version' no projeto do Brodoo); depois correr:"
        Say ('  {0} "{1}" -RepoName {2} -RepoPath "{3}" -Series <SERIE> -Edition {4}' -f $script:PsComando, `
          (Join-Path $PSScriptRoot "pg_clone_odoo_source.ps1"), $repoName, $repo, $(if ($edicao -eq "auto") { "<community|enterprise>" } else { $edicao }))
      }
    }
  }
  Say "  Log: $log"
  # Nesta sessao o CLAUDE.md acabado de criar ainda nao foi carregado, nem os hooks do
  # projeto: o agente so sabe do ritual pelo que ler agora.
  Say "  Primeira sessao: o CLAUDE.md e os hooks do projeto so contam a partir da proxima. Antes de responder,"
  Say "  ler AGENTS.md e .pg_framework/templates/AGENTS_SHARED.md e correr o ritual:"
  foreach ($passo in @("pg_checkout_brodoo_branch.ps1", "pg_ensure_framework_current.ps1", "pg_preflight_context.ps1")) {
    Say ('    {0} "{1}" -RepoPath "{2}"' -f $script:PsComando, (Join-Segments $repo @(".pg_framework", "scripts", $passo)), $repo)
  }
  exit 0
}
catch {
  Say "$prefixo nao concluiu: $($_.Exception.Message)"
  if ($Hook) { exit 0 }
  exit 1
}
