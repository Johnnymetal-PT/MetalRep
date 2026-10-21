# Auditoria de desempenho da framework — givachoice

**Estado:** Fase A e Fase B concluídas. Recebidas as duas extrações pedidas (secções 9 e 10). A tese da secção 7 foi **revista** depois da segunda.

**Datas:** Fase A 2026-09-10 · Fase B 2026-09-11 · **Pedida por:** Bruno Pinheiro

## 1. Objeto

O objeto desta auditoria é **a framework**. Não é o projeto, não é o trabalho de quem nele participou, e não é o resultado para o cliente. A pergunta é estreita e deliberada:

> Onde é que a framework induziu em erro, se calou quando devia ter falado, ou custou sem dar retorno?

O givachoice foi escolhido por ser **o único projeto que adotou a framework a meio da execução**. A hipótese de partida, formulada antes de olhar para a evidência, era que a framework pressupõe adoção de raiz e se comporta mal quando entra num projeto já a andar. A auditoria confirma-a, mas por razões diferentes das esperadas.

### Disciplina de classificação

Cada achado é classificado numa de três categorias, porque «o projeto teve problemas» não é o mesmo que «a framework causou-os»:

| categoria | significado |
|---|---|
| `DANO` | a framework fez o agente fazer, ou concluir, algo errado |
| `LACUNA` | a framework devia ter evitado e não tinha regra nenhuma |
| `ALHEIO` | problema real, mas não imputável à framework |

## 2. Base de evidência, e o que ela não cobre

| fonte | cobertura |
|---|---|
| transcrições nesta máquina | 24 ficheiros, 21 pontos de partida distintos, **11/08 a 10/09** |
| log de consumo (commitado, agrega todas as máquinas) | **192 sessões** desde 19/06 |
| git | 3072 commits, 205 humanos |
| memórias locais do projeto | **107 ficheiros** |
| Odoo, artefactos `.pg`, registo de patches | consultados |

**Três limites que condicionam tudo o que se segue.**

**Vejo cerca de 15% do raciocínio.** Tenho o *que* mudou, de todas as máquinas, pelo git. Tenho o *porquê* apenas das sessões desta máquina. O período de adoção — 27/04 a 10/08 — não tem uma única transcrição aqui.

**Não há atribuição de operador em lado nenhum.** No log de consumo o `repo_path` é idêntico em todas as máquinas, porque o utilizador local tem o mesmo nome; não existe campo de operador. No git, os 205 commits humanos saem todos como «Bruno Pinheiro», quando trabalharam pelo menos três pessoas. Nas sessões, a autenticação aparece ora como `claudio.pereira@`, ora como `it.odoo@`, ora como `nuno.oliveira@`. Isto é, em si, um achado — e é o que obriga esta auditoria a ter uma Fase B.

**Os números de custo históricos são inutilizáveis.** O medidor de tokens somava as releituras de cache ao input até 2026-09-10 (corrigido na v2.22.0). Os 18,6 mil milhões de tokens que o givachoice exibe não significam nada. Esta auditoria não usa nenhum número de custo.

**Não há projeto de controlo.** O givachoice é o único projeto têxtil com evidência de desenvolvimento. Os outros projetos servem para corroboração fraca — dizer se um defeito é geral ou específico — nunca como comparação.

## 3. Contexto do projeto

Sem isto, metade dos achados seria mal lida.

- **Migração Odoo 17 → 19**, produção on-premise, migrada a **31/07/2026**.
- **A 31/08 o cliente escreveu:** «Venho informar que o armazem esta parado por não conseguir fazer o nosso trabalho no sistema. Não conseguimos dar retorno. O nosso stock esta mal.»
- O modelo de trabalho real é **patch a um Odoo vivo**, com registo de patches construído para o efeito (`auditoria_v19/pg_patches_aplicados.py`) e um bot próprio a fotografar produção e testes de 15 em 15 minutos.
- O repositório trabalha na branch `audit`; tem **dois projetos espelhados** e três árvores de addons.
- O publisher do espelho **parou a 10/08**, no início do mês mais intenso.

## 4. Danos

### D1 — O sync destrói o mecanismo de adaptação que a própria framework anuncia
**Ainda vivo hoje.**

O `AGENTS.md` diz de si próprio que serve «para registar overrides locais quando existirem». O `pg_sync_shared_assets.ps1` copia `templates/AGENTS.md` e `templates/CLAUDE.md` por cima dos do projeto, com `-Force` e sem preservação — enquanto preserva o `PG_CONTEXT.md` e o `PG_SCOPE_INTAKE.yaml` com `SKIP ... ja existe`.

`FACTO OBSERVADO` (11/08, registado na memória do projeto): um re-sync **apagou 41 linhas** do `AGENTS.md` do givachoice, precisamente a secção que dizia onde estava o código vivo dos servidores. Recuperado por `git checkout --` porque estava versionado.

