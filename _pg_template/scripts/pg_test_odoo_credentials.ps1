<#
.SYNOPSIS
  Testes da cascata de resolucao das credenciais do Odoo da Parametro Global.

.DESCRIPTION
  A cascata decide QUE chave e usada para falar com o Odoo PG -- e, por essa via, para
  ler as credenciais dos Odoo dos clientes. Uma regressao aqui nao da erro: da a chave
  errada, em silencio, e isso so se descobre quando uma escrita aparece assinada por
  outra pessoa.

  Os testes correm contra uma COPIA da framework numa pasta temporaria, sem
  credentials/brodoo_credentials.json. E a unica forma de exercitar dois casos que na
  arvore real nao se conseguem alcancar -- "nada configurado" e "so a chave da maquina"
  -- porque a chave partilhada existe no repositorio e ganharia sempre a seguir.

  Sem rede: o que se testa e a decisao, nao a autenticacao.
#>
param()

$ErrorActionPreference = "Stop"

function Assert-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { throw "FALHOU: $Message" }
}

function Assert-Contains {
  param([string]$Text, [string]$Expected, [string]$Message)
  $haystack = if ($null -eq $Text) { '' } else { $Text }
  if (-not $haystack.Contains($Expected)) { throw "FALHOU: $Message (texto: $haystack)" }
}

function Assert-Throws {
  param([scriptblock]$Accao, [string]$EsperadoNoErro, [string]$Message)
  $erro = $null
  try { & $Accao | Out-Null }
  catch { $erro = $_.Exception.Message }
  if ($null -eq $erro) { throw "FALHOU: $Message (nao lancou excepcao)" }
  Assert-Contains -Text $erro -Expected $EsperadoNoErro -Message $Message
}

$envOriginal = @{
  PG_ODOO_API_KEY         = $env:PG_ODOO_API_KEY
  PG_ODOO_LOGIN           = $env:PG_ODOO_LOGIN
  PG_ODOO_KNOWLEDGE_TOKEN = $env:PG_ODOO_KNOWLEDGE_TOKEN
  PG_ODOO_CREDENTIALS_FILE = $env:PG_ODOO_CREDENTIALS_FILE
}

