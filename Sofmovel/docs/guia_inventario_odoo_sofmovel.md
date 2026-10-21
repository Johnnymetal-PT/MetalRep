# Sofmovel - Guia de Inventario Fisico no Odoo

## 1. Contexto e objetivo de negocio

Este documento explica qual o procedimento recomendado para realizar inventario fisico no Odoo 17 da Sofmovel, com o objetivo de corrigir as quantidades em mao de forma rastreavel e alinhada com o processo standard da plataforma.

O objetivo principal e permitir que a equipa operacional registe contagens reais de stock sem recorrer a alteracoes avulsas de quantidade fora do fluxo standard de inventario.

**Trigger:** Pedido do cliente para perceber se pode "ajustar manualmente as quantidades em mao" e qual a forma mais correta de fazer o inventario.

**Impacto de negocio se nao resolvido:** Risco de discrepancias entre stock fisico e stock registado, menor rastreabilidade operacional, dificuldade de auditoria interna e potencial desalinhamento contabilistico.

## 2. Processo recomendado

O procedimento recomendado e usar o ecra standard de inventario fisico do Odoo:

`Inventario > Operacoes > Inventario Fisico`

Neste ecra, a equipa:

1. seleciona os produtos e localizacoes a contar;
2. regista a quantidade contada fisicamente;
3. define o motivo ou referencia do ajuste;
4. aplica o ajuste;
5. guarda evidencia da contagem e da justificacao.

**Ferramenta recomendada:** ecra standard `Physical Inventory` / `Inventario Fisico` do Odoo.

**Frequencia:** periodica ou ciclica, conforme a politica interna da Sofmovel.

## 3. Necessidade identificada

- O cliente pretende corrigir quantidades em mao, mas quer evitar impactos indevidos a nivel contabilistico ou fiscal.
- Existe risco de interpretar "ajuste manual" como alteracao direta de quantidades fora do fluxo standard do Odoo.
- E importante nao confundir uma contagem fisica com outros acertos tecnicos ou operacionais que tenham causa diferente.

## 4. Pressupostos confirmados

- A Sofmovel utiliza Odoo 17 Enterprise em ambiente on-premise.
- O processo aqui descrito parte do pressuposto de que o inventario sera feito pelo fluxo standard do Odoo.
- Na base produtiva da Sofmovel, a valorizacao de stock esta configurada como `manual_periodic`.
- O metodo de custo identificado esta configurado como `standard`.
- A verificacao realizada nao encontrou variacao entre categorias de produto neste ponto.

## 5. Guia operacional

### 5.1 Quando usar este processo

Usar este processo quando o objetivo e corrigir o stock registado para o stock fisico realmente existente.

Exemplos:

- contagem geral de armazem;
- contagem ciclica por zona ou familia;
- correcao de divergencias detetadas em auditoria interna;
- regularizacao de faltas ou sobras identificadas fisicamente.

### 5.2 Quando nao usar este processo

Nao usar este processo para:

- atualizar stock em massa por ficheiros de fornecedor sem validacao operacional;
- "forcar" disponibilidade no website;
- corrigir problemas de regras de aprovisionamento, reservas ou website;
- substituir recebimentos, entregas, transferencias internas ou sucata quando esses movimentos sao a causa real da divergencia.

### 5.3 Passo a passo no Odoo

1. Entrar em `Inventario > Operacoes > Inventario Fisico`.
2. Filtrar os produtos ou localizacoes que vao ser contados.
3. Se necessario, usar a atribuicao de utilizador e data planeada para distribuir a contagem.
4. Na coluna de quantidade contada, registar a quantidade fisica real.
5. Rever a diferenca entre quantidade em sistema e quantidade contada.
6. Ao aplicar, preencher uma referencia ou motivo claro.
7. Confirmar o ajuste apenas depois de validada a contagem.
8. Arquivar a folha de contagem, listagem exportada ou outra evidencia interna usada na contagem.

### 5.4 Boas praticas operacionais

