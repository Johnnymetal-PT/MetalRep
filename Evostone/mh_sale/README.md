# MH Inventory - Custom Variant Pricing

Este módulo resolve o problema onde os preços manuais das variantes são perdidos quando os atributos do produto são modificados.

## Funcionalidades

- **Campo Personalizado**: Cada variante tem campos `custom_list_price` e `custom_standard_price`
- **Proteção contra Perda**: Os preços personalizados não são sobrescritos quando atributos mudam
- **Interface Amigável**: Checkbox no produto para ativar/desativar preços personalizados
- **Smart Button**: Acesso rápido à gestão de preços das variantes
- **Menu Dedicado**: Menu específico para gerir preços de variantes

## Como Usar

### 1. Ativar Preços Personalizados
1. Vá para o produto template (ex: Slab PN Mármore Estremoz)
2. Na aba "Sales", marque **"Use Custom Variant Pricing"**
3. Salve o produto

### 2. Definir Preços das Variantes

**Opção A - Via Smart Button:**
1. No produto template, clique no botão "Custom Pricing"
2. Defina `Custom Sale Price` e `Custom Cost Price` para cada variante
3. Salve

**Opção B - Via Menu:**
1. Vá para Sales → Configuration → Variant Custom Pricing
2. Edite os preços das variantes diretamente

**Opção C - Via Variante Individual:**
1. Abra uma variante específica
2. Na aba "Sales", seção "Custom Variant Pricing"
3. Defina os preços personalizados

### 3. Comportamento

- **Preços Ativos**: Quando `use_custom_variant_pricing = True`, os preços personalizados são usados
- **Proteção**: Modificar atributos não afeta mais os preços definidos
- **Inicialização**: Ao ativar, os preços atuais são copiados para os campos personalizados

## Exemplo Prático

Para o Slab PN Mármore Estremoz com 56 variantes:

1. Ative "Use Custom Variant Pricing"
2. Defina preços específicos:
   - Branco/Select/30mm/Polido: €150/m²
   - Branco/Comercial/20mm/Areado: €80/m²
   - Claro/Select 1ª/30mm/Polido: €140/m²
   - etc...
3. Modificar atributos (adicionar nova classe, espessura) não afeta os preços já definidos

## Instalação

1. Copie o módulo para a pasta addons do Odoo
2. Atualize a lista de aplicações
3. Instale o módulo "MH Inventory - Custom Variant Pricing"

## Compatibilidade

- Odoo 18.0
- Depende dos módulos: product, sale, stock