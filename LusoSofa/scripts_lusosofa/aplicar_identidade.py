#!/usr/bin/env python3
"""Aplica a identidade Lusosofá no Odoo 18 de https://lusosofa.parametro.pt.

Por defeito faz **dry-run**: mostra o que mudaria e não escreve nada.
Para escrever mesmo:

    py scripts_lusosofa/aplicar_identidade.py --aplicar

Credenciais: lê ``~/.lusosofa_odoo.json`` (ou ``--creds <ficheiro>``), com as
chaves ``url``, ``db``, ``login`` e ``api_key``. Nunca as escreve para o
repositório.

Passos, pela ordem em que correm:

1. confirma a série do destino contra o próprio destino (18.0) e recusa se não bater
2. tira resguardo do SCSS de personalização e do registo da empresa para
   ``.backup_lusosofa_<data>.json``
3. confirma que ``pg_lusosofa_theme`` está instalado (a instalação em si
   faz-se uma vez à mão pelo Odoo — ver ``INSTRUCOES_MANUAIS``)
4. selecciona a paleta e as fontes nos valores de utilizador do website
4b. invalida o bundle CSS compilado, se for anterior à última actualização
   do módulo — sem isto o site serve o CSS antigo e nada o denuncia
5. preenche a empresa, o nome do website e corrige o typo do catálogo
6. activa o espanhol
7. verifica contra o destino e imprime o resultado

Nada aqui apaga o que existe: o SCSS anterior fica no resguardo e o módulo
desinstala-se sem tocar nas páginas.
"""

import argparse
import base64
import datetime
import json
import mimetypes
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MODULO = "pg_lusosofa_theme"
SERIE_ESPERADA = "18.0"

# Dados confirmados pela Lara a 2026-09-21.
EMPRESA = {
    "name": "Lusosofá — Feel the Confort, Lda.",
    "street": "Rua do Porto, 94",
    "city": "Figueiró",
    "zip": "4590-196",
    "phone": "+351 255 181 731",
    "email": "lusosofa@gmail.com",
    "website": "https://lusosofa.parametro.pt",
    "vat": "PT516435337",
}


# ─────────────────────────────── canal Odoo ────────────────────────────────

