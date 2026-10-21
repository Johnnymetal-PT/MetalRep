"""Publica a política de privacidade bilingue (PT + EN) no website 3 («HMD Furniture 2026»).

Faz três coisas, só no website 3:
  1. cria a vista e a página /privacy-policy;
  2. acrescenta a ligação «Privacy Policy» ao lado de «Cookie Policy» no rodapé
     (vistas 6805 footer_cols_hmd e 6806 footer_hmd);
  3. acrescenta, antes do botão Submit dos dois formulários da página de contactos
     (vista 6810), uma frase com ligação à política.

Corre primeiro sem flags (dry-run: lê, valida e guarda cópia do original e do novo
texto em data_local/). A aplicação exige --plan, --confirm e --allow-prod. Não faz
upgrade de módulos. Texto-fonte: docs/HMD_POLITICA_PRIVACIDADE_WEBSITE3_RASCUNHO_2026-10-14.md
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

CONTEXT = {"lang": "en_US", "website_id": 3, "active_test": False}
FIELDS = ["name", "key", "website_id", "active", "arch_db", "write_date"]
NEW_KEY = "theme_hmd_furniture.privacy_policy_hmd"
NEW_URL = "/privacy-policy"
TARGETS = {
    6805: ("theme_hmd_furniture.footer_cols_hmd", 1),
    6806: ("theme_hmd_furniture.footer_hmd", 1),
    6810: ("theme_hmd_furniture.page_contact_hmd", 2),
}

COOKIE_LINK = '<a href="/cookie-policy">Cookie Policy</a>'
PRIVACY_LINK = '<a href="/privacy-policy">Privacy Policy</a>'
ACTIONS = '<div class="hmd-form__actions">'
FORM_NOTE = ('<p class="hmd-form__privacy small">By submitting this form you acknowledge that '
             'HMD Furniture will process your data to answer your request, as described in our '
             '<a href="/privacy-policy">Privacy Policy</a>.</p>\n                        ')

PT = """
                        <h2 class="pt16">Política de Privacidade</h2>
                        <p><em>Última atualização: 14 de outubro de 2026</em></p>

                        <h3>1. Quem é o responsável pelo tratamento</h3>
                        <p>HMD INTERIORS – EDIÇÃO PRODUÇÃO DE MOBILIÁRIO, LDA. («HMD Furniture»), NIF 505267748, com sede na Rua do Tronco, 375, N.º 02, Centro Empresarial Sarcol, 4465-475 São Mamede de Infesta, Portugal.<br/>
                        Contacto para questões de privacidade: <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a> · +351 229 444 180.</p>

                        <h3>2. Que dados recolhemos, para quê e com que fundamento</h3>
                        <p><strong>a) Pedido de conta de cliente profissional</strong> (formulário «Create your customer account»)</p>
                        <ul>
                            <li><em>Dados:</em> nome, email, telefone, empresa, tipo de empresa, NIF/IVA, página web, morada (rua, código postal, país) e notas que queira acrescentar.</li>
                            <li><em>Finalidade:</em> analisar o pedido, validar a empresa e abrir a sua conta de cliente.</li>
                            <li><em>Fundamento:</em> diligências pré-contratuais a seu pedido (RGPD, art. 6.º, n.º 1, alínea b).</li>
                        </ul>
                        <p><strong>b) Formulário de contacto</strong> («Can we help?»)</p>
                        <ul>
                            <li><em>Dados:</em> nome, email, telefone, empresa, assunto e a sua mensagem.</li>
                            <li><em>Finalidade:</em> responder às suas questões e pedidos de orçamento.</li>
                            <li><em>Fundamento:</em> diligências pré-contratuais a seu pedido ou, quando for apenas uma questão geral, o nosso interesse legítimo em lhe responder (art. 6.º, n.º 1, alíneas b e f).</li>
                        </ul>
                        <p><strong>c) Conta de cliente e início de sessão</strong></p>
                        <ul>
                            <li><em>Dados:</em> email de acesso, palavra-passe (guardada de forma cifrada) e os dados da sua empresa.</li>
                            <li><em>Finalidade:</em> dar-lhe acesso aos preços, ficheiros e encomendas a que tem direito.</li>
                            <li><em>Fundamento:</em> execução do contrato (art. 6.º, n.º 1, alínea b).</li>
                        </ul>
                        <p><strong>d) Encomendas e orçamentos</strong></p>
                        <ul>
                            <li><em>Dados:</em> dados de faturação e de entrega (nome, empresa, NIF, morada, contactos) e o conteúdo da encomenda.</li>
                            <li><em>Finalidade:</em> tratar, faturar e entregar a encomenda.</li>
                            <li><em>Fundamento:</em> execução do contrato e cumprimento de obrigações legais, nomeadamente fiscais (art. 6.º, n.º 1, alíneas b e c).</li>
                        </ul>
                        <p><strong>e) Newsletter</strong></p>
                        <ul>
                            <li><em>Dados:</em> endereço de email.</li>
                            <li><em>Finalidade:</em> enviar-lhe novidades da HMD.</li>
                            <li><em>Fundamento:</em> o seu consentimento (art. 6.º, n.º 1, alínea a), que pode retirar em qualquer altura.</li>
                        </ul>
                        <p><strong>f) Dados técnicos de navegação</strong></p>
                        <ul>
                            <li><em>Dados:</em> endereço IP, tipo de navegador e páginas visitadas, registados pelo servidor, e os cookies descritos na nossa <a href="/cookie-policy">Política de Cookies</a>.</li>
                            <li><em>Finalidade:</em> assegurar o funcionamento e a segurança do site.</li>
                            <li><em>Fundamento:</em> o nosso interesse legítimo em manter o site seguro e a funcionar (art. 6.º, n.º 1, alínea f).</li>
                        </ul>
                        <p>Os campos marcados com asterisco (*) nos formulários são obrigatórios; sem eles não conseguimos tratar o seu pedido.</p>

                        <h3>3. Com quem partilhamos os dados</h3>
                        <p>Não vendemos os seus dados. Podemos partilhá-los apenas com:</p>
                        <ul>
                            <li>prestadores de serviços que tratam dados em nosso nome e segundo as nossas instruções (alojamento e suporte informático, contabilidade e transporte), vinculados por contrato;</li>
                            <li>as autoridades, quando a lei o exigir.</li>
                        </ul>

                        <h3>4. Tipos de letra da Google (Google Fonts)</h3>
                        <p>Para mostrar o site com o seu desenho, as páginas carregam tipos de letra a partir dos servidores da Google (Google Fonts). Ao fazê-lo, o seu navegador comunica à Google o seu endereço IP e dados técnicos do pedido. O fundamento é o nosso interesse legítimo em apresentar o site de forma consistente. Mais informação: <a href="https://policies.google.com/privacy" rel="nofollow">policies.google.com/privacy</a>. Este é o único serviço de terceiros que o site carrega atualmente.</p>

                        <h3>5. Durante quanto tempo conservamos os dados</h3>
                        <p>Conservamos os dados apenas pelo tempo necessário para as finalidades acima e, depois, pelos prazos que a lei exija: por exemplo, os documentos de faturação, durante 10 anos. Quando deixarem de ser necessários, apagamo-los ou tornamo-los anónimos. Se retirar o consentimento para a newsletter, deixamos de lhe enviar mensagens.</p>

                        <h3>6. Os seus direitos</h3>
                        <p>Pode, a qualquer momento, pedir-nos o acesso, a retificação ou o apagamento dos seus dados, a limitação ou a oposição ao tratamento, a portabilidade e, quando o tratamento se basear no consentimento, retirá-lo, escrevendo para <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a>. Respondemos no prazo legal. Tem ainda o direito de apresentar reclamação à Comissão Nacional de Proteção de Dados (CNPD) — <a href="https://www.cnpd.pt" rel="nofollow">www.cnpd.pt</a>.</p>

                        <h3>7. Segurança</h3>
                        <p>O site usa ligação cifrada (HTTPS), as palavras-passe são guardadas de forma cifrada e o acesso aos dados está limitado a quem precisa deles para o trabalho.</p>

                        <h3>8. Menores</h3>
                        <p>O site destina-se a profissionais e não é dirigido a menores. Não recolhemos intencionalmente dados de menores.</p>

                        <h3>9. Cookies</h3>
                        <p>Informação sobre os cookies que o site utiliza, e como gerir a sua escolha, na <a href="/cookie-policy">Política de Cookies</a>.</p>

                        <h3>10. Alterações</h3>
                        <p>Podemos atualizar esta política. A data da última atualização está no topo desta secção.</p>
