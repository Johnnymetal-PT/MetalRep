# Tutorial — Modelos de Orçamento no Odoo (HMD)

> Guia rápido para o comercial criar e usar **Modelos de Orçamento**
> (*Quotation Templates*) no Odoo 18. Serve para acelerar orçamentos
> repetitivos, deixando as linhas-base já preenchidas.

---

## 1. O que é (e o que NÃO é)

Um **Modelo de Orçamento** é um orçamento-base reutilizável: ao escolher o
modelo, o orçamento abre já com as linhas, produtos e condições típicas, sem ter
de as montar de raiz de cada vez.

**Importante — o modelo serve só para a estrutura, não para os preços.**
Na HMD o preço é sempre calculado pelas calculadoras existentes:

- **Calculadora de preço** (botão na linha do orçamento): custo + margem;
- **Calculadora de transporte** (cubicagem): custo de transporte na linha.

Por isso, **não vale a pena fixar preços no modelo** — eles serão recalculados
pelas calculadoras na altura de orçamentar, exatamente como já fazes hoje. O
modelo só te poupa o trabalho de voltar a montar as mesmas linhas.

| Usa o modelo para… | Não uses o modelo para… |
|---|---|
| Pré-montar as linhas de produtos recorrentes (ex.: caixas de amostra) | Definir preços (isso é com as calculadoras) |
| Guardar condições, validade e termos habituais | Substituir a calculadora de preço/transporte |
| Listar produtos opcionais a propor ao cliente | — |

---

## 2. Ativar a funcionalidade (uma única vez)

1. Vai a **Vendas → Configuração → Definições**.
2. Na secção **Orçamentos e Encomendas**, ativa **"Modelos de Orçamento"**
   (*Quotation Templates*).
3. **Guardar**.

> A partir daqui aparece o menu **Vendas → Configuração → Modelos de Orçamento**.
> *(As designações podem variar ligeiramente conforme a tradução.)*

---

## 3. Criar um modelo

1. Vai a **Vendas → Configuração → Modelos de Orçamento** e carrega em **Novo**.
2. Preenche:
   - **Nome do modelo** — ex.: `Caixa de amostra` ou `Sofá-base (linha frequente)`.
   - **Validade (dias)** — quantos dias o orçamento fica válido (campo *number of days*).
   - **Confirmação online** — opcional: exigir **assinatura** e/ou **pagamento**
     (adiantamento) para o cliente confirmar online.
   - **Termos e condições** — texto que aparece no fundo do orçamento.

---

## 4. Adicionar as linhas do modelo

No separador **Linhas** do modelo, carrega em **Adicionar um produto** e, para
cada linha:

- **Produto** — escolhe o produto recorrente.
- **Descrição** — ajusta o texto se necessário.
- **Quantidade** — a quantidade-base típica (podes alterá-la depois no orçamento).
- **Preço** — deixa o que vier por defeito; **vai ser recalculado pela
  calculadora** ao orçamentar.

Podes também estruturar o modelo:

- **Adicionar uma secção** — títulos para agrupar linhas (ex.: "Estrutura",
  "Tecidos", "Acessórios").
- **Adicionar uma nota** — texto livre entre linhas.

### Produtos opcionais (sugestões ao cliente)
No separador **Produtos Opcionais**, adiciona produtos que o comercial pode
propor como extras (não entram no total até serem adicionados).

Guarda o modelo.

---

## 5. Usar o modelo num orçamento (fluxo do dia-a-dia)

1. Cria um orçamento novo (**Vendas → Orçamentos → Novo**) e escolhe o **cliente**.
2. No campo **Modelo de Orçamento**, escolhe o modelo criado.
   → As linhas-base são preenchidas automaticamente.
3. Ajusta quantidades / produtos conforme o pedido real.
4. **Calcula os preços como habitualmente:**
   - em cada linha, abre a **calculadora de preço** e carrega em **Aplicar**;
   - aplica a **calculadora de transporte** quando aplicável.
5. Revê e envia o orçamento.

> **Regra de ouro:** o modelo dá-te o ponto de partida; **o preço final vem
> sempre das calculadoras**. Nunca confies no preço que vem do modelo.

---

## 6. Manutenção e boas práticas

- **Cria poucos modelos e bem definidos** — um por tipo de orçamento recorrente.
  É melhor 5 modelos úteis do que 30 confusos.
- **Mantém os modelos atualizados** — se um produto deixar de se usar, edita ou
  arquiva o modelo.
- **Arquivar em vez de apagar** — usa o botão de arquivar para manter o histórico.
- **Não metas margens nem preços calculados nos modelos** — ficam desatualizados
  e seriam ignorados pela calculadora de qualquer forma.

---

## 7. Resumo em 3 linhas

1. **Modelo = estrutura** (linhas e condições recorrentes), criado uma vez.
2. **Usar = escolher o modelo** no orçamento e ajustar quantidades.
3. **Preço = sempre pelas calculadoras** (preço + transporte), como já fazes.
