Este guia mostra como criar um painel vosso, mantê-lo ao longo do tempo e decidir quem o vê. Para
saber o que já existe e onde ler cada informação, ver
[PAINÉIS E RELATÓRIOS — POR ONDE COMEÇAR]({{kb90}}).

## 1. Quem pode criar e editar painéis

Criar e editar painéis exige o acesso **Painel / Admin**. Na HMD têm-no a **Nina, a Mónica, a Graça,
o Natalino e o Sérgio**. Os restantes utilizadores veem os painéis, mas não os alteram.

Cada painel tem também uma lista de **grupos que o veem**. Por exemplo, o painel standard *Vendas*
só aparece a quem é **Vendas / Administrador**.

## 2. A regra mais importante: não editar os painéis standard — duplicar

Os 18 painéis que vêm com o Odoo (Vendas, Artigo, Faturação, Manufatura…) são **repostos sempre que
o Odoo é atualizado**. Tudo o que for alterado num painel standard perde-se na atualização seguinte,
sem aviso.

**Por isso:**

1. **Painéis › Configuração › Painéis**.
2. Selecionar o painel standard e escolher **Duplicar**.
3. Dar-lhe um nome vosso (por exemplo, `HMD — Vendas`) e editar a cópia.

> ⚠️ **A fazer já:** os painéis standard **Vendas** e **Artigo** foram alterados a 01/10/2026. Para
> não perder essas alterações, duplicá-los agora e passar a usar as cópias.

> 📷 *Ecrã: Painéis › Configuração › Painéis, com a lista dos painéis e o botão Editar (lápis).*

## 3. Criar um painel a partir de uma análise (o caminho mais simples)

É assim que se transforma uma pergunta do dia a dia num painel.

1. Abrir a análise que responde à pergunta. Por exemplo, compras por fornecedor:
   **Compras › A Reportar › Compras**.
2. **Filtrar primeiro pelo estado.** Sem isso, os números misturam rascunhos com encomendas
   confirmadas (ver o ponto 7).
3. Agrupar como fizer sentido: por fornecedor, por mês, por data prevista.
4. Na vista **Pivô** ou **Gráfico**, clicar em **Inserir em planilha**. Numa lista, a opção é
   **Inserir lista na planilha**, no menu da engrenagem ⚙.
5. Escolher **Planilha em branco**. A folha fica guardada em **Documentos**.
6. Na folha, arrumar a tabela e o gráfico. Os números são **dados vivos** do Odoo, e atualizam-se
   sozinhos.
7. Quando estiver pronto, abrir o menu **Ficheiro › Adicionar ao painel**, dar-lhe um nome e
   escolher a secção (Vendas, Logística, Finanças…).

O painel passa a aparecer em **Painéis**, na secção escolhida.

> 📷 *Ecrã: vista Pivô de Compras com o botão «Inserir em planilha».*
> 📷 *Ecrã: menu Ficheiro › Adicionar ao painel, na folha de cálculo.*

## 4. Acrescentar uma análise a um painel que já existe

Repetir os passos 1 a 4 do ponto anterior e, em vez de uma folha em branco, escolher a folha ou o
painel onde a análise deve entrar. Cada análise ocupa uma zona da folha: arrumar para não tapar o
que lá estava.

## 5. Editar e manter um painel

- **Editar:** **Painéis › Configuração › Painéis** → no painel, o botão **Editar** (lápis). As
  alterações gravam-se automaticamente.
- **Quem vê:** na mesma lista, a coluna dos **grupos**. Um painel novo é visto por todos os
  utilizadores internos; para o limitar, escolher os grupos.
- **Publicar ou esconder:** a caixa **Publicado** mostra ou esconde o painel no menu, sem o apagar.
  É a forma de retirar um painel que já não se usa.
- **Nomes:** começar pelos vossos com `HMD —`, para se distinguirem dos standard.

**Revisão periódica**, por exemplo uma vez por trimestre:

- [ ] Os painéis em uso ainda respondem a uma pergunta que alguém faz?
- [ ] Os filtros de estado estão certos (ponto 7)?
- [ ] Há painéis vossos que ninguém abre? Desmarcar **Publicado**.
- [ ] Depois de uma atualização do Odoo, as cópias dos standard continuam iguais?

## 6. Sugestões de painéis para a HMD

Partindo das necessidades que a Nina enviou a 28/07/2026:

| Pergunta | Onde começar | Agrupar por |
|---|---|---|
| Qualidade por fornecedor e data | **Qualidade › A Reportar › Verificações de Qualidade** | fornecedor, mês |
| Compras em produção por fornecedor e data de entrega | **Compras › A Reportar › Compras**, só encomendas confirmadas | fornecedor, data prevista |
| Encomendas com valores pagos e pendentes | **Vendas › Encomendas › Encomendas** | **Estado de Pagamento** (Não pago / Adiantamento recebido / Pago) |
| Faturação mensal face ao objetivo | **Contabilidade › A Reportar › Gestão › Análise de Fatura** | mês |
| Tesouraria a 30/60/90 dias | **Contabilidade › A Reportar › Relatórios de Parceiros › Recebimentos Vencidos** | — (relatório próprio) |

## 7. Armadilhas que dão números errados

- **Não filtrar pelo estado.** Há muitos orçamentos e pedidos de compra em rascunho: sem filtro,
  os totais de vendas e compras ficam várias vezes acima da realidade.
- **Pagamento das encomendas:** usar o campo **Estado de Pagamento** da HMD, que está certo, e não o
  estado de adiantamento do módulo de adiantamentos, que mostra «não pago» em todas.
- **Tesouraria:** enquanto houver linhas de extrato bancário por reconciliar, o cash-flow e os
  vencidos não batem certo com o banco.
- **Acessos:** quem não tem acesso à Contabilidade não vê os painéis de Finanças, mesmo que esteja
  no grupo do painel.

*Guia escrito pela Parâmetro Global a 02/10/2026, com a configuração da vossa base de dados nessa
data. Os ecrãs serão acrescentados; até lá, cada passo indica o caminho exato no menu.*
