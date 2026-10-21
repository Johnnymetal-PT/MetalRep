#!/usr/bin/env python3
"""
Guarda de acesso ao Odoo para migração de dados entre bases.

PARA QUE SERVE
    Ponto único de passagem entre os scripts de migração e o Odoo. Nenhum script deve
    falar com o Odoo directamente: todos importam este módulo e chamam `Guard.kw(...)`.
    Por ser o único caminho, o que aqui é proibido fica proibido para todos.

A AUTORIDADE É A FINALIDADE, NÃO O NOME DA BASE DE DADOS
    A permissão de escrita deriva da `purpose` declarada para a ligação, nunca de uma
    comparação com o nome da base. Em Odoo.sh o nome da base muda a cada rebuild da
    branch, pelo que qualquer constante com o nome da staging fica obsoleta e passa a
    bloquear todo o trabalho. A ligação é identificada pelo `base_url`, que é estável.

    | purpose       | escrita                                      |
    |---------------|----------------------------------------------|
    | brodoo_dev    | permitida com --confirm                      |
    | client_test   | permitida com --confirm                      |
    | production    | bloqueada; exige --confirm E --allow-prod    |

CAMADAS DE PROTEÇÃO (todas têm de passar para uma escrita acontecer)
    1. o método está na lista branca e está classificado como escrita;
    2. a finalidade da ligação permite escrever;
    3. a execução foi confirmada (`confirmed=True`, tipicamente de `--confirm`);
    4. a chamada pediu explicitamente `allow_write=True`;
    5. produção exige ainda `allow_prod=True`.
    Acresce uma verificação de coerência na ligação: base cujo nome contém `main`
    (convenção de produção em Odoo.sh) com finalidade diferente de `production` aborta.

CREDENCIAIS — preferir o Odoo PG, não ficheiros locais

    Caminho preferido (nada toca em disco):
        alvo = resolver_alvo_por_projeto("odoo-reckon-ai", "client_test")
    As credenciais vêm de `pg.odoo.connection` pelo canal Brodoo, em memória. É o que a
    política do `AGENTS_SHARED.md` exige: «as credenciais do cliente ficam centralizadas
    no Odoo PG; nunca em secrets de repos de cliente nem copiadas para o repo».

    O primeiro salto (autenticação no Odoo PG) usa a credencial DESTA MÁQUINA, resolvida
    por `pg_odoo_credentials.py`. Desde 2026-09-28 deixou de ser uma chave partilhada:
    cada pessoa tem a sua, pelo que as escritas passam a ser atribuíveis no Odoo.

    Alternativa, só para ligações ainda não registadas:
        alvo = resolver_alvo("conn_alvo.json")
    O ficheiro tem de declarar a finalidade e contém uma API key — nunca versionar. Este
    caminho obriga quem executa a escrever um segredo para o disco, o que é precisamente
    o que se quer evitar; usar só quando não há registo em `pg.odoo.connection`.

    A regra de escrita depende só da finalidade, nunca da origem das credenciais.

Dependências: nenhuma além da biblioteca standard.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import socket
import time
import urllib.error
import urllib.request
import xmlrpc.client
from dataclasses import dataclass

# Duas vias porque este módulo é usado das duas maneiras: corrido a partir de
# `scripts/` (sys.path traz a pasta) e importado como `scripts.pg_odoo_migration_guard`
# a partir da raiz do repositório, que é como os testes o carregam.
try:
    from pg_odoo_credentials import ErroDeCredenciais, resolver_credenciais_pg
except ImportError:  # pragma: no cover - depende de como o módulo foi carregado
    from scripts.pg_odoo_credentials import ErroDeCredenciais, resolver_credenciais_pg

socket.setdefaulttimeout(120)

# Finalidades e o que cada uma autoriza. Espelha a Selection de pg.odoo.connection.
FINALIDADES = ("production", "brodoo_dev", "client_test")
FINALIDADES_COM_ESCRITA = ("brodoo_dev", "client_test")

METODOS_LEITURA = frozenset({
    "search", "search_read", "search_count", "read", "fields_get", "read_group",
    "name_get", "name_search", "get_metadata", "default_get", "check_access_rights",
    # Renderização de vistas. São leituras puras: devolvem o arch combinado e os metadados
    # dos campos, sem tocar em registos. Precisas para auditar quais os ecrãs que falham a
    # abrir — uma vista pode estar activa e rebentar, e só se descobre mandando-a renderizar.
    "get_view", "get_views", "fields_view_get",
    # `get_combined_arch` devolve o arch de uma vista JA COMBINADO com tudo o que
    # dela herda. O campo `arch_db` nao serve para isto: numa vista que herda ele
    # guarda apenas o diff, nao a vista inteira. Necessario para validar xpaths de
    # um addon contra o que o Odoo realmente vai ver. Leitura pura.
    "get_combined_arch",
})
METODOS_ESCRITA = frozenset({
    "create", "write", "unlink", "copy", "name_create", "web_save", "load",
    "button_immediate_install", "button_immediate_upgrade", "action_apply_inventory",
    "update_list", "action_validate_revaluation",
    # Contabilidade. Não são `write`, mas alteram o livro: lançar, repor a rascunho e
    # conciliar/desconciliar movimentos. Sem estarem aqui, o guard bloqueava-os como
    # método desconhecido — e uma migração de saldos precisa deles.
    "action_post", "button_draft", "button_cancel",
    "reconcile", "remove_move_reconcile",
    # Fluxo operacional: botões que fazem avançar documentos de venda, compra,
    # fabrico, armazém e qualidade. Não são `write`, mas geram movimentos de
    # stock, ordens de fabrico e lotes — logo, escrita, e ficam sujeitos às
    # mesmas guardas (finalidade + --confirm + allow_write, e --allow-prod em
    # produção). Sem estarem classificados, o guard bloqueava-os como método
    # desconhecido e nenhum fluxo ponta-a-ponta podia ser construído.
    # `action_confirm` serve sale.order, mrp.production e stock.picking.
    "action_confirm", "button_confirm",
    "button_mark_done", "action_generate_serial",
    "action_assign", "button_validate",
    "do_pass", "do_fail", "do_measure",
    # Cancelamento de venda. `sale.order` cancela por `action_cancel` e não por
    # `button_cancel`, e sem ele um documento confirmado não pode ser removido: o
    # `unlink` de sale.order só aceita rascunho ou cancelado. A alternativa era escrever
    # `state` à mão, que salta a lógica de cancelamento — o contorno que este guard
    # existe para impedir.
    "action_cancel",
    # Reabastecimento manual do Givachoice (`pg_manual_replenish`). `action_refresh`
    # e `action_rebuild_all` reconstroem a tabela `stock.replenishment.line` a partir
    # dos movimentos de consumo — apagam e recriam linhas, logo são escrita, mesmo
    # não sendo `write`. `action_rebuild_all` é o caminho destrutivo (unlink de tudo);
    # `action_refresh` é o incremental, e é o que acumulava linhas no defeito C1.
    "action_refresh", "action_rebuild_all",
    # `action_replenish_selected` / `pg_launch_replenishment` criam as compras a
    # partir das linhas de reabastecimento. ATENCAO: engolem excepcoes para uma
    # notificacao -- quem os chamar tem de verificar o que foi criado, nao o retorno.
    "action_replenish_selected", "pg_launch_replenishment",
    # Assistentes de confirmacao do armazem: backorder (processar parcial) e
    # aviso de consumo. Confirmam movimentos de stock, logo sao escrita.
    "process", "process_cancel_backorder", "action_confirm_consumption",
    # Criação de lotes na recepção (`pg_lot_management`): a porta de entrada do fluxo
    # de lotes vem de uma vista da base, e estes são os botões que ela expõe.
    "open_lot_creation_wizard", "clean_lot_wizard",
    "reset_and_recalculate_stock", "open_lot_barcode_reader",
    # Regeneração da lista de materiais a partir do modelo (`pg_field_validation` /
    # `pg_stock_quant`): é a cascata que apaga e recria os consumos.
    "action_update_bom", "pg_action_confirm_bom_selection_direct",
    # Carregar um pacote fiscal (plano de contas). É a escrita mais destrutiva da lista:
    # quando a empresa ainda não tem lançamentos, o `_load` APAGA o plano anterior e tudo
    # o que dele depende — contas, impostos, diários, posições fiscais e os `account.move`
    # existentes - antes de carregar o novo (account/models/chart_template.py:210-226).
    # Quando já há lançamentos não apaga nada e carrega o plano novo POR CIMA do antigo,
    # deixando os dois a coexistir. Ambos os resultados são irreversíveis sem restauro de
    # cópia de segurança, por isso quem chama deve verificar `account.move.line` primeiro.
    "try_loading",
    # Instalacao de idioma (`base.language.install.lang_install`). Activa o registo em
    # `res.lang` e, sobretudo, chama `_update_translations` sobre TODOS os modulos
    # instalados, carregando os termos traduzidos — e com `overwrite=True` por omissao,
    # substituindo traducoes personalizadas pelas oficiais. Escrever apenas
    # `res.lang.active = True` nao carrega termo nenhum: o idioma passa a poder ser
    # escolhido e o interface continua na lingua anterior
    # (odoo/addons/base/wizard/base_language_install.py:34-38).
    "lang_install",
    # Juntar contactos (`base.partner.merge.automatic.wizard.action_merge`). Passa por SQL
    # todas as chaves many2one do contacto de origem para o de destino e APAGA a origem
    # (odoo/addons/base/wizard/base_partner_merge.py, `_merge`). Irreversível sem cópia.
    # O sentido conta: o SQL salta o `write`, por isso muda também `sign.log.partner_id`,
    # que entra no hash de integridade da app Sign (enterprise/sign/models/sign_log.py,
    # LOG_FIELDS). O contacto com assinaturas tem de ser o destino.
    "action_merge",
    # Aprovisionamento. `stock.rule.run_scheduler()` e o que o cron "Procurement: run
    # scheduler" corre uma vez por dia (stock/data/stock_sequence_data.xml:46-57): percorre
    # as regras de reabastecimento e cria ordens de compra e de fabrico. Nao e `create`,
    # mas cria documentos — logo, escrita. `action_replenish` e o mesmo a pedido, sobre
    # as regras seleccionadas.
    "run_scheduler", "action_replenish",
    # Convite/reposição de acesso (`res.users.action_reset_password`). É o botão «Reenviar
    # e-mail de convite» / «Enviar instruções de redefinição de senha»: gera um token de
    # signup no parceiro e ENVIA um email ao utilizador. Não é `write`, mas escreve na base
    # e sai para fora — logo, escrita, sujeita às mesmas guardas.
    "action_reset_password",
    # Definições (`res.config.settings`). O `execute` aplica os valores do assistente:
    # ativa ou desativa grupos e módulos, pelo que é escrita, mesmo não sendo `write`.
    "execute",
})

LOG_POR_DEFEITO = os.path.join(".pg", "migration", "api_calls.log.jsonl")


class ErroDeGuarda(PermissionError):
    """Escrita recusada por uma das camadas de proteção."""


@dataclass
class Alvo:
    purpose: str
    base_url: str
    database: str
    login: str
    api_key: str

    @property
    def parece_producao(self) -> bool:
        """Em Odoo.sh a build de produção tem 'main' no nome da base."""
        return "main" in (self.database or "").lower()


def normalizar_base_url(url: str) -> str:
    """
    Remove barras finais e o sufixo '/odoo'.

    A partir do Odoo 17 o browser mostra o backoffice em `https://cliente.odoo.com/odoo`,
    e é esse URL que se copia. Mas os endpoints da API são servidos na raiz
    (`/xmlrpc/2/...`, `/web/database/list`), pelo que o sufixo produz 400 tanto na
    autenticação como na resolução do nome da base — e o erro não diz porquê.
    """
    limpo = (url or "").strip().rstrip("/")
    if limpo.lower().endswith("/odoo"):
        limpo = limpo[: -len("/odoo")].rstrip("/")
    return limpo


def _jsonrpc(base_url: str, params: dict, etiqueta: str):
    """Uma chamada JSON-RPC ao Odoo. Usado só para falar com o Odoo PG (canal Brodoo)."""
    corpo = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode("utf-8")
    pedido = urllib.request.Request(
        f"{normalizar_base_url(base_url)}/jsonrpc", data=corpo,
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))
    if dados.get("error"):
        erro = dados["error"]
        msg = (erro.get("data") or {}).get("message") or erro.get("message")
        raise ErroDeGuarda(f"Odoo PG recusou {etiqueta}: {msg}")
    return dados.get("result")


def _autenticar_pg(pg: dict) -> int:
    """uid no Odoo PG. O `execute_kw` exige o uid, não o login."""
    uid = _jsonrpc(pg["url"], {"service": "common", "method": "authenticate",
                               "args": [pg["db"], pg["login"], pg["api_key"], {}]},
                   "authenticate")
    if not uid:
        raise ErroDeGuarda(
            "Autenticação no Odoo PG falhou. Verificar a credencial desta máquina com: "
            "pg_init_odoo_credentials.ps1 -Verificar")
    return int(uid)


def _rpc(pg: dict, uid: int, model: str, method: str, args=None, kwargs=None):
    return _jsonrpc(pg["url"], {"service": "object", "method": "execute_kw",
                                "args": [pg["db"], uid, pg["api_key"], model, method,
                                         args or [], kwargs or {}]},
                    f"{model}.{method}")


def resolver_alvo_por_projeto(project_key: str, purpose: str,
                              credenciais_brodoo: str | None = None) -> Alvo:
    """
    Obtém as credenciais do Odoo-alvo a partir de `pg.odoo.connection`, pelo canal Brodoo.

    É o caminho preferido: as credenciais do cliente ficam **centralizadas no Odoo PG** e
    nunca são materializadas em disco no repositório do projeto — que é o que a política
    do `AGENTS_SHARED.md` exige. Um ficheiro de ligação local com a API key é um segredo
    a mais para proteger, e obriga quem executa a escrever segredos para o disco.

    Cadeia: `project.project.pg_project_key` -> `pg_repository_id` ->
    `pg.odoo.connection` da finalidade pedida.
    """
    if purpose not in FINALIDADES:
        raise ValueError(f"Finalidade inválida: {purpose!r}. Aceites: {', '.join(FINALIDADES)}")

    # A resolução vive no ponto único (pg_odoo_credentials.py): a chave é de quem corre
    # e vive fora do repositório. O parâmetro `credenciais_brodoo` continua a vencer
    # tudo, para não partir chamadores que apontem a um ficheiro próprio.
    try:
        pg = resolver_credenciais_pg(credenciais_brodoo)
    except ErroDeCredenciais as exc:
        raise ValueError(str(exc)) from exc

    uid = _autenticar_pg(pg)

    proj = _rpc(pg, uid, "project.project", "search_read",
                [[["pg_project_key", "=", project_key]]],
                {"fields": ["pg_repository_id"], "limit": 1})
    if not proj:
        raise ValueError(f"Projeto com pg_project_key='{project_key}' não encontrado no Odoo PG.")
    repo = proj[0].get("pg_repository_id")
    if not repo:
        raise ValueError(f"O projeto '{project_key}' não tem repositório associado.")

    # Com o pg_brodoo 19.0.1.15.0 a `api_key` passa a exigir o grupo "Credenciais dos Odoo
    # dos clientes" (a 2026-10-07 essa versão ainda não está instalada em produção).
    # Sem ele o Odoo recusa o CAMPO, e a mensagem que devolve não diz o que pedir.
    try:
        ligacoes = _rpc(pg, uid, "pg.odoo.connection", "search_read",
                        [[["repository_id", "=", int(repo[0])],
                          ["purpose", "=", purpose], ["active", "=", True]]],
                        {"fields": ["base_url", "database", "login", "api_key"], "limit": 1})
    except ErroDeGuarda as exc:
        if "api_key" in str(exc):
            raise ErroDeGuarda(
                "Sem permissão para ler a API key das ligações Odoo do cliente. Falta o "
                "grupo 'Credenciais dos Odoo dos clientes: Ler credenciais', que se "
                "atribui em Definições > Utilizadores, na categoria Administração. "
                f"Detalhe do Odoo: {exc}") from exc
        raise
    if not ligacoes:
        raise ValueError(
            f"Sem ligação Odoo purpose='{purpose}' para o projeto '{project_key}'. "
            "Configurar em Brodoo > Repositório > Ligações Odoo do cliente.")
    c = ligacoes[0]

    faltam = [k for k in ("base_url", "login", "api_key") if not c.get(k)]
    if faltam:
        raise ValueError(f"Ligação '{purpose}' de '{project_key}' sem: {', '.join(faltam)}")

    return Alvo(
        purpose=purpose,
        base_url=normalizar_base_url(str(c["base_url"])),
        database=c.get("database") or "",
        login=c["login"],
        api_key=c["api_key"],
    )


def resolver_alvo(conn_file: str) -> Alvo:
    """
    Lê um ficheiro de ligação local e valida o que é obrigatório.

    Preferir `resolver_alvo_por_projeto()`: este caminho obriga a ter a API key em disco,
    o que a política de credenciais da framework quer evitar. Fica para casos em que a
    ligação ainda não está registada em `pg.odoo.connection`.
    """
    # utf-8-sig e não utf-8: no Windows o Notepad, o PowerShell (Set-Content -Encoding utf8)
    # e o VS Code escrevem BOM com facilidade, e um BOM fazia o json.load rebentar com um
    # traceback em vez de uma mensagem útil. Lê os dois casos.
    try:
        with open(conn_file, encoding="utf-8-sig") as fh:
            dados = json.load(fh)
    except FileNotFoundError:
        raise ValueError(f"Ficheiro de ligação não encontrado: '{conn_file}'") from None
    except json.JSONDecodeError as erro:
        raise ValueError(f"'{conn_file}' não é JSON válido: {erro}") from None

    purpose = dados.get("purpose")
    if purpose not in FINALIDADES:
        raise ValueError(
            f"'{conn_file}': campo 'purpose' ausente ou inválido ({purpose!r}). "
            f"Valores aceites: {', '.join(FINALIDADES)}. "
            "A finalidade é o que autoriza (ou não) a escrita — não é opcional."
        )

    faltam = [c for c in ("base_url", "login", "api_key") if not dados.get(c)]
    if faltam:
        raise ValueError(f"'{conn_file}': campos obrigatórios em falta: {', '.join(faltam)}")

    return Alvo(
        purpose=purpose,
        base_url=normalizar_base_url(str(dados["base_url"])),
        database=dados.get("database") or "",
        login=dados["login"],
        api_key=dados["api_key"],
    )


def listar_bases(base_url: str):
    """
    Nomes de base de dados expostos pela instância, via POST /web/database/list.

    É o caminho barato de resolução (sem SSH). Devolve lista vazia quando o endpoint
    está fechado (`list_db=False`), que é o caso comum em produção.
    """
    # A construção do Request tem de estar DENTRO do try: um base_url sem esquema
    # (ex.: 'cliente.odoo.com', que existe em ligações reais) faz o urllib levantar
    # ValueError aqui, e isso rebentava com traceback em vez de devolver vazio.
    try:
        pedido = urllib.request.Request(
            f"{normalizar_base_url(base_url)}/web/database/list",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
        return list(corpo.get("result") or [])
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return []


class Guard:
    """
    Ligação ao Odoo com as escritas condicionadas pela finalidade da base-alvo.

        alvo = resolver_alvo("conn_brodoo.json")
        o = Guard(alvo, confirmed=args.confirm, allow_prod=args.allow_prod)
        o.kw("res.partner", "search_count", [[]])                       # leitura
        o.kw("res.partner", "write", [ids, vals], allow_write=True)     # escrita
    """

    def __init__(self, alvo: Alvo, confirmed: bool = False, allow_prod: bool = False,
                 log_path: str | None = None):
        self.alvo = alvo
        self.confirmed = bool(confirmed)
        self.allow_prod = bool(allow_prod)
        self.log_path = log_path or LOG_POR_DEFEITO

        # A coerência é verificada ANTES de autenticar: é erro de configuração, apanha-se
        # sem rede, e não se toca numa base de produção para descobrir que não devíamos.
        self._verificar_coerencia()
        self._autenticar()
        # E outra vez depois, porque o auto-heal pode ter resolvido um nome diferente do
        # declarado (rebuild da branch) — o nome resolvido também tem de ser coerente.
        self._verificar_coerencia()

    def _verificar_coerencia(self) -> None:
        if self.alvo.parece_producao and self.alvo.purpose != "production":
            raise ErroDeGuarda(
                f"ABORTADO: a base '{self.alvo.database}' parece produção (contém 'main') "
                f"mas a ligação está declarada como '{self.alvo.purpose}'. "
                "Corrigir a ligação antes de continuar."
            )

    # -- ligação ---------------------------------------------------------

    def _autenticar(self) -> None:
        """
        Autentica no alvo. Se falhar sem nome de base (ou com um nome obsoleto por
        rebuild da branch), tenta resolver o nome actual e repete.
        """
        comum = xmlrpc.client.ServerProxy(f"{self.alvo.base_url}/xmlrpc/2/common")

        def tentar(db: str):
            if not db:
                return None
            try:
                return comum.authenticate(db, self.alvo.login, self.alvo.api_key, {})
            except Exception:
                return None

        uid = tentar(self.alvo.database)

        if not uid:
            bases = listar_bases(self.alvo.base_url)
            candidatas = [b for b in bases if b != self.alvo.database]
            if len(candidatas) == 1:
                uid = tentar(candidatas[0])
                if uid:
                    print(f"  nome da base resolvido: '{self.alvo.database or '(vazio)'}' "
                          f"-> '{candidatas[0]}'")
                    self.alvo.database = candidatas[0]
            elif len(candidatas) > 1:
                raise ErroDeGuarda(
                    f"Autenticação falhou e a instância expõe várias bases ({', '.join(candidatas)}). "
                    "Indicar 'database' no ficheiro de ligação."
                )

        if not uid:
            raise ErroDeGuarda(
                f"Autenticação falhou em {self.alvo.base_url} (base '{self.alvo.database}'). "
                "Validar base/login/api_key; em Odoo.sh confirmar se a build foi reconstruída."
            )

        self.uid = uid
        self._modelos = xmlrpc.client.ServerProxy(f"{self.alvo.base_url}/xmlrpc/2/object")

    # -- chamada ---------------------------------------------------------

    def _validar(self, method: str, allow_write: bool) -> None:
        if method in METODOS_ESCRITA:
            if self.alvo.purpose not in FINALIDADES_COM_ESCRITA:
                if self.alvo.purpose != "production":
                    raise ErroDeGuarda(
                        f"BLOQUEADO: escrita '{method}' com finalidade '{self.alvo.purpose}'."
                    )
                if not self.allow_prod:
                    raise ErroDeGuarda(
                        f"BLOQUEADO: escrita '{method}' em PRODUÇÃO. "
                        "Exige --allow-prod explícito, depois de um dry-run revisto."
                    )
            if not self.confirmed:
                raise ErroDeGuarda(
                    f"BLOQUEADO: escrita '{method}' sem confirmação. Nada é escrito sem --confirm."
                )
            if not allow_write:
                raise ErroDeGuarda(
                    f"BLOQUEADO: escrita '{method}' sem allow_write=True na chamada. "
                    "O consentimento é por chamada, para nenhuma passagem de leitura escrever por acidente."
                )
        elif method not in METODOS_LEITURA:
            raise ErroDeGuarda(
                f"BLOQUEADO: método desconhecido '{method}'. "
                "Classificá-lo em METODOS_LEITURA ou METODOS_ESCRITA antes de o usar — "
                "um método não classificado pode escrever sem passar pelas guardas."
            )

    def _registar(self, model: str, method: str, args) -> None:
        pasta = os.path.dirname(self.log_path)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        linha = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "purpose": self.alvo.purpose,
            "database": self.alvo.database,
            "model": model,
            "method": method,
            "args_preview": str(args)[:200],
        }
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(linha, ensure_ascii=False) + "\n")

    def kw(self, model: str, method: str, args=None, kwargs=None, allow_write: bool = False):
        """Executa `execute_kw` no alvo, depois de passar todas as guardas."""
        self._validar(method, allow_write)
        args = args or []
        kwargs = kwargs or {}
        self._registar(model, method, args)

        ultimo = None
        for tentativa in range(6):
            try:
                return self._modelos.execute_kw(
                    self.alvo.database, self.uid, self.alvo.api_key, model, method, args, kwargs
                )
            except xmlrpc.client.Fault:
                raise  # erro real do Odoo, não de transporte — não repetir
            except Exception as erro:
                ultimo = erro
                time.sleep(min(2 + tentativa, 6))
        raise ultimo


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verifica uma ligação Odoo de migração (não escreve nada)."
    )
    ap.add_argument("conn", nargs="?",
                    help="ficheiro JSON de ligação (alternativa a --project-key/--purpose)")
    ap.add_argument("--project-key", help="project_key do projeto no Odoo PG (caminho preferido)")
    ap.add_argument("--purpose", choices=FINALIDADES, help="finalidade da ligação a usar")
    ap.add_argument("--log", default=None, help=f"caminho do log (defeito: {LOG_POR_DEFEITO})")
    args = ap.parse_args()

    if not args.conn and not (args.project_key and args.purpose):
        ap.error("indicar um ficheiro de ligação, ou --project-key com --purpose")

    try:
        if args.project_key:
            alvo = resolver_alvo_por_projeto(args.project_key, args.purpose)
        else:
            alvo = resolver_alvo(args.conn)
        guarda = Guard(alvo, confirmed=False, allow_prod=False, log_path=args.log)
        total = guarda.kw("res.users", "search_count", [[]])
    except (ValueError, ErroDeGuarda) as erro:
        print(f"FALHOU: {erro}")
        return 1

    escreve = ("sim, com --confirm" if alvo.purpose in FINALIDADES_COM_ESCRITA
               else "não (exige --confirm e --allow-prod)")
    print(f"LIGAÇÃO OK  uid={guarda.uid}")
    print(f"  finalidade : {alvo.purpose}")
    print(f"  base       : {alvo.database}")
    print(f"  utilizadores: {total}")
    print(f"  escrita    : {escreve}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
