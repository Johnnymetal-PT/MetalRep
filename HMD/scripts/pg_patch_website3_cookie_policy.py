"""Publica a política de cookies bilingue (PT + EN) no website 3 («HMD Furniture 2026»).

Corre primeiro sem flags (dry-run: lê, valida e guarda cópia do original e do novo
texto em data_local/). A aplicação exige --plan, --confirm e --allow-prod.
Escreve só o arch_db da vista da página /cookie-policy do website 3 (vista 6838,
criada pelo Odoo ao ligar a barra de cookies). Não faz upgrade de módulos.
Texto-fonte: docs/HMD_POLITICA_COOKIES_WEBSITE3_RASCUNHO_2026-10-14.md
"""

import argparse
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".pg_framework/scripts"))
from pg_odoo_migration_guard import Guard, resolver_alvo_por_projeto

VIEW_ID = 6838
VIEW_KEY = "website.cookie_policy"
PAGE_ID = 110
CONTEXT = {"lang": "en_US", "website_id": 3, "active_test": False}
FIELDS = ["name", "key", "website_id", "active", "arch_db", "write_date"]

PT = """
                        <h2 class="pt16">Política de Cookies</h2>
                        <p><em>Última atualização: 14 de outubro de 2026</em></p>

                        <h3>1. Quem é o responsável</h3>
                        <p>HMD INTERIORS – EDIÇÃO PRODUÇÃO DE MOBILIÁRIO, LDA. («HMD Furniture»), NIF 505267748, com sede na Rua do Tronco, 375, N.º 02, Centro Empresarial Sarcol, 4465-475 São Mamede de Infesta, Portugal.<br/>
                        Contacto: <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a> · +351 229 444 180.</p>

                        <h3>2. O que são cookies</h3>
                        <p>Cookies são pequenos ficheiros de texto que um site grava no seu computador, telemóvel ou tablet quando o visita. Servem para que o site funcione e se lembre de algumas das suas escolhas.</p>

                        <h3>3. Que cookies utilizamos</h3>
                        <p>Todos os cookies abaixo são <strong>essenciais</strong>.</p>
                        <ul>
                            <li><code>session_id</code> — mantém a sua sessão (por exemplo, o conteúdo do carrinho e o início de sessão) e protege a sua navegação. <em>Duração: 7 dias.</em></li>
                            <li><code>frontend_lang</code> — guarda o idioma do site. <em>Duração: 1 ano.</em></li>
                            <li><code>tz</code> — guarda o fuso horário do seu navegador, para mostrar datas e horas corretas. <em>Duração: até fechar o navegador.</em></li>
                            <li><code>website_cookies_bar</code> — guarda a escolha que fez no aviso de cookies, para não lhe voltar a perguntar. <em>Duração: cerca de 13 meses.</em></li>
                        </ul>
                        <p>Atualmente este site <strong>não utiliza cookies opcionais</strong>, ou seja, de análise de visitas, publicidade ou redes sociais. Se isso vier a mudar, esses cookies só serão ativados depois do seu consentimento e esta política será atualizada.</p>

                        <h3>4. Consentimento</h3>
                        <p>Os cookies essenciais são necessários para o site funcionar e para lhe prestarmos o serviço que pede, por isso não dependem de consentimento. Os restantes, se existirem, só são usados com o seu consentimento.</p>

                        <h3>5. Como alterar a sua escolha ou gerir cookies</h3>
                        <ul>
                            <li>Nesta página, use o botão <strong>«Show the cookies bar»</strong> para voltar a ver o aviso e mudar a sua escolha.</li>
                            <li>Pode também apagar ou bloquear cookies nas definições do seu navegador (Chrome, Firefox, Safari, Edge…). Atenção: se bloquear os cookies essenciais, partes do site, como o início de sessão e o carrinho, podem deixar de funcionar.</li>
                            <li>Este site não responde a sinais «Do Not Track», porque não existe uma norma do setor para isso.</li>
                        </ul>

                        <h3>6. Os seus direitos</h3>
                        <p>Nos termos do Regulamento Geral sobre a Proteção de Dados (RGPD), pode pedir o acesso, a retificação ou o apagamento dos seus dados, a limitação ou oposição ao tratamento e a portabilidade, através de <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a>. Pode ainda apresentar reclamação à Comissão Nacional de Proteção de Dados (CNPD) — <a href="https://www.cnpd.pt" rel="nofollow">www.cnpd.pt</a>.</p>

                        <h3>7. Alterações</h3>
                        <p>Podemos atualizar esta política. A data da última atualização está no topo desta secção.</p>
"""

