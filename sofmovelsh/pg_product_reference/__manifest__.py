{
    'name': 'PG Product Reference',
    'version': '19.0.1.0.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Gera automaticamente a referência interna e o código de barras dos produtos (substitui a automação Studio da V17).',
    'description': """
PG Product Reference
====================

a) Objetivo de negócio
----------------------
Cada artigo e cada variante da Sofmovel tem de ter uma referência interna e um
código de barras próprios, gerados automaticamente a partir de uma sequência.
Na V17 isto era feito por Odoo Studio — automação "PG Gerar Código Barras"
(`base.automation` 4) sobre a server action 973, mais a sequência
`product.cod_artigo`. Estando fora do código, não migra para a v19: este módulo
substitui esse mecanismo.

Cobre a tarefa 6562 (referência automática). A tarefa 6567 ("alterar atributo
não actualiza a referência interna") é da **página web** e não deste módulo:
está atribuída a outra pessoa da equipa. O que este módulo garante é o lado dos
dados — a variante nova nasce com referência —, sem o qual a página web não
teria sequer o que mostrar.

b) Pré-requisitos
-----------------
- Módulo standard `product`.
- Sequência `product.cod_artigo`. Vem na base migrada da V17 (id 48, sem
  prefixo, `padding` 7). Se não existir, é criada pelo `post_init_hook`.

c) Como funciona
----------------
- `models/product_product.py`
  - Override de `create` em `product.product`: preenche `default_code` e
    `barcode` em falta a partir da sequência, **antes** do `super()`.
    Disparar na criação da variante — e não num `onchange` do artigo, como na
    V17 — é o que faz a geração cobrir importações, API e, sobretudo, as
    variantes novas criadas quando se altera um atributo (tarefa 6567).
  - `_pg_build_barcode`: dois formatos, ver alínea (g).
  - `_pg_mirror_to_studio_fields`: copia os valores para
    `x_studio_referncia_interna` e `x_studio_cdigo_de_barras` enquanto esses
    campos existirem na base, sem nunca sobrepor valores históricos.
  - `_pg_backfill_references` / `_pg_fill_missing`: recuperação das variantes
    existentes, reaproveitando a referência Studio quando ela existe.
- `models/product_template.py`
  - Campo novo `pg_template_code` — ver alínea (g), é o ponto mais importante
    deste módulo.
  - `_pg_snapshot_template_codes`: preserva a referência actual do artigo.
  - `action_pg_generate_references`: acção manual sobre artigos seleccionados,
    a substituir o uso manual da server action 973.
- `hooks.py`: cria a sequência só se faltar e corre o snapshot das referências
  de artigo.

d) Passo a passo de utilização
------------------------------
1. Instalar o módulo. O `post_init_hook` preserva as referências de artigo
   existentes em `pg_template_code`.
2. Correr a recuperação das variantes em lotes, até devolver 0:
   `env['product.product']._pg_backfill_references(limit=2000)`.
3. Confirmar as contagens (origem = destino) antes de dar por concluída a
   recuperação.
4. A partir daqui, artigos e variantes novos recebem referência e código de
   barras sozinhos.

e) Exemplo prático
------------------
Artigo com o atributo "Cor" e dois valores. Ao acrescentar um terceiro valor,
o Odoo cria a variante nova; o `create` deste módulo dá-lhe referência
`0128107` e código de barras `8433840128107` sem intervenção. Na V17 a variante
nova ficava sem referência, porque a automação só corria no `onchange` da
categoria do artigo e só quando os campos estavam vazios.

f) FAQ / Resolução de problemas
-------------------------------
- "A referência do artigo desapareceu depois da recuperação":
  Ver alínea (g). Correr `_pg_snapshot_template_codes()` **antes** de escrever
  nas variantes; o `post_init_hook` já o faz na instalação.
- "A recuperação parou a meio com erro de código de barras duplicado":
  O `barcode` é único por empresa. O erro é propositadamente ruidoso — na V17
  as excepções eram engolidas e os produtos ficavam em silêncio por tratar.
  Corrigir o duplicado e voltar a correr; o método é idempotente.
- "Quero importar produtos com os códigos da origem":
  Chamar com `with_context(pg_skip_auto_reference=True)`.
- "Os campos `x_studio_*` não existem":
  É o esperado numa base v19 limpa. O espelho é ignorado.

g) Pontos de atenção
--------------------
- **Referência do artigo (`pg_template_code`)** — a diferença estrutural entre
  V17 e v19 neste módulo. Em v19 `product.template.default_code` é calculado a
  partir das variantes (`_compute_default_code` →
  `_compute_template_field_from_variant_field`) e vale `False` quando o artigo
  tem mais do que uma variante. A base da V17 tem referência gravada em
  artigos multi-variante que **não** corresponde a nenhuma variante (valor
  gravado pela automação 973 e nunca recalculado, porque as variantes nunca
  chegaram a ter `default_code`). À primeira escrita de `default_code` numa
  variante, o standard recalcula e apaga essa referência do artigo. Daí o campo
  próprio e o snapshot no `post_init_hook`.
- **Formato do código de barras** — o modo por omissão (`legacy`) reproduz a
  V17: prefixo + 7 dígitos. Tem 13 caracteres mas o último dígito é o da
  sequência e não o dígito de controlo, pelo que a maioria dos códigos **não é
  EAN-13 válido** (ex.: `8433840038709` tem dígito de controlo 4, não 9). Fica
  por omissão para não divergir das etiquetas já impressas nem dos códigos já
  em base. O modo `ean13` gera códigos válidos, à custa de conviver com dois
  formatos.
- Parâmetros de sistema: `pg_product_reference.ean_prefix` (omissão `843384`),
  `pg_product_reference.barcode_mode` (`legacy` | `ean13`),
  `pg_product_reference.mirror_studio` (`True` | `False`).
- Se a referência vier de fora mas faltar o código de barras, é consumido um
  número de sequência só para o código de barras — nesse caso referência e
  código de barras não coincidem.
- Face à V17, foram deliberadamente removidos: a escrita em
  `ir.model.fields.store` em tempo de execução, a exigência de categoria
  preenchida (que só servia de guarda e nunca era usada) e o `except Exception`
  que escondia falhas produto a produto.
    """,
    'depends': ['product'],
    'data': [
        'views/product_template_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
