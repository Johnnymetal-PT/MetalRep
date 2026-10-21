<#
.SYNOPSIS
  Declara os factos de uma pasta de trabalho que NAO e um repositorio da framework.

.DESCRIPTION
  PORQUE EXISTE

  A framework cobre repositorios. Boa parte do trabalho de Odoo acontece noutro sitio:
  pastas de servidor, arvores de addons, copias de migracao. `FACTO OBSERVADO`
  (givachoice, auditoria de 2026-09): as duas migracoes completas da base de producao e o
  desenvolvimento dos modulos custom decorreram em `C:\Odoo\PGAddons`, `C:\Odoo19\pgmodules`
  e `MIGRV18` -- sem `.pg`, sem espelho, sem `AGENTS.md`.

  O agente PROCURA o AGENTS.md nessas pastas: em 46 conversas fe-lo 7 vezes. Nao encontrou
  nada em nenhuma, respondeu "nao existe, continuo", e seguiu sem os factos do projeto.
  O preco esta medido: seis incidentes de confusao entre Odoo 17, 18 e 19, incluindo um
  deploy de codigo v17 sobre o servidor de testes v19, recuperado de um backup manual feito
  por sorte minutos antes. O proprio agente nomeou o que faltava: "um registo persistente e
  sempre consultado a fixar este projeto e v17, servidor X, base Y".

  E isso que este script escreve. Nao cria `.pg`, nao inventa espelho, nao finge que a
  pasta e um repositorio: declara o que e verdade ali, no unico ficheiro que o agente ja
  procura por conta propria.

  BLOCO DELIMITADO, e nao o ficheiro inteiro

  Tudo o que estiver fora dos marcadores e de quem trabalha na pasta e sobrevive a
  qualquer reexecucao. A framework ja destruiu overrides locais uma vez por copiar um
  template por cima (achado D1 da mesma auditoria); aqui nao se repete.