"""

EN = """
                        <h2 class="pt16">Privacy Policy</h2>
                        <p><em>Last updated: 14 October 2026</em></p>

                        <h3>1. Who is the data controller</h3>
                        <p>HMD INTERIORS – EDIÇÃO PRODUÇÃO DE MOBILIÁRIO, LDA. ("HMD Furniture"), VAT/NIF 505267748, registered office at Rua do Tronco, 375, N.º 02, Centro Empresarial Sarcol, 4465-475 São Mamede de Infesta, Portugal.<br/>
                        Privacy contact: <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a> · +351 229 444 180.</p>

                        <h3>2. What data we collect, why, and on what legal basis</h3>
                        <p><strong>a) Request for a professional customer account</strong> ("Create your customer account" form)</p>
                        <ul>
                            <li><em>Data:</em> name, email, phone, company, company type, VAT number, website, address (street, postal code, country) and any notes you add.</li>
                            <li><em>Purpose:</em> to review your request, verify the company and open your customer account.</li>
                            <li><em>Legal basis:</em> steps taken at your request before entering into a contract (GDPR, Art. 6(1)(b)).</li>
                        </ul>
                        <p><strong>b) Contact form</strong> ("Can we help?")</p>
                        <ul>
                            <li><em>Data:</em> name, email, phone, company, subject and your message.</li>
                            <li><em>Purpose:</em> to answer your questions and quotation requests.</li>
                            <li><em>Legal basis:</em> steps taken at your request before entering into a contract or, for a general enquiry, our legitimate interest in replying (Art. 6(1)(b) and (f)).</li>
                        </ul>
                        <p><strong>c) Customer account and login</strong></p>
                        <ul>
                            <li><em>Data:</em> login email, password (stored in encrypted form) and your company details.</li>
                            <li><em>Purpose:</em> to give you access to the prices, files and orders you are entitled to.</li>
                            <li><em>Legal basis:</em> performance of a contract (Art. 6(1)(b)).</li>
                        </ul>
                        <p><strong>d) Orders and quotations</strong></p>
                        <ul>
                            <li><em>Data:</em> billing and delivery details (name, company, VAT number, address, contacts) and the content of the order.</li>
                            <li><em>Purpose:</em> to process, invoice and deliver the order.</li>
                            <li><em>Legal basis:</em> performance of a contract and compliance with legal obligations, in particular tax law (Art. 6(1)(b) and (c)).</li>
                        </ul>
                        <p><strong>e) Newsletter</strong></p>
                        <ul>
                            <li><em>Data:</em> email address.</li>
                            <li><em>Purpose:</em> to send you HMD news.</li>
                            <li><em>Legal basis:</em> your consent (Art. 6(1)(a)), which you can withdraw at any time.</li>
                        </ul>
                        <p><strong>f) Technical browsing data</strong></p>
                        <ul>
                            <li><em>Data:</em> IP address, browser type and pages visited, logged by the server, and the cookies described in our <a href="/cookie-policy">Cookie Policy</a>.</li>
                            <li><em>Purpose:</em> to keep the site working and secure.</li>
                            <li><em>Legal basis:</em> our legitimate interest in keeping the site secure and running (Art. 6(1)(f)).</li>
                        </ul>
                        <p>Fields marked with an asterisk (*) in the forms are mandatory; without them we cannot handle your request.</p>

                        <h3>3. Who we share data with</h3>
                        <p>We do not sell your data. We may share it only with:</p>
                        <ul>
                            <li>service providers who process data on our behalf and under our instructions (hosting and IT support, accounting and transport), bound by contract;</li>
                            <li>public authorities, where the law requires it.</li>
                        </ul>

                        <h3>4. Google typefaces (Google Fonts)</h3>
                        <p>To display the site as designed, the pages load typefaces from Google's servers (Google Fonts). In doing so, your browser sends Google your IP address and technical details of the request. Our legal basis is our legitimate interest in presenting the site consistently. More information: <a href="https://policies.google.com/privacy" rel="nofollow">policies.google.com/privacy</a>. This is the only third-party service the site currently loads.</p>

                        <h3>5. How long we keep data</h3>
                        <p>We keep data only for as long as needed for the purposes above and, afterwards, for the periods the law requires: for example, invoicing documents for 10 years. When it is no longer needed we delete or anonymise it. If you withdraw your consent to the newsletter, we stop sending you messages.</p>

                        <h3>6. Your rights</h3>
                        <p>You may at any time ask us for access to, rectification or erasure of your data, restriction of or objection to processing, portability and, where processing is based on consent, to withdraw it, by writing to <a href="mailto:info@hmdfurniture.com">info@hmdfurniture.com</a>. We reply within the legal deadline. You also have the right to lodge a complaint with the Portuguese data protection authority, the CNPD — <a href="https://www.cnpd.pt" rel="nofollow">www.cnpd.pt</a>.</p>

                        <h3>7. Security</h3>
                        <p>The site uses an encrypted connection (HTTPS), passwords are stored in encrypted form, and access to data is limited to those who need it for their work.</p>

                        <h3>8. Minors</h3>
                        <p>The site is intended for professionals and is not directed at minors. We do not knowingly collect data from minors.</p>

                        <h3>9. Cookies</h3>
                        <p>Information about the cookies the site uses, and how to manage your choice, is in the <a href="/cookie-policy">Cookie Policy</a>.</p>

                        <h3>10. Changes</h3>
                        <p>We may update this policy. The date of the last update is at the top of this section.</p>
