import pathlib, html
# CSS compilado do tema (ver README.md) e raiz do repositorio
S = pathlib.Path('/tmp')
REPO = pathlib.Path(__file__).resolve().parents[2]
css = (S / 'theme_all.css').read_text(encoding='utf-8')
IMG = '../../theme_hmd_furniture/static/src/img'

MEGA = [
    ('MESAS', ['MESAS DE JANTAR', 'MESAS EXTENSÍVEIS', 'MESAS BAR', 'MESAS AUXILIARES',
               'MESAS DE CENTRO', 'MESAS BISTRO', 'SECRETÁRIAS', 'MESAS DE CABECEIRA']),
    ('ESTOFO', ['CADEIRAS', 'CADEIRÕES', 'POUFS', 'BANCOS', 'SOFÁS', 'SOFÁS MODULARES']),
    ('ARRUMAÇÃO', ['APARADORES', 'CONSOLAS', 'ARMÁRIOS', 'PRATELEIRAS']),
    ('CAMAS', []),
    ('ILUMINAÇÃO', []),
]
NAV = ['HOME', 'COLLECTION', 'PORTFOLIO', 'FABRICS', 'MATERIALS', 'CONTACT US', 'WE ARE']

def header(active='HOME'):
    cols = ''.join(
        f'<div class="hmd-megamenu__col"><a href="#">{h}</a>'
        + ''.join(f'<a href="#">{c}</a>' for c in kids) + '</div>'
        for h, kids in MEGA)
    nav = ''.join(
        f'<span class="hmd-nav__item hmd-nav__trigger{" hmd-nav__item--active" if n==active else ""}">'
        f'<a href="#">{n}</a></span>' for n in NAV)
    return f'''
<div class="hmd-topbar"><a href="#">Private</a><a href="#">Professional</a>
<a class="hmd-topbar__login" href="#">Login</a></div>
<header class="hmd-header">
  <div class="hmd-header__bar">
    <nav class="hmd-nav">{nav}</nav>
    <div class="hmd-header__aside">
      <div class="hmd-header__tools" style="font-family:var(--hmd-ui);font-size:14px">
        <span>&#128722; 7</span><span>&#9829; 3</span><span>Mónica Hedderich &#9662;</span>
      </div>
      <a class="hmd-brand" href="#">hmd furniture</a>
      <div class="hmd-rail">
        <a href="#">Products</a><a href="#">Materials</a><a href="#">Fabrics</a>
        <div class="hmd-rail__lang"><a class="active" href="#">EN</a><a href="#">PT</a></div>
      </div>
    </div>
  </div>
  <div class="hmd-megamenu is-open"><div class="hmd-megamenu__grid">{cols}</div></div>
</header>'''

FOOTER = f'''
<div class="hmd-footer">
  <p class="hmd-footer__intro">HMD designs and produces in Portugal. It's been over 30 years.
  We work closely with artisans — selected for their precision, their patience, and their hands.
  Quietly, our pieces have found their way into private homes and hotels in more than 80 countries.</p>
  <div class="hmd-footer__grid">
    <div class="hmd-footer__col"><span>HMD Furniture©2026</span><a href="#">Cookie Policy</a></div>
    <div class="hmd-footer__col"><a href="#">(+351) 229444180</a>
      <a href="#">costumer@hmdfurniture.com</a><span>Salcol — Rua do Tronco, 375 N0.002</span>
      <span>4465-275</span></div>
    <div class="hmd-footer__col"><a href="#">Instagram</a><a href="#">Facebook</a>
      <a href="#">Pinterest</a><a href="#">LinkedIn</a></div>
    <div class="hmd-footer__col"><span>Newsletter</span>
      <form class="hmd-newsletter"><input type="email" placeholder="Email"/><button type="button">Send</button></form>
    </div>
  </div>
</div>'''

