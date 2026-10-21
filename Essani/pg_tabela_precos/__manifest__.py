# -*- coding: utf-8 -*-

{
    'name': 'PG Tabela de Precos',
    'version': '19.0.1.2.0',
    'category': 'Sales',
    'summary': 'Tabela de precos em Excel, com imagens dos artigos.',
    'description': '''
Objetivo de negocio
===================
A Essani precisa de entregar tabelas de precos com a imagem de cada artigo. A
exportacao normal do Odoo devolve dados em bruto -- sem formatacao, sem imagens
e sem formulas -- e a planilha do Odoo so aceita imagens como objetos flutuantes
colocados a mao, uma a uma, que nao acompanham os dados quando estes mudam.
Nenhuma das duas serve para uma tabela com dezenas de artigos.

Este modulo gera o ficheiro a partir dos dados reais: uma linha por artigo, com
a imagem embutida na celula, agrupado por categoria.

Pre-requisitos
==============
Nenhum alem do Odoo. O `xlsxwriter` ja e dependencia do proprio Odoo.

Como funciona
=============
Um assistente em Vendas > Artigos > Tabela de precos deixa escolher categorias,
lista de precos, se a tabela sai por variante ou por artigo, e se as imagens
entram. Por omissao sai por variante: a referencia de venda vive quase sempre
na variante, e por artigo muitas linhas apareciam sem referencia nenhuma -- foi
a cliente que o apanhou, a olhar para a primeira tabela. Gera um .xlsx e devolve-o para descarga.
As imagens saem do campo `image_256` do artigo, que e a versao ja redimensionada
-- usar a `image_1920` daria ficheiros de dezenas de megabytes sem ganho visivel
na folha.

Passo a passo de utilizacao
===========================
1. Vendas > Artigos > Tabela de precos. 2. Escolher categorias (vazio = todas).
3. Escolher a lista de precos, se houver. 4. Gerar. 5. Descarregar o ficheiro.

Exemplo pratico
===============
Escolhendo "Transformadores" e "Perfis LED", sai uma folha com os artigos dessas
duas familias, cada uma com o seu cabecalho, imagem, referencia, descricao,
unidade e preco.

Pontos de atencao / avisos
==========================
O Odoo guarda muitas imagens em WEBP, formato que o xlsxwriter nao conhece. Sao
convertidas para PNG com o Pillow antes de entrarem na folha -- quando o Pillow do
servidor as souber ler. Quando nao souber, e a linha for de uma variante, usa-se a
imagem do artigo-pai: e a mesma que o Odoo mostraria se a variante nao tivesse foto
propria, e recupera a esmagadora maioria das fotografias sem tocar no catalogo. O
assistente diz quantas linhas sairam por esse recurso. A validacao e feita
antes de entregar a imagem ao xlsxwriter, e nao a volta do `insert_image`: esse
nao le a imagem, so a regista, e o erro so rebentaria ao fechar o ficheiro -- uma
unica imagem ma derrubava a tabela inteira.

Artigos sem imagem deixam a celula vazia e a linha mantem-se: e melhor uma tabela
com um buraco do que uma tabela sem o artigo. Acima de alguns milhares de artigos
a geracao fica pesada, porque cada imagem e descodificada e escrita no ficheiro.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['product', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pg_tabela_precos_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
