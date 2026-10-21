<#
  evo_ler.ps1 — acesso a' base EVOSTONE no Odoo.sh para analise, sem confirmacao
  manual a cada ida e volta.

  PORQUE EXISTE
  A analise desta base precisa de dezenas de leituras remotas. Autorizar `ssh *`
  resolvia isso, mas tambem autorizava qualquer comando destrutivo — e o travao
  das confirmacoes ja evitou hoje um `TRUNCATE CASCADE` que teria alcancado o
  `ir_model_data`. Este involucro liberta a leitura sem libertar a escrita.

  O QUE GARANTE A LEITURA
  Nao e' a expressao regular abaixo — essa e' a segunda rede. A garantia e' do
  proprio PostgreSQL: o guiao corre dentro de `START TRANSACTION READ ONLY` com
  `default_transaction_read_only = on` na sessao. Qualquer escrita e' recusada
  pelo motor, ainda que passe pelo filtro de texto.

  O ALVO E' VALIDADO
  Aceita `<id>@parametroglobaladmin-evostone[-<algo>.dev].odoo.com`. O nome do
  host NAO identifica a base: o encaminhamento do Odoo.sh e' feito pelo id do
  build, e o painel da' o nome curto para a producao. Foi isto que me levou uma
  vez a dar producao por verificada quando lia outra base — usei o nome curto
  com um id de staging, e culpei o nome em vez do id.

  A protecao deixou de ser o nome e passou a ser uma medicao: cada leitura
  imprime `current_database()` como primeira linha do resultado. Nenhuma
  leitura deve ser citada sem se ler essa linha.

  LIMITE HONESTO
  A regra de permissao aponta para este ficheiro, que e' editavel. Se o conteudo
  mudar, a regra passa a cobrir o conteudo novo. O travao esta na disciplina de
  nao transformar este guiao em executor de escritas — nao numa impossibilidade.

    MODOS
      ler      (por defeito)  corre um guiao SQL ou uma consulta, em leitura
      enviar                  copia um ficheiro local para /home/odoo/
      trazer                  copia um ficheiro de /home/odoo/ para local

    EXEMPLOS
      ... -Alvo 37056070@...dev.odoo.com -Consulta "select count(*) from res_users"
      ... -Alvo <alvo> -Guiao C:\tmp\evo_backup\contagens.sql
      ... -Alvo <alvo> -Modo enviar -Ficheiro C:\tmp\evo_backup\evo_crons.py
      ... -Alvo <alvo> -Modo trazer -Ficheiro relatorio.txt -Destino C:\tmp\evo_backup
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Alvo,
    [ValidateSet('ler', 'enviar', 'trazer', 'conferir')][string]$Modo = 'ler',
    [string]$Guiao,
    [string]$Consulta,
    [string]$Ficheiro,
    [string]$Destino
)

$ErrorActionPreference = 'Stop'

# O `ssh` do PATH nao serve. Quando este guiao e' lancado a partir de um shell do
# Git, o PATH resolve para `C:\Program Files\Git\usr\bin\ssh.exe`, que NAO fala
# com o ssh-agent do Windows — onde vive a chave. Sem identidade, devolve
# `Permission denied (publickey)`, que e' indistinguivel de uma chave recusada
# pelo servidor. Custou-me uma manha a perseguir o host, o build, o IP e as
# chaves registadas, quando o defeito era o binario. Fixa-se.
$sshExe = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
$scpExe = Join-Path $env:SystemRoot 'System32\OpenSSH\scp.exe'
foreach ($b in @($sshExe, $scpExe)) {
    if (-not (Test-Path -LiteralPath $b)) {
        Write-Error "PARADO: OpenSSH do Windows nao encontrado -> $b"
        exit 2
    }
}