class Odoo:
    def __init__(self, creds):
        self.url = creds["url"].rstrip("/")
        self.db = creds["db"]
        self.login = creds["login"]
        self.key = creds["api_key"]
        self.uid = self._rpc("common", "authenticate", [self.db, self.login, self.key, {}])
        if not self.uid:
            raise SystemExit("Autenticação falhou. Verifica url, db, login e api_key.")
        self._lang = None

    def _rpc(self, service, method, args, timeout=180):
        payload = {"jsonrpc": "2.0", "method": "call",
                   "params": {"service": service, "method": method, "args": args}}
        req = urllib.request.Request(self.url + "/jsonrpc", json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
        data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        if "error" in data:
            msg = data["error"].get("data", {}).get("message") or data["error"].get("message")
            raise RuntimeError(str(msg)[:500])
        return data["result"]

    def _kw_cru(self, model, method, args=None, kwargs=None, timeout=180):
        """Chamada sem contexto — só para resolver a própria língua do site."""
        return self._rpc("object", "execute_kw",
                         [self.db, self.uid, self.key, model, method, args or [], kwargs or {}],
                         timeout=timeout)

    def lingua_do_site(self):
        """Código da língua que o website serve por defeito (ex.: ``pt_PT``).

        Sem ``lang`` no contexto, o ``execute_kw`` lê e escreve o valor
        ``en_US`` dos campos traduzíveis, mesmo que o utilizador autenticado
        seja pt_PT. Foi assim que a correcção de ``CADERIÃO OSLO`` acertou no
        ``en_US`` enquanto o site continuava a mostrar o typo — e que a
        verificação, a ler pelo mesmo canal, a deu por feita.

        A língua certa é a do **website**, não a do utilizador: o que importa
        é o que o visitante recebe.
        """
        if self._lang is None:
            site = self._kw_cru("website", "search_read", [[]],
                                {"fields": ["default_lang_id"], "limit": 1})
            lang_id = site[0]["default_lang_id"][0] if site and site[0]["default_lang_id"] else None
            if not lang_id:
                raise SystemExit("ABORTADO: o website não tem língua por defeito definida.")
            self._lang = self._kw_cru("res.lang", "read", [[lang_id], ["code"]])[0]["code"]
        return self._lang

    def kw(self, model, method, args=None, kwargs=None, timeout=180):
        kwargs = dict(kwargs or {})
        contexto = dict(kwargs.get("context") or {})
        contexto.setdefault("lang", self.lingua_do_site())
        kwargs["context"] = contexto
        return self._rpc("object", "execute_kw",
                         [self.db, self.uid, self.key, model, method, args or [], kwargs or {}],
                         timeout=timeout)

    def search_read(self, model, domain=None, fields=None, limit=0):
        opts = {"fields": fields or []}
        if limit:
            opts["limit"] = limit
        return self.kw(model, "search_read", [domain or []], opts)

    def versao(self):
        return self._rpc("common", "version", [])["server_serie"]


# ────────────────────────────── passo 1: série ─────────────────────────────

def confirmar_serie(odoo):
    serie = odoo.versao()
    base = odoo.search_read("ir.module.module",
                            [["name", "=", "base"]], ["latest_version"])
    versao_base = base[0]["latest_version"] if base else "?"
    print(f"  destino: série {serie}, módulo base {versao_base}")
    if not serie.startswith(SERIE_ESPERADA):
        raise SystemExit(
            f"ABORTADO: o destino corre a série {serie} e o módulo é para "
            f"{SERIE_ESPERADA}. Não se implanta código de outra série."
        )
    return serie


# ───────────────────────────── passo 2: resguardo ──────────────────────────

def resguardo(odoo):
    carimbo = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dados = {
        "tirado_em_utc": carimbo,
        "base": odoo.db,
        "url": odoo.url,
        "website": odoo.search_read("website", [], ["name", "theme_id", "language_ids"]),
        "empresa": odoo.search_read("res.company", [], list(EMPRESA)),
        "scss": {},
        "produtos": odoo.search_read("product.template", [["is_published", "=", True]],
                                     ["name", "list_price"]),
    }
    for att in odoo.search_read("ir.attachment", [["url", "like", "/_custom/"]],
                                ["url", "datas"]):
        dados["scss"][att["url"]] = (
            base64.b64decode(att["datas"]).decode("utf-8", "replace") if att["datas"] else ""
        )
    destino = RAIZ / f".backup_lusosofa_{carimbo}.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1, default=str),
                       encoding="utf-8")
    print(f"  resguardo: {destino.name} ({len(dados['scss'])} ficheiros SCSS)")
    return destino


# ──────────────────────────── passo 3: instalação ──────────────────────────

def empacotar():
    alvo = RAIZ / f"{MODULO}.zip"
    origem = RAIZ / MODULO
    if not origem.is_dir():
        raise SystemExit(f"ABORTADO: não encontrei {origem}")
    with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(origem.rglob("*")):
            if f.is_file() and f.name != ".DS_Store":
                z.write(f, f.relative_to(RAIZ))
    print(f"  empacotado: {alvo.name} ({alvo.stat().st_size // 1024} KB)")
    return alvo


def modulo_instalado(odoo):
    recs = odoo.search_read("ir.module.module", [["name", "=", MODULO]],
                            ["state", "latest_version"])
    return recs[0] if recs and recs[0]["state"] == "installed" else None


def versao_local():
    """Versão declarada no manifesto do repositório."""
    texto = (RAIZ / MODULO / "__manifest__.py").read_text(encoding="utf-8")
    m = re.search(r"['\"]version['\"]\s*:\s*['\"]([^'\"]+)['\"]", texto)
    if not m:
        raise SystemExit("ABORTADO: não consegui ler a versão do manifesto.")
    return m.group(1)


