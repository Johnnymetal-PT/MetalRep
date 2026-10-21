# Website da LusoSofá — ferramentas

Odoo **18.0**, em `https://lusosofa.parametro.pt`, base `LUSOSOFA`.
A identidade vive no módulo [`pg_lusosofa_theme`](../pg_lusosofa_theme); estes
scripts aplicam-na e mantêm o site.

## Antes de correr seja o que for

As credenciais lêem-se de `~/.lusosofa_odoo.json` e **nunca** entram no
repositório:

```json
{ "url": "https://lusosofa.parametro.pt", "db": "LUSOSOFA",
  "login": "...", "api_key": "..." }
```

> **A chave API expira à meia-noite seguinte**, seja qual for a hora a que for
> criada — `FACTO OBSERVADO` em quatro chaves seguidas, lido de
> `res.users.apikeys.expiration_date`. Uma chave criada às 23:00 dura uma hora.
> No ecrã de criação há um campo de duração: escolher a validade mais longa
> poupa a rotina diária, e é condição para qualquer coisa agendada.

## Os scripts

Todos fazem **dry-run por defeito** e só escrevem com `--aplicar`. Todos tiram
resguardo antes de escrever, para `.backup_lusosofa_*.json` na raiz (ignorados
pelo git), com o comando de reversão lá dentro.

| Script | O que faz |
|---|---|
| `aplicar_identidade.py` | importa o módulo, selecciona paleta e tipografia, invalida o bundle CSS, preenche empresa e website, activa o espanhol e **verifica o contraste de todas as combinações de cor no CSS servido** |
| `criar_categorias_loja.py` | cria as categorias da loja e arruma os artigos, por regra e não por lista |
| `despublicar_pagina.py` | despublica uma página, recusando-se se algum menu ou vista lhe apontar |
| `traduzir_espanhol.py` | traduz o conteúdo próprio (menus, categorias, páginas escritas à mão) |
| `corrigir_rodape.py` | removeu as ligações mortas e traduziu os rótulos ingleses do rodapé |
| `aplicar_decisoes_site.py` | redes sociais, código postal, fim da publicidade ao fornecedor |
| `corrigir_grafia_marca.py` | uniformiza a grafia `LusoSofá`, origem **e** valores traduzidos |
| `criar_pagina_projetos.py` | cria `/projetos` e aponta-lhe a entrada do rodapé |

Uso típico:

```bash
python3 scripts_lusosofa/aplicar_identidade.py               # ver o que mudaria
python3 scripts_lusosofa/aplicar_identidade.py --aplicar     # aplicar
python3 scripts_lusosofa/aplicar_identidade.py --so-verificar
```

## Cinco coisas que custaram caro a descobrir

Estão todas comentadas no código, com data. Repetem-se aqui porque são o tipo
de coisa que alguém «simplifica» de volta ao estado defeituoso.

**1. Escrever numa língua e verificar noutra.** Sem `lang` no contexto, o
`execute_kw` lê e escreve o valor `en_US` dos campos traduzíveis, mesmo que o
utilizador autenticado seja pt_PT. Uma correcção a um nome de produto acertou
no `en_US` enquanto o site, que serve pt_PT, continuava a mostrar o erro — e a
verificação, a ler pelo mesmo canal, deu-a por feita.

**2. Verificar a origem em vez do resultado.** O SCSS do módulo conferia e o
CSS compilado que o browser recebia não, porque o bundle não tinha sido
invalidado. Instalar o módulo não chega: é preciso apagar o anexo do bundle
para o Odoo o recompilar. O passo 7 verifica o **ficheiro servido**, e
pergunta à homepage qual é — escolher o anexo mais recente por data apanha
órfãos de temas antigos durante a janela da recompilação.

**3. Saltar em silêncio o que não se sabe ler.** A verificação de contraste só
lia hexadecimais e ignorava as cores `rgba()` — sem avisar. Um relatório sem
avisos lê-se como aprovação. Agora acusa o que não conseguir interpretar.

**4. Desactivar `web.brand_promotion` põe o site inteiro a HTTP 500**,
incluindo login e portal. É o contentor que várias camadas invocam por
`t-call`, e chamar um template inactivo rebenta o pedido todo. Para lhe
remover o conteúdo, herda-se dela e substitui-se por nada — ver
[`views/sem_publicidade_fornecedor.xml`](../pg_lusosofa_theme/views/sem_publicidade_fornecedor.xml).

**5. Mudar o texto de origem não deixa as traduções órfãs.** O Odoo remapeia-as
para o novo termo e, ao fazê-lo, **grava o texto antigo como tradução da
própria língua de origem**. A página fica com uma tradução pt_PT explícita a
tapar uma origem já corrigida. Corrigir a origem não chega: é preciso corrigir
os valores traduzidos em todas as línguas.

## Contraste: o que a paleta permite e não permite

Medido sobre o CSS servido. As quinze combinações passam AA.

- Sobre o **ouro da marca** `#84703F` (fundo da combinação 4) **só o branco
  passa**, a 4,80:1 — nem o preto puro chega, que fica em 4,37:1. O ouro está
  a meio da escala de luminância, sem folga para nenhum lado. Por isso as
  ligações dessa combinação são brancas e levam sublinhado permanente: com
  texto também branco, a cor deixa de as distinguir.
- As duas combinações claras **não levam o mesmo valor de ligação**: a cc2
  assenta no linho `#EDE7DC` e a cc3 no dourado clareado `#C8B074`. O mesmo
  `#6B5B33` dá 5,38:1 num e 3,13:1 no outro.

## O que falta no site

Do nosso lado: limpar o menu duplicado (`Default Main Menu`), a página `/`
vazia e um dos dois `/contactus`; renomear a transportadora `Standard
delivery`; e o `title="Call Customer Service"` na homepage.

À espera do cliente: preços e IVA, fichas técnicas para as descrições, textos
legais (termos, privacidade, devoluções e livro de reclamações), e um
fornecedor de pagamentos — este último com prazo próprio, por ser contrato.

**Nada disto foi validado pelo cliente.** Implantar prova que o código lá está;
validar é ele dizer que faz o que quer.
