{
    'name': 'PG Partner Shipping Filter',
    'version': '1.0',
    'summary': 'Na venda, limita os endereços de entrega aos do cliente selecionado',
    'description': """
PG Partner Shipping Filter
==========================

Objetivo de negócio
-------------------
Evitar erros ao escolher o endereço de entrega numa encomenda de venda: só devem aparecer
os endereços de entrega do cliente selecionado, e não todos os contactos da base.

Pré-requisitos
--------------
- Módulos: `sale`.
- Clientes com contactos-filho do tipo `delivery` (endereços de entrega) corretamente
  configurados em `res.partner`.

Como funciona
-------------
Estende `sale.order` com um onchange em `partner_id`:
- Procura os contactos-filho do cliente do tipo "delivery" (entrega).
- Aplica um domínio dinâmico ao campo `partner_shipping_id` limitando-o a esses endereços.
- Se o cliente não tiver endereços de entrega, faz fallback para o próprio cliente.
- Sem cliente selecionado, repõe o domínio (sem restrição).

Passo a passo de utilização
---------------------------
1. Garantir que cada cliente tem os seus endereços de entrega (Contactos do cliente com
   type='delivery').
2. Criar uma cotação e escolher o cliente — o campo "Endereço de entrega" passa a oferecer
   apenas os endereços do cliente.
3. Se faltar um endereço, criar/editar no cartão do cliente e recarregar o cliente no SO.

Exemplo prático
---------------
Cliente "Móveis Silva" com 2 endereços de entrega: "Armazém Lisboa" e "Armazém Porto". Numa
nova cotação, ao escolher esse cliente, só esses dois aparecem no autocomplete do endereço
de entrega (em vez de centenas de contactos).

FAQ / Resolução de problemas
----------------------------
- P: Continuo a ver todos os endereços.
  R: O cliente pode não ter contactos-filho de tipo delivery; criar pelo menos um do tipo certo.
- P: Sem endereço de entrega aparece o próprio cliente.
  R: É o fallback intencional para evitar formulários inválidos.
- P: Vejo todos no import.
  R: É o esperado: o filtro só atua no UI (onchange) — importações/API não são afetadas.

Pontos de atenção
-----------------
- O filtro é por domínio no UI (onchange); NÃO impede escolhas via importação/API.
- Se um cliente não tiver delivery contacts, o domínio é reduzido a ele próprio.
""",
    'category': 'Sales',
    'author': 'Your Name',
    'depends': ['sale'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