Verificado a 10/09: a preservação existe para o `.gitignore` (bloco delimitado) e para ficheiros saltados se já existirem. O `AGENTS.md` continua a ser sobreposto.

**Consequência de segunda ordem, e é a mais cara:** a equipa deixou de poder confiar no `AGENTS.md` para regras locais e passou a guardá-las em memórias do agente — que não viajam com o repositório, nem entre máquinas, nem para quem entre no projeto depois.

### D2 — O passo 1 do ritual impõe a branch errada, e isso já produziu uma conclusão factual errada
**Ainda vivo hoje.**

`pg_checkout_brodoo_branch.ps1:97` tem `$targetBranch = 'brodoo'` fixo no código. Neste repositório há **três declarações em desacordo**: o `project.json` namespaced da fase 3 diz `audit`, o legacy da raiz diz `main`, e o script impõe `brodoo`.

`FACTO OBSERVADO` (medido a 11/08): `origin/brodoo` **não tem os dados da fase 3** e tem outra árvore de addons (`PGModules` contra `addons_giva_v19`). Divergência de 1698 commits.

Seguir o ritual põe a sessão a analisar a fase 3 a partir de uma branch que não a contém. **Já aconteceu:** a 06/08 uma sessão concluiu que uma instrumentação não estava deployada, por comparar contra um espelho velho.

A ironia operacional: neste repositório a falha do passo 1 é **protectora**. A memória do projeto teve de a documentar para impedir que alguém a «resolvesse» forçando o checkout.

### D3 — A versão do Odoo declarada esteve errada durante onze dias
Causas latentes; sintoma contornado à mão.

De **31/07 a 11/08** o `PG_CONTEXT.md` declarava **17.0** enquanto a produção corria **19.0**. O preflight derivava daí a documentação oficial de 17.0 — e citar 17.0 num projeto em 19.0 engana precisamente onde o comportamento mudou entre versões (`uom_po_id`, por exemplo, existe em 17.0 e 18.0 e foi removido em 19.0).

Duas causas, ambas da framework:

1. **O bloco de contrato do `PG_CONTEXT.md` não é regenerado quando o campo muda no Odoo.** O espelho já dizia 19.0; o texto que o agente lê continuou em 17.0.
2. **Em repositório multi-projeto a resolução da versão é não-determinística.** `Get-ProjectGovernance` (`pg_preflight_context.ps1:50-66`) percorre todos os `project.json` e fica com o **último** que tenha versão — a ordem de travessia decide. Ficou com a da fase 2. O mesmo padrão em `Get-MirrorArtifactPath:209-219`, que prefere o artefacto *legacy* da raiz, o oposto do que o `AGENTS_SHARED` manda em multi-projeto.

Corrigido a 11/08 **acrescentando rótulos manuais** ao `PG_CONTEXT.md`. O preflight corrido hoje responde 19.0 — mas por causa do contorno, não porque o defeito tenha sido resolvido. Qualquer repositório multi-projeto sem esses rótulos tem o mesmo problema.

*Nota de método: registei primeiro que este defeito reaparecia em 04, 07, 09 e 10/09. Estava errado — todas as ocorrências tardias são a mesma linha de um índice de memória a ser recarregada, do tipo `attachment`. A janela real são onze dias.*

### D4 — O espelho parou a 10/08 e o contexto consolidado é de maio
Último commit do publisher: **10/08**. Agosto teve 87 sessões e setembro 79.

O `PG_CONTEXT.md` declara «Último sync do espelho: 2026-05-07» e afirma no cabeçalho ser «artefacto derivado exclusivamente do espelho». `FACTO OBSERVADO`: desde 07/05 só foi tocado por edições manuais. A fonte de verdade nº 1 do contrato mente sobre a sua própria natureza.

`PONTO POR VALIDAR`: porque parou o publisher a 10/08.

## 5. Lacunas

### L1 — Não existe regra que proteja o que já funciona
**A lacuna mais cara, e a mais fácil de fechar.**

A ordem obrigatória de decisão — standard → módulo adicional → Studio → custom — é um método para escolher **o que construir**. Não há em lado nenhum uma regra que obrigue a estabelecer, antes de alterar, **o que o código já faz e se o cliente já o validou**.

Num projeto de raiz a lacuna é invisível: não há comportamento validado a perder. Num projeto adotado a meio, é onde está quase todo o valor em risco.

**Regressões sobre comportamento do cliente, verificadas uma a uma:**

