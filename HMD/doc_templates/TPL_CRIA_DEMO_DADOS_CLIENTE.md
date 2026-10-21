# TPL_CRIA_DEMO_DADOS_CLIENTE.md

> Template executável: preparar uma **demonstração com os dados reais do cliente**, no
> ambiente do próprio cliente (branch `brodoo`), produzir o **guia do fluxo** e, quando
> validado, **promover** para a base de testes/validação.
> Fonte de verdade deste template: artigo Odoo do workspace `pg_doc_templates`.
> Se for editado localmente, **republicar no Odoo** para não perder no próximo pull.

## Não confundir com `TPL_CRIA_DEMO`

São dois trabalhos diferentes e a regra dos dados é **oposta**:

| | `TPL_CRIA_DEMO` | **este template** |
|---|---|---|
| Dados | fictícios; e-mails obrigatoriamente `@example.com` | **reais do cliente**, ou fornecidos por ele |
| Base | de raiz, criada para a demonstração | ambiente do cliente, branch `brodoo` |
| Módulos | instalados conforme o âmbito | já configurados; **não** instalar em massa |
| Fim | o guia | guia **+ promoção** para validação |

Se não for evidente qual usar, **perguntar ao utilizador** antes de começar. Aplicar a regra
dos dados fictícios a este fluxo sanitiza exactamente os dados que dão valor à demonstração.

## Quando usar

Disparar quando o utilizador pedir, por exemplo: "preparar uma demo com os dados do cliente",
"montar um fluxo de demonstração na brodoo", "fazer um guia do processo actual do módulo X",
"mostrar ao cliente como fica isto com os dados dele".

Cobre também o caso sem demonstração nenhuma: **documentar o processo actual** de um ou mais
módulos de um projeto, em guia imprimível. É o mesmo trabalho — perceber o fluxo e explicá-lo.

---

## Passo 0 — Âmbito e origem dos dados [GATE]

1. Confirmar no `PG_CONTEXT.md`: cliente, projeto, versão/edição Odoo, ambiente, interlocutor.
2. **Que áreas/módulos entram** na demonstração. Uma demonstração que tenta cobrir tudo não
   convence de nada — escolher o circuito que responde à dor de negócio levantada.
3. **De onde vêm os dados:**
   - dados já existentes na base do cliente → usar como estão, não inventar por cima;
   - dados fornecidos pelo cliente (ficheiro) → importar, e registar o que foi importado;
   - dados que faltam para o circuito fechar → criar o **mínimo** necessário e **marcá-los**
     de forma identificável, para poderem ser removidos ou reconhecidos depois.
4. Se a demonstração exigir dados sensíveis (pessoas, valores, clientes reais) e for
   apresentada fora do cliente, **perguntar** antes de os usar.

## Passo 1 — Trabalhar na `brodoo`, nunca na produção

O ambiente de trabalho é a branch `brodoo` do Odoo.sh do cliente (`purpose: brodoo_dev`).

Consultas de leitura ao ambiente:

```
... -File .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey <chave> -Purpose brodoo_dev ^
    -Model <modelo> -Method search_read -Domain "<dominio>" -Fields <campos>
```

Qualquer **escrita** passa pelo guard — ver `TPL_MIGRACAO_DADOS_ODOO.md` (Passo 2). Isto vale
também para a preparação da demonstração: criar registos de exemplo é escrita.

Antes de construir, levantar o que já existe: módulos instalados
(`.pg/projects/<chave>/project/odoo_env.json`), volumes nos modelos-chave, e configuração
relevante. **Não instalar módulos em massa** — o ambiente é do cliente. Se faltar um módulo
standard para o circuito, isso é uma **recomendação a fazer**, com a ordem de decisão
obrigatória do `AGENTS_SHARED.md`, não uma instalação silenciosa.

## Passo 2 — Construir e validar o fluxo

1. Montar o circuito ponta a ponta, na ordem por que vai ser mostrado.
2. **Correr o circuito completo pelo menos uma vez**, com os dados reais, e confirmar que
   não há erro nem ecrã vazio. Uma demonstração que rebenta ao vivo custa mais do que não
   ter havido demonstração.
3. Registar, por passo: o que se mostra, o que o cliente deve concluir, e o que **não** está
   coberto (para não gerar expectativa).
4. Anotar o que ficou por decidir ou por validar — vai para o guia como `[POR VALIDAR]`.

## Passo 3 — Guia do fluxo (entregável)

Produzir um **HTML autónomo e imprimível** em
`outputs/<slug_projeto>/Guia_<Assunto>_<AAAA-MM-DD>.html`.

