# Tutorial — Criar um projeto de cliente a partir do modelo (HMD)

> Como abrir um **novo projeto de cliente** a partir do projeto-modelo da HMD, e
> como **manter** esse modelo. Evita montar as fases e tarefas de raiz de cada vez.
> Serve também de guião para o vídeo curto HMD-specific.

## O projeto-modelo da HMD

Existe um projeto chamado **`Client Project Template`** que funciona como **molde**:
tem as **fases** e as **tarefas-tipo** já organizadas (resultado da reformulação de
fases — 3 fases globais + fases de tarefa). Em vez de criar um projeto vazio,
**duplica-se** este modelo.

> Por agora a criação é **manual** (duplicar o modelo). A criação automática ao
> qualificar um lead no CRM está prevista numa fase seguinte (tarefa P4).

---

## Passo 1 — Duplicar o modelo

1. Vai a **Projeto** e abre a lista de projetos.
2. Localiza **`Client Project Template`**.
3. Duplica-o:
   - no **kanban**, no cartão do projeto, menu **⋮ → Duplicar**; ou
   - abrindo o projeto, menu de **ações (⚙)** → **Duplicar**.

A duplicação cria um novo projeto **com as fases e tarefas do modelo**.

---

## Passo 2 — Adaptar o novo projeto

No projeto duplicado:
1. **Renomeia** para o cliente/obra (ex.: `Projeto — Cliente X`).
2. Define o **cliente** e, se aplicável, **datas** e **responsáveis**.
3. Ajusta/remove as tarefas que não se apliquem a este cliente.

> O grosso do trabalho já vem feito do modelo — só personalizas.

---

## Passo 3 — Trabalhar nas fases

O projeto já traz a estrutura de **fases** definida. Move as tarefas pelas fases
(kanban) à medida que avançam. Não é preciso recriar fases.

---

## Manter o modelo (importante)

Quando algo deve mudar **para todos os projetos futuros**, edita o próprio
**`Client Project Template`** (acrescenta/edita tarefas-tipo, ajusta fases). As
**duplicações seguintes** passam a herdar essa alteração.

> Regra: alterações pontuais fazem-se no projeto do cliente; alterações que devem
> valer para todos fazem-se **no modelo**.

---

## Boas práticas

- **Um modelo limpo:** mantém o `Client Project Template` como referência, sem
  dados de clientes reais.
- **Duplica, não copies à mão:** garante que não esqueces tarefas.
- **Nome consistente** dos projetos de cliente (ex.: `Projeto — <Cliente>`).
- **Tudo standard:** duplicação é nativa do Odoo, sem programação.

---

## Resumo em 3 linhas

1. **Duplicar** o projeto `Client Project Template`.
2. **Renomear** + definir cliente/datas e ajustar tarefas.
3. Mudanças para **todos os futuros** projetos → editar **o modelo**.
