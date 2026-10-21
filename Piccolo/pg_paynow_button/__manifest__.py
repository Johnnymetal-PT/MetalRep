# -*- coding: utf-8 -*-
{
    'name': 'PG PayNow Button',
    'version': '17.0.1.0.0',
    'summary': 'Personaliza o label do botao de submeter pagamento (payment.submit_button) para "Realizar Encomenda".',
    'category': 'Customization',
    'author': 'Parametro Global',
    'depends': ['payment'],
    'data': [
        'views/payment_template.xml',
    ],
    'description': """
PG PayNow Button
================

a) Objetivo de negocio
----------------------
No fluxo de checkout do Piccolo, o cliente nao paga online no
imediato - o botao "Pay Now" do core fica desadequado. Este modulo
renomeia o botao para "Realizar Encomenda" para reforcar que o gesto e
de confirmacao de encomenda, nao de pagamento imediato.

b) Pre-requisitos
-----------------
- Modulo standard ``payment`` instalado (vem com todas as instalacoes
  que tenham checkout/payment provider).

c) Como funciona
----------------
- Override XML do template ``payment.submit_button`` em
  ``views/payment_template.xml``.
- Faz ``xpath`` ao botao ``o_payment_submit_button`` e substitui o
  atributo ``t-out`` por ``'Realizar Encomenda'``.
- Nao tem Python.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Ir ao /shop e avancar ate ao ecra de pagamento.
3. O botao final ja aparece como "Realizar Encomenda".

e) Exemplo pratico
------------------
Cliente chega ao step de pagamento, escolhe "Pagamento mais tarde" e
ve o botao "Realizar Encomenda" em vez do "Pay Now" original.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Botao continua a dizer Pay Now"* -> limpar cache do browser e
  refrescar assets do website (Apps > Update Apps List > /web/refresh).
- *"Quero outro texto"* -> editar a string ``'Realizar Encomenda'``
  no ficheiro ``views/payment_template.xml``.

g) Pontos de atencao / avisos
-----------------------------
- Como combina com ``pg_website_order_bypass`` (que confirma a
  encomenda sem cobrar), o texto "Realizar Encomenda" e coerente. Se o
  bypass for removido, repensar este label.
- Se o Odoo for atualizado e mudar o id do botao
  (``o_payment_submit_button``) o xpath falha em silencio - revalidar
  visualmente apos upgrade.
""",
    'installable': True,
    'application': False,
    'auto_install': False,
}
