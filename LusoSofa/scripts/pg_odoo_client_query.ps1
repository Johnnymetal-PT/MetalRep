<#
.SYNOPSIS
  Consulta direta ao Odoo DO CLIENTE de um projeto, por finalidade, via JSON-RPC.
  Obtem as credenciais do Odoo-alvo a partir do Odoo da Parametro Global (canal
  Brodoo, pg.odoo.connection) e depois consulta o Odoo-alvo.

.DESCRIPTION
  Dois canais por projeto (modelo pg.odoo.connection no Odoo PG):
    - production : Odoo de PRODUCAO do cliente  -> analise de adocao do cliente
    - brodoo_dev : Odoo da branch 'brodoo' (build Staging Odoo.sh) -> desenvolvimento

  Fluxo:
    1) le credentials/brodoo_credentials.json e autentica no Odoo PG;
    2) resolve o repositorio do projeto (por -ProjectKey) e a pg.odoo.connection
       da -Purpose pedida -> base_url/database/login/api_key do Odoo-alvo;
    3) autentica no Odoo-alvo e corre execute_kw sobre o Model/Method indicados.

  E o caminho MAIS caro (read_mode='api', 2 saltos). Preferir sempre primeiro os
  artefactos espelhados (.pg/...). Quem chamar deve registar read_mode='api' no
  consumo de tokens.

.PARAMETER ProjectKey
  project_key do projeto (campo pg_project_key em project.project no Odoo PG).

.PARAMETER Purpose
  'production', 'brodoo_dev' ou 'client_test'.

.PARAMETER Model / Method / Domain / Fields / Limit / ArgsJson
  Iguais ao pg_odoo_query.ps1, mas aplicados ao Odoo-ALVO do cliente.

.PARAMETER Protocol
  Protocolo de consulta: 'auto' (default), 'rpc' (JSON-RPC execute_kw classico) ou
  'mcp' (Model Context Protocol nativo Odoo 19+ / SaaS 19.4+).
  No modo 'auto', se a autenticacao RPC falhar com AccessDenied ou se a instancia
  responder a /mcp, a consulta comuta automaticamente para o canal MCP.

.PARAMETER SshTarget
  (Opcional, reforco) Destino SSH (user@host) da instancia-alvo, da UI "Connect" da
  branch no Odoo.sh. O AUTO-HEAL dispara sempre que a auth no Odoo-alvo falhar (nova
  build -> nome da BD mudou): resolve o nome atual via pg_odoo_resolve_db.ps1 (tenta
  primeiro HTTP /web/database/list com o base_url da ligacao, SEM SSH; so usa este
  -SshTarget se o endpoint estiver bloqueado/ambiguo), persiste-o em
  pg.odoo.connection.database e retenta. O SSH usa a conta GitHub/SSH do operador
  (sem segredos novos).

.EXAMPLE
  # Modulos realmente instalados no Odoo de producao do cliente
  pg_odoo_client_query.ps1 -ProjectKey odoo-epoca -Purpose production `
    -Model ir.module.module -Method search_read `
    -Domain '[["state","=","installed"]]' -Fields name,shortdesc

