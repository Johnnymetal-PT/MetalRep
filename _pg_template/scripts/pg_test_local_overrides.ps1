<#
.SYNOPSIS
  Testes da preservacao dos overrides locais do AGENTS.md / CLAUDE.md no sync.

.DESCRIPTION
  O AGENTS.md diz de si proprio que serve "para registar overrides locais quando
  existirem", e ate 2026-09-11 o sync copiava o template por cima dele com -Force.
  `FACTO OBSERVADO` (givachoice, 11/08/2026): um re-sync apagou 41 linhas do AGENTS.md
  do projeto -- a seccao que dizia onde estava o codigo vivo dos servidores. A equipa
  deixou de confiar no ficheiro e passou a guardar as regras locais em memorias do
  agente, que nao viajam com o repositorio.

  Auditoria: docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md, achado D1.
#>
param()

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'pg_file_io_common.ps1')

$script:Total = 0

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:Total += 1
  if (-not $Condition) { throw "FALHA: $Message" }
  Write-Host "  OK   $Message"
}

$template = @"
# AGENTS - Projeto

## Ritual
Correr o ritual.

## Overrides locais do projeto
- [Sem overrides locais neste momento]
"@

try {
  Write-Host "=== preservacao de overrides locais ==="

  # --- projeto com overrides reais: sobrevivem -----------------------------
  $comOverrides = @"
# AGENTS - Projeto (versao antiga)

## Ritual
Texto antigo do ritual, que deve ser substituido pelo template.

## Overrides locais do projeto
- O codigo vivo dos servidores esta em origin/live/producao e origin/live/testes.
- Correr sempre auditoria_v19\pg_check_live_drift.ps1 antes de ler codigo.
"@

  $resultado = Merge-PgLocalOverrides -ExistingContent $comOverrides -FrameworkContent $template

  Assert-True ($resultado -like '*origin/live/producao*') 'o override local sobrevive ao sync'
  Assert-True ($resultado -like '*pg_check_live_drift*') 'o override inteiro sobrevive, nao so a primeira linha'
  Assert-True ($resultado -like '*Correr o ritual.*') 'o conteudo do template entra'
  Assert-True ($resultado -notlike '*Texto antigo do ritual*') 'o conteudo antigo fora do bloco de overrides e substituido'
  Assert-True ($resultado -notlike '*Sem overrides locais neste momento*') 'o marcador de vazio do template nao fica colado ao override real'
  $ocorrencias = ([regex]::Matches($resultado, [regex]::Escape('## Overrides locais do projeto'))).Count
  Assert-True ($ocorrencias -eq 1) 'o cabecalho dos overrides aparece uma unica vez'

  # --- projeto sem overrides: nada a preservar -----------------------------
  $semOverrides = @"
# AGENTS - Projeto

## Overrides locais do projeto
- [Sem overrides locais neste momento]
"@
  $r2 = Merge-PgLocalOverrides -ExistingContent $semOverrides -FrameworkContent $template
  Assert-True ($r2 -eq $template) 'um bloco por estrear nao conta como override (sem reescrita inutil)'

  # --- ficheiro inexistente ------------------------------------------------
  $r3 = Merge-PgLocalOverrides -ExistingContent $null -FrameworkContent $template
  Assert-True ($r3 -eq $template) 'sem ficheiro no destino, o template passa tal e qual'

  # --- ficheiro sem o cabecalho de overrides -------------------------------
  $r4 = Merge-PgLocalOverrides -ExistingContent "# Outro ficheiro`n`nsem seccao de overrides" -FrameworkContent $template
  Assert-True ($r4 -eq $template) 'sem cabecalho de overrides nao ha nada a preservar'

  # --- idempotencia --------------------------------------------------------
  $r5 = Merge-PgLocalOverrides -ExistingContent $resultado -FrameworkContent $template
  Assert-True ($r5 -eq $resultado) 'correr o sync duas vezes da o mesmo resultado'

  # --- o defeito original: sem preservacao, o override morre ---------------
  # Prova negativa: e isto que acontecia antes, e que os testes acima impedem.
  Assert-True ($template -notlike '*origin/live/producao*') 'o template nao contem o override -- sem merge, o sync apagava-o'

  Write-Host ""
  Write-Host "OK: $($script:Total) verificacoes passaram."
  exit 0
}
catch {
  Write-Host ""
  Write-Host "$_"
  exit 1
}