HOME = f'''
<section class="hmd-hero" style="background-image:url('{IMG}/home_hero.jpg')">
  <h1 class="hmd-hero__kicker">Send us your ideas</h1>
  <div class="hmd-hero__foot">
    <h2 class="hmd-hero__title">Contract us</h2>
    <p class="hmd-hero__lead">For interior design visionaries, we present the Congo Table:
    a seemingly simple piece that unveils itself as a masterpiece for those with refined sensibilities.</p>
  </div>
</section>
<section class="hmd-editorial">
  <div>
    <figure class="hmd-figure"><img src="{IMG}/editorial_interior.jpg" alt=""/>
      <figcaption class="hmd-caption">Legendas imagens</figcaption></figure>
    <h2 class="hmd-editorial__title">News from Portugal</h2>
    <p class="hmd-editorial__body">We are grateful to the architects, designers and clients who
    generously allow us to share their work. Every space reflects a unique vision, and we are proud
    to have contributed with pieces that become part of those stories.</p>
  </div>
  <div>
    <p class="hmd-standfirst">We are grateful to the architects, designers and clients who
    generously allow us to share their work.</p>
    <p class="hmd-editorial__body">Every space reflects a unique vision, and we are proud to have
    contributed with pieces that become part of those stories.</p>
    <figure class="hmd-figure" style="margin-top:1.5rem"><img src="{IMG}/editorial_sketch.jpg" alt=""/>
      <figcaption class="hmd-caption">Legendas imagens</figcaption></figure>
  </div>
</section>
<section class="hmd-feature">
  <h2 class="hmd-feature__title">Congo</h2>
  <p class="hmd-feature__sub">Coffee Tables</p>
  <figure class="hmd-feature__media"><img src="{IMG}/congo_detail.jpg" alt=""/>
    <figcaption class="hmd-caption" style="text-align:left">Legendas imagens</figcaption></figure>
  <p class="hmd-feature__body">We are grateful to the architects, designers and clients who
  generously allow us to share their work. Every space reflects a unique vision, and we are proud
  to have contributed with pieces that become part of those stories.</p>
</section>
<section class="hmd-projects">
  <article class="hmd-project"><img src="{IMG}/editorial_interior.jpg" alt=""/>
    <p class="hmd-project__caption">Project by <strong>L'Elephant</strong></p>
    <p class="hmd-project__body">We are grateful to the architects, designers and clients who
    generously allow us to share their work.</p></article>
  <article class="hmd-project"><img src="{IMG}/editorial_interior.jpg" alt=""/>
    <p class="hmd-project__caption">Project by <strong>L'Elephant</strong></p>
    <p class="hmd-project__body">Every space reflects a unique vision, and we are proud to have
    contributed with pieces that become part of those stories.</p></article>
</section>'''

def variant(label):
    return f'''<div class="hmd-variant"><span class="hmd-variant__label">Select finish</span>
    <div class="hmd-variant__row"><span class="hmd-variant__swatch" style="background:{label}"></span>
    <select><option>CEMENT &amp; TOSCANA</option></select></div></div>'''