.EXAMPLE
  # Consulta forçada via protocolo nativo MCP (Odoo 19+)
  pg_odoo_client_query.ps1 -ProjectKey odoo-cliente -Purpose production `
    -Protocol mcp -Model crm.lead -Fields name,stage_id -Limit 10

.EXAMPLE
  # Com auto-heal do nome da BD (Odoo.sh brodoo_dev): resolve/atualiza se a build mudou
  pg_odoo_client_query.ps1 -ProjectKey odoo-epoca -Purpose brodoo_dev `
    -Model res.users -Method search_count -Domain '[]' `
    -SshTarget parametro-brodoo-12345678@parametro-brodoo-12345678.dev.odoo.com

.NOTES
  As credenciais do cliente vivem centralizadas no Odoo PG (pg.odoo.connection),
  nunca em secrets de repos de cliente. Configurar em Brodoo > Repositorio >
  Ligacoes Odoo do cliente.
#>
param(
  [Parameter(Mandatory = $true)][string]$ProjectKey,
  [Parameter(Mandatory = $true)][ValidateSet('production', 'brodoo_dev', 'client_test')][string]$Purpose,
  [Parameter(Mandatory = $true)][string]$Model,
  [ValidateSet('auto', 'rpc', 'mcp')][string]$Protocol = 'auto',
  [string]$Method = 'search_read',
  [string]$Domain = '[]',
  [string[]]$Fields,
  [int]$Limit = 0,
  [string]$ArgsJson,
  [string]$CredentialsPath,
  # Odoo.sh: destino SSH (user@host) da instancia-alvo, da UI "Connect" da branch.
  # E APENAS um reforco: se a auth no Odoo-alvo falhar (nova build -> nome da BD
  # mudou), o auto-heal ja tenta primeiro resolver via HTTP /web/database/list com o
  # base_url da ligacao (sem SSH). O -SshTarget so e usado se esse endpoint estiver
  # bloqueado/ambiguo. O nome resolvido e persistido em pg.odoo.connection.database.
  [string]$SshTarget
)

$ErrorActionPreference = 'Stop'

function Get-BrodooCredentials {
  param([string]$Explicit)
  $path = if ($Explicit) { $Explicit } else { (Join-Path (Split-Path -Parent $PSScriptRoot) 'credentials\brodoo_credentials.json') }
  if (-not (Test-Path $path)) { throw "Credenciais Brodoo nao encontradas em '$path'. Ver credentials/README.md." }
  $c = Get-Content -Path $path -Raw | ConvertFrom-Json
  foreach ($k in @('url', 'db', 'login', 'api_key')) {
    if ([string]::IsNullOrWhiteSpace([string]$c.$k)) { throw "Campo '$k' em falta nas credenciais Brodoo." }
  }
  if ([string]$c.api_key -match 'COLAR_AQUI') { throw "api_key Brodoo ainda e o placeholder (ver credentials/README.md)." }
  return $c
}

function Invoke-OdooAuth {
  param([string]$Url, [string]$Db, [string]$Login, [string]$Key)
  $body = @{ jsonrpc = '2.0'; method = 'call'; params = @{ service = 'common'; method = 'authenticate'; args = @($Db, $Login, $Key, @{}) } } | ConvertTo-Json -Depth 20 -Compress
  # Corpo como bytes UTF-8: em PS 5.1 um body string é codificado em Latin-1,
  # o que corrompe acentos em escritas (o Odoo espera UTF-8).
  $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
  $endpoint = ($Url.TrimEnd('/')) + '/jsonrpc'
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json; charset=utf-8' -Body $bodyBytes
  }
  catch [System.Net.WebException] {
    # Um 404 em /jsonrpc nao e "servidor em baixo": no Odoo 19 os endpoints RPC sairam do
    # core e passaram a vir do modulo `rpc` ("RPC endpoints", auto_install). Se alguem o
    # desinstalar, TODO o canal Brodoo morre nessa base -- leituras, espelho e migracoes --
    # e a falha aparece como erro de rede. Ninguem adivinha isto a primeira. Ver issue #57.
    $estado = $null
    try { $estado = [int]$_.Exception.Response.StatusCode } catch { }
    if ($estado -eq 404) {
      throw ("O endpoint /jsonrpc respondeu 404 em $Url.`n" +
        "CAUSA PROVAVEL: o modulo 'rpc' ('RPC endpoints') nao esta instalado nesta base. " +
        "No Odoo 19 os endpoints /jsonrpc e /xmlrpc deixaram de ser servidos pelo core e " +
        "passam a vir desse modulo, que e auto_install mas pode ser desinstalado a mao.`n" +
        "Verificar em Definicoes > Aplicacoes (remover o filtro 'Aplicacoes') e procurar 'rpc'; " +
        "sem ele nenhuma consulta a esta base funciona.`n" +
        "Detalhe: $($_.Exception.Message)")
    }
    throw
  }
  if ($resp.error) { throw "Erro de autenticacao Odoo ($Url): $($resp.error.data.message)" }
  if (-not $resp.result -or $resp.result -eq $false) { throw "Autenticacao falhou em $Url (uid vazio). Validar login/api_key/db." }
  return [int]$resp.result
}

