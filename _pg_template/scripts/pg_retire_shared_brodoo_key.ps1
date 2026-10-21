<#
.SYNOPSIS
  Retira de circulacao a chave partilhada do utilizador de servico Brodoo (PG-011, F5).

.DESCRIPTION
  A chave partilhada esteve no historico do git, em todos os clones da equipa, e o
  utilizador Brodoo tem `base.group_system`: e uma chave de ADMINISTRADOR do Odoo da
  Parametro Global. Apagar o ficheiro nunca revogou nada -- a revogacao e do lado do Odoo,
  e e isso que este script faz e prova.

  TRES MODOS, e o primeiro e o default:

    (sem opcoes)         relatorio de prontidao. Nao escreve nada.
    -Revogar -Confirmar  revoga a chave que esta no ficheiro legado e prova pela negativa.
    -Provar              so a prova pela negativa, sem revogar nada.

  PORQUE E QUE A CHAVE SE REVOGA A SI PROPRIA
    `res.users.apikeys.revoke(key)` e `@api.model`, chamavel por RPC, e exige
    `_ensure_can_manage_keys_programmatically()` -- ou seja, `env.is_system()`. Como a
    chave partilhada e de administrador, ela propria satisfaz esse requisito. Nao e
    preciso pedir a ninguem uma credencial de admin para a retirar de circulacao.

  O QUE ESTE SCRIPT NAO FAZ, E PORQUE
    Nao arquiva o utilizador Brodoo nem apaga as outras chaves dele.

    - `res.users.apikeys` nao tem ACL de eliminacao para ninguem (so leitura, em
      `ir.model.access.csv`), e o `remove()` do core tem `@check_identity`, que pede a
      password e nao funciona por RPC. Uma chave de que nao se tenha o valor so se apaga
      pela interface.
    - arquivar o utilizador e a accao que mata TODAS as chaves de uma vez (o `_login` faz
      um `search` normal, pelo que um utilizador arquivado nao e encontrado). Mas e uma
      accao que deve ficar registada em nome de uma PESSOA, nao da conta que se esta a
      retirar. O relatorio final diz exactamente o que falta e a quem pedir.

.PARAMETER Revogar
  Executa a revogacao. Sem -Confirmar nao escreve nada.

.PARAMETER Confirmar
  Confirma a execucao. Obrigatorio com -Revogar.