| o que partiu | causa | dias exposto |
|---|---|---|
| «Ver Ordem» a pintar linhas inteiras de vermelho | patch 1.0.3, 05/08 | **30** |
| «Ver Ordem» com aviso «Lista de materiais desatualizada» | patch 1.0.2 | ~30 |
| app Modelos a abrir no formulário de criação | 4 registos de vista criados pelo Odoo Studio a 19/08, ao entregar o Gantt | 4 |
| etiqueta individual por rolo em vez do total | correcção de 14/08 aplicada no ciclo errado | 7 |

Mais dois casos apanhados **antes** de chegarem ao cliente: os lotes «Geral» (levantados como defeito, eram pedido do cliente) e o custo zero na subcontratação (proposta de incorporar custo, quando o zero está certo em 88% dos casos, por o material ser do cliente).

Duas das quatro são a lacuna da intenção. Uma é efeito colateral do Odoo Studio sobre a ordem das vistas — que a ordem de decisão admite como passo 3 sem dizer nada dos seus efeitos colaterais. Uma é erro de implementação simples.

`SUJEITO A FASE B`: a sessão de 05/08, que produziu a 1.0.3, não está nesta máquina.

**A regra já existe — escrita à mão, num projeto.** A 26/08 o givachoice guardou a memória `dimensionar-e-confirmar-a-intencao-nao-so-testar`, instrução do Bruno «a propósito de alterações que já se revelaram descabidas»:

> «São dois riscos, e o teste só apanha um. *Isto parte alguma coisa?* apanha-se com resguardo, ensaio e verificação. *Isto é o que eles querem?* — nenhum ensaio apanha isto.»

Com o corolário: «uma correcção que ninguém pediu tem de passar uma barra **mais alta**, não mais baixa por ser pequena» e «não confundir *ensaiado* com *validado*: ensaiar prova que corre; validar é o cliente dizer que é aquilo que quer».

Isto pertence ao `AGENTS_SHARED`. Hoje não chega a nenhum outro projeto da frota.

### L2 — A framework não sabe descrever o modo de trabalho deste projeto
A framework pressupõe: código no repositório → ordem de decisão → `vendor/odoo_src` → commit na branch Brodoo.

O givachoice trabalha por patches a um Odoo vivo. O código verdadeiro está nos servidores, publicado por um cron próprio; o repositório tem três árvores de addons de gerações diferentes.

**A medida da lacuna:** entre as 107 memórias locais há **quatro** dedicadas a responder «onde está o código verdadeiro» — que é a fonte de verdade nº 2 do contrato. Quatro memórias para responder a uma pergunta que o contrato dá por respondida.

### L3 — Sem atribuição de operador não há auditabilidade
Ver secção 2. A frota regista que uma sessão aconteceu, nunca quem a fez. Além de bloquear esta auditoria, impede medir o efeito de qualquer alteração à framework — incluindo as que estão propostas.

**A demonstração mais limpa da lacuna veio de dentro da própria auditoria.** Pedida uma extração e um cabeçalho a dizer quem a fez, o agente na máquina `PRIMAVERA` escreveu **João Barros**. O autor é o **José Couto**. Não foi erro do agente: ele reportou a conta autenticada na sessão, porque é a única identidade que consegue ver.

Isto fecha o padrão. Em três sítios diferentes — `repo_path` no log, autor dos commits, conta da sessão — a identidade registada é a que está **configurada**, nunca a de quem está ao teclado. É por isso que a correção (v2.25.0) regista `machine`, detetado do sistema, a par do `operator` declarado: o primeiro não depende de configuração nenhuma, o segundo pode estar errado — como aqui esteve.

## 6. O que não é da framework

Registado para que a auditoria não some o que não deve:

- **A paragem do armazém a 31/08** é sequela de uma migração de versão maior num ERP em produção. `PONTO POR VALIDAR`: se alguma decisão apoiada por agente contribuiu — a janela da migração (31/07) não tem transcrições nesta máquina. `SUJEITO A FASE B`.
- **O campo Fatura Primavera desaparecido** e o **botão «Reservas» inalcançável** são sequela da v19: o Odoo renomeou `tree` para `list`, e personalizações Studio que herdavam da vista antiga deixaram de poder ser reaplicadas.
- **A maior parte dos 59 commits de retrabalho** é desenvolvimento iterativo normal de módulos novos, não regressão. Uma classificação automática deu 44 «regressões nossas»; o número foi descartado por inflacionado, e substituído pelas quatro verificadas à mão.

## 7. Leitura de conjunto

A hipótese de partida confirma-se, mas a causa não é a que se esperava.

**A framework não correu mal no givachoice por ser pesada. Correu mal por ser rígida — e, na maior parte do trabalho, por estar simplesmente ausente.**

*Revisto a 2026-09-11, depois da segunda extração da Fase B.*

