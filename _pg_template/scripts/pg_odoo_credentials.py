#!/usr/bin/env python3
"""
Resolução das credenciais de acesso ao Odoo da Parâmetro Global (lado Python).

Espelha, campo a campo, a cascata de `pg_odoo_credentials_common.ps1`. Manter as duas
alinhadas é obrigatório: um agente que configure a chave e veja o PowerShell funcionar
e o Python falhar não tem como adivinhar que são caminhos diferentes.

CASCATA (a primeira que der chave ganha)
    0. caminho explícito -- vence tudo; mantém o contrato antigo dos chamadores.
    1. PG_ODOO_API_KEY (+ PG_ODOO_LOGIN) -- override por sessão e via de CI.
    2. PG_ODOO_KNOWLEDGE_TOKEN -- alias legado, aceite para não partir quem o use.
    3. ficheiro da máquina: %USERPROFILE%/.pg/odoo_credentials.json
       (ou PG_ODOO_CREDENTIALS_FILE). Fora de qualquer repositório, pelo que não pode
       ser commitado por engano. É a via normal, e é a última: não há degrau seguinte.

O `url` e a `db` não são segredo e vêm de credentials/pg_odoo_endpoint.json, versionado.
Por máquina ficam só o `login` e a `api_key`.

Dependências: nenhuma além da biblioteca standard.
"""

from __future__ import annotations

import json
import os
import sys

PLACEHOLDER = "COLAR_AQUI"

COMANDO_SETUP = (
    "powershell -NoProfile -ExecutionPolicy Bypass "
    r"-File .pg_framework\scripts\pg_init_odoo_credentials.ps1"
)


class ErroDeCredenciais(Exception):
    """Falha a resolver as credenciais do Odoo PG."""


def _raiz_framework() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def caminho_credenciais_da_maquina() -> str | None:
    """Onde vive o ficheiro por máquina.

    `PG_ODOO_CREDENTIALS_FILE` existe para os testes exercitarem a cascata sem tocar
    no perfil de quem corre.
    """
    explicito = os.environ.get("PG_ODOO_CREDENTIALS_FILE", "").strip()
    if explicito:
        return explicito
    raiz = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not raiz:
        return None
    return os.path.join(raiz, ".pg", "odoo_credentials.json")


