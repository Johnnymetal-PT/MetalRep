<#
  Resolucao das credenciais de acesso ao Odoo da Parametro Global.

  PARA QUE SERVE
    Ponto unico de passagem das credenciais do canal Brodoo. Ate 2026-09-28 cada
    consumidor resolvia por sua conta (pg_odoo_query.ps1, pg_odoo_client_query.ps1,
    pg_pull_doc_templates.ps1, pg_odoo_migration_guard.py), e quatro copias da mesma
    logica sao quatro sitios para divergir. E o mesmo argumento do guard de migracoes:
    por ser o unico caminho, o que aqui muda muda para todos.

  O QUE E POR MAQUINA E O QUE E PARTILHADO
    Sao por maquina, e so estes, o `login` e a `api_key`: o segredo passa a ser de uma
    pessoa, revogavel sozinho, e o Odoo passa a saber QUEM fez cada escrita. Ate aqui
    toda a equipa partilhava a chave do utilizador de servico Brodoo, pelo que nenhuma
    escrita era atribuivel -- a mesma cegueira que o campo `operator` do log de tokens
    veio corrigir do lado de ca.

    Sao partilhados, por nao serem segredo, o `url` e a `db`: vivem versionados em
    credentials/pg_odoo_endpoint.json. Se o Odoo PG mudar de endereco, muda num sitio
    e nao em todas as maquinas.

  CASCATA (a primeira que der chave ganha)
    0. -CredentialsPath explicito -- vence tudo; mantem o contrato antigo dos helpers.
    1. $env:PG_ODOO_API_KEY (+ $env:PG_ODOO_LOGIN) -- override por sessao e via de CI.
    2. $env:PG_ODOO_KNOWLEDGE_TOKEN -- alias legado, aceite para nao partir quem o use.
    3. ficheiro da maquina: %USERPROFILE%\.pg\odoo_credentials.json
       (ou $env:PG_ODOO_CREDENTIALS_FILE). Fora de qualquer repositorio, pelo que nao
       pode ser commitado por engano. E a via normal, e e a ULTIMA.

    Houve um quarto degrau -- uma chave partilhada guardada no repositorio -- que saiu a
    2026-09-28, com a conta de servico arquivada e a prova pela negativa feita.

  PORQUE FICHEIRO E NAO DPAPI / CREDENTIAL MANAGER
    Metade dos consumidores e Python (pg_odoo_migration_guard.py,
    pg_doc_templates_common.py) e nao le um segredo cifrado por DPAPI sem um
    intermediario em PowerShell. O que se ganharia era cifra em repouso contra quem ja
    tem a sessao Windows aberta -- que nao e o problema. O problema e a chave estar em
    todos os clones e no historico do git, e um ficheiro fora do repositorio resolve-o
    inteiro.

  Este ficheiro so define funcoes: e feito para ser dot-sourced.
    . (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1')
#>

. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')

$script:PgOdooSetupComando = 'powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1'

function Get-PgOdooSetupCommand {
  return $script:PgOdooSetupComando
}

function Get-PgOdooMachineCredentialsPath {
  # $env:PG_ODOO_CREDENTIALS_FILE existe para os testes exercitarem a cascata sem
  # tocar no perfil de quem corre.
  if (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_CREDENTIALS_FILE)) {
    return $env:PG_ODOO_CREDENTIALS_FILE
  }
  $raiz = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
  if ([string]::IsNullOrWhiteSpace($raiz)) { return $null }
  # Join-Path aninhado, um segmento de cada vez, e nao os dois num literal so: uma barra
  # invertida dentro do segmento e separador no Windows e um caractere normal em
  # macOS/Linux. Ha quem corra isto num Mac, e o lado Python usa os.path.join -- se as
  # duas metades divergirem no separador, uma escreve o ficheiro onde a outra nao o
  # procura. O teste test_o_caminho_da_maquina_nao_fixa_o_separador guarda isto.
  return (Join-Path (Join-Path $raiz '.pg') 'odoo_credentials.json')
}

function Get-PgOdooLegacyCredentialsPath {
  # Nao faz parte da cascata desde 2026-09-28. Fica so para o pg_retire_shared_brodoo_key.ps1
  # poder dizer se o ficheiro ainda esta na arvore.
  return (Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'credentials') 'brodoo_credentials.json')
}

function Get-PgOdooEndpointDefaults {
  # url e db partilhados. Nao sao segredo: ficam versionados.
  $caminho = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'credentials') 'pg_odoo_endpoint.json'
  if (Test-Path $caminho) {
    $e = Read-Utf8JsonFile -Path $caminho
    return @{ url = [string]$e.url; db = [string]$e.db }
  }
  return @{ url = ''; db = '' }
}

function Test-PgOdooKeyIsPlaceholder {
  param([string]$Key)
  return ([string]::IsNullOrWhiteSpace($Key) -or ($Key -match 'COLAR_AQUI'))
}

