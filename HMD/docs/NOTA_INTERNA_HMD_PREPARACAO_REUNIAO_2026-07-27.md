# Nota Interna — Preparação da Reunião de 27/07/2026 | Projeto Odoo HMD

**Uso:** interno Parâmetro Global. **Não enviar ao cliente.**
**Autor:** Bruno Pinheiro · **Data:** 27 de julho de 2026
**Contexto:** pontos sensíveis a resolver ou conter antes/durante a reunião de ponto de situação de hoje, 10h00. Complementa a agenda partilhável e o guião técnico do mesmo dia.

---

## 1. `PONTO POR VALIDAR` — Balanço de horas (agravado face a 22/06)

| Referência | Valor | Fonte |
|---|---|---|
| Serviços protocolados na Ordem S00465 | **50 dias × 480 € = 24.000 €** (≈**400 h**) | `sale.order.line` da S00465, Odoo PG |
| Horas alocadas no projeto de gestão | **338 h** | `project.project` id 93 (`allocated_hours`) |
| **Horas realmente imputadas** | **486,6 h** em 326 linhas de timesheet | `.pg/projects/odoo-hmd/PG_EFFORT_SYNC.json` |

Desvio: **≈ +86,6 h acima das 400 h protocoladas** e **≈ +148,6 h acima das 338 h alocadas**. Distribuição relevante: João Barros 331,6 h; Mariana Oliveira 52,8 h; Vitor Costa 25,5 h; Miguel Dias 20,0 h. Em julho/2026 há apenas 7,8 h imputadas.

**Atenuante a considerar na reconciliação:** a própria Nina afirma, no email de 23/07, que o website inicial foi feito por nós "com muitos erros pelo que inclusive as horas dedicadas não seriam contabilizadas" — ou seja, parte das horas do website (tarefas "Website" ≈ 36,8 h, "Melhoramento website" ≈ 10,3 h, "HMD Odoo Formação Site" ≈ 10,0 h) já é, na leitura do cliente, não faturável. Isso muda a conversa: podemos ter consumido mais horas do que o protocolado **e** ter uma parte dessas horas contestada.

**Regra para hoje:** **não expor qualquer número de horas** ao cliente. A reconciliação (o que conta contra a bolsa, o que é suporte, o que é retrabalho não faturável) tem de ser feita internamente antes de qualquer conversa de fecho de âmbito ou de proposta adicional.

## 2. `PONTO POR VALIDAR` — Estado comercial da Ordem S00465

`FACTO OBSERVADO` (Odoo PG, canal Brodoo, hoje):

- A **S00465** (16/12/2024, 30.316,20 € s/IVA, cliente HMD Interiors / Nina Hedderich, oportunidade "Odoo HMD Furniture", ligada ao projeto 93) está em estado **`cancel`**, com `invoice_status = no`.
- As **únicas** faturas ao cliente neste Odoo são 6 documentos de 2026: 756,00 € (03/03) e cinco de ≈90 €/mês (alojamento), totalizando **1.216,30 €** s/IVA — todos `posted` e com `payment_state = not_paid`.

`INFERÊNCIA`: a faturação do projeto foi feita fora deste Odoo (PHC) e/ou a ordem foi substituída/reemitida sem reflexo aqui; o `payment_state` também sugere que a reconciliação de pagamentos não é feita neste ambiente.

**Implicação direta para hoje:** vamos falar de "fecho do âmbito protocolado" invocando um documento que, no nosso próprio sistema, está **cancelado e não faturado**. Isto não impede a reunião — o âmbito material está documentado e é aceite por ambas as partes — mas **impede** que assumamos hoje qualquer compromisso de fecho contratual, adenda ou orçamento adicional. Confirmar com a área administrativa/comercial:

1. Onde está a base contratual viva (documento, versão, valor, horas) e o que já foi faturado.
2. Se existe adenda ou ordem posterior que substitua a S00465.
3. Se as 6 faturas de 2026 estão realmente em aberto ou se o pagamento não está reconciliado neste Odoo.

## 3. Acompanhamento continuado — decisão: **não abordar hoje**

Decisão tomada: o modelo de acompanhamento/suporte recorrente **não entra na reunião de hoje** e não vão valores à mesa. Fica para depois do fecho do âmbito protocolado — o que é coerente com o próprio faseamento proposto pela HMD.

**Resposta de contenção, se a Nina levantar o tema** (ela já o perguntou duas vezes: 26/06 e 23/07):

> "Queremos manter o acompanhamento e é um tema a que damos importância. Preferimos, no entanto, fechar primeiro o âmbito protocolado — como propuseram — e apresentar-vos depois uma proposta concreta de moldes, em vez de decidirmos isso agora de forma parcial."

**Nota factual a ter presente:** a tarefa **[OPS] Sessões semanais HMD — Quinta 10h-10h30 (a partir 2026-05-28)** está em *Backlog*, com 16 h alocadas e **0 h imputadas** — as sessões não estão a acontecer. Se a Nina o notar, assumir sem rodeios e ligar ao mesmo faseamento. O âmbito protocolado prevê apenas **6 dias de suporte pós-venda**, pelo que acompanhamento continuado excede o protocolado — argumento a usar mais tarde, não hoje.

