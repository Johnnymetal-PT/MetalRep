# Tutorial — Pôr o WhatsApp a funcionar no Odoo (HMD)

> Passo-a-passo para configurar o WhatsApp Business e ligá-lo ao Odoo, para a HMD
> passar a **enviar e receber mensagens de clientes diretamente no Odoo**.
> Escrito para ser seguido sem conhecimentos técnicos. Ao longo do caminho vão
> aparecer alguns **códigos** — basta copiá-los e guardá-los; mais à frente o Odoo
> pede-os.

---

## O que vai conseguir fazer

No fim, a partir de uma **encomenda** ou da **ficha de um cliente** no Odoo, vai poder
enviar uma mensagem de WhatsApp, e as respostas do cliente chegam ao Odoo. Tudo fica
guardado no sítio certo, visível para a equipa.

`Antes de começar, é preciso saber:`
- O WhatsApp Business **tem um custo** (a Meta cobra por conversa). Confirmem
  internamente que querem avançar.
- É preciso um **número de telefone dedicado** a este WhatsApp, que **não esteja já a
  ser usado** no WhatsApp normal de um telemóvel. Se já tiver WhatsApp, libertem-no
  primeiro ou escolham outro número.
- A parte que **demora mais** é a aprovação da Meta (Passos 7 e 8) — pode levar dias a
  semanas e não depende de nós. Convém começar cedo.

> Vão precisar de uma conta de Facebook para gerir tudo isto. Use de preferência uma
> conta ligada à empresa, não a pessoal de alguém que possa sair.

---

# PARTE A — Na Meta (criar a conta de WhatsApp)

## Passo 1 — Criar a conta de empresa na Meta

1. Ir a **business.facebook.com** e iniciar sessão.
2. Criar a conta de empresa (carteira de negócio) com os **dados da HMD**: nome,
   website e email da empresa.
3. Adicionar como **administradoras** as pessoas que vão gerir isto (ex.: Nina e
   Mónica), para não ficar dependente de uma só.

---

## Passo 2 — Ativar o WhatsApp

1. Ir a **developers.facebook.com** e iniciar sessão com a mesma conta.
2. **Criar uma aplicação** (botão *Criar app*) e, quando perguntar o tipo, escolher
   **Empresa / Business**.
3. Dentro da aplicação, na lista de produtos, **adicionar o WhatsApp**.

> Ao adicionar o WhatsApp, a Meta cria automaticamente a vossa conta de WhatsApp
> Business. Vai aparecer um ecrã de configuração — é onde continuamos.

---

## Passo 3 — Registar o número de telefone

1. No ecrã de configuração do WhatsApp, **adicionar o número de telefone** escolhido.
2. A Meta envia um **código de confirmação** (por SMS ou chamada) — introduzir esse
   código para confirmar o número.

`Lembrete:` o número tem de estar livre (sem WhatsApp normal associado).

---

## Passo 4 — Criar a chave de acesso permanente

O Odoo precisa de uma **chave** para falar com a Meta em vosso nome. A chave que
aparece logo no ecrã **só dura 24 horas** (serve para testes), por isso é preciso
criar uma **permanente**:

1. Em **Definições do Negócio (Business Settings) → Utilizadores → Utilizadores de
   Sistema**, criar um novo utilizador de sistema.
2. Gerar uma **chave de acesso (token)** para esse utilizador e, quando pedir
   permissões, marcar as duas relacionadas com **WhatsApp** (gestão e envio de
   mensagens).
3. **Copiar e guardar** essa chave num sítio seguro — só é mostrada **uma vez**.

---

## Passo 5 — Guardar os códigos para o Odoo

Antes de passar ao Odoo, tenham à mão estes **cinco dados** (estão todos nos ecrãs da
aplicação Meta, em *Definições → Básico* e no ecrã do WhatsApp). Não é preciso
perceber o que cada um faz — só copiá-los:

| O que copiar | Onde está (mais ou menos) |
|---|---|
| Identificador da aplicação (*App ID*) | Definições → Básico |
| Segredo da aplicação (*App Secret*) | Definições → Básico |
| Identificador da conta WhatsApp (*Account ID*) | Ecrã do WhatsApp |
| Identificador do número (*Phone Number ID*) | Ecrã do WhatsApp |
| A **chave de acesso** do Passo 4 | (a que guardaram) |

> Sugestão: colem os cinco num documento/bloco de notas só vosso, identificados,
> para os ter prontos no passo seguinte.

---

# PARTE B — No Odoo (ligar e usar)

## Passo 6 — Criar a ligação no Odoo

No Odoo, ir a **WhatsApp → Configuração → Contas WhatsApp Business → Novo** e
preencher com os **cinco dados** que copiaram no Passo 5. Indicar também **quem deve
ser avisado** quando chegarem respostas (pelo menos uma pessoa).

