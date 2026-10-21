# Sessão 7 — PLM: alterações a produtos e listas de materiais

**Cliente:** JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA · **Projeto:** Implementação Odoo · **Data:** 10/2026 · **Formadora:** Lara Cunha (Parâmetro Global)

> A interface do Odoo está em português do Brasil. Os nomes de menus e botões aparecem **a negrito, exatamente como no ecrã**.

## O que se vai ver e porquê

Uma peça feita à medida — uma mesa, um roupeiro, um móvel de apoio — tem uma **lista de materiais**: os componentes e as quantidades necessárias para a produzir. Quando o desenho muda (outro tampo, outra madeira, outras medidas), a lista tem de mudar também.

A aplicação **PLM - Ciclo de Vida do Produto** serve para fazer essas mudanças **de forma controlada**: cada alteração é uma **OAE** (Ordem de Alteração de Engenharia), que passa por fases, pode ser aprovada antes de entrar em vigor e deixa histórico de versões. Assim sabe-se sempre qual é a versão em vigor, o que mudou e quem aprovou.

## Antes → depois

| Hoje | Com o PLM |
|---|---|
| A alteração ao desenho fica num email ou numa nota | Cada alteração é uma OAE com responsável, fase e histórico |
| Não se sabe ao certo qual é a versão atual da peça | A lista de materiais tem **Versão** — a anterior fica guardada |
| A alteração entra em produção sem validação | A OAE só se aplica depois de **Validado** |

## Parte A — A lista de materiais (ponto de partida)

Menu: **PLM - Ciclo de Vida do Produto › Dados mestres › Lista de materiais** (o mesmo que **Fabricação › Produtos › Listas de materiais**) → **Novo**.

1. **Produto** — a peça (ex.: «Mesa»).
2. **Quantidade** — normalmente 1.
3. **Tipo de LM**: **Fabricar este produto**.
4. Separador **Componentes** — os materiais e as quantidades (tampo, pés, ferragens, verniz…).

## Parte B — Criar e aplicar uma alteração (OAE)

Menu: **PLM - Ciclo de Vida do Produto › Alterações** → **Novo**.

1. **Referência** — descrever a alteração (ex.: «Mesa — tampo em carvalho em vez de nogueira»).
2. **Tipo**: **Atualizações de LM**.
3. **Aplicar em**:
   - **Lista de materiais** — muda componentes ou quantidades;
   - **Somente o produto** — muda só a ficha do artigo (ex.: desenho técnico, descrição).
4. **Produto** e **Lista de materiais** a alterar.
5. **Responsável** — quem trata da alteração.
6. **Iniciar revisão** — o Odoo cria uma **Nova lista de materiais** (cópia da atual) onde se faz a alteração, sem tocar na que está em vigor.
7. Abrir a nova lista de materiais (botão no topo da OAE) e alterar os componentes.
8. Anexar o desenho ou o render revisto (clipe no histórico da OAE).
9. Avançar nas fases: **Novo → Em andamento → Validado → Efetivo**.
10. **Aplicar alterações** — a nova versão passa a ser a que está em vigor; a anterior fica arquivada, com a versão antiga.

## Parte C — Aprovações

- Na fase certa, quem tem de aprovar usa **Aprovar** ou **Rejeitar** (separador **Aprovações**).
- Neste momento **não há aprovações configuradas**: qualquer utilizador pode avançar a OAE. Se quiserem que alguém aprove sempre (ex.: o Sr. Ricardo antes de entrar em produção), configura-se em **Configuração › Estágios da OAE**.

## Acompanhar

- **Alterações** — todas as OAE, em cartões por fase.
- **Relatórios › OAEs** — quantas alterações, por produto, responsável ou fase.
- Na lista de materiais, o campo **Versão** mostra quantas revisões já teve.

## Exercício

1. Criar uma lista de materiais de teste para uma peça (ex.: «Mesa de teste», com tampo e pés).
2. Criar uma OAE «Mesa de teste — trocar componente», **Aplicar em** = **Lista de materiais**.
3. **Iniciar revisão**, alterar um componente na nova lista e avançar até **Validado**.
4. **Aplicar alterações** e confirmar que a versão da lista de materiais aumentou.

## O que o Odoo passa a dar

- Histórico de todas as versões de cada peça, com o que mudou e quando.
- Alterações validadas antes de chegarem à produção.
- Desenhos e documentos de cada revisão guardados na própria alteração.

## O que fica fora e o que falta decidir

- **(a decidir)** Que peças vão ter lista de materiais (peças de fabrico próprio vs. artigos comprados prontos).
- **(a decidir)** Quem aprova as alterações e em que fase.
- **(a decidir)** Se as ordens de produção (**Fabricação**) vão ser usadas, ou só as listas de materiais e o PLM.
- No fim do exercício, arquivar a lista de materiais e o artigo de teste.

## Próximos passos

1. Escolher 2 ou 3 peças reais e criar as listas de materiais.
2. Decidir quem aprova as alterações; a Parâmetro Global configura as aprovações.
