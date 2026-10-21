#!/usr/bin/env python3
"""Cliente nativo para o protocolo Odoo MCP (Model Context Protocol).

Suporta instâncias Odoo 19+ / SaaS 19.4+ que expõem o endpoint POST /mcp
com autenticação Authorization: Bearer <API_KEY>.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def normalize_mcp_url(base_url: str) -> str:
    """Normaliza o URL para apontar diretamente ao endpoint /mcp."""
    url = base_url.strip().rstrip("/")
    if url.lower().endswith("/odoo"):
        url = url[:-5].rstrip("/")
    if url.lower().endswith("/mcp"):
        return url
    return f"{url}/mcp"


class OdooMcpClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.endpoint = normalize_mcp_url(base_url)
        self.api_key = api_key.strip()
        self.timeout = timeout

    def _post(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json, text/event-stream",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} {exc.reason} em {self.endpoint}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Erro de ligacao a {self.endpoint}: {exc.reason}") from exc

    def initialize(self) -> dict[str, Any]:
        """Executa o handshake inicial do MCP."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pg_brodoo_mcp", "version": "1.0"},
        }
        res = self._post("initialize", params)
        if res.get("error"):
            raise RuntimeError(f"Erro MCP initialize: {res['error']}")
        return res.get("result", {})

    def list_tools(self) -> list[dict[str, Any]]:
        """Lista as ferramentas disponiveis no Odoo MCP."""
        res = self._post("tools/list", {})
        if res.get("error"):
            raise RuntimeError(f"Erro MCP tools/list: {res['error']}")
        return res.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Executa uma ferramenta MCP e processa a resposta."""
        params = {
            "name": tool_name,
            "arguments": arguments,
        }
        res = self._post("tools/call", params)
        if res.get("error"):
            raise RuntimeError(f"Erro MCP tools/call ({tool_name}): {res['error']}")
        result = res.get("result", {})
        if result.get("isError"):
            err_content = result.get("content", [{}])
            err_msg = err_content[0].get("text", "Erro desconhecido na ferramenta MCP") if err_content else "Erro"
            raise RuntimeError(f"Erro de execucao MCP ({tool_name}): {err_msg}")

        content = result.get("content", [])
        if not content:
            return None
        first_text = content[0].get("text", "")
        # Tenta descodificar texto como JSON se for estrutura de dados
        try:
            return json.loads(first_text)
        except (json.JSONDecodeError, TypeError):
            return first_text

    def get_context(self) -> Any:
        """Obtem informacoes do utilizador, timezone e empresas ativas."""
        return self.call_tool("ai_tool_mcp_retrieve_initial_context", {})

    def get_models(self) -> Any:
        """Devolve a lista de modelos acessiveis."""
        return self.call_tool("ai_tool_get_models", {})

    def get_fields(self, model_name: str, include_description: bool = True) -> Any:
        """Devolve campos e metadados de um modelo."""
        return self.call_tool(
            "ai_tool_get_fields",
            {"model_name": model_name, "include_description": include_description},
        )

    def search(
        self,
        model_name: str,
        domain: str | list[Any] = "[]",
        fields: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        """Pesquisa registos no modelo indicado usando ai_tool_search."""
        domain_str = json.dumps(domain) if not isinstance(domain, str) else domain
        args: dict[str, Any] = {
            "model_name": model_name,
            "domain": domain_str,
            "fields": fields or ["id", "display_name"],
        }
        if limit is not None and limit > 0:
            args["limit"] = limit
        if offset is not None and offset > 0:
            args["offset"] = offset
        if order:
            args["order"] = order

        res = self.call_tool("ai_tool_search", args)
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except json.JSONDecodeError:
                pass
        return res if isinstance(res, list) else [res]

    def read_group(
        self,
        model_name: str,
        domain: str | list[Any] = "[]",
        groupby: list[str] | None = None,
        aggregates: list[str] | None = None,
        having: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
    ) -> Any:
        """Agrega e agrupa registos usando ai_tool_read_group."""
        domain_str = json.dumps(domain) if not isinstance(domain, str) else domain
        args: dict[str, Any] = {
            "model_name": model_name,
            "domain": domain_str,
        }
        if groupby:
            args["groupby"] = groupby
        if aggregates:
            args["aggregates"] = aggregates
        if having:
            args["having"] = having
        if limit is not None and limit > 0:
            args["limit"] = limit
        if offset is not None and offset > 0:
            args["offset"] = offset
        if order:
            args["order"] = order

        res = self.call_tool("ai_tool_read_group", args)
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except json.JSONDecodeError:
                pass
        return res


def parse_list_arg(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed]
        except json.JSONDecodeError:
            pass
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Odoo 19+ via Model Context Protocol (MCP)")
    parser.add_argument("--url", required=True, help="Base URL da instancia Odoo (ex.: https://cliente.odoo.com)")
    parser.add_argument("--key", "--api-key", required=True, dest="api_key", help="Chave de API / Bearer token MCP")
    parser.add_argument(
        "--action",
        choices=["search", "read_group", "get_fields", "get_models", "context", "list_tools", "call_tool", "ping"],
        default="search",
        help="Acao MCP a executar (default: search)",
    )
    parser.add_argument("--model", help="Nome tecnico do modelo Odoo (ex.: crm.lead, res.partner)")
    parser.add_argument("--domain", default="[]", help="Dominio de pesquisa em JSON (ex.: '[[\"stage_id\",\"=\",1]]')")
    parser.add_argument("--fields", help="Campos a devolver (separados por virgula ou array JSON)")
    parser.add_argument("--limit", type=int, default=0, help="Limite maximo de registos")
    parser.add_argument("--offset", type=int, default=0, help="Offset de registos a saltar")
    parser.add_argument("--order", help="Ordenacao (ex.: 'id desc')")
    parser.add_argument("--groupby", help="Campos de agrupamento para read_group (separados por virgula)")
    parser.add_argument("--aggregates", help="Agregacoes para read_group (ex.: 'expected_revenue:sum')")
    parser.add_argument("--having", help="Condicao having para read_group")
    parser.add_argument("--tool-name", help="Nome da ferramenta para call_tool")
    parser.add_argument("--tool-args", default="{}", help="Argumentos em JSON para call_tool")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout em segundos")

    args = parser.parse_args()

    # Reconfigura stdout para UTF-8 de forma segura
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    client = OdooMcpClient(base_url=args.url, api_key=args.api_key, timeout=args.timeout)

    try:
        if args.action == "ping":
            init_res = client.initialize()
            print(json.dumps(init_res, indent=2, ensure_ascii=False))
            return 0

        if args.action == "context":
            ctx = client.get_context()
            print(json.dumps(ctx, indent=2, ensure_ascii=False) if not isinstance(ctx, str) else ctx)
            return 0

        if args.action == "list_tools":
            tools = client.list_tools()
            print(json.dumps(tools, indent=2, ensure_ascii=False))
            return 0

        if args.action == "get_models":
            models_res = client.get_models()
            print(json.dumps(models_res, indent=2, ensure_ascii=False) if not isinstance(models_res, str) else models_res)
            return 0

        if args.action == "get_fields":
            if not args.model:
                raise ValueError("O parametro --model e obrigatorio para action='get_fields'.")
            fields_res = client.get_fields(args.model)
            print(json.dumps(fields_res, indent=2, ensure_ascii=False) if not isinstance(fields_res, str) else fields_res)
            return 0

        if args.action == "call_tool":
            if not args.tool_name:
                raise ValueError("O parametro --tool-name e obrigatorio para action='call_tool'.")
            tool_args = json.loads(args.tool_args) if isinstance(args.tool_args, str) else args.tool_args
            call_res = client.call_tool(args.tool_name, tool_args)
            print(json.dumps(call_res, indent=2, ensure_ascii=False) if not isinstance(call_res, str) else call_res)
            return 0

        if args.action == "read_group":
            if not args.model:
                raise ValueError("O parametro --model e obrigatorio para action='read_group'.")
            rg_res = client.read_group(
                model_name=args.model,
                domain=args.domain,
                groupby=parse_list_arg(args.groupby),
                aggregates=parse_list_arg(args.aggregates),
                having=args.having,
                limit=args.limit if args.limit > 0 else None,
                offset=args.offset if args.offset > 0 else None,
                order=args.order,
            )
            print(json.dumps(rg_res, indent=2, ensure_ascii=False) if not isinstance(rg_res, str) else rg_res)
            return 0

        if args.action == "search":
            if not args.model:
                raise ValueError("O parametro --model e obrigatorio para action='search'.")
            fields_list = parse_list_arg(args.fields)
            search_res = client.search(
                model_name=args.model,
                domain=args.domain,
                fields=fields_list,
                limit=args.limit if args.limit > 0 else None,
                offset=args.offset if args.offset > 0 else None,
                order=args.order,
            )
            print(json.dumps(search_res, indent=2, ensure_ascii=False))
            return 0

        raise ValueError(f"Acao '{args.action}' nao suportada.")

    except Exception as exc:
        sys.stderr.write(f"Erro pg_odoo_mcp_query: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
