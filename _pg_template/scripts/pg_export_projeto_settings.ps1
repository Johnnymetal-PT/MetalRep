<#
.SYNOPSIS
  Exporta o instantaneo portavel das Definicoes do modulo pg_projeto (Odoo do
  cliente do projeto) para um ficheiro JSON no repo do projeto, UM POR BRANCH.

.DESCRIPTION
  So os campos de definicao do pg_projeto que sao valores simples
  (booleano/numero/texto/selecao) - nunca campos que referenciam registos
  (projeto-modelo, produto de servico SAV, centro de trabalho, grupo, etc.),
  porque um id de outra base de dados nao e valido numa base nova/reconstruida.
  Ver pg_projeto/models/pg_settings_snapshot.py (pg_export_settings_snapshot).

  UM FICHEIRO POR BRANCH, NAO um unico ficheiro por projeto: producao, e cada
  branch de staging (teste, teste_jmm, ...), podem ter deliberadamente
  funcionalidades diferentes ligadas (ex.: producao ainda nao usa tudo o que
  uma branch de teste de cliente ja esta a validar). O parametro -Purpose so
  escolhe a LIGACAO (production/brodoo_dev tem credenciais fixas no Odoo PG);
  -Branch identifica o AMBIENTE real por trás dessa ligacao no momento da
  exportacao (o nome de BD do Odoo.sh muda a cada rebuild em staging, por
  isso nao serve como chave estavel - o branch escolhido pelo operador sim).

  Reutiliza pg_odoo_client_query.ps1 para a ligacao (Brodoo -> pg.odoo.connection
  do projeto, por -ProjectKey/-Purpose, com auto-heal do nome da BD em Odoo.sh).
  E o caminho read_mode='api'.

.PARAMETER ProjectKey
  project_key do projeto (campo pg_project_key em project.project no Odoo PG).

.PARAMETER Purpose
  'production', 'brodoo_dev' ou 'client_test' - ligação usada para chegar ao Odoo-alvo.

.PARAMETER Branch
  Nome (ou ID) da branch/ambiente real que esta ligacao representa neste
  momento (ex.: 'production', 'teste', 'teste_jmm'). Define o nome do
  ficheiro de saida e fica gravado como metadado dentro do proprio ficheiro.

.PARAMETER RepoPath
  Caminho do repo do projeto onde gravar o ficheiro (default: diretoria atual).

.PARAMETER OutFile
  Caminho completo do ficheiro de saida (default: '<RepoPath>\pg_projeto_settings.<Branch>.json').

.EXAMPLE
  pg_export_projeto_settings.ps1 -ProjectKey odoo-jmm-formati -Purpose brodoo_dev -Branch teste_jmm -RepoPath "c:\Documentos Parametro\Repos\jmmgroup"

.NOTES
  Complementar a pg_import_projeto_settings.ps1 (aplica o ficheiro de UM branch
  concreto numa base nova/reconstruida DESSE MESMO branch).
#>
param(
  [Parameter(Mandatory = $true)][string]$ProjectKey,
  [Parameter(Mandatory = $true)][ValidateSet('production', 'brodoo_dev', 'client_test')][string]$Purpose,
  [Parameter(Mandatory = $true)][string]$Branch,
  [string]$RepoPath = (Get-Location).Path,
  [string]$OutFile,
  [string]$CredentialsPath,
  [string]$SshTarget
)

$ErrorActionPreference = 'Stop'

# Nome de ficheiro tem de ser seguro em qualquer sistema de ficheiros.
$safeBranch = $Branch -replace '[^A-Za-z0-9_.-]', '_'
if (-not $OutFile) {
  $OutFile = Join-Path $RepoPath "pg_projeto_settings.$safeBranch.json"
}

$queryScript = Join-Path $PSScriptRoot 'pg_odoo_client_query.ps1'
if (-not (Test-Path $queryScript)) { throw "pg_odoo_client_query.ps1 nao encontrado em '$queryScript'." }

# '[]': para metodos @api.model o Odoo NAO retira o 1o elemento como ids
# (odoo/service/model.py call_kw) - os args vao tal como estao para o
# metodo; pg_export_settings_snapshot() nao leva argumentos.
# Splat por HASHTABLE (nao array): um array de pares '-Nome',valor liga por
# POSICAO, nao por nome - com >1 parametro isso liga aos parametros errados.
$queryArgs = @{
  ProjectKey = $ProjectKey
  Purpose    = $Purpose
  Model      = 'res.config.settings'
  Method     = 'pg_export_settings_snapshot'
  ArgsJson   = '[]'
}
if ($CredentialsPath) { $queryArgs['CredentialsPath'] = $CredentialsPath }
if ($SshTarget) { $queryArgs['SshTarget'] = $SshTarget }

$rawOutput = & $queryScript @queryArgs
if ($LASTEXITCODE -ne 0) { throw "pg_odoo_client_query.ps1 falhou: $($rawOutput -join "`n")" }

$jsonText = ($rawOutput -join "`n").Trim()
$settings = $jsonText | ConvertFrom-Json

$envelope = [ordered]@{
  branch           = $Branch
  purpose          = $Purpose
  project_key      = $ProjectKey
  exported_at_utc  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  settings         = $settings
}
$pretty = $envelope | ConvertTo-Json -Depth 20

Set-Content -Path $OutFile -Value $pretty -Encoding utf8
Write-Output "OK: instantaneo das Definicoes do pg_projeto (branch='$Branch') gravado em '$OutFile'."
Write-Output ("Campos exportados: " + (($settings.PSObject.Properties | Select-Object -ExpandProperty Name) -join ', '))
