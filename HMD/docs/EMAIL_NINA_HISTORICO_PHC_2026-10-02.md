---
assunto: Histórico de faturação PHC no Odoo — já disponível; falta escolher como carregar
para: nina@hmdfurniture.com
---

Olá Nina,

Retomo o tema do histórico de faturação do PHC, de que falámos na reunião de 27/07. O email que
enviámos a 19/08 chegou durante as vossas férias e ficou sem seguimento.

Entretanto avançámos com a parte técnica, que já está **ativa no vosso Odoo**. Na ficha de cada
cliente, no separador **Vendas e Compras**, há agora dois campos novos:

- **Volume Histórico PHC** — o total faturado ao cliente no PHC até 31/12/2025;
- **N.º Cliente PHC** — o número do cliente no PHC, para cruzar os dois sistemas.

Ao contrário das notas, estes campos pesquisam-se e ordenam-se. Na lista de contactos é possível
mostrar a coluna do volume, ordenar os clientes pelo valor histórico ou usar o filtro **Com histórico
PHC**. A faturação a partir de 01/01/2026 continua a ser a das faturas do Odoo, por isso os dois
períodos não se misturam. Também confirmámos que não há saldos em aberto a importar: o Odoo só começa a
faturar em janeiro de 2026.

Para carregar os valores, precisamos que nos diga como prefere avançar:

- **Opção A — a Parâmetro Global faz a carga.** O Sérgio envia-nos o ficheiro e nós cruzamos os
  clientes com o Odoo, carregamos os valores e devolvemos a lista dos que não conseguirmos
  identificar.
- **Opção B — o Sérgio faz a carga, com o nosso apoio.** Preparamos o modelo de importação e um guia
  no Conhecimento, e fazemos uma sessão de cerca de 30 minutos com ele. Fica com autonomia para
  futuras atualizações.

Seja qual for a opção, o ficheiro do Sérgio precisa de ter, por cliente:

1. o **número de cliente no PHC** (NR_CLIENTE);
2. o **nome**;
3. o **NIF**, quando existir;
4. o **total faturado até 31/12/2025**.

O número de cliente é o que garante o cruzamento. Hoje só cerca de 5% dos clientes no Odoo têm NIF,
por isso o nome sozinho não chega.

Pode responder-nos com a opção A ou B e, se já estiver pronto, com o ficheiro em anexo?

Com os melhores cumprimentos,

**Equipa Odoo — Parâmetro Global**
