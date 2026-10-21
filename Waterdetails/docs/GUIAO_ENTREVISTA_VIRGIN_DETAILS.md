# Virgin Details, Lda. — Guião de Levantamento de Requisitos

**Cliente:** Daniela Martins  
**Empresa:** Virgin Details, Lda.  
**Localização:** Maia, Porto, Portugal  
**Objectivo da entrevista:** confirmar processos actuais, prioridades, requisitos Odoo e pontos que exigem validação técnica ou fiscal.

> Instrução de utilização: usar as caixas de selecção para guiar a conversa. Quando a resposta não for evidente, assinalar "Por validar" e registar notas.

---

## 1. Contexto da Empresa

### 1.1 Estrutura do grupo

**Pergunta:** Como está estruturado o grupo?

- [ ] Uma empresa operacional principal
- [ ] Duas empresas com operações activas
- [ ] Uma empresa em Portugal e outra no estrangeiro
- [ ] Escritório em Portugal como representante comercial
- [ ] Outro: ______________________________
- [ ] Por validar

**Notas:**  
__________________________________________________________________

### 1.2 Utilizadores previstos

**Pergunta:** Que perfis vão utilizar o sistema?

- [ ] Administração / gestão
- [ ] Comercial
- [ ] Armazém / logística
- [ ] Compras
- [ ] Financeiro
- [ ] Contabilidade interna
- [ ] Gabinete de contabilidade externo
- [ ] Outro: ______________________________

**Número aproximado de utilizadores:** ____________________________

### 1.3 Modelo de negócio

**Pergunta:** Como actua a empresa portuguesa?

- [ ] Compra e revenda de produtos
- [ ] Representação comercial de marcas estrangeiras
- [ ] Intermediação comercial sem stock próprio
- [ ] Venda com stock próprio em Portugal
- [ ] Venda com entrega directa do fornecedor ao cliente
- [ ] Modelo misto
- [ ] Por validar

**Notas:**  
__________________________________________________________________

---

## 2. Objectivos e Prioridades

### 2.1 Objectivo principal

**Pergunta:** Qual é o principal objectivo da mudança para Odoo?

- [ ] Centralizar informação numa solução única
- [ ] Substituir o software de facturação actual
- [ ] Melhorar controlo de stock
- [ ] Melhorar controlo de compras e fornecedores
- [ ] Obter relatórios consolidados do grupo
- [ ] Controlar custos e rentabilidade por projecto
- [ ] Dar acesso móvel ao comercial
- [ ] Outro: ______________________________


## 3. Multiempresa

### 3.1 Empresas a gerir

**Pergunta:** Quantas empresas precisam de estar no Odoo?

- [ ] 1 empresa
- [ ] 2 empresas
- [ ] Mais de 2 empresas
- [ ] Por validar

**Nomes das empresas:**  
1. ________________________________________  
2. ________________________________________

### 3.2 Separação de dados

**Pergunta:** O que deve ser separado por empresa?

- [ ] NIF / dados fiscais
- [ ] Séries de facturação
- [ ] Contabilidade
- [ ] Contas bancárias
- [ ] Clientes
- [ ] Fornecedores
- [ ] Produtos
- [ ] Stock
- [ ] Utilizadores e permissões
- [ ] Por validar

### 3.3 Consolidação

**Pergunta:** Que informação deve ser consolidada ao nível do grupo?

- [ ] Vendas
- [ ] Facturação
- [ ] Margem
- [ ] Contas a receber
- [ ] Contas a pagar
- [ ] Stock
- [ ] Compras
- [ ] Projectos
- [ ] Não é necessário consolidar
- [ ] Por validar

**Notas:**  
__________________________________________________________________

---

## 4. Vendas, Orçamentos e Encomendas

### 4.1 Origem dos pedidos

**Pergunta:** Como chegam normalmente os pedidos dos clientes?

- [ ] Email
- [ ] Telefone
- [ ] Contacto directo do comercial
- [ ] Website
- [ ] Pedido formal de entidade pública
- [ ] Recomendação / contacto recorrente
- [ ] Outro: ______________________________

### 4.2 Processo comercial

**Pergunta:** Qual é o fluxo comercial habitual?

- [ ] Pedido do cliente
- [ ] Orçamento
- [ ] Aprovação do cliente
- [ ] Encomenda de venda
- [ ] Compra a fornecedor, se necessário
- [ ] Preparação de material
- [ ] Transformação interna, se aplicável
- [ ] Guia de transporte
- [ ] Factura
- [ ] Pagamento

**Variações relevantes:**  
__________________________________________________________________

### 4.3 Informação necessária no orçamento

**Pergunta:** Que informação deve constar no orçamento?

