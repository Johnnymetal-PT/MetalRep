# Avaliação da base de dados HMD - Tarefa 6607

Data da análise: 2026-08-04  
Ambiente analisado: produção HMD, Odoo 18.0 Enterprise  
Modo de acesso: API, exclusivamente leitura

## Objetivo

Avaliar os campos em falta nos contactos e artigos usados em documentos comerciais recentes, medir o impacto no fluxo encomenda de venda -> entrega/packing list -> faturação e propor regras de obrigatoriedade. Nenhum dado foi alterado em produção.

## Amostra

- 185 documentos comerciais não cancelados com data desde 2026-01-01: 65 orçamentos, 66 orçamentos enviados e 54 encomendas confirmadas.
- 181 contactos distintos usados como cliente, endereço de faturação ou endereço de entrega.
- 812 linhas de artigo e 395 artigos distintos; 376 artigos físicos e 19 serviços.
- Nas 54 encomendas confirmadas: 83 transferências associadas e 100 movimentos contabilísticos de cliente associados.

## Factos observados

### Contactos

- Nos contactos usados pelas 54 encomendas confirmadas não há faltas em morada, código postal, cidade, país, NIF, email ou telefone/telemóvel.
- No universo dos 185 documentos não cancelados, existem 4 contactos sem país. Afetam 3 orçamentos e 1 orçamento enviado; não afetam encomendas confirmadas.
- Não foram detetadas encomendas sem contacto de faturação ou de entrega.

Conclusão: a qualidade dos contactos é globalmente boa. A única lacuna objetiva encontrada é o país em quatro documentos ainda não confirmados.

### Artigos

Todos os 395 artigos analisados têm referência interna, código de barras, categoria, unidade de venda e unidade de compra. A lacuna relevante está nos campos personalizados usados pela packing list.

Dos 376 artigos físicos:

| Tipificação | Artigos |
|---|---:|
| Sem volumes, peso e cubicagem | 92 |
| Com volumes, mas sem peso e sem cubicagem | 67 |
| Com volumes e cubicagem, mas sem peso | 8 |
| Com volumes e peso, mas cubicagem zero | 1 |
| Com peso, mas volumes zero | 1 |
| Packing completo | 207 |

Em termos de campos isolados:

- 93 artigos têm `packing_volumes = 0`.
- 167 artigos têm `packing_weight = 0`.
- 161 artigos têm `packing_cubicagem = 0`.
- 68 artigos declaram volumes, mas falta pelo menos uma dimensão num dos volumes declarados.
- Não existem quantidades fracionárias de volumes nem divergências entre a cubicagem armazenada e a calculada pelas dimensões existentes.

As falhas distribuem-se por 12 categorias. Nas principais categorias coexistem artigos completos e incompletos, pelo que a categoria do artigo, isoladamente, não é um critério seguro para impor obrigatoriedade.

### Impacto no fluxo

- Das 812 linhas de artigo, 314 têm volumes a zero, 447 têm peso a zero e 434 têm cubicagem a zero.
- Nas encomendas confirmadas existem 46 entregas de saída não canceladas: 4 têm total de volumes zero, 8 têm peso total zero e 7 têm cubicagem total zero.
- Os 200 movimentos de stock dessas entregas incluem 26 linhas com volumes zero, 73 com peso zero e 67 com cubicagem zero.
- As 100 faturas/notas de crédito ligadas às encomendas têm parceiro preenchido; 94 estão publicadas e 6 canceladas.

O código personalizado calcula os valores da encomenda e da entrega diretamente a partir dos campos de packing do artigo. Assim, dados em falta no artigo propagam zeros para a linha de venda, movimento de stock e packing list. Não foi encontrada evidência de falha estrutural no cálculo.

## Proposta de obrigatoriedade

1. Criar no artigo um indicador explícito `Requer dados de embalagem`, aplicável aos artigos físicos que seguem para entrega. A decisão não deve depender apenas da categoria.
2. Para artigos com esse indicador, exigir `packing_volumes > 0`, `packing_weight > 0` e comprimento, altura e largura maiores que zero para cada volume declarado.
3. Manter a cubicagem calculada automaticamente. Deve ser validada pelo resultado das dimensões, não introduzida manualmente como campo obrigatório.
4. Mostrar aviso enquanto o documento está em orçamento e bloquear a confirmação da encomenda quando um artigo que requer embalagem estiver incompleto.
5. Repetir a validação antes da emissão da packing list ou validação da entrega, para cobrir alterações posteriores ao artigo.
6. Exigir país apenas quando o contacto for usado como cliente, endereço de faturação ou endereço de entrega num documento a confirmar. Não tornar o país obrigatório globalmente em todos os contactos.
7. Criar filtros de qualidade de dados para artigos e contactos incompletos, permitindo correção antecipada sem esperar por um erro operacional.

## Correção de dados proposta

- Submeter ao cliente a lista dos 169 artigos físicos incompletos para decisão e preenchimento dos dados reais. Não inferir peso ou dimensões automaticamente.
- Corrigir o país nos quatro contactos antes da confirmação dos respetivos orçamentos.
- Depois da correção, recalcular os campos armazenados das linhas de venda, movimentos e transferências ainda abertos.
- Validar primeiro numa cópia de testes e só depois promover as regras para produção.

## Ponto pendente

O Brodoo tem a ligação de produção configurada e funcional, mas não tem ligações `brodoo_dev` ou `client_test` para este projeto. A reprodução transacional do fluxo, que exige criar/confirmar documentos, não deve ser feita em produção. Fica pendente disponibilizar uma base não produtiva para testar os bloqueios e as automações propostas.
