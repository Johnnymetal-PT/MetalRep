#!/bin/bash
# pg_mirror_server_code.sh — publica em branches do repositório o código que está
# REALMENTE instalado nos servidores de um cliente.
#
# PORQUE EXISTE
#
#   A fonte de verdade n.º 2 da framework é «código do projeto», e isso pressupõe que o
#   repositório é o que está a correr. Em projetos que fazem patch a um Odoo vivo, essa
#   suposição é falsa e nada a denuncia.
#
#   FACTO OBSERVADO (givachoice, 2026-09-11): o repositório tinha doze árvores de addons
#   de gerações diferentes, e a melhor acertava em 10 dos 29 módulos instalados em
#   produção. A branch de espelho acertava em 29 de 29. Um agente que leia as pastas
#   versionadas para «estabelecer o comportamento atual» conclui sobre código que ninguém
#   está a executar.
#
#   Este script é a generalização do `espelhar_addons_servidor.sh` que o givachoice
#   construiu sozinho e que funciona desde agosto de 2026. Foi promovido à framework por
#   decisão de perímetro de Bruno Pinheiro a 2026-09-11 (backlog PG-010, issue #61): a
#   framework passa a SUPORTAR o trabalho por patch a produção viva, em vez de fingir que
#   o cobre. Só os caminhos eram específicos; tudo o resto já era genérico.
#
# ONDE CORRE
#
#   No servidor do cliente, não na máquina do operador. Precisa de ler as árvores de
#   addons e de empurrar para o repositório — tipicamente por deploy key com «Allow write
#   access». Instala-se uma vez e corre por cron.
#
# O QUE NÃO FAZ
#
#   Não toca nas árvores que espelha. O `.git` de cada espelho vive fora delas (em
#   $PG_MIRROR_DIR), com `core.worktree` a apontar para a árvore — o servidor não fica com
#   repositórios git no meio do código em produção.
#
#   E não escreve nada sem CONFIRMA=1. Sem isso, inspeciona e diz o que faria.
#
# UTILIZAÇÃO
#
#   cp pg_mirror_server_code.conf.exemplo ~/pg_mirror.conf   # e editar
#   bash pg_mirror_server_code.sh                            # inspeção
#   CONFIRMA=1 bash pg_mirror_server_code.sh                 # executa
#   CONFIRMA=1 PG_SEM_CORE=1 bash pg_mirror_server_code.sh   # sem a varredura do core
#
#   O ficheiro de configuração é procurado em $PG_MIRROR_CONF, depois em ~/pg_mirror.conf,
#   depois ao lado deste script.
#
# Dependências: bash, git, coreutils. Nada mais.

set -u

# --- configuração ------------------------------------------------------------
AQUI="$(cd "$(dirname "$0")" && pwd)"
CONF="${PG_MIRROR_CONF:-}"
if [ -z "$CONF" ]; then
  for c in "$HOME/pg_mirror.conf" "$AQUI/pg_mirror.conf"; do
    [ -f "$c" ] && { CONF="$c"; break; }
  done
fi
if [ -z "$CONF" ] || [ ! -f "$CONF" ]; then
  echo "ERRO: ficheiro de configuracao nao encontrado."
  echo "      Procurado em: \$PG_MIRROR_CONF, ~/pg_mirror.conf, $AQUI/pg_mirror.conf"
  echo "      Partir de pg_mirror_server_code.conf.exemplo."
  exit 2
fi
# shellcheck disable=SC1090
. "$CONF"
echo "configuracao: $CONF"

# Um valor em falta aqui produziria um espelho silenciosamente errado -- por exemplo, um
# push para o repositorio de outro cliente. Falhar cedo e barato.
for obrigatorio in PG_REMOTO PG_ARVORES; do
  eval "valor=\${$obrigatorio:-}"
  if [ -z "$valor" ]; then
    echo "ERRO: '$obrigatorio' nao esta definido em $CONF"
    exit 2
  fi
done

