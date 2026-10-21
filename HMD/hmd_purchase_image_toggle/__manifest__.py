{
    "name": "HMD Purchase Image Toggle",
    "version": "18.0.1.0.0",
    "summary": "Toggle 'Imprimir Imagens' no cabecalho da PO propaga para todas as linhas (campos Studio).",
    "author": "HMD / Parametro Global",
    "license": "LGPL-3",
    "depends": ["purchase"],
    "data": [],
    "description": """
HMD Purchase Image Toggle (HMD)
===============================

a) Objetivo de negocio
----------------------
A PO da HMD tem (via Studio) um campo `x_studio_imprimir_todas_imagens`
no cabecalho que diz se a impressao da PO deve mostrar imagens dos
produtos linha-a-linha, e um campo `x_studio_imprimir_imagem` em cada
linha que controla por linha. Sem este modulo, alterar o flag de
cabecalho NAO mexia nas linhas, tornando o toggle inutil. Este modulo
sincroniza:
  - quando o utilizador liga/desliga o flag de cabecalho (onchange ou
    write), todas as linhas seguem a decisao;
  - se a linha nao tem `x_studio_imagem_de_produto` (anexo),
    `x_studio_imprimir_imagem` fica `False` mesmo que o cabecalho
    diga `True`;
  - constraint na linha: nao se pode marcar `imprimir_imagem` sem
    haver imagem definida.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `purchase` instalado.
- DEPENDENCIA STUDIO: tem de existir em Studio
    - `purchase.order.x_studio_imprimir_todas_imagens` (Boolean);
    - `purchase.order.line.x_studio_imprimir_imagem` (Boolean);
    - `purchase.order.line.x_studio_imagem_de_produto`
      (Binary/Image).
  Se algum nao existir, o modulo da erro de carregamento.

c) Como funciona (tecnico)
--------------------------
1. `purchase.order._onchange_print_all_images` (onchange UI):
   - Quando o utilizador clica no flag de cabecalho na UI, percorre
     todas as linhas e poe `x_studio_imprimir_imagem = True` apenas
     nas linhas que tem imagem. Se desligar, poe tudo a False.

2. `purchase.order.write` (persistencia):
   - Se `x_studio_imprimir_todas_imagens` esta nos vals, capta
     estado antes/depois.
   - Para cada PO em que o valor mudou, atualiza as linhas que
     ainda estavam alinhadas com o estado antigo (nao mexe nas que
     o utilizador modificou manualmente).

3. `purchase.order.line._check_image_flag_requires_attachment`
   (constrain): impede gravar `imprimir_imagem=True` se nao houver
   `imagem_de_produto`. Levanta `ValidationError`.

d) Passo a passo de utilizacao
------------------------------
1. Garantir que os 3 campos Studio existem.
2. Instalar `hmd_purchase_image_toggle`.
3. Compras > Encomendas > criar/abrir uma PO.
4. Configurar imagens nas linhas (`x_studio_imagem_de_produto`).
5. Marcar `x_studio_imprimir_todas_imagens` no cabecalho.
6. Resultado: todas as linhas com imagem ficam com
   `x_studio_imprimir_imagem = True`.
7. Para excluir uma linha especifica, desmarcar manualmente em cada
   linha.

e) Exemplo pratico
------------------
PO P10 com 4 linhas:
  - L1: tem imagem.
  - L2: tem imagem.
  - L3: SEM imagem.
  - L4: tem imagem.

Marcar `imprimir_todas_imagens = True` no cabecalho ->
  L1=True, L2=True, L3=False (sem imagem), L4=True.

Desmarcar -> L1=L2=L3=L4=False.

Tentar marcar L3 manualmente sem ter imagem -> ValidationError.

f) FAQ / Resolucao de problemas
-------------------------------
P: O toggle de cabecalho nao mexe nas linhas. Porque?
R: Verificar que os campos Studio existem com os nomes esperados.
   Se foram renomeados, o modulo nao apanha.

P: ValidationError ao salvar a PO. O que verificar?
R: Alguma linha tem `imprimir_imagem=True` mas
   `imagem_de_produto` vazia. Ou poe-se a imagem ou desmarca-se o
   flag.

P: Editei manualmente uma linha (`imprimir_imagem=False` numa linha
   que tinha imagem). Vou perder essa edicao?
R: Nao - o `write` apenas atualiza linhas cujo flag estava alinhado
   com o estado antigo do cabecalho. Edicoes manuais sao preservadas.

g) Pontos de atencao / avisos
-----------------------------
- DEPENDENCIA STUDIO HARDCODED nos nomes dos campos:
  `x_studio_imprimir_todas_imagens`, `x_studio_imprimir_imagem`,
  `x_studio_imagem_de_produto`. Renomear em Studio quebra o modulo.
- A constrain corre em todas as escritas. Em batch de muitas
  linhas, custo aceitavel (filtragem em Python).
- O write override so atua se `imprimir_todas_imagens` esta no
  `vals`. Mudancas a outros campos sao pass-through.
""",
    "installable": True,
    "application": False,
}
