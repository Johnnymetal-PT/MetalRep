# Revisao de obsolescencia dos custom modules - 2026-06-02

## Contexto

- Versao origem: Odoo 17.0
- Versao alvo do piloto: Odoo 18.0
- Estado previo: todos os modulos custom instalaram em Odoo 18 apos as correcoes MIG-0001..MIG-0008.
- Objetivo desta revisao: identificar desenvolvimentos que possam ter ficado obsoletos, duplicados ou parcialmente substituiveis por funcionalidades standard do Odoo 18.

Esta revisao nao altera codigo. As conclusoes abaixo devem ser tratadas como triagem funcional/tecnica e confirmadas com owners do processo antes de remover modulos.

## Referencias Odoo 18 usadas

- Odoo 18 Discounts: desconto standard por linha e botao de desconto global/fixo.
- Odoo 18 Product variants: variantes e atributos standard no produto.
- Odoo 18 Managing BoMs for product variants: uma BoM pode servir multiplas variantes do mesmo produto.
- Odoo 18 Packages: packages e package types com peso, dimensoes e shipping weight.
- Odoo 18 Analytic accounting: distribuicao analitica em faturas/contas e modelos de distribuicao.
- Odoo 18 IoT: ligacao de dispositivos fisicos, incluindo impressoras, via IoT Box/Windows virtual IoT.

## Veredicto por modulo

| Modulo | Veredicto | Motivo | Acao recomendada |
|---|---|---|---|
| `pg_tecidos_old` | Obsoleto provavel | Existe `pg_tecidos` atual, mais completo e ja instalado. O sufixo `_old` indica variante legacy. | Nao incluir no escopo ativo salvo se houver fluxo historico que dependa explicitamente dele. |
| `PG_Etiquetas_zpl_old` | Obsoleto provavel | Tem o mesmo nome tecnico visivel que `PG_Etiquetas_zpl`, depende de mais modulos e nao inclui `views/label_template.xml`, que existe no modulo atual. | Manter fora do escopo ativo; confirmar se algum report/wizard antigo ainda e usado. |
| `pg_consumption_table` | Obsoleto provavel / sobreposto | Implementa tabela simples `price_1..price_10` no produto e override de `mrp.production.create` para `Tecido de Fornecedor`. `pg_fabric_consumption` implementa consumo por variante/subvariante, validacoes, BOM duplicada, fornecedores e consignacao. | Validar com negocio se ainda ha produtos que usam exclusivamente esta tabela simples. Se nao houver, remover do piloto ativo. |
| `base_view_inheritance_extension` | Manter enquanto `purchase_analytic` existir | `purchase_analytic` usa `operation=\"update\"` em atributos XML. Este comportamento e fornecido por este addon OCA, nao por configuracao standard. | Manter se `purchase_analytic` continuar. Se `purchase_analytic` for removido/substituido, reavaliar. |
| `purchase_analytic` | Parcialmente substituivel | Odoo 18 tem distribuicao analitica e modelos automaticos, mas este modulo adiciona distribuicao analitica ao cabecalho da compra e propaga para linhas. | Manter se o processo precisa definir analitica no cabecalho do PO. Alternativa: testar se modelos standard cobrem o caso sem modulo. Preferir versao OCA 18 oficial se disponivel. |
| `pg_multi_discount` | Nao obsoleto, mas parcialmente sobreposto | Odoo 18 suporta desconto por linha e descontos globais/fixos. O modulo calcula descontos em cascata no formato `10+5+2`, propaga metadados para compras/faturas e usa grupos. | Manter se descontos multiplos em cascata forem requisito. Nota: parte de vendas esta comentada no manifest; validar se compra/fatura e o unico escopo real. |
| `pg_sale_salesperson` | Nao obsoleto | Odoo standard tem vendedor interno (`user_id`), mas este modulo usa `res.partner` como salesperson funcional e adiciona smart button/relatorio. | Manter se salesperson for contacto/parceiro e nao utilizador interno. |
| `pg_fabric_consumption` | Nao obsoleto | Odoo 18 cobre variantes e BoMs por variantes, mas nao cobre diretamente consumo de tecido por subvariante, duplicacao controlada de produtos/BOMs, copia de fornecedores e consignacao automatica. | Manter. Validar fluxo ponta a ponta: venda configurada -> MO -> BOM -> consumo -> compra/consignacao. |
| `pg_tecidos` | Nao obsoleto | Implementa normalizacao PT/EN de atributos, naming de componentes, substituicao/duplicacao de componentes de BOM, supplierinfo em stock moves e campos de traducao auxiliares. | Manter. Requer validacao funcional forte em produtos configuraveis e MOs. |
| `pg_packing_list_custom` | Parcialmente sobreposto | Odoo 18 tem packages/package types com peso/dimensoes, mas este modulo calcula packing list por produto/stock move ate 6 volumes, cubicagem e totais personalizados para documentos. | Manter se o documento/packing list usa estes totais. Avaliar no futuro se packages standard podem substituir parte dos campos. |
| `PG_Etiquetas_zpl` | Parcialmente sobreposto | Odoo 18 IoT suporta impressoras, mas o modulo adiciona botoes/wizards e templates ZPL/report especificos da operacao. | Manter se as etiquetas ZPL custom continuam necessarias. Validar impressao real em IoT. |
| `pg_bd_geral_security` | Nao obsoleto | Requisitos de perfil BD Geral sao especificos: ACLs restritos, menus re-gated e regras de stock/qualidade/projeto. Odoo standard fornece grupos, mas nao o perfil composto exato. | Manter. Validar com utilizador-teste e rever ponto MIG-0004 sobre modulo/app BD Geral. |
| `pg_producao_armazem_security` | Nao obsoleto | Perfil custom para Producao/Armazem: acesso a apps operacionais, vendas so leitura e valores ocultos. Standard nao cobre exatamente esta combinacao. | Manter. Validar visibilidade de valores em todas as vistas de venda. |

## Principais candidatos a remover do escopo ativo

1. `pg_tecidos_old`
2. `PG_Etiquetas_zpl_old`
3. `pg_consumption_table`, se confirmado que `pg_fabric_consumption` substitui totalmente o fluxo antigo de consumo simples.

## Desenvolvimentos parcialmente substituiveis por standard

Estes nao devem ser removidos automaticamente, mas sao bons candidatos a simplificacao futura:

- `purchase_analytic`: comparar cabecalho de compra custom vs modelos analiticos standard.
- `pg_packing_list_custom`: comparar campos custom de packing list vs packages/package types standard.
- `pg_multi_discount`: comparar desconto multiplo em cascata vs desconto standard por linha/global.
- `PG_Etiquetas_zpl`: comparar templates/wizards custom vs impressao standard via IoT.

## Proximas validacoes funcionais recomendadas

1. Confirmar com negocio se os modulos `_old` sao apenas historicos e podem ficar fora do piloto.
2. Criar uma MO que exercite `pg_consumption_table` e outra que exercite `pg_fabric_consumption`; se o primeiro nao tiver caso real, marcar como removivel.
3. Testar uma compra com distribuicao analitica no cabecalho e verificar se o comportamento standard de modelos analiticos cobre o mesmo processo.
4. Testar desconto multiplo em compra e vendor bill com uma expressao em cascata, por exemplo `10+5+2`.
5. Testar packing list numa entrega com multiplos volumes e comparar com packages standard.
6. Testar perfis de seguranca com utilizadores reais/clone: BD Geral e Producao/Armazem.
