# Novo website HMD — configuração a repetir em produção

Registo do que **não** vive no módulo `theme_hmd_furniture` e por isso se perde
quando a base de teste for refrescada a partir da produção.

Tudo isto foi feito na base `HMD_TESTE` (website 7). Em produção (`HMD`) o
destino é o **website 3 — «HMD Furniture 2026»**, já criado e sem domínio.

> **Estado a 07/10/2026 — aplicado na produção (#7871, #7872, #7040).**
> Tema aplicado ao website 3 a 06/10, com as secções 1 a 3 deste documento,
> as 7 páginas editadas no teste e as categorias da secção 4 (decisão da HMD
> de 07/10, partilhadas com a intranet). O website 3 continua **sem domínio**.
> Cópia de segurança anterior: `/var/lib/postgresql/HMD_antes_site_2026-10-06.dump`.
> Scripts usados (locais, `.pg/migration/` do repositório HMD):
> `hmd_7871_site_novo_website3.py`, `hmd_7872_paginas_editor_w3.py`,
> `hmd_7040_decisoes_contactos_categorias.py`.
>
> **Falta, no dia da colocação online:** passar as listas WHOLESALE e RPP
> (website 1) para o website 3 — decidido pela HMD a 07/10; nenhum cliente
> usa o site antigo. Antes disso deixaria a loja da intranet sem listas.

---

## 1. Aplicar o tema

Instalar o módulo **não muda nada** em nenhum site (verificado: as impressões
digitais dos sites existentes ficaram idênticas). Aplicar é que actua, e só
sobre o website seleccionado.

- **Pela interface:** seleccionar primeiro o website 3 em
  `/website/force/3?path=/`, confirmar no topo que diz «HMD Furniture 2026»,
  e só então *Website → Escolher um Tema → HMD Furniture Theme*.
- **Por API:** `button_choose_theme` com `context={'website_id': 3}`.
  Atenção: por API o gancho `_post_copy` **não corre** (a instalação recarrega
  o registry e perde o contexto), pelo que os passos 2 e 3 têm de ser feitos à
  mão.

---

## 2. Vistas a ligar e desligar (por website)

Usar `theme.utils.disable_view` / `enable_view` com `context={'website_id': 3}`.

**Desligar**

| Vista | Porquê |
|---|---|
| `website.template_header_default` | colide com o nosso cabeçalho (dois `position="replace"` no mesmo nó → HTTP 500) |
| `website.footer_custom` | idem, para o rodapé |
| `website_sale.products_categories` | o desenho não tem barra lateral no catálogo |
| `website_sale.products_attributes` | idem, filtros |
| `website_sale.products_categories_top` | idem, categorias no topo |
| `website_sale.sort` | idem, ordenação |
| `website_sale.search` | a pesquisa vive no cabeçalho |
| `website_sale.alternative_products` | os produtos já incluem o snippet editorial «OTHER OPTIONS» em `website_description`; manter também a vista nativa duplica a secção inteira |

**Ligar**

| Vista |
|---|
| `theme_hmd_furniture.template_header_hmd` |
| `theme_hmd_furniture.footer_hmd` |
| `website.footer_no_copyright` |

---

## 3. Definições do website

| Campo | Valor | Porquê |
|---|---|---|
| `shop_ppr` | 5 | 5 colunas no catálogo |
| `shop_ppg` | 10 | 10 produtos por página, como no XD |
| `domain` | vazio | não intercepta o site vivo |
| `sequence` | 900 | fica fora do caminho de *fallback* |

**Menus:** remover `Shop` e `Blog` da navegação principal (o Odoo cria-os por
defeito e o desenho não os tem; «Products» vive na coluna direita).

**`header_overlay = True`** nas páginas com hero de imagem inteira — `/` e
`/we-are`. Sem isto o cabeçalho empurra a imagem em vez de flutuar por cima, e
o véu translúcido perde a função.

---

## 4. Categorias de produto

O mega-menu lê `product.public.category`. Estas alterações são **dados**, não
código.

### Ordem (campo `sequence`)

| Mesas | Estofo | Arrumação |
|---|---|---|
| Mesas de Jantar | Cadeiras | Aparadores |
| Mesas Extensíveis | Cadeirões | Consolas |
| Mesas Bar | Poufs | Prateleiras |
| Mesas Auxiliares | Bancos | Móveis TV |
| Mesas de Centro | Sofás | |
| Mesas Bistro | Sofás Modulares | |
| Secretárias | | |
| Mesas de Cabeceira | | |

### Traduções em falta

| Categoria | EN | PT |
|---|---|---|
| Modular Sofas | Modular Sofas | Sofás Modulares |
| Consolas | Consoles | Consolas |
| Móveis TV | TV Units | Móveis TV |
| mesas Bistro | Bistro | Mesas Bistro |
| Bar tables | Bar Tables | Mesas Bar |

> **Armários:** o desenho tem essa categoria em Arrumação, mas o desenho está
> desactualizado (confirmado com a HMD). Não criar.

---

## 5. Correcção do editor de blocos

O bundle `website.backend_assets_all_wysiwyg` não compila por causa de um
`min(calc(100vw - 1rem), …)` no módulo `hmd_website_local_typography`. O `min()`
é função de CSS **e** de Sass; o compilador tenta calculá-la e falha. Com o
bundle partido, o construtor de website não abre.

**Contorno aplicado no teste** — registo `ir.asset`:

| Campo | Valor |
|---|---|
| bundle | `website.backend_assets_all_wysiwyg` |
| directive | `remove` |
| path | `hmd_website_local_typography/static/src/scss/website_local_typography.scss` |

**Correcção de fundo:** trocar no SCSS por `width: X; max-width: calc(100vw - 1rem);`,
que é equivalente em CSS e não passa pelo compilador.

> ⚠️ O ficheiro no servidor **não está no git**: a versão do repositório tem 17
> linhas e não contém este código. Um deploy a partir do repositório apagaria a
> alteração sem aviso.

---

## 6. Sequência de aplicação depois de mexer no módulo

| Mudou | É preciso |
|---|---|
| SCSS | limpar o cache de assets (`ir.attachment` com `url like /web/assets/%`) |
| Templates XML | **upgrade do módulo** |
| Python | upgrade **+ reinício do serviço** |

Ficheiro no servidor ≠ site actualizado. Os templates só entram na base de
dados com o upgrade.

### Dados alterados num `odoo shell`: limpar a cache dos processos

Um script corrido em `odoo shell` grava na base, mas **não avisa** os
processos que servem o site. Estes guardam em cache, entre outras coisas, a
lista de menus de cada website. A 06/10/2026, ao retirar dois menus do
website 3 por script, o website deu HTTP 500 (`MissingError:
website.menu(36,)`) até se limpar a cache. No fim de qualquer script que
altere dados:

```python
env.cr.commit()
env.registry.clear_all_caches()
env.registry.signal_changes()
```

### O botão «Publicado» actua no website seleccionado

«HMD Furniture» (intranet) e «HMD Furniture 2026» (site novo) confundem-se.
A 06/10/2026 a página inicial da intranet foi despublicada por engano e
ficou inacessível para visitantes até ao dia seguinte (ciclo de
redireccionamentos para `/`). Confirmar sempre o seletor de website antes
de mexer no editor ou no «Publicado».

---

## 7. Avisos de infraestrutura

**Memória.** O servidor tinha 324 MB livres e 1,8 GB de 2,2 GB de swap em uso,
com oito instâncias de Odoo. Foi isso que derrubou a instância de teste a meio
de um upgrade em 26/08. O mesmo pode acontecer em produção — fazer o deploy
fora de horas, com backup e com alguém disponível para reiniciar.

**Disco.** 89% ocupado, 22 GB livres, com três cópias do filestore da HMD a
ocupar cerca de 30 GB.

---

## 8. Coordenadas do servidor

Confirmadas em 27/08/2026. **Uma só máquina** aloja produção e teste.

| | Produção | Teste |
|---|---|---|
| SSH | `root@hmd.parametro.pt` = `154.58.193.71` (`odoo17pg`), o mesmo para as duas | |
| URL | `https://intranet.hmdfurniture.com` | `https://hmd.parametro.pt` |
| vhost Apache | `hmd-le-ssl.conf` | `hmd_teste-le-ssl.conf` |
| porta Odoo | 9101 (+ 9072 websocket) | 9222 |
| base de dados | `HMD` | `HMD_TESTE` |
| serviço systemd | — | `odoo_hmd_teste.service` |
| `odoo.conf` | `/ProgGest/Odoo18/Clientes/HMD/odoo.conf` | `/ProgGest/Odoo18/Clientes/HMD/Odoo_Teste/odoo.conf` |
| log | — | `/ProgGest/Odoo18/Clientes/HMD/Odoo_Teste/Logs/odoo.log` |
| Python | `/ProgGest/Odoo18/python-venv/bin/python3.10` | idem |
| `odoo-bin` | `/ProgGest/Odoo18/Server/odoo-bin` | idem |

O módulo vive em
`/ProgGest/Odoo18/Clientes/HMD/addons/HMD/theme_hmd_furniture`.

### ⚠ O `addons_path` é partilhado pelas duas instâncias

As **duas** confs incluem `/ProgGest/Odoo18/Clientes/HMD/addons/HMD`. Consequências:

- Qualquer `rsync` para essa pasta altera código que a **produção** também lê.
- O módulo aparece na lista de Apps da `HMD`, mesmo sem estar instalado.
- A separação entre teste e produção depende, exclusivamente, de o módulo
  **não estar instalado** na base `HMD`. Não há isolamento no sistema de
  ficheiros.
- Alterações a Python nesta pasta só entram em produção com reinício do
  serviço de produção — mas um reinício por outro motivo qualquer chega para
  as carregar. Não deixar código a meio nesta pasta.

### Comandos

Sincronizar o módulo (do Mac, **fora** de uma sessão SSH):

```bash
rsync -av --checksum ~/Documents/Parametro/HMD-website/theme_hmd_furniture/ \
  root@hmd.parametro.pt:/ProgGest/Odoo18/Clientes/HMD/addons/HMD/theme_hmd_furniture/
```

Limpar o cache de assets só na base de teste, pelo ORM (a invalidação chega ao
processo que serve a porta 9222, logo **não** é preciso reiniciar):

```bash
ssh root@hmd.parametro.pt 'bash -s' <<'EOF'
echo "r = env['ir.attachment'].search([('url','like','/web/assets/%')]); print('ENCONTRADOS:', len(r)); r.unlink(); env.cr.commit(); print('APAGADOS OK')" \
 | /ProgGest/Odoo18/python-venv/bin/python3.10 /ProgGest/Odoo18/Server/odoo-bin shell \
     -c /ProgGest/Odoo18/Clientes/HMD/Odoo_Teste/odoo.conf -d HMD_TESTE --no-http
EOF
```

A `odoo.conf` define `logfile`, por isso o comando **não** escreve nada no
terminal sem um `print` explícito. Silêncio não é sinal de falha — mas também
não é confirmação: manter o `print`.

---

## 9. Validar SCSS antes de sincronizar

O Odoo compila SCSS com **libsass**, não com dart-sass. A diferença importa:
`min()` e `max()` são funções de CSS **e** de Sass ao mesmo tempo. O dart-sass,
quando os argumentos têm unidades incompatíveis, desiste e passa a expressão
para CSS. O libsass tenta calcular e falha:

```
Internal Error: Incompatible units: 'px' and 'vw'.
```

Um único erro destes faz falhar o bundle **inteiro** — o site fica sem CSS e
aparece a notificação «Style error» no browser. Já aconteceu três vezes neste
projecto (`px`/`%` duas, `px`/`vw` uma).

**Regra: não usar `min()` nem `max()` no SCSS deste tema.** Usar sempre o par
de propriedades:

```scss
// errado
width: min(60vw, 1152px);
// certo
width: 60vw;
max-width: 1152px;
```

`clamp()`, `minmax()` e `calc()` não são funções de Sass e passam intactas —
esses podem usar-se à vontade, mesmo com unidades mistas.

**Testar com o compilador certo** antes de qualquer rsync. Uma vez só:

```bash
python3 -m venv /tmp/sassenv && /tmp/sassenv/bin/pip install libsass
```

Depois, a cada alteração:

```bash
cd theme_hmd_furniture/static/src/scss
for f in tokens layout pages shop; do
  /tmp/sassenv/bin/python -c "
import sass,sys
try: sass.compile(filename='$f.scss'); print('OK    $f')
except sass.CompileError as e: print('FALHA $f:', str(e).strip().splitlines()[0])
"
done
```

`primary_variables.scss` não se testa isolado: depende de `\$o-color-palettes`,
definido pelo Odoo. Nesse ficheiro o que há a garantir é o `append` no manifest
(ver o comentário lá) — com `prepend` o bundle falha com
`Undefined variable: "\$o-color-palettes"`.
