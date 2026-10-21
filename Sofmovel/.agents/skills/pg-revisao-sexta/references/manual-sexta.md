# Manual de sexta-feira para gestores (referência do agente)

Versão completa e editável: Claude Docs «Manual de sexta-feira para gestores». Esta cópia é a que o
agente lê; se divergirem, a versão da direção prevalece e esta atualiza-se.

## Regras do jogo

- Todas as sextas, **cada pessoa pára e gere os seus projetos**: bloco fixo na agenda, 90 a 105 min.
  As duas primeiras sextas pedem 2 a 3 horas (limpeza do quadro).
- Universo: projetos com a etiqueta **Odoo**.
- Quem não fez a Parte A não entra na Parte B: o semáforo de um projeto com o quadro por atualizar não vale nada.
- **Nenhuma linha sai do bloco sem dono e sem hora.**
- Horas lançadas = trabalho feito para o cliente (sem teto diário). Tempo de pessoa = 7 h 30 por dia.

## Parte A: o meu quadro (45 min)

1. **Fechar o que está feito (5 min).** Tarefas em Sprint Complete ainda abertas.
2. **Lançar as horas da semana (5 min).** Dia a dia, por tarefa, só trabalho para o cliente; máximo 7 h 30 por cliente e dia; nenhuma linha sem tarefa.
3. **Passar as tarefas em sprint (25 min).** Sete perguntas por tarefa:

| # | Pergunta | Se a resposta for não |
| --- | --- | --- |
| 1 | Já está feita? | (se sim) Fechar. |
| 2 | Vai ser feita nas próximas 2 semanas? | Devolver ao Backlog. Sprint Backlog é compromisso. |
| 3 | Tem responsável? | Atribuir a quem a faz, ou devolver ao Backlog. |
| 4 | Tem horas alocadas? | Estimar as horas que faltam, em horas de cliente. |
| 5 | Tem prazo? | Pôr um prazo realista; se não der, perguntar ao cliente ou ao gestor. |
| 6 | Está na etapa certa? | Sprint in Progress só se houve trabalho esta semana; senão, Sprint Backlog. |
| 7 | O prazo já passou? | Replanear com nova data e motivo escrito, ou fechar como não necessária. |

4. **Tarefas sem dono que me dizem respeito (5 min).**
5. **Contar antes e depois (5 min).** Tarefas em sprint com dono, horas e prazo.

## Parte B: os meus projetos (45 a 60 min)

Dez pontos por projeto; por cada ponto fora do verde, uma linha de decisão.

| # | Ponto | Onde ver | Se falhar |
| --- | --- | --- | --- |
| 1 | Tem gestor? | Gestor do projeto | Atribuir hoje. |
| 2 | Tem data de fim? | data de fim | Acordar uma data com o cliente. |
| 3 | Tem horas alocadas? | horas alocadas | Definir a partir do orçamento aprovado. |
| 4 | Quanto das horas já foi consumido? | efetivas ÷ alocadas | Ver semáforos. |
| 5 | Houve horas nas últimas 4 semanas? | timesheet | Marcar «Parado». |
| 6 | Próximo marco e a sua data? | marcos | Confirmar; se em risco, avisar o cliente esta semana. |
| 7 | O que aguardo do cliente? | tarefas bloqueadas | Pedir por escrito, com data limite. |
| 8 | O ponto único de contacto está disponível? | horas por semana acordadas | Sem resposta há mais de uma semana: escalar ao patrocinador. |
| 9 | Há pedidos de alteração pendentes? | mensagens do projeto | Só entram se não derrapam prazo e orçamento, ou se outro requisito sai; senão, depois do go-live. |
| 10 | O estado do projeto está atualizado? | atualização do projeto | Cor e uma frase. |

### Profundidade por tipo

| Tipo | Critério (qualquer um) | O que se valida |
| --- | --- | --- |
| A | 40 h ou mais em 4 semanas; ou 300 h ou mais alocadas; ou go-live em 30 dias; ou cliente estratégico | os dez pontos |
| B | de 10 a 40 h em 4 semanas | pontos 4, 5, 6 e 7; os outros só se amarelo ou vermelho |
| C | menos de 10 h em 4 semanas | pontos 1, 2 e 5, em lista |
| Parado | nenhuma hora em 4 semanas | decisão única: retomar, esperar com motivo ou fechar |

«Go-live em 30 dias» e «cliente estratégico» não estão no Odoo: decide-os o gestor.

### Semáforos (valores iniciais, a apertar ao fim de 4 a 8 semanas)

| Medida | Verde | Amarelo | Vermelho |
| --- | --- | --- | --- |
| Horas consumidas ÷ alocadas | até 80 % | 80 a 110 % | acima de 110 % |
| Prazo (provisório, sem baseline) | sem atraso | atraso até 14 dias | atraso acima de 14 dias |
| Atividade (horas em 4 semanas) | 10 h ou mais | de 1 a 10 h | nenhuma hora |
| Quadro (tarefas em sprint com dono, horas e prazo) | 90 % ou mais | 55 a 90 % | abaixo de 55 % |

A cor do projeto é a pior das medidas. O quadro só entra na cor depois da limpeza das duas primeiras sextas.

## Tarefa parada: o que decidir

Tarefa em sprint sem edição há mais de 30 dias → já está feita? **fechar**. → vai ser feita nas próximas
2 semanas? não: **devolver ao Backlog**. → tem dono, horas e prazo? não: **preencher agora**. → o prazo já
passou? sim: **replanear com nova data e motivo escrito**; não: **manter e registar o ponto da situação**.
Parada há mais de 90 dias: devolver ao Backlog ou fechar como não necessária.

## Como registar

- Uma nota no *chatter* do projeto por sexta-feira, com todas as linhas de decisão, formato
  `[Dono] Ação: descrição, até dia e hora`.
- Atualizar o estado do projeto com a cor e uma frase.
- Uma ação que demora mais de 15 min vira tarefa com dono, horas e prazo.
- Notas por script ou agente: `pg_odoo_post_chatter.py` (converte o markdown; nunca HTML sem `body_is_html=True`).
- Entregue não é validado: só se escreve «validado» quando o cliente o disse.

## As duas primeiras sextas: limpar o quadro (2 a 3 h)

1. Fechar as Sprint Complete abertas (15 min).
2. Tarefas em sprint paradas há mais de 90 dias: Backlog ou fechar (30 min).
3. Tarefas em sprint paradas entre 31 e 90 dias: as sete perguntas (30 min).
4. Tarefas em sprint recentes sem dono, horas ou prazo: preencher (20 min).
5. Horas: lançar o que falta e associar a uma tarefa as linhas sem tarefa (20 min).
6. Projetos: gestor, data de fim e horas alocadas; marcar os «Parados» (30 min).
7. Contar antes e depois e registar na síntese (15 min).

## Fecho e síntese

Três linhas por pessoa: (1) quadro, antes e depois, tarefas em sprint com dono, horas e prazo;
(2) projetos verdes, amarelos, vermelhos e parados; (3) o que preciso da direção, e até quando.

## Pedidos de suporte

Entram no Helpdesk da equipa Odoo ou como tarefa com horas. Se o projeto ainda tem horas alocadas, o
pedido gasta essas horas; se já não tem, é pedido de alteração ou novo orçamento, e avisa-se o cliente
antes de começar.