### Requisitos técnicos (todos obrigatórios)

- **Zero dependências externas.** Nada de CSS, tipos de letra ou scripts carregados da
  internet: numa sala de reunião sem rede, ou aberto pelo cliente offline, o guia tem de
  ficar igual. Embeber o que for preciso, ou declarar uma pilha local de fallback.
- **Folha de estilo de impressão** (`@media print`) a sério:
  - `page-break-inside: avoid` nos blocos de passo, para nenhum passo ficar cortado entre páginas;
  - fundos e cores que sobrevivem a preto e branco (o contraste não pode depender da cor);
  - esconder o que só faz sentido no ecrã (navegação, elementos interactivos);
  - margens de página utilizáveis.
- **Identidade Parâmetro Global**, coerente com os decks: azul `#0099FF` nos títulos,
  acento `#009FE3`, texto `#111827`, secundário `#4B5563`, linhas `#E7EEF5`, bandas
  `#F5F9FC`. Tipos de letra `Outfit` (títulos) e `Plus Jakarta Sans` (corpo), com fallback.
- Testar a impressão em PDF antes de entregar. **Rever o PDF**, não só o ecrã.

### Estrutura de conteúdo

1. **Capa** — cliente, projeto, assunto, data, autor.
2. **O que se vai ver e porquê** — a dor de negócio, em duas ou três frases.
3. **Antes → depois**, quando aplicável. É a estrutura que funciona melhor: à esquerda como
   é hoje (o sistema actual, ou o desenvolvimento à medida), à direita como fica no Odoo
   standard. Torna o ganho visível sem ser preciso explicá-lo.
4. **O circuito, passo a passo** — cada passo com o ecrã onde se está, o que se faz, e o que
   fica demonstrado. Numerados, para se poder seguir em conjunto.
5. **O que o Odoo standard passa a dar** — funcionalidades activadas que antes não existiam.
6. **O que fica fora e o que falta decidir** — âmbito não coberto e pontos `[POR VALIDAR]`.
   Esta secção protege-te: sem ela, tudo o que foi mostrado passa a parecer prometido.
7. **Próximos passos** — numerados, com responsável e data.

### Regras de conteúdo

- Números reais do ambiente, nunca inventados. Se um número não foi verificado, não entra.
- Linguagem do negócio do cliente, não do Odoo. Nomes técnicos de modelos e campos só quando
  o interlocutor é técnico.
- Nada de capturas de ecrã com dados de terceiros que o cliente não deva ver.
- Acentuação de português europeu correcta.

## Passo 4 — Promoção para a base de validação

Quando o cliente aprovar o fluxo, promover para a base de testes/validação
(`purpose: client_test`) seguindo **`TPL_MIGRACAO_DADOS_ODOO.md`**. Não duplicar aqui o
método: é o mesmo, com as mesmas guardas, o mesmo dry-run e a mesma reconciliação
obrigatória.

Dois pontos específicos desta promoção:

- **decidir explicitamente o que se promove**: só a configuração e o circuito, ou também os
  dados de exemplo criados para a demonstração? Registar a decisão — é a diferença entre uma
  base de validação limpa e uma base com ruído que o cliente vai encontrar;
- os dados criados no Passo 0 ponto 3 ficam identificáveis precisamente para esta decisão
  poder ser tomada sem adivinhar.

## Checklist antes de entregar (falha = não entregar)

- [ ] Âmbito e origem dos dados confirmados; autorização para usar dados sensíveis, se aplicável.
- [ ] Trabalho feito na `brodoo`; nenhuma escrita fora do guard; nada tocado em produção.
- [ ] Nenhum módulo instalado em massa; falta de módulo tratada como recomendação.
- [ ] Circuito completo corrido de ponta a ponta sem erros, com dados reais.
- [ ] Guia autónomo: sem dependências externas, verificado com a rede desligada.
- [ ] `@media print` presente; **PDF revisto**, sem passos cortados entre páginas.
- [ ] Secção de âmbito excluído e `[POR VALIDAR]` presente.
- [ ] Números do guia conferidos contra o ambiente.
- [ ] Decisão registada sobre o que se promove para validação.
- [ ] Acentuação correcta em todo o guia.

## Resposta final ao utilizador

- Indicar o caminho do guia e confirmar que a impressão foi revista.
- Resumir o circuito demonstrado e as áreas cobertas.
- Listar o que ficou `[POR VALIDAR]` e as decisões pendentes do cliente.
- Perguntar se deve promover para `client_test` e o que deve incluir na promoção.
