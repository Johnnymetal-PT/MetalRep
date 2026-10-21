{
    'name': 'PTAV Price Extra Import',
    'version': '1.0',
    'summary': 'Wizard para importar o "price extra" dos valores de atributo (PTAV) a partir de um Excel',
    'description': """
PTAV Price Extra Import
=======================

Objetivo de negócio
-------------------
Os suplementos de preço por valor de atributo (ex.: cor X custa +5€) vivem no campo
`price_extra` de `product.template.attribute.value` (PTAV). Atualizá-los um a um é moroso.
Este módulo permite importar todos de uma vez a partir de um ficheiro Excel.

Pré-requisitos
--------------
- Módulos: `base`, `product`.
- Biblioteca Python `pandas` instalada no servidor.
- Ficheiro Excel (.xlsx) com as colunas EXATAS: `ID` (id do PTAV) e `Value Price Extra` (novo valor).
- Acesso ao menu/ação do wizard (configurado em security/ir.model.access.csv + view).

Como funciona
-------------
Disponibiliza o wizard `ptav.price.import.wizard`:
1. O utilizador faz upload de um .xlsx.
2. `action_import()` lê o ficheiro com pandas e percorre as linhas.
3. Para cada linha usa a coluna `ID` (id do PTAV) e `Value Price Extra` (novo valor) e
   escreve `price_extra` no PTAV correspondente (via sudo()).
4. No fim mostra notificação com nº de registos atualizados/ignorados.

Passo a passo de utilização
---------------------------
1. Exportar os PTAVs existentes (Atributos > Valores) para obter o ID de cada valor.
2. Preparar o Excel com duas colunas: `ID` (ids dos PTAVs) e `Value Price Extra` (novos valores).
3. Abrir o wizard "PTAV Price Extra Import", carregar o ficheiro e executar.
4. Conferir a notificação final (X atualizados / Y ignorados) e validar alguns PTAVs.

Exemplo prático
---------------
Excel com:
- ID = 17, Value Price Extra = 5
- ID = 18, Value Price Extra = 8
- ID = 19, Value Price Extra = (vazio)  -> ignorado
Resultado: 2 PTAVs atualizados, 1 ignorado.

FAQ / Resolução de problemas
----------------------------
- P: A importação atualizou poucos registos.
  R: Confirmar que as colunas estão escritas EXATAMENTE como `ID` e `Value Price Extra`,
     e que os IDs existem (PTAV pode ter sido apagado).
- P: ImportError: No module named 'pandas'.
  R: Instalar `pandas` no Python do servidor (pip install pandas).
- P: NameError 'UserError'.
  R: É o bug abaixo descrito em Pontos de atenção; ocorre quando o campo ficheiro vai vazio.
- P: Posso correr de novo o mesmo Excel?
  R: Sim — é idempotente; só sobrescreve com o valor da última coluna.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Requer `pandas` instalado no servidor.
- O Excel TEM de ter as colunas exatas `ID` e `Value Price Extra`.
- `action_import` usa `UserError` sem o importar; se o campo ficheiro vier vazio, em vez de
  UserError ocorre NameError. (O campo `file` é `required=True`, por isso raramente acontece.)
""",
    'category': 'Product',
    'depends': ['base', 'product'],
    'data': [
        'views/ptav_price_import_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
