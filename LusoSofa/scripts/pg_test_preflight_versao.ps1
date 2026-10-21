<#
.SYNOPSIS
  Testes da resolucao da versao Odoo no preflight.

.DESCRIPTION
  O passo 3 do ritual existe para garantir que a versao esta CONFIRMADA antes de qualquer
  comando dependente de serie. Ate 2026-09-11 nao garantia:

  - `Get-ProjectGovernance` percorria todos os project.json e ficava com o ULTIMO que
    tivesse versao -- num repositorio multi-projeto, a ordem de travessia do disco
    decidia. `FACTO OBSERVADO` (givachoice, 31/07 a 11/08): dois projetos espelhados,
    17.0 e 19.0, e o preflight deu `pass` a citar documentacao de 17.0 num projeto que
    corria 19.0;
  - a coerencia entre o que o Odoo declara e o que o source E nunca era verificada.
    `FACTO OBSERVADO` (2026-09-11): o PadraoMagistral declara 18.0 e tem o source em 19.0.

  Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achado D3.
#>
param()

$ErrorActionPreference = 'Stop'

$script:Total = 0

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:Total += 1
  if (-not $Condition) { throw "FALHA: $Message" }
  Write-Host "  OK   $Message"
}

function New-RepoPreflight {
  param(
    [string]$Nome,
    [string]$SerieSource,
    [hashtable]$Governance,   # chave = projeto namespaced, valor = odoo_version
    [string]$RotuloVersao
  )

  $repo = Join-Path $raiz $Nome
  New-Item -ItemType Directory -Path $repo -Force | Out-Null

  # Source falso: so o release.py, que e de onde a serie real e lida.
  $core = Join-Path $repo 'vendor\odoo_src\community\odoo'
  New-Item -ItemType Directory -Path $core -Force | Out-Null
  $partes = $SerieSource.Split('.')
  Set-Content -Path (Join-Path $core 'release.py') -Encoding utf8 `
    -Value ("version_info = ({0}, {1}, 0, 'final', 0, '')" -f $partes[0], $partes[1])

  foreach ($chave in $Governance.Keys) {
    $dir = Join-Path $repo ".pg\projects\$chave\project"
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Set-Content -Path (Join-Path $dir 'project.json') -Encoding utf8 `
      -Value ('{ "project": { "governance": { "odoo_version": "' + $Governance[$chave] + '", "odoo_edition": "community" } } }')
  }

  $contexto = "# PG_CONTEXT`n`nAmbiente: on_premise`n"
  if ($RotuloVersao) { $contexto += "Versao do Odoo: $RotuloVersao`nEdicao: Community`n" }
  Set-Content -Path (Join-Path $repo 'PG_CONTEXT.md') -Value $contexto -Encoding utf8

  return $repo
}

function Invoke-Preflight {
  param([string]$RepoPath)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -RepoPath $RepoPath 2>&1
    $codigo = $LASTEXITCODE
  }
  finally { $ErrorActionPreference = $anterior }
  return [pscustomobject]@{
    Texto = (($saida | ForEach-Object { "$_" }) -join "`n")
    Exit  = $codigo
  }
}

$script = Join-Path $PSScriptRoot 'pg_preflight_context.ps1'
$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ('pg-preflight-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $raiz -Force | Out-Null

try {
  Write-Host "=== resolucao da versao Odoo no preflight ==="

  # --- caso do givachoice: multi-projeto, sem rotulo, versoes em desacordo ---
  $r = New-RepoPreflight -Nome 'sem_rotulo_desacordo' -SerieSource '19.0' `
    -Governance @{ 'fase-3' = '19.0'; 'fase-2' = '17.0' }
  $res = Invoke-Preflight -RepoPath $r
  Assert-True ($res.Exit -ne 0) 'sem rotulo e com governance em desacordo, a versao nao esta confirmada: e erro'
  Assert-True ($res.Texto -like '*nao confirmada*') 'o erro diz que a versao nao esta confirmada'
  Assert-True ($res.Texto -like '*arbitraria*') 'e explica que a alternativa seria arbitraria'

  # --- o mesmo repositorio, com rotulo: deixa de ser arbitrario ---
  $r = New-RepoPreflight -Nome 'com_rotulo_desacordo' -SerieSource '19.0' `
    -Governance @{ 'fase-3' = '19.0'; 'fase-2' = '17.0' } -RotuloVersao '19.0'
  $res = Invoke-Preflight -RepoPath $r
  Assert-True ($res.Texto -like '*19.0*') 'com rotulo, a versao resolvida e a declarada'
  Assert-True ($res.Texto -like '*desacordo*') 'o desacordo entre projetos continua a ser reportado'

  # --- governance contra source: as duas autoridades independentes ---
  $r = New-RepoPreflight -Nome 'governance_vs_source' -SerieSource '19.0' `
    -Governance @{ 'proj' = '18.0' } -RotuloVersao '19.0'
  $res = Invoke-Preflight -RepoPath $r
  Assert-True ($res.Exit -ne 0) 'Odoo a declarar 18.0 com o source em 19.0 tem de ser erro'
  Assert-True ($res.Texto -like '*autoridades independentes*') 'o erro explica porque sao duas autoridades'

  # --- caso saudavel: tudo de acordo ---
  $r = New-RepoPreflight -Nome 'coerente' -SerieSource '19.0' `
    -Governance @{ 'proj' = '19.0' } -RotuloVersao '19.0'
  $res = Invoke-Preflight -RepoPath $r
  Assert-True ($res.Texto -like '*Serie source: 19.0*') 'a serie real do source e reportada'
  Assert-True ($res.Texto -notlike '*Incoerencia*') 'com tudo de acordo nao ha incoerencia a reportar'

  # --- um so projeto sem rotulo: a governance basta, nao ha ambiguidade ---
  $r = New-RepoPreflight -Nome 'um_projeto_sem_rotulo' -SerieSource '18.0' `
    -Governance @{ 'proj' = '18.0' }
  $res = Invoke-Preflight -RepoPath $r
  Assert-True ($res.Texto -like '*18.0*') 'com um unico projeto, a governance resolve sem ambiguidade'
  Assert-True ($res.Texto -notlike '*nao confirmada*') 'e nao se inventa um problema onde nao ha'

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