.PARAMETER Provar
  So corre a prova pela negativa: tenta autenticar com a chave legada e espera que falhe.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_retire_shared_brodoo_key.ps1

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_retire_shared_brodoo_key.ps1 -Revogar -Confirmar
#>
param(
  [switch]$Revogar,
  [switch]$Confirmar,
  [switch]$Provar
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_odoo_credentials_common.ps1')

function Invoke-Rpc {
  param([string]$Url, [string]$CorpoJson)
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($CorpoJson)
  $resp = Invoke-RestMethod -Method Post -Uri (($Url.TrimEnd('/')) + '/jsonrpc') `
    -ContentType 'application/json; charset=utf-8' -Body $bytes
  return $resp
}

function Invoke-Autenticar {
  <# Devolve o uid, ou $null se a autenticacao falhar. NAO lanca: a falha e um resultado. #>
  param([string]$Url, [string]$Db, [string]$Login, [string]$Key)
  $corpo = @{ jsonrpc = '2.0'; method = 'call'; params = @{
      service = 'common'; method = 'authenticate'; args = @($Db, $Login, $Key, @{}) } } |
    ConvertTo-Json -Depth 20 -Compress
  try { $r = Invoke-Rpc -Url $Url -CorpoJson $corpo } catch { return $null }
  if ($r.error) { return $null }
  if (-not $r.result -or $r.result -eq $false) { return $null }
  return [int]$r.result
}

function Invoke-ExecuteKw {
  param([string]$Url, [string]$Db, [int]$Uid, [string]$Key,
    [string]$Modelo, [string]$Metodo, [string]$PosicionaisJson, [string]$KwargsJson = '{}')
  # JSON literal: o ConvertTo-Json do PowerShell achata arrays aninhados, e um dominio
  # achatado chega ao Odoo como "invalid item in domain".
  $argumentos = '["' + $Db + '",' + $Uid + ',"' + $Key + '","' + $Modelo + '","' + $Metodo + '",' +
    $PosicionaisJson + ',' + $KwargsJson + ']'
  $corpo = '{"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":' + $argumentos + '}}'
  $r = Invoke-Rpc -Url $Url -CorpoJson $corpo
  if ($r.error) {
    $msg = $r.error.data.message
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $r.error.message }
    throw "Odoo recusou ${Modelo}.${Metodo}: $msg"
  }
  return $r.result
}

function Get-ChaveLegada {
  <# Le o ficheiro legado directamente, e NAO pela cascata: o que interessa aqui e a
     chave que se quer retirar, nao a que a maquina usa para trabalhar. #>
  $caminho = Get-PgOdooLegacyCredentialsPath
  if (-not (Test-Path $caminho)) { return $null }
  $c = Read-Utf8JsonFile -Path $caminho
  if (Test-PgOdooKeyIsPlaceholder -Key ([string]$c.api_key)) { return $null }
  return [pscustomobject]@{
    caminho = $caminho
    login   = [string]$c.login
    api_key = [string]$c.api_key
    url     = [string]$c.url
    db      = [string]$c.db
  }
}

function Test-ProvaPelaNegativa {
  <#
    "Revogado com sucesso" e afirmacao ate alguem verificar. Isto verifica: tenta
    autenticar com a chave antiga e espera FALHAR. Sucesso aqui e a autenticacao recusada.
  #>
  param($Legada, [string]$Url, [string]$Db)
  Write-Host ''
  Write-Host '=== prova pela negativa ==='
  Write-Host ("  a tentar autenticar com a chave legada ({0}) ..." -f $Legada.login)
  $uid = Invoke-Autenticar -Url $Url -Db $Db -Login $Legada.login -Key $Legada.api_key
  if ($null -eq $uid) {
    Write-Host '  RECUSADA -- a chave legada ja nao autentica.'
    Write-Host '  FACTO OBSERVADO: a chave que esteve no historico do git deixou de dar acesso.'
    return $true
  }
  Write-Host ("  ACEITE (uid {0}) -- a chave legada CONTINUA VALIDA." -f $uid)
  Write-Host '  A revogacao NAO esta completa. Ver os passos em falta acima.'
  return $false
}

try {
  $endpoint = Get-PgOdooEndpointDefaults
  $legada = Get-ChaveLegada

  if ($Provar) {
    if (-not $legada) { throw 'Sem ficheiro legado nesta arvore: nao ha chave antiga para testar.' }
    $ok = Test-ProvaPelaNegativa -Legada $legada -Url $endpoint.url -Db $endpoint.db
    exit $(if ($ok) { 0 } else { 2 })
  }

  # --- credencial desta maquina: tem de ser propria -----------------------------------
  # Correr isto a partir da chave partilhada seria serrar o ramo em que se esta sentado:
  # a seguir a revogacao, a propria maquina deixava de conseguir falar com o Odoo.
  $origem = Get-PgOdooCredentialSource
  Write-Host ''
  Write-Host '=== pg_retire_shared_brodoo_key ==='
  Write-Host ("  credencial desta maquina : {0}" -f $origem.kind)
  if ($origem.kind -eq 'legado' -or $origem.kind -eq 'nenhuma') {
    Write-Host ''
    Write-Host '  BLOQUEADO: esta maquina ainda depende da chave partilhada (ou nao tem credencial).'
    Write-Host ("  Configurar a chave desta maquina primeiro: {0}" -f (Get-PgOdooSetupCommand))
    exit 1
  }

  $eu = Get-PgOdooCredentials
  $meuUid = Invoke-Autenticar -Url $eu.url -Db $eu.db -Login $eu.login -Key $eu.api_key
  if ($null -eq $meuUid) { throw "A credencial desta maquina nao autentica ($($eu.login))." }
  $euNome = @(Invoke-ExecuteKw -Url $eu.url -Db $eu.db -Uid $meuUid -Key $eu.api_key `
      -Modelo 'res.users' -Metodo 'read' -PosicionaisJson ("[[$meuUid],[`"name`"]]"))
  Write-Host ("  a correr como            : {0} (uid {1})" -f $euNome[0].name, $meuUid)

  $souAdmin = Invoke-ExecuteKw -Url $eu.url -Db $eu.db -Uid $meuUid -Key $eu.api_key `
    -Modelo 'res.users' -Metodo 'has_group' -PosicionaisJson ("[[$meuUid],`"base.group_system`"]")
  Write-Host ("  tenho Administracao      : {0}" -f $(if ($souAdmin) { 'sim' } else { 'nao' }))

  # --- estado da conta de servico ------------------------------------------------------
  if (-not $legada) {
    Write-Host ''
    Write-Host '  O ficheiro legado ja nao existe nesta arvore.'
    Write-Host '  ATENCAO: isso NAO prova revogacao -- a chave continua no historico do git.'
    Write-Host '  Confirmar o estado da conta de servico no Odoo antes de dar a F5 por fechada.'
    exit 0
  }

  Write-Host ("  ficheiro legado          : {0}" -f $legada.caminho)
  $conta = @(Invoke-ExecuteKw -Url $eu.url -Db $eu.db -Uid $meuUid -Key $eu.api_key `
      -Modelo 'res.users' -Metodo 'search_read' `
      -PosicionaisJson ('[[["login","=","' + $legada.login + '"],["active","in",[true,false]]],["id","name","active"]]'))
  if ($conta.Count -eq 0) {
    Write-Host ("  conta de servico         : '{0}' nao encontrada" -f $legada.login)
  }
  else {
    Write-Host ("  conta de servico         : {0} (uid {1}), activa={2}" -f $conta[0].name, $conta[0].id, $conta[0].active)
  }

  # As chaves de outro utilizador so sao visiveis a quem tem Administracao (regra de
  # registo `api_key_admin`). Sem isso, dizer "tem N chaves" seria dizer o que nao se sabe.
  if ($souAdmin -and $conta.Count -gt 0) {
    $chaves = @(Invoke-ExecuteKw -Url $eu.url -Db $eu.db -Uid $meuUid -Key $eu.api_key `
        -Modelo 'res.users.apikeys' -Metodo 'search_read' `
        -PosicionaisJson ('[[["user_id","=",' + $conta[0].id + ']],["id","name","expiration_date"]]'))
    Write-Host ("  chaves da conta          : {0}" -f $chaves.Count)
    foreach ($k in $chaves) { Write-Host ("     - id={0} {1}" -f $k.id, $k.name) }
  }
  else {
    Write-Host '  chaves da conta          : (so visiveis a quem tem Administracao)'
  }

  if (-not $Revogar) {
    Write-Host ''
    Write-Host '  MODO RELATORIO: nada foi escrito.'
    Write-Host '  Para revogar a chave deste ficheiro:  -Revogar -Confirmar'
    exit 0
  }

  if (-not $Confirmar) {
    Write-Host ''
    Write-Host '  DRY-RUN: -Revogar sem -Confirmar nao escreve nada.'
    Write-Host ('  Seria revogada a chave contida em ' + $legada.caminho)
    exit 0
  }

  # --- revogacao -----------------------------------------------------------------------
  Write-Host ''
  Write-Host '=== revogacao ==='
  $uidLegado = Invoke-Autenticar -Url $endpoint.url -Db $endpoint.db -Login $legada.login -Key $legada.api_key
  if ($null -eq $uidLegado) {
    Write-Host '  A chave legada ja nao autentica: nada a revogar.'
    $null = Test-ProvaPelaNegativa -Legada $legada -Url $endpoint.url -Db $endpoint.db
    exit 0
  }
  Write-Host ("  a chave legada autentica como uid {0}; a revoga-la com ela propria..." -f $uidLegado)
  $resultado = Invoke-ExecuteKw -Url $endpoint.url -Db $endpoint.db -Uid $uidLegado -Key $legada.api_key `
    -Modelo 'res.users.apikeys' -Metodo 'revoke' -PosicionaisJson ('["' + $legada.api_key + '"]')
  Write-Host ("  revoke devolveu: {0}" -f $resultado)

  $provou = Test-ProvaPelaNegativa -Legada $legada -Url $endpoint.url -Db $endpoint.db

  Write-Host ''
  Write-Host '=== o que falta, e nao pode ser feito por aqui ==='
  Write-Host '  1. ARQUIVAR a conta de servico no Odoo (Definicoes > Utilizadores > Brodoo > Arquivar).'
  Write-Host '     E o que mata as restantes chaves de uma vez: um utilizador arquivado nao e'
  Write-Host '     encontrado pelo _login, logo nenhuma chave dele autentica.'
  Write-Host '  2. Apagar as chaves restantes dessa conta pela interface. O modelo nao tem ACL de'
  Write-Host '     eliminacao e o remove() do core pede a password, pelo que nao ha via por RPC.'
  Write-Host '  3. Remover do repositorio o ficheiro legado e o degrau legado da cascata,'
  Write-Host '     e so DEPOIS de a prova pela negativa passar.'
  Write-Host ''
  Write-Host '  Lembrete: apagar o ficheiro nunca revogou nada. A chave esta no historico do git.'

  exit $(if ($provou) { 0 } else { 2 })
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