PRODUCT = f'''
<section class="hmd-product-hero">
  <h1 class="hmd-product-hero__name">Congo</h1>
  <p class="hmd-product-hero__cat">Coffee Tables</p>
  <figure class="hmd-product-hero__media"><img src="{IMG}/congo_detail.jpg" alt=""/>
    <figcaption class="hmd-caption" style="text-align:left">Legendas imagens</figcaption></figure>
  <p class="hmd-product-hero__lead">For Interior Design Visionaries, We Present The Congo Table:
  A Seemingly Simple Piece That Unveils Itself As A Masterpiece For Those With Refined Sensibilities.</p>
</section>
<section class="hmd-lifestyle">
  <div class="hmd-lifestyle__frame"><img src="{IMG}/congo_lifestyle.jpg" alt=""/></div>
  <div class="hmd-lifestyle__dots">
    <button class="hmd-lifestyle__dot is-active">1</button><button class="hmd-lifestyle__dot">2</button>
    <button class="hmd-lifestyle__dot">3</button><button class="hmd-lifestyle__dot">4</button>
    <button class="hmd-lifestyle__dot">5</button></div>
</section>
<section class="hmd-seen">
  <h2 class="hmd-seen__title">Seen in projects</h2>
  <p class="hmd-editorial__body">We are grateful to the architects, designers and clients who
  generously allow us to share their work. Every space reflects a unique vision, and we are proud
  to have contributed with pieces that become part of those stories.</p>
  <div class="hmd-projects hmd-projects--3" style="padding-left:0;padding-right:0">
    {''.join(f"""<article class="hmd-project">
      <p class="hmd-project__caption">Hotel Amano Group — Germany</p>
      <img src="{IMG}/portfolio_0{i}.jpg" alt=""/>
      <p class="hmd-project__caption">Project by <strong>L'Elephant</strong></p></article>""" for i in (1,2,3))}
  </div>
</section>
<section class="hmd-buy">
  <div>
    <h2 class="hmd-buy__name">Congo 110</h2>
    <div class="hmd-buy__thumb"><img src="{IMG}/congo_thumb.png" alt=""/></div>
  </div>
  <div>
    <p class="hmd-buy__desc">For interior design visionaries, we present the CONGO Table: a seemingly
    simple piece that unveils itself as a masterpiece for those with refined sensibilities. Its hollow
    structure, expertly veneered with natural wood, transcends functionality, becoming a contemporary
    sculpture.</p>
    <div class="hmd-buy__downloads"><a href="#">Download technical sheet</a>
      <a href="#">Download 3D files</a></div>
    <figure class="hmd-buy__dimensions"><img src="{IMG}/congo_dimensions.png" alt=""/>
      <figcaption>Dimensions in cm</figcaption></figure>
    {variant('#D9A32A')}{variant('#624C1B')}
    <div class="hmd-qty"><input value="0"/><span class="hmd-qty__btns">
      <button class="hmd-qty__plus">+</button><button class="hmd-qty__minus">-</button></span></div>
    <div class="hmd-buy__actions"><button>Add to card</button></div>
    <p class="hmd-buy__price">437.00 € (tax included)</p>
    <div class="hmd-buy__actions hmd-buy__secondary"><button>Add to wishlist</button>
      <button>Compare</button></div>
  </div>
</section>
<section class="hmd-options">
  <h2 class="hmd-options__title">Other options</h2>
  <div class="hmd-options__grid">
    <div class="hmd-product-card"><img src="{IMG}/congo_thumb.png" alt=""/>
      <h3 class="hmd-product-card__name">Congo 100</h3>
      <p class="hmd-product-card__price">437.00 € (tax included)</p></div>
    <div class="hmd-product-card"><img src="{IMG}/congo_thumb.png" alt=""/>
      <h3 class="hmd-product-card__name">Congo 90</h3>
      <p class="hmd-product-card__price">431.00 € (tax included)</p></div>
  </div>
</section>'''

def page(title, body, active):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
{css}
.hmd-preview-bar {{ position:fixed; right:12px; bottom:12px; z-index:9999;
  background:#1F1C1C; color:#fff; font:12px/1.4 -apple-system,sans-serif;
  padding:8px 12px; letter-spacing:.06em; text-transform:uppercase; }}
.hmd-preview-bar a {{ color:#fff; margin-left:10px; }}
</style></head>
<body>{header(active)}<main>{body}</main>{FOOTER}
<div class="hmd-preview-bar">Pré-visualização do tema
<a href="home.html">Home</a><a href="product.html">Produto</a></div>
</body></html>'''

out = REPO / 'Website_Design' / 'preview'
(out / 'home.html').write_text(page('HMD Furniture — Home', HOME, 'HOME'), encoding='utf-8')
(out / 'product.html').write_text(page('HMD Furniture — Congo', PRODUCT, 'COLLECTION'), encoding='utf-8')
print('escrito:', *(p.name for p in sorted(out.iterdir())))