function Invoke-OdooExecuteKw {
  param([string]$Url, [string]$Db, [int]$Uid, [string]$Key, [string]$Model, [string]$Method, [string]$PositionalJson, [string]$KwargsJson)
  $argsJson = '["' + $Db + '",' + $Uid + ',"' + $Key + '","' + $Model + '","' + $Method + '",' + $PositionalJson + ',' + $KwargsJson + ']'
  $body = '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":' + $argsJson + '}}'
  # Corpo como bytes UTF-8 (ver Invoke-OdooAuth): evita mojibake em create/write com acentos.
  $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
  $endpoint = ($Url.TrimEnd('/')) + '/jsonrpc'
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json; charset=utf-8' -Body $bodyBytes
  }
  catch [System.Net.WebException] {
    # Um 404 em /jsonrpc nao e "servidor em baixo": no Odoo 19 os endpoints RPC sairam do
    # core e passaram a vir do modulo `rpc` ("RPC endpoints", auto_install). Se alguem o
    # desinstalar, TODO o canal Brodoo morre nessa base -- leituras, espelho e migracoes --
    # e a falha aparece como erro de rede. Ninguem adivinha isto a primeira. Ver issue #57.
    $estado = $null
    try { $estado = [int]$_.Exception.Response.StatusCode } catch { }
    if ($estado -eq 404) {
      throw ("O endpoint /jsonrpc respondeu 404 em $Url.`n" +
        "CAUSA PROVAVEL: o modulo 'rpc' ('RPC endpoints') nao esta instalado nesta base. " +
        "No Odoo 19 os endpoints /jsonrpc e /xmlrpc deixaram de ser servidos pelo core e " +
        "passam a vir desse modulo, que e auto_install mas pode ser desinstalado a mao.`n" +
        "Verificar em Definicoes > Aplicacoes (remover o filtro 'Aplicacoes') e procurar 'rpc'; " +
        "sem ele nenhuma consulta a esta base funciona.`n" +
        "Detalhe: $($_.Exception.Message)")
    }
    throw
  }
  if ($resp.error) {
    $msg = $resp.error.data.message
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $resp.error.message }
    throw "Erro Odoo JSON-RPC (execute_kw em $Url): $msg"
  }
  return $resp.result
}

