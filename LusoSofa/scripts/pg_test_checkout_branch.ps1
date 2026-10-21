<#
.SYNOPSIS
  Testes da resolucao da branch Brodoo no ritual (pg_checkout_brodoo_branch.ps1).

.DESCRIPTION
  Ate 2026-09-11 o script tinha `$targetBranch = 'brodoo'` fixo e so consultava o
  project.json quando 'brodoo' NAO existia. `FACTO OBSERVADO` (givachoice): o projeto
  declara `audit`, a `brodoo` existia como linhagem antiga, e o ritual levava a sessao
  para uma branch com 1698 commits de divergencia, sem os dados do projeto e com outra
  arvore de addons -- produzindo pelo menos uma conclusao factual errada (06/08/2026).

  Acresce que `Select-Object -First 1` sobre .pg/projects escolhia a declaracao ao acaso
  em repositorios multi-projeto.

  Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achado D2.
#>
param()

$ErrorActionPreference = 'Stop'

$script:Total = 0

function Assert-Equal {
  param([string]$Esperado, [string]$Obtido, [string]$Message)
  $script:Total += 1
  if ($Esperado -ne $Obtido) { throw "FALHA: $Message (esperado '$Esperado', obtido '$Obtido')" }
  Write-Host "  OK   $Message"
}

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:Total += 1
  if (-not $Condition) { throw "FALHA: $Message" }
  Write-Host "  OK   $Message"
}

function Invoke-GitQuiet {
  param([string]$RepoPath, [string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & git -C $RepoPath @Arguments 2>&1 | Out-Null } finally { $ErrorActionPreference = $anterior }
}

function New-RepoDeTeste {
  # Repositorio local com as branches pedidas e as declaracoes pedidas.
  param(
    [string]$Nome,
    [string[]]$Branches,
    [hashtable]$Declaracoes,   # chave = nome do projeto namespaced, valor = repository_branch
    [string]$DeclaracaoLegacy,
    [string]$BranchFinal
  )

  $repo = Join-Path $raiz $Nome
  New-Item -ItemType Directory -Path $repo -Force | Out-Null
  Invoke-GitQuiet -RepoPath $repo -Arguments @('init', '-b', 'base')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'user.email', 'teste@parametro.global')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'user.name', 'Teste PG')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('config', 'core.autocrlf', 'false')

  if ($Declaracoes) {
    foreach ($chave in $Declaracoes.Keys) {
      $dir = Join-Path $repo ".pg\projects\$chave\project"
      New-Item -ItemType Directory -Path $dir -Force | Out-Null
      Set-Content -Path (Join-Path $dir 'project.json') -Encoding utf8 `
        -Value ('{ "project": { "repository_branch": "' + $Declaracoes[$chave] + '" } }')
    }
  }
  if ($DeclaracaoLegacy) {
    $dir = Join-Path $repo ".pg\project"
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Set-Content -Path (Join-Path $dir 'project.json') -Encoding utf8 `
      -Value ('{ "project": { "repository_branch": "' + $DeclaracaoLegacy + '" } }')
  }

  Set-Content -Path (Join-Path $repo 'leiame.txt') -Value 'conteudo' -Encoding utf8
  Invoke-GitQuiet -RepoPath $repo -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $repo -Arguments @('commit', '-m', 'inicial')

  foreach ($b in $Branches) { Invoke-GitQuiet -RepoPath $repo -Arguments @('branch', $b) }
  if ($BranchFinal) { Invoke-GitQuiet -RepoPath $repo -Arguments @('checkout', $BranchFinal) }

  return $repo
}

function Invoke-Checkout {
  param([string]$RepoPath)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -RepoPath $RepoPath 2>&1
    $codigo = $LASTEXITCODE
  }
  finally { $ErrorActionPreference = $anterior }
  return [pscustomobject]@{
    Texto  = (($saida | ForEach-Object { "$_" }) -join "`n")
    Exit   = $codigo
    Branch = (& git -C $RepoPath rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
  }
}

