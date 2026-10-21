# PG_CONTEXT - Memória funcional e decisória

> Fonte de verdade do estado funcional, técnico e consultivo do projeto.
> Alguns blocos marcados com `PG_AUTO` podem ser atualizados automaticamente a partir de `PG_SCOPE_INTAKE.yaml`, `.pg/PG_SCOPE_SYNC.json` e scripts do template.

## Estado Oficial do Projeto

### Identificação do projeto
<!-- PG_AUTO:IDENTIFICACAO:START -->
Nome do projeto: Detalhes-de-Fada
Cliente / unidade: [PREENCHER]
Resumo funcional do repositorio: [PREENCHER]
Fase atual do projeto: [PONTO POR VALIDAR]
<!-- PG_AUTO:IDENTIFICACAO:END -->

### Parâmetros Odoo ativos
Versão do Odoo: 20.0
Edição: Enterprise
Ambiente: SaaS (Odoo Online), base https://detalhes-de-fada.odoo.com, em período de teste até 2026-10-22 09:51 (sem código de ativação)
Path do core: C:\Users\Utilizador\.pg\odoo_src\20.0\community
Path source Enterprise: C:\Users\Utilizador\.pg\odoo_src\20.0\enterprise
Documentação oficial base: https://www.odoo.com/documentation/20.0/
Documentação Studio: https://www.odoo.com/documentation/20.0/applications/studio.html
Documentação Developer: https://www.odoo.com/documentation/20.0/developer/reference.html
Última sincronização de âmbito: [NAO EXECUTADA]
Fonte do âmbito sincronizado: [PONTO POR VALIDAR]
Última sincronização automática: 2026-10-09 18:13:10 +01:00

### Restrições do projeto
<!-- PG_AUTO:RESTRICOES:START -->
Configuracao standard permitida?: [PONTO POR VALIDAR]
Modulos standard adicionais permitidos?: [PONTO POR VALIDAR]
Odoo Studio ja aplicado no ambiente?: [PONTO POR VALIDAR]
Custom permitido?: [PONTO POR VALIDAR]
Restricoes contratuais adicionais: [PONTO POR VALIDAR]
<!-- PG_AUTO:RESTRICOES:END -->

### Pedido funcional atual
<!-- PG_AUTO:PEDIDO_ATUAL:START -->
Requisito / pedido atual: [PREENCHER]
Objetivo de negocio: [PREENCHER]
Trigger: [PREENCHER]
Frequencia: [PREENCHER]
Volumes: [PREENCHER]
Urgencia: [PREENCHER]
Criterios de aceitacao:
- [PREENCHER]
<!-- PG_AUTO:PEDIDO_ATUAL:END -->

### Processo atual
<!-- PG_AUTO:PROCESSO_ATUAL:START -->
Processo atual: [PREENCHER]
Utilizadores / papeis:
- [PREENCHER]
Excecoes conhecidas:
- [PREENCHER]
Aprovacoes:
- [PREENCHER]
Documentos envolvidos:
- [PREENCHER]
Integracoes:
- [PREENCHER]
Reporting esperado:
- [PREENCHER]
O que ja foi tentado ou validado no standard atual:
- [PREENCHER]
Porque foi considerado insuficiente:
- [PREENCHER]
<!-- PG_AUTO:PROCESSO_ATUAL:END -->

### Problema / dor
<!-- PG_AUTO:PROBLEMA_DOR:START -->
Problema / necessidade observada: [PREENCHER]
<!-- PG_AUTO:PROBLEMA_DOR:END -->

### Impacto no negócio
<!-- PG_AUTO:IMPACTO_NEGOCIO:START -->
Impacto de negocio: [PREENCHER]
<!-- PG_AUTO:IMPACTO_NEGOCIO:END -->

## Artefactos Fatuais Publicados

> Esta camada le snapshots oficiais publicados em `.pg/`.
> Os snapshots continuam a ser a source of truth factual primária; este ficheiro funciona apenas como consolidação derivada de leitura.

### Âmbito factual publicado
<!-- PG_AUTO:SCOPE_ITEMS:START -->
Resumo do scope sincronizado:
- Itens ativos: [PREENCHER]
- Itens validados: [PREENCHER]
- Itens propostos: [PREENCHER]
- Itens diferidos: [PREENCHER]
- Última alteração de task: [PONTO POR VALIDAR]

Itens em âmbito:
- [PREENCHER]
<!-- PG_AUTO:SCOPE_ITEMS:END -->

### Esforço factual publicado

