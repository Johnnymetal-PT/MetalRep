# TPL_MIGRACAO_CONTABILIDADE_MEIO_ANO.md

> Template executável: **passar a contabilidade de um cliente para o Odoo a meio do ano**, com o
> histórico do ano corrente importado do SAF-T de contabilidade do sistema antigo, em Odoo com a
> localização Exo PT+.
> Fonte de verdade deste template: artigo Odoo do workspace `pg_doc_templates`.
> Se for editado localmente, **republicar no Odoo** para não perder no próximo pull.

## Finalidade

Começar a contabilidade no Odoo a meio do ano obriga a trazer os movimentos do ano até à data de
corte, e não só os saldos. Os movimentos têm de entrar de forma que o Odoo e as declarações da Exo
os reconheçam: balancete igual ao do sistema antigo, extratos de clientes e fornecedores certos,
declaração periódica, Balanço, Demonstração de Resultados, IES e Modelo 10 calculados a partir deles.

Importar o ficheiro é a parte fácil. O trabalho está em tudo o que a importação não faz e em provar,
antes de produção, que o resultado bate com a contabilidade do cliente. Este template foi extraído
da migração da Reckon.AI (Odoo 19, Exo PT+, SAF-T Sage de janeiro a julho de 2026, 1 961
lançamentos, sete ensaios até à validação da contabilidade). Não é teoria.

## Quando usar

Disparar quando o cliente quiser começar a contabilidade no Odoo **com o ano já em curso**:
"migrar a contabilidade", "importar o SAF-T de contabilidade", "trazer o histórico do ano",
"passar a contabilidade do PHC/Sage/Primavera para o Odoo".

**Quando não usar:** se o arranque puder ser a 1 de janeiro, não se importa histórico: basta o
lançamento de abertura com os saldos do balancete de 31/12. É muito mais simples, e é o que se
recomenda ao cliente (Passo 0).

---

## Passo 0 — Meio do ano ou ano novo? [GATE]

Antes de orçamentar, pôr a decisão ao cliente e à contabilidade com os custos à vista:

| | Arranque a 1 de janeiro | Arranque a meio do ano |
|---|---|---|
| O que se importa | saldos de abertura | saldos de abertura **e** todos os movimentos do ano até à data de corte |
| Ensaios | um | vários, até a contabilidade validar |
| Declarações do ano | começam limpas | dependem de ligar o histórico a impostos, grelhas e taxonomia |
| Risco | baixo | médio: o que não se ensaiar aparece em produção |

Se o cliente escolher o meio do ano, registar a decisão e quem a tomou. É o tipo de decisão que
depois se discute quando aparecem os primeiros problemas.

## Passo 1 — Pedir ao cliente e à contabilidade [GATE]

Pedir tudo de uma vez, por escrito, com o motivo de cada item:

1. **SAF-T de contabilidade** do ano corrente até à data de corte, **o ficheiro original** do
   sistema antigo (nunca uma versão convertida), com o `TaxonomyCode` das contas preenchido.
   Confirmar que é o definitivo: um SAF-T novo obriga a voltar a ensaiar.
2. **Balancetes** a 31/12 do ano anterior e à data de corte, para comparar.
3. **Plano de contas comentado:** que subcontas se juntam, que contas ficam próprias. As contas com
   consequência fiscal (tributação autónoma, IVA não dedutível, gastos não aceites) ficam sempre
   com conta própria, mesmo sem movimento.
4. **Grelhas por subconta:** o campo da declaração periódica e a linha do Anexo L de cada subconta
   de IVA, de bases e de rendimentos/gastos (a "taxonomia" que a contabilidade usa).
5. **Decisões da contabilidade** que o ficheiro não traz:
   - natureza da alteração no capital próprio dos lançamentos da classe 5 (abertura, aplicação do
     resultado, ações próprias, aumentos de capital);
   - cliente de cada subconta de diferimentos e acréscimos (27x, 28x), se a contabilidade as tiver
     por cliente;
   - entidade das retenções na fonte (24x) que o SAF-T não identifique. Só as retenções de
     rendimentos que vão na Modelo 10 (trabalho independente, rendas) levam NIF; o trabalho
     dependente vai na DMR do programa de salários e os pagamentos ao Estado não levam NIF;
   - contas de apuramento do IVA (a pagar, a recuperar, reembolsos) e as subcontas das retenções.
