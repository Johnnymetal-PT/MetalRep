#!/bin/bash
# pg_export_db_objects.sh — publica numa branch do repositório o que existe SÓ na base de
# dados de um Odoo vivo e não em ficheiros.
#
# PORQUE EXISTE
#
#   Ações de servidor, automatismos, campos manuais, vistas e menus criados pela interface
#   ou pelo Studio não estão em lado nenhum que se possa ler: não aparecem em diff, não
#   viajam com o repositório e não passam por revisão. É a única camada de um projeto sem
#   rastreio nenhum.
#
#   FACTO OBSERVADO (givachoice): 19 ações de servidor com Python lá dentro que ninguém
#   revê e que partem numa migração. E foi por esta camada que entrou uma das quatro
#   regressões sobre comportamento que o cliente já tinha — uma vista acrescentada pelo
#   Studio criou quatro `ir.actions.act_window.view` com sequências mais baixas do que as
#   do padrão, e a aplicação passou a abrir no formulário de criação.
#
#   Com isto publicado numa branch, passa a ver-se em diff o que mudou na configuração de
#   um Odoo vivo — incluindo o que o Studio lá deixou. É o complemento do
#   pg_mirror_server_code.sh: aquele espelha o código, este espelha o que o código não diz.
#
#   Promovido do `exportar_objectos_bd.sh` do givachoice (backlog PG-010, fase F3). Só os
#   caminhos eram específicos.
#
# ONDE CORRE
#
#   No servidor do cliente. Corre pelo shell do próprio Odoo, pelo que lê o `odoo.conf` e
#   NÃO precisa de credenciais novas.
#
# SÓ LÊ
#
#   O guião Python termina em `env.cr.rollback()`. Mesmo que alguém lhe acrescente uma
#   escrita por engano, a transação é desfeita.
#
# O QUE NÃO FAZ
#
#   Não escreve datas dentro dos ficheiros exportados, de propósito: se escrevesse, o diff
#   mudava todos os dias e deixava de dizer alguma coisa. Um diff aqui significa que
#   alguém alterou a configuração, não que o exportador correu.
#
#   E não publica nada sem CONFIRMA=1.
#
# UTILIZAÇÃO
#
#   cp pg_mirror_server_code.conf.exemplo ~/pg_mirror.conf   # e editar (é o mesmo ficheiro)
#   bash pg_export_db_objects.sh                             # inspeção
#   CONFIRMA=1 bash pg_export_db_objects.sh                  # exporta e publica
#
#   Partilha a configuração com o pg_mirror_server_code.sh de propósito: o `PG_REMOTO` é o
#   mesmo, e dois ficheiros com o mesmo remoto são um sítio a mais para divergirem.
#
#   Uma vez por dia chega — estes objetos mudam à mão.
#
# Dependências: bash, git, coreutils, e o Odoo da própria instância.

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

# Um valor em falta aqui produziria uma publicacao silenciosamente errada -- por exemplo,
# um push para o repositorio de outro cliente. Falhar cedo e barato.
for obrigatorio in PG_REMOTO PG_INSTANCIAS; do
  eval "valor=\${$obrigatorio:-}"
  if [ -z "$valor" ]; then
    echo "ERRO: '$obrigatorio' nao esta definido em $CONF"
    exit 2
  fi
done

PG_MIRROR_DIR="${PG_MIRROR_DIR:-$HOME/mirrors}"
PG_AUTOR_NOME="${PG_AUTOR_NOME:-pg mirror}"
PG_AUTOR_EMAIL="${PG_AUTOR_EMAIL:-it.odoo@parametro.pt}"
PG_RAMO_OBJECTOS="${PG_RAMO_OBJECTOS:-live/objectos-bd}"
# Caminhos dentro da raiz de cada instancia. Sao relativos porque variam de instalacao
# para instalacao, e absolutos nao serviriam a mais ninguem.
PG_ODOO_BIN_REL="${PG_ODOO_BIN_REL:-Server/odoo-bin}"
PG_ODOO_CONF_REL="${PG_ODOO_CONF_REL:-odoo.conf}"
PG_PYTHON_REL="${PG_PYTHON_REL:-}"