- Contar por localizacao, e nao apenas por produto agregado.
- Evitar fazer a contagem enquanto existem rececoes, entregas ou transferencias a decorrer na mesma zona.
- Definir um motivo objetivo para o ajuste, por exemplo: `Contagem ciclica junho 2026 - Armazem Freamunde`.
- Em produtos com lotes ou numeros de serie, garantir que a contagem e feita com o lote/serie correto.
- Em diferencas materialmente relevantes, pedir segunda contagem antes da aplicacao.

### 5.5 O que deve ficar registado

- data da contagem;
- utilizador responsavel;
- localizacao;
- quantidade em sistema;
- quantidade contada;
- diferenca;
- motivo do ajuste;
- evidencia da contagem, quando aplicavel.

## 6. Notas contabilisticas e legais

### 6.1 Nota contabilistica

O inventario fisico nao e apenas uma operacao logistica. Sempre que exista uma diferenca entre a quantidade registada e a quantidade fisica, ha uma regularizacao de inventarios com relevancia contabilistica.

Em termos de enquadramento contabilistico portugues, a `NCRF 18 - Inventarios` estabelece que perdas e ajustamentos de inventarios devem ser reconhecidos como gasto do periodo em que ocorram.

Isto significa que:

- uma quebra real de stock nao deve ser tratada como simples "edicao tecnica" sem contexto;
- o ajuste deve ficar suportado por contagem e motivo;
- a entidade deve conseguir explicar a origem de faltas, sobras ou quebras materialmente relevantes.

### 6.2 Nota fiscal e legal

Este processo nao corresponde, por si so, a uma regra fiscal especial autonoma em Portugal. Ou seja, usar o ecra standard de inventario fisico do Odoo nao e um problema fiscal por definicao.

Ainda assim, o tema tem relevancia fiscal indireta porque:

- inventarios influenciam o resultado contabilistico e, por essa via, a materia tributavel;
- as perdas/quebras devem ser coerentes com a contabilidade da entidade;
- a empresa esta sujeita a obrigacoes de comunicacao de inventario a AT, nos termos legais aplicaveis.

### 6.3 Impacto no Odoo na configuracao atual da Sofmovel

Na configuracao atualmente identificada na base produtiva da Sofmovel, a valorizacao de stock esta em modo manual (`manual_periodic`).

Isto significa que o ajuste de inventario continua a ter relevancia contabilistica de fundo, mas nao e esperado que o Odoo gere automaticamente lancamentos contabilisticos de valorizacao de stock como aconteceria num cenario de valorizacao automatica.

Por esse motivo, o ponto critico nao e evitar o ecra standard de inventario. O ponto critico e garantir que cada ajuste fica suportado por contagem real, motivo claro e validacao interna adequada.

## 7. Recomendacao pratica para a Sofmovel

Para a Sofmovel, a orientacao recomendada e:

- usar sempre o fluxo standard de `Inventario Fisico` para contagens e regularizacoes operacionais;
- nao tratar ajustes de inventario como simples alteracao massiva de quantidades fora do fluxo standard;
- considerar que, na configuracao atual identificada, a valorizacao de stock esta manual e o metodo de custo esta standard;
- separar problemas de inventario fisico de problemas de disponibilidade no website ou de logica de aprovisionamento.

## 8. Pontos de governance a definir internamente

- Definir politica interna para contagens ciclicas, segunda contagem e aprovacao de diferencas relevantes.
- Definir quem e o responsavel interno por validar ajustes de inventario com impacto material.
- Definir qual a evidencia minima a arquivar para cada contagem.

## 9. Referencias consultadas

### Documentacao oficial Odoo

- https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/count_products.html
- https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/product_management/inventory_valuation/inventory_valuation_config.html
- https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/product_management/inventory_valuation/using_inventory_valuation.html

### Enquadramento contabilistico e legal Portugal

- NCRF 18 - Inventarios: https://www.cnc.min-financas.pt/pdf/snc/2016/normas/NCRF_18.pdf
- Texto pesquisavel com a passagem sobre reconhecimento como gasto: https://dre.pt/application/file/69889638
- Comunicacao de inventarios a AT - artigo 3.o-A: https://diariodarepublica.pt/dr/detalhe/lei/82-b-2014-66016527
- Dispensas relativas a valorizacao dos inventarios: https://diariodarepublica.pt/dr/detalhe/lei/82-2023-835864042
