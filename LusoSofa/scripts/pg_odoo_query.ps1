<#
.SYNOPSIS
  Canal de dados Brodoo: consulta uniforme ao Odoo da Parametro Global (JSON-RPC),
  usando as credenciais do utilizador de servico Brodoo em credentials/brodoo_credentials.json.

.DESCRIPTION
  Usar SO quando o dado pretendido NAO esta nos artefactos espelhados do projeto
  (.pg/...). E o caminho read_mode='api' (mais caro que o espelho) - preferir sempre
  primeiro os artefactos. Quem chamar deve registar read_mode='api' no consumo de tokens.

  Le as credenciais (url, db, login, api_key), autentica via common.authenticate e
  corre execute_kw sobre o modelo/metodo indicados. Devolve o resultado em JSON.

.PARAMETER Model
  Modelo Odoo (ex.: 'hr.leave', 'res.users', 'project.project').

.PARAMETER Method
  Metodo do ORM (default 'search_read'). Ex.: 'search_read', 'search_count', 'read'.

.PARAMETER Domain
  Dominio de pesquisa em JSON (ex.: '[["state","=","validate"]]'). Default '[]'.

.PARAMETER Fields
  Campos a devolver (para search_read/read).

.PARAMETER Limit
  Limite de registos (para search_read).

.PARAMETER CredentialsPath
  Override do caminho das credenciais. Default: ..\credentials\brodoo_credentials.json
  relativo a este script (resolve via symlink .pg_framework).

.EXAMPLE
  pg_odoo_query.ps1 -Model res.users -Method search_count -Domain "[]"

.EXAMPLE
  pg_odoo_query.ps1 -Model hr.leave -Domain '[["state","=","validate"]]' -Fields employee_id,date_from,date_to -Limit 50

.NOTES
  Segredo partilhado (Brodoo) vive no _pg_template privado; nunca copiar para repos
  de projeto/cliente. Ver credentials/README.md.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$Model,

  [string]$Method = 'search_read',

  [string]$Domain = '[]',

  [string[]]$Fields,

  [int]$Limit = 0,

  [string]$CredentialsPath,

  # Modo avancado: args posicionais crus (JSON) para o execute_kw, p.ex.:
  #   -Method write            -ArgsJson '[[252],{"pg_odoo_version":"19.0"}]'
  #   -Method action_sync_...  -ArgsJson '[[252]]'
  # Quando definido, ignora -Domain/-Fields/-Limit. USAR COM CUIDADO (pode escrever!).
  [string]$ArgsJson
)

$ErrorActionPreference = 'Stop'

function Resolve-CredentialsPath {
  param([string]$Explicit)
  if ($Explicit) { return $Explicit }
  return (Join-Path (Split-Path -Parent $PSScriptRoot) 'credentials\brodoo_credentials.json')
}

function Get-Credentials {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    throw "Credenciais Brodoo nao encontradas em '$Path'. Ver credentials/README.md."
  }
  $c = Get-Content -Path $Path -Raw | ConvertFrom-Json
  foreach ($k in @('url', 'db', 'login', 'api_key')) {
    if ([string]::IsNullOrWhiteSpace([string]$c.$k)) { throw "Campo '$k' em falta nas credenciais Brodoo." }
  }
  if ([string]$c.api_key -match 'COLAR_AQUI') {
    throw "api_key ainda e o placeholder. Colar a chave real do Brodoo em '$Path' (ver credentials/README.md)."
  }
  return $c
}

function Invoke-OdooJsonRpc {
  param([string]$Url, [hashtable]$Params)
  $body = @{ jsonrpc = '2.0'; method = 'call'; params = $Params } | ConvertTo-Json -Depth 20 -Compress
  $endpoint = ($Url.TrimEnd('/')) + '/jsonrpc'
  # Corpo como bytes UTF-8: em PS 5.1 um body string é codificado em Latin-1,
  # o que corrompe acentos em escritas (o Odoo espera UTF-8).
  $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json; charset=utf-8' -Body $bodyBytes
  }
  catch [System.Net.WebException] {
    # Ver a nota em pg_odoo_client_query.ps1: um 404 aqui e o modulo 'rpc' em falta, nao
    # o servidor em baixo. No Odoo 19 os endpoints /jsonrpc e /xmlrpc sairam do core e
    # passaram a vir desse modulo. Issue #57.
    $estado = $null
    try { $estado = [int]$_.Exception.Response.StatusCode } catch { }
    if ($estado -eq 404) {
      throw ("O endpoint respondeu 404: $endpoint`n" +
        "CAUSA PROVAVEL: o modulo 'rpc' ('RPC endpoints') nao esta instalado nesta base. " +
        "Verificar em Definicoes > Aplicacoes, removendo o filtro 'Aplicacoes'.`n" +
        "Detalhe: $($_.Exception.Message)")
    }
    throw
  }
  if ($resp.error) {
    $msg = $resp.error.data.message
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $resp.error.message }
    throw "Erro Odoo JSON-RPC: $msg"
  }
  return $resp.result
}

