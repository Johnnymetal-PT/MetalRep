# Nota Interna — Resposta às Ressalvas da HMD ao Ponto de Situação | Projeto Odoo HMD

**Uso:** interno Parâmetro Global (não enviar ao cliente)
**Data:** 22 de julho de 2026
**Autor:** Bruno Pinheiro
**Contexto:** o ponto de situação foi enviado à Nina a 23/06. A Nina respondeu com ressalvas a 26/06 e fez follow-up a 10/07 a pedir feedback e a sugerir reunião Teams. A atividade *"Validar ponto de situação com o cliente"* (task `6212`, ainda em Backlog) está bloqueada à nossa espera. Esta nota prepara a resposta e o enquadramento de âmbito de cada ponto, antes do email à cliente.

---

## 1. Leitura da resposta da Nina (26/06)

A resposta **não é uma validação fechada**: é uma validação parcial com ressalvas e vários inputs ainda por enviar do lado da HMD. O ponto de fundo, comercialmente, é claro e favorável a nós:

> **"Tudo o que for fora do âmbito inicial do projeto fica pendente de confirmação, até validarmos o fecho do proposto."**

Ou seja, a HMD quer **primeiro fechar/validar o âmbito protocolado (Ordem S00465)** e só depois discutir as frentes adicionais (WhatsApp, upgrade Odoo 19, suporte recorrente). Isto está alinhado com a nossa própria estratégia — devemos abraçar este faseamento e usá-lo para formalizar o fecho do protocolado e destacar as frentes adicionais como propostas próprias.

---

## 2. Análise ponto a ponto (com classificação de âmbito)

> Legenda de âmbito: **[Protocolado]** = dentro da Ordem S00465 · **[Adicional]** = frente adicional a orçamentar · **[Serviço]** = formação/acompanhamento, não desenvolvimento.
> Ordem de decisão aplicada: standard já instalado → módulo standard adicional → Studio → custom.

### 2.1 Website / Shopify — `FACTO`: pedido feito em suporte (fora de âmbito) e já resolvido
- **Correção à leitura anterior:** a data-limite "03 de junho" **não é gralha** — é real e está correta (mesmo estando hoje já ultrapassada). E, ao contrário do que o ponto de situação de 22/06 sugeria, **não é um trabalho pendente/urgente**: os desenvolvimentos web que o cliente queria foram executados **em suporte**, por serem **fora do âmbito** do projeto, e o pedido está **dado como resolvido**.
- **Evidência (Odoo PG, canal Brodoo, `read_mode=api`, 22/07/2026):**
  - `project.task:6234` — "FW: Alteração à pagina de produto" → estágio **"Entregue"** (último update **2026-06-25**), `effective_hours` registadas. É o pedido da Mónica (reencaminhado 24/06) de reorganização da página de produto, que enquadrámos **fora de âmbito** e tratámos como **pedido de suporte faturável** (ver [EMAIL_CLIENTE_ALTERACAO_PAGINA_PRODUTO_2026-06-24.md](EMAIL_CLIENTE_ALTERACAO_PAGINA_PRODUTO_2026-06-24.md)).
  - `helpdesk.ticket:11830` — "FW: Dados de Acesso HMDFurniture.com" → estágio **"New"** (16/07, **ainda aberto**): entrega dos dados de acesso ao domínio `hmdfurniture.com` e alojamento (lendarius.com). Relacionado com a tomada de controlo do site; **não bloqueia** o pedido já resolvido, mas é um fio ainda em aberto a acompanhar.
  - `PONTO POR VALIDAR`: não há nenhum registo **literalmente** rotulado "Shopify" (0 resultados em `helpdesk.ticket`/`project.task`). A evidência do pedido resolvido é a task 6234; se houver outro registo específico da migração Shopify que o Bruno tenha em mente, confirmar o ID.
- **Classificação:** `[Fora de âmbito / Suporte]` — **já entregue**. **Não** listar como pendente/urgente no âmbito protocolado.
- **Ação:** no email, **remover** o pedido de confirmação de data e **reposicionar** o tema — não há nada urgente por fazer aqui do lado do projeto; o desenvolvimento pretendido foi feito em suporte e está resolvido.

### 2.2 "Fora do âmbito fica pendente até fecharmos o proposto" — `FACTO`, aceitar
- Aceitar e formalizar. **Fecho do âmbito protocolado primeiro**; frentes adicionais (WhatsApp, upgrade 19) seguem como propostas dedicadas.
- Isto reforça a necessidade da nossa **reconciliação interna de horas** (ver secção 3).

### 2.3 Créditos e tesouraria — `[Protocolado]` (gestão de tesouraria S00465)
- Empréstimos/leasings: `account_loans` **instalado** e 1 contrato registado → base pronta. Falta lista histórica completa da HMD (input deles, prometido "até dia 3").
- Cartão de crédito: diário criado; falta validar importação automática.
- **Classificação:** `Configuração standard` (módulo já instalado). **Bloqueio:** input da HMD (lista de empréstimos) — em atraso.

