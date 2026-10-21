# PG_EMAIL_ODOO_FORMATTING

## Finalidade

Explicar porque é que um email produzido em markdown não cola no Odoo, o que o editor do Odoo aceita realmente, e como se gera um corpo de email pronto a colar sem edição manual.

Regra operacional: `templates/AGENTS_SHARED.md`, secção "Emails para colar no Odoo".
Ferramentas: `scripts/pg_build_email_cliente.py` (conversão) e `scripts/pg_copy_email_cliente.ps1` (conversão + área de transferência).

## O problema

O `TPL_EMAIL_CLIENTE.md` produz markdown. O compositor do Odoo é um editor rich-text, não um renderizador de markdown: ao colar, os `**`, os `-` de lista e os `|` de tabela ficam como texto literal. Quem envia o email tem de refazer negritos, listas e tabelas à mão, de cada vez.

Colar HTML resolve — mas só o HTML certo. O editor do Odoo filtra tudo o que entra por colagem, e a maior parte do que se escreveria à mão (CSS inline, `<div>`, `<span>`) é descartada em silêncio.

## O que sobrevive à colagem — `FACTO OBSERVADO`

Evidência no source, idêntica em Odoo 17, 18 e 19:

- Odoo 19: `vendor/odoo_src/community/addons/html_editor/static/src/core/clipboard_plugin.js` — `CLIPBOARD_WHITELISTS` (linhas 34-99) e `cleanForPaste` (linhas 455-583)
- Odoo 17 e 18: `vendor/odoo_src/community/addons/web_editor/static/src/js/editor/odoo-editor/src/OdooEditor.js` — `CLIPBOARD_WHITELISTS` (a partir da linha 126), mesmas constantes

| | Sobrevive |
|---|---|
| Etiquetas | `p`, `h1`–`h6`, `blockquote`, `pre`, `ul`, `ol`, `li`, `i`, `b`, `u`, `s`, `em`, `font`, `strong`, `table`, `thead`, `th`, `tbody`, `tr`, `td`, `img`, `br`, `a` |
| Atributos | `class`, `href`, `src`, `target` — e **mais nenhum** |
| Classes | `table`, `table-bordered`, `o_table`, `oe-nested`, `o_checklist`, `o_checked`, `img-fluid`, `rounded`, e os prefixos `float-`, `padding-`, `shadow`, `text-o-`, `bg-o-`, `btn`, `fa` |

Consequências que determinam o formato gerado:

1. **`style` nunca sobrevive.** Não está na lista de atributos, e para `SPAN`, `B`, `STRONG`, `I`, `S`, `U`, `FONT` e `TD` (`styledTags`) é removido explicitamente. Fixar tipo de letra, cor ou margens no HTML do email é trabalho perdido.
2. **`<div>` e `<span>` desaparecem** (o conteúdo é desembrulhado), e `META`, `STYLE` e `SCRIPT` são removidos com o conteúdo. Uma folha de estilo no ficheiro não afecta a colagem.
3. **`<hr>` e `<code>` não estão na lista** — o `<hr>` desaparece, o `<code>` deixa o texto e perde-se a etiqueta.
4. **Listas aninhadas** usam o formato do Odoo: `<li class="oe-nested"><ul>...</ul></li>` (ver `addons/html_editor/static/src/main/list/list_plugin.js`).
5. **Tabelas** recebem automaticamente `class="table table-bordered o_table"` na colagem (`prepareClipboardData`, linha 373).

Ao gravar, o corpo passa ainda por `html_sanitize` (`odoo/tools/mail.py`): `mail.message.body` é declarado com `sanitize_style=True` e a etiqueta `style` está em `kill_tags`. Ou seja, a segunda barreira confirma a primeira.

**Conclusão de desenho:** o HTML gerado é semântico e sem uma linha de CSS. A formatação vem do Odoo — que é exactamente o que se pretende, porque o email fica com o aspecto nativo do ambiente do cliente e igual em qualquer projeto.

## Como se usa

Rascunho `.md` (o assunto e os destinatários no topo, fora do corpo):

```markdown
---
assunto: Decisão necessária — Integração de faturação — até 30/04
para: antonio.silva@cliente.pt
cc: pedro.coelho@parametro.global
---

Exmo. Sr. António Silva,

Para avançarmos, necessitamos da vossa indicação sobre o **formato de comunicação**:

- **Opção A:** comunicação directa por webservice — menos passos manuais
  - requer credenciais de produção da AT
- **Opção B:** exportação SAF-T mensal

Com os melhores cumprimentos,

Nuno Oliveira
Parâmetro Global — Consultoria Informática
```

