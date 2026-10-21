#!/bin/bash
# Testes do pg_export_db_objects.sh.
#
# O script corre no servidor de um cliente e fala com o Odoo de lá. O que se testa aqui é
# tudo o resto, que é onde estão os defeitos que custam caro: leitura da configuração,
# deteção de falhas, e sobretudo a regra de NÃO publicar quando uma instância falhou.
#
# Essa regra é a razão de ser destes testes. No guião original o stderr ia para
# /dev/null e uma instância falhada passava despercebida: o script seguia e publicava a
# árvore da execução anterior como se fosse fresca. Um espelho parado não avisa que
# envelheceu — e um diff vazio passaria por «nada mudou».
#
# O Odoo é substituído por um executável de mentira que escreve ficheiros e imprime a
# linha EXPORTADO, que é exatamente o contrato que o script espera.
#
# Correr:  bash scripts/tests/test_pg_export_db_objects.sh

set -u

AQUI="$(cd "$(dirname "$0")" && pwd)"
ALVO="$AQUI/../server/pg_export_db_objects.sh"
[ -f "$ALVO" ] || { echo "FALHOU: nao encontrei $ALVO"; exit 1; }

RAIZ="$(mktemp -d "${TMPDIR:-/tmp}/pg_test_objbd.XXXXXX")"
trap 'rm -rf "$RAIZ"' EXIT

passou=0
falhou=0

verificar() {  # $1=descricao $2=condicao(0/1)
  if [ "$2" -eq 0 ]; then
    passou=$((passou+1))
  else
    echo "  FALHOU: $1"
    falhou=$((falhou+1))
  fi
}

contem() {  # $1=descricao $2=texto $3=esperado
  case "$2" in
    *"$3"*) verificar "$1" 0 ;;
    *) echo "  FALHOU: $1 (esperava '$3')"; verificar "$1" 1 ;;
  esac
}

nao_contem() {  # $1=descricao $2=texto $3=proibido
  case "$2" in
    *"$3"*) echo "  FALHOU: $1 (nao devia conter '$3')"; verificar "$1" 1 ;;
    *) verificar "$1" 0 ;;
  esac
}

# --- cenario ------------------------------------------------------------------
criar_instancia() {  # $1=nome
  local r="$RAIZ/inst_$1"
  mkdir -p "$r/Server" "$r/python-venv/bin"
  printf '#!/bin/bash\n' > "$r/Server/odoo-bin"
  printf 'db = teste\n' > "$r/odoo.conf"
  # Odoo de mentira: consome o guiao pelo stdin, escreve o que o exportador escreveria,
  # e imprime a linha EXPORTADO -- o contrato que o script procura.
  cat > "$r/python-venv/bin/python3.12" <<'FAKE'
#!/bin/bash
cat > /dev/null
mkdir -p "$PG_DEST/accoes_servidor"
printf '# accao\n' > "$PG_DEST/accoes_servidor/1_teste.py"
printf '# resumo\n' > "$PG_DEST/_RESUMO.md"
echo "EXPORTADO $PG_DEST :: accoes de servidor=1"
FAKE
  chmod +x "$r/python-venv/bin/python3.12"
  printf '%s\n' "$r"
}

INST_A="$(criar_instancia a)"
INST_B="$(criar_instancia b)"

REMOTO="$RAIZ/remoto.git"
git init --bare -q "$REMOTO"

CONF="$RAIZ/pg_mirror.conf"
cat > "$CONF" <<EOF
PG_REMOTO="$REMOTO"
PG_MIRROR_DIR="$RAIZ/mirrors"
PG_INSTANCIAS="
producao | $INST_A | BASE_A
testes   | $INST_B | BASE_B
"
EOF

correr() { PG_MIRROR_CONF="$CONF" CONFIRMA="${CONFIRMA:-0}" bash "$ALVO" 2>&1; }

echo "=== test_pg_export_db_objects ==="