PG_MIRROR_DIR="${PG_MIRROR_DIR:-$HOME/mirrors}"
PG_AUTOR_NOME="${PG_AUTOR_NOME:-pg mirror}"
PG_AUTOR_EMAIL="${PG_AUTOR_EMAIL:-it.odoo@parametro.pt}"
PG_RAIZES_CORE="${PG_RAIZES_CORE:-}"
PG_RAMO_CORE="${PG_RAMO_CORE:-live/core-modificado}"
# Um upgrade ou reinstalacao mexe em milhares de ficheiros de uma vez. Copiar isso nao e
# desvio, e ruido: acima deste teto regista-se a ocorrencia e nao se copia.
PG_TETO_DESVIO="${PG_TETO_DESVIO:-200}"

DESVIO="$PG_MIRROR_DIR/core_desvio"
CONFIRMA="${CONFIRMA:-0}"
falhas=0

# --- mecanica ----------------------------------------------------------------
repo_para() {  # $1=nome $2=arvore $3=ramo
  G="$PG_MIRROR_DIR/$1.git"
  if [ ! -d "$G" ]; then
    git init --bare -q "$G"
    git --git-dir="$G" config core.bare false
    git --git-dir="$G" config core.worktree "$2"
    git --git-dir="$G" config user.name "$PG_AUTOR_NOME"
    git --git-dir="$G" config user.email "$PG_AUTOR_EMAIL"
    git --git-dir="$G" symbolic-ref HEAD "refs/heads/$3"
    printf '%s\n' '__pycache__/' '*.py[co]' '*.bak_*' '*.zip' '*.log' '*.sql' '*.dump' \
      > "$G/info/exclude"
    git --git-dir="$G" remote add origin "$PG_REMOTO"
    echo "    repositorio criado em $G (a arvore nao foi tocada)"
  fi
}

publicar() {  # $1=nome $2=arvore $3=ramo
  G="$PG_MIRROR_DIR/$1.git"
  cd "$2" || { echo "    ERRO: cd falhou"; falhas=$((falhas+1)); return; }
  git --git-dir="$G" add -A
  if git --git-dir="$G" diff --cached --quiet; then
    echo "    sem alteracoes desde o ultimo espelho"
  else
    n=$(git --git-dir="$G" diff --cached --name-only | wc -l)
    git --git-dir="$G" commit -q -m "espelho $1 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "    commit $(git --git-dir="$G" rev-parse --short HEAD) com $n ficheiro(s)"
  fi
  if git --git-dir="$G" push -q -u origin "$3" 2>&1; then
    echo "    push OK -> $3"
  else
    echo "    PUSH FALHOU (a deploy key tem 'Allow write access'?)"; falhas=$((falhas+1))
  fi
}

espelhar() {  # $1=nome $2=arvore $3=ramo
  nome="$1"; arvore="$2"; ramo="$3"
  echo; echo "=== $nome  ->  branch $ramo"; echo "    arvore : $arvore"
  if [ ! -d "$arvore" ]; then
    echo "    ERRO: a pasta nao existe"; falhas=$((falhas+1)); return
  fi
  echo "    tamanho: $(du -sh "$arvore" | cut -f1) em $(find "$arvore" -type f | wc -l) ficheiros"
  if [ "$CONFIRMA" != "1" ]; then echo "    (inspeccao: nada foi escrito)"; return; fi
  mkdir -p "$PG_MIRROR_DIR"
  repo_para "$nome" "$arvore" "$ramo"
  publicar "$nome" "$arvore" "$ramo"
}