function Clear-PgEnv {
  Remove-Item Env:PG_ODOO_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:PG_ODOO_LOGIN -ErrorAction SilentlyContinue
  Remove-Item Env:PG_ODOO_KNOWLEDGE_TOKEN -ErrorAction SilentlyContinue
  Remove-Item Env:PG_ODOO_CREDENTIALS_FILE -ErrorAction SilentlyContinue
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pg_test_cred_" + [System.Guid]::NewGuid().ToString("N"))

try {
  Write-Host "=== pg_test_odoo_credentials ==="

  # --- framework de mentira: scripts + endpoint, SEM a chave partilhada ---------------
  $fakeScripts = Join-Path $tempRoot 'scripts'
  $fakeCredenciais = Join-Path $tempRoot 'credentials'
  New-Item -ItemType Directory -Path $fakeScripts -Force | Out-Null
  New-Item -ItemType Directory -Path $fakeCredenciais -Force | Out-Null
  Copy-Item (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1') $fakeScripts
  Copy-Item (Join-Path $PSScriptRoot 'pg_file_io_common.ps1') $fakeScripts

  $urlEsperada = 'https://exemplo-endpoint.odoo.com'
  $dbEsperada = 'base-de-teste-123'
  (@{ url = $urlEsperada; db = $dbEsperada } | ConvertTo-Json) |
    Set-Content -Path (Join-Path $fakeCredenciais 'pg_odoo_endpoint.json') -Encoding utf8

  Clear-PgEnv
  . (Join-Path $fakeScripts 'pg_odoo_credentials_common.ps1')

  Assert-True -Condition (-not (Test-Path (Get-PgOdooLegacyCredentialsPath))) `
    -Message 'a framework de teste nao pode ter a chave partilhada (senao ganha sempre)'

  # --- 1) nada configurado: erro que DIZ O COMANDO -----------------------------------
  # Uma mensagem que nao diga o que correr obriga quem a le a ir procurar documentacao,
  # e e nesse momento que as pessoas desistem e pedem a chave de outra pessoa.
  $env:PG_ODOO_CREDENTIALS_FILE = Join-Path $tempRoot 'nao_existe.json'
  Assert-Throws -Accao { Get-PgOdooCredentials } `
    -EsperadoNoErro 'pg_init_odoo_credentials.ps1' `
    -Message 'sem credencial nenhuma, o erro nomeia o comando de configuracao'
  Assert-True -Condition ((Get-PgOdooCredentialSource).kind -eq 'nenhuma') `
    -Message 'sem credencial nenhuma, a origem e "nenhuma"'

  # --- 2) ficheiro da maquina: so login+chave; url e db vem do endpoint partilhado ----
  $ficheiroMaquina = Join-Path $tempRoot 'odoo_credentials.json'
  (@{ login = 'pessoa@parametro.global'; api_key = 'chave-da-maquina' } | ConvertTo-Json) |
    Set-Content -Path $ficheiroMaquina -Encoding utf8
  $env:PG_ODOO_CREDENTIALS_FILE = $ficheiroMaquina

  $c = Get-PgOdooCredentials
  Assert-True -Condition ($c.api_key -eq 'chave-da-maquina') -Message 'usa a chave da maquina'
  Assert-True -Condition ($c.login -eq 'pessoa@parametro.global') -Message 'usa o login da maquina'
  Assert-True -Condition ($c.url -eq $urlEsperada) -Message 'url vem do endpoint versionado'
  Assert-True -Condition ($c.db -eq $dbEsperada) -Message 'db vem do endpoint versionado'
  Assert-Contains -Text $c.origem -Expected 'ficheiro da maquina' -Message 'origem identifica o ficheiro da maquina'

  # --- 3) a variavel de ambiente vence o ficheiro -------------------------------------
  $env:PG_ODOO_API_KEY = 'chave-do-ambiente'
  $env:PG_ODOO_LOGIN = 'outra.pessoa@parametro.global'
  $c = Get-PgOdooCredentials
  Assert-True -Condition ($c.api_key -eq 'chave-do-ambiente') -Message 'o ambiente vence o ficheiro da maquina'
  Assert-True -Condition ($c.login -eq 'outra.pessoa@parametro.global') -Message 'o login do ambiente acompanha a chave do ambiente'
  Assert-True -Condition ((Get-PgOdooCredentialSource).kind -eq 'env') -Message 'origem do ambiente reportada como env'

  # --- 4) -CredentialsPath explicito vence o ambiente --------------------------------
  # Mantem o contrato antigo dos helpers: quem passa o caminho espera que seja usado.
  $explicito = Join-Path $tempRoot 'explicito.json'
  (@{ login = 'explicita@parametro.global'; api_key = 'chave-explicita' } | ConvertTo-Json) |
    Set-Content -Path $explicito -Encoding utf8
  $c = Get-PgOdooCredentials -CredentialsPath $explicito
  Assert-True -Condition ($c.api_key -eq 'chave-explicita') -Message 'o caminho explicito vence o ambiente'
  Clear-PgEnv
  $env:PG_ODOO_CREDENTIALS_FILE = $ficheiroMaquina

  # --- 5) o alias legado continua aceite ---------------------------------------------
  # Havia quem usasse PG_ODOO_KNOWLEDGE_TOKEN; retira-lo silenciosamente partia essas
  # maquinas sem nenhuma mensagem que ligasse a causa ao efeito.
  $env:PG_ODOO_KNOWLEDGE_TOKEN = 'chave-legada'
  $env:PG_ODOO_LOGIN = 'legado@parametro.global'
  $c = Get-PgOdooCredentials
  Assert-True -Condition ($c.api_key -eq 'chave-legada') -Message 'PG_ODOO_KNOWLEDGE_TOKEN continua a ser aceite'
  Clear-PgEnv
  $env:PG_ODOO_CREDENTIALS_FILE = $ficheiroMaquina

  # --- 6) chave sem login associado: erro explicito ----------------------------------
  # Uma chave de um utilizador com o login de outro NAO autentica, e o erro do Odoo
  # ("uid vazio") nao sugere nunca que o problema e o login.
  $semLogin = Join-Path $tempRoot 'sem_login.json'
  (@{ api_key = 'chave-sem-dono' } | ConvertTo-Json) | Set-Content -Path $semLogin -Encoding utf8
  $env:PG_ODOO_CREDENTIALS_FILE = $semLogin
  Assert-Throws -Accao { Get-PgOdooCredentials } -EsperadoNoErro 'login' `
    -Message 'chave sem login da um erro que fala do login'
  $env:PG_ODOO_CREDENTIALS_FILE = $ficheiroMaquina

  # --- 7) placeholder nao conta como chave -------------------------------------------
  $placeholder = Join-Path $tempRoot 'placeholder.json'
  (@{ login = 'x@parametro.global'; api_key = 'COLAR_AQUI_A_API_KEY' } | ConvertTo-Json) |
    Set-Content -Path $placeholder -Encoding utf8
  $env:PG_ODOO_CREDENTIALS_FILE = $placeholder
  Assert-Throws -Accao { Get-PgOdooCredentials } -EsperadoNoErro 'pg_init_odoo_credentials.ps1' `
    -Message 'placeholder nao conta como chave configurada'
  Assert-True -Condition ((Get-PgOdooCredentialSource).kind -eq 'nenhuma') `
    -Message 'placeholder nao aparece como origem valida'

  # --- 8) ficheiro partido NAO passa por "nada configurado" --------------------------
  # Sem esta distincao, um JSON com virgula a mais mandava a cascata para a chave
  # partilhada em silencio e ninguem percebia porque e que a chave pessoal nao pegou.
  $partido = Join-Path $tempRoot 'partido.json'
  '{ "login": "x@parametro.global", "api_key": ' | Set-Content -Path $partido -Encoding utf8
  $env:PG_ODOO_CREDENTIALS_FILE = $partido
  Assert-Throws -Accao { Get-PgOdooCredentials } -EsperadoNoErro 'ilegiveis' `
    -Message 'ficheiro de credenciais partido da erro proprio, nao cai para a via seguinte'

  # --- 9) a origem NUNCA devolve a chave ---------------------------------------------
  # E lida pelo preflight, que escreve o resultado em .pg/PREFLIGHT.json -- ficheiro
  # versionado. Uma chave aqui era uma chave commitada.
  $env:PG_ODOO_CREDENTIALS_FILE = $ficheiroMaquina
  $origem = Get-PgOdooCredentialSource
  $propriedades = @($origem.PSObject.Properties.Name)
  Assert-True -Condition (-not ($propriedades -contains 'api_key')) `
    -Message 'a origem nao expoe o campo api_key'
  $serializada = ($origem | ConvertTo-Json -Compress)
  Assert-True -Condition (-not $serializada.Contains('chave-da-maquina')) `
    -Message 'a origem serializada nao contem a chave'

  # --- 10) validade: com UMA chave valida, a data e certa e guarda-se -----------------
  # Em Odoo 19 so quem tem o grupo Definicoes cria chaves persistentes; as outras
  # expiram. Sem esta data guardada, o preflight nao consegue avisar sem rede, e a
  # chave morre a meio de uma sessao com um "uid vazio" que nao fala de datas.
  $futuro = (Get-Date).ToUniversalTime().AddDays(60).ToString('yyyy-MM-dd HH:mm:ss')
  $r = Resolve-PgOdooExpiry -Chaves @([pscustomobject]@{ name = 'PG'; expiration_date = $futuro })
  Assert-True -Condition ($r.valor -eq $futuro) -Message 'uma chave valida da a data certa'

  $r = Resolve-PgOdooExpiry -Chaves @([pscustomobject]@{ name = 'PG'; expiration_date = $false })
  Assert-True -Condition ($r.valor -eq 'persistente') -Message 'chave sem validade fica marcada como persistente'

  # --- 11) validade: com DUAS validas nao se inventa -----------------------------------
  # O Odoo nao expoe o indice da chave, pelo que nao ha como saber qual delas e esta.
  # Guardar a mais proxima seria inventar um facto, e um aviso falso treina quem o le a
  # ignorar todos os outros.
  $r = Resolve-PgOdooExpiry -Chaves @(
    [pscustomobject]@{ name = 'A'; expiration_date = $futuro },
    [pscustomobject]@{ name = 'B'; expiration_date = $false })
  Assert-True -Condition ([string]::IsNullOrWhiteSpace($r.valor)) -Message 'com duas chaves validas nao se guarda data'
  Assert-Contains -Text $r.nota -Expected 'nao da para saber qual' -Message 'e explica-se porque nao se guarda'

  # --- 12) validade: uma chave expirada nao cria ambiguidade --------------------------
  $passado = (Get-Date).ToUniversalTime().AddDays(-3).ToString('yyyy-MM-dd HH:mm:ss')
  $r = Resolve-PgOdooExpiry -Chaves @(
    [pscustomobject]@{ name = 'velha'; expiration_date = $passado },
    [pscustomobject]@{ name = 'nova'; expiration_date = $futuro })
  Assert-True -Condition ($r.valor -eq $futuro) -Message 'chave ja expirada nao conta para a ambiguidade'

  $r = Resolve-PgOdooExpiry -Chaves @()
  Assert-True -Condition ([string]::IsNullOrWhiteSpace($r.valor)) -Message 'sem chaves lidas nao se guarda data'

  # --- 13) a origem transporta a validade guardada, e continua sem a chave ------------
  $comValidade = Join-Path $tempRoot 'com_validade.json'
  (@{ login = 'p@parametro.global'; api_key = 'k'; api_key_expira_em = $futuro } | ConvertTo-Json) |
    Set-Content -Path $comValidade -Encoding utf8
  $env:PG_ODOO_CREDENTIALS_FILE = $comValidade
  $origem = Get-PgOdooCredentialSource
  Assert-True -Condition ($origem.expira_em -eq $futuro) -Message 'a origem transporta a validade para o preflight'
  Assert-True -Condition (-not ($origem | ConvertTo-Json -Compress).Contains('"api_key"')) `
    -Message 'a origem continua sem expor a chave'

  # --- 14) recusa escrever dentro de um repositorio -----------------------------------
  # Um segredo dentro de um repositorio acaba commitado; a questao e so quando.
  $repoFalso = Join-Path $tempRoot 'repo_falso'
  New-Item -ItemType Directory -Path (Join-Path $repoFalso '.git') -Force | Out-Null
  Assert-Throws -Accao { Assert-ForaDeRepositorio -Caminho (Join-Path $repoFalso 'odoo_credentials.json') } `
    -EsperadoNoErro 'RECUSADO' -Message 'recusa escrever a credencial dentro de um repositorio'
  Assert-Throws -Accao { Assert-ForaDeRepositorio -Caminho (Join-Path $repoFalso 'sub\mais\fundo.json') } `
    -EsperadoNoErro 'RECUSADO' -Message 'recusa tambem em subpastas do repositorio'
  $foraDeTudo = Join-Path $tempRoot 'fora\credencial.json'
  New-Item -ItemType Directory -Path (Split-Path -Parent $foraDeTudo) -Force | Out-Null
  Assert-ForaDeRepositorio -Caminho $foraDeTudo

  Write-Host "OK: 19 verificacoes da cascata de credenciais passaram"
}
finally {
  Clear-PgEnv
  foreach ($k in $envOriginal.Keys) {
    if (-not [string]::IsNullOrWhiteSpace($envOriginal[$k])) {
      Set-Item -Path ("Env:" + $k) -Value $envOriginal[$k]
    }
  }
  if (Test-Path $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

exit 0