def importar_modulo(odoo, escrever, forcar=False):
    """Importa o .zip pelo modelo ``base.import.module``.

    Não confundir com o controlador ``/base_import_module/login_upload``, esse
    sim fechado a chaves API: usa ``request.session.authenticate()``, que é
    login interactivo e exige palavra-passe.

    ``base.import.module`` é outra coisa — é o modelo por trás do próprio ecrã
    *Definições > Aplicações > Importar Módulo*. Chamá-lo por ``execute_kw``
    percorre exactamente o mesmo caminho que a interface percorre, com a mesma
    ACL a decidir: `access.base.import.module`, restrita ao grupo
    *Administração / Configurações* (``base.group_system``). Não é uma volta à
    autenticação; é a mesma porta, sem browser. Requer o addon
    ``base_import_module`` instalado — está, nesta base.

    Aviso que a versão não dá: números de versão iguais não provam código
    igual, porque nada obriga a subir a versão ao alterar um ficheiro. Por
    isso existe o ``--forcar-modulo``, e por isso o passo 7 verifica o CSS
    servido em vez de acreditar no número.
    """
    alvo = empacotar()
    instalado = odoo.search_read("ir.module.module", [["name", "=", MODULO]],
                                 ["state", "latest_version"])
    estado = instalado[0]["state"] if instalado else "ausente"
    no_servidor = instalado[0]["latest_version"] if instalado else "—"
    local = versao_local()
    print(f"  servidor: {no_servidor} ({estado})   repositório: {local}")

    if estado == "installed" and no_servidor == local and not forcar:
        print("  mesma versão — nada a importar (usa --forcar-modulo para reimportar)")
        return

    if not escrever:
        print(f"  [dry-run] importaria {alvo.name} com 'Forçar init' ligado")
        return

    dados = base64.b64encode(alvo.read_bytes()).decode()
    rec = odoo.kw("base.import.module", "create", [{"module_file": dados, "force": True}])
    odoo.kw("base.import.module", "import_module", [[rec]], timeout=900)
    resultado = odoo.kw("base.import.module", "read", [[rec], ["state", "import_message"]])[0]
    print(f"  importado: estado {resultado['state']}")
    if resultado.get("import_message"):
        print(f"  mensagem do Odoo: {resultado['import_message']}")

    depois = odoo.search_read("ir.module.module", [["name", "=", MODULO]],
                              ["state", "latest_version"])[0]
    print(f"  servidor agora: {depois['latest_version']} ({depois['state']})")
    if depois["latest_version"] != local:
        raise SystemExit(
            f"ABORTADO: o servidor ficou em {depois['latest_version']} e o "
            f"repositório tem {local}. A importação não pegou."
        )


# ───────────────── passo 4: seleccionar paleta e tipografia ────────────────
#
# O website guarda as escolhas do editor em SCSS na base, e essas escolhas
# ganham ao que o módulo declara. É por isso que instalar o módulo sozinho não
# muda nada: é preciso seleccionar lá a paleta e as fontes, que é o que o
# editor faria à mão.
#
# As cores individuais passam a `null` de propósito: `o-map-omit` retira as
# entradas nulas, e o que fica a valer são as cores da paleta `lusosofa`
# definida no módulo. É assim que a identidade fica versionada no repositório
# em vez de ficar presa a esta base de dados.

PALETA_SCSS = """\
$o-user-color-palette: map-merge($o-user-color-palette, o-map-omit((
    'o-color-1': null,
    'o-color-2': null,
    'o-color-3': null,
    'o-color-4': null,
    'o-color-5': null,
    // O cabeçalho vai ao preto da marca, não ao ouro.
    //
    // O `'menu': 4` declarado no módulo não chega: a resolução por defeito
    // aterra na cor 1 e o cabeçalho sai dourado, com o logótipo — que tem
    // fundo preto — assente nele como um rectângulo colado. É aqui, no
    // ficheiro de personalização, que a escolha manda, porque é aqui que o
    // editor do site a escreveria se alguém a fizesse à mão.
    //
    // Fica a referência à cor 4 e não o hexadecimal: assim o cabeçalho
    // acompanha a paleta se ela mudar, em vez de ficar preso a um valor.
    'menu': 4,
    // -- hook --
)));
"""

