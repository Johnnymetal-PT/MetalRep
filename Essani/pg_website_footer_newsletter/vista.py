# -*- coding: utf-8 -*-
"""O HTML do rodapé e da newsletter, e as suas traduções. Sem dependências do Odoo.

Antes, o rodapé e a newsletter eram criados pelos scripts `pgV4Footer` e `pgNewsletter` do código
personalizado do website, com texto em português fixo e links sem prefixo de língua. O editor de
traduções do Odoo só vê o que está em vistas, por isso nunca foram traduzidos.

A base da vista é inglês (como a homepage); o português e o espanhol aplicam-se a seguir, por
`update_field_translations`. Os scripts antigos terminam logo se `.pg-foot` / `.pg-nl` já
existirem, por isso ficam inertes sem serem apagados.
"""
import html
import re

# Insere antes do rodapé standard do Odoo, tal como o JavaScript fazia (newsletter, rodapé, standard).
ARCH = """<data>
  <xpath expr="//footer[@id='bottom']" position="before">
    <section class="pg-nl">
      <div class="in">
        <div class="eb">Newsletter</div>
        <h3>Stay up to date</h3>
        <p>Subscribe and be the first to receive our campaigns and launches.</p>
        <div class="fw"><iframe width="540" height="240" src="https://1b9e4a59.sibforms.com/v2/serve/MUIFAF0iKLpqWJfQ0OsuG3xQDrPpBKc069PAu5vLBsQzg4YiwKoMiTYpVgoat3MG9FEVcarYbNWBQDF6MNBo5lfPOd_0HAivjjwRgux9zgkIDipvUY3d6Ni2Lmw8gHq9k-TP-RcV8IqMelYw7f9yNjocLs4pusn5zJXyw9b2dxd4vRqGprx4sKKzEn3dl4U9r4eX9FfPiraP-y74" frameborder="0" scrolling="no" allowfullscreen="allowfullscreen" style="display:block;margin:auto;max-width:100%;border:0"></iframe></div>
      </div>
    </section>
    <footer class="pg-foot">
      <div class="in">
        <div>
          <a class="brand" href="/" aria-label="Essani"><img src="/web/image/website/5/logo" alt="Essani" loading="lazy"/></a>
          <p class="tag">LED lighting and technology for professionals — from the linear profile to the invisible sensor, ready to integrate.</p>
          <div class="soc">
            <a href="https://www.instagram.com/essani.iluminacaoetecnologia" target="_blank" rel="noopener" aria-label="Instagram"><i class="fa fa-instagram"></i></a>
            <a href="https://www.facebook.com/essani.pt" target="_blank" rel="noopener" aria-label="Facebook"><i class="fa fa-facebook"></i></a>
            <a href="https://www.linkedin.com/company/essani" target="_blank" rel="noopener" aria-label="LinkedIn"><i class="fa fa-linkedin"></i></a>
          </div>
        </div>
        <div>
          <h4>Explore</h4>
          <ul>
            <li><a href="/solucoes">Solutions</a></li>
            <li><a href="/servicos">Services</a></li>
            <li><a href="/shop/category/destaques-1817">Highlights</a></li>
          </ul>
        </div>
        <div>
          <h4>Company</h4>
          <ul>
            <li><a href="/essani">About Essani</a></li>
            <li><a href="/campanhas">Inspiration</a></li>
            <li><a href="/carreiras">Careers</a></li>
            <li><a href="/contactus">Contact</a></li>
          </ul>
        </div>
        <div>
          <h4>Contact</h4>
          <div class="ct">
            <div class="addr">Rua do Multipark I, nº 133<br/>4595-542 Seroa, Paços de Ferreira</div>
            <a href="tel:+351255105909">(+351) 255 105 909</a>
            <a href="mailto:geral@essani.pt">geral@essani.pt</a>
          </div>
        </div>
      </div>
    </footer>
  </xpath>
</data>"""

# texto em inglês (a fonte) -> (português, espanhol). O espanhol segue o vocabulário do menu do V4/V5.
TRADUCOES = {
    "Stay up to date": ("Fique a par das novidades", "Manténgase al día"),
    "Subscribe and be the first to receive our campaigns and launches.": (
        "Subscreva e receba em primeira mão as nossas campanhas e lançamentos.",
        "Suscríbase y reciba antes que nadie nuestras campañas y novedades."),
    "LED lighting and technology for professionals — from the linear profile to the invisible sensor, ready to integrate.": (
        "Iluminação e tecnologia LED para profissionais — do perfil linear ao sensor invisível, prontos a integrar.",
        "Iluminación y tecnología LED para profesionales: del perfil lineal al sensor invisible, listos para integrar."),
    "Explore": ("Explorar", "Explorar"),
    "Solutions": ("Soluções", "Soluciones"),
    "Services": ("Serviços", "Servicios"),
    "Highlights": ("Destaques", "Destacados"),
    "Company": ("Empresa", "Empresa"),
    "About Essani": ("Sobre a Essani", "Sobre Essani"),
    "Inspiration": ("Inspiração", "Inspiración"),
    "Careers": ("Carreiras", "Empleo"),
    "Contact": ("Contactos", "Contacto"),
}
LINGUAS = ("pt_PT", "es_ES")


def texto(termo):
    """O texto visível de um termo (sem tags, entidades resolvidas, espaços normalizados)."""
    sem_tags = re.sub(r"<[^>]+>", " ", html.unescape(termo or ""))
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def pedido(linhas):
    """Das linhas de `get_field_translations` ({lang, source, value}) devolve
    {lang: {termo-fonte: tradução}} só para os termos que temos traduzidos."""
    fontes = {}
    for linha in linhas:
        fontes.setdefault(linha["source"], None)
    saida = {lg: {} for lg in LINGUAS}
    for fonte in fontes:
        par = TRADUCOES.get(texto(fonte))
        if not par:
            continue
        for lg, valor in zip(LINGUAS, par):
            saida[lg][fonte] = valor
    return saida
