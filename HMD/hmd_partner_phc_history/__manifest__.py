{
    "name": "HMD Partner PHC History",
    "version": "18.0.1.0.0",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "category": "Sales",
    "summary": "Volume de faturação histórico do PHC na ficha do cliente, pesquisável e somado na fusão de contactos.",
    "license": "LGPL-3",
    "description": """
HMD Partner PHC History
=======================

a) Objetivo de negocio
----------------------
A HMD tem 20 anos de historico de faturacao no PHC. Quer consultar, no Odoo,
o volume historico de cada cliente de forma pesquisavel - nao em notas, que
nao se pesquisam (reuniao de 27/07/2026, tarefa #6610). Sao saldos saldados,
nao divida: nao entram na contabilidade.

b) Data de corte
----------------
31/12/2025. O Odoo fatura desde 20/01/2026 e nao tem nenhum documento de
cliente anterior a 2026; o exercicio de 2025 pertence inteiro ao PHC.
- ate 31/12/2025: Volume Historico PHC (este modulo);
- desde 01/01/2026: faturas do Odoo.

c) Como funciona (tecnico)
--------------------------
1. `res.partner` (`models/res_partner.py`), dois campos armazenados:
   - `phc_history_amount` (Monetary, moeda da empresa): volume historico;
   - `phc_customer_number` (Char, indexado): NR_CLIENTE do PHC, chave de
     cruzamento.
   O `total_invoiced` standard nao e armazenado e nao se pesquisa nem ordena;
   estes campos sim.
2. Fusao de contactos (`wizard/base_partner_merge.py`): `phc_history_amount`
   entra em `_get_summable_fields`, por isso fundir duplicados SOMA o volume
   em vez de manter so o do contacto de destino. Importante porque a limpeza
   de contactos (#6611) funde duplicados.
3. Vistas: campos no separador Vendas e Compras do contacto (grupo Vendas);
   colunas opcionais na lista (com soma); filtro "Com historico PHC" e
   pesquisa por N.o Cliente PHC. Visivel a utilizadores de Vendas.

d) Carga dos dados
------------------
Pelo importador standard de Contactos (atualizar por ID), a partir do
ficheiro preparado pelo Sergio Pinto com NR_CLIENTE e o valor acumulado.
Carregar DEPOIS da deduplicacao da #6611, ou pelo menos sabendo que a fusao
ja soma (ponto 2).

e) Pontos de atencao
--------------------
- Nao cria lancamentos contabilisticos nem faturas historicas (conformidade
  SAF-T/hash dos documentos).
- A moeda e a da empresa (EUR).
""",
    "depends": ["account", "sales_team"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