# --- 1. O alvo e' um build deste projeto? -----------------------------------
$padraoAlvo = '^[0-9]{5,10}@parametroglobaladmin-evostone(-[a-z0-9\-]+\.dev)?\.odoo\.com$'
if ($Alvo -notmatch $padraoAlvo) {
    Write-Error @"
PARADO: alvo recusado -> $Alvo
Formato aceite: <id>@parametroglobaladmin-evostone-<algo>.dev.odoo.com
Producao: 37056070@parametroglobaladmin-evostone-main-37056070.dev.odoo.com
Nota: parametroglobaladmin-evostone.odoo.com esta fora de proposito — o SSH
desse nome vai para o staging, nao para a producao.
"@
    exit 2
}

# --- 2. Conferir o que esta em /home/odoo/ ----------------------------------
# Comando fixo, nao arbitrario: tamanho, data e md5 dos ficheiros de trabalho.
# Serve para confirmar que um envio chegou inteiro, sem abrir a porta a shell.
if ($Modo -eq 'conferir') {
    $cmd = 'cd /home/odoo && ls -l --time-style=long-iso *.sh *.py *.sql *.csv ' +
           '*.tsv *.txt *.json *.log *.xlsx 2>/dev/null; echo "--- md5 ---"; ' +
           'md5sum evo_*.sh evo_limpar_*.sql *.csv *.txt 2>/dev/null'
    Write-Output "=== $Alvo / conferir /home/odoo ==="
    & $sshExe -o StrictHostKeyChecking=accept-new -o BatchMode=yes $Alvo $cmd
    $c = $LASTEXITCODE
    Write-Output "CONFERIR=FIM (codigo $c)"
    exit $c
}

# --- 3. Modos de copia ------------------------------------------------------
if ($Modo -eq 'enviar') {
    if (-not $Ficheiro) { Write-Error 'PARADO: -Ficheiro e obrigatorio no modo enviar.'; exit 2 }
    if (-not (Test-Path -LiteralPath $Ficheiro)) { Write-Error "PARADO: nao existe -> $Ficheiro"; exit 2 }
    $nome = Split-Path -Leaf $Ficheiro
    if ($nome -notmatch '^[A-Za-z0-9._\-]+$') {
        Write-Error "PARADO: nome de ficheiro recusado -> $nome"; exit 2
    }
    Write-Output "enviar: $Ficheiro -> ${Alvo}:/home/odoo/$nome"
    # -O forca o protocolo SCP antigo: o servidor do Odoo.sh nao oferece o
    # subsistema sftp que o scp moderno usa por omissao ("subsystem request
    # failed on channel 0").
    & $scpExe -O -o StrictHostKeyChecking=accept-new $Ficheiro "${Alvo}:/home/odoo/$nome"
    exit $LASTEXITCODE
}

if ($Modo -eq 'trazer') {
    if (-not $Ficheiro) { Write-Error 'PARADO: -Ficheiro e obrigatorio no modo trazer.'; exit 2 }
    if ($Ficheiro -notmatch '^[A-Za-z0-9._\-]+$') {
        Write-Error "PARADO: so o nome do ficheiro em /home/odoo/, sem caminho -> $Ficheiro"; exit 2
    }
    if (-not $Destino) { $Destino = 'C:\tmp\evo_backup' }
    # Sem isto, o scp trata um destino inexistente como *nome de ficheiro* e
    # grava o conteudo num ficheiro chamado, por exemplo, `logs`. Custou-me uma
    # leitura confusa.
    if (-not (Test-Path -LiteralPath $Destino -PathType Container)) {
        if (Test-Path -LiteralPath $Destino) {
            Write-Error "PARADO: $Destino existe e nao e uma pasta."; exit 2
        }
        New-Item -ItemType Directory -Path $Destino -Force | Out-Null
        Write-Output "pasta criada: $Destino"
    }
    Write-Output "trazer: ${Alvo}:/home/odoo/$Ficheiro -> $Destino"
    # -O forca o protocolo SCP antigo: o servidor do Odoo.sh nao oferece o
    # subsistema sftp que o scp moderno usa por omissao ("subsystem request
    # failed on channel 0").
    & $scpExe -O -o StrictHostKeyChecking=accept-new "${Alvo}:/home/odoo/$Ficheiro" $Destino
    exit $LASTEXITCODE
}