EN = """
                        <h2 class="pt16">Cookie Policy</h2>
                        <p><em>Last updated: 14 October 2026</em></p>

                        <h3>1. Who is responsible</h3>
                        <p>HMD INTERIORS – EDIÇÃO PRODUÇÃO DE MOBILIÁRIO, LDA. ("HMD Furniture"), VAT/NIF 505267748, registered office at Rua do Tronco, 375, N.º 02, Centro Empresarial Sarcol, 4465-475 São Mamede de Infesta, Portugal.<br/>
                        Contact: <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a> · +351 229 444 180.</p>

                        <h3>2. What cookies are</h3>
                        <p>Cookies are small text files that a website stores on your computer, phone or tablet when you visit. They let the site work and remember some of your choices.</p>

                        <h3>3. Which cookies we use</h3>
                        <p>All the cookies below are <strong>essential</strong>.</p>
                        <ul>
                            <li><code>session_id</code> — keeps your session (for example the contents of your cart and your login) and protects your browsing. <em>Duration: 7 days.</em></li>
                            <li><code>frontend_lang</code> — remembers the language of the site. <em>Duration: 1 year.</em></li>
                            <li><code>tz</code> — stores your browser's time zone so dates and times are shown correctly. <em>Duration: until you close the browser.</em></li>
                            <li><code>website_cookies_bar</code> — remembers the choice you made in the cookie notice, so we do not ask again. <em>Duration: about 13 months.</em></li>
                        </ul>
                        <p>This website <strong>currently uses no optional cookies</strong>, meaning no analytics, advertising or social-media cookies. If that changes, those cookies will only be enabled after you consent, and this policy will be updated.</p>

                        <h3>4. Consent</h3>
                        <p>Essential cookies are necessary for the site to work and to provide the service you request, so they do not require consent. Any other cookies, if they exist, are only used with your consent.</p>

                        <h3>5. How to change your choice or manage cookies</h3>
                        <ul>
                            <li>On this page, use the <strong>"Show the cookies bar"</strong> button to see the notice again and change your choice.</li>
                            <li>You can also delete or block cookies in your browser settings (Chrome, Firefox, Safari, Edge…). Note that blocking essential cookies may stop parts of the site, such as login and the cart, from working.</li>
                            <li>This site does not respond to "Do Not Track" signals, because there is no industry standard for them.</li>
                        </ul>

                        <h3>6. Your rights</h3>
                        <p>Under the General Data Protection Regulation (GDPR) you may request access to, rectification or erasure of your data, restriction of or objection to processing, and portability, by writing to <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a>. You may also lodge a complaint with the Portuguese data protection authority, the CNPD — <a href="https://www.cnpd.pt" rel="nofollow">www.cnpd.pt</a>.</p>

                        <h3>7. Changes</h3>
                        <p>We may update this policy. The date of the last update is at the top of this section.</p>
"""

