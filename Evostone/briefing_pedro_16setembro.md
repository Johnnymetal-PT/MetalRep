# Odoo — EVOSTONE · Ponto de situação para o regresso

**Para:** Pedro Coelho · **De:** equipa em substituição, 14–16 de setembro
**Projeto:** 316 · Odoo 18.0 Enterprise, Odoo.sh · fim planeado 31/10/2026

---

## 1. O que precisas de decidir hoje

**a) A certificação portuguesa não está no sistema — e o cliente já a pagou.**

O `l10n_pt` instalado é só plano de contas e impostos: três ficheiros de modelo,
sem assinatura de documentos, ATCUD, QR, SAF-T ou comunicação de guias à AT. O
«Odoo PT+» da Exo Software, comprado pelo cliente a 11/09 e já faturado, **não
está no repositório nem instalado**. São 48 módulos no repo e nenhum é esse.

Toda a fase correspondente está em Backlog: T2.2 (instalação), T2.3
(parametrização), T2.4 (layouts fiscais), T3.1 (teste de faturação/assinatura/
SAF-T), T4.2 (séries de produção). Tarefas 7045 a 7052.

É a decisão de maior consequência e é tua: quando entra, quem instala, e o que
se diz ao cliente sobre o prazo.

**b) O método de custeio foi alterado em produção hoje de manhã.**

```
Todos / Mercadoria    property_cost_method:  pcmp → average
2026-09-16 07:51      it.odoo@parametro.global
```

Conta partilhada da Parâmetro Global, pela interface web. Não foi o cliente. A
alteração é legítima em si, mas partiu a receção — expôs um defeito latente do
módulo do parceiro anterior, entretanto corrigido. **Enquanto houver 0
existências e 0 camadas de valorização é reversível; depois da primeira receção
real deixa de ser.** Precisa de confirmação de quem a fez.

**c) As horas no papel não são as horas reais.**

33,25 h de 36 alocadas. O último lançamento é de 14/09, com 1 h. Os três dias de
trabalho de 14, 15 e 16 estão praticamente por lançar, por indicação expressa de
se ignorar as horas nesta fase. As 2,75 h que sobram não existem.

**d) A estimativa de datas continua em dívida.** O cliente pediu-a a 08/09,
09/09 e 11/09. Foi-lhe dito que a resposta viria contigo.

---

## 2. O estado da relação com o cliente

A **Maria Dias (CFO)** respondeu ontem às 21:36 anotando o nosso email linha a
linha. Escreveu **«Não entendo nada do que escreveu»** e **«Não entendo o que
escreveu»** em dois pontos distintos.

Isso é um sinal sobre como escrevemos, não sobre ela. Os dois pontos em causa
eram a explicação dos obstáculos à receção e a explicação dos preços — ambos
escritos em vocabulário de sistema.

**Ela tem razão em quatro pontos, contra o que lhe foi dito:**

| o que ela escreveu | quem tinha razão |
|---|---|
| «Cada chapa não é um lote» | Ela. O sistema também modela assim — um lote agrupa várias chapas |
| «No mercado externo o artigo está isento de IVA» | Ela quanto ao facto; o mecanismo confirma-o |
| «Devem saber as obrigações que cada documento tem que ter impresso» | Ela. São obrigação legal, não pedido avulso |
| «Não podemos dar entrada nem saída de material sem isto estar resolvido» | Ela. É bloqueio operacional, não preferência |

Sobre os campos dos documentos, o que lhe foi dito — «desenvolvimento novo a
orçamentar» — está errado. O **Decreto-Lei 147/2003, art. 4.º n.º 4** exige
local de carga, local de descarga e data e hora de início do transporte. A
matrícula não consta do artigo mas é campo da comunicação à AT. E os três vêm no
módulo de certificação que o cliente já comprou. Orçamentá-los seria cobrar
outra vez.

Foi-lhe também dito «15 documentos». São **22** à medida.

---

## 3. O que foi entregue e está provado em produção

| | prova |
|---|---|
| Identidade nos 15 modelos de impressão | renderizado na P00002 real do cliente |
| Remetente do correio corrigido | `odoo.stg@pemaro.net` removido |
| Página de contactos do site | publicava morada da Matola, 3 telefones +258 e `geral@pemaro.net` |
| Sequências, alias, etiquetas NUIT→NIF | varrimento global a zero |
| Receção desbloqueada | 7 categorias, áreas do tipo de serviço, 3 encomendas |
| IVA de compra em 24 artigos | fatura de compra 500,00 → 615,00 |
| Fatura/NC/ND imprimiam com erro | campo `o.migration` do `account_MZ` |
| IBAN registado | `PT50 0018 0003 6905 9608 020 90`, impresso na fatura |
| Defeito do SVL na receção | `FAM/IN/00009 → done`, 322 existências, 160 chapas |

Bateria de validação: **21 verificações, 0 falhas**. Guiões em
`guioes/` (no repositório), detalhe todo no `PG_CONTEXT.md`.

---

## 4. O que não está provado, e porquê

Oito dos 22 documentos à medida — etiquetas de chapa, listagens de stock, lista
de preços de pedras, recibos — **não podem ser testados** enquanto não houver
chapas em stock e recibos emitidos. São precisamente os que o cliente vai usar
todos os dias.

A primeira receção real ainda não aconteceu. Tudo o que está provado foi-o em
transação revertida.

E a maior parte das alterações de configuração foi aplicada **diretamente em
produção**, sem ensaio prévio em staging: valorização, áreas de atuação, site,
sequências, etiquetas, impostos. Só as alterações de código seguiram o caminho
completo. O host de staging tem o id do build no nome e muda a cada publicação,
o que tirou o ensaio das últimas.

---

## 5. Por fazer

- **Sessão com a Maria** sobre a valorização das chapas. Destrava o stock e os
  preços ao mesmo tempo — é o nó de que dependem três queixas do cliente.
- **Segundo IBAN**, que ela anunciou.
- **Recalcular os impostos** das linhas da P00002 e P00001: ficam com `0% EX` e
  `23% EU G`, e o total não muda. Guião pronto.
- **Responder à Maria.** Já não é resposta técnica.
