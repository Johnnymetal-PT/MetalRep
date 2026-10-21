{
    'name': 'Product Variant Internal Reference',
    'version': '1.0.0',
    'summary': 'Gera automaticamente a referência interna (default_code) das variantes a partir de um código base + contador',
    'description': """
Product Variant Internal Reference
==================================

Objetivo de negócio
-------------------
Quando se criam variantes de produto, cada uma deve ter uma referência interna
(default_code) única e previsível, no formato "<BASE>-<NNNNN>". Fazer isto à mão é
moroso e propenso a erros; este módulo atribui a referência automaticamente.

Pré-requisitos
--------------
- Módulos: `product`.
- Existir pelo menos UMA variante do template com `default_code` preenchido, que serve
  de código BASE (a parte antes do primeiro "-"). Sem essa, as novas variantes não
  recebem código (fica registado um aviso no log).

Como funciona
-------------
Estende `product.product`:
- `create()`: ao criar uma variante sem `default_code`, procura o código base na primeira
  variante do template que já tenha código, calcula o próximo contador (maior contador
  existente + 1) e atribui "<BASE>-<NNNNN>" (contador a 5 dígitos).
- `assign_default_codes_to_all_variants()`: preenche o código de todas as variantes do(s)
  template(s) que ainda não tenham, mantendo a numeração sequencial. É chamado também
  após cada criação para cobrir variantes em falta.

Passo a passo de utilização
---------------------------
1. Criar o produto (template) e definir manualmente o `default_code` da primeira variante,
   ex.: "CAD-00001" (o "CAD" passa a ser o código base).
2. Adicionar/gerar novas variantes (por atributos). Cada nova variante recebe
   automaticamente "CAD-00002", "CAD-00003", ...
3. Para produtos antigos sem código nas variantes, correr (via shell/ação de servidor)
   `assign_default_codes_to_all_variants()` sobre as variantes do template.

Exemplo prático
---------------
Template "Cadeira X" com variante inicial `default_code = "CAD-00001"`.
Ao criar a variante "Cadeira X / Azul", o módulo atribui-lhe "CAD-00002".

FAQ / Resolução de problemas
----------------------------
- P: A nova variante ficou sem referência. Porquê?
  R: Nenhuma variante do template tinha `default_code` para servir de base. Defina o
     código da primeira variante e crie novamente (ou corra a função de atribuição).
- P: Os números não são contínuos.
  R: O contador baseia-se no maior número já existente +1; códigos apagados deixam "buracos".
- P: Quero outro número de dígitos.
  R: O formato está fixo em 5 dígitos ("%05d") no código; é preciso alterar o módulo.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- `create` usa assinatura single-record (não `@api.model_create_multi`).
- Assume que o código base é a parte antes do primeiro "-"; default_codes com outro
  padrão podem gerar resultados inesperados.
""",
    'author': 'Your Name or Company',
    'website': 'https://yourwebsite.com',
    'category': 'Inventory/Management',
    'depends': ['product'],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