VALORES_SCSS = """\
// This file is meant to be edited automatically by the user. The variables it
// contains should not be renamed otherwise it would break existing customers
// customizations.

$o-user-website-values: map-merge($o-user-website-values, o-map-omit((
    'menu-gradient': null,
    'menu-secondary-gradient': null,
    'footer-gradient': null,
    'copyright-gradient': null,
    'o-cc1-bg-gradient': null,
    'o-cc2-bg-gradient': null,
    'o-cc3-bg-gradient': null,
    'o-cc4-bg-gradient': null,
    'o-cc5-bg-gradient': null,
    'font': 'Instrument Sans',
    'headings-font': 'Schibsted Grotesk',
    'navbar-font': 'Instrument Sans',
    'buttons-font': 'JetBrains Mono',
    'color-palettes-number': null,
    'color-palettes-name': 'lusosofa',
    'btn-ripple': null,
    'header-template': null,
    'footer-template': 'links',
    'footer-scrolltop': null,
    'google-fonts': null,
    'google-local-fonts': null,
    'uploaded-local-fonts': null,
    'menu-box-shadow': null,
    'header-font-size': 1rem,
    // -- hook --
)));
"""

SCSS_ALVO = {
    "/_custom/web.assets_frontend/website/static/src/scss/options/colors/user_color_palette.scss":
        PALETA_SCSS,
    "/_custom/web.assets_frontend/website/static/src/scss/options/user_values.scss":
        VALORES_SCSS,
}


def aplicar_scss(odoo, escrever):
    for url, conteudo in SCSS_ALVO.items():
        recs = odoo.search_read("ir.attachment", [["url", "=", url]], ["id", "name"])
        if not recs:
            print(f"  ! não encontrei o anexo {url} — saltado")
            continue
        nome = url.rsplit("/", 1)[-1]
        if escrever:
            odoo.kw("ir.attachment", "write",
                    [[recs[0]["id"]],
                     {"datas": base64.b64encode(conteudo.encode()).decode()}])
            print(f"  escrito: {nome}")
        else:
            print(f"  [dry-run] escreveria {nome} ({len(conteudo)} chars)")


# ────────────────── passo 4b: recompilar o bundle se estiver velho ─────────
#
# Instalar o módulo não basta, e seleccionar a paleta também não: o CSS que o
# visitante recebe é um ficheiro compilado, guardado como anexo. Se o módulo
# mudar e o anexo não for invalidado, o site continua a servir o compilado
# anterior — sem nada o denunciar, porque o SCSS de origem confere.
#
# Apagar o anexo é a forma suportada de o invalidar: o Odoo recompila-o ao
# primeiro pedido seguinte. É cache, não é conteúdo — nada se perde, e o
# passo 7 confirma o resultado.


def invalidar_bundle(odoo, escrever):
    mods = odoo.search_read("ir.module.module", [["name", "=", MODULO]], ["write_date"])
    if not mods:
        print("  ! módulo ausente — saltado")
        return

    anexos = odoo.search_read("ir.attachment", [["name", "=", BUNDLE]],
                              ["id", "url", "create_date"])
    if not anexos:
        print(f"  ! não encontrei o bundle {BUNDLE}")
        return

    # Só o que o site serve. Há bundles órfãos de temas anteriores que também
    # são anteriores ao módulo, e apagá-los não resolve nada — só alarga o que
    # se mexe em produção sem razão.
    servido = max(anexos, key=lambda a: a["create_date"])
    if servido["create_date"] >= mods[0]["write_date"]:
        print("  bundle já é posterior à última actualização do módulo — nada a fazer")
        return

    if escrever:
        odoo.kw("ir.attachment", "unlink", [[servido["id"]]])
        print(f"  apagado: {servido['url']} (compilado {servido['create_date']} UTC)")
    else:
        print(f"  [dry-run] apagaria {servido['url']} "
              f"(compilado {servido['create_date']} UTC)")

    if not escrever:
        return

    # Força a recompilação já, para que não seja o primeiro visitante a
    # pagá-la — e para que o passo 7 encontre o ficheiro novo.
    #
    # O pedido regressar não garante que o anexo já exista: a 2026-09-23 o
    # `urlopen` voltou e o anexo novo só ficou gravado 80 segundos depois,
    # tempo suficiente para o passo 7 correr e concluir sobre um ficheiro que
    # ainda não estava lá. Por isso confirma-se, em vez de se assumir.
    # 10 minutos: a compilação do bundle completo passou dos 5 a 2026-09-23,
    # e o aviso de desistência assusta sem razão quando ela ainda está a
    # correr — o ficheiro apareceu pouco depois.
    limite = time.time() + 600
    while time.time() < limite:
        urllib.request.urlopen(odoo.url + "/", timeout=180).read()
        novos = [a for a in odoo.search_read("ir.attachment", [["name", "=", BUNDLE]],
                                             ["url", "create_date"])
                 if a["create_date"] > servido["create_date"]]
        if novos:
            print(f"  recompilado: {novos[0]['url']} ({novos[0]['create_date']} UTC)")
            return
        time.sleep(10)

    print("  ! o bundle não ficou gravado dentro do tempo de espera — "
          "o passo 7 dirá o estado real")


