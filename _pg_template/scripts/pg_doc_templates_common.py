import argparse
import html
import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - enables unit tests without requests installed
    requests = None


class OdooKnowledgeClient:
    def __init__(self, base_url: str, database: str, login: str, api_key: str, transport: str = "auto") -> None:
        if requests is None:
            raise RuntimeError("Python dependency 'requests' is required to run pg_doc_templates_common.py.")
        self.base_url = base_url.rstrip("/")
        self.database = database
        self.login = login
        self.api_key = api_key
        self.transport = transport
        self._uid = None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "pg-template-doc-pull/1.0",
            }
        )

    def _authenticate(self) -> int:
        """Autentica no servico 'common' de /jsonrpc e devolve o uid.

        NAO usar /web/session/authenticate: esse endpoint e o login de sessao web e
        rejeita chaves de API com AccessDenied. Era o que este fallback fazia, pelo que
        na pratica nunca funcionou -- e como so entra em acao quando a via JSON-2 falha,
        um 404 transitorio num unico modelo matava o pull inteiro. O servico 'common'
        aceita a chave de API como password (mesmo caminho do pg_odoo_query.ps1).
        """
        if self._uid is not None:
            return self._uid

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.database, self.login, self.api_key, {}],
            },
            "id": 1,
        }
        response = self.session.post(f"{self.base_url}/jsonrpc", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"Odoo authentication failed: {data['error']}")
        uid = data.get("result")
        if not uid:
            raise RuntimeError("Odoo authentication failed: missing uid in response.")

        self._uid = int(uid)
        return self._uid

    def _call_json2(self, model: str, method: str, *, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> Any:
        args = args or []
        kwargs = kwargs or {}
        body: Dict[str, Any] = dict(kwargs)
        if args:
            body["args"] = args
        headers = {
            "Authorization": f"bearer {self.api_key}",
            "X-Odoo-Database": self.database,
        }
        endpoint = f"{self.base_url}/json/2/{model}/{method}"
        response = self.session.post(endpoint, headers=headers, json=body, timeout=120)
        response.raise_for_status()
        return response.json()

    def _call_jsonrpc(self, model: str, method: str, *, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> Any:
        uid = self._authenticate()
        args = args or []
        kwargs = kwargs or {}
        # execute_kw em vez de /web/dataset/call_kw: o call_kw web exige sessao com cookie,
        # que a chave de API nao estabelece. Os kwargs passam tal e qual (domain, fields,
        # limit, order, attributes sao parametros nomeados dos metodos do ORM).
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.database, uid, self.api_key, model, method, args, kwargs],
            },
            "id": 1,
        }
        endpoint = f"{self.base_url}/jsonrpc"
        response = self.session.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"Odoo call_kw error for {model}.{method}: {data['error']}")
        return data.get("result")

    def call_kw(self, model: str, method: str, *, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> Any:
        if self.transport == "json2":
            return self._call_json2(model, method, args=args, kwargs=kwargs)
        if self.transport == "jsonrpc":
            return self._call_jsonrpc(model, method, args=args, kwargs=kwargs)
        try:
            return self._call_json2(model, method, args=args, kwargs=kwargs)
        except Exception:
            return self._call_jsonrpc(model, method, args=args, kwargs=kwargs)


_CLIENT: Optional[OdooKnowledgeClient] = None
_ARTICLE_BODY_FIELD: Optional[str] = None

# Anexos que sao residuo de download/edicao, nao ativos de template. Chegam a Knowledge
# quando alguem arrasta para o artigo um ficheiro que o browser ainda estava a descarregar
# (.crdownload/.part/...) ou um lock do Office (~$...). Filtrar aqui, na origem do pull,
# evita que se propaguem para doc_templates/assets, para o MANIFEST.json e dai para todos
# os repos de projeto que sincronizam os assets partilhados.
_TRANSIENT_ATTACHMENT_SUFFIXES = (".crdownload", ".part", ".partial", ".download", ".tmp")
_TRANSIENT_ATTACHMENT_PREFIXES = ("~$",)


def _is_transient_attachment(name: str) -> bool:
    normalized = (name or "").strip().lower()
    if not normalized:
        return True
    if normalized.startswith(_TRANSIENT_ATTACHMENT_PREFIXES):
        return True
    return normalized.endswith(_TRANSIENT_ATTACHMENT_SUFFIXES)


def _require_client() -> OdooKnowledgeClient:
    if _CLIENT is None:
        raise RuntimeError("Client not initialized. Call fetch_published_articles first.")
    return _CLIENT


def _resolve_xmlid(xmlid: str) -> int:
    client = _require_client()
    if "." not in xmlid:
        raise ValueError(f"Invalid workspace XML ID: {xmlid}")
    module, name = xmlid.split(".", 1)
    matches = client.call_kw(
        "ir.model.data",
        "search_read",
        kwargs={
            "domain": [["module", "=", module], ["name", "=", name], ["model", "=", "knowledge.article"]],
            "fields": ["res_id"],
            "limit": 1,
        },
    )
    if not matches:
        raise RuntimeError(f"Workspace XML ID not found: {xmlid}")
    return int(matches[0]["res_id"])


def _detect_article_body_field() -> Optional[str]:
    client = _require_client()
    candidates = (
        "body",
        "body_html",
        "article_html",
        "content",
        "content_html",
        "description",
    )
    fields_meta = client.call_kw(
        "knowledge.article",
        "fields_get",
        kwargs={"attributes": ["type"]},
    )
    for name in candidates:
        field_meta = fields_meta.get(name)
        if field_meta and field_meta.get("type") in {"html", "text"}:
            return name
    return None


def _html_to_markdown_like(value: str) -> str:
    text = value

    # Corpo que é inteiramente um <pre> transporta markdown em bruto (tabelas, blocos
    # de código, indentação) e passa tal e qual. É o formato que garante round-trip
    # sem perdas; ver "Onde vive o conteúdo do template" em PG_DOC_TEMPLATES_VERSIONING.md.
    apenas_pre = re.match(r"^\s*<pre[^>]*>(.*)</pre>\s*$", text, re.S | re.I)
    if apenas_pre:
        # O editor do Odoo injecta marcação própria mesmo dentro do <pre> (ex.:
        # <span data-o-mail-quote> em linhas iniciadas por ">"). Remover as etiquetas
        # antes do unescape; o markdown verdadeiro está escapado e não é afectado.
        cru = re.sub(r"<[^>]+>", "", apenas_pre.group(1))
        cru = html.unescape(cru)
        return cru.replace("\r\n", "\n").replace("\r", "\n").strip()

    text = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", text)

    # Cada <p> do editor do Odoo é UMA linha de markdown, e as linhas em branco vêm
    # como <p><br></p>. Fechar o parágrafo com "\n\n" inseria uma linha em branco
    # entre linhas consecutivas, o que parte tabelas markdown (linha de cabeçalho,
    # separador e linhas de dados deixam de ser reconhecidas como tabela) e listas.
    # Com "\n", o <p><br></p> continua a produzir a linha em branco onde o autor a pôs.
    text = re.sub(r"(?i)</\s*p\s*>", "\n", text)

    # O editor usa <div> por linha em alguns articles em vez de <p>. Sem esta regra
    # as linhas ficavam todas concatenadas (o strip generico de etiquetas nao deixa
    # separador nenhum) — ver TPL_TIMESHEET_INSTRUCOES.
    text = re.sub(r"(?i)</\s*div\s*>", "\n", text)

    text = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", text)
    text = re.sub(r"(?i)</\s*li\s*>", "", text)
    text = re.sub(r"(?i)<\s*h([1-6])[^>]*>", lambda m: "\n" + ("#" * int(m.group(1))) + " ", text)
    text = re.sub(r"(?i)</\s*h[1-6]\s*>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # O editor preenche células vazias com &nbsp;; em markdown basta um espaço normal.
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _normalize_native_body(raw_value: Any) -> str:
    if raw_value is None:
        return ""
    if isinstance(raw_value, str):
        value = raw_value.strip()
        if not value:
            return ""
        if "<" in value and ">" in value:
            return unicodedata.normalize("NFC", _html_to_markdown_like(value))
        return unicodedata.normalize("NFC", value)
    if isinstance(raw_value, (dict, list)):
        return unicodedata.normalize("NFC", json.dumps(raw_value, ensure_ascii=False))
    return unicodedata.normalize("NFC", str(raw_value))

def fetch_published_articles(
    base_url: str,
    database: str,
    login: str,
    api_key: str,
    workspace_xmlid: str,
    transport: str = "auto",
) -> List[Dict[str, Any]]:
    global _CLIENT, _ARTICLE_BODY_FIELD
    _CLIENT = OdooKnowledgeClient(
        base_url=base_url,
        database=database,
        login=login,
        api_key=api_key,
        transport=transport,
    )
    workspace_id = _resolve_xmlid(workspace_xmlid)
    _ARTICLE_BODY_FIELD = _detect_article_body_field()

    read_fields = [
        "id",
        "pg_template_code",
        "pg_template_version",
        "pg_template_state",
        "pg_template_body_md",
        "write_uid",
        "write_date",
    ]
    if _ARTICLE_BODY_FIELD and _ARTICLE_BODY_FIELD not in read_fields:
        read_fields.append(_ARTICLE_BODY_FIELD)

    rows = _CLIENT.call_kw(
        "knowledge.article",
        "search_read",
        kwargs={
            "domain": [
                ["parent_id", "child_of", workspace_id],
                ["pg_template_code", "!=", False],
                ["pg_template_state", "=", "published"],
            ],
            "fields": read_fields,
            "order": "pg_template_code asc",
        },
    )

    published_rows = [row for row in rows if row.get("pg_template_state") == "published"]
    for row in published_rows:
        native_body = _normalize_native_body(row.get(_ARTICLE_BODY_FIELD)) if _ARTICLE_BODY_FIELD else ""
        fallback_body = row.get("pg_template_body_md") or ""
        effective_body = native_body or fallback_body
        row["pg_template_body_md"] = effective_body
        row["pg_template_body_source"] = (
            f"knowledge.article.{_ARTICLE_BODY_FIELD}" if native_body else "knowledge.article.pg_template_body_md"
        )
    return published_rows


def fetch_attachments(article_id: int) -> List[Dict[str, Any]]:
    client = _require_client()
    rows = client.call_kw(
        "ir.attachment",
        "search_read",
        kwargs={
            "domain": [["res_model", "=", "knowledge.article"], ["res_id", "=", int(article_id)]],
            "fields": ["id", "name", "datas", "mimetype", "checksum", "write_date"],
            "order": "name asc",
        },
    )
    return [row for row in rows if not _is_transient_attachment(str(row.get("name") or ""))]


def _main() -> int:
    parser = argparse.ArgumentParser(description="Pull published PG doc templates from Odoo Knowledge via JSON-RPC.")
    parser.add_argument("pull", nargs="?", default="pull")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--login", required=True)
    # Não é `required`: a via preferida é a variável de ambiente. Uma chave em `--api-key`
    # fica legível na lista de processos enquanto o processo corre, e é capturada por
    # auditoria de criação de processos e por EDR (risco R3 do
    # PG_SECURITY_CREDENTIALS_AUDIT.md). O argumento sobrevive para chamadas manuais.
    parser.add_argument("--api-key", default="")
    parser.add_argument("--workspace-xmlid", required=True)
    parser.add_argument("--transport", choices=("auto", "json2", "jsonrpc"), default="auto")
    parser.add_argument("--output-file", default="")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("PG_ODOO_API_KEY", "").strip()
    if not api_key:
        parser.error(
            "sem API key: definir PG_ODOO_API_KEY no ambiente (preferido) ou passar --api-key")

    articles = fetch_published_articles(
        base_url=args.base_url,
        database=args.database,
        login=args.login,
        api_key=api_key,
        workspace_xmlid=args.workspace_xmlid,
        transport=args.transport,
    )

    payload = {"templates": []}
    for article in articles:
        payload["templates"].append(
            {
                "article": article,
                "attachments": fetch_attachments(int(article["id"])),
            }
        )

    output = json.dumps(payload, ensure_ascii=False)
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(output)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