- [ ] Produtos / referências
- [ ] Descrição técnica
- [ ] Quantidades
- [ ] Preço unitário
- [ ] Desconto
- [ ] IVA
- [ ] Prazo de entrega
- [ ] Condições de pagamento
- [ ] Validade da proposta
- [ ] Transporte
- [ ] Observações comerciais
- [ ] Anexos técnicos

### 4.4 Regras comerciais

**Pergunta:** Existem regras especiais de preços ou descontos?

- [ ] Tabela de preços única
- [ ] Tabelas por cliente
- [ ] Tabelas por marca
- [ ] Tabelas por família de produto
- [ ] Descontos livres pelo comercial
- [ ] Descontos sujeitos a aprovação
- [ ] Preços negociados caso a caso
- [ ] Por validar

**Notas:**  
__________________________________________________________________

---

## 5. Compras e Fornecedores

### 5.1 Fornecedores principais

**Pergunta:** Quais são os fornecedores mais relevantes?

- [ ] Marcas de Espanha
- [ ] Marcas de Itália
- [ ] Fornecedores nacionais
- [ ] Transportadoras
- [ ] Outros: ______________________________

### 5.2 Fluxo logístico por origem

**Pergunta:** Como circulam os produtos?

- [ ] Espanha envia directamente para o cliente final em Portugal
- [ ] Espanha envia para o escritório/armazém em Portugal
- [ ] Itália envia primeiro para Portugal
- [ ] Itália envia directamente para o cliente final
- [ ] Portugal envia depois para o cliente final
- [ ] Depende do cliente/encomenda
- [ ] Por validar

### 5.3 Compras

**Pergunta:** Quando é criada uma compra ao fornecedor?

- [ ] Sempre após encomenda de cliente
- [ ] Quando stock fica abaixo de mínimo
- [ ] Por previsão de procura
- [ ] Por decisão manual da administração
- [ ] Por indicação do comercial
- [ ] Outro: ______________________________

### 5.4 Controlo de pendentes

**Pergunta:** Que pendentes precisam de acompanhar?

- [ ] Compras por confirmar
- [ ] Encomendas em atraso
- [ ] Material em trânsito
- [ ] Produtos parcialmente recebidos
- [ ] Facturas de fornecedor por receber
- [ ] Pagamentos a fornecedores
- [ ] Reclamações / devoluções

**Notas:**  
__________________________________________________________________

---

## 6. Stock e Armazém

### 6.1 Situação actual

**Pergunta:** Como é gerido o stock actualmente?

- [ ] Excel de entradas e saídas
- [ ] PHC GO
- [ ] Contagem manual
- [ ] Não existe controlo formal
- [ ] Outro: ______________________________

### 6.2 Locais de stock

**Pergunta:** Onde existe ou pode existir stock?

- [ ] Escritório/armazém na Maia
- [ ] Fornecedor em Espanha
- [ ] Fornecedor em Itália
- [ ] Cliente final
- [ ] Em transporte
- [ ] Outro: ______________________________

### 6.3 Nível de controlo pretendido

**Pergunta:** Que tipo de rastreabilidade é necessária?

- [ ] Apenas quantidade por produto
- [ ] Localização de stock
- [ ] Código de barras
- [ ] Lotes
- [ ] Números de série
- [ ] Validade
- [ ] Não necessário nesta fase
- [ ] Por validar

### 6.4 Operações de armazém

**Pergunta:** Que operações devem existir no Odoo?

- [ ] Recepção de mercadoria
- [ ] Transferências internas
- [ ] Reservas para encomendas
- [ ] Preparação de entrega
- [ ] Guias de transporte
- [ ] Inventário físico
- [ ] Ajustes de stock
- [ ] Devoluções de cliente
- [ ] Devoluções a fornecedor

**Notas:**  
__________________________________________________________________

---

## 7. Transformação de Artigos / Bill of Materials

### 7.1 Necessidade

**Pergunta:** A empresa transforma artigos internamente?

- [ ] Sim, regularmente
- [ ] Sim, ocasionalmente
- [ ] Ainda não, mas pretende passar a controlar
- [ ] Não
- [ ] Por validar

### 7.2 Exemplo de transformação

**Pergunta:** Que componentes entram normalmente no produto transformado?

- [ ] Depósito
- [ ] Bomba de água
- [ ] Acessórios
- [ ] Tubagens / ligações
- [ ] Mão de obra
- [ ] Outros componentes: ______________________________

**Produto final / nova referência:** ______________________________

### 7.3 Regras da transformação

**Pergunta:** Como deve funcionar a transformação?

- [ ] Produto final com referência própria
- [ ] Lista de materiais fixa
- [ ] Lista de materiais variável por cliente
- [ ] Baixa automática de stock dos componentes
- [ ] Entrada automática do produto final em stock
- [ ] Cálculo de custo do produto final
- [ ] Registo de mão de obra
- [ ] Registo de desperdícios/perdas
- [ ] Por validar

