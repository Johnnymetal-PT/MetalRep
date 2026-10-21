---
assunto: [WEB] Reorganizar o bloco da página de produto (descrição, preço, desenhos técnicos e documentos)
para: mch@hmdfurniture.com
---

Olá Mónica,

Obrigada pelo esclarecimento. Assim conseguimos fechar um recorte mais seguro e mais útil para si.

A nossa sugestão é separar o website em três tipos de conteúdo:

- **Texto dinâmico vindo do backoffice**: o conteúdo fica bloqueado, ou seja, continua a ser gerido no Odoo e não é editável no site.
- **Texto dinâmico com edição estética**: nestes casos, o texto continua bloqueado, mas pode ajustar localmente o aspeto visual do bloco — tipo de letra, tamanho, entrelinha e espaço entre letras.
- **Blocos editoriais livres**: aqui a edição pode ser aberta, tanto no texto como no estilo.

Este modelo é importante por uma razão prática: em elementos como nome de produto, breadcrumbs, preços ou outros textos gerados pelo sistema, o mais seguro é deixar o conteúdo protegido e abrir apenas a camada visual. Assim evita-se que uma alteração no site parta a ligação ao backoffice ou crie diferenças entre o que está no Odoo e o que aparece no website.

Na prática, a proposta fica assim:

- **bloqueado no conteúdo, editável no estilo**: menu principal, nome de produto, breadcrumbs, footer e outros textos automáticos do sistema;
- **livre no conteúdo e no estilo**: subtítulos editoriais, texto corrido e restantes blocos de conteúdo criados diretamente no website;
- **fora deste âmbito**: campos estruturais como preço, variantes, botões e restantes componentes funcionais do eCommerce, que devem manter comportamento standard.

Se este recorte fizer sentido para si, o passo seguinte é simples: a lista que nos enviar já pode vir organizada por estas três categorias. Isso permite-nos distinguir logo:

- o que fica apenas com controlo visual;
- o que fica totalmente livre no editor;
- e o que deve continuar protegido por ser conteúdo funcional do sistema.

Com essa base, conseguimos fechar consigo o recorte final e perceber exatamente que parte se resolve com organização de CSS e que parte exige desenvolvimento no editor do website.

Aguardamos então essa lista para avançarmos.