**Onde esteve presente, foi rígida.** Assumiu código no repositório quando o código vivo está no servidor. Assumiu uma branch quando havia três declarações em desacordo. Assumiu um projeto quando havia dois. E, quando o projeto se adaptou a essa distância — escrevendo overrides no sítio que a própria framework indica para isso —, **apagou-os no sync seguinte**.

**Onde o trabalho realmente aconteceu, esteve ausente.** As duas migrações completas da base de dados de produção e o desenvolvimento dos módulos custom decorreram em pastas de servidor que a framework não conhece: sem `.pg`, sem espelho, sem `AGENTS.md`. Em 46 conversas, o ritual correu 7 vezes, não encontrou nada em nenhuma, e nunca mudou uma decisão.

E a ausência tem preço medido: seis incidentes de confusão entre Odoo 17, 18 e 19, incluindo **um deploy de código v17 sobre o servidor de testes v19**, recuperado por um backup manual feito por sorte minutos antes. O próprio agente nomeou o que faltava — um registo persistente e sempre consultado a fixar «este projeto é v17, servidor X, base Y». É exactamente o que um `AGENTS.md` é, e não existia ali.

O que se seguiu foi previsível: o projeto construiu um sistema paralelo. 107 memórias, um registo de patches próprio, um mirror de base de dados próprio, guiões de janela de manutenção próprios. Nada disso é reaproveitável por outro projeto, e nada disso volta para a framework.

O custo real não foram os tokens do contrato. Foi um mês de trabalho a construir, num projeto, o que a framework devia ter dado — e a defender-se do que ela impunha.

## 8. Consequências para o plano de melhoria

A auditoria foi pedida para cruzar com a proposta de **cortar o contrato partilhado** (frente 3: separar núcleo de referências a pedido, ~42 KB para ~21 KB).

**Nenhum dos achados desta auditoria é resolvido por esse corte.** E o D1 aponta em sentido contrário: o problema não foi contrato a mais, foi rigidez a mais.

Ordem revista proposta:

1. **A regra em falta (L1)** no `AGENTS_SHARED` — estabelecer o comportamento atual e a sua origem antes de o alterar; distinguir *ensaiado* de *validado*; barra mais alta para o que ninguém pediu.
2. **As três correções com dano provado**: o sync preserva os overrides locais (D1); o checkout respeita a branch declarada (D2); a versão deixa de ser resolvida ao acaso em multi-projeto e o preflight recusa série divergente do source (D3).
3. **Atribuição de operador** no log de consumo (L3) — sem isto nada do resto é mensurável.
4. **O corte do contrato**, que continua a valer, mas deixou de ser o mais urgente.

Fica também uma pergunta de desenho que esta auditoria não resolve: se a framework deve **suportar** modos de trabalho como o do givachoice (patch a produção viva, pastas de servidor fora de qualquer repositório), ou **declarar explicitamente** que não os cobre — como já faz para os projetos não-Odoo, via `.pg/PROJECT_PROFILE.json`. O que não pode continuar é a terceira hipótese atual: fingir que os cobre.

> **DECIDIDO a 2026-09-11 por Bruno Pinheiro: a framework deve SUPORTAR estes modos.**
>
> A consequência não é construir de raiz. Os mecanismos já existem, foram feitos no givachoice e funcionam — o `espelhar_addons_servidor.sh` publica em branches `live/*` o que está realmente instalado nos servidores, e no dia da decisão verificou-se que o `live/producao` corresponde a **29 de 29** módulos instalados, contra 10 de 29 da melhor das doze árvores versionadas. O que falhou foi não terem voltado para a framework, que é o achado central da secção 7. Suportar significa **promover o que existe**, com os caminhos parametrizados.
>
> Plano em quatro fases no `PG-010` do backlog: o espelho generalizado, a janela de manutenção como método, os objectos da base de dados, e o registo de consumo em pastas que não são repositórios.
>
> Duas peças já foram feitas antes da decisão e continuam válidas: o contrato **reconhece** o espelho como fonte do código vivo (v2.30.0) e **exige prova** ao implantar código (v2.31.0). Faltava o mecanismo que produz o espelho — e é esse que a F1 promove.

**Duas frentes novas, vindas da segunda extração:**

5. **O ritual precisa de ter consequência, ou de não ser obrigatório.** Hoje, numa pasta sem `AGENTS.md`, o passo diz «não existe, continuo» e o custo é uma chamada por sessão sem nada em troca. E não volta a correr em conversas retomadas, que é como a maior parte do trabalho longo acontece. Um passo obrigatório que nunca trava nada é treino para o ignorar.

6. **Os factos que o agente não pode esquecer têm de viver onde ele os relê sempre.** O mecanismo de compactação de sessão reintroduziu a versão errada do Odoo **duas semanas depois** de o utilizador a ter corrigido, porque não lê as notas de memória do projeto. Isto tem uma consequência directa para a frente 3: há um núcleo de factos do projeto — versão, servidor, base de dados, o que não se toca — que **não pode** sair do que é sempre carregado. O corte do contrato tem de os proteger, não apenas encolhê-lo.

