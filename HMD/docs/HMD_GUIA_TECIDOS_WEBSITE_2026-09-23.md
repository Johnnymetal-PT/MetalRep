# Guia — Tecidos no website HMD

- **Para:** Mónica Hedderich (HMD)
- **De:** Lara Cunha — Parâmetro Global
- **Data:** 23/09/2026
- **Onde se aplica:** Odoo de produção, o mesmo onde já carrega os produtos

---

## Antes de começar: onde se trabalha

**Este trabalho faz-se no Odoo de produção, o do costume, e não no site novo.**

O `novo.hmd.parametro.pt` é um endereço temporário, só para verem o desenho antes da passagem, e desaparece quando o site novo entrar. O que fosse preenchido lá perdia-se. Preenchido no Odoo de produção, fica feito uma vez e já está no sítio certo quando o site novo arrancar.

## Como a página funciona

- Cada **série** de tecido (ex.: LUDE) é um produto no Odoo. Cada **cor** é uma variante desse produto, com a sua fotografia.
- A página `/fabrics` agrupa as séries pela **categoria** (CAT I a CAT V, e C.O.M.).
- Ao clicar numa amostra abre-se a página da série: as cores, a categoria, a **composição** e o botão para descarregar a **ficha técnica**.
- A composição e a ficha são **da série**, não da cor: basta preencher uma vez por série.
- Só aparecem no site as séries **publicadas**.

## O que falta carregar

Há 32 séries. **Nenhuma tem ainda categoria, composição nem ficha técnica** no Odoo de produção, e 27 cores estão sem fotografia. A tabela no fim deste guia mostra o que falta em cada série, com uma proposta de categoria para confirmar.

---

## Passo a passo

### 1. Abrir uma série

**Vendas › Produtos › Produtos**, e pesquisar o nome da série (ex.: `LUDE`). Abre-se a **série**, não cada cor.

### 2. Escrever a composição

1. No produto, abrir o separador **Tecido**.
2. No campo **Composição**, escrever a composição básica (ex.: `100% linho`).
3. Escolher a **Categoria de tecido** (CAT I a CAT V, ou C.O.M.). É ela que decide em que secção a série aparece. Na tabela do fim há uma proposta para cada série.
4. Guardar.

O campo **Família de tecido** preenche-se sozinho a partir das duas primeiras letras do nome (LU, AL, IM…). Não é preciso mexer nele.

### 3. Anexar a ficha técnica

1. No topo do produto, clicar no botão **Documentos**.
2. Carregar o PDF da ficha técnica.
3. Ligar **Publicar no site** nesse documento. Sem esta opção o ficheiro fica anexado, mas não aparece no site.

**Atenção:** a ficha tem de ser anexada à **série**, no produto, e não a uma cor. O Odoo não publica documentos anexados a uma variante.

### 4. Fotografia de uma cor

1. No produto, abrir o botão **Variantes**.
2. Abrir a cor em falta e carregar a imagem.

### 5. Decidir o que aparece

No produto, o botão **Publicado** / **Não publicado** mostra ou esconde a série em `/fabrics`.

### 6. Verificar

Cada série já tem a sua página de especificações. Abrir o endereço da série, por exemplo (o de cada série está na última coluna da tabela):

`https://intranet.hmdfurniture.com/fabrics/lude-24816`

e confirmar que aparecem a composição e o botão da ficha técnica.

A página ainda aparece com o aspecto do site antigo. O desenho novo só se aplica na passagem, mas o conteúdo é o mesmo. O `novo.hmd.parametro.pt` não mostra este trabalho, porque lê do Odoo de teste.

**Sugestão:** preencher primeiro uma só série e ver o resultado, antes de fazer as outras.

---

## Se alguma coisa não aparecer