function Read-PgOdooCredentialFile {
  param([string]$Path)
  # Um ficheiro ilegivel nao pode passar por "sem credenciais": sem esta distincao,
  # um JSON partido manda a cascata para a chave partilhada em silencio e ninguem
  # percebe porque e que a chave pessoal "nao pegou".
  try {
    return (Read-Utf8JsonFile -Path $Path)
  }
  catch {
    throw "Credenciais ilegiveis em '$Path': $($_.Exception.Message)"
  }
}

function Resolve-PgOdooExpiry {
  <#
    Que data guardar no ficheiro da maquina, e so quando ela e CERTA.

    O Odoo nao expoe o indice da chave, pelo que nao ha forma de saber QUAL das chaves
    do utilizador e a que temos em maos. Com uma so chave valida, nao ha duvida. Com
    varias, guardar a mais proxima seria inventar um facto -- e um aviso falso treina
    quem o le a ignorar todos os outros.

    Devolve @{ valor; nota }: `valor` vazio significa "nao guardar nada".
  #>
  param($Chaves)

  $lista = @($Chaves)
  if ($lista.Count -eq 0) {
    return @{ valor = ''; nota = 'nao consegui ler as chaves; validade por determinar' }
  }

  $agora = (Get-Date).ToUniversalTime()
  $validas = @($lista | Where-Object {
      $d = [string]$_.expiration_date
      # expiration_date a false significa persistente.
      if ([string]::IsNullOrWhiteSpace($d) -or $d -eq 'False') { return $true }
      try { return ([datetime]::Parse($d, [Globalization.CultureInfo]::InvariantCulture) -gt $agora) }
      catch { return $true }
    })

  if ($validas.Count -ne 1) {
    return @{ valor = ''
      nota = ("tens {0} chaves validas neste utilizador; nao da para saber qual e esta, " -f $validas.Count) +
             'por isso nao guardo data de validade (o Odoo nao expoe o indice da chave)'
    }
  }

  $d = [string]$validas[0].expiration_date
  if ([string]::IsNullOrWhiteSpace($d) -or $d -eq 'False') {
    return @{ valor = 'persistente'; nota = 'chave persistente (sem validade)' }
  }
  return @{ valor = $d; nota = "valida ate $d (UTC)" }
}

function Assert-ForaDeRepositorio {
  <# Um segredo dentro de um repositorio acaba commitado. Aqui e agora, nao daqui a um ano. #>
  param([string]$Caminho)
  $dir = Split-Path -Parent $Caminho
  $atual = $dir
  while (-not [string]::IsNullOrWhiteSpace($atual)) {
    if (Test-Path (Join-Path $atual '.git')) {
      throw ("RECUSADO: '$Caminho' fica dentro do repositorio '$atual'.`n" +
        "A credencial tem de viver fora de qualquer repositorio. " +
        "Se USERPROFILE aponta para um repositorio, definir PG_ODOO_CREDENTIALS_FILE para um caminho fora dele.")
    }
    $pai = Split-Path -Parent $atual
    if ($pai -eq $atual) { break }
    $atual = $pai
  }
}

function Get-PgOdooCredentialSource {
  # Diz de ONDE viriam as credenciais, sem nunca devolver a chave. E o que o preflight
  # usa para avisar quem ainda esta na chave partilhada -- assim a mudanca chega as
  # outras maquinas pela via por onde o resto da framework ja chega.
  if (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_API_KEY)) {
    return [pscustomobject]@{ kind = 'env'; path = 'env:PG_ODOO_API_KEY'; login = [string]$env:PG_ODOO_LOGIN }
  }
  if (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_KNOWLEDGE_TOKEN)) {
    return [pscustomobject]@{ kind = 'env'; path = 'env:PG_ODOO_KNOWLEDGE_TOKEN'; login = [string]$env:PG_ODOO_LOGIN }
  }

  $maquina = Get-PgOdooMachineCredentialsPath
  if ($maquina -and (Test-Path $maquina)) {
    $c = $null
    try { $c = Read-Utf8JsonFile -Path $maquina } catch { $c = $null }
    if ($c -and -not (Test-PgOdooKeyIsPlaceholder -Key ([string]$c.api_key))) {
      # `expira_em` e escrito no setup quando a chave e identificavel sem ambiguidade.
      # Existe para o preflight poder avisar SEM rede: uma chave que morre a meio de
      # uma sessao custa a manha a quem esta a trabalhar, e o Odoo so diz "uid vazio".
      return [pscustomobject]@{
        kind      = 'maquina'
        path      = $maquina
        login     = [string]$c.login
        expira_em = [string]$c.api_key_expira_em
      }
    }
  }

  # Nao ha degrau legado. A conta de servico foi arquivada a 2026-09-28 e a chave que
  # vivia no repositorio deixou de autenticar -- verificado pela negativa nesse dia.
  # Mante-la na cascata so servia para uma maquina por configurar falhar com "uid vazio",
  # que nao diz a ninguem o que fazer, em vez de falhar a dizer o comando que resolve.
  return [pscustomobject]@{ kind = 'nenhuma'; path = ''; login = '' }
}