## 9. Fase B (parcial) — máquina do Nuno Oliveira

Extração recebida a 2026-09-10: 16 ficheiros, **13 conversas distintas**, de 04/08 a 10/09. Duas caem na janela pedida. A extração é citada e datada ao segundo, e distingue o que não encontrou do que não existe.

*Falta ainda a máquina do José Couto.*

### B1 — O período de adoção não deixou rasto em máquina nenhuma
`FACTO OBSERVADO`: a transcrição mais antiga na máquina do Nuno é de **2026-08-04T16:53Z**. Nesta máquina, a mais antiga é de 11/08. **Entre 27/04 e 03/08 não existe uma única transcrição em nenhuma das duas máquinas** — quatro meses, incluindo a adoção da framework e a migração para a v19.

A ausência é o resultado: as decisões estruturantes deste projeto não são auditáveis. Junto com L3 (sem atribuição de operador), a conclusão é que **a framework não conserva memória do que os agentes decidiram** — só do que consumiram.

### B2 — O mesmo defeito, dois desfechos opostos: a framework é um chão, não uma guarda
**Este é o achado mais importante da auditoria.**

O preflight reportou **17.0** nas duas conversas, com a mesma causa — lê o projeto da fase 2. O que aconteceu a seguir não podia ser mais diferente.

**CONV 1, 04/08 16:57Z** — o agente repetiu o erro ao utilizador como passo cumprido:

> «Passos 2 e 4 correram OK (preflight `pass`, **Odoo 17.0/série 17.0**, framework sincronizado).»

…três linhas acima de descrever, na mesma resposta, «duas anomalias no **ambiente Odoo 19**» e «a restrição de permissões introduzida na **versão 19**». Nunca reconciliou as duas afirmações.

**CONV 2, 10/08 15:46Z** — o agente contradisse o preflight, com prova:

> «Preflight `pass`, com um aviso a registar: reporta **Odoo 17.0** e `docs_base_url` de 17.0, **porque lê o projeto fase-2**. O source em `vendor/odoo_src` é `version_info = (19, 0, ...)`. **A série a usar é 19.0, não a que o preflight imprimiu.**»

E confirmou contra o servidor (`19.0+e`) e contra o `project.json` do projeto certo.

**A framework forneceu o facto falso nos dois casos.** Se houve dano dependeu inteiramente do rigor daquela sessão. Uma guarda que só funciona quando o operador já é cuidadoso não é uma guarda — é um enfeite que ocasionalmente engana. É a diferença entre *habilitar* e *garantir* que a auditoria de 2026-07 já tinha apontado, agora com prova documental.

### B3 — O passo 1 do ritual bloqueia-se a si próprio
`FACTO OBSERVADO` (10/08 15:44Z): o checkout falhou com

> «`error: Your local changes to the following files would be overwritten by checkout: .pg/tokens/consumption.jsonl`»

**O ficheiro que bloqueia o passo 1 do ritual é escrito pelo hook da própria framework**, a cada sessão. O passo 5 impede o passo 1.

E se tivesse funcionado teria sido pior: `origin/brodoo` diverge de `origin/audit` em **364/1667 commits**, não tem a pasta `auditoria_v19/` e aponta ao projeto errado. O agente gastou três minutos a ler o script para justificar não o cumprir, e classificou-o: «é um defeito do script, que vale reportar ao framework».

### B4 — O ritual não corre em conversas retomadas
Na CONV 1 o ritual correu no arranque de 04/08 e **não voltou a correr** nos dias 05, 06, 07, 11 e 12/08 — a conversa foi retomada e entrou directamente em trabalho.

O ritual é por arranque de sessão, não por dia nem por tarefa. Numa equipa que retoma conversas ao longo de uma semana, a cobertura real é uma fração da presumida. E o override local que obrigava a correr o `pg_check_live_drift.ps1` a partir de 06/08 **nunca foi corrido** nessa conversa.

### B5 — O custo do ritual, medido
`pg_odoo_query.ps1` **não é invocável pela forma que o próprio contrato manda usar**. A 10/08 consumiu **cerca de vinte minutos** de arranque, antes de se tocar na tarefa; a 11/08, cinco chamadas falhadas e um minuto, com uma mensagem de erro que **mente sobre a causa**:

> «`Credenciais Brodoo nao encontradas em 'name\,\ilike\,\Nuno\]]'`»

A causa real: `powershell -File` come as aspas internas na passagem de argumentos, e o Odoo recebe JSON inválido. Só funciona abandonando a invocação prescrita e usando o operador de chamada `&`.