$script = Join-Path $PSScriptRoot 'pg_checkout_brodoo_branch.ps1'
$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ('pg-checkout-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $raiz -Force | Out-Null

try {
  Write-Host "=== resolucao da branch Brodoo ==="

  # --- A declaracao manda, mesmo com 'brodoo' a existir ---------------------
  # E o caso do givachoice, e a razao de este ficheiro existir.
  $r = New-RepoDeTeste -Nome 'declara_audit' -Branches @('brodoo', 'audit') `
    -Declaracoes @{ 'proj-fase-3' = 'audit' } -BranchFinal 'audit'
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'audit' $res.Branch 'com brodoo a existir, a branch declarada continua a mandar'
  Assert-True ($res.Texto -like '*declarada pelo projeto*') 'a saida diz que a branch veio da declaracao'

  # --- Sem declaracao, vale o standard --------------------------------------
  $r = New-RepoDeTeste -Nome 'sem_declaracao' -Branches @('brodoo') -BranchFinal 'base'
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'brodoo' $res.Branch 'sem declaracao, o standard brodoo aplica-se'

  # --- Declaracao a apontar para producao e recusada ------------------------
  $r = New-RepoDeTeste -Nome 'declara_main' -Branches @('brodoo', 'main') `
    -Declaracoes @{ 'proj' = 'main' } -BranchFinal 'base'
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'brodoo' $res.Branch 'declaracao a apontar para main nao e obedecida'
  Assert-True ($res.Texto -like '*producao do cliente*') 'a recusa diz porque'

  # --- Checkout bloqueado por ficheiro nao rastreado: a razao tem de aparecer ---
  # No ancoravip (2026-09-11) o checkout falhava com "Nao foi possivel ficar na branch"
  # e mais nada. A razao do git -- dois ficheiros nao rastreados que seriam sobrescritos,
  # identicos byte a byte aos ja versionados -- ia toda para Out-Null. Sem ela, ninguem
  # sabe o que fazer a seguir.
  $r = New-RepoDeTeste -Nome 'bloqueado_untracked' -Branches @('brodoo') -BranchFinal 'base'
  # ficheiro que existe versionado em 'brodoo' mas nao na branch actual
  Invoke-GitQuiet -RepoPath $r -Arguments @('checkout', 'brodoo')
  Set-Content -Path (Join-Path $r 'so_na_brodoo.md') -Value 'versionado na brodoo' -Encoding utf8
  Invoke-GitQuiet -RepoPath $r -Arguments @('add', '-A')
  Invoke-GitQuiet -RepoPath $r -Arguments @('commit', '-m', 'ficheiro so na brodoo')
  Invoke-GitQuiet -RepoPath $r -Arguments @('checkout', 'base')
  # e agora o mesmo nome, nao rastreado, na branch actual -> o checkout tem de recusar
  Set-Content -Path (Join-Path $r 'so_na_brodoo.md') -Value 'copia local nao rastreada' -Encoding utf8
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'base' $res.Branch 'com untracked a bloquear, o checkout nao acontece'
  Assert-True ($res.Texto -match 'untracked working tree files') 'a razao do git tem de chegar a quem le'
  Assert-True ($res.Texto -like '*so_na_brodoo.md*') 'a mensagem tem de nomear o ficheiro que bloqueia'
  Assert-True ($res.Texto -like '*hash-object*') 'a remediacao diz como comparar antes de apagar'

  # --- O aviso de 'main' nao pode afirmar que o Odoo esta errado -------------
  # A declaracao lida vem do espelho LOCAL, que pode estar velho. No ancoravip o Odoo ja
  # declarava 'brodoo' e o aviso mandava corrigir o Odoo -- procurar um erro que nao existe.
  $r = New-RepoDeTeste -Nome 'aviso_espelho' -Branches @('brodoo', 'main') `
    -Declaracoes @{ 'proj' = 'main' } -BranchFinal 'base'
  $res = Invoke-Checkout -RepoPath $r
  Assert-True ($res.Texto -like '*espelho local declara*') 'o aviso atribui a declaracao ao espelho, nao ao Odoo'
  Assert-True ($res.Texto -like '*re-sincronizar*') 'o aviso oferece a hipotese de ser o espelho que esta velho'

  # --- Declaracoes em desacordo: respeita-se a branch actual ----------------
  $r = New-RepoDeTeste -Nome 'desacordo_actual' -Branches @('brodoo', 'audit') `
    -Declaracoes @{ 'fase-3' = 'audit'; 'fase-2' = 'brodoo' } -BranchFinal 'audit'
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'audit' $res.Branch 'com declaracoes em desacordo, mantem-se a branch actual se for uma delas'
  Assert-True ($res.Texto -like '*desacordo*') 'o desacordo e reportado, nao silenciado'

  # --- Declaracoes em desacordo e nenhuma e a actual: para ------------------
  $r = New-RepoDeTeste -Nome 'desacordo_para' -Branches @('brodoo', 'audit') `
    -Declaracoes @{ 'fase-3' = 'audit'; 'fase-2' = 'teste' } -BranchFinal 'base'
  $res = Invoke-Checkout -RepoPath $r
  Assert-True ($res.Exit -ne 0) 'escolher ao acaso entre declaracoes em desacordo deixa de acontecer: para'
  Assert-True ($res.Texto -like '*em desacordo*') 'a paragem nomeia as candidatas'

  # --- O legacy so conta quando nao ha namespaced ---------------------------
  $r = New-RepoDeTeste -Nome 'legacy_ignorado' -Branches @('brodoo', 'audit') `
    -Declaracoes @{ 'fase-3' = 'audit' } -DeclaracaoLegacy 'main' -BranchFinal 'audit'
  $res = Invoke-Checkout -RepoPath $r
  Assert-Equal 'audit' $res.Branch 'havendo namespaced, o legacy desatualizado e ignorado'

  Write-Host ""
  Write-Host "OK: $($script:Total) verificacoes passaram."
  exit 0
}
catch {
  Write-Host ""
  Write-Host "$_"
  exit 1
}
finally {
  if (Test-Path $raiz) { Remove-Item -LiteralPath $raiz -Recurse -Force -ErrorAction SilentlyContinue }
}