function Get-PgOdooCredentials {
  # Devolve url, db, login, api_key e a origem. Lanca com a via de resolucao quando nao
  # ha chave: uma mensagem que nao diga o comando a correr obriga quem a le a procurar
  # documentacao, e e nesse momento que as pessoas desistem.
  param(
    [string]$CredentialsPath,
    [string]$Login,
    [string]$BaseUrl,
    [string]$Database
  )

  $endpoint = Get-PgOdooEndpointDefaults
  $url = $BaseUrl
  $db = $Database
  $log = $Login
  $key = ''
  $origem = ''

  if (-not [string]::IsNullOrWhiteSpace($CredentialsPath)) {
    if (-not (Test-Path $CredentialsPath)) {
      throw "Credenciais nao encontradas em '$CredentialsPath'."
    }
    $dados = Read-PgOdooCredentialFile -Path $CredentialsPath
    if ([string]::IsNullOrWhiteSpace($url)) { $url = [string]$dados.url }
    if ([string]::IsNullOrWhiteSpace($db)) { $db = [string]$dados.db }
    if ([string]::IsNullOrWhiteSpace($log)) { $log = [string]$dados.login }
    $key = [string]$dados.api_key
    $origem = "ficheiro explicito: $CredentialsPath"
  }
  elseif (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_API_KEY)) {
    $key = [string]$env:PG_ODOO_API_KEY
    if ([string]::IsNullOrWhiteSpace($log)) { $log = [string]$env:PG_ODOO_LOGIN }
    $origem = 'env:PG_ODOO_API_KEY'
  }
  elseif (-not [string]::IsNullOrWhiteSpace($env:PG_ODOO_KNOWLEDGE_TOKEN)) {
    $key = [string]$env:PG_ODOO_KNOWLEDGE_TOKEN
    if ([string]::IsNullOrWhiteSpace($log)) { $log = [string]$env:PG_ODOO_LOGIN }
    $origem = 'env:PG_ODOO_KNOWLEDGE_TOKEN (alias legado)'
  }
  else {
    $maquina = Get-PgOdooMachineCredentialsPath
    if ($maquina -and (Test-Path $maquina)) {
      $dados = Read-PgOdooCredentialFile -Path $maquina
      if (-not (Test-PgOdooKeyIsPlaceholder -Key ([string]$dados.api_key))) {
        if ([string]::IsNullOrWhiteSpace($url)) { $url = [string]$dados.url }
        if ([string]::IsNullOrWhiteSpace($db)) { $db = [string]$dados.db }
        if ([string]::IsNullOrWhiteSpace($log)) { $log = [string]$dados.login }
        $key = [string]$dados.api_key
        $origem = "ficheiro da maquina: $maquina"
      }
    }
    # Aqui acabava a cascata numa chave partilhada guardada no repositorio. Saiu a
    # 2026-09-28, depois de a conta de servico ser arquivada e de se provar pela negativa
    # que a chave deixou de autenticar. Sem ela, quem nao tiver credencial recebe o
    # comando que resolve, em vez de um "uid vazio" que nao explica nada.
  }

  if ([string]::IsNullOrWhiteSpace($url)) { $url = $endpoint.url }
  if ([string]::IsNullOrWhiteSpace($db)) { $db = $endpoint.db }

  if (Test-PgOdooKeyIsPlaceholder -Key $key) {
    throw ("Sem credenciais de acesso ao Odoo da Parametro Global nesta maquina.`n" +
      "Resolver com:  " + $script:PgOdooSetupComando + "`n" +
      "Em alternativa, por sessao: definir PG_ODOO_LOGIN e PG_ODOO_API_KEY no ambiente.`n" +
      "Ver credentials/README.md.")
  }
  if ([string]::IsNullOrWhiteSpace($log)) {
    throw ("Chave obtida de '$origem' mas sem login associado. " +
      "Uma chave de um utilizador com o login de outro NAO autentica. " +
      "Definir PG_ODOO_LOGIN no ambiente ou correr: " + $script:PgOdooSetupComando)
  }
  if ([string]::IsNullOrWhiteSpace($url)) {
    throw "Campo 'url' por resolver. Esperado em credentials/pg_odoo_endpoint.json."
  }
  if ([string]::IsNullOrWhiteSpace($db)) {
    throw "Campo 'db' por resolver. Esperado em credentials/pg_odoo_endpoint.json."
  }

  return [pscustomobject]@{
    url     = $url
    db      = $db
    login   = $log
    api_key = $key
    origem  = $origem
  }
}