### 2.4 Projetos: fases, templates, automações + guia/formação + integração CRM→fecho — misto
- **Instalado:** `project`, `project_enterprise` (fases/estágios standard), `base_automation` (automações sem código), `sale_project` e `crm` (ligação CRM↔venda↔projeto).
- Fases + templates de projeto → `Configuração standard` / `Odoo Studio`. Já existe a task interna [P1+P2+P3] "Reformular fases projeto HMD — 3 fases globais + templates".
- Automação criação de projeto ao qualificar oportunidade → `base_automation`/`Studio`, eventual `Customização leve`. **`PONTO POR VALIDAR`** de enquadramento (já assinalado no ponto de situação): candidato a **[Adicional]**.
- Guia/formação de utilização da cadeia CRM→encomenda → **[Serviço]** (formação; ver 2.6).
- **Classificação:** config/Studio para a base; formação como serviço à parte.

### 2.5 Limpeza/consolidação de contactos — `[Protocolado]` (migração de contactos S00465)
- **Bloqueio:** extração de dados do PHC (input da HMD, prometido "até 1/07") — em atraso. Task interna [V5] aberta.
- **Classificação:** serviço de migração dentro do protocolado; depende do input deles.

### 2.6 Sessões semanais de melhoria — `[Adicional / Serviço]` — **ponto comercial mais importante**
- A S00465 protocola **6 dias de suporte pós-venda**. Acompanhamento semanal continuado **excede** esse suporte → candidato a **contrato de suporte recorrente dedicado**.
- A Nina pergunta explicitamente "em que moldes? passa a ser com o Bruno?". É a abertura para propor um modelo de suporte recorrente.
- **Ação:** decidir internamente o modelo (bolsa mensal de horas vs. avença) **antes** da reunião. Não fechar por email; levar proposta à reunião.

### 2.7 Intrastat / HS code — `[Já entregue]`, clarificar mal-entendido
- **Instalado e a funcionar:** `stock_intrastat` + `account_intrastat`. Foi entregue como capacidade que **extravasou** o âmbito protocolado, mas **já está operacional e sem custo pendente**.
- A confusão da Nina vem de o termos listado como "fora do âmbito" no ponto de situação — ela leu como se estivesse "pendente". **Não está pendente nada do lado dela.**
- **Ação:** clarificar: está implementado, funciona, nada a decidir; a menção era só transparência de âmbito. `Configuração standard` (módulo standard já instalado).

### 2.8 Painéis e relatórios (formação) — `[Serviço]`, app standard já disponível
- **Instalado:** `spreadsheet_dashboard` (app Painéis do Odoo) → **standard já disponível**, nada a desenvolver.
- O pedido é de **guia/formação** para criação/uso de painéis, após fecho da fase inicial.
- **Classificação:** `Configuração standard` + **[Serviço]** de formação. Agrupar com a formação de Projetos (2.4) numa sessão de formação/revisão pós-fase.

### 2.9 Reunião Teams — aceitar e marcar
- A Nina sugeriu duas vezes (26/06 e 10/07). É o formato mais eficiente para fechar tudo isto. Aceitar e propor datas concretas.

---

## 3. Ponto por validar — interno (mantém-se de 22/06)

- **(Por validar) Balanço de horas:** S00465 protocola **400h**; o Odoo de gestão (projeto id 93) regista `allocated_hours = 338`. Reconciliar internamente **antes** de formalizar o fecho do protocolado e antes de propor as frentes adicionais/suporte recorrente. Não expor números ao cliente sem esta reconciliação.

- ~~**(Por validar) Versão de produção**~~ — **RESOLVIDO (22/07/2026):** confirmado em produção que o ambiente é **Odoo 18.0**. O `19.0.x` nas versões de manifesto dos módulos espelhados é apenas artefacto do espelho, não reflete a série do ambiente. A frente de upgrade 18→19 (M4/M5) mantém-se válida.
  - *Nota lateral:* o próprio Odoo da Parâmetro Global (parametroglobal.odoo.com) corre `19.0+e` — não confundir com o ambiente da HMD (18.0).

---

## 4. Estratégia da resposta

1. **Pedir desculpa pelo atraso** no feedback (a Nina fez follow-up a 10/07) — de forma breve e profissional.
2. **Aceitar o faseamento** proposto por ela: fechar primeiro o âmbito protocolado; adicionais depois.
3. **Responder ponto a ponto** às ressalvas (usar as clarificações da secção 2), com destaque para desfazer o mal-entendido do Intrastat.
4. **Recuperar os inputs em atraso** da HMD: lista de empréstimos/leasings e extração PHC. (O tema Shopify/página de produto **não** entra aqui — está resolvido em suporte, ver 2.1.)
5. **Não fechar por email** os temas comerciais (suporte recorrente/sessões semanais, frentes adicionais) — **levá-los à reunião Teams**, com proposta preparada.
6. **Propor 2-3 janelas concretas** para a reunião.

---

## 5. Base factual (verificada 22/07/2026)

- Âmbito protocolado: Ordem S00465 (16/12/2024) — 400h de serviços + licenciamento, faturação certificada, alojamento, 6 dias de suporte pós-venda.
- Ambiente real (`.pg/projects/odoo-hmd/project/odoo_env.json`, sync 20/07/2026): Odoo 18.0 Enterprise on-premise, 486 módulos instalados. Confirmados instalados: `whatsapp`(+`whatsapp_sale`…), `account_loans`, `stock_intrastat`, `account_intrastat`, `spreadsheet_dashboard`, `project`+`project_enterprise`, `base_automation`, `crm`+`sale_project`, `spreadsheet_sale_management`.
- Chatter da task 6212: resposta da Nina 26/06, follow-up 10/07.
