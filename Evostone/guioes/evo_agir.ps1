<#
  evo_agir.ps1 — corre guioes que ESCREVEM, e so' contra bases de staging.

  PORQUE EXISTE, E PORQUE E' SEPARADO DO evo_ler.ps1
  O `evo_ler.ps1` foi escrito de proposito sem caminho para escrever, e essa
  decisao mantem-se para a producao: la' as escritas passam por confirmacao.

  O staging e' outro caso, e a distincao e' material:
    - e' descartavel — um `Rebuild` refaz a copia da producao em minutos;
    - esta neutralizado pelo Odoo.sh — o correio a sair e as tarefas
      automaticas estao desligados, portanto nada chega ao cliente;
    - e' apagado a 26/09/2026 com o fim da avaliacao;
    - o proposito de um ensaio e' precisamente quebrar coisas e aprender.

  A cautela que se justifica na producao nao se justifica aqui, e tratar os dois
  da mesma forma tornava o staging inutil.

  O LIMITE ESTA EM DOIS SITIOS, NAO NUM
    1. o nome do host tem de conter `-staging-`;
    2. e o guiao confirma, **na propria base**, que `current_database()` contem
       `-staging-` antes de correr qualquer coisa.

  Um host pode ser mal escrito; o nome da base que responde nao. Se os dois nao
  concordarem, nao corre. E' a licao da armadilha de 03/09, em que o HTTPS de um
  nome apontava para producao e o SSH do mesmo nome para staging.

    USO
      ... -Alvo <id>@parametroglobaladmin-evostone-staging-<id>.dev.odoo.com `
          -Guiao C:\tmp\evo_backup\evo_ensaio_pt.py -Fase medir
      ... -Alvo <alvo> -Guiao <py> -Fase desinstalar -Escrever
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Alvo,
    [Parameter(Mandatory = $true)][string]$Guiao,
    [string]$Fase = 'medir',
    [switch]$Escrever,
    # Abre o alvo a' producao. Nao esta' aqui para me poupar teclas: esta' aqui
    # para que escrever na producao seja um acto declarado, visivel no comando e
    # no historico, e nunca o resultado de eu ter escrito o host errado.
    # Autorizado pelo gestor de projeto em 04/09/2026, depois de a sequencia
    # inteira passar no staging.
    [switch]$Producao,
    # Confirmacao de conteudo, para guioes que decidem algo que nao se apura
    # lendo a base — por exemplo o mapeamento de contas das categorias de
    # artigo, em que o lado da venda depende do que a empresa faz com a pedra.
    #
    # E' deliberadamente um valor e nao um `switch`: quem confirma fica escrito
    # no comando e no historico. `-Confirmado maria` nao e' o mesmo que
    # `-Confirmado bruno`, e o guiao exige o valor que espera.
    [string]$Confirmado
)

$ErrorActionPreference = 'Stop'

# Mesmo defeito que o `evo_ler.ps1` teve em 04/09/2026: lancado a partir de um
# shell do Git, o PATH resolve `ssh` para o do Git, que nao fala com o ssh-agent
# do Windows. Sem identidade, `Permission denied (publickey)` — indistinguivel
# de uma chave recusada pelo servidor. Fixa-se o binario.
$sshExe = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
$scpExe = Join-Path $env:SystemRoot 'System32\OpenSSH\scp.exe'
foreach ($b in @($sshExe, $scpExe)) {
    if (-not (Test-Path -LiteralPath $b)) {
        Write-Error "PARADO: OpenSSH do Windows nao encontrado -> $b"
        exit 2
    }
}
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

# --- 1. O alvo e' staging, ou producao declarada? ------------------------
$padraoStaging = '^[0-9]{5,10}@parametroglobaladmin-evostone-staging-[0-9]{5,10}\.dev\.odoo\.com$'
$padraoProducao = '^[0-9]{5,10}@parametroglobaladmin-evostone(-main-[0-9]{5,10}\.dev)?\.odoo\.com$'

if ($Alvo -match $padraoStaging) {
    # caminho normal
}
elseif ($Producao -and $Alvo -match $padraoProducao) {
    Write-Output ''
    Write-Output '  ###############################################################'
    Write-Output '  #                  ESCRITA EM PRODUCAO                        #'
    Write-Output "  #  alvo: $Alvo"
    Write-Output "  #  fase: $Fase   escrever: $(if ($Escrever) { 'SIM' } else { 'nao, e ensaio' })"
    Write-Output '  ###############################################################'
    Write-Output ''
}
else {
    Write-Error @"
PARADO: este invólucro escreve.
Alvo recusado -> $Alvo
Staging (livre):   <id>@parametroglobaladmin-evostone-staging-<id>.dev.odoo.com
Producao (exige -Producao): <id>@parametroglobaladmin-evostone[-main-<id>.dev].odoo.com
Sem o -Producao, um host de producao e' recusado. E' de proposito: escrever na
producao tem de ser um acto declarado no comando, e nao o efeito de um host
trocado. Para ler a producao existe o evo_ler.ps1, que nao escreve.
"@
    exit 2
}

if (-not (Test-Path -LiteralPath $Guiao)) {
    Write-Error "PARADO: nao existe -> $Guiao"; exit 2
}
$nome = Split-Path -Leaf $Guiao
if ($nome -notmatch '^[A-Za-z0-9._\-]+\.py$') {
    Write-Error "PARADO: o guiao tem de ser um .py com nome simples -> $nome"; exit 2
}

# --- 2. Enviar o guiao ---------------------------------------------------
Write-Output "=== $Alvo ==="
Write-Output "enviar: $Guiao"
& $scpExe -O -o StrictHostKeyChecking=accept-new $Guiao "${Alvo}:/home/odoo/$nome"
if ($LASTEXITCODE -ne 0) { Write-Error 'PARADO: o envio falhou.'; exit $LASTEXITCODE }

# --- 3. Confirmar na base que e' staging, e correr -----------------------
# O comando remoto vai num FICHEIRO, nao por argumento.
#
# Passar um comando com aspas por argumento a um executavel nativo nao funciona
# em PowerShell: o parser da linha de comandos come as aspas duplas e o `sh`
# remoto recebe `echo fase: medir escrever: nao (ensaio)` sem elas, engasgando-se
# no parentese. E' a mesma armadilha que quebrou a consulta ao Odoo com o JSON
# do dominio. Um ficheiro nao tem este problema, e nao precisa de escapamento
# nenhum.
$modo = if ($Escrever) { '1' } else { '' }
$etiqueta = if ($Escrever) { 'SIM' } else { 'nao, e ensaio' }

# A confirmacao remota da base espelha a decisao local: em staging aceita so'
# staging; com -Producao aceita so' a base `-main-`. O que nao muda e' haver
# sempre uma confirmacao do lado da base, para que um host trocado nao chegue a
# executar nada.
if ($Producao) {
    $conferirBase = @(
        'case "$PGDATABASE" in',
        '  *-main-*) : ;;',
        '  *) echo "PARADO: -Producao mas a base nao e a main. Nada corre." >&2; exit 4 ;;',
        'esac')
    # Os guioes exigem esta variavel do seu lado. Vem daqui, e nao do ambiente,
    # para nao poder ficar ligada por esquecimento numa sessao seguinte.
    $extra = "PRODUCAO=confirmo "
} else {
    $conferirBase = @(
        'case "$PGDATABASE" in',
        '  *-staging-*) : ;;',
        '  *) echo "PARADO: a base nao e de staging. Nada corre." >&2; exit 4 ;;',
        'esac')
    $extra = ''
}

if ($Confirmado) {
    # Vai para o ambiente do guiao remoto, e nao para o da maquina, pela mesma
    # razao do PRODUCAO: para nao poder ficar ligado por esquecimento.
    $extra += "CONFIRMADO='$Confirmado' "
    Write-Output "  confirmado por: $Confirmado"
}

$linhas = @(
    'set -u',
    'test -n "$PGDATABASE" || { echo "PARADO: PGDATABASE nao definido" >&2; exit 3; }'
) + $conferirBase + @(
    'echo "base confirmada: $PGDATABASE"',
    "echo 'fase: $Fase   escrever: $etiqueta'",
    'echo ""',
    "FASE='$Fase' ESCREVER='$modo' ${extra}bash /home/odoo/evo_run_shell.sh /home/odoo/$nome"
)
$tmp = Join-Path $env:TEMP 'evo_agir_remoto.sh'
[System.IO.File]::WriteAllText($tmp, ($linhas -join "`n") + "`n",
                               (New-Object System.Text.UTF8Encoding $false))
& $scpExe -O -o StrictHostKeyChecking=accept-new $tmp "${Alvo}:/home/odoo/_agir.sh"
if ($LASTEXITCODE -ne 0) { Write-Error 'PARADO: nao consegui enviar o comando.'; exit $LASTEXITCODE }

& $sshExe -o StrictHostKeyChecking=accept-new -o BatchMode=yes $Alvo 'bash /home/odoo/_agir.sh'
$codigo = $LASTEXITCODE
Write-Output ''
Write-Output "AGIR=FIM (codigo $codigo)"
exit $codigo
