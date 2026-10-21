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
    1) resolve as credenciais desta maquina e autentica no Odoo PG;
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

.PARAMETER Context
  Contexto Odoo em JSON, injectado nos kwargs do execute_kw (ex.:
  '{"allowed_company_ids":[9]}'). Necessario para ler e escrever campos
  company_dependent, que o Odoo resolve pela empresa do contexto e nao pela do
  utilizador da API. Funciona com -ArgsJson e sem ele. So viaja pelo protocolo
  'rpc'; com 'mcp' o script falha em vez de correr sem contexto.

.PARAMETER Protocol
  Protocolo de consulta: 'auto' (default), 'rpc' (JSON-RPC execute_kw classico) ou
  'mcp' (Model Context Protocol nativo Odoo 19+ / SaaS 19.4+).
  No modo 'auto', se a autenticacao RPC falhar com AccessDenied ou se a instancia
  responder a /mcp, a consulta comuta automaticamente para o canal MCP.

  Chaves: a ligacao guarda uma chave por protocolo. 'api_key' (ambito RPC) serve o
  RPC; 'api_key_mcp' (ambito MCP, Odoo 20+) serve o MCP e, vazia, e substituida pela
  RPC. No Odoo 20 uma chave so abre os endpoints do seu ambito. O MCP nao le todos os
  modelos (o Odoo 20 recusa, p. ex., 'ir.module.module' a agentes de IA): para a ordem
  de decisao, a chave RPC continua a ser a que importa.

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
  # Contexto Odoo (JSON) para os kwargs do execute_kw. Ver .PARAMETER Context.
  [string]$Context,
  [string]$CredentialsPath,
  # Odoo.sh: destino SSH (user@host) da instancia-alvo, da UI "Connect" da branch.
  # E APENAS um reforco: se a auth no Odoo-alvo falhar (nova build -> nome da BD
  # mudou), o auto-heal ja tenta primeiro resolver via HTTP /web/database/list com o
  # base_url da ligacao (sem SSH). O -SshTarget so e usado se esse endpoint estiver
  # bloqueado/ambiguo. O nome resolvido e persistido em pg.odoo.connection.database.
  [string]$SshTarget
)

$ErrorActionPreference = 'Stop'

# O -Context so viaja pelo RPC: o canal MCP nao tem onde o por. Falhar aqui e melhor
# do que correr sem ele -- uma escrita num campo company_dependent sem contexto grava
# na empresa por defeito do utilizador da API e devolve sucesso na mesma. Foi assim
# que um contorno passou por bom durante dois dias sem estar aplicado.
if (-not [string]::IsNullOrWhiteSpace($Context)) {
  try { $null = $Context | ConvertFrom-Json }
  catch { throw "O -Context nao e JSON valido: $($_.Exception.Message)" }
  if ($Protocol -eq 'mcp') {
    throw "O -Context nao e suportado no protocolo 'mcp'. Repetir com -Protocol rpc."
  }
}