# --- 1) inspecao nao invoca o Odoo nem publica --------------------------------
saida="$(correr)"
codigo=$?
contem "inspeccao anuncia-se"            "$saida" "INSPECCAO"
contem "inspeccao nao invoca o Odoo"     "$saida" "(inspeccao: o Odoo nao foi invocado)"
nao_contem "inspeccao nao publica"       "$saida" "push OK"
verificar "inspeccao sai a zero" "$([ $codigo -eq 0 ] && echo 0 || echo 1)"
verificar "inspeccao nao cria o espelho" "$([ ! -d "$RAIZ/mirrors/objectos_bd.git" ] && echo 0 || echo 1)"

# --- 2) execucao real exporta e publica ---------------------------------------
saida="$(CONFIRMA=1 correr)"
contem "exporta a primeira instancia"  "$saida" "EXPORTADO"
contem "publica"                       "$saida" "push OK -> live/objectos-bd"
verificar "o ramo existe no remoto" \
  "$(git --git-dir="$REMOTO" rev-parse --verify -q refs/heads/live/objectos-bd >/dev/null && echo 0 || echo 1)"
ficheiros="$(git --git-dir="$REMOTO" ls-tree -r --name-only refs/heads/live/objectos-bd)"
contem "leva os ficheiros da producao" "$ficheiros" "producao/accoes_servidor/1_teste.py"
contem "leva os ficheiros dos testes"  "$ficheiros" "testes/accoes_servidor/1_teste.py"

# --- 3) sem alteracoes nao inventa commit -------------------------------------
antes="$(git --git-dir="$REMOTO" rev-parse refs/heads/live/objectos-bd)"
saida="$(CONFIRMA=1 correr)"
contem "reconhece que nada mudou" "$saida" "sem alteracoes nos objectos da base de dados"
depois="$(git --git-dir="$REMOTO" rev-parse refs/heads/live/objectos-bd)"
verificar "nao cria commit sem alteracoes" "$([ "$antes" = "$depois" ] && echo 0 || echo 1)"

# --- 4) uma instancia falhada IMPEDE a publicacao -----------------------------
# E o teste que justifica os outros: publicar com uma instancia em falta daria por
# fresco o que e da execucao anterior, e um diff vazio passaria por "nada mudou".
rm -f "$INST_B/Server/odoo-bin"
printf '# mudou\n' > "$INST_A/marcador_para_mudar.txt"
saida="$(CONFIRMA=1 correr)"
codigo=$?
contem "reporta a falha"        "$saida" "ERRO: falta"
contem "recusa publicar"        "$saida" "NAO PUBLICADO"
nao_contem "nao chega a empurrar" "$saida" "push OK"
verificar "sai com erro" "$([ $codigo -ne 0 ] && echo 0 || echo 1)"
depois="$(git --git-dir="$REMOTO" rev-parse refs/heads/live/objectos-bd)"
verificar "o ramo remoto fica intacto" "$([ "$antes" = "$depois" ] && echo 0 || echo 1)"

# --- 5) configuracao incompleta falha cedo ------------------------------------
CONF_MAU="$RAIZ/mau.conf"
printf 'PG_REMOTO="%s"\n' "$REMOTO" > "$CONF_MAU"
saida="$(PG_MIRROR_CONF="$CONF_MAU" CONFIRMA=1 bash "$ALVO" 2>&1)"
codigo=$?
contem "exige PG_INSTANCIAS" "$saida" "'PG_INSTANCIAS' nao esta definido"
verificar "sai com codigo 2" "$([ $codigo -eq 2 ] && echo 0 || echo 1)"

# --- 6) sem configuracao nenhuma ----------------------------------------------
saida="$(PG_MIRROR_CONF="$RAIZ/nao_existe.conf" HOME="$RAIZ/sem_nada" bash "$ALVO" 2>&1)"
contem "diz onde procurou a configuracao" "$saida" "ficheiro de configuracao nao encontrado"

echo
if [ "$falhou" -gt 0 ]; then
  echo "FALHOU: $falhou verificacao(oes); $passou passaram"
  exit 1
fi
echo "OK: $passou verificacoes passaram"
