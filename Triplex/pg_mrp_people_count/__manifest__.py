# -*- coding: utf-8 -*-
{
    "name": "PG MRP People Count",
    "version": "17.0.1.0.0",
    "summary": "Número de pessoas por registo de tempo de fabrico, para apurar horas-pessoa",
    "description": """
PG MRP People Count
===================

Objetivo de negócio
-------------------
O tempo registado no chão de fábrica é tempo de relógio: se a Espuma contar 3 horas, ficam
registadas 3 horas — quer tenha estado lá uma pessoa, quer tenham estado três. A Triplex
precisa de saber **quantas pessoas** produziram aquele tempo, para os números se aproximarem
do custo real da peça.

Este módulo acrescenta essa contagem ao registo de tempo e apura as horas-pessoa.

Tarefa: T4 do documento `docs/PRODUCAO_TAREFAS_2026-07-27.md` (Odoo 6630).

Porque não se usa a funcionalidade nativa de vários operadores
-------------------------------------------------------------
O Odoo suporta nativamente vários operadores por operação, cada um com o seu tempo, mas isso
exige um registo de empregado por pessoa. Na Triplex os empregados registados são os
**responsáveis de cada centro de trabalho** — `FACTO OBSERVADO`: os empregados com PIN são
Corte e Costura, Espuma, Estofo, Embalagem, Armazém e Receção de Material, um por centro. O
cliente não quer criar um empregado por operador, e confirmou a 28/07/2026 que o que
pretende é indicar **a quantas pessoas corresponde o tempo**, mantendo o registo natural de
iniciar e parar.

Como funciona
-------------
- `mrp.workcenter.productivity.pg_people_count`: número de pessoas daquele registo de tempo.
  A contagem fica no **registo**, não na operação, porque o mesmo centro pode ter 2 pessoas
  numa sessão e 4 na seguinte — só com esta granularidade as horas-pessoa saem certas.
- `pg_person_hours`: duração × número de pessoas, no registo e somado na operação.
- `mrp.workorder.pg_people_count`: quantas pessoas estão na operação. É este o valor que o
  diálogo grava e que serve de pré-preenchimento.
- `mrp.workorder._prepare_timeline_vals`: copia esse número para o registo de tempo no
  momento em que ele arranca. É o ponto único por onde passam os registos criados pelo chão
  de fábrica — o `button_start` do Enterprise chama `start_employee`, que chama este método
  para montar os valores e só depois cria o registo.
- `pg_people_count_needed`: diz ao chão de fábrica se tem de perguntar, o que só acontece
  quando a operação ainda não tem nenhum registo de tempo.
- Diálogo no chão de fábrica: pergunta o número à primeira contagem de cada operação, com
  botões grandes de 1 a 8, um toque a escolher e confirmar, e o valor em vigor destacado.
- Botão "N pessoas" no cartão: permite alterar o número a qualquer momento. Ver a secção
  seguinte, porque "alterar" quer dizer duas coisas diferentes.

Alterar o número a meio: lapso ou alteração real
-----------------------------------------------
O pedido "quero mudar o número a meio" esconde duas situações que não se resolvem da mesma
maneira:

- **lapso** — indicou-se 4 mas eram 3 desde o início. O tempo decorrido pertence a 3 pessoas,
  logo corrige-se o próprio registo em curso;
- **alteração real** — eram 4 e alguém saiu. O tempo decorrido pertence efectivamente a 4
  pessoas e só a partir de agora são 3. Reescrever o registo falsificaria o passado; o
  correcto é fechar o registo em curso e abrir outro com o novo número.

O `pg_set_people_count` distingue-os **pelo tempo decorrido, sem perguntar nada ao
operador**: até 2 minutos assume lapso, acima disso assume alteração real. Um erro de
digitação é notado em segundos; alguém sair da equipa leva mais do que isso. A alternativa
era pôr o operador a escolher entre "eram sempre N" e "passam a ser N", o que num tablet, com
este público, troca um problema pequeno por outro maior.

Correcções retroactivas descobertas muito depois fazem-se no back office, pelo gestor de
fabrico. Reescrever o passado não deve ser uma acção de chão de fábrica.

Porque o número vai na operação e não no contexto da chamada
-----------------------------------------------------------
O `startWorking` do Chão de Fábrica constrói o contexto de `button_start` internamente, com
valores fixos. Acrescentar-lhe uma chave obrigaria a reimplementar esse método — código do
Enterprise, longo e que muda entre versões. Gravar o número na operação antes de arrancar
evita isso, e dá de graça a alteração a meio: escreve-se o campo e os registos de tempo
seguintes seguem-no, sem tocar nos anteriores. O contexto continua a ser aceite com
precedência, por ser útil em chamadas por API e em testes.

Regra de recolha decidida com o cliente
---------------------------------------
Obrigatório **na primeira vez** que se inicia a contagem numa operação, com o valor
pré-preenchido a **1**. Assim nunca há registos sem contagem, e nas contagens seguintes o
operador não repete o que já disse — o valor anterior é reutilizado.

**Alterável até a operação ser marcada como concluída.** Depois disso o operador deixa de
poder mexer, senão o número deixaria de corresponder ao que foi entregue. O gestor de fabrico
não é travado: uma correcção descoberta mais tarde continua a ser possível no back office,
que é onde os erros de registo se corrigem — travar todos criaria um problema de suporte sem
resolver nenhum.

É por operação, logo **por centro de trabalho**: cada registo de tempo pertence a uma
operação, e cada operação a um centro. Duas pessoas no Corte e quatro na Espuma, na mesma
peça, são contagens independentes, e a pergunta é feita uma vez em cada centro.

Passo a passo de utilização
---------------------------
1. Instalar o módulo.
2. No back office, abrir uma ordem de trabalho e o separador "Time Tracking": cada registo
   de tempo passa a mostrar o número de pessoas e as horas-pessoa.
3. Corrigir ali qualquer registo em que a contagem esteja errada.

FAQ / Resolução de problemas
----------------------------
- P: Os registos antigos aparecem todos com 1 pessoa. Foi medido?
  R: Não. Ao criar a coluna, o Odoo aplica o valor por omissão aos registos existentes. Para
     o histórico isso significa que as horas-pessoa igualam as horas de relógio, que é
     exactamente o que se sabia antes deste módulo. **Não é uma medição** — é a ausência
     dela, e não deve ser lida como tal em relatórios sobre períodos anteriores.
- P: O tempo registado muda com o número de pessoas?
  R: Não. A duração continua a ser tempo de relógio; a contagem é um segundo dado, e as
     horas-pessoa são o produto dos dois.

Pontos de atenção
-----------------
- **Falta a passagem para o painel de planeamento da oficina**, critério de aceitação da T4.
  Fica no módulo do planeamento, que é o consumidor destes dados, e depende deste.
- O diálogo **precisa de validação visual em tablet**, como o restante trabalho de
  acessibilidade — os 88 px dos botões e as quatro colunas foram escolhidos por cálculo, não
  vistos no ecrã do cliente.
- Fechar o diálogo sem escolher (Cancelar, Esc, clicar fora) **cancela o arranque** da
  contagem, em vez de arrancar com um número que ninguém confirmou. É o que torna a recolha
  efectivamente obrigatória.
- Registos criados fora do chão de fábrica — back office, importações — seguem o campo da
  operação, cujo valor por omissão é 1.
""",
    "category": "Manufacturing",
    "author": "Parametro Global",
    "license": "LGPL-3",
    # `mrp_workorder` é a app Chão de Fábrica, onde vive o diálogo que faz a pergunta.
    "depends": ["mrp", "mrp_workorder"],
    "data": [
        "views/mrp_workorder_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_people_count/static/src/js/people_count_dialog.js",
            "pg_mrp_people_count/static/src/xml/people_count_dialog.xml",
            "pg_mrp_people_count/static/src/xml/mrp_display_record.xml",
            "pg_mrp_people_count/static/src/xml/mrp_workorder_line.xml",
            "pg_mrp_people_count/static/src/js/mrp_display_patches.js",
            "pg_mrp_people_count/static/src/js/mrp_workorder_line_patch.js",
            "pg_mrp_people_count/static/src/scss/people_count_dialog.scss",
        ],
    },
    "installable": True,
    "application": False,
}