# Primeiro salto (Odoo PG): a resolucao das credenciais vive no ponto unico, com a
# chave por maquina. Ver pg_odoo_credentials_common.ps1.
. (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1')

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
  # No Odoo 20 as chaves API tem ambito, e uma chave criada para o MCP da exatamente
  # este "uid vazio" no /jsonrpc, com o mesmo login e a mesma base. Foi o que custou
  # tempo a 2026-10-14 (animovel): a chave funcionava no MCP e parecia errada no RPC.
  if (-not $resp.result -or $resp.result -eq $false) {
    throw ("Autenticacao falhou em $Url (uid vazio). Validar login/api_key/db.`n" +
      "Em Odoo 20+, confirmar tambem o AMBITO da chave: o campo 'api_key' da ligacao tem de ter ambito RPC. " +
      "Uma chave de ambito MCP so serve o /mcp e vai no campo 'api_key_mcp'.")
  }
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
  $pg = Get-PgOdooCredentials -CredentialsPath $CredentialsPath
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
  # Uma ligacao por finalidade, uma chave por protocolo: 'api_key' (ambito RPC) e
  # 'api_key_mcp' (ambito MCP, opcional). No Odoo 20 cada chave so abre os endpoints do
  # seu ambito -- uma chave MCP da "uid vazio" no /jsonrpc. O campo 'api_key_mcp' so
  # existe a partir do pg_brodoo 19.0.1.14.2; com um Brodoo mais antigo o Odoo recusa o
  # campo desconhecido, e repete-se a leitura sem ele (a chave RPC serve os dois canais,
  # como ate ao Odoo 19).
  $connPositional = '[[["repository_id","=",' + $repoId + '],["purpose","=","' + $Purpose + '"],["active","=",true]]]'
  try {
    try {
      $connRes = Invoke-OdooExecuteKw -Url $pg.url -Db $pg.db -Uid $pgUid -Key $pg.api_key `
        -Model 'pg.odoo.connection' -Method 'search_read' -PositionalJson $connPositional -KwargsJson '{"fields":["id","base_url","database","login","api_key","api_key_mcp"],"limit":1}'
    }
    catch {
      if ($_.Exception.Message -notmatch 'api_key_mcp') { throw }
      $connRes = Invoke-OdooExecuteKw -Url $pg.url -Db $pg.db -Uid $pgUid -Key $pg.api_key `
        -Model 'pg.odoo.connection' -Method 'search_read' -PositionalJson $connPositional -KwargsJson '{"fields":["id","base_url","database","login","api_key"],"limit":1}'
    }
  }
  catch {
    # Com o pg_brodoo 19.0.1.15.0 a `api_key` das ligacoes passa a exigir o grupo
    # "Credenciais dos Odoo dos clientes" (risco R1: sem ele, qualquer utilizador de projeto
    # le as chaves de todos os clientes). A 2026-10-07 essa versao NAO esta instalada em
    # producao; este ramo fica pronto para quando entrar. Sem o grupo, o Odoo recusa o
    # CAMPO, e a mensagem que ele devolve nao diz a ninguem o que pedir nem a quem.
    if ($_.Exception.Message -match 'api_key') {
      throw ("Sem permissao para ler a API key das ligacoes Odoo do cliente.`n" +
        "Falta o grupo 'Credenciais dos Odoo dos clientes: Ler credenciais', que se atribui em " +
        "Definicoes > Utilizadores, na categoria Administracao.`n" +
        "Detalhe do Odoo: $($_.Exception.Message)")
    }
    throw
  }
  if (-not $connRes -or $connRes.Count -eq 0) {
    throw "Sem ligacao Odoo purpose='$Purpose' para o projeto '$ProjectKey'. Configurar em Brodoo > Repositorio > Ligacoes Odoo do cliente."
  }
  $conn = $connRes[0]
  # 'database' NAO entra nos obrigatorios: em Odoo.sh o nome muda a cada rebuild da
  # branch, e o auto-heal abaixo resolve-o e persiste-o. Exigi-lo aqui impedia o
  # proprio mecanismo que existe para o dispensar (ligacoes de staging deixam-no vazio).
  # Chave do canal MCP: a propria, se a ligacao a tiver; senao a RPC (Odoo <= 19, onde
  # uma chave serve os dois). A chave RPC so e obrigatoria quando a consulta pode ir
  # por RPC: com -Protocol mcp basta a MCP.
  # O Odoo devolve 'false' num Char vazio, e [string]$false e o texto "False": testar
  # o valor antes de o converter, senao "False" passava por chave.
  $mcpKey = if ($conn.api_key_mcp) { [string]$conn.api_key_mcp } elseif ($conn.api_key) { [string]$conn.api_key } else { '' }
  $obrigatorios = @('base_url', 'login')
  if ($Protocol -ne 'mcp') { $obrigatorios += 'api_key' }
  foreach ($k in $obrigatorios) {
    if ([string]::IsNullOrWhiteSpace([string]$conn.$k)) { throw "Ligacao '$Purpose' de '$ProjectKey' com campo '$k' em falta." }
  }
  if ([string]::IsNullOrWhiteSpace($mcpKey) -and $Protocol -eq 'mcp') {
    throw "Ligacao '$Purpose' de '$ProjectKey' sem chave para o MCP (campos 'api_key_mcp' e 'api_key' vazios)."
  }

  # Normalizar o base_url: o Odoo 17+ mostra o backoffice em '.../odoo' e e esse URL
  # que se copia, mas os endpoints da API vivem na raiz. O sufixo dava 400 na
  # autenticacao E na resolucao da BD, sem dizer porque.
  $conn.base_url = ([string]$conn.base_url).Trim().TrimEnd('/')
  if ($conn.base_url.ToLower().EndsWith('/odoo')) { $conn.base_url = $conn.base_url.Substring(0, $conn.base_url.Length - 5).TrimEnd('/') }
  # O mesmo para '/mcp': e o endereco que a documentacao do MCP mostra, e guardado na
  # ligacao punha o RPC a bater em '/mcp/jsonrpc' (404, lido como "modulo rpc em falta").
  if ($conn.base_url.ToLower().EndsWith('/mcp')) { $conn.base_url = $conn.base_url.Substring(0, $conn.base_url.Length - 4).TrimEnd('/') }
  if ($conn.base_url -and $conn.base_url -notmatch '^https?://') { $conn.base_url = "https://$($conn.base_url)" }

  # 3) Se Protocol for explicitamente 'mcp', consulta via MCP imediatamente
  if ($Protocol -eq 'mcp') {
    $mcpScript = Join-Path $PSScriptRoot 'pg_odoo_mcp_query.ps1'
    if (-not (Test-Path $mcpScript)) { throw "Script MCP nao encontrado em '$mcpScript'." }
    $mcpAction = if ($Method -eq 'read_group') { 'read_group' } else { 'search' }
    & $mcpScript -BaseUrl $conn.base_url -ApiKey $mcpKey -Action $mcpAction -Model $Model -Domain $Domain -Fields $Fields -Limit $Limit
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
          $pingRes = & $mcpScript -BaseUrl $conn.base_url -ApiKey $mcpKey -Action ping 2>$null
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
      if (-not [string]::IsNullOrWhiteSpace($Context)) {
        throw ("RPC falhou e o fallback MCP nao suporta -Context. A consulta NAO foi feita. " +
          "Corrigir a autenticacao RPC e repetir com -Protocol rpc.")
      }
      Write-Warning "RPC falhou mas endpoint MCP disponivel em '$($conn.base_url)'. A executar consulta via MCP..."
      $mcpAction = if ($Method -eq 'read_group') { 'read_group' } else { 'search' }
      & $mcpScript -BaseUrl $conn.base_url -ApiKey $mcpKey -Action $mcpAction -Model $Model -Domain $Domain -Fields $Fields -Limit $Limit
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

  # Os kwargs passam a ser montados nos dois modos. Antes, com -ArgsJson, eram sempre
  # '{}' -- e sem kwargs nao ha onde por o contexto, o que deixava os campos
  # company_dependent fora do alcance deste canal.
  $kwargsParts = @()
  if (-not [string]::IsNullOrWhiteSpace($ArgsJson)) {
    $positionalJson = $ArgsJson.Trim()
  }
  else {
    $domainRaw = if ([string]::IsNullOrWhiteSpace($Domain)) { '[]' } else { $Domain.Trim() }
    if ($Fields) { $Fields = @($Fields | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
    if ($Fields -and $Fields.Count -gt 0) {
      $fieldsJson = ($Fields | ForEach-Object { '"' + $_ + '"' }) -join ','
      $kwargsParts += '"fields":[' + $fieldsJson + ']'
    }
    if ($Limit -gt 0) { $kwargsParts += '"limit":' + [int]$Limit }
    $positionalJson = '[' + $domainRaw + ']'
  }
  if (-not [string]::IsNullOrWhiteSpace($Context)) {
    $kwargsParts += '"context":' + $Context.Trim()
  }
  $kwargsJson = '{' + ($kwargsParts -join ',') + '}'

  $result = Invoke-OdooExecuteKw -Url $conn.base_url -Db $conn.database -Uid $tgtUid -Key $conn.api_key `
    -Model $Model -Method $Method -PositionalJson $positionalJson -KwargsJson $kwargsJson

  $result | ConvertTo-Json -Depth 20
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
