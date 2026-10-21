# Tutorial — Email Marketing e Listas de Mailing (HMD)

> Como criar listas de mailing organizadas, enviar campanhas de email e acompanhar
> resultados no Odoo 18 (módulo **Email Marketing**, já instalado). Inclui uma
> introdução ao **Marketing Automation**. Serve também de guião para vídeo.

## As duas ferramentas

| Ferramenta | Para quê |
|---|---|
| **Email Marketing** | Enviar **campanhas de email** em massa a uma lista e ver aberturas/cliques |
| **Marketing Automation** | **Fluxos automáticos** (ex.: enviar email → esperar → seguir conforme a reação) |

Este guia foca o **Email Marketing** (uso diário) e termina com uma noção de
Marketing Automation.

---

## 1. Regra de ouro — separar marketing dos contactos comerciais

`IMPORTANTE` — As campanhas de marketing **não devem** ser enviadas para os
contactos operacionais/comerciais do dia-a-dia. Mantém **listas dedicadas a
marketing** (quem deu consentimento para newsletter), separadas dos clientes de
trabalho.

> Situação atual a arrumar: existem listas pouco segmentadas (ex.: uma `GERAL` com
> milhares de contactos e listas por domínio de email como `gmail`/`hotmail`). O
> ideal é consolidar em listas com **critério claro** (ex.: "Newsletter Clientes",
> "Newsletter Prospetos").

---

## 2. Criar e gerir uma lista de mailing

Em **Email Marketing → Listas de Mailing → Novo**:
1. Dá um **nome** com critério (ex.: `Newsletter Clientes 2026`).
2. Adiciona contactos de uma das formas:
   - **Manualmente** (Contactos da Lista → adicionar);
   - **Importar** de um ficheiro (Excel/CSV);
   - A partir dos **Contactos**: filtra os contactos desejados, seleciona e usa
     **Ação → Adicionar à lista de mailing**.

> Cada contacto de mailing tem o seu estado de **subscrição** e pode estar em
> **lista negra** (ver ponto 5).

---

## 3. Criar e enviar uma campanha (mailing)

Em **Email Marketing → Mailings → Novo**:
1. **Assunto** do email.
2. **Destinatários**: escolhe **Lista(s) de Mailing** (recomendado) ou um modelo
   filtrado (ex.: clientes que cumprem um critério).
3. **Desenhar o corpo**: usar um dos templates/blocos (arrastar e largar).
4. **Enviar um teste** primeiro (botão *Enviar Teste* para um email teu).
5. **Enviar** (ou **Agendar** para uma data/hora).

> Envia sempre um **teste** antes do envio real.

---

## 4. Acompanhar resultados

Depois de enviado, o mailing mostra:
- **Entregues**, **Aberturas**, **Cliques**;
- **Devoluções** (bounces) e **Cancelamentos de subscrição**.

Usa estes números para perceber o que funciona e limpar contactos inválidos.

---

## 5. RGPD / consentimento (obrigatório)

`IMPORTANTE` — Enviar marketing exige **consentimento** e **opção de cancelar**:
- Cada email inclui automaticamente a ligação de **cancelar subscrição**
  (*unsubscribe*).
- Contactos que cancelam ou que devolvem entram em **lista negra** (*blacklist*) e
  deixam de receber.
- **Não** reutilizar para marketing contactos recolhidos só para fins
  operacionais/contratuais sem base para tal.

---

## 6. Marketing Automation (introdução)

Em **Marketing Automation** podes criar **campanhas automáticas** com vários
passos e condições, por exemplo:
1. Alvo: uma lista ou um filtro de contactos.
2. Passo 1: enviar email de boas-vindas.
3. Espera 3 dias.
4. Condição: se **abriu** → enviar oferta; se **não abriu** → reenviar.

É útil para nutrição de prospetos sem trabalho manual. Recomenda-se começar pelo
Email Marketing simples e só depois desenhar automações.

---

## 7. Boas práticas

- **Listas com critério**, não listas "GERAL" gigantes.
- **Consentimento e opt-out** sempre respeitados.
- **Testar antes de enviar.**
- **Separar marketing dos contactos comerciais.**
- **Limpar** devoluções/inválidos regularmente.
- **Tudo standard** do Odoo — sem programação.

---

## 8. Resumo em 3 linhas

1. **Listas dedicadas a marketing**, separadas dos contactos comerciais.
2. **Mailings**: assunto → destinatários (lista) → testar → enviar.
3. Respeitar **consentimento/opt-out**; usar **Marketing Automation** para fluxos.