# ───────────────────── passo 5: empresa, website, catálogo ─────────────────

def aplicar_dados(odoo, escrever):
    empresa = odoo.search_read("res.company", [], ["id", "name"])[0]
    if escrever:
        odoo.kw("res.company", "write", [[empresa["id"]], EMPRESA])
        print(f"  escrito: empresa {empresa['name']} -> {EMPRESA['name']}")
    else:
        print(f"  [dry-run] empresa {empresa['name']} -> {EMPRESA['name']}")

    site = odoo.search_read("website", [], ["id", "name"])[0]
    valores = {"name": "Lusosofá", "domain": "https://lusosofa.parametro.pt"}
    if escrever:
        odoo.kw("website", "write", [[site["id"]], valores])
        print(f"  escrito: website {site['name']} -> Lusosofá")
    else:
        print(f"  [dry-run] website {site['name']} -> Lusosofá")

    # Typo no catálogo: CADERIÃO -> CADEIRÃO.
    for p in odoo.search_read("product.template",
                              [["name", "like", "CADERI"]], ["id", "name"]):
        novo = p["name"].replace("CADERIÃO", "CADEIRÃO").replace("CADERIAO", "CADEIRAO")
        if escrever:
            odoo.kw("product.template", "write", [[p["id"]], {"name": novo}])
            print(f"  escrito: produto {p['name']} -> {novo}")
        else:
            print(f"  [dry-run] produto {p['name']} -> {novo}")


# ────────────────────────── passo 6: espanhol ──────────────────────────────

def activar_espanhol(odoo, escrever):
    """Activa o es_ES pelo assistente `base.language.install`.

    O `res.lang._activate_lang` é privado e não se chama por RPC. O caminho
    público é o mesmo assistente que a interface usa — ver
    `addons/base/wizard/base_language_install.py` (18.0): campo `lang_ids`
    e método `lang_install()`.

    `overwrite` fica a False de propósito. O valor por defeito do assistente
    é True, e isso substituiria traduções já personalizadas pelas oficiais.
    Aqui não há nenhuma em espanhol, mas não é o defeito que se quer herdar
    da próxima vez que este script correr.
    """
    activas = odoo.search_read("res.lang", [["code", "=", "es_ES"], ["active", "=", True]],
                               ["id"])
    if activas:
        print("  espanhol já está activo")
        return

    langs = odoo.kw("res.lang", "search_read",
                    [[["code", "=", "es_ES"]]],
                    {"fields": ["id", "name"], "context": {"active_test": False}})
    if not langs:
        raise SystemExit(
            "ABORTADO: não existe res.lang com o código es_ES nesta base. "
            "Saltar em silêncio faria o passo 7 reportar sucesso sobre um "
            "idioma que nunca foi activado."
        )

    if not escrever:
        print(f"  [dry-run] instalaria {langs[0]['name']} e ligava-o ao website")
        return

    print("  a instalar traduções (percorre os módulos instalados, demora)...")
    wiz = odoo.kw("base.language.install", "create",
                  [{"lang_ids": [(6, 0, [langs[0]["id"]])], "overwrite": False}])
    odoo.kw("base.language.install", "lang_install", [[wiz]], timeout=900)

    site = odoo.search_read("website", [], ["id"])[0]
    odoo.kw("website", "write", [[site["id"]], {"language_ids": [(4, langs[0]["id"])]}])
    print(f"  escrito: {langs[0]['name']} activo e ligado ao website")


