# -*- coding: utf-8 -*-
{
    'name': 'PG Protótipos',
    'version': '19.0.1.2.0',
    'category': 'Services/Project',
    'summary': (
        'Cria protótipos a partir de oportunidades CRM: artigo com especificações, '
        'projeto com etapas e versionamento entre revisões.'
    ),
    'description': '''
Objetivo de negocio
===================
Na Essani o desenvolvimento de um produto por encomenda passa por CRM, Projeto e Produção,
e até aqui partia-se em três sítios: as especificações viviam em conversas, o versionamento
era feito no nome do projeto (``control_cabinas_V7.0_Medical``) e cada projeto inventava as
suas etapas de raiz.

Este módulo fecha esse circuito. Um protótipo passa a ser, ao mesmo tempo, **um artigo** —
com referência interna própria, especificações e documentos — e **um projeto** — com etapas,
tarefas e responsáveis. São criados juntos, num gesto, a partir da oportunidade; e quando o
protótipo é aprovado já é um artigo de catálogo, sem migração nem reintrodução de dados.

Pre-requisitos
==============
- Aplicações ``project``, ``product`` e ``crm`` instaladas.
- Um projeto marcado como modelo (``is_template``), com as etapas de engenharia que os
  protótipos devem herdar. Por omissão o módulo procura o modelo chamado ``Produto Novo``;
  se não existir, o assistente pede que se escolha um.
- Uma árvore de categorias de artigo para protótipos (por omissão ``Protótipos``), com as
  especificações de cada categoria definidas em *Especificações do Artigo*
  (``product.category.product_properties_definition``). É daí que vêm os campos que o
  vendedor preenche: acrescentar uma categoria nova é configuração, não desenvolvimento.

Como funciona
=============
**Criação.** Na oportunidade existe o botão *Criar protótipo*. O assistente pede a categoria,
o nome, o gestor de projeto e as especificações pedidas pelo cliente — estas últimas aparecem
conforme a categoria escolhida. Ao confirmar, o módulo atribui a referência seguinte da
sequência ``pg.prototipo.ref`` (``PROT-AAAA-NNNN``), cria o artigo com as especificações, cria
o projeto a partir do modelo com as etapas e tarefas, liga os dois e devolve o protótipo aberto.

**Versões.** No protótipo, o botão *Nova versão* duplica artigo e projeto, herdando
especificações, etapas e tarefas, e regista a linhagem em *Versão de origem*. Recusa correr em
projetos que não sejam protótipos, e recusa **antes** de consumir uma referência.

**Alterações de especificação.** Quando as especificações de um artigo de protótipo mudam, os
projetos ligados recebem uma nota no registo e **todos os gestores** do protótipo — o gestor
de projeto e os restantes, indicados em *Outros gestores* — recebem uma atividade. É o que
garante que uma mudança acordada entre vendedor e cliente chega a quem gere a produção.

Passo a passo de utilizacao
===========================
1. Abrir a oportunidade no CRM e carregar em *Criar protótipo*.
2. Escolher a categoria do protótipo; os campos de especificação mudam conforme a categoria.
3. Preencher o nome, o gestor de projeto e as especificações pedidas pelo cliente.
4. Confirmar. O protótipo abre-se, já com a referência, o artigo e as etapas.
5. Para uma revisão, abrir o protótipo e carregar em *Nova versão*.

Exemplo pratico
===============
Uma oportunidade pede uma fonte de alimentação de 48 V e 200 W. O vendedor carrega em *Criar
protótipo*, escolhe ``Protótipos / Fontes de alimentação``, e o assistente mostra tensão de
entrada, tensão de saída, potência, corrente máxima, capacidade de carga e grau de proteção.
Preenche o que o cliente pediu e confirma. Sai ``PROT-2026-0007``, com projeto e artigo ligados.
Semanas depois o cliente sobe a potência: o gestor de projeto recebe a atividade, e a revisão
faz-se com *Nova versão*, que nasce com tudo o que a anterior tinha.

FAQ / Resolucao de problemas
============================
*Não aparece nenhum campo de especificação no assistente.* A categoria escolhida não tem
especificações definidas. Configurar em Inventário > Configuração > Categorias de Artigo, no
campo *Especificações do Artigo*.

*O assistente diz que não encontra o modelo de projeto.* Não existe nenhum projeto com
``is_template`` ativo, ou o nome do modelo mudou. Escolher o modelo no próprio assistente ou
ajustar o parâmetro ``pg_prototipos.modelo_projeto``.

*"Nova versão" recusa.* O projeto não tem artigo associado, logo não é um protótipo e não há
especificações para herdar. Preencher *Artigo do protótipo* primeiro.

*Um protótipo pode ter mais do que um gestor?* Sim. O gestor de projeto continua a ser o
principal; os restantes juntam-se em *Outros gestores* (no assistente e no projeto). Um
projeto sem outros gestores avisa só o principal, como antes.

*O gestor não recebeu a atividade.* A notificação só corre para artigos dentro da árvore de
categorias de protótipos e para projetos ligados ao artigo pelo campo *Artigo do protótipo*.

Pontos de atencao / avisos
==========================
- A sequência ``PROT-`` usa uma sequência PostgreSQL: um número consumido **não volta atrás**
  com um rollback. É por isso que todas as validações acontecem antes de a consumir.
- Ao duplicar um projeto, o indicador de modelo (``is_template``) sobrevive à cópia; o módulo
  limpa-o explicitamente, senão cada protótipo nasceria como modelo e desapareceria da lista.
- Este módulo substitui as ações de servidor e a regra de automatização criadas à mão durante
  a fase de configuração. Depois de instalar, essas devem ser **desativadas, nunca apagadas**,
  para não duplicar notificações.
- Os campos manuais ``x_pg_artigo_prototipo`` e ``x_pg_versao_origem`` são migrados na
  instalação. Ficam em base como estavam; convém desativá-los depois de confirmar a migração.
''',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['project', 'product', 'crm'],
    # A ordem importa: o botao no formulario da oportunidade referencia a accao do
    # assistente, por isso o ficheiro que a define tem de ser carregado primeiro.
    # Ao contrario, a instalacao morre com "External ID not found".
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/pg_prototipo_criar_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/crm_lead_views.xml',
    ],
    'post_init_hook': 'post_init_migrar_campos_manuais',
    'installable': True,
    'application': False,
    'auto_install': False,
}
