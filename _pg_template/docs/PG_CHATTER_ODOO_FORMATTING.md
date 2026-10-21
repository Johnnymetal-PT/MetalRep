# PG_CHATTER_ODOO_FORMATTING

## Finalidade

Explicar porque é que uma nota publicada no chatter a partir de um script sai com as etiquetas HTML à vista, e como se publica com formatação.

Regra operacional: `templates/AGENTS_SHARED.md`, secção "Publicar no chatter a partir de um script".
Ferramenta: `scripts/pg_odoo_post_chatter.py`.

É o problema irmão do `PG_EMAIL_ODOO_FORMATTING.md`: ali o Odoo descarta o que se cola, aqui escapa o que se envia. Nos dois casos, o que se escreve não é o que o Odoo mostra, e só se descobre a olhar para o resultado.

## O problema

Chamar `message_post` por RPC com um corpo em HTML produz uma nota com `<p>`, `<b>` e `<code>` visíveis como texto, embrulhados num `<p>` que o Odoo acrescenta.

`FACTO OBSERVADO` (2026-09-28, tarefa 7577 no Odoo da Parâmetro Global): uma nota publicada por `project.task` / `message_post` ficou guardada como `<p>&lt;p&gt;Duas correções ao auto-bootstrap...`, e assim foi lida por toda a gente que abriu a tarefa.

## Porquê — `FACTO OBSERVADO`

O corpo só é tratado como HTML quando chega como `Markup`. Evidência em `vendor/odoo_src/community/addons/mail/models/mail_thread.py` (Odoo 19):

- linha 2332: `'body': escape(body),  # escape if text, keep if markup`
- linha 2209 (docstring): `:param str|Markup body: body of the message, str content will be escaped, Markup for html body`

Um `str` que atravesse JSON-RPC **nunca** é `Markup`: o tipo não sobrevive à serialização. Por isso o caminho ingénuo não tem como funcionar, e falha em silêncio — a chamada devolve o id da mensagem e nada indica que o corpo foi escapado.

## A solução, que é do próprio Odoo

`message_post` aceita `body_is_html`:

- linha 2205: `attachments=None, attachment_ids=None, body_is_html=False,`
- linha 2237: `:param bool body_is_html: indicates body should be threated as HTML even if str`
- linhas 2319-2322: com `body_is_html` e utilizador interno, faz `body = Markup(body)` — e escreve no log `Posting HTML message using body_is_html=True, use a Markup object instead`

Esse aviso no log é esperado e não é erro: existe para desencorajar o parâmetro em código Python, onde se deve passar `Markup` diretamente. Por RPC não há alternativa.

O parâmetro existe nas três séries da frota: `17.0` (linha 2104), `18.0` (linha 2165), `19.0` (linha 2205).

Ensaio no Odoo da Parâmetro Global, 2026-09-28: com `body_is_html=True`, o corpo ficou guardado como `<p>ensaio <b>negrito</b> e <code>codigo</code></p>`, sem escape.

## Como se usa

O corpo escreve-se em markdown e converte-se pelo mesmo conversor dos emails ao cliente — o HTML que o Odoo aceita é o mesmo nos dois sítios, e ter um conversor só evita que divirjam.

```powershell
py .pg_framework\scripts\pg_odoo_post_chatter.py --model project.task --id 7577 --ficheiro nota.md --dry-run
py .pg_framework\scripts\pg_odoo_post_chatter.py --model project.task --id 7577 --ficheiro nota.md
```

`--dry-run` mostra o HTML e não publica. `--nota-interna` publica como nota (`mail.mt_note`) em vez de mensagem (`mail.mt_comment`), que é a diferença entre registar para a equipa e notificar os seguidores.

O `scripts/pg_odoo_query.ps1` **não serve** para isto. Desde 2026-10-07 aceita argumentos nomeados (`-KwargsJson`), que o `message_post` exige, mas não converte o markdown nem garante o `body_is_html=True` — e é isso que evita as etiquetas à vista.

## Reparar uma nota já publicada

O campo `mail.message.body` é `Html` e guarda o que lá se puser, pelo que um `write` no id da mensagem repõe o corpo correcto.

**O `write` não reenvia a notificação.** Quem recebeu o email recebeu-o com as etiquetas à vista; só o chatter fica corrigido. Se isso importar, apagar a mensagem e publicar de novo — ao custo de duas entradas no histórico.

## Uma perda conhecida: `<code>` e `<hr>`

O conversor é partilhado com os emails ao cliente, e ali o `<code>` e o `<hr>` são descartados porque não sobrevivem à colagem no compositor do Odoo (ver `PG_EMAIL_ODOO_FORMATTING.md`). No chatter **sobreviveriam** — `mail.message.body` guarda-os —, mas o conversor descarta-os na origem.

`FACTO OBSERVADO` (2026-09-28): um `<code>codigo</code>` enviado diretamente ao `message_post` ficou guardado intacto; o mesmo texto passado pelo conversor chegou como texto simples.

É uma perda deliberada, a favor de ter um conversor só. Se um dia pesar, resolve-se dando ao conversor um modo «chatter» — não duplicando-o. O script avisa quando descartou alguma coisa.
