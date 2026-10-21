# PG - Padrão de Documentação de Módulos Custom

> Objetivo: garantir que qualquer pessoa que pegue num módulo custom deste
> repositório pela primeira vez percebe **para que serve** e **como funciona**
> sem ter de decifrar o código. Aplica-se a todos os módulos com prefixo `pg_`.

Este padrão é **obrigatório** ao criar ou alterar módulos custom. Não é
trabalho opcional para "depois": faz parte da definição de pronto (DoD) de
qualquer implementação ou atualização de módulo custom.

## Âmbito

- **Módulos ativos:** documentar a fundo (manifest + código), conforme abaixo.
- **Módulos deprecados:** NÃO documentar a fundo. Basta, no `__manifest__.py`,
  uma nota de obsoleto + indicação do substituto (ver secção "Módulos
  deprecados").

## 1. Manifest (`__manifest__.py`)

O `summary` e o `description` do manifest são a documentação de referência do
módulo para quem lê o código. (No Apps do Odoo a página visível vem do
`static/description/index.html` — ver secção 2.)

- **`summary`**: uma frase clara com o efeito de negócio (não jargão técnico).
- **`description`**: texto estruturado, em Português, com as secções:
  1. **Para quem lê isto pela primeira vez** — resumo de 2-3 linhas do propósito.
  2. **Comportamento standard do Odoo** — o que o Odoo faz sem este módulo.
  3. **O que este módulo faz** — em bullets, do ponto de vista funcional.
  4. **Como funciona (técnico)** — o mecanismo (override, herança, etc.) e
     remissão para os docstrings do código para o detalhe.
  5. **Instalação** — como instalar e que configuração (se alguma) é precisa.
  6. **Guia de utilização** — orientado ao utilizador final, com:
     - *pré-requisitos* (definições/dados que têm de existir);
     - *passo a passo* concreto;
     - *exemplo prático* com valores ilustrativos quando ajudar a perceber;
     - *FAQ / resolução de problemas* (o que correu mal e porquê).
  7. **Manutenção / upgrade** — o que validar em upgrades (pontos frágeis).
  8. **Estado** — `ATIVO` ou `DEPRECADO — substituído por <módulo>`.
  9. **Referências** — paths do core/`vendor/odoo_src` e docs relevantes.

## 2. Página de Apps — `static/description/index.html`

**Obrigatório em módulos ativos.** O Odoo, quando renderiza a página
"Informação" de um módulo em Apps, dá prioridade ao ficheiro
`<modulo>/static/description/index.html` sobre o `description` do manifest
(ver `odoo/addons/base/models/ir_module.py::_get_desc`). Este ficheiro é lido
**ao vivo do disco** em cada acesso à página (campo computado não-armazenado),
o que significa que **a descrição refresca imediatamente em cada deploy**, sem
depender de upgrade do módulo nem de "Atualizar Lista de Aplicações".

Sem `index.html`, a descrição mostrada vem do campo `ir.module.module.description`
e só é refrescada por `update_list` (que pode ser bloqueado por cache de
manifests nos workers em execução). Em Odoo.sh, isto traduz-se em descrições
desatualizadas que não refrescam mesmo após upgrade — usar `index.html` evita
o problema de raiz.

Conteúdo: espelhar as mesmas secções do `description` do manifest (ver
secção 1), em HTML semântico. O Odoo aplica `html_sanitize` e reescreve
caminhos de imagens relativos para `/<modulo>/static/description/`.

## 3. Código Python

- **Docstring de módulo** (topo do ficheiro): propósito do ficheiro e, no
  ficheiro principal, o panorama do módulo (o "porquê" e o fluxo de dados).
- **Docstring de classe**: o que a classe faz e como se liga ao standard.
- **Docstring de método** (sobretudo em overrides): o que faz, porquê existe e
  o que muda face ao standard. Em overrides, dizer sempre o que se delega ao
  `super()`.
- **Comentários inline**: explicar o **porquê**, não o **quê**. Reservar para
  decisões não óbvias, armadilhas do Odoo e invariantes a preservar.
- **Constantes nomeadas** em vez de literais soltos (ex.: tipos de documento),
  com comentário a explicar o critério.

## 4. Vistas / XML

- Comentário no topo de cada vista herdada: o que acrescenta e a que vista
  standard.
- Comentário junto a cada `xpath` a justificar a **âncora escolhida** e a
  lógica de visibilidade/readonly.

## 5. Módulos deprecados

Quando um módulo é descontinuado:
- Marcar `'installable': False`.
- No `description`, substituir o conteúdo por:
  `Estado: DEPRECADO — substituído por <módulo/abordagem>. <1-2 linhas de contexto>.`
- Não investir em comentar o código a fundo.

## Checklist (Definition of Done de um módulo custom)

- [ ] `summary` com efeito de negócio claro.
- [ ] `description` com as 9 secções acima (ou nota de deprecado).
- [ ] `static/description/index.html` a espelhar a descrição (módulos ativos).
- [ ] Docstring de módulo no ficheiro Python principal.
- [ ] Docstrings de classe e de métodos (especialmente overrides).
- [ ] Comentários inline a explicar o "porquê" das partes não óbvias.
- [ ] Comentários nas vistas XML (intenção + âncora).
- [ ] Secção "Manutenção / upgrade" preenchida com os pontos frágeis.

## Exemplo de referência

O módulo [`pg_account_invoice_currency_date`](../pg_account_invoice_currency_date)
segue integralmente este padrão e serve de modelo para novos módulos.
