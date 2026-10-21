<#
.SYNOPSIS
  Configura, nesta maquina, a credencial de acesso ao Odoo da Parametro Global.

.DESCRIPTION
  Escreve %USERPROFILE%\.pg\odoo_credentials.json com o login e a API key de QUEM corre
  o comando. Substitui a chave partilhada do utilizador de servico Brodoo, que vivia no
  repositorio e portanto no historico do git.

  Porque e que a chave passa a ser pessoal:
    - revogar deixa de obrigar a rodar a chave de toda a gente;
    - o Odoo passa a saber QUEM fez cada escrita. Com a chave partilhada, as ligacoes e
      os artigos criados pelos scripts apareciam todos como "Brodoo", e uma utilizacao
      indevida nao era atribuivel a ninguem.

  O ficheiro fica FORA de qualquer repositorio: nao pode ser commitado por engano, e o
  script recusa-se a escrever dentro de um repositorio git.

  NAO valida depois de escrever: valida ANTES, e so escreve o que autenticou. Persistir
  uma chave que nao funciona deixa a maquina com uma configuracao que parece feita e
  falha na primeira utilizacao real, tipicamente a meio de outra coisa.

.PARAMETER Login
  Login no Odoo da Parametro Global -- o mesmo com que se entra no Odoo. Atencao ao
  dominio: ha contas em @parametro.global e contas em @parametro.pt. Sem ele, e pedido
  interactivamente.

.PARAMETER ApiKey
  A API key. Sem ela, e pedida interactivamente e nao aparece no ecra. Preferir a via
  interactiva: uma chave escrita na linha de comandos fica no historico da consola.

.PARAMETER Verificar
  So verifica o que ja esta configurado (origem, login, uid) e nao escreve nada.

.PARAMETER Force
  Substitui uma configuracao existente de outro login sem perguntar.

.EXAMPLE
  # Como criar a chave, primeiro, no Odoo:
  #   Definicoes > Utilizadores > (o meu utilizador) > Seguranca da conta > Novas chaves API
  powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1 -Verificar
#>
param(
  [string]$Login,
  [string]$ApiKey,
  [switch]$Verificar,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1')

function Invoke-PgJsonRpc {
  param([string]$Url, [hashtable]$Params)
  $body = @{ jsonrpc = '2.0'; method = 'call'; params = $Params } | ConvertTo-Json -Depth 20 -Compress
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
  $resp = Invoke-RestMethod -Method Post -Uri (($Url.TrimEnd('/')) + '/jsonrpc') `
    -ContentType 'application/json; charset=utf-8' -Body $bytes
  if ($resp.error) {
    $msg = $resp.error.data.message
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $resp.error.message }
    throw "Erro Odoo JSON-RPC: $msg"
  }
  return $resp.result
}

function Test-PgOdooLogin {
  <#
    Autentica e devolve quem e. Mostrar o NOME e o ponto: e o que apanha a chave colada
    do utilizador errado, que de outra forma so se descobre quando uma escrita aparece
    assinada por outra pessoa.
  #>
  param([string]$Url, [string]$Db, [string]$LoginParaTestar, [string]$Key)

  $uid = Invoke-PgJsonRpc -Url $Url -Params @{
    service = 'common'; method = 'authenticate'
    args    = @($Db, $LoginParaTestar, $Key, @{})
  }
  if (-not $uid -or $uid -eq $false) {
    # O dominio vem primeiro porque foi a causa do primeiro caso real (2026-09-28): a
    # base tem contas em @parametro.pt e em @parametro.global, e o exemplo que este
    # script dava no prompt encaminhava toda a gente para o segundo.
    throw ("Autenticacao recusada para '$LoginParaTestar' em $Url.`n" +
      "CAUSA MAIS PROVAVEL: o dominio do login. Ha contas em @parametro.pt e em " +
      "@parametro.global -- confirmar qual e o teu no Odoo, em Definicoes > Utilizadores.`n" +
      "Outras causas: a chave nao e deste login; a chave foi revogada.")
  }

  $utilizador = Invoke-PgJsonRpc -Url $Url -Params @{
    service = 'object'; method = 'execute_kw'
    args    = @($Db, [int]$uid, $Key, 'res.users', 'read', @(@([int]$uid), @('name', 'login')))
  }
  # @() e obrigatorio: um `read` de um so registo chega como PSCustomObject, e um
  # PSCustomObject nao tem .Count em PS 5.1 -- a verificacao passava a dizer
  # "(nome por ler)" exactamente no caso normal, que e o de um utilizador.
  $lista = @($utilizador)
  $nome = if ($lista.Count -gt 0) { [string]$lista[0].name } else { '(nome por ler)' }
  return [pscustomobject]@{ uid = [int]$uid; nome = $nome }
}

