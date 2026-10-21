---
assunto: EVOSTONE — contabilidade portuguesa: dados que precisamos da sua parte
para: Maria Dias — endereço a confirmar
---

Boa tarde Maria,

Sou o Bruno Pinheiro, da Parâmetro Global, responsável pela implementação do Odoo na EVOSTONE. O Rui indicou-nos que a parte contabilística deve ser trabalhada consigo.

Escrevo-lhe com quatro pontos concretos. Deixo primeiro o enquadramento, para que nenhum deles apareça sem contexto.

**Onde estamos**

A base de dados que nos foi entregue trazia a contabilidade de Moçambique: o plano de contas moçambicano, taxas de IVA a 16%, 5% e 0%, e diários associados a bancos moçambicanos. A empresa está já configurada em euros e com Portugal como país, mas a estrutura contabilística por baixo continua a ser a de origem.

É por isso que, por exemplo, as encomendas de compra saem sem IVA: não existe nenhuma taxa portuguesa na base.

**O que vamos instalar — já decidido, não precisa de decisão sua**

- A localização portuguesa do Odoo: plano de contas SNC, taxas de IVA, posições fiscais e diários. Testámo-la já num ambiente de ensaio, com a base real, e confirmámos o resultado: 2224 contas, 211 grupos de contas, 42 taxas de imposto e 8 posições fiscais.
- A solução da EXO sobre esse plano, para a facturação certificada: SAF-T, séries e ATCUD.

Não lhe pedimos que escolha a solução — está escolhida. O que precisamos são os dados abaixo.

**1. O plano de contas: NC-ME ou SNC Base?**

Confirme-nos, por favor, se a EVOSTONE está actualmente a aplicar a **NC-ME (Microentidades)** ou o **SNC Base / Pequenas Entidades**.

Para que saiba o peso da pergunta: as contas são as mesmas nos dois casos. O que a sua resposta determina é o modelo de Balanço e de Demonstração de Resultados que instalamos. Por isso este ponto não nos atrasa — avançamos com todo o resto e instalamos o modelo certo quando nos disser.

**2. O prefixo das séries de facturação**

Este ponto exige uma decisão sua, e não tem alternativa.

Pelo Decreto-Lei n.º 28/2019, não é legalmente possível manter o prefixo de série que era usado no software anterior. A criação de uma série num software novo exige a comunicação de raiz à Autoridade Tributária, associada ao certificado da nova aplicação, para a emissão de um novo código de validação (ATCUD). Reutilizar um prefixo antigo geraria conflitos de numeração no ficheiro SAF-T.

Precisamos que defina um prefixo novo. A convenção que usamos habitualmente, e que sugerimos:

- **FT 26/** para facturas
- **FR 26/** para facturas-recibo
- **FS 26/** para facturas simplificadas

O **26** associa-se ao ano de arranque. Se preferir outra referência — por exemplo **FTEV/**, com sigla da empresa — basta indicar-nos.

**3. Credenciais AT para a comunicação das séries**

A facturação certificada exige comunicar as séries à AT e obter o código ATCUD. Para isso necessitamos de uma de duas vias:

- **Preferencial** — um subutilizador do Portal das Finanças com a permissão «Comunicação e Gestão de Séries por Webservice (WSE)», com o respectivo utilizador e senha.
- **Alternativa** — caso prefiram registar as séries manualmente no Portal das Finanças, os códigos de validação que a AT devolve, por série.

**4. Contas bancárias portuguesas**

As três contas bancárias registadas na base são moçambicanas: BCI, BIM e Moza. Indique-nos, por favor, as contas bancárias portuguesas da EVOSTONE e a conta do plano a associar a cada uma, e configuramos os diários correspondentes.

**Dois pontos que já apurámos, e que só precisam da sua confirmação**

- **Número de contribuinte** — vamos registar o NIF **516617770** na empresa. A base tinha ainda o NUIT moçambicano. Diga-nos se o número não for esse, porque uma factura certificada não se corrige depois de emitida.
- **Imobilizado** — existem nove elementos de imobilizado herdados do sistema anterior. Com a passagem da base para euros, os montantes de aquisição mantiveram os valores de origem e precisam de ser reexpressos. Enviamos-lhe a lista dos nove, para que indique o valor de aquisição em euros de cada um.

Depois de instalado o plano português ficam **seis categorias de artigo** a precisar de conta de compra e de venda. Já lhe levamos uma proposta para cada uma, em vez de lhe pedirmos que a construa: no plano moçambicano a distinção entre nacional e estrangeiro estava dentro da própria conta, e no SNC essa distinção é feita pela posição fiscal, pelo que as seis se resolvem com duas contas de compra e duas de venda. Basta-nos a sua confirmação. Verificámos também que nenhuma das oito localizações de armazém tem conta de valorização associada, pelo que não há nada a decidir aí.

**Um pedido quanto ao calendário**

A substituição do plano de contas só é possível de forma limpa enquanto não existirem lançamentos contabilísticos registados. Neste momento não existe nenhum, e isso mantém a operação simples e reversível. A partir da primeira factura emitida, passa a exigir migração manual de contas e de saldos.

Por isso pedimos que, até termos o plano português instalado, **não sejam emitidas facturas de cliente nem de fornecedor**. O restante trabalho no sistema — contactos, orçamentos, encomendas, recepções de mercadoria — pode prosseguir sem qualquer restrição, e verificámos que nada disso gera lançamentos.

O Rui indicou-nos **15 de Setembro** como data de início de facturação. Os pontos 2 e 3 são os que condicionam essa data, porque a comunicação das séries à AT tem prazo próprio.

Fico ao dispor para uma chamada, se preferir tratar isto por telefone.

Com os melhores cumprimentos,
Bruno Pinheiro