# ─────────────────────────── passo 7: verificação ──────────────────────────

BUNDLE = "web.assets_frontend.min.css"
AA = 4.5


def _luminancia(hexa):
    hexa = hexa.lstrip("#")
    if len(hexa) == 3:
        hexa = "".join(c * 2 for c in hexa)
    canais = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    canais = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in canais]
    return .2126 * canais[0] + .7152 * canais[1] + .0722 * canais[2]


def _contraste(frente, fundo):
    a, b = _luminancia(frente), _luminancia(fundo)
    claro, escuro = max(a, b), min(a, b)
    return (claro + .05) / (escuro + .05)


def verificar_bundle(odoo, modulo_escrito_em):
    """Verifica o CSS que o servidor serve, não o SCSS de onde ele vem.

    Duas coisas distintas, e foi por as confundir que o defeito de contraste
    ficou no ar depois de corrigido: o módulo foi reimportado às 16:41 de
    2026-09-22 e o bundle continuou a ser o compilado às 16:34. O SCSS de
    origem conferia; o que o browser recebia é que não.

    Por isso aqui não se procuram valores esperados — calcula-se o contraste
    real de cada combinação de cor a partir do ficheiro servido. É a
    propriedade que interessa, e sobrevive a mudanças de paleta.

    Qual é «o ficheiro servido» pergunta-se à homepage, não à base. Escolher
    o anexo com data mais recente parece equivalente e não é: logo a seguir a
    invalidar o bundle há uma janela em que o novo ainda não foi compilado, e
    nessa janela o mais recente é um órfão de um tema anterior. A 2026-09-23
    esta função acusou «o site serve CSS velho» apontando para um ficheiro de
    2025-04-02, com o roxo do Odoo — sobre um site que estava bom. Um alarme
    falso desta gravidade custa mais do que a verificação vale.
    """
    ok = True
    pagina = urllib.request.urlopen(odoo.url + "/", timeout=120).read().decode("utf-8", "replace")
    refs = re.findall(r"/web/assets/[^\"']+?/%s" % re.escape(BUNDLE), pagina)
    if not refs:
        print(f"  ! a homepage não referencia nenhum {BUNDLE}")
        return False

    servido = refs[0]
    print(f"  bundle servido: {servido}")

    with urllib.request.urlopen(odoo.url + servido, timeout=120) as r:
        css = r.read().decode("utf-8", "replace")

    # O bundle compilou de facto?
    #
    # `FACTO OBSERVADO` (2026-09-28): um erro de SCSS — `clamp(1.9rem, 1.25rem
    # + 1.9vw, …)`, unidades que o compilador não sabe somar — fez o Odoo
    # servir um ficheiro de 12 KB com a mensagem de erro em vez dos 726 KB de
    # estilos. O site ficou em Times, sem cor nem grelha.
    #
    # E esta verificação deu «tudo confere»: mediu as variáveis de cor, que
    # ainda vinham em cache do ficheiro anterior, e nunca olhou para o
    # tamanho. Media a cor de um ficheiro que já não era o servido.
    #
    # Duas perguntas que custam nada e apanham a classe inteira de falha:
    # o ficheiro tem tamanho de folha de estilos, e não tem erro lá dentro.
    if "css_error_message" in css or "A css error occured" in css:
        erro = re.search(r'content:\s*"Error:(.{0,220})', css)
        print("  ! O BUNDLE NÃO COMPILOU — o site está sem estilos.")
        if erro:
            print(f"    {erro.group(1).split(chr(92) + 'A')[0].strip()}")
        return False
    if len(css) < 100_000:
        print(f"  ! bundle com apenas {len(css) // 1024} KB — folha de estilos "
              f"completa anda pelos 700 KB. Compilação suspeita.")
        return False
    print(f"  bundle: {len(css) // 1024} KB, sem erro de compilação")

    # A data do anexo só se usa para nomear a causa quando alguma coisa falha;
    # não é ela que decide se está bom.
    anexo = odoo.search_read("ir.attachment", [["url", "=", servido]], ["create_date"])
    if anexo and modulo_escrito_em and anexo[0]["create_date"] < modulo_escrito_em:
        print(f"  ! compilado em {anexo[0]['create_date']} UTC, anterior à última "
              f"actualização do módulo ({modulo_escrito_em} UTC) — CSS velho.")
        print("    Remediação: apagar o anexo; o Odoo recompila ao primeiro pedido.")
        ok = False

    def valor(nome):
        """Devolve a cor, seja ela ``#rrggbb`` ou ``rgba(r, g, b, a)``.

        Só ler o hexadecimal deixava passar tudo o que tivesse transparência,
        em silêncio: a 2026-09-23 o texto das combinações 1 e 5 é
        ``rgba(237,231,220,.78)`` e desapareceu simplesmente do relatório. Uma
        verificação que salta o que não sabe ler é pior do que não existir,
        porque o que ela não diz lê-se como estando bem.
        """
        m = re.search(r"--%s:\s*(#[0-9A-Fa-f]{3,8}|rgba?\([^)]+\))" % re.escape(nome), css)
        return m.group(1).strip() if m else None

    def sobre(frente, fundo):
        """Achata a transparência contra o fundo — é o que o olho vê."""
        m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,/\s]+([\d.]+))?",
                     frente)
        if not m:
            return frente
        r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        alfa = float(m.group(4)) if m.group(4) else 1.0
        fundo = fundo.lstrip("#")
        fr, fg, fb = (int(fundo[i:i + 2], 16) for i in (0, 2, 4))
        return "#%02X%02X%02X" % tuple(
            round(c * alfa + f * (1 - alfa)) for c, f in ((r, fr), (g, fg), (b, fb))
        )

    for n in range(1, 6):
        fundo = valor(f"o-cc{n}-bg")
        if not fundo or not fundo.startswith("#"):
            continue
        for papel in ("headings", "text", "link"):
            bruto = valor(f"o-cc{n}-{papel}")
            if not bruto:
                print(f"  ! cc{n} {papel}: não declarado no CSS servido")
                ok = False
                continue
            frente = sobre(bruto, fundo)
            nota = f" ({bruto})" if frente != bruto else ""
            r = _contraste(frente, fundo)
            if r < AA:
                print(f"  ! cc{n} {papel}: {frente}{nota} sobre {fundo} "
                      f"= {r:.2f}:1 — chumba AA")
                ok = False
            else:
                print(f"  cc{n} {papel}: {frente}{nota} sobre {fundo} = {r:.2f}:1")
    return ok


