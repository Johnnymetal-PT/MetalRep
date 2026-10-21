# Pré-visualização do tema

Páginas estáticas geradas a partir do CSS **real** do módulo
`theme_hmd_furniture`, para rever a fidelidade ao desenho do XD sem precisar
de instalar nada no Odoo.

Abrir `home.html` ou `product.html` no browser.

## Regenerar

Os `.html` são **artefactos gerados** — não editar à mão. Depois de mexer no
SCSS do tema:

```bash
# 1. compilar o SCSS do módulo para CSS
cd theme_hmd_furniture/static/src/scss
cat tokens.scss layout.scss pages.scss shop.scss > /tmp/theme_all.scss
npx sass --no-source-map --style=expanded /tmp/theme_all.scss /tmp/theme_all.css

# 2. gerar as páginas
cd -
python3 Website_Design/preview/build_preview.py
```

O gerador lê `/tmp/theme_all.css` e escreve `home.html` e `product.html`.
As imagens vêm por caminho relativo de `theme_hmd_furniture/static/src/img/`.

## Limites

Isto **não** é o site: é uma maqueta estática. O mega-menu aparece sempre
aberto (é o estado desenhado por a Mónica), os widgets de carrinho e conta
são texto fixo, e não há catálogo. O comportamento real — variantes, carrinho,
wishlist, traduções — só existe no Odoo depois do deploy do módulo.
