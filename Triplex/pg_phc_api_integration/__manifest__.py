# -*- coding: utf-8 -*-
{
    'name': 'pg PHC Api Integration',
    'version': '17.0.2.0.0',
    'summary': 'Sincroniza faturas e guias de transporte do Odoo para o PHC e devolve o PDF oficial',
    'description': """
PHC Api Integration (faturas e guias de transporte)
===================================================

Objetivo de negócio
-------------------
A faturação fiscal e as guias de transporte são emitidas no PHC. Este módulo envia
automaticamente as faturas (account.move) e as guias/entregas (stock.picking) do Odoo para
o PHC via Web Service SOAP, e traz de volta o PDF oficial do PHC para anexar ao documento.

Pré-requisitos
--------------
- Módulos: `sale_stock`, `sale_management`, `pg_phc_api` (conector base + credenciais PHC).
- Credenciais/endpoint PHC configurados na empresa (ver `pg_phc_api`).
- Clientes já sincronizados com o PHC (o cliente da fatura tem de existir no PHC).
- Produtos com a tipologia adequada (mapeada para MERCADORIAS/SERVIÇO/CONSUMIVEL).

Como funciona
-------------
- `phc_connection.py` (PHCConnection): cliente SOAP que monta o XML a partir do template
  `api/send_invoice.xml` e chama os scripts PHC:
    * `CriaFT`   -> fatura normal
    * `CriaFTAD` -> fatura de adiantamento (downpayment)
    * `CriaFTGT` -> guia de transporte / documento de entrega
  Trata regras complexas: ponto decimal forçado, descrições até 60 chars (com linhas de
  continuação), referências de adiantamentos (adano/adnum), anti-duplicação, etc.
- `account.move`: ao publicar a fatura (`_post`), sincroniza com o PHC; guarda `is_phc_synced`,
  a resposta e o PDF devolvido (anexado ao documento). Também há sync manual (`action_sync_to_phc`).
- `stock.picking`: ao concluir a entrega de saída (`_action_done`), envia a guia (CriaFTGT);
  campos próprios (matrícula, PDF, resposta) e sync manual/forçado.
- `wizard/account_move_send.py`: ao enviar a fatura por email, usa o PDF do PHC em vez do PDF do Odoo.

Passo a passo de utilização
---------------------------
1. Garantir `pg_phc_api` instalado e configurado (URL/utilizador/password do PHC).
2. Confirmar/publicar uma fatura de venda -> é enviada ao PHC automaticamente; o PDF do PHC
   fica anexado e `is_phc_synced` passa a True.
3. Validar uma entrega de saída -> a guia de transporte é criada no PHC (CriaFTGT).
4. Em caso de falha, usar o botão de sincronizar (ou forçar) e consultar "PHC Last Response".

Exemplo prático
---------------
Publicar a fatura FT/2026/123 -> o módulo chama CriaFT no PHC, recebe o PDF oficial e
anexa-o; ao enviar ao cliente por email, segue o PDF do PHC e não o do Odoo.

FAQ / Resolução de problemas
----------------------------
- P: A fatura não sincronizou.
  R: Ver "PHC Last Response"; confirmar credenciais PHC e que o cliente existe no PHC.
- P: Linhas em branco a aparecer como artigos no PHC.
  R: É tratado no conector (tabiva vazio nas linhas de continuação); ver notas no topo de phc_connection.py.
- P: Sincronizou duas vezes.
  R: Há anti-duplicação; usar a sincronização forçada (`phc_force_resync`) apenas quando necessário.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- `models/phc_connection_old.py` NÃO é importado (código morto, mantido por histórico).
- Em `models/__init__.py`, `res_company` e `res_config_settings` estão comentados — os campos
  de empresa vêm do `pg_phc_api`.
- Comunicação SOAP com `verify_ssl=False` (ignora verificação TLS) e downloads de PDF idem.
- Lógica fiscal sensível (faturas/adiantamentos); validar sempre em ambiente de teste.
""",
    'category': 'Accounting',

    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    'depends': ['sale_stock', 'sale_management', 'pg_phc_api'],

    'data': [
        #'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
    ],

    'installable': True,
    'application': False
}
