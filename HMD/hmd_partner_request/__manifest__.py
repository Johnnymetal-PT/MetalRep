# -*- coding: utf-8 -*-
{
    "name": "HMD Partner Account Request",
    "version": "18.0.1.0.0",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "category": "Sales/CRM",
    "summary": "Aprovacao dos pedidos de conta de parceiro feitos no website.",
    "license": "LGPL-3",
    "description": """
HMD Partner Account Request
===========================

a) Objetivo de negocio
----------------------
O website tem um formulario "Create your customer account" onde um visitante
pede conta de parceiro. Ate agora esses pedidos caiam no CRM misturados com
os contactos normais, e transformar um pedido em parceiro com acesso ao
portal era trabalho manual: criar o contacto, copiar os campos, ir aos
utilizadores do portal, convidar.

Este modulo marca os pedidos e da-lhes um botao de aprovacao.

Origem: reuniao de 04/09/2026, ponto 4. Quem aprova e a Nina Hedderich, e a
HMD pediu expressamente que NAO haja tempo de resposta comprometido.

b) Porque nao um modelo proprio
-------------------------------
Ponderou-se criar um modelo `hmd.partner.request`. Nao se fez: o formulario
ja escreve em `crm.lead`, que ja isola os pedidos dos contactos reais (um
lead nao e um cliente), e a HMD ja trabalha no CRM todos os dias. Um modelo
novo obrigaria a mais uma aplicacao, mais permissoes e mais um sitio onde
olhar, para guardar exactamente os mesmos campos.

Tambem se ponderou escrever direto em `res.partner`. Recusado: um formulario
publico a criar contactos e um alvo de spam e sujaria a base de clientes.

c) Como funciona
----------------
`crm.lead`:
  - `hmd_is_account_request` — marcado pelo formulario do website atraves de
    um campo escondido. E o que distingue estes pedidos dos outros leads;
  - `hmd_account_state` — por tratar / aprovado / recusado;
  - botao "Aprovar pedido de conta", visivel so nos pedidos por tratar, que:
      1. procura um parceiro pelo NIF e depois pelo email, para nao duplicar
         quem ja existe; se nao houver, cria a empresa com os dados do pedido;
      2. liga o lead a esse parceiro;
      3. concede-lhe acesso ao portal, o que dispara o convite por email do
         proprio Odoo — e esse convite que o parceiro usa para definir a
         palavra-passe;
      4. regista no lead o que foi feito, com ligacao para o parceiro.
  - botao "Recusar", que so muda o estado e deixa o lead no sitio. Nao apaga
    nada: o registo de quem pediu e quando fica.

d) O que este modulo NAO faz
----------------------------
Nao valida o NIF, nao verifica se a empresa existe, e nao decide nada
sozinho. A decisao e da Nina; isto so lhe poupa os sete passos manuais.
""",
    "depends": ["crm", "portal", "website_crm"],
    "data": [
        "data/ir_model_data.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "application": False,
}