Geração:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_copy_email_cliente.ps1 -Path .\email_decisao.md
```

O que acontece:
- escreve `email_decisao.html` ao lado do rascunho — pré-visualização com o assunto, os destinatários, os avisos da conversão e um botão **Copiar corpo**;
- deixa o corpo na área de transferência em dois formatos: `HTML Format` (CF_HTML), que é o que o editor do Odoo lê, e texto simples para campos sem formatação;
- imprime o assunto, os destinatários e os avisos.

No Odoo: abrir o compositor, colocar o cursor no corpo, `Ctrl+V`. O assunto copia-se da linha impressa na consola ou do topo do `.html`.

`-NoClipboard` gera só o ficheiro (útil em CI ou por SSH). O conversor Python funciona isolado e sem dependências externas:

```bash
python scripts/pg_build_email_cliente.py --md email_decisao.md --fragmento   # HTML colável para stdout
python scripts/pg_build_email_cliente.py --md email_decisao.md --texto       # alternativa em texto simples
```

## Markdown suportado

| Markdown | HTML gerado | Nota |
|---|---|---|
| linha em branco | `<p>` | separa parágrafos |
| quebra simples | `<br>` | é o que serve para assinaturas |
| `**texto**`, `__texto__` | `<strong>` | |
| `*texto*`, `_texto_` | `<em>` | |
| `~~texto~~` | `<s>` | |
| `[texto](url)` | `<a href target="_blank">` | email sem esquema vira `mailto:`; `javascript:` é removido |
| `- item` / `1. item` | `<ul>` / `<ol>` | aninhamento por indentação, no formato `li.oe-nested` |
| `\| a \| b \|` + separador | `<table class="table table-bordered o_table">` | primeira linha vira `<thead>` |
| `> citação` | `<blockquote>` | |
| ```` ``` ```` | `<pre>` | |
| `# ` a `###### ` | `<h1>`–`<h6>` | níveis 1 e 2 avisam: no Odoo ficam enormes num email |
| `---` | nada | `<hr>` não sobrevive; o conversor avisa |
| `` `código` `` | texto simples | `<code>` não sobrevive; o conversor avisa |

Etiquetas cruas aceites no markdown, sem atributos: `<br>`, `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<s>`. Qualquer outro HTML é escapado e aparece como texto — com aviso.

## Fecho e assinatura

O compositor do Odoo insere a assinatura do utilizador (`res.users.signature`) em cada envio, e essa assinatura já traz a saudação de fecho, o nome, o cargo e o rodapé da marca com logótipo. Um fecho escrito no rascunho aparece **por cima** dela — e quem envia tem de o apagar à mão, de cada vez.

Por isso o conversor **retira do fim do corpo** o fecho e a assinatura, e diz nos avisos exactamente o que retirou. Corta a partir de uma saudação de fecho (`Com os melhores cumprimentos`, `Cumprimentos`, `Atentamente`, `Best regards` e variantes) ou de um separador `--`.

Salvaguardas para não comer conteúdo:
- só procura na cauda do documento, e só em parágrafos — uma lista, uma tabela ou um título travam a procura;
- a cauda está limitada a 10 linhas de texto;
- a saudação tem de ocupar a linha inteira, pelo que "Cumprimentos ao Sr. António pela decisão" não é um fecho;
- nada é removido em silêncio: o que saiu vai no aviso, linha a linha.

`-ManterAssinatura` (ou `--manter-assinatura` no conversor) desliga o comportamento, para destinos sem assinatura configurada.

A regra a montante é não escrever o fecho no rascunho — está em `templates/AGENTS_SHARED.md`. A remoção é a rede de segurança para os rascunhos que já existem.

## Avisos da conversão

Os avisos não são decorativos: são a lista do que o Odoo vai descartar ou do que ficou por preencher. Aparecem na consola e no topo do `.html`. Casos cobertos: falta de assunto, `---` removido, `<code>` perdido, título de nível 1 ou 2, HTML escapado, link sem esquema ou com esquema proibido, chave de cabeçalho desconhecida e **marcador de template por preencher** (ex.: ficou um `[Nome]` no corpo).

## Garantia de que o HTML é colável

`pg_build_email_cliente.py` valida o resultado contra a lista branca antes de o devolver (`validar_fragmento`) e **falha** se aparecer uma etiqueta, atributo ou classe que não sobreviva à colagem. Não é possível gerar um email com `style` ou `<div>` por acidente.

Testes: `python -m unittest scripts.tests.test_pg_build_email_cliente -v` (a partir da raiz do `_pg_template`; 27 casos, incluindo os invariantes de colagem e a preservação de acentos).

## Nota de codificação

Dois pontos onde os acentos se perderiam, ambos resolvidos:

- **Python → PowerShell:** o resultado passa por um ficheiro JSON em UTF-8 lido com `Read-Utf8JsonFile`, não por `stdout` (a consola do PS 5.1 descodifica em ANSI e produziria mojibake).
- **PowerShell → área de transferência:** o CF_HTML é escrito como bytes UTF-8 num `MemoryStream`. Passar a string directamente ao `DataObject` faz o .NET Framework gravar com a codificação errada.

`FACTO OBSERVADO`: a leitura de volta com `Clipboard::GetData('HTML Format')` mostra acentos estragados, mas isso é um bug de descodificação do .NET Framework na leitura — os bytes na área de transferência estão correctos (verificado com leitura crua via Win32: `RegisterClipboardFormat` + `GetClipboardData` + `GlobalLock`). Por isso a verificação dentro do script só olha para marcas ASCII.

## Limitações conhecidas

- **Alinhamento de colunas** em tabelas markdown (`:---:`) não tem efeito: exigiria `style` ou classes fora da lista branca.
- **Imagens** só funcionam com `src` acessível pelo destinatário; um caminho local no disco não sobrevive ao envio. Para imagens no corpo, o caminho fiável continua a ser inseri-las no editor do Odoo.
- **Assinatura:** ver a secção "Fecho e assinatura" acima. O conversor nunca acrescenta assinatura, e retira a que encontrar no fim do rascunho.
- `PONTO POR VALIDAR`: em ambientes onde a colagem seja feita por um browser com política restritiva de área de transferência, o botão **Copiar corpo** do `.html` pode cair no caminho alternativo (`document.execCommand`). O resultado é o mesmo; só muda o mecanismo.

## Referências

- Regra operacional: `templates/AGENTS_SHARED.md` (secção "Produção de documentos")
- Template do conteúdo e tom: `doc_templates/TPL_EMAIL_CLIENTE.md`
- Higiene de conteúdo e acentuação: [PG_CONTENT_HYGIENE.md](PG_CONTENT_HYGIENE.md)