def _ler_json(caminho: str) -> dict:
    # utf-8-sig e não utf-8: no Windows o Notepad, o PowerShell e o VS Code escrevem BOM
    # com facilidade, e um BOM fazia o json.load rebentar com um traceback em vez de uma
    # mensagem útil.
    try:
        with open(caminho, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        # Um ficheiro partido não pode passar por "sem credenciais": sem esta distinção
        # a cascata caía em silêncio para a chave partilhada e ninguém percebia porque é
        # que a chave pessoal "não pegou".
        raise ErroDeCredenciais(f"Credenciais ilegíveis em '{caminho}': {exc}") from exc


def _endpoint_partilhado() -> dict:
    caminho = os.path.join(_raiz_framework(), "credentials", "pg_odoo_endpoint.json")
    if not os.path.exists(caminho):
        return {}
    dados = _ler_json(caminho)
    return {"url": dados.get("url") or "", "db": dados.get("db") or ""}


def _e_placeholder(chave: str | None) -> bool:
    return (not chave) or (not chave.strip()) or (PLACEHOLDER in chave)


def origem_das_credenciais() -> dict:
    """De ONDE viriam as credenciais, sem nunca devolver a chave.

    Serve diagnósticos e o aviso do preflight. `tipo` é um de:
    `env`, `maquina`, `nenhuma`.
    """
    if os.environ.get("PG_ODOO_API_KEY", "").strip():
        return {"tipo": "env", "caminho": "PG_ODOO_API_KEY",
                "login": os.environ.get("PG_ODOO_LOGIN", "")}
    if os.environ.get("PG_ODOO_KNOWLEDGE_TOKEN", "").strip():
        return {"tipo": "env", "caminho": "PG_ODOO_KNOWLEDGE_TOKEN",
                "login": os.environ.get("PG_ODOO_LOGIN", "")}

    maquina = caminho_credenciais_da_maquina()
    if maquina and os.path.exists(maquina):
        try:
            dados = _ler_json(maquina)
        except ErroDeCredenciais:
            dados = {}
        if not _e_placeholder(dados.get("api_key")):
            return {"tipo": "maquina", "caminho": maquina, "login": dados.get("login", "")}

    return {"tipo": "nenhuma", "caminho": "", "login": ""}


def resolver_credenciais_pg(caminho_explicito: str | None = None,
                            login: str | None = None,
                            base_url: str | None = None,
                            database: str | None = None) -> dict:
    """Devolve `{url, db, login, api_key, origem}`.

    Levanta `ErroDeCredenciais` com a via de resolução quando não há chave: uma
    mensagem que não diga o comando a correr obriga quem a lê a procurar documentação,
    e é nesse momento que as pessoas desistem.
    """
    url = base_url or ""
    db = database or ""
    log = login or ""
    chave = ""
    origem = ""

    def _absorver(dados: dict) -> None:
        nonlocal url, db, log, chave
        url = url or (dados.get("url") or "")
        db = db or (dados.get("db") or "")
        log = log or (dados.get("login") or "")
        chave = dados.get("api_key") or ""

    if caminho_explicito:
        if not os.path.exists(caminho_explicito):
            raise ErroDeCredenciais(
                f"Credenciais não encontradas em '{caminho_explicito}'.")
        _absorver(_ler_json(caminho_explicito))
        origem = f"ficheiro explícito: {caminho_explicito}"
    elif os.environ.get("PG_ODOO_API_KEY", "").strip():
        chave = os.environ["PG_ODOO_API_KEY"].strip()
        log = log or os.environ.get("PG_ODOO_LOGIN", "").strip()
        origem = "PG_ODOO_API_KEY"
    elif os.environ.get("PG_ODOO_KNOWLEDGE_TOKEN", "").strip():
        chave = os.environ["PG_ODOO_KNOWLEDGE_TOKEN"].strip()
        log = log or os.environ.get("PG_ODOO_LOGIN", "").strip()
        origem = "PG_ODOO_KNOWLEDGE_TOKEN (alias legado)"
    else:
        maquina = caminho_credenciais_da_maquina()
        if maquina and os.path.exists(maquina):
            dados = _ler_json(maquina)
            if not _e_placeholder(dados.get("api_key")):
                _absorver(dados)
                origem = f"ficheiro da máquina: {maquina}"
        # Aqui acabava a cascata numa chave partilhada guardada no repositório. Saiu a
        # 2026-09-28, depois de a conta de serviço ser arquivada e de se provar pela
        # negativa que a chave deixou de autenticar.

    partilhado = _endpoint_partilhado()
    url = url or partilhado.get("url", "")
    db = db or partilhado.get("db", "")

    if _e_placeholder(chave):
        raise ErroDeCredenciais(
            "Sem credenciais de acesso ao Odoo da Parâmetro Global nesta máquina.\n"
            f"Resolver com:  {COMANDO_SETUP}\n"
            "Em alternativa, por sessão: definir PG_ODOO_LOGIN e PG_ODOO_API_KEY.\n"
            "Ver credentials/README.md.")
    if not log:
        raise ErroDeCredenciais(
            f"Chave obtida de '{origem}' mas sem login associado. Uma chave de um "
            "utilizador com o login de outro NÃO autentica. Definir PG_ODOO_LOGIN ou "
            f"correr: {COMANDO_SETUP}")
    if not url:
        raise ErroDeCredenciais(
            "Campo 'url' por resolver. Esperado em credentials/pg_odoo_endpoint.json.")
    if not db:
        raise ErroDeCredenciais(
            "Campo 'db' por resolver. Esperado em credentials/pg_odoo_endpoint.json.")

    return {"url": url, "db": db, "login": log, "api_key": chave, "origem": origem}


if __name__ == "__main__":
    # Diagnóstico: diz de onde vêm as credenciais, sem nunca imprimir a chave.
    info = origem_das_credenciais()
    print(json.dumps(info, ensure_ascii=False, indent=2))
