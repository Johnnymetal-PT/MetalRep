<#
.SYNOPSIS
  Testes deterministas de pg_align_fleet_framework.ps1.

.DESCRIPTION
  Monta uma frota falsa em pasta temporaria -- repositorios git reais, com remoto bare --
  e verifica as guardas que a operacao manual de 2026-08-24 mostrou serem necessarias:
  branch declarada, main recusada, commits alheios preservados, caminhos do publisher
  nunca em stage, e a corrida com o publisher resolvida por fetch e retentativa.

  Nao toca em nenhum repositorio real nem na rede.
#>
param(
  [switch]$KeepTemp
)

# O git escreve avisos (ex.: conversao CRLF) no stderr; com Stop cada aviso
# virava erro terminante e o teste morria antes da primeira verificacao.
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

function Initialize-RepoDeTeste {
  # autocrlf desligado para o git nao emitir avisos de conversao, e identidade fixa
  # para os commits nao dependerem da configuracao da maquina.
  param([string]$RepoPath)
  Invoke-GitQuiet -RepoPath $RepoPath -Arguments @('config', 'core.autocrlf', 'false')
  Invoke-GitQuiet -RepoPath $RepoPath -Arguments @('config', 'user.email', 'teste@parametro.global')
  Invoke-GitQuiet -RepoPath $RepoPath -Arguments @('config', 'user.name', 'Teste PG')
}

# ---------------------------------------------------------------------------
# Andaime
# ---------------------------------------------------------------------------

$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ("pg-align-test-" + [Guid]::NewGuid().ToString('N'))
$frota = Join-Path $raiz 'repos'
$remotos = Join-Path $raiz 'remotos'
New-Item -ItemType Directory -Path $frota -Force | Out-Null
New-Item -ItemType Directory -Path $remotos -Force | Out-Null

# O script deriva a raiz da frota como a pasta-mae do _pg_template, por isso o
# _pg_template de teste tem de viver dentro da frota falsa.
$templateFalso = Join-Path $frota '_pg_template'
$scriptsFalsos = Join-Path $templateFalso 'scripts'
New-Item -ItemType Directory -Path $scriptsFalsos -Force | Out-Null

$scriptsReais = $PSScriptRoot
Copy-Item (Join-Path $scriptsReais 'pg_align_fleet_framework.ps1') $scriptsFalsos -Force
Copy-Item (Join-Path $scriptsReais 'pg_file_io_common.ps1') $scriptsFalsos -Force

# Duplo do pg_sync_shared_assets.ps1: escreve um marcador deterministico em AGENTS.md
# e o estado de sync, como o real. Assim o teste nao depende do conteudo dos templates,
# mas depende do mesmo efeito observavel: depois de sincronizar, o repositorio declara
# a versao da framework com que ficou.
@'
param([string]$RepoName, [string]$RepoPath, [switch]$Force)
$ErrorActionPreference = "Stop"
$raizTemplate = Split-Path -Parent $PSScriptRoot
$destino = if ($RepoPath) { $RepoPath } else { Join-Path (Split-Path -Parent $raizTemplate) $RepoName }
Set-Content -Path (Join-Path $destino 'AGENTS.md') -Value "AGENTS sincronizado pelo duplo de teste" -Encoding utf8
$head = (& git -C $raizTemplate rev-parse HEAD 2>$null)
if ($head) {
  $pasta = Join-Path $destino '.pg'
  if (-not (Test-Path $pasta)) { New-Item -ItemType Directory -Path $pasta -Force | Out-Null }
  Set-Content -Path (Join-Path $pasta 'PG_TEMPLATE_SYNC_STATE.json') -Value ('{ "template_git_head": "' + $head.Trim() + '" }') -Encoding utf8
}
exit 0
'@ | Set-Content -Path (Join-Path $scriptsFalsos 'pg_sync_shared_assets.ps1') -Encoding utf8

Invoke-GitQuiet -RepoPath $templateFalso -Arguments @('init', '-b', 'main')
Initialize-RepoDeTeste -RepoPath $templateFalso
Set-Content -Path (Join-Path $templateFalso 'marca.txt') -Value 'framework' -Encoding utf8
Invoke-GitQuiet -RepoPath $templateFalso -Arguments @('add', '-A')
Invoke-GitQuiet -RepoPath $templateFalso -Arguments @('commit', '-m', 'framework')