**Notas:**  
__________________________________________________________________

---

## 8. Facturação, Guias e Pagamentos

### 8.1 Documentos emitidos

**Pergunta:** Que documentos são necessários?

- [ ] Orçamentos
- [ ] Encomendas de venda
- [ ] Facturas
- [ ] Facturas-recibo
- [ ] Notas de crédito
- [ ] Guias de transporte
- [ ] Guias de remessa
- [ ] Recibos
- [ ] Outros: ______________________________

### 8.2 Condições de pagamento

**Pergunta:** Quais são as condições de pagamento usadas?

- [ ] Pagamento antecipado
- [ ] Pronto pagamento
- [ ] 30 dias
- [ ] 60 dias
- [ ] Pagamento parcial
- [ ] Condição específica por cliente
- [ ] Outro: ______________________________

### 8.3 Certificação e obrigações fiscais

**Pergunta:** Que requisitos legais/fiscais devem ser considerados?

- [ ] Facturação certificada pela AT
- [ ] Comunicação de documentos de transporte
- [ ] SAFT
- [ ] IVA
- [ ] Séries documentais por empresa
- [ ] Integração com contabilista
- [ ] Por validar com parceiro/localização portuguesa

**Notas:**  
__________________________________________________________________

---

## 9. Contabilidade, Bancos e Reconciliação

### 9.1 Âmbito contabilístico

**Pergunta:** O que pretendem gerir no Odoo?

- [ ] Apenas facturação
- [ ] Facturação e recebimentos
- [ ] Compras e pagamentos
- [ ] Contabilidade completa
- [ ] Reconciliação bancária
- [ ] Relatórios financeiros
- [ ] Exportação para gabinete externo
- [ ] Por validar

### 9.2 Bancos

**Pergunta:** Como pretendem tratar bancos e pagamentos?

- [ ] Importação manual de extractos
- [ ] Integração bancária automática
- [ ] Reconciliação automática
- [ ] Controlo de pagamentos de clientes
- [ ] Controlo de pagamentos a fornecedores
- [ ] Avisos de vencimento
- [ ] Por validar

**Bancos utilizados:**  
__________________________________________________________________

---

## 10. Projectos e Contabilidade Analítica

### 10.1 Tipo de projectos

**Pergunta:** Que projectos precisam de acompanhar?

- [ ] Obras maiores
- [ ] Projectos para câmaras municipais
- [ ] Instalações específicas
- [ ] Encomendas especiais
- [ ] Projectos internos
- [ ] Outro: ______________________________

### 10.2 Custos a imputar

**Pergunta:** Que custos devem ser associados a cada projecto?

- [ ] Produtos / materiais
- [ ] Compras específicas
- [ ] Horas da equipa
- [ ] Deslocações
- [ ] Transporte
- [ ] Subcontratação
- [ ] Despesas gerais
- [ ] Outros: ______________________________

### 10.3 Indicadores por projecto

**Pergunta:** Que análise pretendem obter?

- [ ] Orçamento vs custo real
- [ ] Receita por projecto
- [ ] Margem por projecto
- [ ] Custos por categoria
- [ ] Tarefas e responsáveis
- [ ] Estado de execução
- [ ] Rentabilidade final
- [ ] Por validar

**Notas:**  
__________________________________________________________________

---

## 11. Mobilidade e Comercial

### 11.1 Informação no telemóvel

**Pergunta:** Que informação o comercial deve consultar na app móvel?

- [ ] Clientes
- [ ] Contactos
- [ ] Orçamentos
- [ ] Encomendas
- [ ] Stock disponível
- [ ] Preços de venda
- [ ] Histórico de compras do cliente
- [ ] Dívidas do cliente
- [ ] Estado de encomendas
- [ ] Prazos de entrega
- [ ] Por validar

### 11.2 Acções no telemóvel

**Pergunta:** O que o comercial deve conseguir fazer na app?

- [ ] Criar orçamento
- [ ] Editar orçamento
- [ ] Confirmar encomenda
- [ ] Consultar stock
- [ ] Criar actividade/tarefa
- [ ] Registar visita ao cliente
- [ ] Consultar documentos
- [ ] Enviar orçamento ao cliente
- [ ] Apenas consulta
- [ ] Por validar

### 11.3 Permissões

**Pergunta:** Que informação deve ser limitada ao comercial?

- [ ] Preço de custo
- [ ] Margem
- [ ] Dívidas do cliente
- [ ] Informação de outras empresas
- [ ] Informação contabilística
- [ ] Sem restrições relevantes
- [ ] Por validar

---

