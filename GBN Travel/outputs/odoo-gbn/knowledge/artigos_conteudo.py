# -*- coding: utf-8 -*-
"""Conteúdo dos tutoriais de Knowledge do projeto Odoo - GBN (tarefa 6737).

Este ficheiro é **só dados**: a árvore de artigos a criar em `knowledge.article`
no Odoo do cliente. Quem escreve no Odoo é o `pg_criar_artigos_knowledge.py`,
que passa obrigatoriamente pelo `pg_odoo_migration_guard.py`.

Estrutura de cada entrada:
    chave   - identificador estável usado para reconciliar execuções (idempotência).
              Não é gravado no Odoo; serve para o script reconhecer o artigo pelo
              par (título, artigo-pai) e escrever em vez de duplicar.
    titulo  - `name` do artigo.
    icone   - `icon` (emoji) do artigo.
    pai     - chave do artigo-pai, ou None para o artigo de raiz.
    corpo   - `body`, HTML. O editor do Knowledge aceita HTML standard.

Ambiente confirmado (leitura à API do Odoo do cliente, 2026-07-31)
------------------------------------------------------------------
Base `joao-barros-pg-gbn-demo-main-31884248` em https://gbntravel.odoo.com,
Odoo **19.0+e** (Enterprise). Interface dos três utilizadores internos em `pt_PT`.

Instalados e relevantes: `account`, `account_accountant` (ecrã de reconciliação),
`account_invoice_extract` (leitura automática de faturas), `purchase`,
`account_online_synchronization` e `account_bank_statement_import` (movimentos
bancários), `documents` e `documents_account`, `knowledge`, `helpdesk`,
`website_helpdesk`, `base_vat` (validação de NIF), `l10n_pt`.
**Não** instalado: `account_3way_match`.

Configuração confirmada:
  - receção de faturas: `faturas@gbntravel.odoo.com`, diário «Purchases» (BILL, id 9);
  - diário bancário: «Bank» (BNK1), EUR;
  - posições fiscais: Portugal, Inside EU, Private EU, Outside EU;
  - Helpdesk: equipa «Customer Care» (id 1), formulário publicado em
    https://gbntravel.odoo.com/helpdesk/customer-care-1, alias `customer-care@`,
    etapas New / In Progress / On Hold / Solved / Cancelled, SLA activo **sem
    políticas definidas**, um único membro;
  - a base de conhecimento pública do Helpdesk está **desligada**
    (`use_website_helpdesk_knowledge = False`) — é por isso que estes manuais
    ficam numa raiz própria e não sob o artigo «Help», que é o candidato natural
    a ser publicado no site.

Números do ambiente a 2026-07-31: 92 fornecedores (43 sem NIF), 100 contactos de
empresa, 67 contactos filhos do tipo endereço de faturação, 18 faturas de
fornecedor (todas em rascunho), 3 tickets de Helpdesk.

Os `[POR VALIDAR]` que restam são decisões de negócio da GBN, não factos que se
possam ler no ambiente.
"""

# Nota de redação: os rótulos de menus e campos são os do Odoo 19.0 em português
# europeu, que é o idioma dos utilizadores desta base. Nomes de etapas do
# Helpdesk e de diários aparecem em inglês porque são registos de dados criados
# em inglês, não rótulos de interface — e é assim que o utilizador os vê no ecrã.