function New-RepoFalso {
  param(
    [string]$Nome,
    [string]$BranchDeclarada,
    [switch]$SemDeclaracao,
    [switch]$SemLink
  )

  $remoto = Join-Path $remotos "$Nome.git"
  Invoke-GitQuiet -RepoPath $remotos -Arguments @('init', '--bare', "$Nome.git")

  $repo = Join-Path $frota $Nome
  New-Item -ItemType Directory -Path $repo -Force | Out-Null
  Invoke-GitQuiet -RepoPath $repo -Arguments @('init', '-b', $BranchDeclarada)
  Initialize-RepoDeTeste -RepoPath $repo
  Invoke-GitQuiet -RepoPath $repo -Arguments @('remote', 'add', 'origin', $remoto)

  # .pg_framework: o script exige a sua presenca para considerar o repo bootstrapado
  if (-not $SemLink) {
    New-Item -ItemType Directory -Path (Join-Path $repo '.pg_framework') -Force | Out-Null
    Set-Content -Path (Join-Path $repo '.pg_framework\marca.txt') -Value 'link' -Encoding utf8
  }

  $projectDir = Join-Path $repo ".pg\projects\proj-teste\project"
  New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
  if (-not $SemDeclaracao) {
    $json = '{ "project": { "repository_branch": "' + $BranchDeclarada + '" } }'
    Set-Content -Path (Join-Path $projectDir 'project.json') -Value $json -Encoding utf8
  }

  Set-Content -Path (Join-Path $repo 'AGENTS.md') -Value 'AGENTS antigo' -Encoding utf8
  Set-Content -Path (Join-Path $repo 'modulo_do_projeto.py') -Value '# codigo do projeto' -Encoding utf8
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg\projects\proj-teste') -Force | Out-Null
  Set-Content -Path (Join-Path $repo '.pg\projects\proj-teste\PG_SCOPE_SYNC.json') -Value '{"v":1}' -Encoding utf8

  Invoke-GitQuiet -RepoPath $repo -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('commit', '-m', 'inicial')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('push', '-u', 'origin', $BranchDeclarada)
  return $repo
}

function Invoke-Alinhador {
  # Devolve o texto E o relatorio JSON. As verificacoes usam o JSON: a consola do
  # processo-filho quebra linhas longas, e asserçoes por texto falhavam por isso.
  param([string[]]$ArgumentosExtra)

  $script = Join-Path $scriptsFalsos 'pg_align_fleet_framework.ps1'
  $relatorio = Join-Path $raiz ("relatorio-" + [Guid]::NewGuid().ToString('N') + ".json")
  $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -ReposRoot $frota -ReportPath $relatorio @ArgumentosExtra 2>&1
  $json = $null
  if (Test-Path $relatorio) { $json = Get-Content $relatorio -Raw | ConvertFrom-Json }
  return [pscustomobject]@{
    Texto     = (($saida | ForEach-Object { "$_" }) -join "`n")
    Relatorio = $json
    Caminho   = $relatorio
  }
}

function Get-EstadoDoRepo {
  param($Relatorio, [string]$Nome)
  $linha = $Relatorio.repos | Where-Object { $_.repo -eq $Nome }
  if (-not $linha) { return '(ausente do relatorio)' }
  return $linha.status
}