function Get-PgOdooApiKeys {
  <#
    As chaves do proprio utilizador, com a data de validade.

    Em Odoo 19 uma chave so e persistente se quem a cria tiver o grupo Definicoes
    (`env.is_system()`); toda a gente fica limitada ao teto do seu grupo. Logo, a maioria
    das chaves TEM validade, e uma chave que morre a meio de uma sessao aparece como
    "uid vazio" -- que nao sugere nunca que o problema e a data.

    A regra de registo `api_key_user` do Odoo limita a leitura as chaves do proprio
    (`[('user_id','=',user.id)]`), pelo que isto nao ve as chaves de mais ninguem.
  #>
  param([string]$Url, [string]$Db, [int]$Uid, [string]$Key)

  $dominio = '[["user_id","=",' + $Uid + ']]'
  $argsJson = '["' + $Db + '",' + $Uid + ',"' + $Key + '","res.users.apikeys","search_read",[' +
    $dominio + '],{"fields":["name","expiration_date","create_date"]}]'
  $corpo = '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":' + $argsJson + '}}'
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($corpo)
  try {
    $resp = Invoke-RestMethod -Method Post -Uri (($Url.TrimEnd('/')) + '/jsonrpc') `
      -ContentType 'application/json; charset=utf-8' -Body $bytes
  }
  catch {
    # Nao saber a validade nao invalida a credencial: o setup continua.
    return $null
  }
  if ($resp.error) { return $null }
  return @($resp.result)
}

function Protect-Ficheiro {
  <# Sem heranca e so para quem o escreveu. Falhar aqui nao invalida a configuracao. #>
  param([string]$Caminho)
  try {
    $acl = Get-Acl -Path $Caminho
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($regra in @($acl.Access)) { [void]$acl.RemoveAccessRule($regra) }
    $eu = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $regraNova = New-Object System.Security.AccessControl.FileSystemAccessRule(
      $eu, 'FullControl', 'None', 'None', 'Allow')
    $acl.SetAccessRule($regraNova)
    Set-Acl -Path $Caminho -AclObject $acl
    return $true
  }
  catch {
    Write-Warning "Nao foi possivel restringir as permissoes de '$Caminho': $($_.Exception.Message)"
    return $false
  }
}

try {
  $endpoint = Get-PgOdooEndpointDefaults
  if ([string]::IsNullOrWhiteSpace($endpoint.url) -or [string]::IsNullOrWhiteSpace($endpoint.db)) {
    throw "credentials/pg_odoo_endpoint.json sem 'url' ou 'db'. Sem isso nao ha onde autenticar."
  }

  if ($Verificar) {
    $origem = Get-PgOdooCredentialSource
    Write-Host ''
    Write-Host '=== pg_init_odoo_credentials -Verificar ==='
    Write-Host ("  origem   : {0}" -f $origem.kind)
    if ($origem.path) { Write-Host ("  caminho  : {0}" -f $origem.path) }
    if ($origem.kind -eq 'nenhuma') {
      Write-Host '  estado   : POR CONFIGURAR'
      Write-Host ("  resolver : {0}" -f (Get-PgOdooSetupCommand))
      exit 1
    }
    $cred = Get-PgOdooCredentials
    $quem = Test-PgOdooLogin -Url $cred.url -Db $cred.db -LoginParaTestar $cred.login -Key $cred.api_key
    Write-Host ("  login    : {0}" -f $cred.login)
    Write-Host ("  autentica: SIM -- {0} (uid {1})" -f $quem.nome, $quem.uid)

    # Ao vivo, nao do que ficou guardado: e para isto que serve um -Verificar.
    $chaves = @(Get-PgOdooApiKeys -Url $cred.url -Db $cred.db -Uid $quem.uid -Key $cred.api_key)
    if ($chaves.Count -gt 0) {
      Write-Host ("  chaves   : {0} neste utilizador" -f $chaves.Count)
      foreach ($k in $chaves) {
        $d = [string]$k.expiration_date
        $quando = if ([string]::IsNullOrWhiteSpace($d) -or $d -eq 'False') { 'sem validade (persistente)' } else { "expira $d (UTC)" }
        Write-Host ("             - {0}: {1}" -f $k.name, $quando)
      }
    }
    if ($origem.kind -eq 'legado') {
      Write-Host ''
      Write-Host '  ATENCAO: esta maquina ainda usa a CHAVE PARTILHADA do Brodoo, que vai ser revogada.'
      Write-Host ("  Configurar a chave desta maquina: {0}" -f (Get-PgOdooSetupCommand))
      exit 2
    }
    Write-Host '  estado   : OK'
    exit 0
  }

  if ([string]::IsNullOrWhiteSpace($Login)) {
    Write-Host 'Login no Odoo da Parametro Global -- o MESMO com que entras no Odoo.'
    Write-Host 'Atencao ao dominio: ha contas em @parametro.global e contas em @parametro.pt.'
    $Login = (Read-Host -Prompt '  login').Trim()
  }
  if ([string]::IsNullOrWhiteSpace($Login)) { throw 'Login vazio. Nada foi escrito.' }

  if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Host ''
    Write-Host 'API key do TEU utilizador. Criar em:'
    Write-Host '  Definicoes > Utilizadores > (o meu utilizador) > Seguranca da conta > Novas chaves API'
    $seguro = Read-Host -Prompt '  api key' -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)
    try { $ApiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
  }
  if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'API key vazia. Nada foi escrito.' }

  $destino = Get-PgOdooMachineCredentialsPath
  if ([string]::IsNullOrWhiteSpace($destino)) {
    throw 'Nao consegui determinar o perfil do utilizador (USERPROFILE/HOME por definir).'
  }
  Assert-ForaDeRepositorio -Caminho $destino

  if ((Test-Path $destino) -and (-not $Force)) {
    $anterior = $null
    try { $anterior = Read-Utf8JsonFile -Path $destino } catch { $anterior = $null }
    $loginAnterior = if ($anterior) { [string]$anterior.login } else { '' }
    if ($loginAnterior -and ($loginAnterior -ne $Login)) {
      throw ("Ja existe credencial nesta maquina para '$loginAnterior' e estas a configurar '$Login'.`n" +
        "Se e mesmo para substituir, repetir com -Force.")
    }
  }

  # Validar ANTES de escrever: so persiste o que autenticou.
  Write-Host ''
  Write-Host ("A validar contra {0} ..." -f $endpoint.url)
  $quem = Test-PgOdooLogin -Url $endpoint.url -Db $endpoint.db -LoginParaTestar $Login -Key $ApiKey
  Write-Host ("  autenticado: {0} (uid {1})" -f $quem.nome, $quem.uid)

  $chaves = Get-PgOdooApiKeys -Url $endpoint.url -Db $endpoint.db -Uid $quem.uid -Key $ApiKey
  $validade = Resolve-PgOdooExpiry -Chaves $chaves
  Write-Host ("  validade   : {0}" -f $validade.nota)

  $conteudo = [ordered]@{
    _nota   = 'Credencial DESTA maquina para o Odoo da Parametro Global. Pessoal e intransmissivel: as escritas feitas com ela ficam registadas em teu nome. Nunca copiar para um repositorio. Escrito por pg_init_odoo_credentials.ps1.'
    login   = $Login
    api_key = $ApiKey
  }
  # So se guarda o que se sabe: sem certeza sobre qual e a chave, nao se inventa a data.
  if (-not [string]::IsNullOrWhiteSpace($validade.valor)) {
    $conteudo.api_key_expira_em = $validade.valor
  }
  $conteudo = $conteudo | ConvertTo-Json -Depth 5

  Write-Utf8NoBomFile -Path $destino -Content ($conteudo + "`n")
  $protegido = Protect-Ficheiro -Caminho $destino

  # Reler pela cascata: prova que o ficheiro escrito e mesmo o que os scripts vao usar.
  # Escrever no sitio certo e ser encontrado no sitio certo sao duas coisas diferentes.
  $origemFinal = Get-PgOdooCredentialSource
  if ($origemFinal.kind -eq 'env') {
    Write-Warning ("Ficheiro escrito, mas esta sessao tem PG_ODOO_API_KEY definida e essa vence. " +
      "Fechar e reabrir a consola, ou limpar a variavel, para passar a usar o ficheiro.")
  }
  elseif ($origemFinal.kind -ne 'maquina') {
    throw ("Escrevi '$destino' mas a cascata continua a resolver por '$($origemFinal.kind)'. " +
      "Isto nao devia acontecer: reportar.")
  }

  Write-Host ''
  Write-Host '=== configurado ==='
  Write-Host ("  ficheiro  : {0}" -f $destino)
  Write-Host ("  login     : {0}" -f $Login)
  Write-Host ("  permissoes: {0}" -f $(if ($protegido) { 'restritas a este utilizador' } else { 'por restringir (ver aviso acima)' }))
  Write-Host ''
  Write-Host '  A partir daqui as consultas ao Odoo PG correm em teu nome.'
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