Ao gravar, o Odoo mostra **dois valores próprios** — um **endereço (URL)** e um
**código de verificação**. Vão ser precisos no passo seguinte; deixem este ecrã à
mão.

---

## Passo 7 — Ligar a receção de respostas

Para as respostas dos clientes chegarem ao Odoo, é preciso "apresentar" o Odoo à Meta:

1. Voltar à aplicação Meta, ao ecrã do WhatsApp, à secção de **Webhook** (receção de
   mensagens).
2. Colar lá o **endereço (URL)** e o **código de verificação** que o Odoo mostrou no
   Passo 6.
3. Ativar a receção de **mensagens**.

`Um pedido à equipa de informática:` para isto funcionar, o servidor do Odoo da HMD
tem de estar **acessível pela internet de forma segura**. Peçam ao vosso IT para
confirmar este ponto — sem isso, conseguem enviar mas **não recebem** respostas. Se
precisarem, ajudamos a validar.

---

## Passo 8 — Preparar as mensagens (templates)

A Meta tem uma regra: para **começar** uma conversa, só se podem usar **mensagens
aprovadas por ela** (chamadas *templates*).

1. Pensar nas mensagens que a HMD quer poder enviar, por exemplo:
   - confirmação de orçamento ou encomenda;
   - aviso de envio / entrega;
   - pedido de uma confirmação ou documento.
2. Criar essas mensagens (no Odoo, em **WhatsApp → Templates**, ou no painel da Meta) e
   **submetê-las à aprovação**. Podem ter espaços que se preenchem sozinhos (nome do
   cliente, número da encomenda…).
3. No Odoo há o botão **Sincronizar Templates**, que vai buscar à Meta as mensagens já
   aprovadas.

> A Meta pode demorar e até recusar mensagens que pareçam publicidade. Por isso:
> usem linguagem simples e clara, submetam **cedo** e preparem **mais do que uma**.

---

## Passo 9 — Validar a empresa na Meta

Para sair do modo de testes e poder escrever a clientes a sério, a Meta pede uma
**verificação do negócio**: confirmar que a HMD é uma empresa real.

- Em **Definições do Negócio → Centro de Segurança**, submeter os **documentos da
  empresa** quando forem pedidos (ex.: certidão e comprovativo de morada).

Enquanto isto não estiver feito, só dá para enviar para muito poucos números de teste.

---

## Passo 10 — Testar

No ecrã da conta WhatsApp no Odoo, carregar em **Testar Ligação (Test Connection)**.
Só se deve usar com clientes reais quando este teste ficar **verde**.

---

## Como usar no dia-a-dia

### Enviar uma mensagem
1. Abrir a **encomenda** ou a **ficha do cliente** no Odoo.
2. No painel de mensagens (à direita), escolher **enviar por WhatsApp**.
3. Escolher a mensagem aprovada e confirmar — o Odoo já preenche o nome do cliente, o
   número da encomenda, etc.
4. Enviar. A conversa fica guardada na **própria encomenda/cliente**.

### Receber respostas
Quando o cliente responde, a mensagem **entra no Odoo** e as pessoas indicadas são
avisadas. Fica tudo no mesmo sítio, visível para a equipa.

### A regra das 24 horas
- Depois de um cliente vos escrever, podem responder com **texto livre durante 24
  horas**.
- Passadas as 24 horas, ou para **iniciar** uma conversa do zero, só com uma das
  **mensagens aprovadas** (Passo 8).

---

## Lista de verificação (pela ordem certa)

1. ☐ Confirmar internamente que avançam (há um **custo por conversa**).
2. ☐ Escolher o **número dedicado** (livre de WhatsApp normal).
3. ☐ Criar a **conta de empresa na Meta** (Passo 1).
4. ☐ **Ativar o WhatsApp** e **registar o número** (Passos 2 e 3).
5. ☐ Criar a **chave de acesso** permanente e guardar os **5 códigos** (Passos 4 e 5).
6. ☐ **Ligar no Odoo** e **a receção de respostas** (Passos 6 e 7) — com o IT a
   confirmar o acesso ao servidor.
7. ☐ **Preparar e submeter as mensagens** à Meta — quanto mais cedo melhor (Passo 8).
8. ☐ **Validar a empresa** na Meta (Passo 9).
9. ☐ **Testar a ligação** (Passo 10) e fazer um primeiro envio.

---

## Uma nota sobre o custo

A Meta cobra **por conversa** (não por mensagem) e o valor varia com o tipo de
mensagem e o país. É um custo de operação a contar todos os meses. Em caso de dúvida
sobre valores, falem connosco antes de avançar.

---

> Estamos disponíveis para acompanhar qualquer um destes passos convosco, em especial
> a primeira ligação ao Odoo (Passos 6 e 7). Não têm de fazer tudo sozinhas.