recolher_desvio() {  # $1=instancia $2=raiz a vigiar
  inst="$1"; raiz="$2"
  [ -d "$raiz" ] || return
  # Inspeccao nao escreve NADA, nem o carimbo. No guiao original do givachoice o carimbo
  # era criado mesmo sem CONFIRMA, e isso tem consequencia: a primeira execucao a serio
  # passava a comparar contra um carimbo posto pela inspeccao, em vez de criar o seu. Um
  # modo que se diz de inspeccao tem de o ser por inteiro, senao ninguem confia nele.
  if [ "$CONFIRMA" != "1" ]; then
    echo "    $raiz: (inspeccao: nada foi escrito)"
    return
  fi
  # PG_SEM_CORE=1 salta esta parte, e e a cara deste guiao: um `git status` sobre o core
  # do Odoo percorre 47 mil ficheiros, e o `find` sobre o Enterprise faz o mesmo gasto. A
  # data de modificacao nao desaparece, portanto isto nao precisa de correr de 15 em 15
  # minutos -- corre uma vez por dia, num cron proprio, e a passagem dos addons fica leve.
  # Motivo: 2026-08-06, suspeita de lentidao do servidor reportada pelo cliente.
  if [ "${PG_SEM_CORE:-0}" = "1" ]; then
    echo "    $raiz: saltado (PG_SEM_CORE=1)"
    return
  fi
  carimbo="$PG_MIRROR_DIR/.carimbo_$(echo "$raiz" | tr '/' '_')"
  # O metodo escolhe-se sozinho: `git status` e exacto mas so existe se a pasta for um
  # repositorio; a data de modificacao serve em qualquer caso.
  if git -C "$raiz" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    metodo="git status"
    lista=$(cd "$raiz" && git status --porcelain --untracked-files=no | awk '{print $NF}')
  else
    metodo="data de modificacao"
    if [ ! -f "$carimbo" ]; then
      touch "$carimbo"
      echo "    $raiz: carimbo criado, sem historico anterior ($metodo)"
      return
    fi
    lista=$(find "$raiz" -type f -newer "$carimbo" ! -path '*__pycache__*' ! -name '*.pyc' \
      2>/dev/null | sed "s|^$raiz/||")
  fi
  n=$(printf '%s' "$lista" | grep -c . || true)
  echo "    $raiz: $n alterado(s) [$metodo]"
  [ "$n" -eq 0 ] && { [ -f "$carimbo" ] && touch "$carimbo"; return; }
  if [ "$n" -gt "$PG_TETO_DESVIO" ]; then
    echo "    $n ficheiros: provavel upgrade/reinstalacao, NAO copiado (teto $PG_TETO_DESVIO)"
    mkdir -p "$DESVIO/$inst"
    { echo "# $(date '+%F %T')  $raiz  $n ficheiros ($metodo) - acima do teto, so a lista"
      echo "$lista"; } > "$DESVIO/$inst/_UPGRADE_$(date '+%Y%m%d_%H%M%S').txt"
  else
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      [ -f "$raiz/$f" ] || continue
      mkdir -p "$DESVIO/$inst/$(dirname "$f")"
      cp -p "$raiz/$f" "$DESVIO/$inst/$f"
    done <<< "$lista"
    { echo "# $(date '+%F %T')  $raiz  $metodo"; echo "$lista"; } >> "$DESVIO/$inst/_INDICE.txt"
  fi
  [ -f "$carimbo" ] && touch "$carimbo"
}

# --- execução ----------------------------------------------------------------
echo "############ addons (o que interessa ao desenvolvimento) ############"
# PG_ARVORES: uma entrada por linha, "nome|caminho|branch".
while IFS='|' read -r nome caminho ramo; do
  case "$nome" in ''|'#'*) continue ;; esac
  espelhar "$(echo "$nome" | tr -d ' ')" "$(echo "$caminho" | tr -d ' ')" "$(echo "$ramo" | tr -d ' ')"
done <<< "$PG_ARVORES"

if [ -n "$PG_RAIZES_CORE" ]; then
  echo
  echo "############ core e Enterprise: so o que estiver alterado ############"
  [ "$CONFIRMA" = "1" ] && mkdir -p "$DESVIO"
  # PG_RAIZES_CORE: uma entrada por linha, "instancia|caminho".
  while IFS='|' read -r inst caminho; do
    case "$inst" in ''|'#'*) continue ;; esac
    recolher_desvio "$(echo "$inst" | tr -d ' ')" "$(echo "$caminho" | tr -d ' ')"
  done <<< "$PG_RAIZES_CORE"
  if [ "$CONFIRMA" = "1" ]; then
    repo_para core_desvio "$DESVIO" "$PG_RAMO_CORE"
    publicar  core_desvio "$DESVIO" "$PG_RAMO_CORE"
  fi
fi

echo
if [ "$CONFIRMA" != "1" ]; then
  echo "INSPECCAO apenas. Para executar: CONFIRMA=1 bash $0"
  exit 0
fi
if [ "$falhas" -eq 0 ]; then
  echo "RESULTADO: ok"
  exit 0
fi
echo "RESULTADO: $falhas falha(s), ver acima"
exit 1
