r"""Regista um defeito como tarefa no projeto Brodoo, para nao ficar preso no repositorio.

O buraco que isto fecha nao e "esquecemo-nos de criar a tarefa". E mais dificil de ver:
**afirma-se que a tarefa foi criada e nao foi**. `FACTO OBSERVADO` (givachoice, linha 206
do PG_CONTEXT.md): "registado como defeito do framework no projeto Brodoo" -- e as tres
tarefas irmas do mesmo dia existem, essa nao. Ninguem podia ter dado por isso, porque a
afirmacao nao tinha numero e nada a verificava.

Por isso o comando faz tres coisas, e a terceira e a que importa:
  1. cria a tarefa no Brodoo, em Backlog e sem responsavel (qualquer tecnico lhe pega);
  2. nao duplica: cada tarefa leva uma impressao digital, e um defeito ja registado recebe
     uma ocorrencia nova no chatter em vez de uma tarefa nova;
  3. escreve o numero num livro-razao no repositorio onde o defeito foi observado
     (.pg/defeitos.jsonl), que e o que torna a afirmacao verificavel por maquina.

Sem chave pessoal ou sem rede, escreve a linha do livro-razao com task_id null e diz como
completar. Um defeito nao se perde porque a rede caiu.

Ambito: defeitos do framework e do pg_brodoo. Comportamento indesejado no Odoo de um
cliente e gerido por quem trabalha nesse projeto, no projeto do cliente (--projeto).

Uso:
  py scripts\pg_report_defect.py --titulo "o preflight aceita..." --ficheiro d.md --dry-run
  py scripts\pg_report_defect.py --titulo "..." --ficheiro d.md --componente pg_brodoo
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

PROJETO_BRODOO = 234
ETAPA_BACKLOG = 846          # entrada; a lista da sprint e decisao de quem planeia
COMPONENTES = ("framework", "pg_brodoo")
SECCOES = ("O que acontece", "Onde foi observado", "Como se reproduz", "Impacto")
SCHEMA = "1.0"


def _sem_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto):
    return re.sub(r"\s+", " ", _sem_acentos(texto or "").casefold()).strip()


def impressao_digital(componente, titulo):
    """Do componente e do titulo, e nao do corpo: o corpo ganha detalhe a cada ocorrencia."""
    assinatura = normalizar(componente) + "|" + normalizar(titulo)
    return hashlib.sha256(assinatura.encode("utf-8")).hexdigest()[:16]


def seccoes_em_falta(markdown):
    presentes = set()
    for m in re.finditer(r"^#{2,3}\s*(.+?)\s*$", markdown, re.M):
        presentes.add(normalizar(m.group(1)))
    return [s for s in SECCOES if normalizar(s) not in presentes]


def procurar_por_impressao(cliente, projeto, fp):
    achados = cliente.call_kw(
        "project.task", "search_read",
        args=[[["project_id", "=", projeto], ["description", "ilike", fp]]],
        kwargs={"fields": ["name"], "limit": 1})
    if achados:
        return achados[0]["id"], achados[0]["name"]
    return None, None


def registar_ocorrencia(cliente, task_id, onde, quando):
    corpo = ("<p>Nova ocorrencia deste defeito em <b>" + onde + "</b>, a " + quando + ". "
             "Registada pelo pg_report_defect.py em vez de abrir tarefa nova.</p>")
    # body_is_html: sem ele o Odoo escapa o corpo e a nota sai com as etiquetas a vista.
    # Quando o PR #65 entrar, passar a chamar o pg_odoo_post_chatter.py, que e o sitio da regra.
    cliente.call_kw("project.task", "message_post", args=[[task_id]],
                    kwargs={"body": corpo, "message_type": "comment",
                            "subtype_xmlid": "mail.mt_note", "body_is_html": True})


def corpo_da_tarefa(markdown, fp, confirmado):
    from pg_build_email_cliente import converter
    html = converter(markdown, manter_assinatura=True).fragmento
    if confirmado:
        html += ("<p><i>Sem evidencia reproduzida no momento do registo; criada com "
                 "confirmacao explicita do utilizador.</i></p>")
    return html + "<p>fingerprint: " + fp + "</p>"


def escrever_livro_razao(repo, registo):
    caminho = pathlib.Path(repo) / ".pg" / "defeitos.jsonl"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(registo, ensure_ascii=False) + "\n")
    return caminho


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--titulo", required=True, help="sem o prefixo do componente")
    ap.add_argument("--ficheiro", required=True, type=pathlib.Path,
                    help="rascunho .md com as seccoes do contrato")
    ap.add_argument("--componente", default="framework", choices=COMPONENTES)
    ap.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd(),
                    help="repositorio onde o defeito foi observado")
    ap.add_argument("--projeto", type=int, default=PROJETO_BRODOO,
                    help="id do projeto (para um cliente, o projeto do cliente)")
    ap.add_argument("--confirmado-pelo-utilizador", action="store_true",
                    help="sem evidencia reproduzida, mas o utilizador confirmou a criacao")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not args.ficheiro.exists():
        print("ERRO: " + str(args.ficheiro) + " nao existe", file=sys.stderr)
        return 2
    markdown = args.ficheiro.read_text(encoding="utf-8")

    falta = seccoes_em_falta(markdown)
    if falta and not args.confirmado_pelo_utilizador:
        print("ERRO: faltam seccoes do contrato: " + ", ".join(falta), file=sys.stderr)
        print("      Sem evidencia reproduzivel, perguntar ao utilizador e usar "
              "--confirmado-pelo-utilizador.", file=sys.stderr)
        return 2

    fp = impressao_digital(args.componente, args.titulo)
    nome = args.componente + " - " + args.titulo
    html = corpo_da_tarefa(markdown, fp, args.confirmado_pelo_utilizador)
    repo = args.repo.resolve()
    agora = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    if args.dry_run:
        print("--- PLANO ---")
        print("projeto  : " + str(args.projeto))
        print("etapa    : Backlog (" + str(ETAPA_BACKLOG) + "), sem responsavel")
        print("nome     : " + nome)
        print("impressao: " + fp)
        print("livro    : " + str(repo / ".pg" / "defeitos.jsonl"))
        print("seccoes em falta: " + (", ".join(falta) if falta else "nenhuma"))
        print("--- corpo ---")
        print(html)
        return 0

    registo = {"schema_version": SCHEMA, "fingerprint": fp, "task_id": None,
               "project_id": args.projeto, "componente": args.componente,
               "titulo": args.titulo, "repo_name": repo.name,
               "criado_em_utc": agora, "operador": None}

    try:
        from pg_doc_templates_common import OdooKnowledgeClient
        from pg_odoo_credentials import resolver_credenciais_pg
        cred = resolver_credenciais_pg()
        registo["operador"] = cred["login"]
        cliente = OdooKnowledgeClient(cred["url"], cred["db"], cred["login"], cred["api_key"])

        existente, nome_existente = procurar_por_impressao(cliente, args.projeto, fp)
        if existente:
            registar_ocorrencia(cliente, existente, repo.name, agora[:10])
            registo["task_id"] = existente
            registo["ocorrencia_de"] = existente
            escrever_livro_razao(repo, registo)
            print("JA REGISTADO: tarefa " + str(existente) + " (" + str(nome_existente) + ")")
            print("              ocorrencia acrescentada, sem tarefa nova.")
            return 0

        devolvido = cliente.call_kw("project.task", "create", args=[{
            "name": nome,
            "project_id": args.projeto,
            "stage_id": ETAPA_BACKLOG,
            "user_ids": [(6, 0, [])],   # sem responsavel: uma tarefa atribuida parece tratada
            "description": html,
        }])
        registo["task_id"] = devolvido[0] if isinstance(devolvido, list) else devolvido
    except Exception as exc:                                  # noqa: BLE001
        escrever_livro_razao(repo, registo)
        print("AVISO: nao foi possivel criar a tarefa (" + str(exc) + ").", file=sys.stderr)
        print("       Registado localmente com task_id null; o preflight avisa ate a tarefa "
              "existir.", file=sys.stderr)
        print("       Repetir o comando quando houver chave pessoal e rede.", file=sys.stderr)
        return 1

    caminho = escrever_livro_razao(repo, registo)
    print("tarefa criada: " + str(registo["task_id"]) + " | " + nome)
    print("livro-razao  : " + str(caminho))
    return 0


if __name__ == "__main__":
    sys.exit(main())