.PARAMETER Path            Pasta de trabalho a declarar.
.PARAMETER Nome            Nome curto do trabalho (ex.: "Givachoice - addons v17").
.PARAMETER OdooVersion     Versao do Odoo desta pasta (ex.: 17.0). Detectada de -OdooSourcePath se omitida.
.PARAMETER OdooSourcePath  Source do Odoo a que esta pasta corresponde; usado para detectar a versao.
.PARAMETER Edicao          community | enterprise.
.PARAMETER Servidor        Servidor/instancia a que esta pasta e servida (ex.: "192.168.0.239:8069").
.PARAMETER BaseDados       Base de dados correspondente (ex.: GIVA17).
.PARAMETER RepoDoProjeto   Caminho do repositorio da framework do projeto, se existir.
.PARAMETER SoLeitura       Pastas/ficheiros que NUNCA se alteram (referencia do cliente, copias de base).
.PARAMETER NaoTocar        Avisos livres do que nao se faz nesta pasta (ex.: "nao reiniciar o servidor").

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pg_init_work_folder.ps1 `
    -Path C:\Odoo\PGAddons -Nome "Givachoice - addons v17" -OdooVersion 17.0 -Edicao enterprise `
    -Servidor "C:\Odoo\server" -BaseDados GIVA17 `
    -SoLeitura C:\Odoo\addons_giva_prod -NaoTocar "nao reiniciar o servidor: pedir ao utilizador"
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$Path,

  [string]$Nome,
  [string]$OdooVersion,
  [string]$OdooSourcePath,
  [ValidateSet('community', 'enterprise')]
  [string]$Edicao,
  [string]$Servidor,
  [string]$BaseDados,
  [string]$RepoDoProjeto,
  [string[]]$SoLeitura,
  [string[]]$NaoTocar,
  [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')

$script:InicioBloco = '<!-- PG_WORK_FOLDER:START (bloco gerido por pg_init_work_folder.ps1 - nao editar aqui) -->'
$script:FimBloco = '<!-- PG_WORK_FOLDER:END (o que estiver fora deste bloco e seu e sobrevive) -->'

function Get-SerieDoSource {
  # A serie REAL, lida do release.py. Declarar a versao a mao e o que falha: e assim que
  # se acaba a citar documentacao de uma versao e a ler o codigo de outra.
  param([string]$CaminhoSource)

  if ([string]::IsNullOrWhiteSpace($CaminhoSource)) { return $null }

  foreach ($tentativa in @(
      (Join-Path $CaminhoSource 'odoo\release.py'),
      (Join-Path $CaminhoSource 'community\odoo\release.py'),
      (Join-Path $CaminhoSource 'release.py'))) {
    if (-not (Test-Path $tentativa)) { continue }
    try { $texto = Get-Content -Path $tentativa -Raw -Encoding UTF8 } catch { continue }
    if ($texto -match 'version_info\s*=\s*\(\s*[''"]?(\d+)[''"]?\s*,\s*(\d+)') {
      return ("{0}.{1}" -f $Matches[1], $Matches[2])
    }
  }
  return $null
}

$pasta = [System.IO.Path]::GetFullPath($Path)
if (-not (Test-Path $pasta)) { throw "Pasta nao encontrada: $pasta" }

# Uma pasta que JA e repositorio da framework nao precisa disto -- e sobrepor-lhe o
# AGENTS.md do projeto seria estragar o contrato que ela ja tem.
if ((Test-Path (Join-Path $pasta '.pg')) -or (Test-Path (Join-Path $pasta 'PG_CONTEXT.md'))) {
  throw "'$pasta' ja e um repositorio da framework (tem .pg/ ou PG_CONTEXT.md). Este script e para pastas de trabalho que NAO sao repositorios; aqui usar o bootstrap normal."
}

$serieDetectada = Get-SerieDoSource -CaminhoSource $OdooSourcePath
if ($serieDetectada -and $OdooVersion -and ($serieDetectada -ne $OdooVersion)) {
  throw "Incoerencia: declarou -OdooVersion $OdooVersion mas o source em '$OdooSourcePath' e $serieDetectada. Um dos dois esta errado, e e exactamente esta divergencia que este ficheiro existe para impedir."
}
$versao = if ($OdooVersion) { $OdooVersion } elseif ($serieDetectada) { $serieDetectada } else { $null }

if (-not $versao) {
  Write-Host "AVISO: versao do Odoo nao declarada nem detectavel. E o facto mais caro de todos -- indicar -OdooVersion ou -OdooSourcePath."
}

# ---------------------------------------------------------------------------
# Construcao do bloco
# ---------------------------------------------------------------------------
$linhas = New-Object System.Collections.Generic.List[string]
$linhas.Add($script:InicioBloco)
$linhas.Add('')
$linhas.Add('# ' + $(if ($Nome) { $Nome } else { Split-Path -Leaf $pasta }))
$linhas.Add('')
$linhas.Add('**Esta pasta NAO e um repositorio da framework.** Nao tem `.pg/`, nao tem espelho do')
$linhas.Add('Odoo e nao tem branch Brodoo. O ritual de arranque nao se aplica aqui: o que se aplica')
$linhas.Add('sao os factos abaixo, e eles tem precedencia sobre qualquer suposicao.')
$linhas.Add('')
$linhas.Add('## Factos desta pasta')
$linhas.Add('')
if ($versao) { $linhas.Add('Versao do Odoo: ' + $versao) }
if ($Edicao) { $linhas.Add('Edicao: ' + $Edicao) }
if ($Servidor) { $linhas.Add('Servidor: ' + $Servidor) }
if ($BaseDados) { $linhas.Add('Base de dados: ' + $BaseDados) }
if ($OdooSourcePath) { $linhas.Add('Path do core: ' + $OdooSourcePath) }
if ($RepoDoProjeto) { $linhas.Add('Repositorio do projeto: ' + $RepoDoProjeto) }
$linhas.Add('')
$linhas.Add('> Se uma sessao retomada ou um resumo automatico disser outra versao, outro servidor')
$linhas.Add('> ou outra base, **este bloco e que manda**. Um resumo de compactacao ja reintroduziu')
$linhas.Add('> a versao errada duas semanas depois de corrigida, por nao reler as notas do projeto.')
$linhas.Add('')

if ($SoLeitura -and $SoLeitura.Count -gt 0) {
  $linhas.Add('## So leitura — nunca alterar')
  $linhas.Add('')
  foreach ($item in $SoLeitura) { $linhas.Add('- `' + $item + '`') }
  $linhas.Add('')
}

if ($NaoTocar -and $NaoTocar.Count -gt 0) {
  $linhas.Add('## Nao fazer nesta pasta')
  $linhas.Add('')
  foreach ($item in $NaoTocar) { $linhas.Add('- ' + $item) }
  $linhas.Add('')
}

$linhas.Add('## Antes de alterar o que ja funciona')
$linhas.Add('')
$linhas.Add('Vale aqui a mesma regra do metodo partilhado: sao dois riscos e o ensaio so apanha um.')
$linhas.Add('*Isto parte alguma coisa?* apanha-se com resguardo e verificacao. *Isto e o que eles')
$linhas.Add('querem?* nenhum ensaio apanha -- procurar a origem do pedido, e dizer que nao se')
$linhas.Add('encontrou em vez de assumir que nao existe. Uma correccao que ninguem pediu passa uma')
$linhas.Add('barra mais alta, nao mais baixa por ser pequena.')
$linhas.Add('')
$linhas.Add($script:FimBloco)

$bloco = ($linhas -join [Environment]::NewLine)

# ---------------------------------------------------------------------------
# Escrita: substituir o bloco, preservar o resto
# ---------------------------------------------------------------------------
$destino = Join-Path $pasta 'AGENTS.md'
$existente = if (Test-Path $destino) { Read-Utf8TextFile -Path $destino } else { $null }

if ([string]::IsNullOrWhiteSpace($existente)) {
  $novo = $bloco + [Environment]::NewLine
}
else {
  $normalizado = ($existente -replace "`r`n", "`n" -replace "`r", "`n")
  $padrao = [regex]::Escape($script:InicioBloco) + ".*?" + [regex]::Escape($script:FimBloco)
  if ([regex]::IsMatch($normalizado, $padrao, [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
    # MatchEvaluator e nao string de substituicao: um '$' num caminho seria lido como
    # referencia de grupo.
    $avaliador = { param($m) return $bloco }
    $novo = [regex]::Replace($normalizado, $padrao, $avaliador, [System.Text.RegularExpressions.RegexOptions]::Singleline)
  }
  else {
    # Ficheiro que ja existia sem bloco: o bloco entra no topo, porque e o que tem de ser
    # lido primeiro, e o conteudo de quem la trabalha fica intacto por baixo.
    $novo = $bloco + [Environment]::NewLine + [Environment]::NewLine + $normalizado.TrimStart("`n")
  }
}

if ($WhatIf) {
  Write-Host "WHATIF: escreveria o bloco de factos em $destino"
  Write-Host ""
  Write-Host $bloco
  exit 0
}

if ($existente -ceq $novo) {
  Write-Host "OK: $destino ja declara estes factos (nada a escrever)"
  exit 0
}

Write-Utf8NoBomFile -Path $destino -Content $novo
Write-Host "OK: factos declarados em $destino"
if ($versao) { Write-Host "  Versao do Odoo : $versao$(if ($serieDetectada) { ' (confirmada no source)' })" }
if ($Servidor) { Write-Host "  Servidor       : $Servidor" }
if ($BaseDados) { Write-Host "  Base de dados  : $BaseDados" }
if ($SoLeitura) { Write-Host "  So leitura     : $($SoLeitura.Count) caminho(s)" }
Write-Host "  O que estiver fora do bloco delimitado nao foi tocado."
exit 0