6. **SAF-T de faturação** do sistema antigo para os meses entre a data de corte e o arranque.
7. **Identificador das séries documentais** e quem tem as credenciais da AT.
8. **Acessos:** quem da contabilidade entra no Odoo, com que perfil, e para que email vão as
   notificações. Se é a contabilidade a fechar os meses, precisa de Accounting / Administrator
   (só esse perfil muda a data de bloqueio).
9. **Bancos:** para cada conta bancária, o IBAN, a moeda e a conta da contabilidade onde fica o
   saldo à data de corte. Serve para criar os diários antes de ligar os bancos (Passo 9).

## Passo 2 — Ambiente de ensaio

1. **Cópia neutralizada de produção**, descartável. Num projeto Odoo.sh à parte ou numa staging;
   nunca na base de testes onde o cliente trabalha.
2. **Mesma versão da Exo** que vai para produção. Se for preciso atualizar o submódulo da Exo em
   produção, o ensaio corre já na versão nova e o push faz parte do dia da passagem.
3. **Empresa certa:** ano fiscal a 31/12 e periodicidade da declaração (mensal ou trimestral) iguais
   às do cliente. Com o ano fiscal errado, os nomes dos lançamentos ficam errados e não se corrigem.
4. **Módulos da Exo:** `ptplus_accounting_tax_statement` (declaração periódica, recapitulativa,
   Anexos R e L), `ptplus_accounting_reports` (Balanço, DR, balancete, IES),
   `ptplus_accounting_efatura` e `ptplus_reports_withholding` (Modelo 10, Modelo 30, declaração
   mensal de retenções). Instalam-se **depois** da importação e do lançamento, como nos ensaios
   (Passo 8). Confirmar depois da instalação que as definições das declarações ficaram na empresa
   do cliente e não na empresa de criação da base; se ficaram nesta, mudam-se só essas
   (`l10n_pt.account.statement`), e não os impostos ou parceiros dessa empresa.

## Passo 3 — Tabela de correspondência do plano de contas

Uma tabela, por conta do SAF-T: código antigo, conta final no Odoo, operação. As operações são:

- **recodificar:** a conta passa um-para-um para outro código;
- **juntar:** várias subcontas numa conta final (muda-se a conta das linhas; o assistente "Juntar
  contas" do Odoo não serve para isto);
- **reclassificar:** linhas que caíram numa conta certificada com o mesmo código e outro sentido;
- **manter:** conta própria (as de consequência fiscal, as pedidas pela contabilidade).

A tabela gera também o **saldo esperado** de cada conta final à data de corte, somando os saldos de
fecho do SAF-T. É contra isto que se verifica.

## Passo 4 — Grelhas e impostos

1. **Grelhas por subconta** a partir da taxonomia da contabilidade, convertidas para as grelhas da
   Exo (declaração periódica e Anexo L). Ficam de fora os diários de apuramento (IVA, existências,
   retenções): transferem saldos no fim do período e anulariam os campos.
2. **Impostos nas linhas.** A declaração periódica da Exo só conta linhas ligadas a um imposto: a
   linha de IVA à repartição do imposto, a base ao imposto. As linhas importadas vêm só com a
   conta. Liga-se cada linha de IVA ao imposto da Exo com a mesma grelha e a mesma taxa, e cada base
   ao imposto do mesmo lançamento.

## Passo 5 — Sequência do ensaio

Cada passo corre sobre os lançamentos ainda em rascunho, por esta ordem:

| Passo | O que faz | Porquê |
|---|---|---|
| importar, ignorar, gravar | importação da Exo; marcar Ignorar nas atualizações de contas, grupos e parceiros que já existem | a atualização reescreve designações certificadas e fichas de produção |
| fundir fichas | um NIF, uma ficha, com a fusão de contactos do Odoo; antes, corrigir os NIF errados que a contabilidade indicar | o importador cria outra ficha sempre que o NIF vem escrito de outra forma (espaço, com ou sem prefixo); produção pode já ter duplicados seus |
| parceiros em falta | criar as entidades que o SAF-T não identifica | sem entidade não há NIF por onde ligar |
| parceiros | parceiro de cada linha pela entidade da subconta; nas retenções a crédito de trabalho independente e rendas, pelo lançamento; nos diferimentos, pela tabela da contabilidade; tirar o parceiro às retenções que não levam NIF | o importador põe a entidade do cabeçalho em todas as linhas dos lançamentos de bancos agregados |
| faltas | recriar os lançamentos que a importação recusou | ver o motivo de cada recusa |
| grelhas, impostos | Passo 4 | |
| recodificar, juntar, reclassificar | Passo 3 | depois de grelhas e impostos, para as linhas os levarem consigo |
| abertura | lançamento de abertura a 31/12 do ano anterior, com parceiro nas contas de terceiros e nos diferimentos | |
| limpar | designações finais; apagar contas e grupos do sistema antigo sem movimentos | |
| extratos | contas de outros devedores e credores como "não comerciais"; Razão Geral com filtro de parceiro | a contabilidade consulta cada conta em separado (clientes, adiantamentos) |
| taxonomia | taxonomia SNC de cada conta, a partir do SAF-T | o Balanço, a DR e a IES da Exo somam por ela; sem ela saem a zeros |
| configuração fiscal | grupos do IVA com as contas de apuramento; impostos de retenção nas subcontas e fora do apuramento do IVA | sem contas nos grupos, o fecho em Tax Return dá erro; a Exo traz as retenções marcadas para o apuramento do IVA |
| natureza | natureza da alteração no capital próprio nas linhas da classe 5 | a Exo não lança a classe 5 sem ela |
| bloqueio, lançar, bloqueio | baixar o bloqueio para a véspera da abertura, lançar por ordem de data, pôr o bloqueio na **data de corte** | a contabilidade lança os meses depois do corte, e a sincronização bancária começa no dia a seguir ao bloqueio; repor um bloqueio posterior que o cliente tivesse bloqueava esses meses |

**Toda a escrita em linhas que já tenham impostos passa `skip_invoice_sync`.** Sem isso o Odoo
recalcula o IVA: refaz as linhas de IVA sem as grelhas, cria linhas de equilíbrio automático e, num
lote que falhe, só o último é revertido. A base afetada não se repara; ensaia-se numa staging nova.

## Passo 6 — Verificações [GATE]

Antes e depois de lançar, e o ensaio pára se alguma falhar:

1. **Saldos:** cada conta final igual ao saldo esperado da tabela (BATE CERTO).
2. **Parceiros:** cada linha de clientes e fornecedores com a entidade da sua subconta no SAF-T
   (tem de dar 0 diferentes).
3. **IVA:** cada linha de IVA existe no SAF-T com os mesmos valores e descrição (0 refeitas) e não
   há linhas de equilíbrio automático (0).
4. **Fichas:** nenhum NIF com mais de uma ficha (0).
5. **Retenções:** as retenções da Modelo 10 com parceiro e nenhuma retenção sem NIF com parceiro.
6. **Contagens:** linhas com grelha; linhas de diferimentos sem parceiro.

A verificação compara com o SAF-T, não com o Odoo: um erro que o Odoo produza sozinho não se
apanha comparando o Odoo consigo mesmo.

## Passo 7 — Validação com a contabilidade [GATE]

Dar à contabilidade um utilizador na base de ensaio e pedir que confira, com os seus mapas:

- **declaração periódica** de cada trimestre do ano (Exo, filtro "Auxiliary Fields" para ver o
  campo 7 calculado);
- **Balanço e Demonstração de Resultados da Exo** (Reporting › Portugal), não os relatórios
  financeiros do Odoo: são dois relatórios diferentes no menu, e a contabilidade usa os da Exo;
- **extratos de clientes e fornecedores** contra o balancete, subconta a subconta;
- **fichas de parceiro** duplicadas ou em falta.

Cada correção volta ao Passo 5 numa staging nova. Não se corrige à mão na base de validação:
editar um lançamento importado (repor em rascunho, mudar, lançar) pode tirar a grelha à linha de
IVA sem se notar.

Diferenças de apresentação a esperar e a perguntar: subcontas de outros devedores e credores com
saldo de sinal contrário (o Odoo apresenta cada uma pelo seu saldo) e empréstimos cuja taxonomia
no SAF-T não coincide com a classificação no balanço da contabilidade.

## Passo 8 — Dia da passagem

Princípio: tudo o que se desfaz com o backup vem antes do que não se desfaz (registo das séries na
AT). E em produção só corre o que correu igual no ensaio, pela mesma ordem.

0. Ensaio final numa staging nova, com o código final, de uma só vez. Só se avança com o Passo 6
   todo a 0.
1. **Backup manual** de produção: Odoo.sh › Branches › main › Backups › **Create Backup**, com
   comentário. É o ponto de reposição (botão Restore). O download do dump é opcional e não o
   substitui.
2. Empresa: ano fiscal e periodicidade. Confirmar também a data de bloqueio que o cliente tem.
3. Versão da Exo: push do submódulo, se for o caso, e acompanhar o build até às versões do ensaio.
4. Verificação prévia (grelhas, impostos, contas, estado).
5. Passo 5 em produção, com as mesmas verificações e o bloqueio final na data de corte.
6. Módulos da Exo (Passo 2) e definições das declarações na empresa do cliente.
7. Utilizador da contabilidade, só na empresa do cliente, com o email real para as notificações.
   O convite para a palavra-passe segue para esse email.
8. Conferir: declaração periódica de um trimestre, Balanço e DR da Exo, Razão Geral por parceiro.
9. Configuração final: diários de banco (Passo 9) e contas por defeito dos diários de vendas.
10. Exo: **Certification Service Backend = Exo Software** (o "Test" não certifica) e código de
    subscrição, gravar e atualizar. A validade aparece sem ano quando é do ano corrente.
11. Segundo backup.
12. Séries na AT (não se desfaz): numeradores com o prefixo que dá o identificador combinado,
    sem saltos (`no_gap`). A Guia de Transporte precisa do filtro das operações de entrega
    (Picking Type Filter); as séries de faturação não. **Registar primeiro uma série como teste**
    (ex.: Pró-forma): se registar, a subscrição e as credenciais da AT estão bem. Uma série
    registada com erro pode cancelar-se enquanto não tiver documentos.
13. Aviso ao cliente, com a data a partir da qual se fatura no Odoo e o sistema antigo deixa de
    faturar.

## Passo 9 — Depois da passagem

- **Bancos.** Ao ligar uma conta do banco, o Odoo usa um diário de banco com o mesmo IBAN e moeda;
  se não houver, cria um diário com uma **conta contabilística nova e vazia**, fora da conta onde
  ficou o saldo à data de corte. Antes de ligar (ou antes de associar ligações já feitas), criar um
  diário por conta bancária, com o IBAN, a moeda e a conta certa. A sincronização começa no último
  extrato do diário ou, sem extratos, no dia a seguir ao bloqueio. Os bancos dão 60 a 90 dias de
  histórico: fazer cedo, ou carregar os primeiros meses por ficheiro.
- Importar o SAF-T de faturação dos meses entre a data de corte e o arranque (ensaiado antes).
- Modelo 10 do período importado: as retenções importadas não estão ligadas a um imposto de
  retenção; ligam-se e ensaiam-se antes da entrega, numa janela com backup.
- Base de testes do cliente reconstruída a partir de produção.

## O que este template não leva, e é deliberado

- **Salários:** ficam no programa de salários do cliente até ao fim do ano; lançam-se por
  importação ou à mão. O Odoo não tem processamento de salários para Portugal.
- **Correção do passado:** declarações já entregues não se refazem. O que o cliente corrigia à mão
  nas declarações fica como está; daqui em diante usa as grelhas nas linhas.
- **Inventário valorizado:** os saldos de existências entram pela contabilidade; o stock do Odoo é
  outra migração (`TPL_MIGRACAO_DADOS_ODOO.md`).

## Referências

- **Motor:** `.pg_framework/scripts/pg_migracao_contabilidade/` — `correr.py` (sequência completa,
  ensaio e produção, com `--desde` para retomar), `motor.py` (cada passo), `verificar.py` (contra o
  SAF-T). O `README.md` da pasta tem a configuração do projeto (JSON) e o contrato das tabelas que
  os preparadores de cada cliente produzem. Os preparadores (ler o Excel do plano, a taxonomia em
  PDF) ficam no projeto, porque dependem dos ficheiros que cada cliente envia.
- **Caso de referência:** repositório `reckon.ai` — configuração em
  `docs/plano_contas/migracao_contabilidade.json`, preparadores em `docs/plano_contas/`, passagem
  executada a 06/10/2026 em `docs/plano_contas/GUIAO_REPLICAR_PRODUCAO.md`. O motor foi provado com
  um ensaio completo que deu os mesmos números da produção.
- Aprendizagens: `.pg_framework/docs/PG_PROJECT_LEARNINGS.md`, LEARNING 008 a 010.