function Set-ConnectionDatabase {
  # Persiste o novo nome da BD em pg.odoo.connection.database (canal Brodoo, method write).
  param([string]$PgUrl, [string]$PgDb, [int]$PgUid, [string]$PgKey, [int]$ConnId, [string]$NewDb)
  $positional = '[[' + $ConnId + '],{"database":"' + $NewDb + '"}]'
  [void](Invoke-OdooExecuteKw -Url $PgUrl -Db $PgDb -Uid $PgUid -Key $PgKey `
      -Model 'pg.odoo.connection' -Method 'write' -PositionalJson $positional -KwargsJson '{}')
}

try {
  # 1) Autenticar no Odoo PG (canal Brodoo)
  $pg = Get-BrodooCredentials -Explicit $CredentialsPath
  $pgUid = Invoke-OdooAuth -Url $pg.url -Db $pg.db -Login $pg.login -Key $pg.api_key

  # 2a) Resolver o repositorio do projeto a partir do project_key
  $projKeyEsc = $ProjectKey.Replace('\', '\\').Replace('"', '\"')
  $projPositional = '[[["pg_project_key","=","' + $projKeyEsc + '"]]]'
  $projRes = Invoke-OdooExecuteKw -Url $pg.url -Db $pg.db -Uid $pgUid -Key $pg.api_key `
    -Model 'project.project' -Method 'search_read' -PositionalJson $projPositional -KwargsJson '{"fields":["pg_repository_id"],"limit":1}'
  if (-not $projRes -or $projRes.Count -eq 0) { throw "Projeto com pg_project_key='$ProjectKey' nao encontrado no Odoo PG." }
  $repoField = $projRes[0].pg_repository_id
  if (-not $repoField) { throw "O projeto '$ProjectKey' nao tem repositorio (pg_repository_id) associado." }
  $repoId = [int]$repoField[0]

  # 2b) Resolver a pg.odoo.connection da finalidade pedida
  $connPositional = '[[["repository_id","=",' + $repoId + '],["purpose","=","' + $Purpose + '"],["active","=",true]]]'
  $connRes = Invoke-OdooExecuteKw -Url $pg.url -Db $pg.db -Uid $pgUid -Key $pg.api_key `
    -Model 'pg.odoo.connection' -Method 'search_read' -PositionalJson $connPositional -KwargsJson '{"fields":["id","base_url","database","login","api_key"],"limit":1}'
  if (-not $connRes -or $connRes.Count -eq 0) {
    throw "Sem ligacao Odoo purpose='$Purpose' para o projeto '$ProjectKey'. Configurar em Brodoo > Repositorio > Ligacoes Odoo do cliente."
  }
  $conn = $connRes[0]
  # 'database' NAO entra nos obrigatorios: em Odoo.sh o nome muda a cada rebuild da
  # branch, e o auto-heal abaixo resolve-o e persiste-o. Exigi-lo aqui impedia o
  # proprio mecanismo que existe para o dispensar (ligacoes de staging deixam-no vazio).
  foreach ($k in @('base_url', 'login', 'api_key')) {
    if ([string]::IsNullOrWhiteSpace([string]$conn.$k)) { throw "Ligacao '$Purpose' de '$ProjectKey' com campo '$k' em falta." }
  }

  # Normalizar o base_url: o Odoo 17+ mostra o backoffice em '.../odoo' e e esse URL
  # que se copia, mas os endpoints da API vivem na raiz. O sufixo dava 400 na
  # autenticacao E na resolucao da BD, sem dizer porque.
  $conn.base_url = ([string]$conn.base_url).Trim().TrimEnd('/')
  if ($conn.base_url.ToLower().EndsWith('/odoo')) { $conn.base_url = $conn.base_url.Substring(0, $conn.base_url.Length - 5).TrimEnd('/') }
  if ($conn.base_url -and $conn.base_url -notmatch '^https?://') { $conn.base_url = "https://$($conn.base_url)" }

  # 3) Se Protocol for explicitamente 'mcp', consulta via MCP imediatamente
  if ($Protocol -eq 'mcp') {
    $mcpScript = Join-Path $PSScriptRoot 'pg_odoo_mcp_query.ps1'
    if (-not (Test-Path $mcpScript)) { throw "Script MCP nao encontrado em '$mcpScript'." }
    $mcpAction = if ($Method -eq 'read_group') { 'read_group' } else { 'search' }
    & $mcpScript -BaseUrl $conn.base_url -ApiKey $conn.api_key -Action $mcpAction -Model $Model -Domain $Domain -Fields $Fields -Limit $Limit
    exit 0
  }

  # 4) Autenticar no Odoo-ALVO (RPC com fallback automatico para MCP se falhar)
  $tgtUid = $null
  $useMcpFallback = $false

  try {
    $tgtUid = Invoke-OdooAuth -Url $conn.base_url -Db $conn.database -Login $conn.login -Key $conn.api_key
  }
  catch {
    $authErr = $_.Exception.Message
    
    # Se protocolo for 'auto', verificar primeiro se o endpoint /mcp responde com sucesso
    if ($Protocol -eq 'auto') {
      $mcpScript = Join-Path $PSScriptRoot 'pg_odoo_mcp_query.ps1'
      if (Test-Path $mcpScript) {
        try {
          $pingRes = & $mcpScript -BaseUrl $conn.base_url -ApiKey $conn.api_key -Action ping 2>$null
          if ($pingRes -and $LASTEXITCODE -eq 0) {
            $useMcpFallback = $true
          }
        }
        catch {
          $useMcpFallback = $false
        }
      }
    }

    if ($useMcpFallback) {
      Write-Warning "RPC falhou mas endpoint MCP disponivel em '$($conn.base_url)'. A executar consulta via MCP..."
      $mcpAction = if ($Method -eq 'read_group') { 'read_group' } else { 'search' }
      & $mcpScript -BaseUrl $conn.base_url -ApiKey $conn.api_key -Action $mcpAction -Model $Model -Domain $Domain -Fields $Fields -Limit $Limit
      exit 0
    }

    # Em staging do Odoo.sh, a cada rebuild mudam o database E o base_url. O resolver
    # resolve a base DADO um URL; nao resolve o URL. Se o host deixou de existir, nenhuma
    # das mensagens abaixo faz sentido sem esta pista -- e quem apanha isto perde tempo a
    # investigar credenciais e rede. Ver issue #58 e AGENTS_SHARED.
    $pistaStaging = ''
    if ($Purpose -in @('client_test', 'brodoo_dev')) {
      $pistaStaging = ("`nCAUSA PROVAVEL: esta ligacao e de staging ('$Purpose') e em Odoo.sh cada rebuild da branch " +
        "muda TAMBEM o base_url, nao so o database. O base_url guardado e '$($conn.base_url)'. " +
        "Copiar o URL atual do botao CONNECT da branch no Odoo.sh e actualizar pg.odoo.connection.base_url:" +
        "`n  pg_odoo_query.ps1 -Model pg.odoo.connection -Method write -ArgsJson '[[$($conn.id)],{`"base_url`":`"<url novo>`"}]'")
    }

    $resolver = Join-Path $PSScriptRoot 'pg_odoo_resolve_db.ps1'
    if (-not (Test-Path $resolver)) { throw "Resolver nao encontrado em '$resolver'. Detalhe auth: $authErr" }

    Write-Warning "Auth falhou com database='$($conn.database)'. A resolver o nome atual da BD (HTTP /web/database/list -> SSH)..."
    $resolverArgs = @{ BaseUrl = $conn.base_url }
    if (-not [string]::IsNullOrWhiteSpace($SshTarget)) { $resolverArgs['SshTarget'] = $SshTarget }

    try {
      $newDb = ([string]((& $resolver @resolverArgs) | Select-Object -Last 1)).Trim()
    }
    catch {
      throw ("Nao foi possivel resolver o nome da BD para '$($conn.base_url)'." + $pistaStaging +
        "`nO /web/database/list pode tambem estar bloqueado/ambiguo; nesse caso reexecutar com " +
        "-SshTarget <user@host> (UI 'Connect' do Odoo.sh) para resolver via shell. " +
        "`nDetalhe resolver: $($_.Exception.Message) | Detalhe auth: $authErr")
    }
    if ([string]::IsNullOrWhiteSpace($newDb)) {
      throw ("Resolver nao devolveu nome de BD para '$($conn.base_url)'." + $pistaStaging + "`nDetalhe auth: $authErr")
    }

    if ($newDb -ne [string]$conn.database) {
      Write-Warning "BD resolvida: '$newDb' (antiga: '$($conn.database)'). A persistir em pg.odoo.connection..."
      Set-ConnectionDatabase -PgUrl $pg.url -PgDb $pg.db -PgUid $pgUid -PgKey $pg.api_key -ConnId ([int]$conn.id) -NewDb $newDb
      $conn.database = $newDb
    }
    $tgtUid = Invoke-OdooAuth -Url $conn.base_url -Db $conn.database -Login $conn.login -Key $conn.api_key
  }

  if (-not [string]::IsNullOrWhiteSpace($ArgsJson)) {
    $positionalJson = $ArgsJson.Trim()
    $kwargsJson = '{}'
  }
  else {
    $domainRaw = if ([string]::IsNullOrWhiteSpace($Domain)) { '[]' } else { $Domain.Trim() }
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

  $result = Invoke-OdooExecuteKw -Url $conn.base_url -Db $conn.database -Uid $tgtUid -Key $conn.api_key `
    -Model $Model -Method $Method -PositionalJson $positionalJson -KwargsJson $kwargsJson

  $result | ConvertTo-Json -Depth 20
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