DESTINO="$PG_MIRROR_DIR/objectos_bd"
CONFIRMA="${CONFIRMA:-0}"
falhas=0
exportadas=0

GUIAO="$(mktemp "${TMPDIR:-/tmp}/pg_export_db_objects.XXXXXX.py")"
LOG="$(mktemp "${TMPDIR:-/tmp}/pg_export_db_objects.XXXXXX.log")"
# Caminho fixo em /tmp era colisao entre execucoes concorrentes e ficheiro legivel por
# qualquer utilizador da maquina. E limpa-se no fim, aconteca o que acontecer.
trap 'rm -f "$GUIAO" "$LOG"' EXIT

# --- o exportador, em Python -------------------------------------------------
cat > "$GUIAO" <<'PYEOF'
import os, re, csv, shutil

dest = os.environ["PG_DEST"]
for sub in ("accoes_servidor", "automatismos", "vistas"):
    p = os.path.join(dest, sub)
    if os.path.isdir(p):
        shutil.rmtree(p)
os.makedirs(dest, exist_ok=True)

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "sem-nome").lower()).strip("-")
    return s[:60] or "sem-nome"

def escrever(caminho, texto):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)

def ler(modelo, ids, campos):
    # Filtrar pelos campos que existem mesmo: entre series do Odoo os campos mudam, e um
    # campo inexistente rebentava a exportacao inteira em vez de a degradar.
    if not ids:
        return []
    existe = set(env[modelo].fields_get().keys())
    campos = [c for c in campos if c in existe]
    return sorted(env[modelo].browse(ids).read(campos), key=lambda r: r["id"])

def ids_studio(modelo):
    return [d["res_id"] for d in env["ir.model.data"].search_read(
        [("module", "=", "studio_customization"), ("model", "=", modelo)], ["res_id"])]

def ids_sem_modulo(modelo):
    # O que nao tem `ir.model.data` nenhum: criado pela interface, sem modulo que o
    # explique. Em lotes porque um `in` com dezenas de milhares de ids nao passa.
    todos = env[modelo].search([]).ids
    com = set()
    for i in range(0, len(todos), 2000):
        com |= {d["res_id"] for d in env["ir.model.data"].search_read(
            [("model", "=", modelo), ("res_id", "in", todos[i:i + 2000])], ["res_id"])}
    return [i for i in todos if i not in com]

def alvo(modelo):
    return sorted(set(ids_studio(modelo)) | set(ids_sem_modulo(modelo)))

resumo = []

accoes = ler("ir.actions.server", alvo("ir.actions.server"),
             ["id", "name", "model_id", "state", "code", "usage", "sequence"])
for a in accoes:
    cab = ["# accao de servidor %s" % a["id"],
           "# nome   : %s" % a.get("name"),
           "# modelo : %s" % (a.get("model_id") and a["model_id"][1]),
           "# tipo   : %s" % a.get("state"),
           "# uso    : %s" % a.get("usage"), ""]
    escrever(os.path.join(dest, "accoes_servidor", "%s_%s.py" % (a["id"], slug(a.get("name")))),
             "\n".join(cab) + (a.get("code") or "# (sem codigo: nao e do tipo 'code')\n"))
resumo.append(("accoes de servidor", len(accoes)))

autos = ler("base.automation", alvo("base.automation"),
            ["id", "name", "model_id", "trigger", "filter_domain", "filter_pre_domain",
             "active", "trigger_field_ids", "action_server_ids", "on_change_field_ids"])
for a in autos:
    linhas = ["automatismo %s" % a["id"]]
    for k in ("name", "model_id", "trigger", "active", "filter_domain", "filter_pre_domain",
              "trigger_field_ids", "action_server_ids", "on_change_field_ids"):
        if k in a:
            linhas.append("%-20s %s" % (k, a[k]))
    escrever(os.path.join(dest, "automatismos", "%s_%s.txt" % (a["id"], slug(a.get("name")))),
             "\n".join(linhas) + "\n")
resumo.append(("automatismos", len(autos)))