def verificar(odoo):
    """Verifica contra o destino. Não confia no que o passo anterior disse."""
    ok = True

    mods = odoo.search_read("ir.module.module", [["name", "=", MODULO]],
                            ["state", "latest_version", "write_date"])
    if mods and mods[0]["state"] == "installed":
        print(f"  módulo instalado, versão {mods[0]['latest_version']}")
    else:
        estado = mods[0]["state"] if mods else "ausente"
        print(f"  ! módulo NÃO instalado (estado: {estado})")
        ok = False

    for url, esperado in SCSS_ALVO.items():
        recs = odoo.search_read("ir.attachment", [["url", "=", url]], ["datas"])
        lido = base64.b64decode(recs[0]["datas"]).decode("utf-8", "replace") if recs else ""
        nome = url.rsplit("/", 1)[-1]
        if lido.strip() == esperado.strip():
            print(f"  {nome} confere")
        else:
            print(f"  ! {nome} NÃO confere com o que foi escrito")
            ok = False

    # O SCSS de origem conferir não prova o CSS que o browser recebe.
    ok = verificar_bundle(odoo, mods[0]["write_date"] if mods else None) and ok

    empresa = odoo.search_read("res.company", [], ["name", "vat", "phone"])[0]
    print(f"  empresa: {empresa['name']} | {empresa['vat']} | {empresa['phone']}")
    if empresa["name"] != EMPRESA["name"]:
        ok = False

    restos = odoo.search_read("product.template", [["name", "like", "CADERI"]], ["name"])
    print(f"  typo do catálogo (língua {odoo.lingua_do_site()}):",
          "corrigido" if not restos else f"por corrigir {restos}")
    ok = ok and not restos

    es = odoo.search_read("res.lang", [["code", "=", "es_ES"], ["active", "=", True]], ["id"])
    site = odoo.search_read("website", [], ["language_ids"])[0]
    if es and es[0]["id"] in (site["language_ids"] or []):
        print("  espanhol: activo e ligado ao website")
    elif es:
        print("  ! espanhol activo mas NÃO ligado ao website")
        ok = False
    else:
        print("  ! espanhol NÃO activo")
        ok = False

    # A página tem de continuar a responder. Um erro de SCSS nas variáveis
    # primárias parte o frontend inteiro, e é isso que esta chamada apanha.
    try:
        with urllib.request.urlopen(odoo.url + "/", timeout=60) as r:
            print(f"  homepage: HTTP {r.status}")
            if r.status != 200:
                ok = False
    except Exception as e:
        print(f"  ! homepage não respondeu: {e}")
        ok = False

    return ok


