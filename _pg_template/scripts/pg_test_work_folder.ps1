<#
.SYNOPSIS
  Testes da declaracao de factos em pastas de trabalho fora de repositorio.

.DESCRIPTION
  A framework cobre repositorios; boa parte do trabalho de Odoo acontece em pastas de
  servidor. `FACTO OBSERVADO` (givachoice): em 46 conversas o agente procurou o AGENTS.md
  7 vezes nessas pastas, nao encontrou nada em nenhuma, e seguiu sem os factos do projeto
  -- seis incidentes de confusao de versao depois, incluindo um deploy de codigo v17 sobre
  o servidor de testes v19.

  Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achados B8 a B10.
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

function Invoke-Init {
  param([string[]]$Arguments)
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $saida = & powershell -NoProfile -ExecutionPolicy Bypass -File $script @Arguments 2>&1
    $codigo = $LASTEXITCODE
  }
  finally { $ErrorActionPreference = $anterior }
  return [pscustomobject]@{
    Texto = (($saida | ForEach-Object { "$_" }) -join "`n")
    Exit  = $codigo
  }
}

function New-SourceFalso {
  param([string]$Caminho, [string]$Serie)
  $odoo = Join-Path $Caminho 'odoo'
  New-Item -ItemType Directory -Path $odoo -Force | Out-Null
  $partes = $Serie.Split('.')
  Set-Content -Path (Join-Path $odoo 'release.py') -Encoding utf8 `
    -Value ("version_info = ({0}, {1}, 0, 'final', 0, '')" -f $partes[0], $partes[1])
  return $Caminho
}

$script = Join-Path $PSScriptRoot 'pg_init_work_folder.ps1'
$raiz = Join-Path ([System.IO.Path]::GetTempPath()) ('pg-wf-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $raiz -Force | Out-Null

try {
  Write-Host "=== factos em pastas de trabalho ==="

  # --- escrita basica -------------------------------------------------------
  $pasta = Join-Path $raiz 'addons_v17'
  New-Item -ItemType Directory -Path $pasta -Force | Out-Null
  $r = Invoke-Init @('-Path', $pasta, '-OdooVersion', '17.0', '-Servidor', 'C:\Odoo\server', '-BaseDados', 'GIVA17')
  Assert-True ($r.Exit -eq 0) 'a escrita basica conclui'
  $conteudo = Get-Content (Join-Path $pasta 'AGENTS.md') -Raw
  Assert-True ($conteudo -like '*Versao do Odoo: 17.0*') 'a versao fica declarada'
  Assert-True ($conteudo -like '*Base de dados: GIVA17*') 'a base de dados fica declarada'
  Assert-True ($conteudo -like '*NAO e um repositorio da framework*') 'o ficheiro diz o que a pasta nao e'

  # --- o conteudo de quem la trabalha sobrevive ----------------------------
  # E a licao do achado D1: a framework ja destruiu overrides locais uma vez.
  $meu = "`n`n## Notas minhas`n`n- O deploy faz-se por rsync, nao por git."
  Add-Content -Path (Join-Path $pasta 'AGENTS.md') -Value $meu -Encoding utf8
  $r = Invoke-Init @('-Path', $pasta, '-OdooVersion', '17.0', '-Servidor', 'C:\Odoo\server', '-BaseDados', 'GIVA19')
  Assert-True ($r.Exit -eq 0) 'a reexecucao conclui'
  $conteudo = Get-Content (Join-Path $pasta 'AGENTS.md') -Raw
  Assert-True ($conteudo -like '*O deploy faz-se por rsync*') 'o que esta fora do bloco sobrevive a reexecucao'
  Assert-True ($conteudo -like '*Base de dados: GIVA19*') 'o bloco foi de facto actualizado'
  Assert-True (([regex]::Matches($conteudo, 'PG_WORK_FOLDER:START')).Count -eq 1) 'o bloco nao se duplica'

  # --- idempotencia ---------------------------------------------------------
  $r = Invoke-Init @('-Path', $pasta, '-OdooVersion', '17.0', '-Servidor', 'C:\Odoo\server', '-BaseDados', 'GIVA19')
  Assert-True ($r.Texto -like '*nada a escrever*') 'sem alteracao, nao se reescreve'

  # --- versao detectada do source ------------------------------------------
  $src = New-SourceFalso -Caminho (Join-Path $raiz 'src19') -Serie '19.0'
  $pasta2 = Join-Path $raiz 'addons_v19'
  New-Item -ItemType Directory -Path $pasta2 -Force | Out-Null
  $r = Invoke-Init @('-Path', $pasta2, '-OdooSourcePath', $src)
  Assert-True ((Get-Content (Join-Path $pasta2 'AGENTS.md') -Raw) -like '*Versao do Odoo: 19.0*') 'a versao e detectada do release.py quando nao e declarada'
  Assert-True ($r.Texto -like '*confirmada no source*') 'e dito que a versao foi confirmada no source'

  # --- declarar uma versao que o source contradiz ---------------------------
  # E exactamente o erro que custou o deploy de v17 sobre o servidor v19.
  $pasta3 = Join-Path $raiz 'contradiz'
  New-Item -ItemType Directory -Path $pasta3 -Force | Out-Null
  $r = Invoke-Init @('-Path', $pasta3, '-OdooVersion', '17.0', '-OdooSourcePath', $src)
  Assert-True ($r.Exit -ne 0) 'declarar 17.0 com o source em 19.0 tem de falhar'
  Assert-True ($r.Texto -like '*Incoerencia*') 'a falha nomeia a incoerencia'
  Assert-True (-not (Test-Path (Join-Path $pasta3 'AGENTS.md'))) 'e nao escreve nada quando os factos se contradizem'

  # --- nunca sobre um repositorio da framework ------------------------------
  $repo = Join-Path $raiz 'repo_a_serio'
  New-Item -ItemType Directory -Path (Join-Path $repo '.pg') -Force | Out-Null
  $r = Invoke-Init @('-Path', $repo, '-OdooVersion', '19.0')
  Assert-True ($r.Exit -ne 0) 'uma pasta que ja e repositorio da framework tem de ser recusada'
  Assert-True ($r.Texto -like '*ja e um repositorio*') 'a recusa explica porque'
  Assert-True (-not (Test-Path (Join-Path $repo 'AGENTS.md'))) 'e nao lhe toca no AGENTS.md'

  # --- sem versao, avisa em vez de calar ------------------------------------
  $pasta4 = Join-Path $raiz 'sem_versao'
  New-Item -ItemType Directory -Path $pasta4 -Force | Out-Null
  $r = Invoke-Init @('-Path', $pasta4, '-Servidor', 'algures')
  Assert-True ($r.Texto -like '*facto mais caro*') 'sem versao, avisa que e o facto que mais custa'

  # --- o ritual passa a ter resposta nestas pastas -------------------------
  #
  # Era esta a metade que faltava: uma ancora que ninguem le nao vale nada. Ate agora o
  # preflight respondia "PG_CONTEXT.md nao encontrado - repositorio nao bootstrapado",
  # que e verdade e nao serve de nada a quem esta a trabalhar na pasta.
  $preflight = Join-Path $PSScriptRoot 'pg_preflight_context.ps1'

  $anterior = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $saidaPre = & powershell -NoProfile -ExecutionPolicy Bypass -File $preflight -RepoPath $pasta2 2>&1
  $codigoPre = $LASTEXITCODE
  $ErrorActionPreference = $anterior
  $textoPre = (($saidaPre | ForEach-Object { "$_" }) -join "`n")

  Assert-True ($codigoPre -eq 0) 'o ritual conclui numa pasta de trabalho declarada'
  Assert-True ($textoPre -like '*pasta de trabalho*') 'e diz que o que tem a frente e uma pasta de trabalho'
  Assert-True ($textoPre -like '*19.0*') 'recita a versao declarada'
  Assert-True ($textoPre -like '*documentation/19.0*') 'e deriva a documentacao da serie certa'
  Assert-True (-not (Test-Path (Join-Path $pasta2 '.pg'))) 'e nao cria estrutura de framework na pasta'

  # Numa pasta sem o bloco, o ritual nao inventa nada de novo.
  $semBloco = Join-Path $raiz 'sem_bloco'
  New-Item -ItemType Directory -Path $semBloco -Force | Out-Null
  Set-Content -Path (Join-Path $semBloco 'AGENTS.md') -Value '# Notas soltas' -Encoding utf8
  $ErrorActionPreference = 'Continue'
  $saidaSem = & powershell -NoProfile -ExecutionPolicy Bypass -File $preflight -RepoPath $semBloco 2>&1
  $ErrorActionPreference = $anterior
  Assert-True ((($saidaSem | ForEach-Object { "$_" }) -join "`n") -notlike '*pasta de trabalho declarada*') 'sem o marcador, nada muda: e por declaracao explicita, nunca por inferencia'

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