## 4. Estado do projeto — números internos (não expor tal e qual)

- **236 tarefas** espelhadas; **12 abertas**, das quais 5 são da frente `[v19]` e apenas 3 têm responsável atribuído.
- **M1 (15/06)** e **M2 (30/06)** ultrapassados e ainda em `planned`; M3 30/09, M4 31/10, M5 15/01/2027. `progress` do projeto = 0.
- Abertas com relevância operacional: "Erro ao conectar o banco" (*Sprint Backlog*), "Erro no e-mail de saída do Miguel", `[C11]` alerta de pagamento → estado da encomenda (6 h), `[W2]` acerto O365/alojamento com Cláudio.
- **Suporte:** 15 tickets históricos da HMD, 14 resolvidos; **1 aberto** — *"FW: Dados de Acesso HMDFurniture.com"* (16/07, em **New**, Hugo Ferreira). É o fio do domínio. Os dados de acesso ao domínio e ao painel de alojamento foram entregues pelo fornecedor do site nesse ticket; **não repetir credenciais em documentos ou email**.

## 5. Riscos da reunião e como os conter

1. **Cadência de resposta.** Entre 26/06 e 22/07 estivemos quase um mês sem responder (férias), e as questões de 23/07 continuam sem resposta escrita. Conter: entrar com agenda estruturada e sair com datas concretas por ponto.
2. **Inputs em atraso do cliente.** Empréstimos ("até dia 3") e contactos ("até 1/07") continuam pendentes. Usar sem atrito, como explicação factual do calendário — não como acusação.
3. **Marcos ultrapassados.** Se não reagendarmos hoje, o próximo ponto de situação repete a mesma crítica.
4. **Tudo cair no mesmo saco.** O maior risco técnico é a HMD ler configuração, comportamento standard, defeito nosso e âmbito adicional como um único bloco de "coisas que não funcionam". Separar explicitamente em cada resposta (ver guião).
5. **Higiene de comunicação.** No email de 22/07 enviado à Nina ficou um marcador interno no corpo do texto ("!!!!!!!desenvolvimento realizado e validado pelo cliente"). Sem consequência aparente, mas revisar antes de enviar passa a ser regra.

## 6. Estado da validação técnica

A ligação de produção da HMD foi registada hoje em *Brodoo > Repositório > Ligações Odoo do cliente* (`https://intranet.hmdfurniture.com/`, BD `HMD`, login `it.odoo@parametro.pt`), o que permitiu **validar B1 e B2 no ambiente real às 09h40**. Resultados que mudam o discurso da reunião:

- **Registo no site aberto a qualquer visitante** (`auth_signup.invitation_scope = b2c`) — não é configuração B2B. Alteração simples, com consequência operacional (contas passam a ser por convite).
- **Não existe menu "Todos os produtos"** no website *HMD Furniture*: o que a Nina vê é a primeira linha da **barra de categorias da loja**. Muda a resposta — não é remover um menu.
- **205 artigos com produtos alternativos vs. 80 com produtos opcionais** (276 publicados): confirma que a queixa do carrinho é **configuração de catálogo**, não defeito. E dimensiona o trabalho de uniformização — não prometer prazo hoje.
- Existem **2 websites** no ambiente (*HMD Furniture* e *Fria*) — aplicar definições ao website correto.

**Limitação remanescente:** o utilizador de API não tem acesso ao modelo `website.website`, pelo que as definições de checkout/acesso ao eCommerce por website ficam por confirmar em ecrã. Vale a pena rever as permissões desse utilizador para análises futuras.

**B4 (empréstimos) não foi validado no ambiente** — mantém-se como caminho recomendado a demonstrar com o caso BCP.

## 7. Checklist antes das 10h00

- [ ] Confirmar internamente a base contratual viva e o que está faturado (secção 2).
- [ ] Confirmar quais tutoriais foram efetivamente enviados à HMD e quando (evita afirmação errada na reunião).
- [ ] Confirmar com Hugo Ferreira o estado do bloqueio do domínio junto do alojamento atual.
- [ ] Pedir à Nina, no início da reunião, o **artigo/URL concreto** do problema do carrinho e do erro do bloco 3D.
- [ ] Ter aberto o contrato BCP em `Contabilidade > Empréstimos` para a demonstração do ponto B4.

## 8. Referências

- `.pg/projects/odoo-hmd/`: `tasks/tasks.json`, `chatter/chatter.json`, `PG_EFFORT_SYNC.json`, `project/deliverables.json`, `planning/planning.json`, `project/odoo_env.json`
- Odoo PG, canal Brodoo (`read_mode=api`, 27/07/2026): `sale.order` e `sale.order.line` (S00465), `account.move`, `helpdesk.ticket`, `mail.message`/`mail.activity` da tarefa 6212, `pg.odoo.connection`
- `docs/PONTO_SITUACAO_HMD_2026-06-22.md`, `docs/NOTA_INTERNA_HMD_PONTOS_VALIDAR_2026-06-22.md`, `docs/NOTA_INTERNA_HMD_RESPOSTA_RESSALVAS_2026-07-22.md`
- `docs/AGENDA_REUNIAO_HMD_2026-07-27.md`, `docs/GUIAO_RESPOSTA_QUESTOES_HMD_2026-07-27.md`