| O que se vê | Porquê | O que fazer |
|---|---|---|
| A página da série dá «página não encontrada» | A série não está publicada | Publicar (passo 5) |
| A série não aparece em nenhuma secção de `/fabrics` (no site novo) | Não tem categoria | Separador **Tecido** → **Categoria de tecido** (passo 2) |
| Não aparece o botão da ficha | O documento não está publicado, ou está anexado a uma cor | Passo 3: anexar à série e ligar **Publicar no site** |
| Uma cor aparece sem imagem | A variante não tem fotografia | Passo 4 |

---

## O que falta, série a série

Categoria, composição e ficha técnica faltam em **todas**. A categoria proposta é a que está hoje no site de teste: confirme ou corrija. As séries com **não** na coluna "Publicada" não aparecem no site, e a página delas só abre depois de publicadas: é para confirmar se é intencional.

| Série | Categoria proposta | Publicada | Cores | Cores sem fotografia | Página (em intranet.hmdfurniture.com) |
|---|---|---|---:|---|---|
| ALBO | CAT I | sim | 11 | — | /fabrics/albo-24562 |
| ALCH | CAT I | sim | 5 | 10 | /fabrics/alch-24801 |
| ALMO | CAT I | sim | 1 | — | /fabrics/almo-24802 |
| ALRC | CAT I | sim | 10 | 01 | /fabrics/alrc-24803 |
| ALSI | CAT I | sim | 6 | 0056 | /fabrics/alsi-24804 |
| ALSW | CAT I | sim | 4 | 03 | /fabrics/alsw-24805 |
| LQ435 | CAT I | **não** | 6 | OYSTER 0021 | /fabrics/lq435-23160 |
| LQ550 | CAT I | sim | 1 | LQ550 | /fabrics/lq550-24815 |
| IMAI | CAT II | sim | 12 | 220 | /fabrics/imai-24806 |
| IMAN | CAT II | sim | 21 | 200 | /fabrics/iman-24807 |
| IMCR | CAT II | sim | 10 | 204 | /fabrics/imcr-24808 |
| IMFU | CAT II | sim | 6 | 400 | /fabrics/imfu-24812 |
| IMLA | CAT II | sim | 6 | 200 | /fabrics/imla-24811 |
| IMMAM | CAT II | sim | 3 | 204 | /fabrics/immam-24810 |
| IMST | CAT II | sim | 11 | 200 | /fabrics/imst-24809 |
| LUBE | CAT II | sim | 7 | 28 | /fabrics/lube-24819 |
| LUCO | CAT II | sim | 7 | 19 | /fabrics/luco-24740 |
| LUDE | CAT II | sim | 7 | 14, 16 | /fabrics/lude-24816 |
| LUMA | CAT II | sim | 7 | — | /fabrics/luma-24817 |
| LUQU | CAT II | sim | 10 | 28 | /fabrics/luqu-24818 |
| JQNI | CAT III | sim | 5 | 211 | /fabrics/jqni-24820 |
| JQRI | CAT III | sim | 5 | — | /fabrics/jqri-24823 |
| JQSE | CAT III | sim | 4 | TALPA | /fabrics/jqse-24822 |
| JQTR | CAT III | sim | 4 | CD22 | /fabrics/jqtr-24821 |
| PRDA | CAT III | sim | 6 | BIANCO | /fabrics/prda-24813 |
| LA803 | CAT IV | sim | 6 | 0027 | /fabrics/la803-24814 |
| SYAT | CAT IV | sim | 6 | — | /fabrics/syat-23155 |
| SYBO | CAT IV | **não** | 6 | 900 | /fabrics/sybo-23156 |
| SYCO | CAT IV | **não** | 6 | 911 | /fabrics/syco-23157 |
| SYHI | CAT IV | **não** | 7 | — | /fabrics/syhi-23158 |
| SYPA | CAT IV | **não** | 7 | 900 | /fabrics/sypa-23159 |
| LEATHER | CAT V | sim | 4 | SELECT 390 | /fabrics/leather-24977 |

*Levantamento feito a 23/09/2026 no Odoo de produção.*