ARTIGOS = [

    # ------------------------------------------------------------------ #
    # RAIZ                                                               #
    # ------------------------------------------------------------------ #
    {
        "chave": "raiz",
        "titulo": "Manuais internos — GBN Travel",
        "icone": "📚",
        "pai": None,
        "corpo": """
<h1>Manuais internos — GBN Travel</h1>

<p>Manuais de utilização do Odoo da GBN Travel, escritos a partir da configuração
real desta base. Servem quem executa o trabalho todos os dias: criar e manter
contactos, tratar faturas de fornecedor de ponta a ponta, e atender pedidos de
apoio.</p>

<h2>As três áreas</h2>

<ul>
  <li><strong>Contactos</strong> — a base de tudo o resto. Um contacto bem feito poupa
      correcções em cada compra, cada fatura e cada reconciliação.</li>
  <li><strong>Faturas de fornecedor</strong> — o circuito completo, desde o email onde a
      fatura chega até ao movimento bancário reconciliado.</li>
  <li><strong>Helpdesk</strong> — pedidos de apoio que entram pelo formulário do site.</li>
</ul>

<h2>Material interno</h2>

<p>Estes manuais são para uso interno da GBN. Descrevem diários, contas,
controlos internos e números do negócio.</p>

<p>Há no Knowledge um artigo <strong>«Help»</strong> separado destes manuais, e é
propositado: esse é o artigo que o Odoo propõe publicar no site como base de
conhecimento dos clientes. Conteúdo interno não deve ficar por baixo dele — se
algum dia a base de conhecimento pública for activada, tudo o que lá estiver
passa a ser visível de fora.</p>

<h2>Como manter isto útil</h2>

<p>Estes artigos vivem no Odoo, por isso quem os usa pode corrigi-los. Quando um
passo estiver desactualizado, ou faltar um caso que aconteceu na prática, o sítio
para o registar é aqui — e não num documento à parte que ninguém volta a abrir.</p>

<p>Escritos a 31 de julho de 2026, contra a configuração então em vigor.</p>
""",
    },

    # ------------------------------------------------------------------ #
    # 1. CONTACTOS                                                       #
    # ------------------------------------------------------------------ #
    {
        "chave": "contactos",
        "titulo": "Contactos — criar e gerir",
        "icone": "👥",
        "pai": "raiz",
        "corpo": """
<h1>Contactos — criar e gerir</h1>

<p>Um contacto no Odoo é a ficha única de uma entidade com quem a GBN se
relaciona: um fornecedor, um cliente, um banco, uma pessoa dentro de uma empresa.
Não existe uma ficha de fornecedor separada de uma ficha de cliente — é a mesma
ficha, e é o uso que lhe dá o papel.</p>

<p>É por isso que vale a pena investir nos contactos antes de tudo o resto: cada
campo preenchido aqui deixa de ser perguntado depois. O contacto alimenta:</p>

<ul>
  <li>as <strong>ordens de compra</strong> — moeda, condições de pagamento, endereços;</li>
  <li>as <strong>faturas de fornecedor</strong> — NIF, posição fiscal, vencimento;</li>
  <li>a <strong>reconciliação bancária</strong> — o Odoo usa o contacto e o IBAN para propor a
      correspondência entre o movimento do banco e a fatura;</li>
  <li>os <strong>tickets de Helpdesk</strong> — quem submete o formulário do site é ligado a um
      contacto, e é assim que o histórico de um cliente se acumula num só lugar.</li>
</ul>

<p>Um contacto mal criado não dá erro imediato. Dá trabalho três semanas depois,
quando a fatura não reconcilia ou o mesmo fornecedor aparece duplicado em dois
relatórios com valores diferentes.</p>

<h2>Onde se encontram</h2>

<p>Aplicação <strong>Contactos</strong>. A mesma lista está acessível de dentro de Compras,
Contabilidade e Helpdesk, através dos campos que apontam para contactos.</p>

<h2>O estado actual desta base</h2>

<p>A 31 de julho de 2026: <strong>100 contactos de empresa</strong>, dos quais <strong>92 com
histórico de fornecedor</strong>, e <strong>67 contactos filhos do tipo endereço de
faturação</strong> — resultado da importação de fornecedores feita em maio de 2026.</p>

<p><strong>43 desses 92 fornecedores não têm NIF preenchido.</strong> É o trabalho pendente
mais concreto que existe nesta área, e está explicado em <em>Duplicados, arquivo e
correcções</em>.</p>

<h2>Nesta secção</h2>

<ol>
  <li><strong>Empresa ou pessoa</strong> — os dois tipos de contacto e quando usar cada um.</li>
  <li><strong>Contactos filhos e tipos de endereço</strong> — como se representa uma empresa com
      vários endereços e vários interlocutores.</li>
  <li><strong>Nome fiscal, nome comercial e NIF</strong> — incluindo a convenção seguida na
      importação desta base.</li>
  <li><strong>Fornecedor ou cliente</strong> — como o Odoo distingue os papéis.</li>
  <li><strong>Os campos que fazem o contacto funcionar</strong> nas compras e na contabilidade.</li>
  <li><strong>Duplicados, arquivo e correcções</strong> — e os 43 NIF por preencher.</li>
  <li><strong>Importar contactos</strong> a partir de um ficheiro.</li>
</ol>
""",
    },

    {
        "chave": "contactos-empresa-pessoa",
        "titulo": "Empresa ou pessoa: os dois tipos de contacto",
        "icone": "🏢",
        "pai": "contactos",
        "corpo": """
<h1>Empresa ou pessoa: os dois tipos de contacto</h1>

<p>Ao criar um contacto, a primeira decisão é a única difícil de mudar depois sem
consequências: <strong>Empresa</strong> ou <strong>Individual</strong>.</p>

<h2>A diferença prática</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Empresa</strong></td>
      <td>Entidade com NIF próprio, que emite e recebe faturas. Pode ter contactos
          filhos (pessoas e endereços) por baixo dela.</td>
    </tr>
    <tr>
      <td><strong>Individual</strong></td>
      <td>Uma pessoa. Pode existir sozinha, ou estar associada a uma empresa através
          do campo <strong>Nome da empresa</strong>, passando a ser um contacto filho dela.</td>
    </tr>
  </tbody>
</table>

<h2>A regra a seguir</h2>

<p><strong>Quem fatura é a empresa.</strong> Se a entidade emite faturas à GBN, o contacto
principal é do tipo Empresa, com o NIF. As pessoas com quem se fala — o comercial,
o responsável de contabilidade — são contactos <em>filhos</em> dessa empresa, nunca
contactos soltos.</p>

<p>O erro comum é criar a pessoa como contacto independente porque foi com ela que
se falou primeiro. Resultado: a fatura chega em nome da empresa, o Odoo não
encontra correspondência, e nasce um segundo contacto para a mesma entidade.</p>

<h2>Passo a passo</h2>

<ol>
  <li>Aplicação <strong>Contactos</strong> → <strong>Novo</strong>.</li>
  <li>Escolher <strong>Empresa</strong> ou <strong>Individual</strong> no topo do formulário.</li>
  <li>Preencher o nome. Ver <em>Nome fiscal, nome comercial e NIF</em> — nesta base há
      uma convenção definida sobre qual nome usar.</li>
  <li>Preencher o endereço, o <strong>país</strong> e o NIF.</li>
  <li>Guardar.</li>
</ol>

<h2>O que confirmar antes de guardar</h2>

<ul>
  <li>O <strong>país</strong> está preenchido. Condiciona a validação do NIF e a posição fiscal
      aplicada nas faturas — e nesta base a validação de NIF está activa.</li>
  <li>Se é uma pessoa dentro de uma empresa, o campo <strong>Nome da empresa</strong> aponta para
      a empresa correcta, e essa empresa já existe como contacto.</li>
</ul>

<h2>Nota técnica</h2>

<p>Em base de dados a distinção é o campo <code>is_company</code>; o selector
Empresa/Individual é o campo de interface <code>company_type</code>, que apenas
escreve nele. Confirmado em <code>odoo/addons/base/models/res_partner.py</code>
(Odoo 19.0).</p>
""",
    },

    {
        "chave": "contactos-filhos-enderecos",
        "titulo": "Contactos filhos e tipos de endereço",
        "icone": "🗂️",
        "pai": "contactos",
        "corpo": """
<h1>Contactos filhos e tipos de endereço</h1>

<p>Uma empresa raramente tem um só endereço e uma só pessoa. O Odoo representa isso
com <strong>contactos filhos</strong>: fichas por baixo da ficha da empresa, cada uma com um
tipo que diz ao Odoo <em>para que serve</em>.</p>

<h2>Os quatro tipos de endereço</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Contacto</strong></td>
      <td>Uma pessoa. É o tipo por defeito. Usa-se para interlocutores: comercial,
          contabilidade, responsável técnico.</td>
    </tr>
    <tr>
      <td><strong>Endereço de faturação</strong></td>
      <td>Onde a fatura é emitida ou enviada. É o que o Odoo propõe no campo de
          faturação dos documentos.</td>
    </tr>
    <tr>
      <td><strong>Endereço de entrega</strong></td>
      <td>Onde a mercadoria é entregue. Proposto nas ordens de compra e nas
          receções.</td>
    </tr>
    <tr>
      <td><strong>Outro</strong></td>
      <td>Qualquer endereço que não encaixe nos anteriores.</td>
    </tr>
  </tbody>
</table>

<p>Confirmado no campo <code>type</code> de <code>res.partner</code>
(<code>odoo/addons/base/models/res_partner.py</code>, Odoo 19.0). Os tipos
<em>faturação</em>, <em>entrega</em> e <em>outro</em> aparecem no nome completo do contacto,
o que ajuda a distingui-los nas listas.</p>

<h2>A convenção seguida nesta base</h2>

<p>Na importação de fornecedores, os <strong>emails de faturação de cada fornecedor foram
criados como contactos filhos do tipo Endereço de faturação</strong>, por baixo do
contacto principal da empresa. Existem hoje <strong>67 contactos filhos deste tipo</strong>, o
que mostra que a convenção foi aplicada com consistência.</p>

<p>É a estrutura standard do Odoo e é a que se deve continuar a seguir: um
fornecedor com dois emails de faturação tem dois contactos filhos, não dois
endereços amontoados no contacto principal.</p>

<p>Consequência prática: quando for preciso mudar o email para onde a GBN envia
correspondência de faturação, o sítio é o <strong>contacto filho</strong> — não a empresa.</p>

<h2>Passo a passo — acrescentar um contacto filho</h2>

<ol>
  <li>Abrir o contacto da <strong>empresa</strong>.</li>
  <li>Separador <strong>Contactos e endereços</strong> → <strong>Adicionar</strong>.</li>
  <li>Escolher o <strong>tipo</strong>.</li>
  <li>Preencher só o que distingue este filho da empresa. O que ficar vazio é
      herdado — não vale a pena repetir o endereço se é o mesmo.</li>
  <li>Guardar.</li>
</ol>

<h2>O que não fazer</h2>

<ul>
  <li>Não criar o contacto filho como Empresa. Se tem NIF próprio e emite faturas,
      então não é um filho: é outra empresa.</li>
  <li>Não duplicar o endereço da empresa em cada filho. Quando a empresa muda de
      instalações, ficam cinco endereços desactualizados em vez de um.</li>
</ul>
""",
    },

    {
        "chave": "contactos-nif-nome",
        "titulo": "Nome fiscal, nome comercial e NIF",
        "icone": "🧮",
        "pai": "contactos",
        "corpo": """
<h1>Nome fiscal, nome comercial e NIF</h1>

<p>Muitas empresas são conhecidas por um nome e faturam com outro. O Odoo tem um
campo de nome; é preciso decidir qual dos dois lá fica — e a decisão tem de ser a
mesma para todos, ou as pesquisas deixam de ser fiáveis.</p>

<h2>A convenção desta base</h2>

<p>Na importação dos fornecedores foi decidido e executado o seguinte:</p>

<ul>
  <li>o <strong>Nome Fiscal</strong> é o nome principal do contacto no Odoo;</li>
  <li>o <strong>nome comercial</strong> que vinha na coluna <em>Nome</em> do ficheiro de origem foi
      guardado no campo <strong>Notas</strong>, para consulta interna;</li>
  <li>os <strong>NIF que não passaram a validação</strong> foram também registados nas
      <strong>Notas</strong>, para preenchimento manual posterior.</li>
</ul>

<p>Isto tem duas consequências no dia a dia. Primeira: ao procurar um fornecedor
pelo nome comercial, pode não o encontrar — procurar pelo NIF ou pelo nome fiscal.
Segunda: <strong>as Notas de alguns fornecedores contêm um NIF que ainda não está no
campo próprio</strong>.</p>

<h2>O campo NIF</h2>

<p>Nesta base a validação de NIF está activa (módulo <code>base_vat</code>) e o
número é validado em função do <strong>país</strong> do contacto. Um NIF que não passe a
validação impede a gravação — foi por isso que a importação exigiu ajustes de
formatação.</p>

<p>Regras práticas:</p>

<ul>
  <li>preencher sempre o <strong>país</strong> antes do NIF: a validação depende dele;</li>
  <li>o NIF entra sem espaços; o prefixo do país é aceite (por exemplo <code>PT</code>
      seguido dos nove dígitos);</li>
  <li>se o Odoo recusar um NIF que se sabe correcto, o problema costuma ser o país
      errado no contacto, não o número;</li>
  <li>o NIF é pesquisável na barra de pesquisa dos contactos. É a forma mais fiável
      de encontrar uma empresa e de detetar duplicados.</li>
</ul>

<h2>Porque é que o NIF em falta importa</h2>

<p>Um fornecedor sem NIF não tem validação fiscal. Isso reflete-se nos mapas
fiscais e na comunicação de documentos, e obriga a corrigir caso a caso quando
aparece uma fatura desse fornecedor. Com <strong>43 fornecedores nesta situação</strong>, não é
um caso isolado — é uma lista de trabalho. Ver <em>Duplicados, arquivo e
correcções</em>.</p>
""",
    },

    {
        "chave": "contactos-fornecedor-cliente",
        "titulo": "Fornecedor ou cliente: como o Odoo distingue",
        "icone": "🔁",
        "pai": "contactos",
        "corpo": """
<h1>Fornecedor ou cliente: como o Odoo distingue</h1>

<p>Não existe uma caixa para marcar «este contacto é fornecedor». Quem chega de
outros sistemas procura-a e não a encontra, e por isso convém explicar como
funciona.</p>

<h2>O papel vem do uso</h2>

<p>O Odoo mantém dois contadores internos em cada contacto: um sobe quando o
contacto é usado como cliente, outro quando é usado como fornecedor. Ao criar a
primeira fatura de fornecedor para uma empresa, ela passa a aparecer nas listas de
fornecedores. Não há nada a marcar à mão.</p>

<p>É assim que se sabe que esta base tem <strong>92 fornecedores</strong>: são os contactos com
histórico de compra, não os que alguém classificou como tal.</p>

<p>Consequência: <strong>o mesmo contacto pode ser cliente e fornecedor ao mesmo
tempo</strong>, e é assim que deve ser. Uma única ficha, com o histórico completo dos
dois lados da relação.</p>

<h2>Como encontrar só fornecedores</h2>

<p>Nos campos de contacto dentro de Compras e das faturas de fornecedor, o Odoo já
propõe primeiro os contactos com histórico de compra. Na aplicação Contactos,
usar os filtros da barra de pesquisa.</p>

<h2>Se for preciso classificar antes de haver histórico</h2>

<p>Para separar fornecedores por natureza — agências, hotelaria, serviços,
tecnologia — o instrumento certo são as <strong>Etiquetas</strong> do contacto. São livres,
podem ser várias por contacto, e servem para filtrar e agrupar em qualquer lista e
relatório.</p>

<p>Convém que a lista de etiquetas seja curta e decidida antes de se começar a
usar. Etiquetas criadas ao correr do teclado acabam em três variantes da mesma
ideia e deixam de servir para filtrar.</p>

<p><strong>[POR VALIDAR]</strong> Se a GBN quer uma lista de etiquetas de fornecedor definida,
e quais. Hoje não há convenção registada.</p>
""",
    },

    {
        "chave": "contactos-campos-jusante",
        "titulo": "Os campos que fazem o contacto funcionar",
        "icone": "⚙️",
        "pai": "contactos",
        "corpo": """
<h1>Os campos que fazem o contacto funcionar</h1>

<p>Estes campos vivem no contacto mas o efeito sente-se noutro lado. Cada um,
preenchido uma vez, poupa uma correcção por documento.</p>

<h2>Separador Vendas e Compra</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Condições de pagamento</strong><br>(do fornecedor)</td>
      <td>Determina a <em>data de vencimento</em> calculada nas faturas de fornecedor.
          Sem isto, as faturas nascem com vencimento imediato e o planeamento de
          tesouraria deixa de fazer sentido.</td>
    </tr>
    <tr>
      <td><strong>Moeda</strong></td>
      <td>Proposta nos documentos deste fornecedor. Relevante na GBN, que compra em
          moeda estrangeira — ver <em>Faturas em moeda estrangeira</em>.</td>
    </tr>
  </tbody>
</table>

<h2>Separador Contabilidade</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Contas bancárias</strong></td>
      <td>O IBAN do fornecedor. Permite preparar pagamentos e é usado na
          reconciliação: um movimento bancário cuja contraparte tem IBAN conhecido
          é associado ao fornecedor certo com muito mais frequência.</td>
    </tr>
    <tr>
      <td><strong>Posição fiscal</strong></td>
      <td>Traduz automaticamente impostos e contas em função da origem do
          fornecedor. Nesta base estão configuradas quatro: <strong>Portugal</strong>,
          <strong>Inside EU</strong>, <strong>Private EU</strong> e <strong>Outside EU</strong>. É o campo que evita
          corrigir o IVA à mão em cada fatura estrangeira.</td>
    </tr>
    <tr>
      <td><strong>Contas a pagar / a receber</strong></td>
      <td>Só preencher se este fornecedor tiver de usar uma conta diferente da
          predefinida do plano de contas. Na dúvida, deixar como está.</td>
    </tr>
  </tbody>
</table>

<h2>A ordem por que vale a pena preencher</h2>

<ol>
  <li><strong>País e NIF</strong> — condicionam validação e posição fiscal.</li>
  <li><strong>Posição fiscal</strong> — evita erros de IVA repetidos.</li>
  <li><strong>Condições de pagamento</strong> — dão vencimentos reais.</li>
  <li><strong>IBAN</strong> — habilita pagamento e ajuda a reconciliação.</li>
  <li><strong>Etiquetas</strong> — organizam a lista.</li>
</ol>

<p><strong>[POR VALIDAR]</strong> Qual das quatro posições fiscais se aplica a cada tipo de
fornecedor da GBN. As quatro existem; a regra de atribuição é uma decisão de
negócio e não está registada. Enquanto não estiver, quem lança faturas de
fornecedores estrangeiros tem de perguntar.</p>
""",
    },

    {
        "chave": "contactos-duplicados",
        "titulo": "Duplicados, arquivo e correcções",
        "icone": "🧹",
        "pai": "contactos",
        "corpo": """
<h1>Duplicados, arquivo e correcções</h1>

<h2>Antes de criar, procurar</h2>

<p>A causa número um de contactos duplicados é criar sem procurar. Procurar
<strong>pelo NIF</strong>, não pelo nome: os nomes escrevem-se de várias maneiras, o NIF não.
Nesta base, com o nome fiscal como nome principal, procurar pelo nome comercial
pode não devolver nada mesmo quando o contacto existe.</p>

<h2>Arquivar, não apagar</h2>

<p>Um contacto que já tem documentos associados não deve ser apagado — o Odoo
impede-o, e com razão: apagaria a contraparte de faturas lançadas. O que se faz é
<strong>arquivar</strong>. O contacto desaparece das listas e das propostas de preenchimento,
mas o histórico contabilístico continua íntegro.</p>

<p>Para arquivar: abrir o contacto → menu de ações → <strong>Arquivar</strong>.</p>

<h2>Se já houver duplicados</h2>

<p>Escolher qual fica — normalmente o que tem mais documentos associados —,
transferir a informação que só existe no outro, e arquivar o que sobra. Não vale a
pena tentar mover documentos entre contactos: dá mais problemas do que resolve.</p>

<h2>Os 43 fornecedores sem NIF</h2>

<p>A 31 de julho de 2026, <strong>43 dos 92 fornecedores não têm NIF preenchido</strong>. Vêm da
importação de maio de 2026: o número original não passava a validação do Odoo e foi
registado nas <strong>Notas</strong> em vez do campo próprio, precisamente para poder ser
tratado por quem conhece os fornecedores. Foi também entregue um ficheiro Excel
com uma folha específica de identificação desses casos.</p>

<h2>Como fechar esta lista</h2>

<ol>
  <li>Na aplicação Contactos, filtrar os fornecedores <strong>sem NIF</strong>.</li>
  <li>Para cada um, ler as <strong>Notas</strong>: em muitos casos o número está lá, apenas mal
      formatado.</li>
  <li>Confirmar o <strong>país</strong> do contacto antes de mexer no NIF — é a causa mais
      frequente de a validação recusar um número correcto.</li>
  <li>Preencher o campo <strong>NIF</strong> e guardar.</li>
  <li>Limpar das Notas a parte que passou a estar no campo próprio, para a nota não
      ficar a contradizer a ficha.</li>
  <li>Se o número não se confirmar, pedi-lo ao fornecedor. Um NIF inventado é pior
      do que um NIF em falta.</li>
</ol>

<p>É trabalho que se faz uma vez. Cada contacto fechado fica fechado.</p>

<p><strong>[POR VALIDAR]</strong> Quem na GBN assume esta lista e até quando. Sem responsável
designado, 43 contactos incompletos continuam a gerar correcções a cada fatura.</p>
""",
    },

    {
        "chave": "contactos-importar",
        "titulo": "Importar contactos a partir de um ficheiro",
        "icone": "📥",
        "pai": "contactos",
        "corpo": """
<h1>Importar contactos a partir de um ficheiro</h1>

<p>Para volumes acima de uma dúzia, importar é mais rápido e mais consistente do
que criar à mão. O caminho é a vista de lista dos Contactos → menu de ações →
<strong>Importar registos</strong>.</p>

<h2>O método que funciona</h2>

<ol>
  <li><strong>Exportar primeiro um exemplo.</strong> Criar um contacto completo à mão,
      exportá-lo, e usar esse ficheiro como molde. Garante que os nomes das colunas
      são exactamente os que o Odoo espera.</li>
  <li><strong>Importar as empresas antes das pessoas.</strong> Um contacto filho precisa que a
      empresa já exista para se lhe poder ligar. Duas passagens: empresas primeiro,
      filhos depois.</li>
  <li><strong>Testar com dez linhas.</strong> O Odoo mostra o resultado antes de gravar.
      Corrigir o molde com dez linhas custa minutos; com mil, custa uma limpeza.</li>
  <li><strong>Guardar o ficheiro usado</strong>, com a data. Quando aparecer uma dúvida sobre um
      contacto, a origem é a primeira coisa que se quer ver.</li>
</ol>

<h2>Onde a importação costuma falhar</h2>

<ul>
  <li><strong>NIF inválido.</strong> O campo é validado e um número mal formatado faz falhar a
      linha. Foi exactamente o que aconteceu na importação desta base, e deu origem
      aos 43 contactos por completar.</li>
  <li><strong>País em falta</strong>, ou escrito de forma que o Odoo não reconhece. Sem país não
      há validação de NIF nem posição fiscal.</li>
  <li><strong>Contacto filho sem ligação à empresa</strong>, que fica um contacto solto.</li>
  <li><strong>Tipo de endereço em falta</strong> nos filhos, que ficam todos como «Contacto»
      quando alguns deviam ser «Endereço de faturação».</li>
</ul>

<h2>Decidir antes de importar</h2>

<p>Duas decisões que se tomam uma vez e condicionam tudo o que vem depois: <strong>qual
nome fica como nome principal</strong> — nesta base, o nome fiscal — e <strong>onde vai a
informação que não tem campo próprio</strong> — nesta base, as Notas.</p>

<p>Mudar de critério a meio produz uma base em que metade dos contactos segue uma
regra e a outra metade segue outra. Se um dia houver nova importação, seguir a
convenção que já está em vigor, mesmo que se prefira outra.</p>
""",
    },

    # ------------------------------------------------------------------ #
    # 2. FATURAS DE FORNECEDOR                                           #
    # ------------------------------------------------------------------ #
    {
        "chave": "faturas",
        "titulo": "Faturas de fornecedor — da receção por email à reconciliação",
        "icone": "🧾",
        "pai": "raiz",
        "corpo": """
<h1>Faturas de fornecedor — da receção por email à reconciliação</h1>

<p>Na GBN as faturas de fornecedor <strong>entram por email</strong>, para
<strong>faturas@gbntravel.odoo.com</strong>. Ninguém cria a fatura a partir de zero: quando um
utilizador chega ao Odoo, a fatura já lá está, em rascunho, com o ficheiro
original anexado e com os dados já lidos do PDF. O trabalho é <em>revê-la</em>,
confirmá-la, pagá-la e reconciliá-la.</p>

<h2>O circuito completo</h2>

<ol>
  <li><strong>Receção</strong> — o fornecedor envia para <code>faturas@gbntravel.odoo.com</code>.
      O Odoo cria uma fatura de fornecedor em rascunho no diário «Purchases».</li>
  <li><strong>Leitura automática</strong> — o Odoo extrai do PDF o fornecedor, as datas, os
      totais e as linhas, e preenche o rascunho.</li>
  <li><strong>Revisão</strong> — uma pessoa confere o que foi extraído contra o documento e
      corrige o que estiver errado.</li>
  <li><strong>Confirmação</strong> — a fatura passa a lançada e produz movimento
      contabilístico. Passa a haver dívida ao fornecedor.</li>
  <li><strong>Pagamento</strong> — registado no Odoo, deixa a fatura como paga.</li>
  <li><strong>Reconciliação</strong> — o movimento do extrato bancário é ligado ao pagamento,
      fechando o circuito.</li>
</ol>

<h2>O ponto crítico</h2>

<p>Uma fatura que fica em rascunho <strong>não existe para a contabilidade</strong>: não aparece
em dívidas a fornecedores, não conta para o IVA, e não é detetada como esquecida.
Não dá erro — simplesmente não está lá.</p>

<p>A 31 de julho de 2026 esta base tem <strong>18 faturas de fornecedor, todas as 18 em
rascunho</strong>. Nenhuma foi confirmada até hoje. Não é uma hipótese teórica: é o estado
actual, e é a razão pela qual o passo 4 deste circuito é o que merece mais
atenção.</p>

<p>A lista de faturas em rascunho é a lista de trabalho pendente. Deve ser vista
todos os dias e não deve crescer.</p>

<h2>Nesta secção</h2>

<ol>
  <li><strong>Como a fatura entra pelo email</strong> — o mecanismo, e o que fazer quando não entra.</li>
  <li><strong>Rever o que o Odoo leu do PDF</strong>.</li>
  <li><strong>Confirmar a fatura</strong> e o que isso faz na contabilidade.</li>
  <li><strong>Faturas em moeda estrangeira e a Data de Criação</strong> — específico desta base.</li>
  <li><strong>Registar o pagamento</strong>.</li>
  <li><strong>Reconciliar com o extrato bancário</strong>.</li>
  <li><strong>Casos que correm mal</strong> e como resolver.</li>
</ol>
""",
    },

    {
        "chave": "faturas-email",
        "titulo": "Como a fatura entra no Odoo pelo email",
        "icone": "📧",
        "pai": "faturas",
        "corpo": """
<h1>Como a fatura entra no Odoo pelo email</h1>

<h2>O endereço</h2>

<p><strong>faturas@gbntravel.odoo.com</strong></p>

<p>É este o endereço a dar aos fornecedores. Está configurado no diário
<strong>«Purchases»</strong> (código <code>BILL</code>), que é o diário onde as faturas de
fornecedor são lançadas.</p>

<h2>O mecanismo</h2>

<p>Cada diário do Odoo pode ter um endereço de email próprio. Quando lá chega uma
mensagem, o Odoo cria automaticamente:</p>

<ul>
  <li>uma <strong>fatura de fornecedor em rascunho</strong>, no diário de compras;</li>
  <li>com o <strong>email e os seus anexos</strong> guardados no documento — o PDF original fica
      sempre acessível a partir da fatura;</li>
  <li>e o <strong>remetente registado no histórico</strong> do documento.</li>
</ul>

<p>Isto é comportamento standard, não desenvolvimento à medida. Confirmado no
código: <code>account.journal</code> define o alias de email, e o alias cria
registos de <code>account.move</code> com tipo «fatura de fornecedor» e o diário já
preenchido — <code>addons/account/models/account_journal.py</code>, método
<code>_alias_get_creation_values</code> (Odoo 19.0).</p>

<h2>Onde encontrar o que entrou</h2>

<p><strong>Contabilidade</strong> → <strong>Fornecedores</strong> → <strong>Faturas</strong>, filtrando por rascunho. É
esta a caixa de entrada real do processo.</p>

<h2>Quando a fatura não aparece</h2>

<p>Por ordem de probabilidade:</p>

<ol>
  <li><strong>O fornecedor enviou para o endereço errado</strong> — para a caixa de correio de
      uma pessoa, e não para <code>faturas@gbntravel.odoo.com</code>. É o caso mais
      frequente. Reencaminhar a fatura para o endereço correcto e corrigir o
      fornecedor, para a próxima vir bem.</li>
  <li><strong>Chegou, mas ainda não foi processada.</strong> A receção não é instantânea;
      esperar alguns minutos antes de concluir que falhou.</li>
  <li><strong>A regra de encaminhamento não está a funcionar.</strong> Se a mensagem passa por
      redirecionamento configurado fora do Odoo, a falha pode estar aí. Escalar a
      quem administra o domínio.</li>
</ol>

<h2>Enquanto isso: carregar o ficheiro à mão</h2>

<p>Não é preciso esperar pela resolução para lançar a fatura. Na lista de faturas
de fornecedor é possível <strong>carregar o PDF</strong> directamente, e o Odoo cria o rascunho
e faz a leitura automática da mesma maneira. O email é o caminho normal, não o
único.</p>

<p>Esta base tem também a aplicação <strong>Documentos</strong> instalada, que é outro caminho
para transformar um ficheiro recebido numa fatura de fornecedor. Serve para
documentos que chegam por outra via — em mão, por exemplo.</p>

<h2>Pontos por confirmar</h2>

<p><strong>[POR VALIDAR]</strong> O projeto tem tarefas sobre <em>múltiplos emails de receção de
faturas</em> e <em>redirecionamento de emails</em>, com regras criadas fora do Odoo. No Odoo
existe hoje <strong>um único</strong> endereço de receção de faturas, o acima. Se existem
outros endereços que encaminham para ele, isso deve ser registado aqui — porque
muda o que se diz aos fornecedores.</p>
""",
    },

    {
        "chave": "faturas-verificar",
        "titulo": "Rever o que o Odoo leu do PDF",
        "icone": "🔍",
        "pai": "faturas",
        "corpo": """
<h1>Rever o que o Odoo leu do PDF</h1>

<p>Esta base tem a <strong>leitura automática de faturas</strong> activa (módulo
<code>account_invoice_extract</code> do Enterprise). O Odoo lê o PDF e preenche o
rascunho: fornecedor, número do documento, datas, totais e linhas.</p>

<p>Isso muda a natureza deste passo. <strong>Não se está a introduzir uma fatura — está-se
a revisar uma leitura.</strong> É mais rápido, e tem um risco próprio: é fácil confirmar
sem olhar. A leitura automática acerta na maioria dos casos, e é precisamente por
isso que os casos em que erra passam despercebidos.</p>

<h2>Abrir a fatura ao lado do PDF</h2>

<p>O anexo aparece junto ao formulário, o que permite conferir campo a campo sem
trocar de janela. É a forma mais rápida de trabalhar e a que produz menos erros.</p>

<h2>O que conferir, por ordem</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Fornecedor</strong></td>
      <td>Tem de ser o contacto correcto. Se vier vazio, o email do remetente não
          corresponde a nenhum contacto — ver <em>Casos que correm mal</em>. Nunca criar
          um contacto novo sem procurar pelo NIF primeiro.</td>
    </tr>
    <tr>
      <td><strong>Referência da fatura</strong></td>
      <td>O número do documento do fornecedor, tal como vem no PDF. É por aqui que o
          Odoo deteta faturas repetidas e é por aqui que se encontra a fatura quando
          o fornecedor telefona.</td>
    </tr>
    <tr>
      <td><strong>Data da fatura</strong></td>
      <td>A data do documento, não a de hoje. Determina o período contabilístico e o
          câmbio aplicado.</td>
    </tr>
    <tr>
      <td><strong>Data de vencimento</strong></td>
      <td>Vem das condições de pagamento do fornecedor. Se estiver errada, corrigir
          o <em>contacto</em> — assim as próximas ficam certas sem intervenção.</td>
    </tr>
    <tr>
      <td><strong>Moeda</strong></td>
      <td>A do documento. Em moeda estrangeira, ler <em>Faturas em moeda
          estrangeira</em> <strong>antes</strong> de confirmar.</td>
    </tr>
    <tr>
      <td><strong>Linhas e impostos</strong></td>
      <td>Descrição, valor, imposto e conta. É onde a leitura automática erra mais,
          sobretudo em faturas com muitas linhas ou com layout invulgar.</td>
    </tr>
  </tbody>
</table>

<h2>A verificação que não se pode saltar</h2>

<p><strong>O total do Odoo tem de ser igual ao total do documento, ao cêntimo.</strong> É a
verificação que apanha quase todos os erros de leitura de uma só vez: se o total
bate, o resto está quase certamente bem; se não bate, há algo por corrigir.</p>

<p>Quando não bate, o mais provável é o imposto: uma taxa errada numa linha, ou
posição fiscal em falta no contacto. <strong>Corrigir a causa, não o número.</strong> Um valor
forçado numa linha faz o total fechar hoje e volta a falhar na fatura seguinte do
mesmo fornecedor.</p>

<h2>Ajudar a leitura a melhorar</h2>

<p>Quando se corrige um campo que o Odoo leu mal, a correcção serve de exemplo:
faturas seguintes do mesmo fornecedor tendem a ser lidas melhor. Vale a pena
corrigir no campo certo em vez de contornar o problema noutro sítio.</p>
""",
    },

    {
        "chave": "faturas-confirmar",
        "titulo": "Confirmar a fatura e o que isso faz na contabilidade",
        "icone": "✅",
        "pai": "faturas",
        "corpo": """
<h1>Confirmar a fatura e o que isso faz na contabilidade</h1>

<h2>O que muda ao confirmar</h2>

<p>Em rascunho, a fatura é um documento de trabalho sem efeito contabilístico
nenhum. Ao <strong>confirmar</strong>:</p>

<ul>
  <li>é-lhe atribuído um <strong>número sequencial</strong> do diário, que não se repete nem se
      reutiliza;</li>
  <li>é criado o <strong>movimento contabilístico</strong>: a despesa e o IVA a debitar, a dívida
      ao fornecedor a creditar;</li>
  <li>a fatura passa a contar para os <strong>saldos de fornecedores</strong>, para a antiguidade
      de dívidas e para os mapas de IVA;</li>
  <li>fica em estado <strong>Não pago</strong>, à espera de pagamento.</li>
</ul>

<h2>Confirmar é uma decisão, não um clique</h2>

<p>Depois de confirmada, a fatura não se edita livremente. É possível repor em
rascunho, mas é uma operação que mexe em contabilidade já lançada e que em certos
casos — período fechado, documento já reportado — não está disponível.</p>

<p>A regra prática: <strong>confirmar quando o total bate e o fornecedor está certo</strong>.
Nem antes, nem muito depois.</p>

<h2>O outro lado do mesmo problema</h2>

<p>Se confirmar cedo demais lança um erro na contabilidade, não confirmar deixa a
fatura invisível. Com <strong>18 faturas em rascunho e nenhuma confirmada</strong> nesta base, o
risco em que a GBN está hoje é claramente o segundo. Uma fatura revista deve ser
confirmada no mesmo dia.</p>

<h2>Anular uma fatura confirmada</h2>

<p>Uma fatura lançada por engano não se apaga. Há dois caminhos, e a escolha não é
indiferente:</p>

<ul>
  <li><strong>Repor em rascunho</strong> e corrigir — quando o erro é interno, foi detetado logo,
      e o período ainda está aberto;</li>
  <li><strong>Nota de crédito</strong> — quando o documento já foi refletido para fora
      (pagamento, declaração fiscal) ou o período está fechado. Deixa rasto dos dois
      documentos, que é o que a contabilidade precisa.</li>
</ul>

<p><strong>[POR VALIDAR]</strong> Quem na GBN tem permissão para repor faturas em rascunho, e
quem confirma. Esta base tem três utilizadores internos — Administrator, Accounting
e Carlos Ventura — e a separação de responsabilidades entre eles não está
registada. É uma decisão de controlo interno.</p>
""",
    },

    {
        "chave": "faturas-moeda",
        "titulo": "Faturas em moeda estrangeira e a Data de Criação",
        "icone": "💱",
        "pai": "faturas",
        "corpo": """
<h1>Faturas em moeda estrangeira e a Data de Criação</h1>

<p>Este artigo descreve um comportamento <strong>específico desta base</strong>, que não existe
num Odoo standard. Foi desenvolvido a pedido da GBN.</p>

<h2>O problema</h2>

<p>Em standard, o Odoo converte uma fatura em moeda estrangeira usando a taxa de
câmbio da <strong>data da fatura</strong>. Para a GBN isso não servia: a data relevante para o
câmbio de algumas faturas de fornecedor não é a data do documento.</p>

<h2>A solução em uso</h2>

<p>Existe um campo <strong>Data de Criação</strong> nas faturas e notas de crédito
<em>de fornecedor</em>. Quando está preenchido, é <strong>essa</strong> data que determina a taxa de
câmbio aplicada. Quando está vazio, nada muda: o Odoo usa a data da fatura, como
faria de origem.</p>

<h2>Onde está e como se usa</h2>

<ul>
  <li>Fica no cabeçalho da fatura, no grupo das datas, junto à data da fatura.</li>
  <li>Só aparece em <strong>faturas e notas de crédito de fornecedor</strong>. Em documentos de
      venda não existe.</li>
  <li>Só é editável com a fatura em <strong>rascunho</strong>. Depois de confirmada não se
      altera — o câmbio já foi aplicado ao movimento contabilístico.</li>
</ul>

<h2>A consequência prática</h2>

<p>Numa fatura em moeda estrangeira, <strong>preencher a Data de Criação antes de
confirmar</strong>. Deixá-la para depois obriga a repor a fatura em rascunho para corrigir
o câmbio, o que mexe em contabilidade lançada.</p>

<p>Conferir o valor convertido antes de confirmar: se o montante em euros não é o
esperado, a data usada para o câmbio é o primeiro sítio a olhar. O diário bancário
desta base é em <strong>EUR</strong>, pelo que é sempre em euros que o valor acaba por ter de
fazer sentido.</p>

<h2>Nota técnica</h2>

<p>Módulo <code>pg_account_invoice_currency_date</code>. O campo é
<code>pg_data_criacao</code> e a extensão é feita no ponto que o próprio Odoo
desenhou para isso — o método <code>_get_invoice_currency_rate_date()</code> de
<code>account.move</code>, o mesmo que o Odoo estende na localização checa. Não
substitui lógica standard: acrescenta um caso e delega o resto.</p>

<p><strong>[POR VALIDAR]</strong> Que critério de negócio determina a data a preencher — data de
emissão do serviço, data da reserva, ou outra. O módulo dá o mecanismo; a regra de
quando o usar é da GBN e não está registada em sítio nenhum. Sem ela, cada pessoa
preenche por critério próprio e o câmbio deixa de ser comparável entre faturas.</p>
""",
    },

    {
        "chave": "faturas-pagamento",
        "titulo": "Registar o pagamento",
        "icone": "💸",
        "pai": "faturas",
        "corpo": """
<h1>Registar o pagamento</h1>

<h2>O passo</h2>

<p>Numa fatura confirmada e não paga, o botão <strong>Registar pagamento</strong> abre uma
janela com o diário — o banco de onde sai o dinheiro, nesta base <strong>«Bank»</strong> —, a
data, o montante e a referência. Confirmado, a fatura passa a <strong>Pago</strong> ou
<strong>Parcialmente pago</strong>.</p>

<h2>O que fica pendente depois</h2>

<p>Registar o pagamento no Odoo não é o mesmo que o dinheiro ter saído do banco. O
pagamento fica em trânsito até ser <strong>reconciliado</strong> com o movimento real do
extrato. É esse o passo que confirma que o Odoo corresponde ao banco — ver
<em>Reconciliar com o extrato bancário</em>.</p>

<h2>Situações comuns</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Pagamento parcial</strong></td>
      <td>Registar o valor efectivamente pago. A fatura fica parcialmente paga com o
          remanescente em aberto, e aceita um segundo pagamento mais tarde.</td>
    </tr>
    <tr>
      <td><strong>Várias faturas num só pagamento</strong></td>
      <td>Selecionar as faturas na lista e registar o pagamento em conjunto. Sai um
          movimento único, que é o que vai aparecer no extrato — e por isso
          reconcilia sem esforço. Registar uma a uma cria vários pagamentos que
          depois não correspondem à linha única do banco.</td>
    </tr>
    <tr>
      <td><strong>Pagamento em moeda estrangeira</strong></td>
      <td>A diferença de câmbio entre a data da fatura e a do pagamento é calculada
          e lançada pelo Odoo. Não a corrigir à mão nas linhas.</td>
    </tr>
    <tr>
      <td><strong>Pagamento registado por engano</strong></td>
      <td>O pagamento pode ser desassociado da fatura, que volta a não paga. Não
          criar uma nota de crédito para «anular» um pagamento — são coisas
          diferentes e deixam a contabilidade a dizer outra coisa.</td>
    </tr>
  </tbody>
</table>

<p><strong>[POR VALIDAR]</strong> Quem tem permissão para registar pagamentos, e se a GBN quer
que quem confirma a fatura seja pessoa diferente de quem a paga. É a separação de
funções mais elementar num circuito de compras.</p>
""",
    },

    {
        "chave": "faturas-reconciliacao",
        "titulo": "Reconciliar com o extrato bancário",
        "icone": "🏦",
        "pai": "faturas",
        "corpo": """
<h1>Reconciliar com o extrato bancário</h1>

<p>Reconciliar é ligar cada movimento do extrato do banco ao documento que lhe
corresponde no Odoo. É o passo que torna o Odoo uma fonte fiável: enquanto não
estiver feito, o saldo do Odoo e o saldo do banco não são comparáveis.</p>

<p>Esta base tem o módulo de <strong>Contabilidade</strong> completo instalado
(<code>account_accountant</code>), que é o que fornece o ecrã de reconciliação.</p>

<h2>Como os movimentos do banco entram</h2>

<p>Estão instalados os dois caminhos:</p>

<ul>
  <li><strong>Ligação automática ao banco</strong> (<code>account_online_synchronization</code>) — os
      movimentos entram sozinhos, sem ninguém fazer nada;</li>
  <li><strong>Importação de ficheiro</strong> (<code>account_bank_statement_import</code>) — para
      bancos sem ligação automática, ou para recuperar um período.</li>
</ul>

<p><strong>[POR VALIDAR]</strong> Qual dos dois está efectivamente em uso na GBN. Os módulos
existem; não está confirmado se a ligação automática foi configurada com o banco.
Faz diferença no dia a dia: com ligação, a reconciliação é uma rotina diária; sem
ela, alguém tem de se lembrar de importar o ficheiro.</p>

<h2>O circuito</h2>

<ol>
  <li>Os movimentos do banco entram no Odoo.</li>
  <li><strong>O Odoo propõe correspondências</strong> — para cada linha do extrato, sugere o
      pagamento ou a fatura que encaixa, com base no montante, na data, na
      contraparte e na referência.</li>
  <li><strong>A pessoa valida</strong> as propostas certas e resolve à mão as que sobram.</li>
</ol>

<h2>Porque é que uns movimentos são propostos e outros não</h2>

<p>Quanto melhores os dados, mais o Odoo acerta sozinho:</p>

<ul>
  <li>o <strong>IBAN do fornecedor</strong> no contacto permite identificar a contraparte de um
      movimento;</li>
  <li>a <strong>referência da fatura</strong> permite casar pela descrição do movimento;</li>
  <li>pagamentos <strong>agrupados</strong> no Odoo tal como saíram do banco casam directamente;
      um pagamento por fatura contra uma transferência única no banco não casa.</li>
</ul>

<p>É aqui que se paga o preço dos contactos incompletos. Um fornecedor sem IBAN não
é reconhecido, e a linha tem de ser resolvida à mão todos os meses — não uma vez,
todos os meses.</p>

<h2>O que fazer com o que não casa</h2>

<ul>
  <li><strong>Movimento sem fatura no Odoo</strong> — a fatura não foi lançada. Lançá-la primeiro.
      Não forçar a reconciliação contra uma conta genérica: a despesa fica sem
      documento e ninguém sabe explicá-la depois.</li>
  <li><strong>Diferença pequena</strong> — comissões, arredondamento de câmbio. O ecrã de
      reconciliação permite lançar a diferença numa conta própria, e é o
      procedimento correcto.</li>
  <li><strong>Movimento que não é de fornecedores</strong> — reconciliar contra a conta que lhe
      corresponde.</li>
</ul>

<h2>A ligação ao resto do circuito</h2>

<p>Com as 18 faturas desta base em rascunho, nenhuma tem pagamento e nenhuma pode
ser reconciliada. A reconciliação não é um problema autónomo: só funciona se os
passos anteriores estiverem feitos.</p>
""",
    },

    {
        "chave": "faturas-casos",
        "titulo": "Casos que correm mal e como resolver",
        "icone": "🛠️",
        "pai": "faturas",
        "corpo": """
<h1>Casos que correm mal e como resolver</h1>

<h2>A fatura chegou sem fornecedor identificado</h2>

<p>O Odoo liga o email do remetente a um contacto. Se o fornecedor envia de um
endereço que não está em nenhum contacto, o rascunho fica sem fornecedor.</p>

<p>Procurar o fornecedor <strong>pelo NIF do documento</strong>, não pelo nome. Se existir,
preencher o fornecedor no rascunho e acrescentar aquele email como <strong>contacto filho
do tipo Endereço de faturação</strong> — assim a próxima fatura já vem identificada. Se
não existir, criar o contacto seguindo os manuais de Contactos.</p>

<p>Cada vez que se faz isto, o processo fica melhor para sempre. Não fazer significa
repetir o mesmo trabalho na fatura seguinte do mesmo fornecedor.</p>

<h2>A mesma fatura entrou duas vezes</h2>

<p>Acontece quando o fornecedor reenvia, ou quando o email é reencaminhado por duas
vias. Com a <strong>referência da fatura</strong> preenchida, o Odoo avisa da repetição.</p>

<p>Ficar com um rascunho e apagar o outro — um rascunho apaga-se sem consequências,
porque ainda não há contabilidade. Se as duas já foram confirmadas, o caminho é a
nota de crédito, não a eliminação.</p>

<h2>O total não bate com o PDF</h2>

<p>Por ordem de probabilidade: taxa de imposto errada numa linha; posição fiscal em
falta no contacto (típico em fornecedores estrangeiros — esta base tem <em>Inside
EU</em>, <em>Private EU</em> e <em>Outside EU</em> configuradas); arredondamento, por o
fornecedor calcular o IVA sobre o total e o Odoo linha a linha; ou câmbio, se a
fatura é em moeda estrangeira — nesse caso ver a <em>Data de Criação</em>.</p>

<p>Corrigir a causa, não o número.</p>

<h2>A leitura automática leu mal</h2>

<p>Acontece com layouts invulgares e com faturas digitalizadas de má qualidade.
Corrigir os campos directamente no rascunho. Não vale a pena apagar e recarregar o
PDF à espera de melhor resultado — a leitura será a mesma.</p>

<h2>A fatura ficou esquecida em rascunho</h2>

<p>É o risco maior de todo o processo, porque não dá erro. A fatura simplesmente
não existe para a contabilidade, não aparece em dívidas, e não é paga — até o
fornecedor telefonar.</p>

<p>Não é hipotético nesta base: <strong>as 18 faturas existentes estão todas em
rascunho</strong>. A defesa é olhar para a lista de rascunhos com regularidade e não a
deixar crescer.</p>

<p><strong>[POR VALIDAR]</strong> Quem revê a lista de rascunhos e com que periodicidade. Sem
responsável designado, este controlo não existe na prática — e o estado actual
mostra-o.</p>

<h2>O fornecedor diz que enviou e não há nada no Odoo</h2>

<p>Ver <em>Como a fatura entra no Odoo pelo email</em>. Na maioria dos casos foi enviada
para o endereço errado. Enquanto se resolve, a fatura pode ser carregada à mão a
partir do PDF.</p>
""",
    },

    # ------------------------------------------------------------------ #
    # 3. HELPDESK                                                        #
    # ------------------------------------------------------------------ #
    {
        "chave": "helpdesk",
        "titulo": "Helpdesk — tickets a partir do formulário do site",
        "icone": "🎫",
        "pai": "raiz",
        "corpo": """
<h1>Helpdesk — tickets a partir do formulário do site</h1>

<p>O Helpdesk dá à GBN um canal único de pedidos de apoio. Em vez de chegarem por
email a pessoas diferentes, os pedidos entram por um <strong>formulário no site</strong> e
tornam-se <em>tickets</em>: registos com estado, responsável e histórico.</p>

<h2>A configuração desta base</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Equipa</strong></td>
      <td>Customer Care</td>
    </tr>
    <tr>
      <td><strong>Formulário público</strong></td>
      <td><a href="https://gbntravel.odoo.com/helpdesk/customer-care-1">https://gbntravel.odoo.com/helpdesk/customer-care-1</a> — publicado</td>
    </tr>
    <tr>
      <td><strong>Email alternativo</strong></td>
      <td><code>customer-care@gbntravel.odoo.com</code> — um email para este endereço
          também cria ticket</td>
    </tr>
    <tr>
      <td><strong>Etapas</strong></td>
      <td>New → In Progress → On Hold → Solved → Cancelled</td>
    </tr>
    <tr>
      <td><strong>Site</strong></td>
      <td>GBN Travel</td>
    </tr>
  </tbody>
</table>

<p>As etapas aparecem em inglês porque foram criadas em inglês: são registos de
dados, não rótulos de interface. O resto do Odoo está em português.</p>

<h2>O que se ganha em relação ao email</h2>

<ul>
  <li>nada se perde numa caixa de correio pessoal — os pedidos estão todos na mesma
      lista, visível a toda a equipa;</li>
  <li>cada pedido tem <strong>um responsável</strong> e uma <strong>etapa</strong>, e vê-se num relance o que
      está parado;</li>
  <li>o histórico fica <strong>ligado ao contacto</strong>, o que permite ver tudo o que já
      aconteceu com um cliente;</li>
  <li>o formulário <strong>pergunta o que é preciso</strong> à entrada, evitando a troca de três
      emails só para saber do que se trata.</li>
</ul>

<h2>Duas coisas a decidir antes de abrir isto ao público a sério</h2>

<p><strong>A equipa tem um único membro.</strong> Com uma pessoa na equipa, todos os tickets
caem para o mesmo lado e não há a quem distribuir. Se o Helpdesk vai ser usado a
sério, a equipa precisa dos membros reais.</p>

<p><strong>O SLA está ligado mas não tem políticas definidas.</strong> A funcionalidade está
activa e não há nenhuma regra de prazo configurada, pelo que não produz efeito
nenhum. Ou se definem prazos, ou o indicador não existe — ver <em>Fechar o ticket e
acompanhar o serviço</em>.</p>

<h2>Nesta secção</h2>

<ol>
  <li><strong>Como o pedido chega</strong> pelo formulário do site.</li>
  <li><strong>Triagem</strong> — etapa, prioridade e responsável.</li>
  <li><strong>Responder ao cliente</strong>.</li>
  <li><strong>Fechar o ticket</strong> e acompanhar o serviço.</li>
</ol>
""",
    },

    {
        "chave": "helpdesk-formulario",
        "titulo": "Como o pedido chega pelo formulário do site",
        "icone": "🌐",
        "pai": "helpdesk",
        "corpo": """
<h1>Como o pedido chega pelo formulário do site</h1>

<h2>Do lado de quem pede</h2>

<p>O cliente abre <a href="https://gbntravel.odoo.com/helpdesk/customer-care-1">a
página de tickets</a>, preenche o formulário e submete. Recebe confirmação de que o
pedido foi registado. Não precisa de conta nem de saber a quem se dirigir.</p>

<h2>Do lado do Odoo</h2>

<p>Cada submissão cria um <strong>ticket</strong> na equipa Customer Care, com:</p>

<ul>
  <li>o <strong>assunto</strong> e a <strong>descrição</strong> que o cliente escreveu;</li>
  <li>o <strong>contacto</strong>, ligado à ficha existente se o email corresponder a um contacto
      conhecido — é assim que o histórico se acumula;</li>
  <li>a etapa <strong>New</strong>;</li>
  <li>os <strong>anexos</strong> que o cliente juntou.</li>
</ul>

<p>A partir daí, toda a conversa fica no ticket. Ninguém tem de reencaminhar emails
para pôr um colega a par.</p>

<h2>O email como segundo caminho</h2>

<p>Um email para <code>customer-care@gbntravel.odoo.com</code> também cria ticket. É
útil para clientes que preferem responder ao email que já têm, mas o formulário é
melhor: pergunta o que é preciso à entrada, e um email diz só o que o cliente se
lembrou de escrever.</p>

<h2>Onde ver os tickets que entraram</h2>

<p>Aplicação <strong>Helpdesk</strong>, na vista da equipa Customer Care. Os tickets aparecem
organizados por etapa, o que dá de imediato a leitura do que está por atender.
Existem hoje <strong>3 tickets</strong> nesta base.</p>

<h2>Um cuidado a ter no formulário</h2>

<p>A qualidade do que entra depende do que se pergunta. Um formulário com um campo
de texto livre produz pedidos vagos que obrigam a perguntar tudo outra vez; um
formulário com campos a mais afasta quem o ia preencher. O equilíbrio útil é
perguntar o mínimo que permite <strong>encaminhar</strong> o pedido sem ter de falar com o
cliente.</p>

<p><strong>[POR VALIDAR]</strong> Se os campos do formulário actual correspondem ao que a GBN
precisa de saber à entrada.</p>

<h2>Proteção contra submissões automáticas</h2>

<p>Formulários públicos atraem submissões automáticas. O projeto já registou uma
questão de <em>reCAPTCHA</em> nesta página, entretanto resolvida. Vale a pena confirmar
que a proteção continua activa depois de qualquer alteração ao site — sem ela, a
lista de tickets enche-se de ruído e deixa de ser usada.</p>
""",
    },

    {
        "chave": "helpdesk-triagem",
        "titulo": "Triagem: etapa, prioridade e responsável",
        "icone": "🧭",
        "pai": "helpdesk",
        "corpo": """
<h1>Triagem: etapa, prioridade e responsável</h1>

<p>Um ticket que entra e fica sem responsável é um ticket que ninguém trata, mesmo
estando visível para todos. A triagem é o que evita isso, e vale mais fazê-la
depressa e mal do que bem e tarde.</p>

<h2>As etapas desta base</h2>

<table>
  <tbody>
    <tr>
      <td><strong>New</strong></td>
      <td>Entrou e ainda não foi visto. Não deve ficar aqui mais de um dia.</td>
    </tr>
    <tr>
      <td><strong>In Progress</strong></td>
      <td>Alguém está a tratar. Se ninguém está, não é esta a etapa.</td>
    </tr>
    <tr>
      <td><strong>On Hold</strong></td>
      <td>Parado à espera de algo — normalmente resposta do cliente ou de
          terceiros. É a etapa que evita que um ticket bloqueado pareça
          abandonado.</td>
    </tr>
    <tr>
      <td><strong>Solved</strong></td>
      <td>Resolvido. Fecha a coluna na vista.</td>
    </tr>
    <tr>
      <td><strong>Cancelled</strong></td>
      <td>Não vai ser tratado — duplicado, fora de âmbito, ou desistência.</td>
    </tr>
  </tbody>
</table>

<p>Mover um ticket é arrastá-lo de coluna na vista da equipa. O que importa é que a
coluna onde está <strong>diga a verdade</strong>: um ticket em <em>In Progress</em> que ninguém está a
tratar destrói a utilidade da vista para todos.</p>

<h2>Atribuir um responsável</h2>

<p>Cada ticket deve ter uma pessoa. «A equipa» não é um responsável: se o ticket é
de todos, não é de ninguém. Atribuir no campo próprio, ou arrastando na vista.</p>

<p>Hoje a equipa Customer Care tem um único membro, pelo que a atribuição é
nominal. Enquanto assim for, a triagem não separa nada — é uma razão prática para
acrescentar os membros reais.</p>

<h2>Prioridade</h2>

<p>Serve para ordenar o que se faz primeiro dentro da mesma etapa. Só funciona com
parcimónia: se tudo for urgente, a prioridade deixa de ordenar nada.</p>

<h2>Etiquetas</h2>

<p>Classificam por tema e permitem filtrar e medir — saber quais os assuntos que
geram mais pedidos é o que permite atacar a causa em vez de atender sempre o
sintoma. Como nos contactos, convém uma lista curta decidida à partida.</p>

<h2>O hábito que faz a diferença</h2>

<p>Olhar para a etapa <strong>New</strong> uma vez por dia e não deixar lá nada sem responsável.
É um minuto de trabalho e é o que separa um Helpdesk que funciona de uma lista que
se ignora.</p>
""",
    },

    {
        "chave": "helpdesk-responder",
        "titulo": "Responder ao cliente",
        "icone": "💬",
        "pai": "helpdesk",
        "corpo": """
<h1>Responder ao cliente</h1>

<h2>Duas formas de escrever, e a diferença importa</h2>

<table>
  <tbody>
    <tr>
      <td><strong>Enviar mensagem</strong></td>
      <td>Vai para o cliente, por email. É a resposta.</td>
    </tr>
    <tr>
      <td><strong>Nota interna</strong></td>
      <td>Fica só para a equipa. O cliente não a vê.</td>
    </tr>
  </tbody>
</table>

<p>É a confusão mais comum e a mais difícil de remediar depois: uma apreciação
interna enviada como mensagem chega ao cliente. Antes de escrever, confirmar qual
dos dois está seleccionado.</p>

<h2>A resposta do cliente volta ao ticket</h2>

<p>Quando o cliente responde ao email, a resposta entra no <strong>mesmo</strong> ticket. Não
nasce um ticket novo e não é preciso reencaminhar nada.</p>

<p>É por isso que a conversa deve acontecer no ticket e não na caixa de correio de
alguém: o que sai para fora do Odoo desaparece do histórico, e quem pegar no
assunto depois não tem como saber o que já foi dito.</p>

<h2>Escrever de forma que não gere outra pergunta</h2>

<ul>
  <li>dizer <strong>o que foi feito</strong>, não o que se vai tentar;</li>
  <li>se falta informação, <strong>pedir tudo de uma vez</strong>, não um campo por email;</li>
  <li>se vai demorar, <strong>dizer quanto</strong> — a espera sem prazo é o que gera o
      telefonema;</li>
  <li>evitar vocabulário do Odoo com quem não o usa: o cliente não sabe o que é uma
      «etapa» nem um «ticket em On Hold».</li>
</ul>

<h2>Quando o ticket fica à espera do cliente</h2>

<p>Depois de pedir informação, mover o ticket para <strong>On Hold</strong>. Deixá-lo em
<em>In Progress</em> faz parecer que está a ser tratado quando está parado, e faz a vista
da equipa mentir.</p>
""",
    },

    {
        "chave": "helpdesk-fechar",
        "titulo": "Fechar o ticket e acompanhar o serviço",
        "icone": "📊",
        "pai": "helpdesk",
        "corpo": """
<h1>Fechar o ticket e acompanhar o serviço</h1>

<h2>Fechar</h2>

<p>Um ticket resolvido move-se para <strong>Solved</strong>. Antes de o fazer, duas coisas: <strong>o
cliente foi informado</strong> de que está resolvido, e <strong>o que se fez está escrito no
ticket</strong>. Um ticket fechado sem explicação não serve de nada quando o mesmo
problema voltar dentro de seis meses.</p>

<p>Se o cliente responder depois de fechado, a mensagem entra no mesmo ticket e ele
pode ser reaberto. Não criar um ticket novo para a continuação de um assunto:
parte o histórico em dois e ninguém volta a juntar as pontas.</p>

<p><strong>Cancelled</strong> é diferente de <strong>Solved</strong>, e a distinção importa para as
estatísticas: um pedido duplicado ou fora de âmbito é cancelado, não resolvido. Se
tudo for para <em>Solved</em>, a taxa de resolução deixa de dizer nada.</p>

<h2>O que se passa a poder medir</h2>

<p>Com os tickets todos no mesmo sítio, passa a haver resposta para perguntas que
antes não tinham: quantos pedidos entram por semana, quanto tempo demoram, que
assuntos geram mais pedidos, quem está sobrecarregado.</p>

<p>A mais útil das quatro é a terceira. Os assuntos que se repetem são candidatos a
serem eliminados na origem — por uma correcção no processo, ou por um artigo que
responda antes de o cliente ter de perguntar.</p>

<h2>SLA: activo mas vazio</h2>

<p>Nesta base a funcionalidade de <strong>SLA</strong> está ligada na equipa Customer Care, mas
<strong>não existe nenhuma política definida</strong>. Na prática não produz efeito: nenhum
ticket é marcado como em risco, porque não há prazo contra o qual medir.</p>

<p>Um SLA é uma regra do género «pedidos de prioridade alta são respondidos em 4
horas», e o Odoo passa a sinalizar os tickets que estão a aproximar-se do prazo. É
o que transforma «demorar muito» de apreciação em indicador.</p>

<p><strong>[POR VALIDAR]</strong> Se a GBN quer definir SLA e com que prazos. Enquanto não
definir, vale a pena saber que o indicador que a equipa possa achar que tem, não
tem.</p>

<h2>Base de conhecimento para clientes</h2>

<p>O Odoo permite publicar artigos na própria página de Helpdesk, para o cliente
encontrar a resposta sem abrir ticket. Está <strong>desligado</strong> nesta base.</p>

<p>Se for activado, atenção ao artigo que se escolhe publicar: tudo o que estiver
por baixo dele passa a ser visível de fora. Estes manuais internos estão
propositadamente numa raiz separada do artigo «Help» por essa razão.</p>
""",
    },
]
