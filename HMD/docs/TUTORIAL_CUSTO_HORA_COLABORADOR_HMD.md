# Tutorial — Definir o custo/hora por colaborador (HMD)

> Como preencher o **Custo por Hora** de cada colaborador no Odoo 18. Serve para
> a **análise de custo pré-venda** (saber quanto custa o tempo de quem faz
> orçamentos/estudos). **Não** exige registo de horas detalhado por tarefa.
> Serve também de guião para o vídeo curto HMD-specific.

## Para que serve

O **custo/hora** é o valor de referência do tempo de um colaborador. O Odoo usa-o
para calcular o **custo do esforço** (ex.: horas de análise pré-venda), sem ser
preciso lançar timesheets detalhados. É um campo simples a preencher uma vez (e a
atualizar quando o custo mudar).

---

## Passo 1 — Abrir o colaborador

Vai a **Funcionários** (*Employees*) e abre a ficha do colaborador.

---

## Passo 2 — Preencher o Custo por Hora

1. No formulário, vai ao separador **Definições de RH** (*HR Settings*).
2. No grupo de definições, preenche o campo **Custo por Hora** (*Hourly Cost*)
   com o valor (na moeda da empresa).
3. **Guardar**.

> Basta preencher para os colaboradores que fazem **análise pré-venda** — não é
> obrigatório para todos.

---

## Passo 3 — Manutenção

- **Atualiza** o valor quando o custo do colaborador mudar.
- Mantém uma **regra interna** de como calculam o custo/hora (ex.: custo anual ÷
  horas anuais), para ser consistente entre colaboradores.

---

## Boas práticas

- **Foca os relevantes:** preenche primeiro quem faz orçamentos/estudos.
- **Coerência:** usa o mesmo método de cálculo para todos.
- **Sem timesheets obrigatórios:** este campo, por si só, já permite a análise de
  custo; o registo de horas por tarefa é independente e opcional.
- **Tudo standard:** é um campo nativo do Odoo, sem programação.

---

## Resumo em 3 linhas

1. **Funcionários → abrir o colaborador**.
2. Separador **Definições de RH** → campo **Custo por Hora** → guardar.
3. Preencher para quem faz **análise pré-venda**; atualizar quando mudar.
