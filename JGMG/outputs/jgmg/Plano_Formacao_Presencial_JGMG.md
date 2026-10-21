# JGMG — Plano da Formação Odoo

**Versão:** 2.0 · **Data:** 06/10/2026 · **Autor:** Lara Cunha (Parâmetro Global) · **Estado:** Data acordada na reunião de 02/10/2026

| Item | Valor |
|---|---|
| Cliente / Empresa | JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA — design de interiores, compra de produtos e montagem |
| Data | **Sexta-feira, 16/10/2026, das 15:00 às 18:00** (3 horas) |
| Versão / Edição Odoo | Enterprise 19.0 (SaaS `saas~19.4`), base em período de teste |
| Faturação | Faturas a clientes emitidas no Odoo, sem faturação certificada — decisão do cliente (02/10/2026) |
| Empresa-alvo | Empresa única. A cervejaria não entra nesta fase |
| Tarefa Odoo PG | 6788 «Formação presencial» |
| Material de apoio | Conhecimento › Guias de formação Odoo › Tutoriais da formação (sessões 1 a 7) |

---

## 1. Objetivo

No fim da tarde, cada colaborador deve conseguir fazer sozinho o circuito da empresa no Odoo:

**oportunidade → orçamento → projeto → compras → fatura do fornecedor → fatura ao cliente**

Com 3 horas, a formação mostra o circuito completo e deixa o detalhe de cada tema para os tutoriais do Conhecimento, que cada pessoa pode seguir ao seu ritmo.

Nota: a interface do Odoo está em português do Brasil. Os nomes de menus e botões são apresentados tal como aparecem no ecrã.

---

## 2. Pré-requisitos (falha = adiar a formação)

- [ ] **Base ativa no dia 16/10.** A base de teste atual expira a 09/10; tem de estar duplicada (tarefa 7580) e todos têm de ter o **endereço novo**.
- [ ] **Todos os participantes entram na base duplicada** — confirmar 2 dias antes.
- [x] Dados reais importados: 664 contactos e 2 241 artigos com stock (02/10).
- [x] Dados da empresa completos (NIF, morada, telefone, email, IBAN, logótipo).
- [x] Fases dos projetos definidas (modelo «Geral»).
- [ ] Sala com ecrã ou projetor e rede; cada participante com o seu portátil.

---

## 3. Programa (15:00–18:00)

| Hora | Tema | Tutorial |
|---|---|---|
| 15:00–15:15 | **Primeiros passos:** entrar, navegar, pesquisar, histórico e atividades; onde estão os tutoriais | Sessão 1 |
| 15:15–15:45 | **Artigos e CRM:** encontrar artigos importados (por referência), criar um artigo novo; registar e acompanhar uma oportunidade | Sessão 2 |
| 15:45–16:30 | **Orçamentos e faturas a clientes:** orçamento por secções, enviar, confirmar; criar a fatura (sinal ou total), enviar, registar o pagamento | Sessões 3 e 6 (Parte A) |
| 16:30–16:40 | Pausa | |
| 16:40–17:20 | **Projetos:** fases do modelo «Geral» (Ficha cliente → Orçamentação → Orçamentos fechados → Aditamentos → Financeiro → Encomendas → Entregas → Auditoria), tarefas, anexos, horas | Sessão 4 |
| 17:20–17:50 | **Compras e faturas de fornecedores:** pedido de cotação, encomenda, receção; registar a conta do fornecedor a partir da compra | Sessões 5 e 6 (Parte B) |
| 17:50–18:00 | Dúvidas e próximos passos | |

**Fica para uma sessão à parte:** PLM e listas de materiais (tutorial da sessão 7) — propor data ao cliente.

---

## 4. Faturação — o que mostrar

1. **Fluxo:** pedido de venda → **Criar fatura** → rever o rascunho → **Confirmar** → **Enviar** → **Pagar**.
2. **Irreversibilidade:** uma fatura confirmada não se edita nem se apaga; corrige-se com **Nota de crédito**.
3. **Numeração:** as faturas saem como INV/2026/xxxxx. A INV/2026/00001 foi usada na demonstração de 02/10 e está cancelada.

> ⚠️ **Regra para os exercícios:** nenhuma fatura de exercício é confirmada — fica em rascunho e é eliminada no fim. Para mostrar o botão **Confirmar**, usar só uma fatura real que tenha de ser emitida nesse dia.

---

## 5. Exercício principal (com dados reais, ~10 min por tema)

1. Abrir a oportunidade de um cliente real e criar o orçamento com secções.
2. Confirmar o orçamento de teste e preparar a fatura (**em rascunho**).
3. Num projeto real (ex.: «Adélia Reis - Acessório Doseador»), mover uma tarefa de fase e lançar 0,5 h.
4. Criar um pedido de compra para um fornecedor importado e registar a receção.
5. No fim: cancelar o orçamento e a compra de teste e eliminar os rascunhos.

---

## 6. O que fica fora e o que falta decidir

- **Fora desta formação:** PLM (sessão à parte), contabilidade (fecho, IVA), inventário avançado, cervejaria e website.
- `PONTO POR VALIDAR` **Local:** presencial nas instalações do cliente (Penafiel) ou por videochamada?
- `PONTO POR VALIDAR` **Participantes:** quem vai — Ricardo Guimarães, Cristina Moreira, José Correia, Andreia Rocha, Marta Guimarães — e o que cada um faz.
- `PONTO POR VALIDAR` **Vídeos de onboarding** (tarefa 6789): gravar a sessão?

---

## 7. Próximos passos

| # | Ação | Responsável | Data |
|---|---|---|---|
| 1 | Duplicar a base e comunicar o endereço novo | Lara Cunha | até 08/10/2026 |
| 2 | Confirmar local e participantes com o cliente | Lara Cunha | até 09/10/2026 |
| 3 | Confirmar que todos entram na base duplicada | Lara Cunha | 14/10/2026 |
| 4 | Dar a formação | Lara Cunha | 16/10/2026, 15:00 |
| 5 | Propor data para a sessão de PLM | Lara Cunha | 16/10/2026 |

---

## 8. Referências

- `PG_CONTEXT.md` do projeto (decisões de 23/09, 29/09 e 02/10)
- Template `TPL_IMPORTACAO_INICIAL_CONTACTOS_PRODUTOS.md`, §6
- Tutoriais no Conhecimento do cliente (artigos 47–54) e guias (39–46)
- Documentação oficial: https://www.odoo.com/documentation/19.0/