try {
  Write-Host "=== andaime em $raiz ==="

  $ok = New-RepoFalso -Nome 'RepoBrodoo' -BranchDeclarada 'brodoo'
  $emMain = New-RepoFalso -Nome 'RepoMain' -BranchDeclarada 'main'
  $semDecl = New-RepoFalso -Nome 'RepoSemDeclaracao' -BranchDeclarada 'brodoo' -SemDeclaracao
  $comAlheio = New-RepoFalso -Nome 'RepoComTrabalhoAlheio' -BranchDeclarada 'brodoo'

  # commit local nao publicado, fora do ambito da framework
  Set-Content -Path (Join-Path $comAlheio 'modulo_do_projeto.py') -Value '# alteracao nao publicada' -Encoding utf8
  Invoke-GitQuiet -RepoPath $comAlheio -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $comAlheio -Arguments @('commit', '-m', 'trabalho de outra pessoa')

  # Divergente: tem commit local alheio E o remoto andou para a frente entretanto.
  # E o caso do Evostone (43 a frente, 272 atras): um push e RECUSADO pelo git, e
  # dizer "publicar ou rever" manda a pessoa fazer o que nao e possivel fazer.
  #
  # Montagem sem segundo clone: publica-se um commit, recua-se o local para o deixar
  # atras, e so entao se cria o commit local. Resultado: 1 a frente, 1 atras.
  $divergente = New-RepoFalso -Nome 'RepoDivergente' -BranchDeclarada 'brodoo'
  Set-Content -Path (Join-Path $divergente 'outro_ficheiro.py') -Value '# publicado por outra maquina' -Encoding utf8
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('commit', '-m', 'trabalho publicado por outra maquina')
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('push', 'origin', 'brodoo')
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('reset', '--hard', 'HEAD~1')
  Set-Content -Path (Join-Path $divergente 'modulo_do_projeto.py') -Value '# local alheio' -Encoding utf8
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $divergente -Arguments @('commit', '-m', 'trabalho local de outra pessoa')


  # Repositorio de produto: tem .pg/ mas nao e projeto de cliente, e declara-o. E o caso
  # do parametro-odoo/Parametro_Global, onde vive o pg_brodoo. Antes aparecia na lista de
  # nao-alinhados como "branch Brodoo nao declarada", ao lado de defeitos a serio.
  $produto = New-RepoFalso -Nome 'RepoProduto' -BranchDeclarada 'brodoo' -SemDeclaracao
  Set-Content -Encoding utf8 -Path (Join-Path $produto '.pg\PROJECT_PROFILE.json') -Value (
    '{ "schema_version": "1.1", "brodoo_mirror_applicable": false, "reason": "repositorio do addon pg_brodoo" }')

  # Perfil que NAO dispensa: um ficheiro presente nao pode, por si, tirar um repo da frota.
  $perfilQueNaoDispensa = New-RepoFalso -Nome 'RepoPerfilNormal' -BranchDeclarada 'brodoo' -SemDeclaracao
  Set-Content -Encoding utf8 -Path (Join-Path $perfilQueNaoDispensa '.pg\PROJECT_PROFILE.json') -Value (
    '{ "schema_version": "1.0", "erp": "primavera", "odoo_applicable": false }')

  # Perfil ilegivel: um gate nao se desliga por um ficheiro partido.
  $perfilPartido = New-RepoFalso -Nome 'RepoPerfilPartido' -BranchDeclarada 'brodoo' -SemDeclaracao
  Set-Content -Encoding utf8 -Path (Join-Path $perfilPartido '.pg\PROJECT_PROFILE.json') -Value '{ isto nao e json'

  # Declara 'main' no espelho local, mas o remoto ja tem 'brodoo': o clone e que esta
  # velho. Antes, isto era reportado como declaracao errada no Odoo.
  $mainDesatualizado = New-RepoFalso -Nome 'RepoMainDesatualizado' -BranchDeclarada 'main'
  Invoke-GitQuiet -RepoPath $mainDesatualizado -Arguments @('push', 'origin', 'main:brodoo')

  # Elegivel (tem .pg/) mas sem o link: antes desaparecia da auditoria em silencio.
  $semLink = New-RepoFalso -Nome 'RepoSemLink' -BranchDeclarada 'brodoo' -SemLink

  # Pasta que nao e elegivel de todo: continua a nao ser da conta do alinhador.
  $naoElegivel = Join-Path $frota 'PastaQualquer'
  New-Item -ItemType Directory -Path $naoElegivel -Force | Out-Null
  Invoke-GitQuiet -RepoPath $naoElegivel -Arguments @('init', '-b', 'main')
  Initialize-RepoDeTeste -RepoPath $naoElegivel
  Set-Content -Path (Join-Path $naoElegivel 'leiame.txt') -Value 'nada a ver com a frota' -Encoding utf8
  Invoke-GitQuiet -RepoPath $naoElegivel -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $naoElegivel -Arguments @('commit', '-m', 'inicial')

  Write-Host ""
  Write-Host "--- auditoria (sem -Apply) nao escreve nada ---"
  $antesOk = & git -C $ok rev-parse HEAD
  $r = Invoke-Alinhador
  Assert-Equal 'audit' $r.Relatorio.mode 'o relatorio declara o modo auditoria'
  Assert-Equal 'alinharia' (Get-EstadoDoRepo $r.Relatorio 'RepoBrodoo') 'RepoBrodoo aparece como alinhavel'
  Assert-Equal $antesOk (& git -C $ok rev-parse HEAD) 'auditoria nao cria commits'

  Write-Host ""
  Write-Host "--- 'main' declarada: distinguir clone velho de declaracao errada ---"
  $linhaMain = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoMain' }
  Assert-Equal 'saltado' $linhaMain.status 'declaracao main sem origin/brodoo continua a ser saltada'
  Assert-True ($linhaMain.reason -like '*migrar a declaracao no Odoo*') 'sem origin/brodoo, a remediacao e mesmo no Odoo'

  $linhaVelha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoMainDesatualizado' }
  Assert-Equal 'saltado' $linhaVelha.status 'clone desatualizado continua a nao ser alinhado'
  Assert-True ($linhaVelha.reason -like '*clone esta desatualizado*') 'com origin/brodoo no remoto, a causa e o clone e nao a declaracao'
  Assert-True ($linhaVelha.reason -notlike '*migrar a declaracao no Odoo*') 'nao mandar corrigir o Odoo quando o Odoo esta certo'

  Write-Host ""
  Write-Host "--- repositorio elegivel sem .pg_framework nao desaparece ---"
  Assert-Equal 'sem_framework' (Get-EstadoDoRepo $r.Relatorio 'RepoSemLink') 'repo elegivel sem link tem de aparecer no relatorio, e nao ser saltado em silencio'
  $linhaSemLink = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoSemLink' }
  Assert-True ($linhaSemLink.reason -like '*pg_link_framework*') 'a razao tem de trazer a remediacao'
  Assert-Equal '(ausente do relatorio)' (Get-EstadoDoRepo $r.Relatorio 'PastaQualquer') 'uma pasta que nao e elegivel continua fora do relatorio'
  Assert-True ($r.Texto -like '*sem link*') 'o cabecalho anuncia quantos estao fora do perimetro'

  Write-Host ""
  Write-Host "--- -RepoNames que nao resolve nada e erro, nao silencio ---"
  $inexistente = Invoke-Alinhador -ArgumentosExtra @('-RepoNames', 'RepoQueNaoExiste')
  Assert-True ($inexistente.Texto -like '*ERRO: nenhum dos repositorios pedidos*') 'um -RepoNames que nao resolve nada tem de dar erro; sair com 0 e sem relatorio le-se como sucesso'
  Assert-True ($null -eq $inexistente.Relatorio) 'sem repositorios nao ha relatorio a escrever'

  Write-Host ""
  Write-Host "--- a auditoria diz em que versao esta a frota ---"
  # Nenhum dos repos de teste tem PG_TEMPLATE_SYNC_STATE.json, logo nenhum esta na versao.
  Assert-Equal 0 $r.Relatorio.repos_na_versao 'sem estado de sync, nenhum repo conta como estando na versao corrente'
  Assert-True ($r.Relatorio.repos_total -gt 0) 'o relatorio conta o universo de repositorios'

  # Com o estado de sync a apontar para o HEAD do framework de teste, passa a contar.
  $headFramework = (& git -C $templateFalso rev-parse HEAD).Trim()
  $estadoSync = Join-Path $ok '.pg\PG_TEMPLATE_SYNC_STATE.json'
  Set-Content -Path $estadoSync -Value ('{ "template_git_head": "' + $headFramework + '" }') -Encoding utf8
  $rVersao = Invoke-Alinhador
  Assert-Equal 1 $rVersao.Relatorio.repos_na_versao 'um repo sincronizado com o HEAD do framework conta como estando na versao corrente'
  Assert-True ($rVersao.Texto -like '*na versao corrente*') 'o resumo anuncia a cobertura de versao da frota'
  Remove-Item -LiteralPath $estadoSync -Force

  Write-Host ""
  Write-Host "--- guardas ---"
  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoMain') 'recusa branch declarada main'
  Assert-True ((($r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoMain' }).reason -match 'producao do cliente')) 'a razao do RepoMain nomeia a producao do cliente'
  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoSemDeclaracao') 'recusa repo sem branch declarada'
  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoComTrabalhoAlheio') 'recusa repo com commit alheio nao publicado'
  Assert-True ((($r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoComTrabalhoAlheio' }).reason -match '1 commit')) 'a razao conta o commit alheio'
  $razaoSoFrente = ($r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoComTrabalhoAlheio' }).reason
  Assert-True ($razaoSoFrente -like '*publicar ou rever*') 'so a frente: a accao possivel e publicar'
  Assert-True ($razaoSoFrente -notlike '*DIVERGENTE*') 'so a frente nao pode ser reportado como divergente'

  # Divergente: o texto tem de dizer que um push seria recusado, senao manda fazer o
  # impossivel. Foi este o texto que produziu um diagnostico errado a 2026-09-11.
  # --- fora do perimetro por declaracao explicita -------------------------
  Assert-Equal 'fora_do_perimetro' (Get-EstadoDoRepo $r.Relatorio 'RepoProduto') 'repo de produto declarado sai do perimetro'
  $razaoProduto = ($r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoProduto' }).reason
  Assert-True ($razaoProduto -like '*pg_brodoo*') 'a razao declarada pelo repo tem de aparecer, para a decisao ser auditavel'
  Assert-True ($r.Texto -notmatch 'RepoProduto\s+SALTADO') 'um repo fora do perimetro nao pode aparecer como saltado'

  # o que dispensa e a chave, nao a existencia do ficheiro
  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoPerfilNormal') 'PROJECT_PROFILE sem a chave nao tira o repo da frota'
  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoPerfilPartido') 'perfil ilegivel nao dispensa nada'

  Assert-Equal 'saltado' (Get-EstadoDoRepo $r.Relatorio 'RepoDivergente') 'repo divergente tambem e saltado'
  $razaoDiv = ($r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoDivergente' }).reason
  Assert-True ($razaoDiv -like '*DIVERGENTE*') 'a divergencia tem de ser nomeada, nao escondida em "nao publicados"'
  Assert-True ($razaoDiv -match 'por integrar') 'a razao tem de contar tambem os commits da origin que faltam'
  Assert-True ($razaoDiv -like '*reconciliar*') 'a remediacao de um divergente e reconciliar, nao publicar'
  Assert-True ($razaoDiv -notlike '*publicar ou rever*') 'nao mandar publicar quando o push seria recusado'

  Write-Host ""
  Write-Host "--- apply: alinha e publica ---"
  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply')
  Assert-Equal 'publicado' (Get-EstadoDoRepo $r.Relatorio 'RepoBrodoo') 'RepoBrodoo publicado'

  # O resumo tem de contar o estado DEPOIS do sync. Lido antes, anunciava zero
  # imediatamente a seguir a alinhar com sucesso.
  Assert-True ($r.Relatorio.repos_na_versao -gt 0) 'depois de alinhar, a cobertura de versao nao pode continuar a zero'
  $linhaAlinhada = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoBrodoo' }
  Assert-True ([bool]$linhaAlinhada.synced_current) 'o repositorio acabado de sincronizar tem de ficar marcado como estando na versao'

  $conteudoRemoto = (& git -C $ok show 'origin/brodoo:AGENTS.md') -join "`n"
  Assert-Equal 'AGENTS sincronizado pelo duplo de teste' $conteudoRemoto.Trim() 'o remoto recebeu o AGENTS.md sincronizado'

  # o commit alheio continua local e intacto
  $alheioAindaLocal = @(& git -C $comAlheio rev-list 'origin/brodoo..HEAD').Count
  Assert-Equal 1 $alheioAindaLocal 'o commit alheio continua nao publicado'

  Write-Host ""
  Write-Host "--- nunca faz stage de caminhos do publisher ---"
  $publisher = New-RepoFalso -Nome 'RepoPublisher' -BranchDeclarada 'brodoo'
  Set-Content -Path (Join-Path $publisher '.pg\projects\proj-teste\PG_SCOPE_SYNC.json') -Value '{"v":2}' -Encoding utf8
  Set-Content -Path (Join-Path $publisher 'PG_CONTEXT.md') -Value 'contexto local' -Encoding utf8
  Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoPublisher') | Out-Null
  $ficheirosDoCommit = @(& git -C $publisher show --name-only --format= HEAD)
  Assert-True (-not ($ficheirosDoCommit -match '^\.pg/projects/')) 'o commit nao inclui .pg/projects/**'
  Assert-True (-not ($ficheirosDoCommit -match '^PG_CONTEXT\.md$')) 'o commit nao inclui PG_CONTEXT.md'
  $sujoDepois = @(& git -C $publisher status --porcelain) -join "`n"
  Assert-True ($sujoDepois -match 'PG_SCOPE_SYNC\.json') 'a alteracao do publisher fica por commitar, intacta'

  Write-Host ""
  Write-Host "--- corrida com o publisher: fetch e retentativa ---"
  $corrida = New-RepoFalso -Nome 'RepoCorrida' -BranchDeclarada 'brodoo'
  # simular o publisher a escrever no remoto depois do ultimo fetch local
  $clonePublisher = Join-Path $raiz 'clone-publisher'
  # -b e obrigatorio: o remoto bare foi criado com `git init --bare`, cujo HEAD aponta
  # para master/main, e a branch publicada e 'brodoo'. Sem -b, o clone sai vazio.
  & git clone -b 'brodoo' (Join-Path $remotos 'RepoCorrida.git') $clonePublisher *> $null
  Initialize-RepoDeTeste -RepoPath $clonePublisher
  Set-Content -Path (Join-Path $clonePublisher '.pg\projects\proj-teste\PG_SCOPE_SYNC.json') -Value '{"publisher":true}' -Encoding utf8
  Invoke-GitQuiet -RepoPath $clonePublisher -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $clonePublisher -Arguments @('commit', '-m', 'chore(pg-sync): refresh')
  Invoke-GitQuiet -RepoPath $clonePublisher -Arguments @('push', 'origin', 'brodoo')

  Assert-True (Test-Path (Join-Path $clonePublisher '.pg')) 'o clone do publisher tem o espelho'
  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoCorrida')
  Assert-Equal 'publicado' (Get-EstadoDoRepo $r.Relatorio 'RepoCorrida') 'publica apesar de o remoto ter avancado'
  $publisherPreservado = (& git -C $corrida show 'origin/brodoo:.pg/projects/proj-teste/PG_SCOPE_SYNC.json') -join ''
  Assert-True ($publisherPreservado -match 'publisher') 'o commit do publisher sobreviveu ao alinhamento'

  Write-Host ""
  Write-Host "--- caminho com acentos nao e confundido com trabalho alheio ---"
  $acentos = New-RepoFalso -Nome 'RepoAcentos' -BranchDeclarada 'brodoo'
  $assets = Join-Path $acentos 'doc_templatesssets'
  New-Item -ItemType Directory -Path $assets -Force | Out-Null
  # o git cita caminhos com bytes nao-ASCII; sem core.quotepath=false a aspa inicial
  # rebenta a ancora ^doc_templates/ e o ficheiro conta como fora do ambito
  Set-Content -Path (Join-Path $assets 'Nao confirmado 93645.crdownload') -Value 'x' -Encoding utf8
  Set-Content -Path (Join-Path $assets ([char]0x4E + [char]0xE3 + [char]0x6F + ' confirmado 93645.crdownload')) -Value 'x' -Encoding utf8
  Invoke-GitQuiet -RepoPath $acentos -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $acentos -Arguments @('commit', '-m', 'chore(framework): anexo com acentos')
  $r = Invoke-Alinhador -ArgumentosExtra @('-RepoNames', 'RepoAcentos')
  Assert-Equal 'alinharia' (Get-EstadoDoRepo $r.Relatorio 'RepoAcentos') 'commit com caminho acentuado conta como framework'

  Write-Host ""
  Write-Host "--- merge recusado pelo git nao vira push condenado ---"
  # Um merge que o git RECUSA nao produz conflitos: aborta antes de comecar. Sem verificar
  # o codigo de saida, o alinhador seguia, commitava e tentava publicar uma branch que
  # continuava atras -- e cada retentativa juntava um commit redundante.
  $recusa = New-RepoFalso -Nome 'RepoMergeRecusado' -BranchDeclarada 'brodoo'
  $clonePush = Join-Path $raiz 'clone-recusa'
  & git clone -b 'brodoo' (Join-Path $remotos 'RepoMergeRecusado.git') $clonePush *> $null
  Initialize-RepoDeTeste -RepoPath $clonePush
  # o remoto muda um ficheiro do PROJETO (fora do ambito da framework)
  Set-Content -Path (Join-Path $clonePush 'modulo_do_projeto.py') -Value '# versao do remoto' -Encoding utf8
  Invoke-GitQuiet -RepoPath $clonePush -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $clonePush -Arguments @('commit', '-m', 'alteracao no remoto')
  Invoke-GitQuiet -RepoPath $clonePush -Arguments @('push', 'origin', 'brodoo')
  # localmente o mesmo ficheiro esta modificado e por commitar: o merge tem de ser recusado
  Set-Content -Path (Join-Path $recusa 'modulo_do_projeto.py') -Value '# versao local por commitar' -Encoding utf8

  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoMergeRecusado')
  $linha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoMergeRecusado' }
  Assert-Equal 'merge_recusado' $linha.status 'merge recusado e reportado como tal'
  Assert-Equal 1 $linha.attempts 'nao retenta um merge recusado'
  $locais = @(& git -C $recusa rev-list 'origin/brodoo..HEAD').Count
  Assert-Equal 0 $locais 'nao deixa commits redundantes para tras'
  $conteudoLocal = (Get-Content (Join-Path $recusa 'modulo_do_projeto.py') -Raw).Trim()
  Assert-Equal '# versao local por commitar' $conteudoLocal 'a alteracao local fica intacta'

  Write-Host ""
  Write-Host "--- avisos do git no stderr nao contam como conflito ---"
  # Com autocrlf ligado o git emite "warning: ... CRLF will be replaced ..." no stderr.
  # Misturado com o stdout, esse aviso entrava na lista de conflitos e era classificado
  # como caminho fora do ambito da framework.
  $ruido = New-RepoFalso -Nome 'RepoRuidoStderr' -BranchDeclarada 'brodoo'
  Invoke-GitQuiet -RepoPath $ruido -Arguments @('config', 'core.autocrlf', 'true')
  $comCrlf = "linha um`r`nlinha dois`r`n"
  New-Item -ItemType Directory -Path (Join-Path $ruido 'doc_templates') -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $ruido 'doc_templates\ficheiro_crlf.md'), $comCrlf)
  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoRuidoStderr')
  $linha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoRuidoStderr' }
  Assert-Equal 'publicado' $linha.status 'aviso de CRLF nao impede o alinhamento'

  Write-Host ""
  Write-Host "--- estado local versionado nao bloqueia o merge ---"
  # O .pg/PREFLIGHT.json e regenerado a cada arranque. Seguido no indice, modificado
  # localmente e tambem alterado pelos commits a entrar, faz o git RECUSAR o merge.
  # A v2.21.1 pos o desversionamento no sync, que corre DEPOIS do merge -- nunca
  # desbloqueava nada. Tem de acontecer antes.
  $estado = New-RepoFalso -Nome 'RepoEstadoLocal' -BranchDeclarada 'brodoo'
  Set-Content -Path (Join-Path $estado '.pg\PREFLIGHT.json') -Value '{"origem":"local"}' -Encoding utf8
  Invoke-GitQuiet -RepoPath $estado -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $estado -Arguments @('commit', '-m', 'chore(framework): preflight versionado')
  Invoke-GitQuiet -RepoPath $estado -Arguments @('push', 'origin', 'brodoo')

  $clonePf = Join-Path $raiz 'clone-preflight'
  & git clone -b 'brodoo' (Join-Path $remotos 'RepoEstadoLocal.git') $clonePf *> $null
  Initialize-RepoDeTeste -RepoPath $clonePf
  Set-Content -Path (Join-Path $clonePf '.pg\PREFLIGHT.json') -Value '{"origem":"outra maquina"}' -Encoding utf8
  Invoke-GitQuiet -RepoPath $clonePf -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $clonePf -Arguments @('commit', '-m', 'preflight de outra maquina')
  Invoke-GitQuiet -RepoPath $clonePf -Arguments @('push', 'origin', 'brodoo')

  # e localmente o mesmo ficheiro esta modificado e por commitar
  Set-Content -Path (Join-Path $estado '.pg\PREFLIGHT.json') -Value '{"origem":"esta maquina, por commitar"}' -Encoding utf8

  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoEstadoLocal')
  $linha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoEstadoLocal' }
  Assert-Equal 'publicado' $linha.status 'estado local versionado nao impede o alinhamento'
  $aindaSeguido = @(& git -C $estado ls-files '.pg/PREFLIGHT.json').Count
  Assert-Equal 0 $aindaSeguido 'o PREFLIGHT.json saiu do indice'
  # o alinhador tira-o tambem do disco: fica regenerado no arranque seguinte pelo
  # preflight, e um ficheiro nao seguido bloquearia o merge da mesma forma
  Assert-True (-not (Test-Path (Join-Path $estado '.pg\PREFLIGHT.json'))) 'e saiu do disco, para nao bloquear o merge'

  Write-Host ""
  Write-Host "--- conflito so em ficheiros de framework resolve-se ---"
  # O conteudo dos ficheiros de framework nao se negocia entre lados: e regenerado a
  # partir do template pelo sync. Abortar aqui deixava o repositorio eternamente preso.
  $conf = New-RepoFalso -Nome 'RepoConflitoFramework' -BranchDeclarada 'brodoo'
  $cloneConf = Join-Path $raiz 'clone-conflito'
  & git clone -b 'brodoo' (Join-Path $remotos 'RepoConflitoFramework.git') $cloneConf *> $null
  Initialize-RepoDeTeste -RepoPath $cloneConf
  Set-Content -Path (Join-Path $cloneConf 'AGENTS.md') -Value 'AGENTS na versao do remoto' -Encoding utf8
  Invoke-GitQuiet -RepoPath $cloneConf -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $cloneConf -Arguments @('commit', '-m', 'AGENTS mudado no remoto')
  Invoke-GitQuiet -RepoPath $cloneConf -Arguments @('push', 'origin', 'brodoo')
  # o mesmo ficheiro, mudado de forma diferente e commitado localmente: conflito garantido
  Set-Content -Path (Join-Path $conf 'AGENTS.md') -Value 'AGENTS na versao local divergente' -Encoding utf8
  Invoke-GitQuiet -RepoPath $conf -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $conf -Arguments @('commit', '-m', 'chore(framework): AGENTS local')

  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoConflitoFramework')
  $linha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoConflitoFramework' }
  Assert-Equal 'publicado' $linha.status 'conflito de framework nao impede o alinhamento'
  Assert-True ($linha.resolved_conflicts -ge 1) 'o relatorio conta os conflitos resolvidos'
  $noRemoto = (& git -C $conf show 'origin/brodoo:AGENTS.md') -join "`n"
  Assert-Equal 'AGENTS sincronizado pelo duplo de teste' $noRemoto.Trim() 'o sync regenerou o conteudo, nao ficou nenhum dos dois lados'

  Write-Host ""
  Write-Host "--- a recusa do merge nomeia os ficheiros ---"
  $recusa2 = New-RepoFalso -Nome 'RepoRecusaDetalhada' -BranchDeclarada 'brodoo'
  $cloneR2 = Join-Path $raiz 'clone-recusa2'
  & git clone -b 'brodoo' (Join-Path $remotos 'RepoRecusaDetalhada.git') $cloneR2 *> $null
  Initialize-RepoDeTeste -RepoPath $cloneR2
  Set-Content -Path (Join-Path $cloneR2 'modulo_do_projeto.py') -Value '# remoto' -Encoding utf8
  Invoke-GitQuiet -RepoPath $cloneR2 -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $cloneR2 -Arguments @('commit', '-m', 'projeto mudado no remoto')
  Invoke-GitQuiet -RepoPath $cloneR2 -Arguments @('push', 'origin', 'brodoo')
  Set-Content -Path (Join-Path $recusa2 'modulo_do_projeto.py') -Value '# local por commitar' -Encoding utf8

  $r = Invoke-Alinhador -ArgumentosExtra @('-Apply', '-RepoNames', 'RepoRecusaDetalhada')
  $linha = $r.Relatorio.repos | Where-Object { $_.repo -eq 'RepoRecusaDetalhada' }
  Assert-Equal 'merge_recusado' $linha.status 'recusa reportada'
  Assert-True ($linha.reason -match 'modulo_do_projeto\.py') 'a razao nomeia o ficheiro que bloqueia'

  Write-Host ""
  Write-Host "--- relatorio JSON ---"
  $r = Invoke-Alinhador
  Assert-True (Test-Path $r.Caminho) 'escreve o relatorio'
  Assert-True ($r.Relatorio.repos.Count -ge 4) 'o relatorio cobre a frota'
  Assert-True (-not [string]::IsNullOrWhiteSpace($r.Relatorio.framework_head)) 'o relatorio registra a versao da framework'

  Write-Host ""
  if ($script:Falhas -eq 0) {
    Write-Host "OK: $($script:Total) verificacoes passaram."
  }
  else {
    Write-Host "ERRO: $($script:Falhas) de $($script:Total) verificacoes falharam."
  }
}
catch {
  # Sem isto, um erro no andaime era engolido pelo finally e o teste saia com 0 --
  # o resumo simplesmente nao aparecia, o que e pior do que falhar.
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