Derivado de `.pg/PG_EFFORT_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

## Consolidação e Gaps

### Gaps factuais ainda por consolidar

- Projeto no Brodoo sem gestor, sem objetivo e sem âmbito estruturado: o âmbito real vive nas notas da tarefa 7844 (reunião de 06/10) e nas tarefas 7897 a 7905, 7955 e 7956.
- `odoo_env.json` com inventário de módulos `unavailable`: os módulos instalados foram lidos pelo canal `production` a 07/10 (ver «Standard já existente»).

### Dependências de refresh e validação

- A ligação `production` em `pg.odoo.connection` aponta para `detalhes-de-fada.odoo.com`. Se a base for duplicada antes de expirar (lembrete a 21/10), o URL e a base mudam e a ligação tem de ser atualizada.

## Curadoria Assistida e Itens Por Promover

> Drafts, chatter e backlog operacional vivem aqui apenas como apoio a curadoria.
> Nada desta secção deve competir com os campos oficiais ou com os snapshots publicados.

### Drafts e sinais em revisão

- [PREENCHER]

### Itens por promover a oficial

- [PREENCHER]

## Análise Consultiva e Decisão

### Análise de solução

Requisito: website com loja online para vender vestuário religioso (camisas cabeção, polos, malhas, lenços do adeus), com pedido de orçamento, sob a marca «Il Pastor», orientado à internacionalização (Itália, Espanha, França, Suíça, América; já vendem para Açores e Madeira).

### 1. Standard já existente no projeto
Estado: ANALISADO (2026-10-07)
Factos observados:
- `FACTO OBSERVADO` (canal `production`, 07/10): instalados `website`, `website_sale`, `crm`, `sale_management`, `account`, `stock`, `l10n_pt`, `l10n_pt_reports`, tema `theme_anelusia`.
- `FACTO OBSERVADO`: plano de contas português, EUR, nenhuma fatura emitida no Odoo; nenhum meio de pagamento publicado.
- `FACTO OBSERVADO`: o formulário do website cria `crm.lead` (data-model_name `crm.lead`), e `website.crm_default_user_id` atribui os pedidos à cliente.
Inferências:
- `INFERENCIA`: website, loja, formulário de orçamento e CRM cobrem o pedido apenas com configuração.
Pontos por validar:
- `PONTO POR VALIDAR`: meios de pagamento e transportadora (tarefa 7955 e 7904).

### 2. Standard adicional Odoo
Estado: ANALISADO PARCIALMENTE
Módulos / funcionalidades a avaliar:
- prestador de pagamentos compatível com MB WAY / Multibanco (por decidir com a cliente);
- métodos de envio da transportadora escolhida.
Cobertura do requisito: [PONTO POR VALIDAR]
Implicações de adoção:
- contrato com prestador de pagamentos e transportadora.
Factos observados:
- `vendor/odoo_src/community/addons/l10n_pt/__manifest__.py`: a localização PT 20.0 não inclui um módulo de certificação de faturação AT.
Inferências:
- `INFERENCIA`: faturar no Odoo exige confirmar a certificação AT da versão e do plano SaaS.
Pontos por validar:
- `PONTO POR VALIDAR`: faturação continua no WeoInvoice ou passa para o Odoo (tarefa 7905).

### 3. Custom
Estado: NÃO NECESSÁRIO
Escopo mínimo se for necessário:
- só uma eventual integração Odoo ↔ WeoInvoice, se a cliente quiser manter as duas e o WeoInvoice tiver API.
Factos observados:
- nenhum desenvolvimento feito; nada criado em Studio.
Inferências:
- n/a
Pontos por validar:
- API do WeoInvoice (só se a opção 3 da tarefa 7905 for escolhida).

### Decisão atual
Classificação final: `Configuracao standard`
Decisão: website e loja montados por configuração (páginas, menu, categorias, formulário CRM, idiomas pt_PT e en_US, design no `website.custom_code_head`), via os scripts de `website/` (branch `main`), todos pelo `pg_odoo_migration_guard`.
Justificação: o standard cobre o pedido; não há gap que justifique custom.

### Riscos
- Base em teste até 2026-10-22 09:51 sem licença: a Paula trata da licença só quando o trabalho estiver concluído; lembrete a 21/10 para duplicar a base (atividade 6372).
- Textos do site e textos legais escritos a partir das notas: **implantados, não validados** pela cliente. Textos legais por rever por jurista.
- Artigos EX-01 a EX-12 são exemplos com preços indicativos: retirar com `--retirar` quando chegar a lista real.
- Sem meios de pagamento: a loja não vende online até a tarefa 7955 estar feita.
- Imagens de ambiente e dos artigos de exemplo geradas por IA: só para a demonstração; artigos reais com fotografias reais. A imagem dos lenços mostra o Santuário de Fátima: confirmar com a cliente.
- Trabalho feito antes de a cotação ser aceite, por decisão da Lara (a Paula tinha pedido para parar a 07/10). Site em inglês (opcional do orçamento) já feito.
- API key da base da cliente exposta numa conversa: trocar.

### Próximos passos
- Reunião com a cliente a 2026-10-20 14h (guia e guião em `outputs/detalhes-de-fada/`, branch `main`): validar textos e logótipo, testar formulário, formação; decidir idiomas, envios, pagamentos e faturação.
- Carregar a lista real de artigos (Excel enviado a 07/10) e retirar os exemplos.
- Lara: trocar a API key da base da cliente; duplicar a base a 21/10 se não houver licença.
- Horas: 13h45 registadas até 08/10; cerca de 11h previstas para fechar a 1.ª fase (ponto de situação enviado à Paula).

### Odoo Studio existente (diagnóstico, não opção)
**Criar em Studio está proibido** (ver `AGENTS_SHARED.md`). Esta secção existe porque o Studio **já aplicado** muda o que o sistema faz e **não aparece no código nem em diff** — ler o repositório não basta para estabelecer o comportamento atual.
Estado: NÃO ANALISADO (base criada a 2026-10-06; `INFERENCIA`: sem Studio)
Vistas, menus, campos `x_` e automações encontrados:
- [PREENCHER]
Impacto observado no comportamento:
- [PREENCHER]
Destino proposto (migrar para standard, migrar para módulo versionado, manter):
- [PREENCHER]

## Referências e Histórico

### Referências consultadas

#### Documentação Odoo
- https://www.odoo.com/documentation/20.0/

#### Core Odoo
- `vendor/odoo_src/community/addons/website/models/website.py` (`_handle_favicon`: o ícone não é gravável por RPC no 20.0)
- `vendor/odoo_src/community/addons/website_crm/views/website_templates_contactus.xml`
- `vendor/odoo_src/community/addons/l10n_pt/__manifest__.py`
- `vendor/odoo_src/community/odoo/addons/base/models/ir_attachment.py` (`_check_contents`: no 20.0 o campo `datas` é ignorado em silêncio; o conteúdo vai em `raw`)
- `vendor/odoo_src/community/odoo/orm/fields_textual.py` (`write`: com o en_US inativo, o que se escreve noutra língua é copiado para o en_US) e `vendor/odoo_src/community/odoo/tools/translate.py` (`StoredTranslations.written`)

#### Código do projeto
- `website/` na branch `main`: scripts de montagem, conteúdos, Excel da lista de artigos e cópias das vistas originais (`website/backup/`).

### Histórico de marcos de decisão

#### 2026-10-06 - Reunião de levantamento do website
Contexto:
- reunião com a cliente (Margarida Pereira); notas na tarefa 7844.

Decisão:
- o nome visível no site é «Il Pastor»; Detalhes de Fada só onde a lei obriga.
- loja online com venda direta e pedido de orçamento (email + CRM).

Riscos / pendências:
- valor do website e licenciamento: Paula Gomes.

Referências:
- tarefa 7844; inspiração indicada pela cliente: desta.it (camiceria, maglieria) e store.fatima.pt (paramentaria).

#### 2026-10-07 - Website montado na base de produção
Contexto:
- base em pt_BR com conteúdo de exemplo do configurador (testemunhos inventados, «Black Friday», contactos fictícios) e email da empresa it.odoo@parametro.pt.

Decisão:
- site e Odoo da cliente em pt_PT; páginas, menu, categorias, formulário CRM, páginas legais, SEO e 12 artigos de exemplo; email e NIF da empresa corrigidos.

Riscos / pendências:
- validação da cliente a 20/10; revisão jurídica; meios de pagamento; licença.

Referências:
- tarefas 7900–7905, 7955, 7956; scripts em `website/`.

#### 2026-10-07 - Marca corrigida para «Il Pastore» e design novo
Contexto:
- a cliente corrigiu por email: a marca é «Il Pastore», com E.

Decisão:
- nome corrigido em todo o site; design a combinar com o logótipo (marfim, carvão, dourado; Cormorant Garamond e Lato; ramo do logótipo original), página inicial editorial, imagens de ambiente geradas por IA; traduções pt_PT em falta no pacote do Odoo 20.

Riscos / pendências:
- validação da cliente; imagens de IA só para ambiente e demonstração.

Referências:
- tarefa 7900; `website/pg_design_il_pastore.py`, `website/pg_design_v2_il_pastore.py`, `website/pg_traducoes_pt_pt.py`.

#### 2026-10-08 - Site em inglês, guias da reunião e imagens dos artigos
Contexto:
- `FACTO OBSERVADO`: base criada em pt_BR com o en_US inativo; o Odoo 20 copia para o en_US o que se escreve noutra língua, pelo que as traduções pt_PT da loja tinham passado para o texto inglês das vistas.

Decisão:
- en_US ativado e acrescentado ao website como segundo idioma; inglês original das vistas da loja reposto a partir do source; tradução inglesa do site escrita só no en_US, com verificação de que o pt_PT ficou igual.
- guia do website para a cliente e guião da demonstração (`outputs/detalhes-de-fada/`); imagens geradas por IA nos 12 artigos de exemplo.

Riscos / pendências:
- textos legais em inglês seguem a revisão jurídica dos portugueses; outros idiomas por decidir.

Referências:
- tarefas 7899, 7902, 7904; `website/pg_site_ingles_il_pastore.py`, `website/traducoes_en.py`.