**É a terceira redescoberta independente do mesmo defeito**: está numa memória do givachoice para o `-Domain`, aparece duas vezes nesta extração, e voltou a morder a 2026-09-10 no `pg_align_fleet_framework.ps1 -RepoNames` (corrigido na v2.22.1, mas só ali). O defeito é do contrato, que prescreve uma forma de invocação que não funciona com argumentos estruturados.

### B6 — O que funcionou, e vale registar
A auditoria não é um inventário de falhas. Na CONV 2:

- o agente **estabeleceu o comportamento existente antes de o alterar**, linha a linha, contra o código vivo (`origin/live/producao`), com `FACTO OBSERVADO`, e comparou o entregável contra o vivo por `diff`;
- **dimensionou antes de mexer**: «apenas 78 encomendas com custo de tecido calculado, de todos os tempos»;
- **preservou o comportamento anterior** onde não o conseguia justificar;
- **o espelho foi útil e não enganou**: apanhou que um ficheiro tinha ido parar a produção em vez de testes.

Ou seja: **o que falta à framework (L1) já é praticado por algumas sessões.** O que não existe é a obrigação — e por isso o resultado varia com quem está ao teclado, que é exactamente o que um método serve para evitar.

### B7 — Precisão sobre L1
A alteração ao `pg_giva_pdf_reports` datada de 04/08 no registo de consumo é uma **correção legítima de permissões** — o campo `sale.order.tag_ids` passou a ter `groups="sales_team.group_sale_salesman"` na v19, e sem `sudo()` o armazém e a produção apanhavam `AccessError` ao abrir o «Ver Ordem». Bem fundamentada e pedida.

A pintura das linhas a vermelho, que o cliente mandou reverter, **é alteração distinta sob o mesmo número de versão**. A sessão que a fez não existe em nenhuma das duas máquinas.

`INFERÊNCIA`: a 1.0.3 juntou uma correção pedida e uma alteração de comportamento não pedida. Se se confirmar, acrescenta à L1 um corolário: **não embrulhar alteração não pedida no mesmo lote de uma correção pedida**, porque a segunda serve de boleia à primeira e ninguém a revê em separado.

## 10. Fase B (2) — José Couto, máquina `PRIMAVERA`

Extração recebida a 2026-09-11: **7 sessões, 46 conversas distintas**, de 2026-07-06 a 2026-08-10, mais 7 notas de memória de 2026-06-09 a 2026-07-03 sem transcrição de suporte. 213 MB de transcrições reduzidos a digests citáveis.

**Nota de autoria, que é ela própria um achado.** O documento identifica-se no cabeçalho como sendo de **João Barros**; o autor é o **José Couto**. O agente reportou a conta autenticada na sessão, que era a única identidade à sua vista. Ver a nota no fim da secção 11.

### B8 — O trabalho aconteceu quase todo fora do perímetro da framework
`DANO ESTRUTURAL` · e obriga a rever a tese

As pastas de trabalho desta máquina são `C:\Odoo\PGAddons`, `C:\Odoo19\pgmodules`, `C:\Odoo\PGAddons\MIGRV18` e `pg_cut_plan`. **Nenhuma é o repositório `givachoice`.** Não têm `.pg/`, não têm espelho, não têm branch Brodoo — e, como se verá, não têm `AGENTS.md`.

Ou seja: durante mais de um mês, o desenvolvimento dos módulos custom e **as duas migrações completas da base de dados de produção** decorreram em árvores de ficheiros que a framework não conhece. O espelho publicava o estado de um projeto cujo trabalho real estava noutro sítio.

Isto não é o givachoice a ser especial. É a framework a cobrir **o repositório**, quando o trabalho de Odoo acontece em **pastas de servidor**.

### B9 — O ritual correu 7 vezes em 46 conversas, nunca encontrou nada e nunca mudou nada
`DANO DA FRAMEWORK` · severidade alta

`FACTO OBSERVADO`, contado na extração:

- em 46 conversas e 7 sessões, a verificação do `AGENTS.md` ou do `.pg_framework` aparece **7 vezes**, tipicamente só na primeira mensagem de cada sessão;
- em **nenhuma** dessas 7 há prova de que o ficheiro tenha sido encontrado e lido. As respostas registadas são «Sem AGENTS.md», «não existe AGENTS.md no projeto — como manda a instrução global, deixo nota e continuo», e `Glob -> .pg_framework*` sem resultado;
- em **todas as retomas depois de horas ou dias** — dezenas, incluindo retomas a meio de uma migração de produção em curso — o ritual **não se repetiu**;
- **nunca há registo de o ritual ter travado uma ação ou mudado uma decisão.**

