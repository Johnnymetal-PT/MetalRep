<#
.SYNOPSIS
  Aplica o instantaneo portavel das Definicoes do modulo pg_projeto (gravado por
  pg_export_projeto_settings.ps1) numa base de dados do Odoo do cliente do
  projeto - tipicamente uma base nova ou reconstruida DO MESMO BRANCH.

.DESCRIPTION
  So reaplica os campos de definicao simples (booleano/numero/texto/selecao)
  incluidos no ficheiro. Qualquer definicao que referencie um registo
  (projeto-modelo, produto de servico SAV, centro de trabalho, grupo, etc.)
  fica sempre no valor por defeito do modulo - o instantaneo nunca a inclui,
  porque um id de outra base de dados nao e valido na base de destino.
  Ver pg_projeto/models/pg_settings_snapshot.py (pg_import_settings_snapshot).

  UM FICHEIRO POR BRANCH: producao e cada branch de staging (teste,
  teste_jmm, ...) podem ter deliberadamente funcionalidades diferentes
  ligadas. Por isso o -Branch pedido aqui tem de corresponder ao 'branch'
  gravado dentro do ficheiro (metadado escrito pelo export) - evita aplicar
  por engano o instantaneo de um ambiente no ambiente errado (ex.: ligar em
  producao uma funcionalidade que so a branch de teste do cliente devia ter).
  Usar -Force só para ignorar essa validacao de propósito.

  Reutiliza pg_odoo_client_query.ps1 para a ligacao (Brodoo -> pg.odoo.connection
  do projeto, por -ProjectKey/-Purpose, com auto-heal do nome da BD em Odoo.sh).
  E o caminho read_mode='api' - esta operacao ESCREVE na base de destino.

.PARAMETER ProjectKey
  project_key do projeto (campo pg_project_key em project.project no Odoo PG).

.PARAMETER Purpose
  'production', 'brodoo_dev' ou 'client_test' - ligação usada para chegar ao Odoo-alvo.

.PARAMETER Branch
  Nome (ou ID) da branch/ambiente de destino (ex.: 'production', 'teste',
  'teste_jmm'). Define o nome do ficheiro de entrada por defeito e tem de
  corresponder ao 'branch' gravado dentro do ficheiro, salvo -Force.

.PARAMETER RepoPath
  Caminho do repo do projeto onde ler o ficheiro (default: diretoria atual).

.PARAMETER InFile
  Caminho completo do ficheiro a aplicar (default: '<RepoPath>\pg_projeto_settings.<Branch>.json').

.PARAMETER Force
  Ignora a validacao de que o 'branch' gravado no ficheiro coincide com -Branch.

.EXAMPLE
  pg_import_projeto_settings.ps1 -ProjectKey odoo-jmm-formati -Purpose brodoo_dev -Branch teste_jmm -RepoPath "c:\Documentos Parametro\Repos\jmmgroup"

.NOTES
  Complementar a pg_export_projeto_settings.ps1. Confirmar com o utilizador antes
  de correr contra -Purpose production - escreve definicoes na base de dados alvo.
#>
param(
  [Parameter(Mandatory = $true)][string]$ProjectKey,
  [Parameter(Mandatory = $true)][ValidateSet('production', 'brodoo_dev', 'client_test')][string]$Purpose,
  [Parameter(Mandatory = $true)][string]$Branch,
  [string]$RepoPath = (Get-Location).Path,
  [string]$InFile,
  [switch]$Force,
  [string]$CredentialsPath,
  [string]$SshTarget
)

$ErrorActionPreference = 'Stop'

$safeBranch = $Branch -replace '[^A-Za-z0-9_.-]', '_'
if (-not $InFile) {
  $InFile = Join-Path $RepoPath "pg_projeto_settings.$safeBranch.json"
}
if (-not (Test-Path $InFile)) { throw "Ficheiro de instantaneo nao encontrado em '$InFile'. Correr primeiro pg_export_projeto_settings.ps1 -Branch '$Branch'." }

$queryScript = Join-Path $PSScriptRoot 'pg_odoo_client_query.ps1'
if (-not (Test-Path $queryScript)) { throw "pg_odoo_client_query.ps1 nao encontrado em '$queryScript'." }

$envelope = (Get-Content -Path $InFile -Raw) | ConvertFrom-Json
if (-not $envelope.settings) { throw "Ficheiro '$InFile' nao tem a forma esperada (falta a chave 'settings' - foi gerado por uma versao antiga deste script? reexportar)." }
if (-not $Force -and $envelope.branch -and ([string]$envelope.branch -ne $Branch)) {
  throw "O ficheiro '$InFile' foi exportado do branch '$($envelope.branch)', mas pediste -Branch '$Branch'. Isto evita aplicar por engano a configuracao de um ambiente noutro. Usar -Force se for mesmo essa a intencao."
}

$valuesJson = ($envelope.settings | ConvertTo-Json -Depth 20 -Compress)

# Para metodos @api.model o Odoo NAO retira o 1o elemento como ids
# (odoo/service/model.py call_kw) - os args vao tal como estao para o
# metodo; pg_import_settings_snapshot(values) leva so o dict, sem lista de ids.
$argsJson = '[' + $valuesJson + ']'

# Splat por HASHTABLE (nao array): um array de pares '-Nome',valor liga por
# POSICAO, nao por nome - com >1 parametro isso liga aos parametros errados.
$queryArgs = @{
  ProjectKey = $ProjectKey
  Purpose    = $Purpose
  Model      = 'res.config.settings'
  Method     = 'pg_import_settings_snapshot'
  ArgsJson   = $argsJson
}
if ($CredentialsPath) { $queryArgs['CredentialsPath'] = $CredentialsPath }
if ($SshTarget) { $queryArgs['SshTarget'] = $SshTarget }

$rawOutput = & $queryScript @queryArgs
if ($LASTEXITCODE -ne 0) { throw "pg_odoo_client_query.ps1 falhou: $($rawOutput -join "`n")" }

Write-Output "OK: instantaneo do branch '$($envelope.branch)' ('$InFile') aplicado nas Definicoes do pg_projeto (purpose=$Purpose, branch destino=$Branch)."
Write-Output ("Resultado: " + ($rawOutput -join ' '))