vistas = ler("ir.ui.view", alvo("ir.ui.view"),
             ["id", "name", "model", "type", "priority", "active", "inherit_id", "arch_db"])
for v in vistas:
    cab = "<!-- vista %s | %s | modelo %s | herda %s | activa %s -->\n" % (
        v["id"], v.get("name"), v.get("model"),
        (v.get("inherit_id") and v["inherit_id"][1]) or "-", v.get("active"))
    escrever(os.path.join(dest, "vistas", "%s_%s.xml" % (v["id"], slug(v.get("name")))),
             cab + (v.get("arch_db") or ""))
resumo.append(("vistas", len(vistas)))

def tabela(ficheiro, modelo, dominio, campos, chave):
    regs = env[modelo].search_read(dominio, campos)
    regs.sort(key=chave)
    with open(os.path.join(dest, ficheiro), "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(campos)
        for r in regs:
            w.writerow([r.get(c) for c in campos])
    return len(regs)

resumo.append(("campos manuais", tabela(
    "campos_manuais.csv", "ir.model.fields", [("state", "=", "manual")],
    ["model", "name", "ttype", "field_description", "relation", "related", "store", "required"],
    lambda r: (r["model"] or "", r["name"] or ""))))
resumo.append(("menus", tabela(
    "menus.csv", "ir.ui.menu", [("id", "in", alvo("ir.ui.menu"))],
    ["id", "name", "parent_id", "sequence", "active"], lambda r: r["id"])))
resumo.append(("valores por defeito", tabela(
    "valores_defeito.csv", "ir.default", [("id", "in", alvo("ir.default"))],
    ["id", "field_id", "json_value", "company_id"], lambda r: r["id"])))

escrever(os.path.join(dest, "_RESUMO.md"),
         "# Objectos que existem so na base de dados\n\n"
         "Exportado pelo shell do Odoo. Sem datas de proposito: um diff neste directorio\n"
         "significa que alguem alterou alguma coisa, nao que o exportador correu.\n\n"
         + "\n".join("- %s: %d" % (n, q) for n, q in resumo) + "\n")

# So leituras. Mesmo que alguem acrescente uma escrita por engano, e desfeita aqui.
env.cr.rollback()
print("EXPORTADO %s :: %s" % (dest, ", ".join("%s=%d" % (n, q) for n, q in resumo)))
PYEOF

# --- mecânica ----------------------------------------------------------------
resolver_python() {  # $1=raiz
  if [ -n "$PG_PYTHON_REL" ]; then
    printf '%s\n' "$1/$PG_PYTHON_REL"
    return
  fi
  # A versao do interpretador no venv muda entre instalacoes (3.10, 3.12, ...). Fixa-la
  # na configuracao seria obrigar a editar o ficheiro a cada upgrade de Python.
  for p in "$1"/python-venv/bin/python3.* "$1"/python-venv/bin/python3 "$1"/venv/bin/python3; do
    [ -x "$p" ] && { printf '%s\n' "$p"; return; }
  done
  command -v python3 2>/dev/null || printf '%s\n' "python3"
}

exportar() {  # $1=nome $2=raiz $3=base
  nome="$1"; raiz="$2"; base="$3"
  echo
  echo "=== $nome ($base)"
  echo "    raiz: $raiz"
  py="$(resolver_python "$raiz")"
  bin="$raiz/$PG_ODOO_BIN_REL"
  conf="$raiz/$PG_ODOO_CONF_REL"
  for f in "$py" "$bin" "$conf"; do
    if [ ! -e "$f" ]; then
      echo "    ERRO: falta $f"; falhas=$((falhas+1)); return
    fi
  done
  if [ "$CONFIRMA" != "1" ]; then
    echo "    (inspeccao: o Odoo nao foi invocado)"
    return
  fi

  # O stderr vai para ficheiro, mas NAO para o esquecimento: no guiao original era
  # mandado para /dev/null e a falha de uma instancia passava despercebida -- o script
  # seguia e publicava a arvore da execucao ANTERIOR como se fosse fresca. Um espelho
  # parado nao avisa que envelheceu, e essa e a falha mais perigosa que ele pode ter.
  saida="$(PG_DEST="$DESTINO/$nome" "$py" "$bin" shell -c "$conf" -d "$base" --no-http \
    < "$GUIAO" 2>"$LOG" | grep '^EXPORTADO')"
  if [ -z "$saida" ]; then
    echo "    ERRO: a exportacao nao produziu resultado."
    echo "    ultimas linhas do stderr:"
    tail -n 5 "$LOG" | sed 's|^|      |'
    falhas=$((falhas+1))
    return
  fi
  echo "$saida" | sed 's|^|    |'
  exportadas=$((exportadas+1))
}

publicar() {
  G="$PG_MIRROR_DIR/objectos_bd.git"
  if [ ! -d "$G" ]; then
    git init --bare -q "$G"
    git --git-dir="$G" config core.bare false
    git --git-dir="$G" config core.worktree "$DESTINO"
    git --git-dir="$G" config user.name "$PG_AUTOR_NOME"
    git --git-dir="$G" config user.email "$PG_AUTOR_EMAIL"
    git --git-dir="$G" symbolic-ref HEAD "refs/heads/$PG_RAMO_OBJECTOS"
    git --git-dir="$G" remote add origin "$PG_REMOTO"
    echo "    repositorio criado em $G"
  fi
  cd "$DESTINO" || { echo "    ERRO: cd para $DESTINO falhou"; falhas=$((falhas+1)); return; }
  git --git-dir="$G" add -A
  if git --git-dir="$G" diff --cached --quiet; then
    echo "    sem alteracoes nos objectos da base de dados"
  else
    n=$(git --git-dir="$G" diff --cached --name-only | wc -l)
    git --git-dir="$G" commit -q -m "objectos bd $(date '+%Y-%m-%d %H:%M:%S')"
    echo "    commit $(git --git-dir="$G" rev-parse --short HEAD) com $n ficheiro(s)"
  fi
  if git --git-dir="$G" push -q -u origin "$PG_RAMO_OBJECTOS" 2>&1; then
    echo "    push OK -> $PG_RAMO_OBJECTOS"
  else
    echo "    PUSH FALHOU (a deploy key tem 'Allow write access'?)"; falhas=$((falhas+1))
  fi
}

# --- execução ----------------------------------------------------------------
total=0
printf '%s\n' "$PG_INSTANCIAS" | while IFS='|' read -r n r b; do :; done  # valida sintaxe cedo
while IFS='|' read -r nome raiz base; do
  nome="$(printf '%s' "${nome:-}" | tr -d '[:space:]')"
  raiz="$(printf '%s' "${raiz:-}" | tr -d '[:space:]')"
  base="$(printf '%s' "${base:-}" | tr -d '[:space:]')"
  [ -z "$nome" ] && continue
  total=$((total+1))
  exportar "$nome" "$raiz" "$base"
done <<EOF
$PG_INSTANCIAS
EOF

if [ "$CONFIRMA" != "1" ]; then
  echo
  echo "INSPECCAO: nada foi exportado nem publicado. $total instancia(s) declarada(s)."
  echo "Para exportar e publicar: CONFIRMA=1 bash $0"
  exit 0
fi

echo
# Publicar com uma instancia em falta seria dar por fresco o que e da execucao anterior --
# e um diff vazio passaria por "nada mudou". Melhor nao publicar e dizer porque.
if [ "$falhas" -gt 0 ]; then
  echo "NAO PUBLICADO: $falhas falha(s) na exportacao ($exportadas de $total instancias)."
  echo "Publicar agora daria por actual o que e da execucao anterior."
  exit 1
fi

if [ "$exportadas" -eq 0 ]; then
  echo "NAO PUBLICADO: nenhuma instancia exportada. Verificar PG_INSTANCIAS em $CONF."
  exit 1
fi

echo "=== publicacao ($exportadas de $total instancias)"
publicar

if [ "$falhas" -gt 0 ]; then
  echo; echo "concluido com $falhas falha(s)"
  exit 1
fi
echo; echo "concluido sem falhas"