E numa ocasião o próprio arranque do ritual falhou tecnicamente: um comando PowerShell enviado à ferramenta Bash, erro de sintaxe, repetido na ferramenta certa. O ritual custou uma chamada e uma explicação, e não deu nada em troca.

**A framework não tem resposta para «esta pasta de trabalho não é um repositório da framework».** O agente conclui «não existe, continuo» — que é a única coisa que pode fazer — e o passo obrigatório transforma-se em ruído.

### B10 — A confusão de versão do Odoo: seis incidentes datados, e o mais caro de todos
`LACUNA DA FRAMEWORK` · severidade alta

Não é um erro isolado; é um padrão com seis ocorrências em sessões e módulos diferentes:

| data | o que aconteceu |
|---|---|
| 2026-07-13 | um **resumo automático de compactação** rotula `pg_cut_plan` como «Odoo 19 addon». O addon é v17. O erro nasce aqui, em silêncio |
| 2026-07-15 | tentativa de atualizar o módulo v17 correndo o servidor do **Odoo 19**; ~10 minutos e mais de 20 chamadas de ferramenta até descobrir o caminho certo. A meio, procura `AGENTS.md` — não encontra |
| **2026-07-23** | **deploy de código v17 sobre `C:\Odoo19\pgmodules\pg_cut_plan`**, o servidor de testes real. Recuperado de um backup manual feito minutos antes, por sorte. Detetado só porque o utilizador perguntou «e o servidor de testes?» |
| 2026-07-28 | consulta ao código-fonte de referência feita na árvore do Odoo 19 para decidir um fix no v17. Correto por coincidência |
| 2026-07-29 | o resumo automático **volta a escrever** «Odoo v19, base GIVA19», duas semanas depois da correção. ~40 minutos de consultas contra a base errada |
| 2026-07-31 | o resumo automático repete o erro outra vez |

O utilizador tinha corrigido explicitamente a 2026-07-30: «esquece a v19 estamos a trabalhar na v17». O mecanismo de compactação de sessão **não lê as notas de memória do projeto** antes de gerar o seu resumo, e reintroduz o facto errado.

E há um agravante: a lição **já tinha sido ensinada em junho**. A nota `feedback_scope.md`, de 2026-06-18, diz textualmente que referências a outras pastas/versões «podem induzir conclusões erradas (ex: usar Odoo 19 como referência para um addon v17)» — mais de um mês antes do incidente de 23/07. **Não generalizou de uma sessão para outra.**

O próprio agente nomeia a solução em falta, a 15/07: o que faltava era um registo persistente e sempre consultado que fixasse *este projeto é v17, servidor X, base Y*.

### B11 — «Aplicado em produção com sucesso», e não estava
`LACUNA DA FRAMEWORK`

Três ocorrências em três dias (05, 06 e 07/08): correções presentes em local e em teste, reportadas como aplicadas, que **nunca chegaram a produção**. A de 05/08 só foi descoberta porque o utilizador se recusou a aceitar «está feito» e insistiu duas vezes: «está em produção?», «Na de produção ainda está assim, podes confirmar?».

Não há controlo de versões nessas árvores, e portanto não há nada que detete deriva entre local, teste e produção. A deteção é sempre manual, por *diff*, e sempre reativa.

### B12 — Retrabalho por não verificar se o mecanismo já existia
`LACUNA DA FRAMEWORK`

Quatro casos de implementação completa — código, deploy, teste — posteriormente descartada por duplicar algo que já existia. O mais claro, a 03/08: um sistema de operadores construído de raiz em `pg_tablet_workorder_ui` e revertido ficheiro a ficheiro ao descobrir-se equivalente em `pg_cut_plan`, módulo que o próprio agente tinha explorado horas antes.

A framework tem uma ordem obrigatória para decidir entre standard, módulo, Studio e custom. **Não tem nenhum passo que obrigue a procurar, antes de construir, se já existe mecanismo equivalente no próprio código do projeto.**

### B13 — O ciclo «o próprio fix partiu isto»
`SINTOMA` · oito ocorrências independentes

Documentado oito vezes ao longo do período, em módulos diferentes: uma sincronização identificada como sendo a própria causa do bug que devia corrigir (29/07); um `CREATE OR REPLACE VIEW` que rebentou o serviço por ordem de colunas (06/08); um regex de correção que truncou o `arch_db` de 18k para 4k caracteres, esvaziando o relatório que tentava consertar (10/08); e um arranque acidental de um processo Odoo na base errada, tomando a porta do servidor, **apesar de instrução explícita para não tocar no servidor** (31/07).

### B14 — Edição de pasta explicitamente marcada como só-leitura
`LACUNA DA FRAMEWORK`

