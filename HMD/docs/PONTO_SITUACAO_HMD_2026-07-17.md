Exmos. Senhores,

Partilhamos abaixo o ponto de situação dos trabalhos realizados no âmbito do projeto **Odoo — HMD Interiors**, com base nas atividades registadas até **10 de julho de 2026**.

---

## 1. Resumo executivo

O projeto tem como objetivo consolidar e evoluir as adaptações Odoo que ligam venda, compra, produção e publicação web de produtos e projetos, melhorando a rastreabilidade e reduzindo a operação manual. Ao longo do período foram desenvolvidas atividades transversais às áreas de gestão de projeto e formação, website e eCommerce, vendas e orçamentação, infraestrutura, importação de dados e contabilidade/qualidade.

Os trabalhos focaram-se maioritariamente em:

- Evolução da **calculadora de transporte** e da **calculadora de preços** integradas no orçamento, incluindo a decomposição de custos e a ponte das embalagens do orçamento para a expedição;

- Consolidação e afinação do **website e da apresentação de produtos** (grelha de imagens, acessos, navegação);

- **Estabilização operacional** — correções de faturação, comunicação de valores e apoio recorrente através de tutoriais escritos.

No global, o projeto encontra-se numa fase de estabilização comercial e de qualidade, com o roteiro já orientado para a preparação do upgrade para o Odoo 19.

---

## 2. Trabalhos realizados

### Vendas, orçamentos e calculadoras

Área central deste período, focada em dotar a equipa comercial de ferramentas de orçamentação fiáveis e automáticas dentro do próprio orçamento.

- Calculadora de **transporte** com comparação entre transportadoras, destacando a opção mais económica e aplicando o custo diretamente na linha do orçamento;

- Camada de **avisos e mensagens** (motivo de LDM vs. m³, limiares de peso, validações de dimensões) alinhada com a versão mais recente da folha de cálculo da HMD;

- **Cadeia de preço** completa (custo base, sobretaxa de combustível, margem e custo por palete), com decomposição dos valores no orçamento e nas observações de logística;

- **Reaproveitamento das medidas** de caixas e paletes da simulação de orçamento na guia de expedição, evitando reintrodução manual;

- Calculadora de **preço/margem** por linha, com correção para margem sobre o preço de venda conforme validado.

Estas ferramentas reduzem significativamente o esforço manual e o risco de erro na elaboração de orçamentos.

### Website e eCommerce

Trabalho continuado de afinação da apresentação do catálogo e da experiência de navegação.

- Reformulação da **grelha de imagens** na página de produto e reposicionamento de imagens/media;

- Ajustes de navegação, menus e acessos de clientes registados;

- Melhoramentos gerais e formação sobre a gestão do site.

O website encontra-se estável e a apresentação de produtos alinhada com o pretendido.

### Estabilização, contabilidade e qualidade

Correções pontuais e capacitação da equipa em processos financeiros e de qualidade.

- Correção de erros de faturação e do comportamento de comunicação de valores;

- Diagnóstico do diário predefinido nas faturas de cliente (afinação de configuração, sem desenvolvimento);

- Materiais de apoio (tutoriais) sobre controlo de qualidade, adiantamentos, categorias de despesa, cash-flow e custo/hora de colaborador.

Estas ações aumentam a autonomia da equipa e reduzem o volume de pedidos de suporte pontual.

### Infraestrutura e sistemas

Manutenção e segurança da plataforma que suporta a operação.

- Configuração de firewall (PFSense) e acesso externo à intranet;

- Atualizações de módulos e do servidor, certificação e apoio à configuração de emails.

A plataforma mantém-se operacional e atualizada.

### Importação de dados e catálogo

Continuação da consolidação do catálogo e dos dados provenientes do PHC.

- Levantamento de catálogo e listagem de pendentes de importação;

- Importações sucessivas de clientes, fornecedores e produtos.

### Gestão de projeto, reuniões e formação

Acompanhamento regular do projeto e capacitação da equipa.

- Reuniões periódicas de ponto de situação e sessões semanais de acompanhamento;

- Sessões de formação e gestão contínua do backlog.

---

## 3. Carga horária registada

**Total de horas registadas (acumulado do projeto, 15/01/2025 a 10/07/2026):** 481h21

**Distribuição resumida por área:**

| Área | Horas |
|---|---|
| Gestão de projeto, reuniões e formação | 116h30 |
| Website e eCommerce | 114h30 |
| Infraestrutura e sistemas | 51h45 |
| Contabilidade, faturação e qualidade | 34h45 |
| Compras, produção e projetos | 32h15 |
| Importação de dados e catálogo | 27h50 |
| Vendas, orçamentos e calculadoras | 26h55 |
| Outros / diversos | 76h51 |

**Distribuição por consultor:**

| Consultor | Horas |
|---|---|
| João Barros | 328h50 |
| Mariana Oliveira | 52h46 |
| Vitor Costa | 25h30 |
| Miguel Ângelo Barros Dias | 20h00 |
| Pedro Coelho | 17h30 |
| Hugo Ferreira | 9h30 |
| João Castro | 8h00 |
| Nuno Oliveira | 7h15 |
| Outros consultores | 12h00 |

---

## 4. Estado atual

À data deste relatório, o projeto encontra-se com progresso relevante nas seguintes frentes:

- Calculadoras de transporte e de preço **desenvolvidas e em fase de validação**, com decomposição de custos e ponte para a expedição concluídas;

- Website e apresentação de produtos **estáveis** e alinhados com o pretendido;

- Processos financeiros e de qualidade **documentados** e com a equipa capacitada através de tutoriais;

- Roteiro do projeto organizado em 5 marcos, atualmente na fase de **estabilização comercial e qualidade**, com preparação do upgrade para o Odoo 19 já mapeada.

---

## 5. Próximos passos

Os próximos passos passam por:

- **Colocar em produção** as evoluções das calculadoras e as correções pendentes, seguidas de validação funcional com a equipa HMD;

- Concluir a **validação das tabelas de tarifas de transporte** e das regras de cálculo com a HMD;

- Automatizar o **alerta de pagamento do cliente** para atualização do estado da encomenda;

- Iniciar a **preparação do upgrade para o Odoo 19** (ambiente de testes e adaptação dos módulos), sujeita à decisão de go/no-go.

---

## 6. Riscos e pontos de atenção

- **Deploy diferenciado das calculadoras:** os módulos têm procedimentos de atualização distintos (uma reinstalação vs. atualização), pelo que a colocação em produção requer coordenação para preservar as tarifas configuradas. *Mitigação: procedimento de deploy documentado e executado em janela combinada.*

- **Compatibilidade com o upgrade para o Odoo 19:** as adaptações desenvolvidas terão de ser revistas para garantir compatibilidade. *Mitigação: refactor mapeado como marco dedicado e testado previamente em ambiente clonado.*

---

## 7. Decisões pendentes do cliente

| Decisão necessária | Impacto se não decidido | Prazo |
|---|---|---|
| Confirmação das tabelas de tarifas de transporte e regras de cálculo | Bloqueia a validação final e a entrada em produção da calculadora | A confirmar |
| Go/no-go do upgrade para o Odoo 19 | Condiciona o arranque da preparação e a calendarização da janela Dez/Jan | A confirmar |
| Acerto contratual O365 / alojamento | Impacto na faturação e na continuidade dos serviços de infraestrutura | A confirmar |

---

Ficamos disponíveis para qualquer esclarecimento adicional.

Com os melhores cumprimentos,

João Barros
Parâmetro Global
