<#
.SYNOPSIS
  Resolve o nome REAL da base de dados de uma instancia Odoo, do canal mais barato
  para o mais caro: 1) HTTP /web/database/list  ->  2) SSH (Odoo.sh).

.DESCRIPTION
  O External API (JSON-RPC) exige o nome da BD como 1.o argumento de authenticate/
  execute_kw e NAO o consegue derivar de url+login+api_key. Em SaaS/Odoo.sh o nome
  tambem NAO e o subdominio (ex.: dominio 'cartonagemsaotiago.odoo.com' -> BD
  'parametroglobaladmin-cst1-producao-25532973'). Em Odoo.sh o nome = build e MUDA a
  cada rebuild, pelo que o 'database' guardado em pg.odoo.connection e uma cache.

  Este helper resolve o nome atual tentando, por ordem:
    1) POST /web/database/list (HTTP, anonimo, instantaneo) -- so precisa de -BaseUrl.
       Se devolver exatamente 1 BD, e o nome. E o caminho preferido (rapido/barato).
    2) SSH 'psql -tAc "select current_database()"' -- fallback robusto quando o
       endpoint HTTP esta bloqueado (list_db=False) ou devolve varias BDs (ambiguo).
       Usa a chave SSH/conta GitHub do OPERADOR (sem segredos novos).

  Imprime SO o nome da BD no stdout (progresso vai para o stream de aviso).

.PARAMETER BaseUrl
  URL base da instancia-alvo (ex.: https://cliente.odoo.com/). Ativa a tentativa HTTP.

.PARAMETER SshTarget
  (Opcional) Destino SSH (user@host) da instancia-alvo, da UI "Connect" da branch no
  Odoo.sh. Ativa o fallback SSH. Em Odoo.sh o alvo e, tipicamente, por build, pelo que
  deve ser obtido no momento (a sintaxe exata nao e adivinhada: e recebida aqui).

.PARAMETER SshCommand
  Override do comando remoto. Default: psql -tAc "select current_database()".

.PARAMETER SshOptions
  Opcoes extra a passar ao ssh (array), p.ex. @('-i','C:\caminho\chave').

.EXAMPLE
  # Caso rapido: resolve via HTTP (nenhum SSH necessario)
  pg_odoo_resolve_db.ps1 -BaseUrl https://cartonagemsaotiago.odoo.com/

.EXAMPLE
  # Com fallback SSH (instancias que bloqueiam /web/database/list)
  pg_odoo_resolve_db.ps1 -BaseUrl https://cliente.odoo.com/ `
    -SshTarget cliente-main-12345678@cliente-main-12345678.dev.odoo.com

.NOTES
  - Pelo menos um de -BaseUrl / -SshTarget tem de ser dado.
  - E o caminho read_mode='api'/shell (caro face ao espelho): usar SO quando o nome
    guardado falhou a autenticacao (nova build) ou nao existe.
  - PONTO POR VALIDAR: o /web/database/list depende da config (list_db) da instancia;
    quando fechado, so o SSH resolve.
#>
param(
  [string]$BaseUrl,
  [string]$SshTarget,
  [string]$SshCommand,
  [string[]]$SshOptions
)

$ErrorActionPreference = 'Stop'

# Normalizar o BaseUrl recebido: sufixo '/odoo' (URL do backoffice em Odoo 17+),
# barra final e esquema em falta. Sem isto o /web/database/list responde 400.
$BaseUrl = ([string]$BaseUrl).Trim().TrimEnd('/')
if ($BaseUrl.ToLower().EndsWith('/odoo')) { $BaseUrl = $BaseUrl.Substring(0, $BaseUrl.Length - 5).TrimEnd('/') }
if ($BaseUrl -and $BaseUrl -notmatch '^https?://') { $BaseUrl = "https://$BaseUrl" }

function Test-DbName {
  param([string]$Name)
  return ($Name -match '^[A-Za-z0-9][A-Za-z0-9._-]*$')
}

function Resolve-ViaHttp {
  param([string]$Url)
  $endpoint = ($Url.TrimEnd('/')) + '/web/database/list'
  $body = @{ jsonrpc = '2.0'; method = 'call'; params = @{} } | ConvertTo-Json -Compress
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json' -Body $body -TimeoutSec 30
  }
  catch {
    Write-Warning "HTTP /web/database/list indisponivel ($($_.Exception.Message))."
    return $null
  }
  if ($resp.error) { Write-Warning "HTTP /web/database/list recusado: $($resp.error.data.message)"; return $null }
  $dbs = @($resp.result | Where-Object { Test-DbName $_ })
  if ($dbs.Count -eq 1) { return $dbs[0] }
  if ($dbs.Count -eq 0) { Write-Warning 'HTTP /web/database/list nao devolveu BDs.'; return $null }
  Write-Warning "HTTP /web/database/list devolveu varias BDs (ambiguo): $($dbs -join ', '). A tentar SSH se disponivel."
  return $null
}

function Resolve-ViaSsh {
  param([string]$Target, [string]$Cmd, [string[]]$Opts)
  $sshExe = 'ssh'
  if (-not (Get-Command $sshExe -ErrorAction SilentlyContinue)) {
    throw "Cliente 'ssh' nao encontrado no PATH (OpenSSH)."
  }
  $remoteCmd = if ([string]::IsNullOrWhiteSpace($Cmd)) { 'psql -tAc "select current_database()"' } else { $Cmd }
  $sshArgs = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'LogLevel=ERROR', '-o', 'ConnectTimeout=20')
  if ($Opts) { $sshArgs += $Opts }
  $sshArgs += $Target
  $sshArgs += $remoteCmd
  Write-Warning "A resolver via SSH: $Target"
  $raw = & $sshExe @sshArgs 2>&1
  if ($LASTEXITCODE -ne 0) { throw "SSH falhou (exit $LASTEXITCODE) para '$Target': $($raw -join ' ')" }
  $cands = @($raw | ForEach-Object { ([string]$_).Trim() } | Where-Object { Test-DbName $_ })
  if ($cands.Count -eq 0) { throw "SSH nao devolveu um nome de BD valido: '$($raw -join ' ')'." }
  return $cands[-1]
}

try {
  if ([string]::IsNullOrWhiteSpace($BaseUrl) -and [string]::IsNullOrWhiteSpace($SshTarget)) {
    throw 'Indicar pelo menos -BaseUrl (tentativa HTTP) ou -SshTarget (fallback SSH).'
  }

  $dbName = $null

  # 1) HTTP (preferido)
  if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) {
    $dbName = Resolve-ViaHttp -Url $BaseUrl
  }

  # 2) SSH (fallback)
  if ([string]::IsNullOrWhiteSpace($dbName)) {
    if (-not [string]::IsNullOrWhiteSpace($SshTarget)) {
      $dbName = Resolve-ViaSsh -Target $SshTarget -Cmd $SshCommand -Opts $SshOptions
    }
    else {
      throw "Nao foi possivel resolver a BD via HTTP para '$BaseUrl' (endpoint bloqueado/ambiguo) e nao foi dado -SshTarget para o fallback SSH."
    }
  }

  Write-Output $dbName
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