## 12. Relatórios e Indicadores

### 12.1 Relatórios necessários

**Pergunta:** Que relatórios são essenciais?

- [ ] Vendas por empresa
- [ ] Vendas consolidadas do grupo
- [ ] Vendas por cliente
- [ ] Vendas por marca
- [ ] Vendas por produto
- [ ] Margem por produto
- [ ] Margem por projecto
- [ ] Stock disponível
- [ ] Encomendas pendentes
- [ ] Compras pendentes
- [ ] Clientes com valores em dívida
- [ ] Fornecedores com valores em dívida
- [ ] Tesouraria / bancos
- [ ] Outro: ______________________________

### 12.2 Frequência

**Pergunta:** Com que frequência devem ser analisados?

- [ ] Diário
- [ ] Semanal
- [ ] Mensal
- [ ] Trimestral
- [ ] Apenas quando solicitado

**Responsáveis pela análise:**  
__________________________________________________________________

---

## 13. Dados a Migrar

### 13.1 Origem dos dados

**Pergunta:** Que sistemas ou ficheiros têm dados a migrar?

- [ ] PHC GO
- [ ] Excel de stock
- [ ] Excel de produtos
- [ ] Excel de clientes
- [ ] Excel de fornecedores
- [ ] Email / documentos avulsos
- [ ] Outro: ______________________________

### 13.2 Dados pretendidos

**Pergunta:** Que dados devem entrar no Odoo?

- [ ] Clientes
- [ ] Fornecedores
- [ ] Produtos
- [ ] Tabelas de preços
- [ ] Stock inicial
- [ ] Facturas em aberto
- [ ] Saldos de clientes
- [ ] Saldos de fornecedores
- [ ] Histórico completo de facturação
- [ ] Apenas documentos/saldos em aberto
- [ ] Por validar

### 13.3 Qualidade dos dados

**Pergunta:** Existem problemas conhecidos nos dados actuais?

- [ ] Clientes duplicados
- [ ] Fornecedores duplicados
- [ ] Produtos sem referência normalizada
- [ ] Produtos sem família/categoria
- [ ] Stock desactualizado
- [ ] Preços desactualizados
- [ ] Dados fiscais incompletos
- [ ] Não existem problemas conhecidos
- [ ] Por validar

**Responsável pela validação dos dados:** _________________________

---

## 14. Implementação, Timing e Riscos

### 14.1 Timing

**Pergunta:** Existe data pretendida para decisão ou arranque?

- [ ] Imediato
- [ ] Próximos 30 dias
- [ ] Próximos 3 meses
- [ ] Próximos 6 meses
- [ ] Depende do custo de implementação
- [ ] Depende de validação interna
- [ ] Sem data definida

**Data alvo, se existir:** ________________________________________

### 14.2 Faseamento

**Pergunta:** Qual seria uma primeira fase aceitável?

- [ ] Multiempresa + facturação
- [ ] Vendas + facturação + stock
- [ ] Vendas + compras + stock
- [ ] Contabilidade + bancos
- [ ] Transformação de artigos
- [ ] Projectos e analítica
- [ ] Tudo de uma vez
- [ ] Por definir após proposta

### 14.3 Principais riscos

**Pergunta:** Que riscos devem ser considerados?

- [ ] Certificação fiscal portuguesa
- [ ] Migração de dados
- [ ] Qualidade do stock actual
- [ ] Adoção pela equipa
- [ ] Complexidade multiempresa
- [ ] Integração bancária
- [ ] Processos com fornecedores estrangeiros
- [ ] Custo de adaptação/implementação
- [ ] Outro: ______________________________

---

## 15. Fecho da Entrevista

### 15.1 Confirmação de obrigatórios

**Pergunta:** Sem quais destes pontos a solução não serve?

- [ ] Facturação certificada em Portugal
- [ ] Multiempresa
- [ ] Gestão de stock
- [ ] App móvel para comercial
- [ ] Transformação de artigos
- [ ] Compras a fornecedores estrangeiros
- [ ] Relatórios consolidados
- [ ] Contabilidade e bancos
- [ ] Projectos e analítica
- [ ] Outro: ______________________________

### 15.2 Próximos passos

- [ ] Validar requisitos fiscais com parceiro/localização portuguesa
- [ ] Confirmar dados a migrar
- [ ] Pedir exemplos reais de documentos
- [ ] Pedir ficheiro Excel actual de stock
- [ ] Pedir lista de produtos/referências
- [ ] Pedir exemplo de transformação de artigo
- [ ] Pedir exemplo de projecto/obra
- [ ] Preparar proposta de faseamento
- [ ] Estimar esforço de implementação

**Notas finais:**  
__________________________________________________________________
__________________________________________________________________
__________________________________________________________________