NEW_ARCH = (
    '<t name="Cookie Policy" t-name="website.cookie_policy">\n'
    '        <t t-call="website.layout">\n'
    '            <div id="wrap" class="oe_structure">\n'
    '                <section class="pt8 pb8">\n'
    '                    <div class="container">\n'
    + PT +
    '                        <hr class="my-5"/>\n'
    + EN +
    '                    </div>\n'
    '                </section>\n'
    '            </div>\n'
    '        </t>\n'
    '    </t>'
)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_view(guard):
    rows = guard.kw("ir.ui.view", "read", [[VIEW_ID]], {"fields": FIELDS, "context": CONTEXT})
    row = rows[0]
    if row["key"] != VIEW_KEY or row["website_id"][0] != 3 or not row["active"]:
        raise ValueError(f"Destino inesperado: {row['key']} website {row['website_id']}")
    page = guard.kw("website.page", "read", [[PAGE_ID]], {"fields": ["url", "view_id", "website_id"]})[0]
    if page["url"] != "/cookie-policy" or page["view_id"][0] != VIEW_ID or page["website_id"][0] != 3:
        raise ValueError("A página 110 já não aponta para a vista 6838 do website 3")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--allow-prod", action="store_true")
    args = parser.parse_args()
    if args.confirm and (not args.plan or not args.allow_prod):
        parser.error("Aplicar exige --plan e --allow-prod")
    guard = Guard(resolver_alvo_por_projeto("odoo-hmd", "production"),
                  confirmed=args.confirm, allow_prod=args.allow_prod,
                  log_path=str(ROOT / ".pg/migration/api_calls.log.jsonl"))
    base = guard.kw("ir.module.module", "search_read", [[["name", "=", "base"]]],
                    {"fields": ["installed_version"]})
    if not base[0]["installed_version"].startswith("18.0."):
        raise ValueError("A série do destino não é Odoo 18")
    row = read_view(guard)
    ET.fromstring(NEW_ARCH)
    if not args.confirm:
        folder = ROOT / "data_local" / ("w3_cookies_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        folder.mkdir(parents=True)
        old = row["arch_db"]
        (folder / "view_before.xml").write_text(old, encoding="utf-8")
        (folder / "view_after.xml").write_text(NEW_ARCH, encoding="utf-8")
        (folder / "view.diff").write_text("".join(difflib.unified_diff(
            old.splitlines(True), NEW_ARCH.splitlines(True), "before", "after")), encoding="utf-8")
        plan = {"website_id": 3, "database": guard.alvo.database, "base_url": guard.alvo.base_url,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "authorization": "Utilizador autorizou publicar a política de cookies bilingue no website 3, 14/10/2026.",
                "view": dict(row, expected=NEW_ARCH, before_sha256=digest(old), after_sha256=digest(NEW_ARCH))}
        (folder / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"vista {VIEW_ID} {row['key']}: {len(old)} -> {len(NEW_ARCH)} caracteres; XML válido")
        print(f"PLAN={folder / 'plan.json'}")
        return
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan["database"] != guard.alvo.database or plan["base_url"] != guard.alvo.base_url:
        raise ValueError("Ligação diferente da utilizada no dry-run")
    entry = plan["view"]
    if entry["expected"] != NEW_ARCH:
        raise ValueError("Plano diferente do texto revisto")
    if row["arch_db"] != entry["arch_db"] or row["write_date"] != entry["write_date"]:
        raise ValueError("Vista alterada desde o dry-run; não escrever")
    outcome = guard.kw("ir.ui.view", "write", [[VIEW_ID], {"arch_db": NEW_ARCH}],
                       {"context": CONTEXT}, allow_write=True)
    if outcome is not True:
        raise ValueError("Retorno inesperado ao escrever")
    actual = read_view(guard)
    if actual["arch_db"] != NEW_ARCH:
        raise ValueError("Divergência após escrita")
    (args.plan.parent / "result.json").write_text(json.dumps(
        {"id": VIEW_ID, "sha256": digest(actual["arch_db"]), "verified": True}, indent=2), encoding="utf-8")
    print(f"{VIEW_ID}: aplicado, leitura idêntica ao plano (sha256 {digest(actual['arch_db'])[:16]}…)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