# --- 3. Modo ler ------------------------------------------------------------
if ($Guiao -and $Consulta) { Write-Error 'PARADO: use -Guiao ou -Consulta, nao os dois.'; exit 2 }
if ($Guiao) {
    if (-not (Test-Path -LiteralPath $Guiao)) { Write-Error "PARADO: nao existe -> $Guiao"; exit 2 }
    $sql = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $Guiao))
    $origem = $Guiao
}
elseif ($Consulta) {
    $sql = $Consulta
    $origem = '(consulta directa)'
}
else {
    Write-Error 'PARADO: falta -Guiao ou -Consulta.'; exit 2
}

# Os comentarios saem antes do filtro: um guiao de verificacao pode explicar em
# palavras o que uma limpeza apagaria, e isso nao e' motivo para o recusar.
$semComentarios = [regex]::Replace($sql, '/\*.*?\*/', ' ', 'Singleline')
$semComentarios = [regex]::Replace($semComentarios, '--[^\r\n]*', ' ')

$proibidos = '\b(delete|update|insert|truncate|drop|alter|create|grant|revoke|' +
             'reindex|vacuum|cluster|copy|commit|checkpoint|call)\b' +
             '|default_transaction_read_only|\bread\s+write\b|\bdo\b\s*\$'
$achado = [regex]::Match($semComentarios, $proibidos, 'IgnoreCase')
if ($achado.Success) {
    Write-Error @"
PARADO: o guiao contem '$($achado.Value)', que nao pertence a uma leitura.
Este caminho serve analise. Escritas sobre a producao continuam a passar por
confirmacao explicita — nao por aqui.
  origem: $origem
"@
    exit 2
}

# A garantia real: transaccao de leitura imposta pelo motor.
#
# `SET client_encoding` mais o $OutputEncoding abaixo: sem os dois, o PowerShell
# 5.1 codifica o canal para um executavel nativo na pagina de codigo da consola
# e o UTF-8 chega estragado. Custou-me uma leitura errada — 12 distritos deram
# «FALTA» por `Evora` ter viajado como `?vora` e nao casar com o que esta na
# base. Um resultado que parecia dizer que faltavam distritos dizia so que o
# meu canal estava mal codificado.
# O `ROLLBACK;` e' colado depois do guiao. Se este nao terminar em ponto e
# virgula, os dois juntam-se e o PostgreSQL da' «syntax error at or near
# ROLLBACK» — que e' uma mensagem que aponta para o sitio errado e faz perder
# tempo. Fecha-se aqui, em vez de depender de eu me lembrar.
$sqlFechado = $sql.TrimEnd()
if ($sqlFechado -and -not $sqlFechado.EndsWith(';')) { $sqlFechado += ';' }

$carga = @"
SET client_encoding TO 'UTF8';
SET default_transaction_read_only = on;
START TRANSACTION READ ONLY;
SELECT current_database() AS base_lida;
$sqlFechado
ROLLBACK;
"@

$OutputEncoding = New-Object System.Text.UTF8Encoding $false

$remoto = 'test -n "$PGDATABASE" || { echo "PARADO: PGDATABASE nao definido na sessao remota" >&2; exit 3; }; ' +
          'psql -d "$PGDATABASE" -v ON_ERROR_STOP=1 -P pager=off -f -'

Write-Output "=== $Alvo / leitura / $origem ==="
$carga | & $sshExe -o StrictHostKeyChecking=accept-new -o BatchMode=yes $Alvo $remoto
$codigo = $LASTEXITCODE
Write-Output "LER=FIM (codigo $codigo)"
exit $codigo