# ─────────────────────────────────── main ──────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true",
                    help="escreve mesmo (por defeito só mostra)")
    ap.add_argument("--creds", default=os.path.expanduser("~/.lusosofa_odoo.json"))
    ap.add_argument("--so-verificar", action="store_true",
                    help="corre apenas o passo 7")
    ap.add_argument("--forcar-modulo", action="store_true", dest="forcar_modulo",
                    help="reimporta o módulo mesmo que a versão seja a mesma "
                         "(a versão não prova o código)")
    args = ap.parse_args()

    if not os.path.exists(args.creds):
        raise SystemExit(f"Não encontrei as credenciais em {args.creds}.")
    odoo = Odoo(json.load(open(args.creds, encoding="utf-8")))

    modo = "APLICAR" if args.aplicar else "dry-run (não escreve nada)"
    print(f"\nLusosofá — identidade do website [{modo}]")
    print(f"{odoo.url} · base {odoo.db} · uid {odoo.uid}\n")

    if args.so_verificar:
        print("7. verificação")
        sys.exit(0 if verificar(odoo) else 1)

    print("1. série do destino")
    confirmar_serie(odoo)

    print("\n2. resguardo")
    if args.aplicar:
        resguardo(odoo)
    else:
        print("  [dry-run] tiraria resguardo para .backup_lusosofa_<data>.json")

    print("\n3. módulo")
    importar_modulo(odoo, args.aplicar, forcar=args.forcar_modulo)
    if args.aplicar and not modulo_instalado(odoo):
        raise SystemExit(
            "PARADO no passo 3: o módulo não ficou instalado. Os passos "
            "seguintes escolhem a paleta 'lusosofa', que só existe depois "
            "disso — aplicá-los agora deixaria o website a apontar para uma "
            "paleta inexistente."
        )

    print("\n4. paleta e tipografia")
    aplicar_scss(odoo, args.aplicar)

    print("\n4b. bundle compilado")
    invalidar_bundle(odoo, args.aplicar)

    print("\n5. empresa, website e catálogo")
    aplicar_dados(odoo, args.aplicar)

    print("\n6. espanhol")
    activar_espanhol(odoo, args.aplicar)

    if not args.aplicar:
        print("\nNada foi escrito. Para aplicar: --aplicar\n")
        return

    print("\n7. verificação")
    ok = verificar(odoo)
    print("\n" + ("Tudo confere." if ok else
                  "ATENÇÃO: alguma coisa não confere. Vê o resguardo antes de repetir."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
