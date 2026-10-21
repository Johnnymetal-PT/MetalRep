# Instruções para Criação de Base de Dados de Demonstração (Demo)

Quando o utilizador pedir para **"criar uma demo"**, o agente de IA deve obrigatoriamente seguir este protocolo e aplicar estas regras por defeito.

## 1. Solicitação de Credenciais (Obrigatório)

Antes de realizar qualquer chamada de API ou criar scripts, o agente deve parar e pedir ao utilizador os seguintes dados de acesso para a base de dados Odoo:

- **URL da Base de Dados** (ex: `https://nome-cliente.odoo.com`)

- **Nome da Base de Dados (Db)** (ex: `nome-cliente`)

- **Login/Username do Utilizador de Admin/Integração**

- **Chave de API (API Key) ou Password**

## 2. Regras de Negócio e Sementeira de Dados (Por Defeito)

Após obter as credenciais, o agente deve analisar o contexto funcional do projeto (lendo `PG_CONTEXT.md` e a documentação existente) e configurar o Odoo de acordo com as seguintes regras fundamentais:

### A. Instalação de Módulos Odoo Relevantes

Com base no âmbito do projeto, instalar automaticamente as aplicações necessárias do Odoo core e enterprise. Para fluxos de orçamentação, projetos e fabrico (MRP), considerar:

- `crm`, `sale_project`, `project_enterprise`, `purchase`, `hr_timesheet`, `stock`, `stock_dropshipping`, `mrp`, `mrp_workorder`, `mrp_account`, `project_mrp`, `sale_mrp`.

### B. Gestão de E-mails de Demonstração (MANDATÓRIA)

- **TODOS** os e-mails criados para novos parceiros (clientes, fornecedores, contactos comerciais, etc.) **DEVEM usar obrigatoriamente o domínio `@example.com`** (ex: `cliente-demo@example.com`, `fornecedor-demo@example.com`).

- Nunca usar e-mails reais ou domínios de produção para parceiros fictícios de demonstração.

- O único e-mail com domínio real permitido é o e-mail de administrador fornecido pelo utilizador para a ligação técnica da API.

### C. Reordenação e Simplificação de Menus

- Reorganizar a ordem das aplicações no painel principal do Odoo (dashboard) de forma a refletir a ordem lógica exata da demonstração (deixando *Contactos*, *CRM* e *Vendas* nas primeiras posições).

- Se houver módulos instalados que não fazem parte do fluxo principal da demonstração (por exemplo, `rental` / Aluguer), empurrar o menu para o fim ou definir uma sequência elevada (ex: `112`), reduzindo o ruído visual no dashboard.

### D. Configurações de Inventário e Aprovisionamento

- Ativar o rastreio analítico e contabilidade analítica nas definições.

- Garantir que as rotas de stock como **MTO (Make to Order / Obter por Encomenda)** e **Buy (Comprar)** ou **Manufacture (Fabricar)** estão ativas no armazém e configuradas nos produtos de teste.

### E. Script de Simulação e Verificação

- Criar sempre um script de teste Python (ex: `simulate_full_flow.py`) para correr no terminal que simule de forma automática a criação de uma oportunidade, venda, criação de projeto/tarefas correspondentes, ordens de compra/produção e rentabilidade analítica, garantindo que a base de dados responde sem erros.

## 3. Entrega do Guia de Demonstração Comercial

- Criar um ficheiro HTML de apresentação comercial em `/guia_demo_reuniao.html` (e respetiva cópia no diretório de artefactos da IA).

- O guia deve ter um design premium (cores harmoniosas, tipos de letra modernos como *Outfit* e *Plus Jakarta Sans*, sem placeholders e com efeito interativo).

- O guia deve obrigatoriamente **começar na ficha de cliente (Contactos)** e demonstrar que a partir dos botões inteligentes da ficha do cliente se navega para as Oportunidades CRM, Vendas, Projetos e Faturas, unificando todo o circuito de ponta a ponta.