try {
  $credPath = Resolve-CredentialsPath -Explicit $CredentialsPath
  $cred = Get-Credentials -Path $credPath

  # 1) Autenticar (API key funciona como password em authenticate)
  $uid = Invoke-OdooJsonRpc -Url $cred.url -Params @{
    service = 'common'
    method  = 'authenticate'
    args    = @($cred.db, $cred.login, $cred.api_key, @{})
  }
  if (-not $uid -or $uid -eq $false) {
    throw "Autenticacao falhou (uid vazio). Validar login/api_key/db do Brodoo."
  }

  # 2) Construir os args do execute_kw como JSON EXPLICITO (evita o PowerShell serializar
  #    arrays como {value,Count}, que o Odoo rejeita com "Domain() invalid").
  if (-not [string]::IsNullOrWhiteSpace($ArgsJson)) {
    # Modo avancado: os args posicionais vem crus (write/call/etc.); sem kwargs.
    $positionalJson = $ArgsJson.Trim()
    $kwargsJson = '{}'
  }
  else {
    $domainRaw = if ([string]::IsNullOrWhiteSpace($Domain)) { '[]' } else { $Domain.Trim() }

    # Normalizar -Fields: via 'powershell -File' um "a,b,c" chega como um unico elemento.
    if ($Fields) { $Fields = @($Fields | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }

    $kwargsParts = @()
    if ($Fields -and $Fields.Count -gt 0) {
      $fieldsJson = ($Fields | ForEach-Object { '"' + $_ + '"' }) -join ','
      $kwargsParts += '"fields":[' + $fieldsJson + ']'
    }
    if ($Limit -gt 0) { $kwargsParts += '"limit":' + [int]$Limit }
    $kwargsJson = '{' + ($kwargsParts -join ',') + '}'
    $positionalJson = '[' + $domainRaw + ']'
  }

  # args = [db, uid, api_key, model, method, <positional>, kwargs]
  $argsJson = '["' + $cred.db + '",' + [int]$uid + ',"' + $cred.api_key + '","' + $Model + '","' + $Method + '",' + $positionalJson + ',' + $kwargsJson + ']'
  $body = '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":' + $argsJson + '}}'
  $endpoint = ($cred.url.TrimEnd('/')) + '/jsonrpc'
  # Corpo como bytes UTF-8 (ver Invoke-OdooJsonRpc): evita mojibake em create/write com acentos.
  $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json; charset=utf-8' -Body $bodyBytes
  }
  catch [System.Net.WebException] {
    # Ver a nota em pg_odoo_client_query.ps1: um 404 aqui e o modulo 'rpc' em falta, nao
    # o servidor em baixo. No Odoo 19 os endpoints /jsonrpc e /xmlrpc sairam do core e
    # passaram a vir desse modulo. Issue #57.
    $estado = $null
    try { $estado = [int]$_.Exception.Response.StatusCode } catch { }
    if ($estado -eq 404) {
      throw ("O endpoint respondeu 404: $endpoint`n" +
        "CAUSA PROVAVEL: o modulo 'rpc' ('RPC endpoints') nao esta instalado nesta base. " +
        "Verificar em Definicoes > Aplicacoes, removendo o filtro 'Aplicacoes'.`n" +
        "Detalhe: $($_.Exception.Message)")
    }
    throw
  }
  if ($resp.error) {
    $msg = $resp.error.data.message
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $resp.error.message }
    throw "Erro Odoo JSON-RPC (execute_kw): $msg"
  }

  $resp.result | ConvertTo-Json -Depth 20
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
