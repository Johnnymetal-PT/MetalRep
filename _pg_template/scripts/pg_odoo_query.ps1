<#
.SYNOPSIS
  Canal de dados Brodoo: consulta uniforme ao Odoo da Parametro Global (JSON-RPC),
  usando as credenciais desta maquina (ver pg_odoo_credentials_common.ps1).

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

.PARAMETER KwargsJson
  Argumentos nomeados do execute_kw, em JSON (objeto). Ha metodos que so os aceitam
  assim -- o message_post e o caso conhecido -- e outros que precisam deles para
  'context', 'order' ou 'offset'. Funciona com e sem -ArgsJson. Sem -ArgsJson, junta-se
  ao 'fields'/'limit' construidos a partir de -Fields/-Limit; uma chave repetida falha
  em vez de uma das duas ganhar em silencio.

.PARAMETER CredentialsPath
  Override do caminho das credenciais. Sem ele, a cascata normal: variaveis de ambiente,
  depois %USERPROFILE%\.pg\odoo_credentials.json (a chave desta maquina).

.EXAMPLE
  pg_odoo_query.ps1 -Model res.users -Method search_count -Domain "[]"

.EXAMPLE
  pg_odoo_query.ps1 -Model hr.leave -Domain '[["state","=","validate"]]' -Fields employee_id,date_from,date_to -Limit 50

.EXAMPLE
  pg_odoo_query.ps1 -Model project.task -Domain '[["project_id","=",234]]' -Fields name -Limit 5 -KwargsJson '{"order":"id desc"}'

.NOTES
  A chave e de quem a corre e vive FORA do repositorio, em %USERPROFILE%\.pg\.
  Nunca copiar credenciais para repos de projeto/cliente. Ver credentials/README.md.
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
  [string]$ArgsJson,

  # Argumentos nomeados (JSON, objeto) para o execute_kw. Ver .PARAMETER KwargsJson.
  [string]$KwargsJson
)

$ErrorActionPreference = 'Stop'

# Validar o -KwargsJson antes de autenticar: um JSON partido so devia custar um erro
# local, nao uma ida ao servidor. Ate 2026-10-07 este helper nao tinha forma de passar
# argumentos nomeados, e o message_post -- que so os aceita -- ficava fora de alcance
# (tarefa 7586).
$kwargsExtraKeys = @()
$kwargsExtraInner = ''
if (-not [string]::IsNullOrWhiteSpace($KwargsJson)) {
  $kwargsTrim = $KwargsJson.Trim()
  try { $kwargsParsed = $kwargsTrim | ConvertFrom-Json }
  catch { Write-Error "O -KwargsJson nao e JSON valido: $($_.Exception.Message)"; exit 1 }
  if ($kwargsParsed -isnot [pscustomobject] -or -not $kwargsTrim.StartsWith('{')) {
    Write-Error 'O -KwargsJson tem de ser um objeto JSON (ex.: ''{"order":"id desc"}'').'
    exit 1
  }
  $kwargsExtraKeys = @($kwargsParsed.PSObject.Properties | ForEach-Object { $_.Name })
  # O conteudo segue tal como veio: reserializar em PS 5.1 estraga arrays de um elemento.
  $kwargsExtraInner = $kwargsTrim.Substring(1, $kwargsTrim.Length - 2).Trim()
}

# A resolucao das credenciais vive no ponto unico (ver pg_odoo_credentials_common.ps1):
# a chave e por maquina, e ter a cascata copiada aqui era ter um sitio a mais para
# divergir do Python do guard.
. (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1')

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
  $cred = Get-PgOdooCredentials -CredentialsPath $CredentialsPath

  # 1) Autenticar (API key funciona como password em authenticate)
  $uid = Invoke-OdooJsonRpc -Url $cred.url -Params @{
    service = 'common'
    method  = 'authenticate'
    args    = @($cred.db, $cred.login, $cred.api_key, @{})
  }
  if (-not $uid -or $uid -eq $false) {
    # Nomear a origem: com a chave por maquina, "autenticacao falhou" sem dizer QUAL
    # credencial foi usada manda quem le a mexer no ficheiro errado.
    # A causa mais provavel desde que as chaves passaram a ter validade: em Odoo 19 so
    # quem tem o grupo Definicoes cria chaves persistentes, e uma chave expirada falha
    # exactamente assim -- com um uid vazio que nao diz nada sobre datas.
    throw ("Autenticacao falhou (uid vazio) para o login '$($cred.login)'.`n" +
      "Credenciais obtidas de: $($cred.origem)`n" +
      "CAUSAS PROVAVEIS: a chave EXPIROU; foi revogada; ou nao pertence a este login.`n" +
      "Verificar com: powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1 -Verificar")
  }

  # 2) Construir os args do execute_kw como JSON EXPLICITO (evita o PowerShell serializar
  #    arrays como {value,Count}, que o Odoo rejeita com "Domain() invalid").
  if (-not [string]::IsNullOrWhiteSpace($ArgsJson)) {
    # Modo avancado: os args posicionais vem crus (write/call/etc.); os kwargs so
    # existem se vierem em -KwargsJson.
    $positionalJson = $ArgsJson.Trim()
    $kwargsParts = @()
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
    $positionalJson = '[' + $domainRaw + ']'

    foreach ($nome in @('fields', 'limit')) {
      $construida = ($nome -eq 'fields' -and $Fields -and $Fields.Count -gt 0) -or ($nome -eq 'limit' -and $Limit -gt 0)
      if ($construida -and $kwargsExtraKeys -contains $nome) {
        throw "'$nome' veio em -KwargsJson e tambem em -$((Get-Culture).TextInfo.ToTitleCase($nome)). Indicar so num dos dois."
      }
    }
  }
  if ($kwargsExtraInner) { $kwargsParts += $kwargsExtraInner }
  $kwargsJson = '{' + ($kwargsParts -join ',') + '}'

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