A memória `feedback_addons_giva_prod.md` (25/06) regista que o agente editou `C:\Odoo\addons_giva_prod`, descrita nas próprias instruções de âmbito como «base/referência do cliente, nunca modificar». Corrigido pelo utilizador: «addons_giva_prod disse para não mexer é a nossa base, repõe».

**A regra foi criada como reação ao incidente, não como prevenção.** É o mesmo padrão de L1: a regra que falta só nasce depois de o dano acontecer, e fica presa ao projeto onde nasceu.

### B15 — Seis semanas sem rasto nenhum, e um mês só com memória
`LACUNA DA FRAMEWORK` · confirma B1

Entre **27/04 e 08/06** não há rasto de espécie alguma nesta máquina — nem transcrição, nem memória. Entre **09/06 e 03/07** há sete notas de memória datadas mas **nenhuma transcrição**: houve trabalho real, documentado na própria memória, cujas conversas já não existem.

O que essas notas registam não é trivial: execução em produção real a 26/06 com 5.863 movimentos limpos, 2.173 quants criados, 3.242 fantasmas cancelados e cinco módulos instalados. E, a 03/07, SQL de correção escrito, documentado e explicitamente deixado **«pendente de execução pelo utilizador»** — sem que exista, em nenhuma nota posterior, confirmação de que tenha sido corrido.

### B16 — O que funcionou, e é preciso dizê-lo
A extração é explícita a registar disciplina repetida: pedidos de «analisa primeiro, sem alterar nada» respeitados à letra; simulações em `savepoint` com *rollback* antes de qualquer escrita em produção; confirmação explícita antes de eliminações em massa; avaliação crítica de segundas opiniões externas coladas pelo utilizador; e pelo menos uma vez o sistema de memória poupou trabalho real.

E um caso exemplar face à L1: a 29/07 o utilizador pede «verifica nos addons anteriores» e o agente fá-lo — *grep* em três pastas de cópia — antes de decidir remover uma verificação, concluindo que «sempre esteve lá — isto é uma decisão de desenho nova, não um rollback». É exactamente o que a regra da v2.24.0 passa a exigir. **Já se praticava; faltava ser obrigatório.**

## 11. Fase B — o que a Fase B respondeu, e o que fica sem resposta

As três perguntas do pedido tiveram resposta. Duas delas, a resposta é uma ausência — e a ausência é o resultado.

| pergunta | resposta |
|---|---|
| **05/08** — a sessão que pintou as linhas de vermelho no «Ver Ordem» | **Não existe em máquina nenhuma.** A alteração de 04/08 registada no log é uma correção legítima de permissões (`sudo()` sobre `tag_ids`, restringido na v19); a pintura das linhas é alteração distinta sob o mesmo número de versão, e a sessão que a fez não sobreviveu |
| **31/07 a 04/08** — a janela da migração | Coberta pela extração da máquina `PRIMAVERA`, com densidade: as duas migrações completas, o SQL de «Fase 6/7» saltado, e os bugs que apareceram em produção horas depois |
| **27/04 a 30/07** — o período de adoção | **Nada entre 27/04 e 08/06** em nenhuma das três máquinas. Entre 09/06 e 03/07, só notas de memória, sem uma única transcrição — houve trabalho documentado, incluindo execução em produção real a 26/06, cujas conversas já não existem |

**A adoção da framework neste projeto não deixou rasto em máquina nenhuma.** As decisões que fixaram o modo de trabalho — patch a produção viva, três árvores de addons, pastas de servidor fora de qualquer repositório — não são auditáveis. Só se conhecem pelos seus efeitos.

Fica uma pendência operacional fora do âmbito desta auditoria, encontrada na memória de 03/07 e digna de verificação: SQL de correção de movimentos abertos em MOs canceladas, escrito e documentado, deixado como «pendente de execução pelo utilizador», sem confirmação posterior de que tenha sido corrido.

### Nota de autoria — a lacuna L3 a demonstrar-se dentro da auditoria sobre ela

A extração da máquina `PRIMAVERA` identifica-se, no seu próprio cabeçalho, como sendo de **João Barros**. **O autor é o José Couto** (confirmado por Bruno Pinheiro, 2026-09-11).

O agente não inventou o nome: reportou **a conta autenticada na sessão**, que é a única identidade que tinha à vista. É a mesma razão por que o `repo_path` não distingue máquinas e por que os 205 commits humanos deste projeto saem todos com o mesmo nome — em nenhum desses sítios existe o operador, existe apenas o que está configurado.

O detalhe importa para o desenho da correção: um agente a quem se pergunta «quem és?» responde com a conta, porque é o que consegue ver. Foi por isso que a v2.25.0 passou a registar **`machine`** — detetado do sistema, e o único discriminador que não depende de configuração — a par do `operator` declarado. Um diz onde; o outro diz quem se assumiu ser, e pode estar errado, como aqui.
