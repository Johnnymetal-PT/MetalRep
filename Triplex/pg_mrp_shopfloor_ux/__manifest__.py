# -*- coding: utf-8 -*-
{
    "name": "PG MRP Shop Floor UX",
    "version": "17.0.1.0.0",
    "summary": "Chão de Fábrica legível e utilizável em tablet por operadores de oficina",
    "description": """
PG MRP Shop Floor UX
====================

Objetivo de negócio
-------------------
O Chão de Fábrica é usado na oficina, em tablet, de pé, por operadores com pouca prática
de tecnologia e alguns com dificuldade de visão. Com as medidas por omissão do backend do
Odoo — botões pequenos, comandos representados apenas por ícones, letra de escritório — a
app é desconfortável e leva a toques errados.

Este módulo ajusta tamanhos, contraste e alvos de toque. Não altera comportamento nenhum.

Tarefa: T15 do documento `docs/PRODUCAO_TAREFAS_2026-07-27.md`.

O problema concreto que originou o módulo
-----------------------------------------
O acesso aos operadores era um botão **só com ícone** (`oi-panel-right`), pequeno e sem
etiqueta, no canto superior do ecrã (`enterprise/mrp_workorder/static/src/mrp_display/mrp_display.xml:10`).
Para chegar ao "Add Operator" era preciso descobrir esse símbolo primeiro. Segundo o
cliente, a 28/07/2026: *"está escondido num popup que se clica num símbolo estranho e muito
pequeno em tablet, para pessoas de mais idade sem grande toque com tecnologia é muito mau"*.

Três regras seguidas
--------------------
1. Nenhum comando principal representado só por um ícone — texto sempre.
2. Alvo de toque nunca abaixo de 48 px; 56 px nas acções principais.
3. Letra e contraste acima do que o backend usa por omissão.

O que muda
----------
- **Zona de iniciar/parar tempo**: é a alteração mais importante. No Enterprise **não existe
  botão de cronómetro** — o comando é o cabeçalho inteiro do cartão
  (`t-on-click="onClickHeader"` em `mrp_display_record.xml:8`, que chama `startWorking`), e
  o único sinal disso é um `cursor-pointer`, que num tablet não existe. Passa a ter 64 px,
  barra colorida à esquerda, retorno visual ao toque e um ícone de iniciar/parar. O tempo a
  decorrer passa a 1,6 rem com dígitos de largura fixa, para não "saltar" a contar.
- **Centro de trabalho selecionado**: os separadores já vinham com cor própria do Enterprise
  (`o_workcenter_item_color_{{id % 11}}`, `control_panel.xml:14`), mas todos com o mesmo
  peso visual. O activo passa a ter moldura, sublinhado grosso e letra maior.
- **Botão de operadores**: passa a ter a etiqueta "Operadores", 56 px de altura, contorno
  visível, e fundo cheio quando o painel está aberto (para se ler como interruptor).
- **Painel de operadores**: linhas de 72 px, avatar de 48 px, e o "Add Operator" com 64 px
  e letra maior — é o comando mais usado do painel.
- **Cartões**: título a 1,3 rem, cabeçalho a 1,1 rem, botões com 48 px mínimos (o
  Enterprise usava `btn-sm` no "Registrar produção"), acções principais a 56 px, e mais
  espaço entre cartões para evitar toques no cartão vizinho.
- **Teclado do PIN**: teclas de 72 px e o valor introduzido a 1,8 rem.

Como funciona
-------------
Só CSS, num único ficheiro (`static/src/scss/shopfloor_ux.scss`). **Nenhum template do
Enterprise é herdado**, de propósito: o `mrp_workorder` é código proprietário e cada patch
a templates dele é dívida a pagar no próximo upgrade.

Passo a passo de utilização
---------------------------
1. Instalar o módulo.
2. Abrir o Chão de Fábrica num tablet (ou reduzir a janela do browser à largura de um).
3. O botão "Operadores" está visível no topo, com texto.

FAQ / Resolução de problemas
----------------------------
- P: Instalei e o ecrã está igual.
  R: Limpar a cache do browser (Ctrl+F5). Os assets são compilados e ficam em cache.
- P: O ecrã voltou ao aspecto antigo depois de um upgrade do Odoo.
  R: Os selectores são internos do `mrp_workorder` e podem mudar de versão. É o ficheiro
     SCSS que precisa de ser reajustado — está comentado para isso.
- P: Quero afinar os tamanhos.
  R: As três medidas estão em variáveis no topo do SCSS
     (`$pg-sf-toque-minimo`, `$pg-sf-toque-principal`, `$pg-sf-tecla-pin`).

Traduções pt-PT (passo de deploy separado)
------------------------------------------
O `enterprise/mrp_workorder/i18n/pt.po` tem **41 termos com `msgstr ""`**, vários bem
visíveis no Chão de Fábrica: "Add Operator", "All MO", "This Station", "No workorders",
"Connected Employees", "+ New Operator". As traduções estão escritas em
`i18n_extra_mrp_workorder/pt.po`, **dentro deste módulo mas fora do que o Odoo carrega**.

Têm de ser copiadas para `<addons>/mrp_workorder/i18n_extra/pt.po`. As traduções de código
são carregadas por módulo — `get_po_paths` (`odoo/tools/translate.py:1648-1666`) procura em
`<módulo>/i18n/` e `<módulo>/i18n_extra/`, sempre dentro do módulo a que o termo pertence.
Um PO aqui só traduziria termos nossos, por isso não há como daqui traduzir o
`mrp_workorder`. O `i18n_extra` é o mecanismo suportado para acrescentar traduções sem
alterar o ficheiro original.

**Um upgrade do Odoo que substitua a pasta do `mrp_workorder` apaga esse ficheiro** — é a
mesma armadilha das correções que vivem só na base de dados. O ficheiro é versionado aqui
como cópia de referência, e a reposição é um passo de deploy a repetir depois de upgrades.

Pontos de atenção
-----------------
- Há **um** patch de JavaScript, e apenas um: o getter `cssClass` do cartão, para lhe
  acrescentar a classe da cor do centro de trabalho (`js/mrp_display_record_workcenter_class.js`).
  Não foi possível por CSS — a cor vive nos separadores do topo e o cartão não tem o centro
  de trabalho no DOM nem relação de ascendência com o separador activo. Escolheu-se estender
  um getter em vez de herdar o template: se o patch falhar, o cartão perde a cor e mais nada;
  um `xpath` que deixe de casar rebenta a compilação dos assets e leva o backend com ele.
- O estado "a contar" usa a classe `o_active`, que o Enterprise põe no cartão quando **o
  operador da sessão** está entre os que trabalham naquela ordem
  (`mrp_display_record.js:396-398`). Se outra pessoa estiver a contar tempo na mesma ordem,
  o cartão não fica verde para mim — é o comportamento correcto para a vista de cada
  operador, mas convém saber.
- A etiqueta "Operadores" vem de `content` em CSS e **não é traduzível**. Troca deliberada:
  a alternativa era herdar o template do Enterprise para acrescentar um `<span>`, e não
  compensa o risco por uma palavra numa base inteiramente em português. Se o módulo for
  reutilizado noutro cliente com outro idioma, é o primeiro ponto a mudar.
- A regra do teclado do PIN usa `.popup .popup-numpad`, que fica fora de `.o_mrp_display`
  porque os diálogos do Odoo montam num portal no fim do body. O nome é genérico e o Ponto
  de Venda usa nomes parecidos; nesta base o `point_of_sale` está **desinstalado**
  (verificado a 28/07/2026). Se vier a ser instalado, confirmar que não há colisão.
- Não mexe em comportamento: nada de novos campos, ações ou permissões. Desinstalar
  devolve o aspecto original.
""",
    "category": "Manufacturing",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "depends": ["mrp_workorder"],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_ux/static/src/js/mrp_display_record_workcenter_class.js",
            "pg_mrp_shopfloor_ux/static/src/scss/shopfloor_ux.scss",
        ],
    },
    "installable": True,
    "application": False,
}