"""

NEW_ARCH = (
    '<t name="Privacy Policy" t-name="' + NEW_KEY + '">\n'
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


def patch(view_id, old):
    """Insere as ligações; uma segunda passagem é neutra."""
    if view_id in (6805, 6806):
        if PRIVACY_LINK in old:
            return old
        if old.count(COOKIE_LINK) != 1:
            raise ValueError(f"Âncora do rodapé inesperada na vista {view_id}")
        return old.replace(COOKIE_LINK, COOKIE_LINK + "\n                        " + PRIVACY_LINK)
    if view_id == 6810:
        if "hmd-form__privacy" in old:
            return old
        if old.count(ACTIONS) != 2:
            raise ValueError("A vista 6810 não tem os dois botões de envio esperados")
        return old.replace(ACTIONS, FORM_NOTE + ACTIONS)
    raise ValueError(view_id)


def read_views(guard):
    rows = guard.kw("ir.ui.view", "read", [list(TARGETS)], {"fields": FIELDS, "context": CONTEXT})
    if len(rows) != len(TARGETS):
        raise ValueError("Não foram encontradas as três vistas")
    for row in rows:
        if row["key"] != TARGETS[row["id"]][0] or row["website_id"][0] != 3 or not row["active"]:
            raise ValueError(f"Destino inesperado: {row['id']}")
    return {row["id"]: row for row in rows}


def assert_free(guard):
    views = guard.kw("ir.ui.view", "search", [[["key", "=", NEW_KEY], ["website_id", "=", 3]]],
                     {"context": CONTEXT})
    pages = guard.kw("website.page", "search", [[["url", "=", NEW_URL], ["website_id", "=", 3]]],
                     {"context": CONTEXT})
    if views or pages:
        raise ValueError(f"Já existem vista {views} ou página {pages} para {NEW_URL} no website 3")


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
    ET.fromstring(NEW_ARCH)
    rows = read_views(guard)
    assert_free(guard)
    if not args.confirm:
        folder = ROOT / "data_local" / ("w3_privacy_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        folder.mkdir(parents=True)
        (folder / "new_page_arch.xml").write_text(NEW_ARCH, encoding="utf-8")
        plan = {"website_id": 3, "database": guard.alvo.database, "base_url": guard.alvo.base_url,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "authorization": "Utilizador autorizou publicar a política de privacidade e as ligações no website 3, 14/10/2026.",
                "new_view_key": NEW_KEY, "new_url": NEW_URL, "views": []}
        for view_id in TARGETS:
            row = rows[view_id]
            old = row["arch_db"]
            new = patch(view_id, old)
            ET.fromstring(new)
            if patch(view_id, new) != new:
                raise ValueError(f"Patch não é idempotente: {view_id}")
            if len(new) < len(old):
                raise ValueError(f"Redução inesperada: {view_id}")
            (folder / f"view_{view_id}_before.xml").write_text(old, encoding="utf-8")
            (folder / f"view_{view_id}_after.xml").write_text(new, encoding="utf-8")
            (folder / f"view_{view_id}.diff").write_text("".join(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True), f"{view_id}_before", f"{view_id}_after")), encoding="utf-8")
            plan["views"].append(dict(row, expected=new, before_sha256=digest(old), after_sha256=digest(new)))
            print(f"{view_id} {row['key']}: {len(old)} -> {len(new)}; idempotência OK")
        print(f"nova página {NEW_URL}: arch com {len(NEW_ARCH)} caracteres; XML válido")
        (folder / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PLAN={folder / 'plan.json'}")
        return
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan["database"] != guard.alvo.database or plan["base_url"] != guard.alvo.base_url:
        raise ValueError("Ligação diferente da utilizada no dry-run")
    if [v["id"] for v in plan["views"]] != list(TARGETS):
        raise ValueError("Plano não cobre exatamente as três vistas autorizadas")
    for entry in plan["views"]:
        row = rows[entry["id"]]
        if row["arch_db"] != entry["arch_db"] or row["write_date"] != entry["write_date"]:
            raise ValueError(f"Vista {row['id']} alterada desde o dry-run; não escrever")
        if patch(row["id"], row["arch_db"]) != entry["expected"]:
            raise ValueError("Plano diferente do patch revisto")
    results = {"views": []}
    # 1) a página primeiro, para as ligações nunca apontarem para um 404
    view_id_new = guard.kw("ir.ui.view", "create", [{
        "name": "Privacy Policy", "type": "qweb", "key": NEW_KEY, "website_id": 3, "arch": NEW_ARCH}],
        {"context": CONTEXT}, allow_write=True)
    page_id = guard.kw("website.page", "create", [{
        "url": NEW_URL, "view_id": view_id_new, "website_id": 3,
        "is_published": True, "website_indexed": False}], {"context": CONTEXT}, allow_write=True)
    created = guard.kw("ir.ui.view", "read", [[view_id_new]], {"fields": FIELDS, "context": CONTEXT})[0]
    if created["arch_db"] != NEW_ARCH or created["website_id"][0] != 3:
        raise ValueError("Divergência na vista criada")
    page = guard.kw("website.page", "read", [[page_id]], {"fields": ["url", "view_id", "website_id", "is_published"]})[0]
    if page["url"] != NEW_URL or page["website_id"][0] != 3 or not page["is_published"]:
        raise ValueError("Divergência na página criada")
    results.update({"view_id": view_id_new, "page_id": page_id})
    print(f"página criada: vista {view_id_new}, página {page_id}, {NEW_URL}")
    # 2) depois as ligações
    for entry in plan["views"]:
        view_id = entry["id"]
        current = read_views(guard)[view_id]
        if current["arch_db"] != entry["arch_db"] or current["write_date"] != entry["write_date"]:
            raise ValueError(f"Edição concorrente da vista {view_id}; interromper")
        outcome = guard.kw("ir.ui.view", "write", [[view_id], {"arch_db": entry["expected"]}],
                           {"context": CONTEXT}, allow_write=True)
        if outcome is not True:
            raise ValueError(f"Retorno inesperado ao escrever {view_id}")
        actual = read_views(guard)[view_id]
        if actual["arch_db"] != entry["expected"]:
            raise ValueError(f"Divergência após escrita: {view_id}")
        results["views"].append({"id": view_id, "key": entry["key"], "sha256": digest(actual["arch_db"]), "verified": True})
        (args.plan.parent / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{view_id} {entry['key']}: aplicado, leitura idêntica ao plano")
    print(f"RECONCILIAÇÃO: 1 página + {len(results['views'])} vistas verificadas; 0 divergências")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
