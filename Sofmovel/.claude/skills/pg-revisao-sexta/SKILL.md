---
name: pg-revisao-sexta
description: Conduz a revisão de sexta-feira de projetos Odoo da Parâmetro Global, ponto a ponto. Usar à sexta-feira, ou quando pedirem a revisão semanal, a limpeza do quadro de tarefas, a revisão dos meus projetos, o ponto de situação do quadro ou a carga da semana. Gera a ficha a partir do Odoo (só leitura) e guia a pessoa pela Parte A (o meu quadro) e pela Parte B (os meus projetos).
---

# PG Revisão de sexta-feira

Todas as sextas, cada pessoa pára e gere os seus projetos (decisão da direção, 2026-10-10). Este
procedimento faz o agente preparar a ficha e percorrê-la com a pessoa, um ponto de cada vez.
O manual completo está em [references/manual-sexta.md](references/manual-sexta.md): lê-o antes
de conduzir a sessão.

## Quando correr

- A pessoa pede a revisão de sexta, a limpeza do quadro ou «os meus projetos».
- É sexta-feira (data local) e a sessão abriu num projeto: depois do ritual do `AGENTS.md`,
  **lembra uma vez** que é dia de revisão e oferece correr esta skill. Não insistir se disser que não.

## Fluxo

1. Correr o ritual de arranque do `AGENTS.md` (branch Brodoo, framework atualizada, preflight).
   Sem credencial pessoal do Odoo o script falha com o comando a correr
   (`pg_init_odoo_credentials.ps1`); resolver isso primeiro.
2. Gerar a ficha. Dentro de um repositório de projeto, passar o `project_key` (está em
   `.pg/project/project.json` ou `.pg/projects/<key>/`), para a Parte B focar esse projeto:

```powershell
py .pg_framework\scripts\pg_revisao_sexta.py --projeto-key <project_key>
```

   Outras opções: `--parte A|B|ambas`, `--login <login>` (rever outra pessoa), `--max-tarefas N`,
   `--quadro-na-cor` (só depois das duas primeiras sextas), `--stdout`, `--json`.
   A ficha é gravada **fora do repositório** (`%USERPROFILE%\.pg\revisao\`), porque traz nomes de
   clientes. Ler o ficheiro indicado no fim. Nunca a copiar para um repositório.
3. **Parte A, o meu quadro (45 min).** Por esta ordem, e só avançar quando a pessoa confirmar:
   1. Horas da semana: dias sem horas, linhas sem tarefa, excesso por cliente e dia (máximo
      7 h 30 por cliente e dia, `TPL_TIMESHEET_INSTRUCOES`).
   2. Tarefas em sprint, da menos editada para a mais recente, **em blocos de 10**. Por cada uma,
      as sete perguntas do manual e a ação sugerida da ficha. Pedir uma decisão por tarefa.
   3. Tarefas sem dono que dizem respeito à pessoa.
   4. Contar depois: voltar a correr o script e comparar com a contagem «antes».
4. **Parte B, os meus projetos (45 a 60 min).** Só para quem é gestor, e só depois da Parte A.
   Por tipo (A item a item, B só se amarelo ou vermelho, C em lista, Parado numa decisão: retomar,
   esperar com motivo ou fechar), validar os dez pontos do manual. Para cada ponto fora do verde,
   escrever **uma linha de decisão**: `[Dono] Ação: descrição, até dia e hora`. Nenhuma linha sai
   sem dono e sem hora.
5. **Registar.** Propor o texto da nota por projeto, mostrá-lo e só depois publicar como nota
   interna:

```powershell
py .pg_framework\scripts\pg_odoo_post_chatter.py --model project.project --id <id> --ficheiro <nota>.md --nota-interna --dry-run
```

   Sem `--dry-run` só depois de a pessoa aprovar o texto.
6. **Fecho.** Três linhas de síntese (quadro antes e depois; projetos por cor; o que precisa da
   direção) e o convite para as enviar ao responsável de equipa.

## O que o agente nunca faz

- **Escrever no Odoo sem confirmação explícita daquela lista concreta.** A ficha só lê. Para
  alterar tarefas (horas, prazo, responsável) usar `pg_odoo_query.ps1` com `-Method write`, uma
  tarefa de cada vez, depois de a pessoa dizer sim, e voltar a ler a seguir. Mudar etapas
  (fechar, devolver ao Backlog) só depois de ler as etapas desse projeto: cada projeto tem as suas.
- **Decidir por ela.** O agente propõe a ação da ficha; a decisão é da pessoa. Uma tarefa parada
  pode ser trabalho a sério que ninguém registou.
- Incluir projetos que não têm a etiqueta **Odoo** (PHC, Primavera, internos).
- Criar configuração, campos ou vistas em Odoo Studio (proibido).
- Escrever «validado» sobre o que só foi entregue: validar é o cliente dizer que é aquilo que quer.
- Copiar a ficha, nomes de clientes ou horas para um repositório de projeto ou de cliente.

## Leitura certa dos números

- As horas lançadas são **horas de cliente** e não têm teto diário: com agentes de IA uma pessoa
  trabalha em vários projetos ao mesmo tempo. O tempo de pessoa é 7 h 30 por dia. Nunca
  calcular carga como «horas ÷ 37,5 h».
- A ficha vê só projetos Odoo. Uma pessoa pode ter outro trabalho (PHC, Primavera, suporte,
  internos): perguntar antes de concluir que está livre.
- O prazo do projeto é provisório (só olha para a data de fim, sem baseline). Declarar isso.
- Os limiares (semáforos, tipos A/B/C) são valores iniciais da direção, a apertar ao fim de 4 a 8
  semanas. Estão fixados em `scripts/tests/test_pg_revisao_sexta.py`; mudar um obriga a mudar o manual.
- Registo de consumo de tokens: esta consulta é `read_mode: api`.
