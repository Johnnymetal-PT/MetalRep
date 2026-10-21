# CHANGELOG

Todas as evoluções relevantes do `_pg_template` devem ser registadas neste ficheiro.

## v2.34.0 - 2026-09-11

Status:
- o trabalho feito fora de repositorios deixa de ser invisivel a medicao (PG-010, fase F4)

Resumo:
- **boa parte do trabalho de Odoo acontece fora de repositorios** — pastas de servidor, arvores de addons, copias de migracao. O hook de consumo exigia `.pg/` ou `PG_CONTEXT.md` na pasta, e uma pasta de servidor nao tem nenhum: **esse trabalho nao contava para nada**
- foi essa cegueira que obrigou a auditoria do givachoice a pedir extraccoes maquina a maquina, ao Nuno e ao Jose, para reconstruir o que la tinha acontecido — porque o log nao sabia que tinha acontecido
- uma pasta declarada pelo `pg_init_work_folder.ps1` passa a contar. **O log NAO vai para a pasta**: vai para o repositorio que o bloco declara em `Repositorio do projeto:`. A pasta continua sem `.pg` e sem estrutura da framework, que e o desenho do `pg_init_work_folder`

A separacao que isto obrigou a fazer:
- o evento e **escrito** no repositorio, mas **regista** a pasta onde o trabalho se fez, com `work_folder: true`. Novo parametro `-CaminhoDoTrabalho` no `pg_log_token_consumption.ps1`
- sem ele, o `session_open` dizia o repositorio e o `session_close` dizia a pasta — dois eventos da mesma sessao a discordar um do outro. Foi apanhado no primeiro teste real, depois de a funcionalidade ja «funcionar»

Cobertura por declaracao, como em todo o resto:
- **sem bloco declarado, nada muda**: a pasta continua fora da medicao. Uma pasta nao entra por um script achar que sim
- **bloco declarado a apontar para um repositorio inexistente**: nao regista e **nao rebenta**. Um hook que rebente estraga a sessao de quem esta a trabalhar

Validação:
- `pg_test_token_consumption.ps1` ganha **7 verificacoes**: o registo acontece, regista a pasta e nao o repositorio, marca-se como `work_folder`, a pasta nao ganha `.pg`, uma pasta anonima nao regista, e um repositorio declarado inexistente nem regista nem rebenta
- **verificado por mutacao**: desligando o reconhecimento do bloco, a suite falha e nomeia a verificacao
- confirmado que o `pg_validate_token_consumption.ps1` aceita o campo novo, e que em repositorios normais nada muda
- `ps_syntax` (60) e `pt_accents` a passar

Falta do `PG-010`: a fase **F3** (objectos da base de dados).

## v2.33.0 - 2026-09-11

Status:
- a janela de manutencao passa a ter template (PG-010, fase F2)

Resumo:
- a regra de implantacao (v2.31.0) diz **o que** tem de acontecer; faltava a forma. Novo `TPL_JANELA_MANUTENCAO.md`, promovido dos guioes reais do givachoice — nao desenhado de raiz
- as sete seccoes sao os cinco passos da regra, mais duas que a pratica mostrou fazerem falta e que eu nao teria inventado:
  - **«O que este guiao NAO leva, e e deliberado»** — o ambito negativo explicito. Sem isto, o que fica de fora parece esquecimento em vez de decisao. Nos guioes reais serve para nao arrastar alteracoes de outra pessoa por publicar
  - **«Antes de abrir a janela»** — quem avisar, e porque. Se o modulo e territorio de outra pessoa, avisa-se mesmo com o travao a proteger: o travao protege os dados, nao a relacao
- a **linha de base** é o travao central: md5 de cada ficheiro a substituir, versoes em disco, contagens de `ir.model.data`, modulos pendentes. **Se qualquer md5 nao bater no momento da execucao, aborta sem copiar nada** — e o que impede sobrepor trabalho publicado entretanto, num projeto onde varias pessoas publicam no mesmo modulo
- a **reversao escreve-se antes**, nao quando for precisa

Onde vive, e porque isso importa:
- o template foi criado **no Knowledge** (artigo 851, sob «Doc Templates»), nao no repositorio. `FACTO OBSERVADO`: o `pg_pull_doc_templates.ps1` **apaga** todos os `TPL_*.md` locais e repoe os do Knowledge — um template criado no repositorio desaparecia no pull seguinte
- publicado com o corpo num `<pre>` unico, que e o formato que o `pg_doc_templates_common.py` reconhece como markdown em bruto e devolve tal e qual. **Round-trip verificado: 4005 caracteres a entrar, 4005 a sair, byte a byte identicos**, com as 7 tabelas, os 2 blocos de codigo e os 141 caracteres acentuados intactos e **zero sequencias de mojibake**
- `pg_template_state` posto em `published` e `pg_template_version` em `1.0.0`, seguindo o padrao dos templates existentes — sem isso o pull nao o traz

Validação:
- round-trip completo Knowledge -> repositorio, verificado por comparacao exacta e por contagem de pontos de codigo nao-ASCII
- `pt_accents` a passar

Nota para quem mantem a metodologia:
- o espaco «Doc Templates» do Knowledge e mantido por **Pedro Coelho**. Este artigo foi criado sem o consultar; se preferir rever antes de estar publicado, basta pôr `pg_template_state` em `draft` e o template deixa de chegar a frota

## v2.32.0 - 2026-09-11

Status:
- o mecanismo do espelho do codigo vivo passa a ser da framework (PG-010, fase F1)

Decisao de perimetro de Bruno Pinheiro, 2026-09-11: a framework **suporta** o trabalho por patch a producao viva, em vez de fingir que o cobre. A primeira consequencia nao e construir — e **promover o que ja existe e funciona**.

Resumo:
- novo `scripts/server/pg_mirror_server_code.sh`, generalizacao do `espelhar_addons_servidor.sh` que o givachoice construiu sozinho e que corre desde agosto de 2026. **So os caminhos eram especificos**; tudo o resto ja era generico
- instala-se **no servidor do cliente** e publica em branches `live/*` o que la esta mesmo instalado. Configuracao num ficheiro proprio (`pg_mirror.conf`), a partir do `.conf.exemplo` que traz os valores reais do givachoice comentados
- o contrato ja **reconhecia** o espelho como fonte (v2.30.0) e ja tinha o **verificador** do lado de ca (`pg_compare_client_addons.py --ref`). Faltava o mecanismo que o produz — e este e ele

O que o guiao faz, e que vale por si:
- **nao toca nas arvores que espelha**: o `.git` de cada espelho vive fora delas, com `core.worktree` a apontar para a arvore. O servidor nao fica com repositorios git no meio do codigo em producao
- **do core espelha so o desvio**. O core passa de 1 GB e nao compensa copia-lo; compensa saber que alguem lhe tocou e ver o que fez. Acima de um teto de ficheiros alterados **regista a ocorrencia e nao copia**, porque um upgrade mexe em milhares de ficheiros de uma vez e isso e ruido, nao desvio
- **a varredura do core e separavel** (`PG_SEM_CORE=1`), porque um `git status` sobre o core percorre 47 mil ficheiros — a 2026-08-06 isso gerou uma suspeita de lentidao do servidor reportada pelo cliente. O padrao sao dois crons: addons frequentes e leves, core uma vez por dia
- **escolhe sozinho o metodo de deteccao** do desvio: `git status` se a raiz for um repositorio (exacto), data de modificacao contra carimbo se nao for

Um defeito herdado, corrigido na promocao:
- no guiao original a inspeccao **escrevia** — criava o carimbo do core e a pasta de desvio mesmo sem `CONFIRMA=1`. Tem consequencia: a primeira execucao a serio passava a comparar contra um carimbo posto pela inspeccao, em vez de criar o seu. Um modo que se diz de inspeccao tem de o ser por inteiro, senao ninguem confia nele. Verificado: a inspeccao deixa de criar sequer a pasta

Validação, com um servidor simulado de ponta a ponta:
- inspeccao **nao escreve nada**, nem a pasta do espelho
- execucao real publica nas branches certas e **a arvore do servidor fica intacta**, sem `.git` la dentro e com o mesmo numero de ficheiros
- uma alteracao no servidor aparece no espelho na passagem seguinte; sem alteracoes **nao ha commit**
- o teto do desvio, forcado a 2 com 3 ficheiros alterados: nao copia e escreve o registo `_UPGRADE_*.txt`
- `PG_SEM_CORE=1` salta a varredura
- falha cedo e com mensagem se faltar `PG_REMOTO` ou `PG_ARVORES` — um valor em falta produziria um espelho silenciosamente errado, por exemplo um push para o repositorio de outro cliente

Apanhado ao commitar, e seria um defeito grave:
- o `.gitattributes` **nao tinha regra para `*.sh`**. O `text=auto` guarda LF no repositorio, mas o checkout em Windows escreve **CRLF no disco** — e e esse o ficheiro que alguem copia para o servidor. Num servidor Linux, um `.sh` com CRLF falha a arrancar: o kernel le o shebang como `/bin/bash` e responde `bad interpreter: /bin/bash^M`. Ja tinha mordido no GBUK, com o `pg_diag.sh`
- acrescentadas as regras `*.sh`, `*.conf` e `*.exemplo` com `eol=lf`. Verificado: o script sai do checkout em LF e o shebang fica intacto

Fases seguintes do `PG-010`, por fazer: a janela de manutencao como metodo (F2), os objectos da base de dados (F3), e o registo de consumo em pastas que nao sao repositorios (F4).

## v2.31.0 - 2026-09-11

Status:
- implantar codigo num servidor de cliente passa a ter regra, como ja tinha migrar dados

Resumo:
- **a assimetria era dificil de defender.** Migrar um campo exigia dry-run, `--confirm`, `--allow-prod` e reconciliacao; por codigo novo a correr na producao de um cliente nao exigia nada
- `FACTO OBSERVADO` (givachoice): os **dois incidentes mais caros do projeto foram de codigo, nao de dados** — um deploy de codigo **v17 sobre o servidor de testes v19**, recuperado por um backup manual feito por sorte minutos antes, e um «aplicado em producao com sucesso» que **nao estava**. Nenhum teria passado pelo guard de dados, porque nenhum tocou em dados
- nova seccao «Implantar codigo no servidor de um cliente», com cinco passos por ordem: confirmar a serie do destino **contra o proprio destino**; resguardo antes de tocar; dry-run; confirmacao explicita em producao; e verificar depois, contra o destino

O passo 5 e o que se costuma fazer mal:
- **a versao do manifest nao prova o codigo em execucao** — nada obriga a subi-la ao alterar um ficheiro. `FACTO OBSERVADO` (GBUK): a versao `18.0.2.8.3` chegou a nomear **dois codigos diferentes**
- por isso a framework **exige a prova, nao o mecanismo**. Dois projetos ja resolveram isto de maneiras diferentes e ambas servem: o GBUK pede ao modulo instalado a sua impressao digital SHA-256 por ficheiro; o givachoice publica o codigo vivo em branches de espelho. Qualquer meio serve desde que prove **codigo** e nao so rotulo
- sem nenhum deles, a verificacao possivel e a das versoes — e a conclusao tem de ser declarada como o que e: `PONTO POR VALIDAR`, nunca «verificado»
- e **nunca escrever «validado» sobre o que so foi implantado**: implantar prova que o codigo la esta; validar e o cliente dizer que faz o que ele quer

Ferramenta para o passo 1:
- `pg_compare_client_addons.py --serie-esperada <serie>` le a serie que corre **mesmo** na base-alvo (pela versao do modulo `base`) e **aborta** se nao for a esperada, antes de qualquer outra coisa
- **verificado contra o caso real**: apontado a producao do givachoice com `--serie-esperada 19.0` confirma e prossegue; apontado a ligacao `client_test` do mesmo projeto — que corre Odoo 17.0 — aborta e nomeia o incidente. E exactamente o cenario que custou o backup de sorte, agora travado antes de copiar um unico ficheiro
- quando o gate passa, a serie confirmada e reutilizada para normalizar as versoes, pelo que deixa de ser preciso passar `--serie` a mao

Validação:
- `test_pg_docs_coerencia` passa de 15 para **19 testes**: a extracao da serie a partir do modulo `base`, o caso sem resposta (devolve vazio e **nao adivinha** — adivinhar aqui seria pior do que falhar), a presenca dos cinco passos no contrato, e a exigencia de prova de codigo e nao so de versao
- `python_suites` (7 suites, **117 testes**) e `pt_accents` a passar

## v2.30.0 - 2026-09-11

Status:
- a framework passa a perguntar se o codigo que le e o codigo que corre

Resumo:
- **a fonte de verdade n.2 e «codigo do projeto», e isso pressupoe que o repositorio e o que esta a correr.** Em projetos adotados a meio, ou que fazem patch a um Odoo vivo, a suposicao pode ser falsa **sem que nada o denuncie** — e o agente fecha a ordem obrigatoria de decisao sobre codigo que ninguem esta a executar
- `FACTO OBSERVADO` (givachoice): doze arvores de addons em `addons_giva_v19/`, e a melhor acerta em **10 dos 29** modulos instalados em producao
- **mas a verdade ja estava no repositorio.** O projeto tinha construido, sozinho, um espelho automatico do codigo vivo em branches `live/*`, escrito de hora a hora. O `live/producao` acerta em **29 de 29**. O que faltava nao era mecanismo — era a framework saber que existe e dizer ao agente para o ler. E o mesmo padrao das 107 memorias e do registo de patches proprios: o projeto resolve, e a framework nao aprende
- nova seccao no `AGENTS_SHARED.md`: antes de concluir sobre comportamento a partir de codigo, estabelecer **de onde vem esse codigo**. Se o projeto tem espelho, e essa a fonte e deve estar declarada nos overrides locais; e verificar que o espelho **ainda corresponde**, porque um espelho parado nao avisa que envelheceu — continua a parecer a fonte de verdade, que e a pior das duas falhas
- **declarado no givachoice**, no bloco de overrides locais que o sync passou a preservar: as quatro branches de espelho, `addons_giva_v19/` marcado como historia, e o comando de verificacao. **Verificado que sobrevive**: 104 linhas antes e depois de um sync — a correcao D1 provada num caso real e nao num andaime

Novo `pg_compare_client_addons.py`:
- responde a uma pergunta: **o que estou a ler corresponde ao que esta instalado?** Nao sincroniza, nao escreve, nao corrige
- dois modos: comparar as arvores do repositorio (qual, se alguma, corresponde) e **vigiar o espelho** (`--ref`), lendo de uma ref git com `git show`, sem checkout e sem tocar na arvore de trabalho
- **a normalizacao de versoes e o coracao disto, e nasceu de um erro meu.** A primeira execucao reportou 20 divergencias falsas em 29 modulos: o Odoo prefixa `latest_version` com a serie quando o manifest a omite, pelo que `1.0.84` e `19.0.1.0.84` sao a mesma versao. Quase se reportou um espelho saudavel como avariado. Um comparador com falsos positivos e pior do que nao existir — ensina a ignorar o alarme
- documenta o que **nao** prova: versoes iguais nao provam codigo igual, porque nada obriga a subir a versao ao alterar um ficheiro

O que o modo de vigilancia apanhou a primeira execucao, sem ninguem o procurar:
- **a ligacao `client_test` do givachoice aponta para uma base em Odoo 17.0**, contra os 19.0 da producao. Confirmado pela versao do modulo `base` nas tres ligacoes: `production` 19.0, `brodoo_dev` 19.0, `client_test` **17.0**
- Bruno Pinheiro confirmou que aquela base e um **resto de v17** e que existe outra base de teste em 19.0, cujo endereco esta por apurar
- validar contra 17.0 o que corre em 19.0 e a origem documentada do incidente mais caro deste projeto: um deploy de codigo v17 sobre o servidor de testes v19, recuperado por um backup manual feito por sorte. Desta vez ninguem deployou nada — a armadilha estava apenas montada, declarada no Odoo como se fosse legitima
- `PONTO POR VALIDAR` registado no `AGENTS.md` do projeto, com a instrucao de **nao usar** `-Purpose client_test` ate a ligacao ser corrigida

Validação:
- `test_pg_docs_coerencia` passa de 10 para **15 testes**, cinco deles sobre a normalizacao — nos dois sentidos: o que deve normalizar, e o que **nao** deve. Normalizar de mais esconderia divergencias verdadeiras, que e pior do que o falso positivo original. Um dos testes trava exactamente o caso que revelou o Odoo 17: `1.0` contra `17.0.1.0` com serie `19.0` **nao** pode passar por igual
- o comparador verificado contra o real nos dois modos: `live/producao` da 29/29, `live/testes` da divergencia total (o achado acima)
- `ps_syntax` (60), `python_suites` (7 suites, 112 testes) e `pt_accents` a passar

## v2.29.1 - 2026-09-11

Status:
- a proibicao do Studio chega ao publisher e ao que vai para o cliente

Resumo:
- a v2.29.0 tirou o Studio do contrato, mas dois sistemas continuavam a dizer o contrario, e **ambos sao visiveis a quem nao le o contrato**: o publisher escrevia `- Odoo Studio: <permissao>` nos `PG_CONTEXT.md` de toda a frota, e o `TPL_ORCAMENTO` anunciava ao cliente, num orcamento, a ordem em quatro passos. Deixar assim reintroduzia o Studio pela porta do lado: quem le um `PG_CONTEXT.md` gerado conclui que e uma opcao cuja permissao se negoceia
- **`TPL_ORCAMENTO` corrigido na fonte.** O template e gerido no Knowledge (artigo 739) e sincronizado; editar o ficheiro do repositorio seria desfeito no pull seguinte. Editado no Knowledge, verificado por releitura, e trazido pelo `pg_pull_doc_templates.ps1`. A ordem anunciada ao cliente passou a tres passos
- **addon alterado no repositorio certo.** `parametro-odoo/Parametro_Global`, branch `feat/studio-proibido`, a aguardar PR. A pasta `pg_brodoo/` deste repositorio e espelho de teste e **nao foi tocada**: edita-la criaria um fork silencioso
- a decisao de desenho foi **dimensionada contra a producao**, aplicando a regra «Antes de alterar o que ja funciona» a nos proprios: 49 projetos declaram `yes` e 2 declaram `no` em `pg_studio_allowed`. Reaproveitar o campo inverteria o significado desses 51 registos — um `yes` que significa «o contrato permite» passaria a ler-se «existe Studio aplicado», o que e falso na maioria. Dai campo novo `pg_studio_applied`, e o antigo **deprecado e legivel, nao apagado**, pela mesma regra de nunca destruir camadas anteriores que se aplica ao Studio dos clientes

Validação:
- artigo do Knowledge: dry-run primeiro (1 ocorrencia exacta do padrao, delta -39 caracteres), resguardo do original antes de escrever, e **releitura a confirmar** que o Studio saiu
- a edicao correu inteiramente em processo PowerShell, sem o HTML atravessar o stdout — a travessia corrompe acentos, e este body tem-nos
- addon: os 7 modulos Python compilam e os 2 XML sao bem formados. **A suite do addon exige instancia Odoo e nao foi corrida**
- `pt_accents` a passar

Falta, e esta no `PG-009` / issue #60:
- PR, revisao e merge do `feat/studio-proibido`, e republicacao dos espelhos depois disso
- avisar **Pedro Coelho**, autor e mantenedor do artigo 739
- `TPL_PLANEAMENTO_ONBOARDING_PROJETO`, que acompanha o merge do addon

Verificado e sem alteracao necessaria:
- o `TPL_MIGRACAO_DADOS_ODOO.md` menciona Studio cinco vezes e as cinco estao **correctas**: tratam de migrar Studio -> standard e da regra de nunca apagar a camada anterior, que e o que continua permitido. Foi verificado em vez de assumido

## v2.29.0 - 2026-09-11

Status:
- o Odoo Studio deixa de ser um passo da ordem de decisao e passa a ser proibido

Decisao de Bruno Pinheiro, 2026-09-11: nao se fazem configuracoes, desenvolvimentos nem automacoes em Odoo Studio. A ordem obrigatoria passa de quatro passos a **tres**: standard ja disponivel -> standard adicional -> desenvolvimento custom.

Resumo:
- **escrito como proibicao, nao como omissao.** Apagar a mencao faria o Studio parecer apenas esquecido, e um agente reintroduzi-lo-ia como «opcao leve» -- que e exactamente como ele entra. A nova seccao «O Odoo Studio nao e um passo desta ordem» diz o que esta proibido, porque, e o que fazer em vez disso
- **a evidencia e do givachoice**: acrescentar uma vista pelo Studio criou quatro registos `ir.actions.act_window.view` com sequencias mais baixas do que as do padrao, e a aplicacao do cliente passou a abrir no formulario de criacao. Foi uma das quatro regressoes sobre comportamento que o cliente ja tinha. O Studio escreve na base registos que a analise nao preve, nao passam por revisao, nao aparecem em diff e nao viajam com o repositorio
- **a proibicao e de CRIAR, nao de lidar com o existente** -- e ha Studio em varios clientes. Ler, documentar e migrar continua legitimo, e a regra de **nunca apagar** vistas, menus e campos `x_` (desactivar, que e reversivel) mantem-se inteira. Remove-la seria trocar um problema de metodo por um risco de perda de dados
- o que muda no raciocinio: um requisito que antes «parecia pedir Studio» classifica-se agora como `Customizacao leve`/`Customizacao estrutural` com justificacao, ou como `Nao recomendado / alto risco`

Alcance da alteracao:
- `AGENTS_SHARED.md`: ordem de decisao a tres passos; categoria `Odoo Studio` fora da classificacao final; a validacao obrigatoria deixa de perguntar «Studio permitido?» e passa a perguntar se existe Studio **ja aplicado** -- que e o que muda o comportamento e nao se ve no codigo; a justificacao deixa de ter de explicar porque o Studio nao serve
- `templates/PG_CONTEXT.md`: a seccao «3. Odoo Studio» da analise consultiva desaparece (o custom sobe a 3) e nasce uma seccao de **diagnostico** do Studio existente, com destino proposto por item
- os quatro documentos de apoio que o contrato cita -- `PG_DECISION_ENGINE_PROMPT`, `PG_CHALLENGER_PROMPT`, `PG_PRE_RESPONSE_CHECKLIST`, `PG_FIT_GAP_FRAMING_PROMPT` -- alinhados e com a proibicao no topo. Um documento de apoio que ainda mandasse avaliar Studio como opcao poria o agente a fazer o contrario do contrato, e o agente le os dois
- `pg_build_pg_context.ps1` e `pg_apply_scope_sync.ps1`: o rotulo gerado passa de «Odoo Studio permitido?» a «Odoo Studio ja aplicado no ambiente?». O campo `studio_allowed` do intake e do espelho continua a alimenta-lo, pelo que nada se perde

Validação:
- `test_pg_docs_coerencia.py` passa de 5 para **10 testes**, com cinco novos que travam a reintroducao silenciosa: a proibicao tem de estar escrita, o Studio nao pode voltar ao bloco da ordem de decisao nem a lista de classificacoes, lidar com o existente tem de continuar permitido, e nenhum documento de apoio pode falar de Studio sem dizer que esta proibido
- verificado por **mutacao**: reintroduzindo `3. solucao via Odoo Studio` na ordem, a suite falha
- `ps_syntax` (60), `context_hygiene` e `pt_accents` a passar

`PONTO POR VALIDAR` -- fora do alcance desta release:
- o **publisher** (`pg_brodoo`, no repositorio `parametro-odoo/Parametro_Global`) continua a escrever `- Odoo Studio: <permissao>` no `PG_CONTEXT.md` que gera, e o wizard de onboarding continua a perguntar pela permissao de Studio. Nao foi alterado aqui de proposito: a pasta `pg_brodoo/` deste repositorio e um espelho de teste, e edita-la cria um fork silencioso do addon
- os **templates documentais** (`TPL_ORCAMENTO`, `TPL_MIGRACAO_DADOS_ODOO`, `TPL_PLANEAMENTO_ONBOARDING_PROJETO`) e o `README` mantêm mencoes ao Studio como opcao. Sao entregaveis e material de leitura humana, nao instrucoes ao agente; revê-los e trabalho a parte

## v2.28.4 - 2026-09-11

Status:
- um 404 no canal de dados deixa de se parecer com um problema de rede

Resumo:
- **issue #57 fechado, mas nao como estava proposto.** A sugestao era o preflight verificar o modulo `rpc` nas bases de cliente com ligacao configurada. Isso poe uma chamada a API do cliente no ritual de arranque de **todas** as sessoes -- e o proprio contrato classifica o canal API como o caminho mais caro, a usar so quando o espelho nao chega. O preflight tambem nao fala com o Odoo: le ficheiros locais e funciona offline. Era custo permanente para um caso raro
- **o sinal mais barato ja existia**: sem o modulo `rpc`, o `POST /jsonrpc` devolve **404**. E assinatura inequivoca e acontece exactamente quando interessa -- na falha -- sem acrescentar uma unica chamada
- `pg_odoo_query.ps1` (2 sitios) e `pg_odoo_client_query.ps1` (2 sitios) passam a apanhar a `WebException`, ler o `StatusCode` e, sendo 404, nomear a causa provavel e dizer onde confirmar (Definicoes > Aplicacoes, sem o filtro «Aplicacoes»). Qualquer outro erro e re-lancado intacto
- porque importa: no Odoo 19 os endpoints RPC sairam do core para um modulo proprio (`auto_install`, mas desinstalavel a mao). Se alguem o desinstalar, **todo o canal Brodoo morre nessa base** -- leituras, espelho e migracoes -- e ate aqui a falha aparecia como erro de rede ou de autenticacao
- documentado no `AGENTS_SHARED.md`, com a nota de que os mesmos endpoints saem no Odoo 22 (#56)

Validação:
- mecanica verificada contra um 404 real: chega como `WebException` com `StatusCode` legivel
- canal Brodoo confirmado a funcionar depois da alteracao, com consulta real ao `project.project`
- `ps_syntax` (60), `pt_accents`, `align_fleet_framework` (63), `checkout_branch` (16) a passar

Frota: **29 de 32**, 1 fora do perimetro, 2 por resolver (eram 8 no inicio do dia)
- `Evostone` (43 a frente / 272 atras), `GBUK` (17/6) e `besimple` (4/5) reconciliados e publicados. Zero conflitos nos tres: os commits do remoto eram todos do publisher a escrever o espelho, e nao tocavam em nenhum ficheiro alterado localmente. Verificado antes de cada merge, e cada push varrido por credenciais

`PONTO POR VALIDAR` -- `domusacropoles` **nao e arrumacao, e um repositorio que nao funciona em Windows**:
- a tentativa de o pos na branch declarada falhou com `'origin/Teste' is not a commit`. Causa: com `core.ignoreCase=true` (o default em Windows), o git **nunca conseguiu criar** `refs/remotes/origin/Teste`, porque colide com `origin/teste`; inventou `origin/Teste-cap` e `origin/Teste-remote` no lugar
- ou seja, **nenhum clone em Windows consegue trabalhar na branch `Teste`** enquanto as duas existirem. Nao foi contornado de proposito: um contorno local esconderia o problema para a proxima pessoa que clonar
- a decisao esta preparada: a `Teste` e a viva (1854 commits, ultimo a 2026-09-07, do publisher) e e a que o Odoo declara; a `teste` tem um unico commit, de 2026-03-02. Falta decidir o destino do modulo `pg_projeto_mobiliario`, que so existe na `teste`

`PONTO POR VALIDAR` -- registo de tokens orfao no `GBUK`:
- um ficheiro chamado `c:UsersUtilizadorDesktopReposGBUK.pgtokensconsumption.jsonl` -- o caminho completo com os separadores comidos, usado como nome. De 2026-05-11, schema antigo, com o registo de uma sessao real (reprocessamento de payroll, 9968 work entries). Aquele consumo nunca entrou no log
- varrida a frota inteira: e o **unico** caso. Nao foi tocado -- apagar perde o registo, e inseri-lo agora falsearia a cronologia de um ficheiro append-only

## v2.28.3 - 2026-09-11

Status:
- a lista de nao-alinhados da frota passa a ter so problemas a serio

Resumo:
- **um repositorio de produto nao e um projeto, e estava a ser avaliado como se fosse.** O `parametro-odoo/Parametro_Global` -- onde vivem o `pg_brodoo`, o `pg_doc_templates` e os outros addons da casa -- aparecia na lista de nao-alinhados como «branch Brodoo nao declarada», ao lado de casos que sao mesmo defeitos. Nao esta mal configurado: **nao ha espelho Brodoo a publicar, porque este e o codigo do proprio Brodoo**. `FACTO OBSERVADO`: nao tem um unico `project.json`
- uma lista de excepcoes so vale enquanto cada linha merecer atencao; ruido nela ensina a ignora-la toda, e era esse o caminho
- nova chave `brodoo_mirror_applicable: false` no `.pg/PROJECT_PROFILE.json` ja existente, herdando o mecanismo dos projetos nao-Odoo. Como la, e por **declaracao explicita e nunca por inferencia**: um repositorio nao sai do perimetro por um script achar que sim
- o alinhador classifica-o como `fora_do_perimetro` -- continua no relatorio JSON e na contagem do resumo, mas sai da lista de problemas por resolver, e a `reason` declarada aparece, para a decisao ficar auditavel
- so a **chave** dispensa: um `PROJECT_PROFILE.json` presente sem ela nao tira nada da frota, e um perfil ilegivel nao dispensa nada. Um gate que se desliga por um ficheiro partido nao e um gate

Validação:
- `pg_test_align_fleet_framework.ps1` passa de 58 para **63 verificacoes**, com tres repositorios novos no andaime: um de produto que declara a chave, um com perfil que **nao** a tem, e um com perfil ilegivel. As asserçoes exigem que o primeiro saia do perimetro com a razao visivel, e que os outros dois continuem a ser avaliados normalmente
- `ps_syntax` (60), `checkout_branch` (16), `work_folder` (24), `preflight_versao` (11), `local_overrides` (11), `untrack_local_state` (10) e `pt_accents` a passar

Estado da frota: **26 alinhados, 1 fora do perimetro, 5 por resolver** (eram 8 no inicio do dia)

Dossie dos 5 que restam, levantado com o git e nao por estimativa -- todos precisam de decisao humana:

`domusacropoles` -- **a duvida esta resolvida**:
- o remoto tem duas branches que so diferem na capitalizacao. `Teste` tem o ultimo commit a **2026-09-07**, do publisher, e **1854 commits** que a outra nao tem; `teste` tem **um unico** commit, de **2026-03-02**, «add initial project files». O Odoo declara `Teste`. E a `Teste` a branch viva
- `PONTO POR VALIDAR` que sobra: esse unico commit da `teste` traz um modulo **`pg_projeto_mobiliario`** que **nao existe na `Teste`**. Antes de eliminar a `teste`, decidir se esse codigo tem destino -- num repositorio cujo conteudo e `ptplus_*` e `l10n_pt`, um modulo de mobiliario parece ter sido commitado no repositorio errado

Os quatro divergentes:
- **nenhum** dos commits locais existe no remoto sob outro sha (comparado por `patch-id`, nao por mensagem): sao trabalho genuinamente por integrar, nao duplicados
- `besimple`, `GBUK` e `Evostone` tocam em **zero ficheiros em comum** com o que o remoto andou para a frente. Os merges nao tem conflitos: sao minutos, nao uma tarde
- `Hipermercado` e outra coisa: local e remoto **nao tem antepassado comum**. O local comeca a 2026-03-10 («Initial commit») e o remoto a 2026-08-14 -- o repositorio foi recomecado e o clone local e de uma linha de historia abandonada. Projeto cancelado, pelo que nao e urgente, mas nao se resolve com um merge

`PONTO POR VALIDAR` -- onde versionar a declaracao do `Parametro_Global`:
- o ficheiro foi escrito no repositorio mas **nao commitado**. A regra de commits manda os ficheiros `.pg/` para a branch Brodoo, e este repositorio nao tem nenhuma -- e essa a razao de existir a declaracao. Commita-lo na branch de trabalho actual (`fix/effort-sync-resilience`) seria arrastar um ficheiro de framework para uma branch de codigo. Ate decidir, a declaracao vale apenas nesta maquina

## v2.28.2 - 2026-09-11

Status:
- as mensagens de erro passam a dizer o que fazer a seguir, e a sintaxe dos 60 scripts deixa de depender de alguem os correr

Resumo:
- **o checkout da branch Brodoo falhava sem dizer porque.** O `pg_checkout_brodoo_branch.ps1` mandava a saida do `git checkout` para `Out-Null` e, se a branch nao mudasse, dizia apenas «Nao foi possivel ficar na branch». No `ancoravip` a razao real era `untracked working tree files would be overwritten`, com dois nomes de ficheiro -- tudo deitado fora. A saida passa a ser guardada, o erro traz o que o git disse, e quando a causa e essa traz tambem a remediacao: comparar (`git hash-object` vs `git rev-parse origin/<branch>:<ficheiro>`) antes de apagar, porque iguais nao perdem nada e diferentes sao trabalho local
- **o aviso mandava corrigir o Odoo quando o Odoo estava certo.** A declaracao lida vem do **espelho local**, que pode estar velho; o aviso afirmava que o `repository_branch` no Odoo e que estava errado. No `ancoravip` o Odoo ja declarava `brodoo` ha duas semanas e era o espelho que nao tinha sido re-sincronizado. O aviso passa a atribuir a declaracao ao espelho e a oferecer as duas hipoteses
- **`ancoravip` desbloqueado**: 0 commits por publicar, 252 atras -- era so um clone velho. Dois ficheiros nao rastreados que bloqueavam o checkout eram **identicos byte a byte** aos ja versionados em `origin/brodoo`, confirmado por hash antes de os remover. Passou de saltado a alinhavel e esta na versao corrente
- **issue #58 documentado**: em builds de staging do Odoo.sh, a cada rebuild muda **tambem o `base_url`**, nao so o `database`. Nada no contrato o dizia, e o `pg_odoo_resolve_db.ps1` resolve a base *dado* um URL -- nao resolve o URL. Testados os URLs estaveis por branch (`<projeto>-<branch>.dev.odoo.com` e `.odoo.com`): ambos bloqueados ou ambiguos, **nao ha URL adivinhavel**. Nova seccao no `AGENTS_SHARED.md` e, no `pg_odoo_client_query.ps1`, as falhas do resolver em ligacoes `client_test`/`brodoo_dev` passam a nomear o rebuild como causa provavel e a dar o comando que actualiza o `base_url`

Novo `pg_test_ps_syntax.ps1`:
- valida a sintaxe dos **60 scripts** `.ps1` do repositorio com o mesmo parser que o PowerShell usa para executar, pelo que nao ha divergencia entre o que aceita e o que a maquina aceita
- **existe porque foi preciso**: uma edicao nesta sessao introduziu um escape invalido (`\"` onde o PowerShell quer backtick) e nada no repositorio o teria apanhado -- o ficheiro so falharia quando alguem o corresse, tipicamente num projeto de cliente, com o erro a apontar para um parentesis em falta cinco funcoes acima do problema real
- nao substitui testes de comportamento (um script pode ter sintaxe perfeita e estar errado), mas cobre os 60 de uma vez contra a classe de erro que parte o ficheiro inteiro, e corre em segundos
- verificado por mutacao: com um ficheiro deliberadamente partido, falha e nomeia a linha

Validação:
- `checkout_branch` passa de 10 para **16 verificacoes**, com um repositorio montado de raiz onde um ficheiro nao rastreado bloqueia o checkout; as asserçoes exigem que a razao do git chegue a quem le, que o ficheiro seja nomeado, que a remediacao apareca, e que o aviso nao culpe o Odoo
- `ps_syntax` (60), `align_fleet_framework` (58), `work_folder` (24), `preflight_versao` (11), `local_overrides` (11), `untrack_local_state` (10), `context_hygiene`, `token_consumption`, `pt_accents` e `python_suites` (7 suites, 107 testes) a passar

Estado da frota:
- os bloqueados passam de 8 para **6**: sai o `ancoravip` (resolvido) e o `givachoice` (publicado, 126 commits na branch `audit`)
- por resolver, e todos a precisar de decisao humana: quatro divergentes (`Evostone` 43/272, `Hipermercado` 228/99, `GBUK` 17/6, `besimple` 4/5), o `domusacropoles` e o `Parametro_Global`

`PONTO POR VALIDAR` -- `domusacropoles`:
- o remoto tem **duas branches que so diferem na capitalizacao**, `Teste` (74664de) e `teste` (562930f), em commits diferentes. Num sistema de ficheiros case-insensitive o git nao consegue manter as duas como refs locais, e inventou `origin/Teste-cap` e `origin/Teste-remote`. O Odoo declara `Teste`. Qual das duas e a verdadeira, e o que fazer a outra, e decisao de quem conhece o projeto -- nenhum script deve adivinhar isto

## v2.28.1 - 2026-09-11

Status:
- o relatorio da frota deixa de mandar fazer o que o git recusa

Resumo:
- **um repositorio divergente era reportado como estando so a frente.** A guarda 4 do `pg_align_fleet_framework.ps1` contava os commits locais fora do ambito da framework e dizia «publicar ou rever antes de alinhar». Mas nao contava o outro lado: no Evostone eram **43 a frente e 272 atras**, e ali um `push` e recusado pelo git. O texto mandava fazer o que nao era possivel fazer
- o script **ja fazia `fetch`** antes de classificar; o defeito nunca foi a frescura dos dados, foi descrever metade do estado e chamar-lhe o todo
- passa a distinguir os dois casos: **a frente** («publicar ou rever») e **DIVERGENTE** («reconciliar (merge/rebase) antes de alinhar -- um push seria recusado»), com a contagem dos dois lados

O que a correcao revelou na frota, a primeira passagem:
- `Evostone` 43 a frente / **272 atras**; `Hipermercado` 228 / **99**; `GBUK` 17 / **6**; `besimple` 4 / **5**
- `givachoice` e o **unico** caso genuino de trabalho por publicar (123 a frente, zero atras)
- quatro dos cinco repositorios que a frota dava como «por publicar» sao afinal arvores divergentes, e precisam de decisao humana, nao de um push

Validação:
- `pg_test_align_fleet_framework.ps1` passa de 51 para **58 verificacoes**, com um repositorio divergente montado de raiz no andaime (publica-se um commit, recua-se o local, cria-se o commit local) e asserçoes que travam os dois enganos: um divergente nao pode dizer «publicar», e um que so esta a frente nao pode ser reportado como divergente
- `checkout_branch` (10), `preflight_versao` (11), `work_folder` (24), `local_overrides` (11) e `pt_accents` a passar

Backlog:
- novo `PG-008` em `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` (issue #59), pedido por Bruno Pinheiro: em modo automatico, **alertar em vez de bloquear**. O gate actual recusou nesta sessao o `-Apply` do alinhador e um `write` no Odoo da Parametro Global, nenhum deles com alternativa; e em modo manual a confirmacao por cada acao trivial leva a responder «sim» por habito, o que nao protege de nada. A escrita em producao de clientes nao e abrangida e continua a exigir autorizacao

## v2.28.0 - 2026-09-11

Status:
- a framework passa a entregar PDF, e passa a ter **uma** paleta da marca em vez de duas

Resumo:
- **a framework tinha caminho de saída para PPTX, para Word e para HTML colável, e não tinha para PDF.** Na prática, entregar um documento ao cliente era entregar-lhe um `.md` em bruto ou converter à mão. Novo `pg_build_pdf_from_markdown.py`: o conteúdo continua a sair do template em Markdown — o que fica versionado e se revê em diff — e o PDF é gerado a partir dele
- **o que justifica o conversor é a paginação, não a conversão.** `thead { display: table-header-group }` repete o cabeçalho da tabela em cada página; `page-break-inside: avoid` impede uma linha de se partir; `page-break-after: avoid` impede um título de ficar órfão. Foi o caso real que lhe deu origem: uma folha de classificação de 44 artigos para o cliente preencher, que sem isto se parte a meio sem cabeçalho e fica inútil
- **motor: Chromium do Playwright**, decisão de dependência tomada por Bruno Pinheiro a 2026-09-11. Custa ~150 MB de binários por máquina e um comando de instalação à parte (`python -m playwright install chromium`); em troca é um motor de layout a sério, com suporte real das regras de impressão acima, e é o mesmo que já serve a captura de ecrãs para documentação — não é uma dependência só para isto. Quando falta, o conversor falha **a dizer o comando exacto** que resolve
- `--subtitulo` aceita `@ficheiro`: em Windows os acentos perdem-se a passar por argumentos de linha de comando, e um PDF real saiu com «Mobiliario» em vez de «Mobiliário»

A paleta, que é o achado desta release:
- a regra da identidade visual existe para que dois documentos gerados em projetos diferentes saiam iguais. `FACTO OBSERVADO`: havia **duas paletas** e divergiam — azul de acento `#009FE3` no módulo de PowerPoint, `#0094E9` no de Word. Cada módulo declarava o seu próprio ficheiro da marca, pelo que a divergência **parecia legítima**
- amostradas as cores efectivamente usadas no conteúdo dos dois ficheiros da marca: o template PowerPoint traz `#009FE3` 30 vezes e `#111827` 58; o template Word traz `#4F81BD` 46 vezes, que é o **accent1 do tema de fábrica do Office 2007**, e ambos os ficheiros trazem temas de fábrica, diferentes entre si. Ou seja: a identidade Parâmetro vive no conteúdo do template PowerPoint, e o template Word está em grande parte por marcar
- o `#0094E9` do módulo Word **não corresponde a nenhum dos dois ficheiros** — era um valor aproximado
- novo `pg_brand_palette.py`, fonte única para os três formatos, com esta evidência inscrita no próprio módulo. `pg_pptx_identity.py` e `pg_docx_identity.py` passam a importar dali

Mudança visível num entregável (ler antes de gerar documentos):
- os documentos **Word** gerados a partir de agora saem com o azul `#009FE3` em vez de `#0094E9`. É a correcção, não um efeito colateral — mas é uma alteração de aspecto num formato que vai para o cliente, e um documento regerado não fica idêntico ao que foi entregue antes desta versão. Os decks PowerPoint não mudam: a paleta partiu deles

Dependências:
- novo `requirements.txt` na raiz. `FACTO OBSERVADO`: a framework dependia de `python-docx`, `python-pptx`, `markdown` e `playwright` sem o declarar em lado nenhum — quem clonasse o repositório numa máquina nova descobria-o por erro de import, e o `pg_odoo_migration_guard.py` chega a declarar no cabeçalho «Dependências: nenhuma além da biblioteca standard» (verdade para aquele ficheiro, falso para o conjunto). A lista foi levantada dos imports reais de `scripts/*.py`, não de memória
- e o `.gitignore` ia engoli-lo: a regra `/*.txt` da raiz, criada para travar despejos de consultas com dados de clientes, ignorava também o `requirements.txt`. Escrito, ignorado, e só apanhado ao commitar. Passa a ter excepção explícita — um ficheiro permanente entra por regra, não por `git add -f`, que a próxima pessoa não se lembra de usar

Validação:
- novo `scripts/tests/test_pg_build_pdf.py`: **16 testes**, dos quais um ponta-a-ponta que gera um PDF a sério com uma tabela de 44 linhas e o volta a ler com `pypdf` para confirmar que paginou, que os acentos sobreviveram e que o cabeçalho da tabela **repete** na segunda página. Os testes da paleta travam a regressão que deu origem a tudo isto: se os dois módulos voltarem a divergir, falham
- verificado no `.docx` gerado depois da mudança: `#009FE3` presente, `#0094E9` sem qualquer ocorrência residual
- `pg_test_python_suites` (7 suites, **107 testes**), `align_fleet_framework` (51), `work_folder` (24), `local_overrides` (11), `preflight_versao` (11), `checkout_branch` (10), `untrack_local_state` (10), `context_hygiene`, `token_consumption` e `pt_accents` a passar

Nota sobre o que isto não resolve:
- o `requirements.txt` declara as dependências; não as instala em ninguém. Cada máquina da frota precisa dos dois comandos uma vez, e o Chromium não vem no `pip install`. Até lá, o conversor de PDF falha nessas máquinas — a falhar bem, com o comando que resolve, mas falha.
- o template Word da marca continua por marcar. Esta release alinha os **geradores** pela identidade que existe; não corrige o ficheiro da marca, que é trabalho de quem o mantém.

## v2.27.0 - 2026-09-11

Status:
- a framework passa a cobrir pastas de trabalho que não são repositórios — decisão de perímetro tomada por Bruno Pinheiro a 2026-09-11

Resumo:
- **a framework cobria repositórios, e boa parte do trabalho de Odoo não acontece em repositórios.** `FACTO OBSERVADO` (auditoria do givachoice): as duas migrações completas da base de produção e o desenvolvimento dos módulos custom decorreram em `C:\Odoo\PGAddons`, `C:\Odoo19\pgmodules` e `MIGRV18` — pastas de servidor, sem `.pg`, sem espelho, sem `AGENTS.md`
- **o agente já procurava.** Em 46 conversas procurou o `AGENTS.md` nessas pastas **7 vezes**, não encontrou nada em nenhuma, respondeu «não existe, continuo», e seguiu sem os factos do projeto. Seis incidentes de confusão entre Odoo 17, 18 e 19 depois — incluindo um deploy de código v17 sobre o servidor de testes v19, recuperado de um backup manual feito por sorte
- por isso a âncora **não é uma convenção nova**: é um `AGENTS.md`, no único sítio onde o agente já olha por conta própria. Novo `pg_init_work_folder.ps1` declara ali, num comando, o que é verdade na pasta: versão do Odoo, edição, servidor, base de dados, o que é só de leitura, o que não se faz
- **a versão é confirmada contra o source, não declarada de boa fé.** Com `-OdooSourcePath`, é lida do `release.py`; e declarar uma versão que o source contradiz **falha e não escreve nada** — é exactamente o erro que custou o deploy de v17 sobre o v19
- **bloco delimitado, e não o ficheiro inteiro.** Tudo o que estiver fora dos marcadores é de quem trabalha na pasta e sobrevive a qualquer reexecução. A framework já destruiu overrides locais uma vez por copiar um template por cima (achado D1); aqui não se repete. E o script recusa-se a correr numa pasta que já seja repositório da framework
- **o ritual passa a ter resposta.** Era esta a metade que faltava: uma âncora que ninguém lê não vale nada. O preflight reconhece o bloco, recita os factos, deriva a documentação da série certa, e recusa quando os factos declarados contradizem o source. Não escreve `.pg` — a pasta não leva estrutura da framework só por ter sido inspecionada
- como no `PROJECT_PROFILE.json`, é por **declaração explícita**: sem o marcador, nada muda

Validação:
- novo `pg_test_work_folder.ps1`: **24 verificações**, incluindo o conteúdo de quem trabalha na pasta a sobreviver à reexecução, o bloco a não se duplicar, a incoerência versão-vs-source a falhar sem escrever, a recusa sobre um repositório da framework, e o ritual a concluir na pasta sem lá criar `.pg`
- `pg_test_python_suites` (6 suites, 91 testes), `preflight_versao` (11), `context_hygiene`, `token_consumption`, `local_overrides` (11), `checkout_branch` (10), `align_fleet_framework` (51), `untrack_local_state` (10), `pt_accents` a passar

Nota sobre o que isto não resolve:
- declarar os factos de uma pasta é um ato humano, feito uma vez por pasta. A framework passa a ter onde os guardar e a lê-los; não os adivinha. As pastas do givachoice continuam por declarar até alguém correr o comando nelas.

## v2.26.0 - 2026-09-11

Status:
- a versão do Odoo deixa de poder ser um palpite com aparência de facto

Resumo:
- **o passo 3 do ritual existe para garantir que a versão está confirmada, e não garantia.** `Get-ProjectGovernance` percorria todos os `project.json` e ficava com o **último** que tivesse versão preenchida: num repositório multi-projeto, a ordem de travessia do disco decidia qual. Quando não há rótulo `Versao do Odoo:` no `PG_CONTEXT.md`, era daí que a versão vinha — e o preflight dava `pass` sobre ela
- `FACTO OBSERVADO`: **16 dos 32 repositórios da frota não têm o rótulo**, e dependiam todos desse caminho
- sem rótulo e com as versões da governance em desacordo, a versão passa a ser **erro** («não confirmada»), não um aviso. Com rótulo, o desacordo continua a ser reportado, mas a resolução deixa de ser arbitrária
- **nova verificação cruzada entre as duas autoridades independentes**: o que o Odoo declara (governance do espelho) contra o que o source **é** (`release.py`). O rótulo do `PG_CONTEXT` não serve de testemunha aqui, porque é derivado; o que vale a pena confrontar é o Odoo com o código que o agente vai mesmo ler

Dois casos vivos, encontrados à primeira passagem pela frota:
- **Evostone** declarava 19.0 com o source em 18.0. O valor tinha sido corrigido na fonte a 27/08 — o próprio `PG_CONTEXT.md` regista a decisão em prosa — e o rótulo escrito à mão continuou a declarar 19.0 por cima dela durante duas semanas. Corrigido para 18.0 (versão real confirmada por Bruno Pinheiro)
- **PadraoMagistral** declara **18.0** no Odoo e tem o `vendor/odoo_src` em **19.0**. Quem lá trabalhar está a ler o código da versão errada. `PONTO POR VALIDAR`: qual dos dois está certo
- `PONTO POR VALIDAR`: o repositório do **Evostone** contém `.pg/projects/odoo-padrao-magistral/` — dados de espelho de outro projeto, o que explica a governance que ali se lia

Um desenho que foi construído e revertido, porque estava errado:
- a primeira abordagem foi ligar o `pg_sync_pg_context.ps1` ao ritual, para **reescrever** os rótulos do `PG_CONTEXT.md` a partir do source. Funcionava, e foi provado a funcionar. Mas o publisher **regenera** o `PG_CONTEXT.md` a partir do espelho: os rótulos seriam apagados pelo publisher e repostos pelo ritual, indefinidamente. É a mesma armadilha do AUD-04 — um campo volátil num ficheiro versionado gera ruído permanente —, e um ficheiro sujo escrito pela própria framework foi o que bloqueou o passo 1 do ritual no givachoice. Revertido antes de sair daqui
- do que se construiu nessa tentativa fica o que é bom por si: o `pg_sync_pg_context.ps1` **deixa de escrever quando nada muda**. Carimbava a hora a cada execução, pelo que qualquer corrida produzia um diff; agora compara ignorando o carimbo, e quando corrige a versão declarada **diz de que valor para que valor**

Validação:
- novo `pg_test_preflight_versao.ps1`: **11 verificações** com repositórios de fixture — o caso exacto do givachoice (multi-projeto, sem rótulo, 17.0 contra 19.0) a dar erro; o mesmo com rótulo a resolver sem ambiguidade; governance contra source a discordar; o caso saudável a não inventar problema; e um único projeto sem rótulo a resolver-se pela governance sem alarme
- preflight corrido sobre a frota: **27 passam, 6 falham** — os mesmos 5 de sempre, por pré-condições em falta, mais o PadraoMagistral, que é achado verdadeiro
- `pg_test_python_suites` (6 suites, 91 testes), `context_hygiene`, `token_consumption`, `local_overrides` (11), `checkout_branch` (10), `align_fleet_framework` (51), `untrack_local_state` (10), `pt_accents` a passar

## v2.25.0 - 2026-09-11

Status:
- o registo de consumo passa a dizer **quem** fez a sessão, e não só que ela aconteceu

Resumo:
- **o log é commitado no repositório e agrega todas as máquinas — mas não dizia quem.** O `repo_path` é idêntico em toda a frota, porque o utilizador local se chama `Utilizador` em todas as máquinas, e não havia campo de operador. `FACTO OBSERVADO`: foi exactamente isso que obrigou a auditoria do givachoice a pedir extrações a colegas, máquina a máquina, para reconstruir decisões que o log tinha contado sem atribuir. Auditoria: [PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md](docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md), lacuna L3
- schema `1.3` com dois campos, e a distinção entre eles é o ponto: **`machine`** é o discriminador fiável, detetado do sistema; **`operator`** é a identidade **declarada** no git e vale o que a configuração valer — na mesma auditoria, 205 commits de três pessoas diferentes saíam todos com o mesmo nome. Um diz onde; o outro diz quem se assumiu ser. Nenhum é prova de autoria, e o relatório di-lo
- os **três escritores** do log passam a registá-los: o logger manual (com `-Machine`/`-Operator` para casos em que a deteção não serve), o hook do Claude e o hook do Codex — este último estava ainda no schema `1.1` e nunca tinha recebido os campos de contabilidade da v2.22.0
- a resolução é feita **em linha nos três**, e não num helper partilhado: os hooks são à prova de falhas por desenho e não devem ganhar dependências de ficheiro para quatro linhas
- o relatório agrupa por máquina e por operador, e avisa quando as sessões são anteriores a esta versão — sem identidade não se sabe quem fez o trabalho, e dizê-lo é melhor do que apresentar uma coluna vazia como se fosse um dado
- o validador recusa `machine` ou `operator` **vazios**: pior do que ausentes, porque parecem preenchidos. Quando não se sabe, escreve-se `unknown`

Validação:
- `pg_test_token_consumption.ps1` com verificações novas: identidade detetada do git do repositório, `unknown` quando não há git configurado, identidade explícita a mandar sobre a detetada, e o validador a recusar campo vazio nomeando-o
- prova ponta-a-ponta nos dois caminhos: pelo logger (`machine=PGBPINHEIRO`, operador lido do `user.email`) e pelo hook do Claude, que continua a separar corretamente as releituras de cache (input 300, cache 50 000)
- o teste antigo que exigia schema `1.2` no fecho do hook **reprovou** com a mudança, como devia, e foi atualizado
- `pg_test_python_suites` (6 suites, 91 testes), `local_overrides` (11), `checkout_branch` (10), `align_fleet_framework` (51), `untrack_local_state` (10), `context_hygiene`, `pt_accents` a passar

Nota sobre o histórico:
- as sessões anteriores não ganham identidade retroactivamente. O log é *append-only* e o que passou fica sem atribuição — é o que torna a Fase B da auditoria do givachoice dependente de pedidos manuais a colegas. A partir daqui deixa de ser preciso.

## v2.24.0 - 2026-09-11

Status:
- o que a auditoria de desempenho do givachoice mandou corrigir: a regra que faltava, e os três danos com prova

Contexto: [PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md](docs/PG_AUDITORIA_DESEMPENHO_GIVACHOICE.md). O givachoice é o único projeto que adotou a framework a meio da execução, e a conclusão da auditoria é que **ela não correu mal por ser pesada — correu mal por ser rígida**.

Resumo:

**A regra que faltava.** A ordem obrigatória de decisão é um método para escolher *o que construir*; não havia nenhuma regra que protegesse *o que já funciona*. Nova secção «Antes de alterar o que já funciona» no `AGENTS_SHARED.md`: são dois riscos e o ensaio só apanha um — *isto parte alguma coisa?* apanha-se com resguardo e verificação; *isto é o que eles querem?* **nenhum ensaio apanha**. Quatro passos antes de propor qualquer alteração de comportamento, e o corolário: uma correção que ninguém pediu tem de passar uma barra **mais alta**, não mais baixa por ser pequena. A regra não é nova — foi escrita à mão na memória do givachoice a 26/08, depois do dano, e não chegava a mais nenhum projeto.

**O sync destruía o mecanismo de adaptação que a própria framework anuncia.** O `AGENTS.md` diz de si próprio que serve «para registar overrides locais», e o sync copiava o template por cima dele com `-Force` — enquanto preservava o `PG_CONTEXT.md` e o `PG_SCOPE_INTAKE.yaml`. `FACTO OBSERVADO`: um re-sync apagou **41 linhas** do `AGENTS.md` do givachoice, a secção que dizia onde estava o código vivo dos servidores; a equipa deixou de confiar no ficheiro e passou a guardar as regras locais em memórias do agente, que não viajam com o repositório. Novo `Merge-PgLocalOverrides`, pelo mesmo padrão do `.gitignore`: o que está depois de `## Overrides locais do projeto` sobrevive.

**O passo 1 do ritual impunha a branch errada.** `pg_checkout_brodoo_branch.ps1` tinha `brodoo` fixo no código e só consultava o `project.json` quando `brodoo` **não** existia. No givachoice — que declara `audit` e tem `brodoo` como linhagem antiga — o ritual levava a sessão para uma branch com **1698 commits de divergência**, sem os dados do projeto e com outra árvore de addons; produziu pelo menos uma conclusão factual errada a 06/08. O `pg_align_fleet_framework.ps1` já respeitava a declaração: **eram dois scripts da mesma framework a discordar um do outro**. A declaração passa a mandar; `main` continua recusada, que é para isso que o standard existe; e declarações em desacordo param em vez de se escolher uma ao acaso.

**O preflight validava a presença do source e nunca a sua coerência.** Passa a ler a série real do `release.py` e a recusar quando o projeto declara uma série e o source é outra — foi essa lacuna que deixou passar onze dias de documentação de 17.0 num projeto em 19.0. `FACTO OBSERVADO`: a primeira passagem sobre a frota encontrou uma instância viva — o **Evostone declara 19.0 e tem o source em 18.0**.

**A resolução da versão em multi-projeto deixa de ser ao acaso.** `Get-ProjectGovernance` percorria todos os `project.json` e ficava com o **último** que tivesse versão; a ordem de travessia decidia. Passa a preferir o namespaced sobre o legacy da raiz — o que o `AGENTS_SHARED` já mandava — e a avisar quando há versões em desacordo, em vez de as esconder. O givachoice, com 17.0 e 19.0 declarados, passa a dizê-lo.

Validação:
- novo `pg_test_local_overrides.ps1` (**11 verificações**) e novo `pg_test_checkout_branch.ps1` (**10**, com fixtures git reais, incluindo o caso exacto do givachoice)
- prova ponta-a-ponta num repositório da frota: override colocado no `AGENTS.md` do CNM, sync corrido, override sobreviveu e o sync anunciou-o; reposto a seguir
- ritual corrido nos repositórios reais: `givachoice` fica em `audit` (declarada), `Essani` e `MIMO` em `Test` (declarada), `CNM` mantém `brodoo` com aviso de desacordo. Antes, os três últimos eram empurrados para `brodoo`
- preflight corrido sobre a frota: **27 passam, 1 nova falha** — e é verdadeira
- `pg_test_python_suites` (6 suites, 91 testes), `align_fleet_framework` (51), `token_consumption`, `untrack_local_state` (10), `context_hygiene`, `pt_accents` a passar

Por fazer, desta mesma auditoria: atribuição de operador no registo de consumo — sem ela a frota regista que uma sessão aconteceu, nunca quem a fez.

## v2.23.2 - 2026-09-10

Status:
- o ponto de entrada operativo deixa de poder mentir sobre a versão, e a poda de ramos devolve o repositório a quatro

Resumo:
- **o `PG_CURRENT_WORKING_STATE.md` anunciava `v2.9.1` com o `CHANGELOG` em `v2.23.1`** — catorze releases de atraso, num ficheiro declarado como ponto de entrada operativo único e lido por agentes. O `BLK-000` do backlog existiu para corrigir exactamente esta divergência, foi dado por fechado em 2026-05, e ela regressou
- **a correção não foi atualizá-lo, foi tirar-lhe o facto duplicado.** A versão da release deixa de viver ali: vive na primeira entrada do `CHANGELOG.md`, e o documento aponta para lá. Um facto derivável guardado em dois sítios envelhece sempre num deles, e a disciplina de atualizar os dois é precisamente o que já falhou uma vez
- o que fica no documento é o que **não** é derivável — frente dominante, bloqueio, próximo passo — e vai **datado**, porque esse juízo decai na mesma e a data é o que diz a quem lê se ainda pode confiar nele. A regra de conflito passa a dizer isso explicitamente: com a data meses atrasada, o documento é histórico como outro qualquer
- **novo `scripts/tests/test_pg_docs_coerencia.py`**: o estado operativo não pode voltar a declarar uma versão, tem de apontar para o `CHANGELOG` e tem de trazer data; o `PG_TEMPLATE_VERSIONING.md` — onde a duplicação é deliberada, por ser um registo — tem de coincidir com o `CHANGELOG`; e a entrada do topo do `CHANGELOG` tem de ser a versão mais alta. Validado por mutação: reposta a linha da versão, o teste reprova e nomeia-a
- a verificação distingue **declarar** de **mencionar**: «resumo da release fechada: ... (v2.22.0) ...» conta história e é legítimo; «release fechada: v2.9.1» é um registo que envelhece. Sem essa distinção o teste reprovava os próprios resumos que descrevem o passado
- a ordenação do `CHANGELOG` é verificada por **versão e não por data**: o histórico tem entradas antigas fora de ordem cronológica, e reescrever o passado de outra pessoa para satisfazer um teste seria trocar um problema por outro

Higiene do repositório:
- **52 ramos locais → 4.** Apagados 46 já fundidos na `main`; ficam os três que não estão (`feat/guard-metodos-por-projeto`, do PR aberto, `prod-1.5.0-overlay` e `simplify/pg-brodoo-3-pilares`)
- **16 worktrees → 1.** Treze áreas de trabalho em `C:/tmp` sobravam das vagas AUD-01..04 e M1/M3, de julho. Verificadas uma a uma antes de remover: zero alterações por commitar e zero commits fora da `main` em todas. Duas outras estavam registadas para pastas que já não existiam

Validação:
- `pg_test_python_suites.ps1`: **6 suites, 91 testes**
- `pg_test_align_fleet_framework` (51), `pg_test_token_consumption`, `pg_test_untrack_local_state` (10), `pg_test_context_hygiene`, `pg_test_pt_accents` a passar

## v2.23.1 - 2026-09-10

Status:
- a cobertura de versão da frota deixa de ser lida antes do sync que a altera

Resumo:
- **o contador contradizia o relatório imediatamente acima dele.** O `synced_head` de cada repositório era lido no início, antes de o sync correr; em modo `-Apply` isso torna-o obsoleto no momento de somar, e o resumo anunciava `0 de 33` logo a seguir a listar 25 repositórios publicados com sucesso. Passa a reler do disco antes de contar: agora diz `25 de 33`
- um número que contradiz o que o próprio relatório acabou de listar é pior do que número nenhum, porque ensina quem o lê a não acreditar no relatório

Validação:
- `pg_test_align_fleet_framework.ps1`: **51 verificações** (eram 49). O duplo do sync no andaime passa a escrever o estado de sync, como o real, e o teste exige que depois de alinhar a cobertura não continue a zero
- confirmado na frota: `25 de 33` na versão corrente

## v2.23.0 - 2026-09-10

Status:
- o guard de migração passa a ter testes, as suites Python passam a ser corridas, e a geração de documentos Word deixa de ser invisível

Resumo:
- **o componente de maior consequência do repositório não tinha um único teste.** O `pg_odoo_migration_guard.py` é o ponto único de passagem entre os scripts de migração e o Odoo de um cliente — o que ele proíbe fica proibido para todos. E foi alterado duas vezes no mesmo dia, uma delas resolvendo à mão um conflito entre duas listas brancas independentes, sem nada que acusasse um erro
- **30 testes novos** sobre a máquina de decisão, sem rede: as cinco camadas que uma escrita tem de atravessar, o método não classificado a ser bloqueado, produção a exigir `--allow-prod` sem que isso dispense o `--confirm` nem o `allow_write`, a incoerência de nome de base (`main` declarado como *staging*) a abortar, a normalização do URL do backoffice e a leitura do ficheiro de ligação. Duas invariantes que só se lembram depois de doerem: **nenhum método pode estar nas duas listas** ao mesmo tempo, e os métodos que vieram de cada lado da fusão de hoje têm de continuar lá
- os testes foram validados por **mutação**: com a produção a permitir escrita sem `--allow-prod`, e com o método desconhecido a deixar de ser bloqueado, a suite reprova em ambos os casos. Uma suite que não se testa contra o defeito que existe para apanhar é decoração
- **as suites Python não eram corridas por nada.** Havia cinco ficheiros em `scripts/tests` e só um tinha invocador próprio. Novo `scripts/pg_test_python_suites.ps1`: corre-as todas, cada uma em processo próprio, sem parar na primeira que falhe, e entra no gate mínimo da política de release. São **86 testes** que estavam a passar despercebidos
- **a geração de documentos Word estava construída e invisível.** Entrou no repositório sem referência em documento nenhum: sem entrada no mapeamento de formatos do `AGENTS_SHARED`, nenhum agente a invoca. Passa a ter regra própria, ao lado da dos decks — o conteúdo sai do template em Markdown e a identidade vem de `pg_docx_identity.py`, nunca do documento
- **a raiz do repositório fecha-se a despejos de consulta.** São sete ficheiros seguidos, nenhum `.txt` ou `.json`; tudo o que lá aparece com essas extensões é saída de consulta ad-hoc, e traz dados de clientes. Estavam lá ids e `write_uid` de produção do GLC e nomes de produtos da Vasil, num repositório que também aloja credenciais. A regra é por extensão e não por nome, porque o problema é o hábito e não aqueles ficheiros

Validação:
- `pg_test_python_suites.ps1`: **5 suites, 86 testes**, todas verdes
- mutações confirmadas a reprovar, uma por camada de proteção
- `pg_test_align_fleet_framework` (49), `pg_test_token_consumption`, `pg_test_untrack_local_state` (10), `pg_test_context_hygiene`, `pg_test_pt_accents` a passar

## v2.22.1 - 2026-09-10

Status:
- um `-RepoNames` que não resolve nada deixa de sair em silêncio como se tivesse corrido bem

Resumo:
- **a invocação que o próprio ritual manda usar quebra o parâmetro.** `powershell -File <script> -RepoNames a,b,c` entrega a lista como **um único nome** (`"a,b,c"`); o caminho não existe, nenhum repositório resolve, e o script saía com `0` e sem escrever relatório. `FACTO OBSERVADO`: ao repetir o alinhamento de quatro repositórios cujo *push* tinha perdido a corrida com o publisher, o comando devolveu êxito e não fez absolutamente nada — o modo de falha mais caro que há, porque se lê como sucesso
- um pedido explícito que não resolve nada passa a ser **erro** (`exit 1`), com os nomes pedidos e a forma correta de passar um array: invocar em processo, `& <script> -RepoNames @('a','b')`. Sem `-RepoNames`, uma frota vazia continua a ser apenas um aviso — aí não há pedido nenhum a falhar

Validação:
- `pg_test_align_fleet_framework.ps1`: **49 verificações** (eram 47). A nova exige o erro e a ausência de relatório quando nenhum dos nomes pedidos existe
- alinhamento da frota concluído com esta versão: **25 de 25** repositórios alinháveis publicados

## v2.22.0 - 2026-09-10

Status:
- o medidor de consumo deixa de somar a releitura do contexto, e a métrica-alvo do AUD-03 volta a ser calculável

Resumo:
- **o relatório de consumo da frota declarava 32 537 831 158 tokens em 702 sessões**, com uma média de **204 505 036 tokens por sessão** em modo `api` e uma sessão isolada de **3 676 354 561** (givachoice, 28/08). Nenhum destes números é possível: a maior janela de contexto em uso tem 1 milhão de tokens
- **causa exacta**, em `pg_hook_log_token_consumption.ps1`: o hook somava ao input os três contadores de entrada do transcript, incluindo `cache_read_input_tokens`. Esse contador é o contexto **inteiro** relido do cache em **cada turno**, pelo que o total dava *contexto × número de turnos* e o erro crescia com a duração da sessão
- **a consequência era a tese da framework, não um número feio.** O AUD-03 existe para provar que ler do espelho custa menos do que ir à API. O rácio de 285× que o relatório exibia (`mirror` 714 989 contra `api` 204 505 036 tokens/sessão) media sobretudo o comprimento das sessões, e não o modo de leitura. `FACTO OBSERVADO`: a primeira sessão registada com a contabilidade corrigida tem 2 455 713 tokens de material distinto contra 113 501 379 de releituras de cache — um factor de 46× numa única sessão
- **`estimated_input_tokens` passa a ser o volume de material distinto** (entrada nova mais escrita de cache). As releituras vão para `cache_read_input_tokens`, em campo próprio: contam para custo, nunca para volume. Schema `1.2`, com `token_accounting` a declarar como o número foi contado (`unique_input_v2`, `cache_summed_v1` ou `unknown`)
- **o relatório nunca mistura as duas contabilidades.** A métrica-alvo é calculada exclusivamente sobre registos `unique_input_v2`; enquanto não houver nenhum, imprime `SEM DADOS` e explica porquê — em vez de exibir um rácio que se lê como prova. O histórico continua nos totais por projeto e por agente, com o aviso
- **quarentena por grandeza**: sessões acima de 20 milhões de tokens ficam fora de todas as médias. Não é um limite de gosto — acima disso não há sessão pesada, há erro de contagem. São 102 sessões da frota, e uma delas sozinha deslocava o total
- **o validador passa a olhar para a grandeza, e não só para a forma.** Era exactamente esta a lacuna: em 2026-08 o validador **já tinha visto** 2 676 726 927 tokens numa linha do givachoice, diagnosticou o problema como sendo o seu próprio cast `[int]`, alargou-o para `[long]` e deu a linha por válida. O formato estava certo; o número é que era impossível
- `[long]` em vez de `[int]` também no hook e no logger: um `[int]` do PowerShell que transborda é promovido a `[double]` e passa a escrever valores arredondados
- **o hook do Codex não tinha o defeito** — lê o `total_token_usage` cumulativo do rollout, que é um valor único e não uma soma por mensagem. Só o do Claude foi tocado
- `AGENTS_SHARED.md` deixa de afirmar que o transcript **subconta**. Afirmava o contrário do que acontecia, com um erro de duas a três ordens de grandeza, e era essa frase que dispensava qualquer dúvida sobre os números

Validação:
- `pg_test_token_consumption.ps1`: **seis verificações novas**. A central reintroduz o defeito e exige que ele reprove — transcript com três turnos de 50 000 tokens de cache, que tem de dar 900 de input e não 150 900. Confirmado com o defeito reposto: o teste falha e nomeia o valor errado
- cobertura também para o campo próprio das releituras, o `token_accounting` no fecho, contadores acima do limite do `[int]`, `token_accounting` inválido como erro, grandeza implausível como aviso, e o relatório a separar contabilidades e a pôr em quarentena
- `pg_test_pt_accents`, `pg_test_context_hygiene`, `pg_test_untrack_local_state` (10) e `pg_test_align_fleet_framework` (34) a passar
- relatório corrido sobre os 35 logs da frota: 600 sessões agregadas, 102 em quarentena, uma já com contabilidade v2
- `pg_test_align_fleet_framework.ps1`: **42 verificações** (eram 34). As oito novas cobrem o repositório elegível sem link a aparecer no relatório com a remediação, a pasta não elegível a continuar de fora, o cabeçalho a anunciar quantos estão fora do perímetro, e a contagem de cobertura de versão com e sem estado de sync
- auditoria real da frota depois da alteração: 32 repositórios no perímetro, 2 fora (um clone duplicado do `HMD` e o repositório do addon)

Estado da frota depois da intervenção operacional de 2026-09-10:
- **repositórios alinháveis: 18 → 25** (de 32 no perímetro); bloqueados: 14 → 7
- **declarações em `main` no Odoo: 1 → 0.** A única real era o projeto 129 «Odoo - CasaMagna website», que partilha o repositório `Triplex` com o projeto 62 (já em `brodoo`) e nunca tinha publicado (`never`). Migrado para `brodoo` com autorização explícita — impedia que o espelho viesse a escrever ficheiros de framework na produção do cliente. Nenhum projeto da frota fica com repositório sem branch declarada
- **seis clones postos na branch que o Odoo declara** (`CarlaZuzarte`, `Limite-Crucial`, `Piccolo`, `Triplex`, `givachoicefase1`, `Studiomad`), mais o `Essani` em `Test`. O estado local de framework foi para *stash* em cada um, e não descartado: é regenerável pelo sync, mas apagar trabalho sem rede não é decisão de quem passa
- o `.pg/PREFLIGHT.json` voltou a bloquear, agora no `checkout`: está ignorado localmente e versionado na branch de destino, pelo que o git recusa sobrepô-lo. É apagado e regenerado no arranque seguinte
- **três casos ficam por resolver, por exigirem decisão humana**: o `ancoravip` tem um documento local que colide com o publicado; o `domusacropoles` declara a branch `Teste`, que não existe no remoto (há `teste`, `Teste-cap` e `Teste-remote`, e o git em Windows casa com a errada por ser insensível a maiúsculas) — foi reposto exactamente como estava; e cinco repositórios têm entre 4 e 228 commits de outra pessoa por publicar

Também nesta versão (trabalho que estava na árvore, com commit próprio):
- **cartão de estado global opcional no ponto de situação PPTX**: `mostrar_estado_global: false` no payload retira-o e a fila reparte a largura pelos restantes indicadores. Serve os pontos de situação em que não se quer pôr uma etiqueta de saúde à frente do cliente
- **lista branca do guard de migração estendida** com os métodos dos módulos do Givachoice: reabastecimento manual (`action_refresh`, `action_rebuild_all`, `action_replenish_selected`, `pg_launch_replenishment`), assistentes de confirmação do armazém, criação de lotes na receção e regeneração da lista de materiais. Um método não classificado é bloqueado — pode escrever sem se saber — pelo que classificá-los é o que os torna utilizáveis

Nota de leitura do histórico:
- os registos anteriores a esta versão não se corrigem: o log é *append-only* e o transcript de origem nem sempre existe. Ficam identificados pela ausência de `token_accounting` e fora da métrica-alvo. **A comparação entre espelho e API está, hoje, por demonstrar** — e volta a ser demonstrável a partir das sessões que se seguirem

Perímetro e cobertura da frota:
- **descobrir a frota pela presença do symlink tornava invisível o repositório que o perdeu.** Em vez de aparecer avariado, desaparecia — e a auditoria, o smoke test e o alinhador descobrem-na todos da mesma maneira, pelo que desaparecia dos três ao mesmo tempo. `FACTO OBSERVADO`: o `artful` e o `domusacropoles`, ambos com espelho publicado pelo Brodoo, estavam fora do perímetro sem que nada o dissesse. Ambos ligados nesta data
- o alinhador passa a reportar como `sem_framework` qualquer repositório **elegível** (com `.pg/` ou `PG_CONTEXT.md`) sem o link, com a remediação na razão. Uma pasta que não é elegível continua a não ser da sua conta. Não conta para o código de saída: resolver exige uma decisão humana, e um check permanentemente vermelho treina qualquer pessoa a ignorar o resultado
- **a auditoria passa a dizer em que versão está a frota**, e não só o que faria: lê o `PG_TEMPLATE_SYNC_STATE.json` de cada repositório e resume `repos_na_versao` de `repos_total`. `FACTO OBSERVADO`: **5 de 34**, e os cinco eram exactamente aqueles onde tinha havido sessão nos dias anteriores — a auto-atualização por sessão funciona, mas não chega a repositórios que ninguém abre
- `PG_RELEASE_POLICY.md` ganha o passo 11: uma release publicada não é uma release adotada. Fica documentado o que o alinhador **não** resolve — trabalho alheio por publicar, e repositórios sem link — porque automatizar o gatilho sem resolver esses casos produziria um trabalho permanentemente vermelho
- **o alinhador mandava corrigir o sítio errado.** A branch Brodoo é resolvida a partir do `project.json` do espelho **local**, que pode estar meses atrasado; quando dizia `main`, o script concluía que a declaração no Odoo estava errada e mandava migrá-la. `FACTO OBSERVADO`: dos sete repositórios reportados assim, **seis já estavam declarados `brodoo` no Odoo havia meses**, com o espelho a publicar sem falhas — o que estava velho era o clone. A guarda passa a fazer `fetch` antes de concluir: se existir `origin/brodoo`, a causa é o clone e a remediação é `pg_checkout_brodoo_branch.ps1`, não o Odoo

## v2.21.2 - 2026-08-24

Status:
- o alinhador desbloqueia o estado local **antes** do merge e resolve conflitos que só envolvam ficheiros da framework

Resumo:
- **a correcção da v2.21.1 estava no sítio errado da sequência.** O desversionamento do `.pg/PREFLIGHT.json` foi posto no `pg_sync_shared_assets.ps1`, que no alinhador corre **depois** do merge — pelo que nunca chegava a desbloquear nada. `FACTO OBSERVADO`: no `-Apply` seguinte, cinco repositórios (`jmmgroup`, `Mercado-Abastecedor`, `odoosh`, `SmartEnergy`, `sofmovelsh`) continuaram em `merge_recusado`, com o ficheiro ainda no índice. A função passou para `pg_file_io_common.ps1`, partilhada pelos dois scripts, e o alinhador chama-a antes do merge
- **sair do índice não bastava.** Desversionado, o ficheiro fica no disco como **não seguido** — e o git recusa-se igualmente a sobrepor um ficheiro não seguido durante o merge. No alinhador, o estado local sai também do disco; é regenerado pelo `pg_preflight_context.ps1` no arranque seguinte. O sync mantém-no, porque lá não há merge a desbloquear
- **e depois disso o conflito passou a ser no próprio ficheiro**, em `delete/modify`: nós apagamos, o lado remoto alterou. O estado local entra no padrão de âmbito da framework e resolve-se mantendo a remoção — `checkout --ours` não serve para um ficheiro apagado
- **conflito exclusivamente em ficheiros de framework deixa de abortar.** O conteúdo destes ficheiros não se negocia entre lados: é regenerado a partir do template pelo sync idempotente do passo seguinte. Abortar deixava o repositório eternamente preso — foi o caso do `Essani`. Conflito **fora** do âmbito continua a abortar, que é onde não há resolução automática segura. O relatório passa a trazer `resolved_conflicts`
- **a razão da recusa passa a nomear os ficheiros.** A mensagem útil do git vem em várias linhas — o cabeçalho `error: Your local changes ... would be overwritten by merge:` seguido da **lista** — e guardar só a primeira linha dava um diagnóstico sem o dado que interessa
- `String.Replace` em vez do operador `-replace` na construção do caminho: o operador trata a substituição como padrão e deixava duas barras invertidas, pelo que o `Test-Path` nunca encontrava o ficheiro e a remoção não acontecia em silêncio

Validação:
- `pg_test_align_fleet_framework.ps1`: **34 verificações** (eram 26). As três novas cobrem estado local versionado a bloquear o merge, conflito só em ficheiros de framework a resolver-se com o conteúdo regenerado pelo sync, e a razão da recusa a nomear o ficheiro que bloqueia
- `pg_test_untrack_local_state.ps1` (10), `pg_test_pt_accents`, `pg_test_context_hygiene`, `pg_test_token_consumption` a passar
- `pg_smoke_test_repo.ps1` sem erros no `PRIacademia` e no `GBUK`

## v2.21.1 - 2026-08-24

Status:
- o `.pg/PREFLIGHT.json` deixa de estar ignorado e versionado ao mesmo tempo, o que bloqueava o alinhamento da frota

Resumo:
- **o `.gitignore` não desversiona o que já está seguido.** A v2.20.0 acrescentou o `.pg/PREFLIGHT.json` ao `.gitignore` do template — é estado local da máquina, regenerado a cada arranque e com o path absoluto de quem correu o preflight — mas nada o retirava do índice dos repositórios que já o versionavam. `FACTO OBSERVADO`: está seguido em **11 repositórios** da frota (`besimple`, `ENIGMAF`, `givachoice`, `GLC`, `HMD`, `jmmgroup`, `Mercado-Abastecedor`, `odoosh`, `reckon.ai`, `SmartEnergy`, `sofmovelsh`), cinco deles já com a regra de ignorar aplicada — o pior dos dois mundos
- **e era o bloqueador real do alinhamento.** Nos cinco repositórios que ficaram presos no primeiro `-Apply` do `pg_align_fleet_framework.ps1`, o `.pg/PREFLIGHT.json` aparece em todos como ficheiro modificado localmente que os commits a entrar também alteram — a condição exacta que faz o `git merge` recusar-se a começar. Sem o desversionar, cada alinhamento futuro da frota volta a bater no mesmo sítio
- **`pg_sync_shared_assets.ps1` passa a desversionar (`git rm --cached`) o estado local declarado**, mantendo o ficheiro no disco: continua a ser útil localmente, o que não pode é viajar entre máquinas. A regra no `.gitignore` e o desversionamento passam a andar juntos, no mesmo passo
- **a lista é explícita, não uma varredura pelas regras do bloco.** O bloco tem padrões largos (`.vscode/`, `*.log`, `.idea/`) e um projeto pode versionar algum deles de propósito; desversionar por inferência apagaria trabalho alheio do índice. Há teste dedicado a isso: um `.log` versionado deliberadamente tem de sobreviver
- **terceira ocorrência do mesmo defeito de plataforma nesta série.** `git ls-files --error-unmatch` escreve no stderr quando o ficheiro **não** está seguido — o caso normal na segunda passagem — e com `ErrorActionPreference = Stop` isso termina o script. O sync passava a falhar logo **depois** de ter desversionado com sucesso. Resolvido sem `--error-unmatch` (saída vazia já significa "não seguido") e isolando o `ErrorActionPreference` em volta das chamadas nativas

Validação:
- `pg_test_untrack_local_state.ps1`: 10 verificações — desversiona sem apagar, não toca no código do projeto, não desversiona por inferência um `.log` que o projeto quer versionado, é idempotente, e o `.gitignore` passa a ignorá-lo
- `pg_test_align_fleet_framework.ps1` (26), `pg_test_pt_accents`, `pg_test_context_hygiene`, `pg_test_token_consumption`, `pg_test_odools_setup` a passar
- `pg_smoke_test_repo.ps1` sem erros no `PRIacademia` e no `GBUK`

Nota de frota:
- apareceu um repositório novo durante o alinhamento, o `GLC`: tem estado de framework e está na branch `brodoo`, mas **sem `.pg_framework` ligado**. Como a auditoria, o smoke test e o alinhador descobrem repositórios pela presença do symlink, está fora do perímetro de tudo. Precisa de `pg_link_framework.ps1`

## v2.21.0 - 2026-08-24

Status:
- o alinhamento dos ficheiros da framework na frota deixa de ser trabalho manual e passa a ser um script auditável

Resumo:
- **o publisher do espelho nunca atualiza os ficheiros da framework.** `FACTO OBSERVADO`: nos commits que o `parametroglobaladmin` escreve nas branches Brodoo (`chore(pg-sync)`, `chore(pg-mirror)`), o `git diff` toca exclusivamente em `.pg/projects/**` e `projects/**`. O `AGENTS.md`, o `CLAUDE.md`, o `config.toml`, o `.gitignore`, o `doc_templates/` e os hooks só mudam quando alguém corre o sync localmente e faz commit. A consequência é que **a cada release do `_pg_template` os 76 repositórios ficam desalinhados** e o alinhamento tem de ser refeito à mão, com a agravante de os clones locais estarem tipicamente centenas de commits atrás — no alinhamento manual desta data, entre 9 e 930
- **novo `pg_align_fleet_framework.ps1`**: percorre a frota, resolve a branch Brodoo declarada, faz `fetch`, commita o estado local dos ficheiros de framework, faz `git merge origin/<branch>`, corre o sync idempotente, commita e publica. Audit-first: sem `-Apply` nada é escrito; `-NoPush` commita sem publicar; `-ReportPath` escreve o relatório em JSON
- **as guardas vêm todas de um erro real cometido no alinhamento manual**, não de hipóteses:
  - **`fetch` imediatamente antes do merge, com retentativas.** O publisher escreve nas branches *durante* a execução. Um merge contra uma referência remota antiga faz o push ser rejeitado como non-fast-forward; foi o que aconteceu a 16 repositórios de uma vez. Nada é forçado: a tentativa seguinte volta a buscar e a fundir
  - **`.pg/projects/**`, `projects/**` e `PG_CONTEXT.md` nunca entram em stage.** São do publisher. Um commit que os inclua, feito a partir de um clone desatualizado, **reverte dados do espelho** publicados entretanto pelo Odoo. Há uma segunda rede de segurança (`Reset-StagedPublisherPaths`) que os retira do index se algum lá chegar
  - **repositórios com commits locais não publicados fora do âmbito da framework são saltados.** Foi isto que impediu publicar 85 commits de auditoria e formação no `givachoice` e 228 no `Hipermercado` — trabalho de outra pessoa, que um `git push` teria levado atrás
  - **branch Brodoo declarada `main` é recusada.** `main` é a produção do cliente e ficheiros de framework não vão para lá. A migração da declaração tem de ser feita no Odoo (`repository_branch` em `pg.odoo.connection`/`project.json`) e o espelho republicado — sem isso, criar a branch localmente não resolve, porque o `pg_checkout_brodoo_branch.ps1` procura a branch *auto-consistente* e devolve `main`
  - **conflito fora do âmbito da framework aborta o repositório**, em vez de o resolver. Dentro do âmbito, resolve e deixa o sync regenerar o conteúdo
  - **o que não foi alinhado é relatado com a razão**, nunca silenciado — um relatório que omite o que saltou lê-se como cobertura total
- **`Invoke-Git` fixa `core.quotepath=false`.** Por omissão o git cita caminhos com bytes não-ASCII (`"doc_templates/assets/N\303\243o confirmado 93645.crdownload"`), e a aspa inicial rebenta qualquer âncora `^` nas expressões de âmbito. Seis repositórios da frota foram classificados como tendo trabalho alheio quando o que tinham era um anexo do Knowledge com nome em português — num framework cujas regras de redação exigem acentuação, é um defeito garantido
- **`Invoke-Git` isola também o `ErrorActionPreference`.** Em Windows PowerShell 5.1 redirecionar o stderr de um executável nativo embrulha cada linha num `ErrorRecord`, e com `Stop` isso aborta o script mesmo quando o git devolveu `0`. O git escreve no stderr rotineiramente (avisos de CRLF, progresso do push), pelo que o modo `-Apply` morria a meio da frota, antes de escrever o relatório — apanhado pelos testes, não em produção

Validação:
- `pg_test_align_fleet_framework.ps1`: 21 verificações, frota falsa em pasta temporária com repositórios git reais e remoto bare. Cobre o modo auditoria não escrever nada, as quatro guardas, a publicação efetiva, os caminhos do publisher ficarem intactos, a corrida com o publisher (commit do publisher a entrar no remoto entre o `fetch` e o `push`) e a regressão do caminho acentuado
- auditoria da frota real (26 repositórios): 16 alinháveis, 10 saltados — 7 por declararem `main`, 1 sem declaração, 2 com trabalho de terceiros não publicado

## v2.20.1 - 2026-08-24

Status:
- a auditoria da frota deixa de sincronizar o `_pg_template` consigo mesmo e de terminar sempre em erro

Resumo:
- **`pg_audit_bootstrapped_repos.ps1` tratava o `_pg_template` como repositório de projeto.** A descoberta de repositórios é feita pela presença de `.pg_framework`, e o próprio `_pg_template` tem um symlink `.pg_framework` que aponta para si mesmo. `FACTO OBSERVADO`: numa auditoria completa da frota, o resumo terminava em `_pg_template: sync=FAIL` com `Cannot overwrite the item ... config.toml with itself` e `exit 1`, apesar de os 25 repositórios de projeto terem passado. Uma auditoria que falha sempre treina quem a corre a ignorar o código de saída, que é precisamente o sinal que ela existe para dar. A descoberta passa a excluir a raiz do framework, por comparação de caminho normalizado
- **o dano era anterior à falha.** O sync aborta no `config.toml` (primeiro ficheiro cujo destino coincide com a origem), mas nesse ponto já tinha substituído o `CLAUDE.md` do `_pg_template` — que é o do repositório do framework — pelo `templates/CLAUDE.md`, o wrapper destinado a projetos; já tinha criado `AGENTS.md`, `.agents/`, `.claude/`, `.codex/` e `.github/` na raiz do framework; e já tinha reescrito o `.gitattributes`. O contrato com os agentes no próprio repositório do framework ficava trocado pelo contrato dos projetos
- **a guarda definitiva vive em `pg_sync_shared_assets.ps1`**, não no chamador. É o ponto único de passagem: `pg_bootstrap_repo.ps1`, `pg_bootstrap_assisted.ps1`, `pg_ensure_framework_current.ps1` e `pg_smoke_test_repo.ps1` chamam-no todos, e o `pg_ensure_framework_current.ps1` corre no hook `SessionStart` — uma sessão aberta na raiz do `_pg_template` reproduziria o mesmo dano a cada arranque. O sync passa a recusar-se, com mensagem explícita, quando o alvo é o próprio framework
- **reparados dois registos de consumo de tokens inválidos** no `Sofmovel` (linhas 17 e 18): o `repo_path` do Windows escrito com barras invertidas simples, em que as sequências resultantes não são escapes válidos em JSON. É exactamente o defeito que o `AGENTS_SHARED` documenta ao exigir que o log seja escrito por `pg_log_token_consumption.ps1` e nunca à mão. Ambas as linhas estavam por commitar, pelo que a reparação não reescreve histórico

Validação:
- `pg_audit_bootstrapped_repos.ps1` sobre a frota local: 26 repositórios `sync=OK; smoke=OK`, `exit 0`
- guarda testada nos dois sentidos: alvo `_pg_template` recusado com `exit 1`; sync de um projeto (`GBUK`) inalterado com `exit 0`
- `pg_test_pt_accents`, `pg_test_context_hygiene`, `pg_test_token_consumption` e `pg_test_odools_setup` a passar

> Nota de numeração: estas duas entradas foram desenvolvidas a 11 e 14 de agosto como `v2.17.0` e
> `v2.18.0`, mas ficaram em PR aberto enquanto a `main` avançou e ocupou esses dois números
> (OdooLS a 17/08 e MCP a 21/08). Foram renumeradas para `v2.19.0` e `v2.20.0` na integração,
> mantendo a data real do trabalho. As versões `v2.17.0` e `v2.18.0` abaixo são as da `main`.

## v2.20.0 - 2026-08-14 (integrado em `main` a 2026-08-24)

Status:
- o bootstrap deixa de destruir o `.gitignore` de repositórios que já têm código; projetos cujo ERP não é Odoo passam a poder usar a framework; e o `PG_CONTEXT.md` da raiz deixa de contradizer o contexto namespaced do espelho

Resumo:
- **o sync de assets destruía o `.gitignore` do projeto.** `pg_sync_shared_assets.ps1` copiava-o com `Copy-Item -Force`, sem merge. `FACTO OBSERVADO`: no bootstrap do `PRIacademia` (projeto .NET/PEX Primavera) desapareceram `[Bb]in/`, `[Oo]bj/`, `.vs/`, `*.user` e `*.suo` — sem reposição, os artefactos de build do Visual Studio passavam a ser versionados. O dano era silencioso e a regra, não a excepção: o bootstrap corre tipicamente **depois** de o repositório do cliente já ter código. As regras da framework passam a viver num bloco delimitado (`PG_FRAMEWORK:START/END`) e tudo o que está fora dele é do projeto e sobrevive ao sync (`Merge-PgGitignoreContent`). Em repositórios sem marcadores, o conteúdo existente é preservado e o bloco acrescentado; a desduplicação é por parágrafo, para não deixar comentários órfãos sem regras
- `pg_smoke_test_repo.ps1`: a paridade do `.gitignore` passa a ser do **bloco** e não do ficheiro inteiro — com merge, comparar por hash total seria drift falso em qualquer repositório com regras próprias
- **`templates/.gitignore` não ignorava `.pg/PREFLIGHT.json`**, embora o `.gitignore` do próprio `_pg_template` já o fizesse. O ficheiro é estado local da máquina e traz o path absoluto de quem correu o preflight, pelo que entrava nos repositórios de cliente e gerava conflitos entre máquinas sem qualquer ganho
- **projetos que não são de Odoo ficavam permanentemente bloqueados.** `pg_preflight_context.ps1` tratava "versão Odoo confirmada" e "`vendor/odoo_src` presente" como erros incondicionais. Num projeto de PRIMAVERA são pré-condições impossíveis, e pela regra bloqueante do `AGENTS_SHARED` impediam todo o trabalho num repositório saudável — enquanto o espelho Brodoo, que é o motivo de o repositório existir, funcionava sem elas (`odoo_version` é publicado como `false` e não entra nas validações do payload). Passa a haver dispensa por **declaração explícita** em `.pg/PROJECT_PROFILE.json` (`erp`, `odoo_applicable`), nunca por inferência: uma etiqueta no Odoo a desligar um gate de qualidade seria pior do que o gate errado. Sem o ficheiro nada muda — o default é Odoo. `PREFLIGHT.json` schema 1.2 → 1.3, com `project_erp` e `odoo_applicable`
- **o `PG_CONTEXT.md` da raiz contradizia o do espelho.** Em modo multi-projeto o espelho publica o contexto real em `projects/<key>/PG_CONTEXT.md` e os snapshots em `.pg/projects/<key>/`, enquanto os ficheiros da raiz ficam nos placeholders do bootstrap. `pg_refresh_pg_context.ps1` só conhecia os da raiz e alimentava o contexto a partir de um snapshot vazio. `FACTO OBSERVADO`: no `PRIacademia`, o `PG_CONTEXT.md` da raiz — o único que o `AGENTS.md` manda ler — dizia `Cliente: [PREENCHER]` enquanto o namespaced tinha 142 linhas de contexto real; e o `.pg/PG_EFFORT_SYNC.json` da raiz declarava `logged_hours_total: 0.0` contra **31,75h** reais, pelo que um ponto de situação construído a partir dele diria ao cliente que não houve trabalho. O script passa a aceitar `-ProjectKey`, a resolvê-lo automaticamente a partir do `PG_PROJECT_INDEX.json` quando há um só projeto ativo, a parar com mensagem accionável quando há vários, e a **nunca** recorrer ao placeholder da raiz em modo multi-projeto. Acrescenta ainda ao `PG_CONTEXT.md` da raiz um bloco que aponta para o contexto real, para quem o abrir não ser induzido em erro
- **`pg_extract_doc_template_assets.py`** deixa de emitir `.md`/`.txt` de aviso para anexos que não sabe ler. Escrevia `[Binary attachment] Extraction not supported...` como par de ficheiros para cada `.py`, `.png` ou download incompleto anexado: 8 cópias do mesmo aviso sem informação, propagadas para **todos** os repositórios da frota pelo sync de assets. Código (`.py`/`.ps1`/`.sql`) fica deliberadamente de fora: a camada de extracção existe para dar o conteúdo de documentos binários, e extrair um script só criava uma cópia byte-a-byte noutro caminho
- removidos dois `.crdownload` (downloads incompletos do Chrome) de `doc_templates/assets/`. Duplicação de conteúdo em `doc_templates`: **17 blobs → 3**, e os 3 restantes são referenciados (`create_parametro_*.py`, citado pelo `TPL_ORCAMENTO_PPTX.md` como fonte da paleta) ou contratuais (extracção de um `.txt` dá um `.txt` igual)
- **`pg_validate_pt_accents.ps1`**: o padrão protegido passa a cobrir paths com barras. Um link markdown para `projects/pri-academia-reformulacao-rh-e-cbl/PG_CONTEXT.md` fazia o validador exigir acento em `reformulacao` **dentro do path** — falso positivo garantido em qualquer documento que ligue a um artefacto namespaced, já que os `project_key` são slugs kebab-case derivados do nome português do projeto. Paths são excepção explícita da regra de acentuação
- **`AGENTS_SHARED`**: nova secção "Projetos que não são de Odoo", com o schema do `PROJECT_PROFILE.json` e a lista do que deixa de se aplicar (ordem obrigatória de decisão, `vendor/odoo_src`, documentação oficial, wizard de Onboarding, `odoo_env.json`)

Validação:
- `pg_smoke_test_repo.ps1` sem erros no `PRIacademia` (não-Odoo, preflight `pass`) e no `GBUK` (Odoo 18.0)
- preflight testado nos três casos: não-Odoo declarado (`pass`), Odoo com source (`pass`, caminho Odoo intacto), Odoo sem source (`fail`, exit 1 — o gate continua a morder)
- merge do `.gitignore` testado em criação, repositório legado, idempotência e adição de regra nova
- `pg_test_pt_accents.ps1` a passar

Nota de adopção:
- os repositórios já bootstrapados vão acusar dois avisos novos até ao próximo `pg_sync_shared_assets.ps1`: `.gitignore` sem o bloco da framework e `doc_templates` desfasado. São transitórios e a mensagem diz o que correr
- os `.crdownload` e os scripts `create_parametro_*.py` duplicados são **anexos do workspace Knowledge no Odoo**. `pg_pull_doc_templates.ps1` reconstrói `assets/` e `assets_extracted/` a partir de lá, pelo que a limpeza definitiva tem de ser feita no Odoo — caso contrário o próximo pull traz os `.crdownload` de volta

## v2.19.0 - 2026-08-11 (integrado em `main` a 2026-08-24)

Status:
- o espelho `odoo_env.json` deixa de publicar o inventário de módulos da base da Parâmetro Global como se fosse o do cliente; a ausência de inventário passa a ser um estado explícito

Resumo:
- **o M1 descrevia a base errada.** `_installed_modules()` fazia `self.env['ir.module.module'].search([('state','=','installed')])` — `self.env` é a base onde o `pg_brodoo` corre, que é o Odoo da Parâmetro Global, não o do cliente. O resultado era publicado com os dados do projeto do cliente. `FACTO OBSERVADO`: nos 13 espelhos disponíveis localmente, 483–488 módulos declarados e **100% dos nomes coincidentes** com os instalados no Odoo da PG, incluindo `pg_brodoo`, `pg_doc_templates` e `pg_project_budget_import`. O universo real é maior: **76 projetos** têm repositório configurado
- **o comportamento estava consagrado em teste.** `test_odoo_env_payload_lists_installed_modules_and_version` afirmava `assertIn('pg_brodoo', names)` — exigia que o inventário contivesse o módulo do próprio Brodoo, isto é, que fosse o da base local. Passa a exigir o contrário
- **porque isto importa:** o `odoo_env.json` é a fonte de verdade nº 6 do `AGENTS_SHARED` e o árbitro do passo 1 (standard já instalado) contra o passo 2 (standard adicional) da ordem obrigatória de decisão. Com o inventário da PG no lugar do do cliente, um agente conclui que quase tudo já está instalado e recomenda como "já disponível" o que exige instalar um módulo — o erro que a ordem obrigatória existe para evitar
- **`ODOO_ENV_SCHEMA_VERSION` 1.0 → 1.1**, com bloco `collection`: `status` (`collected` / `unavailable` / `stale`), `purpose`, `base_url`, `database`, `collected_at`, `collected_by` e `unavailable_reason`. Enquanto não existir recolha no cliente (fase F2), o payload sai `unavailable` / `never_collected` com `installed_modules: []`
- `validate_odoo_env_payload()` recusa `status` fora da lista, exige lista vazia em `unavailable` e exige a identificação da base em `collected`/`stale`. `collected_at` fica **fora** do `payload_hash`: recolher o mesmo inventário de novo não deve gerar commit
- **`AGENTS_SHARED`**: fonte de verdade nº 6 reescrita, com tabela de leitura do `status` e a regra de que `installed_modules` vazio sem `collected` significa "não sei" e nunca "nada instalado". Elimina a contradição com o `PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP`, que já mandava obter os módulos instalados pelo canal `production`
- **`pg_preflight_context.ps1`** valida estado em vez de presença: avisa em `unavailable`, `stale`, JSON ilegível e schema `1.0` (origem desconhecida — pode ser o inventário da PG). Antes só verificava se o ficheiro existia, pelo que os 13 espelhos errados passavam como válidos
- **`pg.odoo.connection` perdeu a restrição de unicidade em Odoo 19.** O modelo declarava-a com `_sql_constraints`, que a versão 19 deixou de suportar (`WARNING: Model attribute '_sql_constraints' is no longer supported`), e a restrição não chegava a ser criada na base: duas ligações com a mesma finalidade para o mesmo repositório passavam sem erro. `FACTO OBSERVADO`: `test_duplicate_purpose_is_rejected` falhava com `AssertionError: IntegrityError not raised`. Convertido para `models.Constraint`, como os restantes modelos do addon já usavam; confirmado em produção em `ir.model.constraint` (`type: u`, `unique(repository_id, purpose)`). Dados verificados antes: 43 ligações, zero duplicados
- corrigido `test_two_purposes_coexist_on_same_repo`, cuja asserção esperava o label da finalidade sem acentos enquanto o modelo já tinha `Produção do cliente (adoção)`
- contrato arquitectural em `docs/PG_007_ODOO_ENV_COLLECTION_CONTRACT.md` (decisão D3 fechada; D1 e D2 em aberto, bloqueiam a F2), `LEARNING 007` em `docs/PG_PROJECT_LEARNINGS.md` e item `PG-007` no backlog

Nota de proveniência:
- apareceu a diagnosticar um sintoma sem relação aparente: o filtro "Employees" na escolha de participantes do Calendar devolvia 4 nomes de 13 empregados. Essa causa era outra (ver `LEARNING 007`), mas a verificação dos módulos instalados expôs este defeito

Nota de operação:
- o addon deployado vive em `parametro-odoo/Parametro_Global` (branch `brodoo` → `main`); `_pg_template/pg_brodoo/` é espelho de teste. As alterações foram feitas na fonte, promovidas a produção (`pg_brodoo 19.0.1.14.0`) e o espelho ressincronizado a partir dela
- os espelhos já publicados **não** se corrigem com o deploy: mantêm o schema `1.0` até ao próximo sync de cada projeto. Só o `jmmgroup` foi republicado. O aviso do preflight é o que impede que sejam usados para a ordem de decisão entretanto
## v2.18.0 - 2026-08-21

Status:
- `READY`: suporte nativo ao protocolo Odoo MCP (Model Context Protocol) integrado no framework e validado em produção com instâncias Odoo 19+ / SaaS 19.4+

Resumo:
- **novo cliente MCP Odoo (`scripts/pg_odoo_mcp_query.py` e `scripts/pg_odoo_mcp_query.ps1`)**: suporta o endpoint nativo `POST /mcp` com autenticação Bearer Token (`Authorization: Bearer <KEY>`), dispensando `db`, `uid` ou `common.authenticate` clássico
- **suporte a ações MCP completas**: `search` (via `ai_tool_search`), `read_group` (via `ai_tool_read_group`), `get_fields` (`ai_tool_get_fields`), `get_models` (`ai_tool_get_models`), `context` (`ai_tool_mcp_retrieve_initial_context`), `list_tools`, `call_tool` e handshake `ping` (`initialize`)
- **auto-comutação e fallback no `pg_odoo_client_query.ps1`**: novo parâmetro `-Protocol auto|rpc|mcp`. No modo `auto`, se a autenticação RPC falhar com `AccessDenied` ou a base for moderna SaaS, o helper comuta automaticamente para o canal MCP sem interromper o fluxo
- **novo Dashboard Executivo no Ponto de Situação PPTX (`scripts/pg_build_ponto_situacao_pptx.py` & `scripts/pg_pptx_identity.py`)**: o slide 1 foi totalmente transformado num painel executivo visual orientado ao cliente, com KPIs com badges de estado (Saúde do Projeto, Progresso %, Esforço e Saldo), barras de progresso visual por área (`progress_bar`), destaques de valor entregue e caixa de decisões prioritárias do cliente
- **atualização de templates e schemas**: `doc_templates/TPL_PONTO_SITUACAO_PPTX.md` atualizado com o schema enriquecido e diretrizes de redação orientadas a valor de negócio
- **nova suite de testes `scripts/tests/test_pg_odoo_mcp_query.py` e `scripts/pg_test_mcp_query.ps1`**: cobertura completa de normalização de URLs, parsing de argumentos, handshake, pesquisa e tratamento de exceções MCP
- **atualização documental**: `templates/AGENTS_SHARED.md` e `docs/PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP.md` atualizados com instruções de uso e arquitetura do canal MCP

## v2.17.0 - 2026-08-17

Status:
- `READY WITH GUARDRAILS`: rollout OdooLS consolidado no template e validado em piloto real; o servidor persistente do IDE e o modo recomendado
- 53 de 58 repositorios de cliente configurados localmente; cinco bloqueados por source Odoo em falta

Resumo:
- novo `pg_setup_odools.ps1`: gera `odools.toml` local a partir do `PG_CONTEXT.md`, junction de source e manifests versionados, sem substituir configuracao manual por omissao
- novo `pg_rollout_odools_orgwide.ps1`: audit-first e aplicacao explicita, com relatorio JSON e bloqueios por repositorio
- nova skill `pg-odoo-navigator`, distribuida para `.agents/skills` e `.claude/skills`, com resultados limitados e fallback dirigido
- novo cliente LSP `pg_odools_query.py`; validado em `GLC` com classes/modelos Python e XML IDs reais
- primeira indexacao de `GLC` demorou cerca de 278 segundos e um novo processo nao ficou pronto em 120 segundos; por isso o uso recomendado e o servidor persistente do IDE, nao cold starts repetidos por pergunta
- extensao oficial VS Code `Odoo.odoo` 1.2.1 instalada e validada nesta maquina
- `odools.toml` e `.pg/odools/` ficam ignorados globalmente pelo template e localmente por `.git/info/exclude`
- novo teste determinista `pg_test_odools_setup.ps1` e validacao formal da skill
- corrigido `pg_report_token_consumption.ps1`: `JavaScriptSerializer` e inteiros de 32 bits faziam 1.694 linhas aparecer como erros/zero tokens; passa a usar `ConvertFrom-Json`, `Int64` e um unico close cumulativo por sessao
- hooks Claude/Codex passam a registar `navigation_mode` (`odools` ou `native`) para permitir A/B real; historico atual continua quase todo estimado

## v2.16.4 - 2026-08-10

Status:
- o validador de acentuacao passa a filtrar o que analisa e a cobrir 41 palavras comuns que deixava passar; os artefactos extraidos deixam de estar em CRLF contra a sua propria regra

Resumo:
- **o filtro `-Include` nunca funcionou em scans de pasta.** `Get-ChildItem -LiteralPath <dir> -Recurse -Include '*.md'` devolve **todos** os ficheiros: com `-LiteralPath` e `-Recurse`, o PowerShell ignora silenciosamente o `-Include`. Um scan de pasta com o default `*.md` analisava tambem `.py`, `.docx` e tudo o resto (`FACTO OBSERVADO`: reproduzido em pasta com `a.md`, `b.py`, `c.docx` — os tres devolvidos). Passa a filtrar a mao, por `-like` sobre cada padrao
- **ficheiros binarios sao ignorados**, mesmo quando o caminho e explicito. Um `.docx` e um ZIP e, lido como texto, produz achados a partir de bytes comprimidos — foram 24 achados falsos (`So`, `Ja`, `sO`) em dois `.docx` de um projecto real. Lista em `PgAccentBinaryExtensions`
- **`-Include` aceita padroes separados por virgula.** Via `powershell -File` — a forma que o ritual impoe — um `'*.md,*.ps1'` chegava como um unico elemento do array e nao correspondia a nada. Mesma normalizacao que o `-Fields` do `pg_odoo_query.ps1` ja fazia
- **mapa de acentuacao estendido de 432 para 473 entradas.** Faltavam palavras muito comuns em prosa tecnica, que davam `OK` e ficavam por corrigir: `guiao`, `paragrafo`, `cabecalho`, `cabeca`, `titulo`, `subtitulo`, `saida`, `mao`, `celula`, `clicavel`, `preenchivel`, `citacao`, `visiveis`, `secoes`, `rodape`, `sitio`, `reconstruido`, `rotulo`, `heuristico`, `continuacao`, `vao` e respectivos plurais/femininos. Nenhuma tem homografo
- **aviso ao correr `-Fix` fora de prosa.** A regra de redacao cobre comentarios e docstrings, pelo que validar `.ps1`/`.py` e legitimo; mas uma palavra do mapa pode coincidir com um identificador (uma variavel `titulo` viraria `título` e partiria o codigo). O script avisa e deixa a decisao a quem corre
- **40 artefactos extraidos estavam em CRLF contra o proprio `.gitattributes`.** `git ls-files --eol` dava `i/lf w/crlf attr/text eol=lf` em 36 `.txt` de `doc_templates/assets_extracted/`, no `pg_brodoo/models/project_task.py` e em 3 ficheiros com acentos no nome. Causa: foram materializados por um `git checkout` anterior a entrada da regra `eol=lf` — o extractor Python ja escrevia LF, e o `Copy-Item` do sync copia byte a byte, pelo que propagava o CRLF para todos os projetos bootstrapados. Consequencias observadas: ficheiros permanentemente `modified` no `git status` com `git diff` vazio, e o `pg_smoke_test_repo.ps1` a avisar `doc_templates desfasado do framework partilhado` (compara SHA256 dos bytes). Corrigido deixando o git reescrever os ficheiros; `git ls-files --eol` nao tem agora nenhum `w/crlf` com `eol=lf`
- novo `scripts/pg_test_pt_accents.ps1`: cobre o filtro `-Include`, o salto de binarios, a integridade do mapa (sem duplicados, pares bem formados, chaves ASCII) e a deteccao/correccao de 9 das palavras novas. 20 assercoes, sem dependencias externas
- `docs/PG_CONTENT_HYGIENE.md` documenta as novas regras, o diagnostico de fins de linha por `git ls-files --eol`, e passa a dizer explicitamente que o validador e um auxiliar e nao um gate suficiente: uma palavra ausente do mapa passa em silencio

Nota de proveniencia:
- os tres defeitos apareceram a validar documentos gerados no projecto MAP (Mercado Abastecedor do Porto). O validador dava `OK: nenhuma perda de acentuacao detetada` num ficheiro com 52 palavras sem acento, dava 24 achados falsos vindos de `.docx`, e o CRLF fazia 40 ficheiros aparecerem como modificados sem alteracao de conteudo

Nota de operacao:
- ao reescrever os ficheiros para LF **a mao** (Python/PowerShell) o `git status` continua a marca-los como modificados apesar de o hash coincidir com o indice. A correccao tem de passar pelo git: apagar e `git checkout -- <caminhos>`

## v2.16.3 - 2026-07-30

Status:
- o fallback do pull passa a existir de facto; falha transitória do Odoo deixa de derrubar o refresh

Resumo:
- detetado numa segunda execução do bootstrap do `vendaspp`: a via JSON-2 devolveu `404` em `/json/2/ir.attachment/search_read` (transitório — a mesma chamada funcionou minutos antes e depois), e o pull morreu. O bootstrap sobreviveu, como manda a `v2.16.1`, mas o refresh não tinha por que falhar
- **o fallback JSON-RPC nunca funcionou.** Autenticava em `/web/session/authenticate`, que é o login de sessão web e **rejeita chaves de API** com `AccessDenied` (`FACTO OBSERVADO`: confirmado à parte, forçando `--transport jsonrpc`). Como só entra em ação quando a via principal falha, um `404` num único modelo derrubava o pull inteiro. Passa a autenticar no serviço `common` de `/jsonrpc` e a chamar `object.execute_kw` — o caminho que o `pg_odoo_query.ps1` já provava funcionar com a chave do Brodoo. Verificado ponta a ponta: 17 templates e 80 anexos por JSON-RPC, e com a via JSON-2 forçada a falhar em todas as chamadas o pull continua a completar
- o `uid` da autenticação passa a ser reutilizado, em vez de uma autenticação por chamada
- **tracebacks do Python saem da consola**: o `stderr` do helper vai para ficheiro e o que sobe é a última linha da excepção — a que diz a causa — com o caminho do log completo. Cada tentativa falhada despejava ~50 linhas a vermelho e enterrava as mensagens que interessam (era o que se via no ecrã do operador). O `ErrorActionPreference` volta a `Continue` durante a chamada, senão o PS 5.1 lança `NativeCommandError` e mascara o erro real
- **removidos os dois endpoints mortos** da lista hardcoded: `parametroglobal` responde "Database not found" e o dev `parametroglobal-dev-32714143` já não resolve em DNS. Cada falha real custava três tentativas e três tracebacks, dois deles garantidamente inúteis. O alvo passa a ser o que a cascata de credenciais resolve; a redundância que interessa é a dos transportes
- 3 testes novos travam a regressão (51 no total). Corrigidos também os fakes existentes: não aceitavam o parâmetro `headers`, pelo que a chamada JSON-2 rebentava com `TypeError`, o `call_kw` engolia a excepção e **todos os testes deste módulo exercitavam o fallback** sem que nada o dissesse — a via principal não estava testada. Os fakes passam a distinguir os dois envelopes de resposta e a falhar se houver queda silenciosa para o fallback

## v2.16.2 - 2026-07-30

Status:
- pull de doc templates passa a ser idempotente: onboarding deixa de sujar a árvore do framework

Resumo:
- fecha o defeito que a `v2.16.1` documentou e deixou aberto. Estava errado deixá-lo: como o pull passou a correr com sucesso em cada bootstrap, o `doc_templates/` ficava modificado a cada onboarding sem nada ter mudado, e a "solução" era uma regra para as pessoas se lembrarem de correr `git checkout`. Regra que alguém haveria de esquecer, commitando um manifest que produz `hash mismatch` em todos os projetos
- **os `TPL_*.md` passam a ser escritos em LF**, não CRLF. O `.gitattributes` impõe `*.md text eol=lf`, pelo que é em LF que materializam em qualquer checkout: gravar o `sha256` de bytes CRLF era gravar o hash de bytes que deixavam de existir no primeiro checkout seguinte
- **novo `scripts/pg_json_canonical.py`**: o `MANIFEST.json` deixa de ser serializado pelo `ConvertTo-Json` e passa por um canonicalizador determinista (indentação de 2 espaços, LF, não-ASCII literal, ordem do produtor preservada). O `ConvertTo-Json` do Windows PowerShell 5.1 e o do PowerShell 7 formatam de maneira diferente e reescreviam o ficheiro inteiro consoante o shell de quem corria o pull. 13 testes em `scripts/tests/test_pg_json_canonical.py`
- **`generated_at` só muda quando o snapshot muda**: sendo o manifest gerado igual ao que está em disco à parte do timestamp, preserva-se o anterior e o promote fica um no-op (`INFO: snapshot sem alteracoes`). A semântica do campo passa a ser "quando o snapshot mudou", não "quando o pull correu"; o `sha256` cobre todo o conteúdo, pelo que manifest igual implica snapshot igual
- **anexos binários deixam de ser corrompidos no checkout** (`doc_templates/assets/** -text` no `.gitattributes`, e no `templates/.gitattributes` que os projetos recebem). O `* text=auto` classificava como texto os anexos sem bytes nulos — dois `.crdownload` e um `.txt` vindos da Knowledge — e convertia-lhes os fins de linha ao materializar: `Não confirmado 93645.crdownload` passava de 10147 para 10454 bytes e o `sha256` deixava de corresponder ao registado. Consequência real, observada no `vendaspp`: `WARN: doc_templates desfasado do framework partilhado` em qualquer projeto sincronizado. 3 dos 40 anexos estavam afectados; agora os 40 batem com o manifest
- higiene, no mesmo caminho: `pg_extract_doc_template_assets.py` passa a escrever LF explicitamente (o modo texto do Python traduzia para CRLF em Windows) e o `.gitattributes` ganha regra `*.txt text eol=lf`, que faltava. Nota de honestidade: os 40 ficheiros de `assets_extracted/` que apareciam como `M` **não** eram divergência real — era o stat cache do git, e `git add` confirmou que não havia nada para commitar. A alteração vale por consistência (bytes em disco iguais aos versionados, sem avisos de CRLF), não por corrigir um defeito
- verificado com pull real contra a Knowledge: duas execuções seguidas numa árvore alinhada deixam `git status doc_templates/` **vazio**; adulterando um `sha256` no manifest em disco, o pull corrige-o e refresca o `generated_at`; os 40 anexos batem com o manifest; e o smoke test do `vendaspp` volta aos 3 avisos esperados de projeto novo, sem o de desfasamento. É este o critério de aceitação, e está registado em `PG_DOC_TEMPLATES_VERSIONING.md`
- `PONTO POR VALIDAR`: o `templates/.github/workflows/pg_doc_templates_drift_check.yml`, que a documentação dá como workflow partilhado de drift-check semanal, **não existe no repositório** — o único workflow em `templates/.github/workflows/` é o `pg_refresh_pg_context.yml`. Anotado no próprio documento; enquanto não for confirmado, não contar com esse job como rede de segurança

## v2.16.1 - 2026-07-30

Status:
- onboarding de projeto novo deixa de abortar quando o refresh de doc templates falha

Resumo:
- detetado no onboarding real do `vendaspp`: `pg_bootstrap_assisted.ps1` **abortou a meio** porque `pg_pull_doc_templates.ps1` não encontrou `PG_ODOO_KNOWLEDGE_TOKEN`. O repositório ficou sem `doc_templates/`, sem `vendor/odoo_src` e sem smoke test — os passos seguintes nunca correram
- **o refresh passa a ser não bloqueante no bootstrap** (`pg_bootstrap_repo.ps1`): falhando, avisa em `WARN`, diz como actualizar mais tarde e segue com a cópia versionada em `doc_templates/`, que é a que o sync partilhado leva para o projeto. Trabalhar com templates de há uns dias é melhor do que um projeto sem framework nenhuma; o `pg_preflight_context.ps1` já tratava a ausência de `doc_templates` como aviso, não como bloqueio
- **credencial da Knowledge passa a resolver em cascata** (`pg_pull_doc_templates.ps1`): `$env:PG_ODOO_KNOWLEDGE_TOKEN` primeiro (override por sessão, e caminho do CI), depois `credentials/brodoo_credentials.json`. Do ficheiro vêm `api_key`, `login`, `url` e `db` em conjunto — chave de uma conta com o login de outra não autentica —, e qualquer parâmetro explícito do chamador vence o ficheiro. Quem tem o framework passa a ter a credencial, sem variável de ambiente por máquina
- validado que o utilizador de serviço Brodoo lê o que o pull precisa (`knowledge.article` com `pg_template_code`, `pg_template_version`, `pg_template_state`, `pg_template_body_md` e anexos): pull completo em dry-run sem env var definida
- a credencial passa a ser resolvida **antes** do loop de endpoints. Faltando, o erro sai uma vez e com as duas vias de resolução, em vez das três tentativas com a mesma mensagem que tornavam o output ilegível
- o default `-Login` deixa de ser a única via de identidade: continua a valer no caminho da variável de ambiente (compatibilidade), mas o caminho partilhado usa o login do utilizador de serviço
- docs actualizados: `PG_DOC_TEMPLATES_VERSIONING.md` (nova secção "Credencial (cascata)" e nota de não bloqueio) e `PG_004_OPERATIONAL_CLOSURE_CHECKLIST.md` (comando de validação local sem env var)
- novo `docs/PG_SECURITY_CREDENTIALS_AUDIT.md`: levantamento factual do modelo de credenciais (o que está contido e verificado, riscos R1 a R5, pontos por validar) e prompt de trabalho pronto a usar por quem pegar na frente. O achado que mais pesa: a chave Brodoo lê o campo `api_key` de `pg.odoo.connection` (`pg_odoo_client_query.ps1:141-142`), o que a torna, na prática, chave de acesso aos Odoo dos clientes e não apenas uma credencial de consultas de apoio
- **defeito conhecido, exposto por esta alteração** (não corrigido aqui): correr o pull deixa `doc_templates/` com um diff de ~1000 linhas em `MANIFEST.json` sem que nenhum template mude de conteúdo. Duas causas independentes, ambas confirmadas com o pull real deste dia:
  - **line endings**: o pull escreve os `TPL_*.md` em CRLF e grava o `sha256` sobre esses bytes, mas o `.gitattributes` impõe `*.md text eol=lf`. Depois de commit + checkout, os ficheiros materializam em LF e **nenhum** `sha256` do manifest corresponde. `pg_smoke_test_repo.ps1` compara com `Get-FileHash` cru, sem normalizar, e trata a divergência como **erro** ("ficheiro editado sem refresh de MANIFEST.json"). `FACTO OBSERVADO`: para `TPL_ORCAMENTO.md`, sha CRLF `9fe21685…` vs sha LF `c104b643…`, sendo o segundo o que está no manifest em `HEAD` e o único que bate com uma árvore checkoutada
  - **serializador**: o `ConvertTo-Json` do Windows PowerShell 5.1 e o do PowerShell 7 formatam de maneira diferente (indentação cumulativa, dois espaços depois de `:`, arrays vazios em três linhas). O manifest é reescrito de ponta a ponta consoante o shell que corre o pull, e o drift-check semanal passa a acusar drift que não existe
  - efeito prático: o pull não é idempotente ao nível do ficheiro; só o é ao nível do conteúdo dos templates. Enquanto não for corrigido, **não commitar o `doc_templates/` saído de um pull local sem confirmar que há mudança real de conteúdo** (`git diff -- doc_templates/*.md` vazio = só churn). Correção mínima proposta: escrever os `TPL_*.md` em LF (alinhado com o `.gitattributes`) e serializar o manifest de forma determinista, independente do shell
- `PONTO POR VALIDAR`: `FrameworkVersion` em `pg_pull_doc_templates.ps1` está fixo em `v2.9.1` e é isso que fica gravado em `doc_templates/MANIFEST.json` (`framework_version`). Coincide com a "última release fechada" declarada no `README.md` e em `PG_CURRENT_WORKING_STATE.md`, pelo que pode ser intencional; fica por confirmar se o valor deve acompanhar a release fechada (e ser actualizado no fecho) ou a linha do `CHANGELOG`. Não afecta o conteúdo dos templates nem o drift-check

## v2.16.0 - 2026-07-29

Status:
- fim do apagar o rodapé à mão em cada email: o corpo deixa de trazer fecho e assinatura

Resumo:
- **o compositor do Odoo já insere a assinatura do utilizador** (`res.users.signature`), com saudação de fecho, nome, cargo e rodapé da marca. O `TPL_EMAIL_CLIENTE` manda escrever tudo isso no corpo, pelo que cada email chegava com o fecho duplicado e obrigava quem envia a apagar um deles. Detetado no primeiro envio real (validação do CRM do reckon.ai)
- `pg_build_email_cliente.py` **retira o fecho e a assinatura do fim do corpo** e reporta linha a linha o que retirou. Corta a partir de uma saudação de fecho (`Com os melhores cumprimentos`, `Cumprimentos`, `Atentamente`, `Best regards` e variantes) ou de um separador `--`
- salvaguardas para não comer conteúdo: só procura na cauda e só em parágrafos (lista, tabela ou título travam a procura), cauda limitada a 10 linhas, e a saudação tem de ocupar a linha inteira — "Cumprimentos ao Sr. António pela decisão" não é fecho. Nada sai em silêncio
- `-ManterAssinatura` / `--manter-assinatura` desliga o comportamento, para destinos sem assinatura configurada
- `AGENTS_SHARED.md`: o contrato do rascunho passa a proibir escrever fecho e assinatura. A remoção no conversor é a rede de segurança para os rascunhos que já existem
- 7 testes novos (35 no total), incluindo os casos que garantem que conteúdo real no fim do email não é cortado
- `PONTO POR VALIDAR`: o `TPL_EMAIL_CLIENTE` (article 736) continua a prescrever o bloco de assinatura na estrutura do email. Enquanto não for corrigido na Knowledge, os agentes continuam a escrevê-lo e é o conversor que o apara

## v2.15.1 - 2026-07-29

Resumo:
- o `.html` gerado passa a levar, na linha 2, um comentário a dizer para **não** copiar o ficheiro a partir do editor de código. Na primeira utilização real o ficheiro foi aberto no VS Code, onde o que se vê é o HTML da pré-visualização — copiado em bruto, o Odoo mostraria as etiquetas como texto. O aviso aponta os dois caminhos válidos (o `Ctrl+V` que o script já preparou, ou o botão "Copiar corpo" no browser). É comentário HTML: não aparece na página nem no corpo colável

## v2.15.0 - 2026-07-29

Status:
- email ao cliente deixa de ser reformatado à mão no Odoo: passa a colar formatado com `Ctrl+V`

Resumo:
- **novo `scripts/pg_build_email_cliente.py`**: converte o rascunho markdown de um email no HTML que o editor do Odoo aceita. Sem dependências externas, determinista (mesmo markdown → mesmo HTML) e com validação do resultado contra a lista branca do editor — falha se gerar algo que não sobreviva à colagem. Suporta negrito, itálico, listas com aninhamento, tabelas, links, citações e blocos de código; o assunto e os destinatários saem num bloco de cabeçalho e nunca entram no corpo
- **novo `scripts/pg_copy_email_cliente.ps1`**: corre o conversor, escreve o `.html` de pré-visualização (com botão de copiar) e deixa o corpo na área de transferência em `HTML Format` (CF_HTML) + texto simples. No Odoo é só colar
- **o HTML sai sem CSS, e é propositado.** `CLIPBOARD_WHITELISTS` no editor do Odoo (`addons/html_editor/.../clipboard_plugin.js` em 19; `addons/web_editor/.../OdooEditor.js` em 17/18 — constantes idênticas) só deixa passar os atributos `class`, `href`, `src` e `target`: o `style` é sempre removido, tal como `<div>`, `<span>`, `<hr>` e `<code>`. Qualquer tentativa de fixar tipos de letra ou cores seria trabalho perdido; assim a formatação vem do próprio Odoo e o email sai igual em qualquer projeto
- o conversor **avisa** do que o Odoo descarta (`---`, `` `código` ``, títulos de nível 1 e 2, HTML escapado) e do que ficou por preencher (marcadores de template como `[Nome]`, assunto em falta)
- `AGENTS_SHARED.md`: nova regra "Emails para colar no Odoo" — o `.md` é rascunho, o entregável é o HTML colável; proibido entregar markdown para colar ou escrever o HTML à mão
- novo `docs/PG_EMAIL_ODOO_FORMATTING.md` com o racional, os paths da evidência no source, a tabela do markdown suportado e as limitações
- dois pontos de mojibake fechados no caminho: o resultado passa do Python para o PowerShell por ficheiro JSON UTF-8 (não por `stdout`, que o PS 5.1 descodifica em ANSI) e o CF_HTML vai para a área de transferência como bytes UTF-8 num `MemoryStream`
- testes: `scripts/tests/test_pg_build_email_cliente.py`, 27 casos
- `PONTO POR VALIDAR`: o `TPL_EMAIL_CLIENTE` (article 736 na Knowledge) continua a descrever só a estrutura do texto. Acrescentar-lhe o bloco de cabeçalho e o passo de geração exige edição na Knowledge com bump MINOR e revisão 2-eyes — não foi feito nesta entrega

## v2.14.3 - 2026-07-29

Status:
- log de tokens deixa de se auto-invalidar; frota passa de 12 para 9 repos vermelhos no smoke test

Resumo:
- **auditoria da frota** (23 repos com `.pg_framework`): 12 repos de projeto vermelhos, nenhum por causa da v2.14.1. A maior causa, em 9 deles, era o `.pg/tokens/consumption.jsonl` inválido — e a raiz estava no próprio framework
- **`pg_log_token_consumption.ps1` inventava um `session_id` novo quando o `-SessionId` era omitido.** Num `session_progress`/`session_close` isso cria, por construção, uma sessão sem `session_open`; como o log é histórico append-only, o defeito ficava no ficheiro **para sempre**. Passa a só gerar id novo no `session_open`; nos outros eventos reutiliza a última sessão aberta **do mesmo agente** e, se não houver nenhuma, falha com mensagem accionável em vez de escrever lixo permanente
- **`pg_validate_token_consumption.ps1`: orfandade de sessão passa de erro a aviso.** Sendo irreparável (não se reescreve histórico), reprovava o repo indefinidamente — e um check permanentemente vermelho treina as pessoas a ignorar o resultado. Os eventos continuam a servir para agregar consumo; o que falta é o par. Erros de formato/schema continuam erros, porque esses são corrigíveis. As duas regras anteriores eram redundantes (a segunda continha a primeira)
- `pg_smoke_test_repo.ps1` passa a trazer o stream de avisos do validador (`3>&1`) para a sua própria contagem — com o `| Out-Null` os avisos ficariam invisíveis
- **`AGENTS_SHARED.md`: escrever o log só pelo script, nunca compondo o JSON à mão.** O `repo_path` do Windows leva `\` e `\U`/`\D`/`\R` não são escapes válidos em JSON — foi exactamente assim que a linha 17 do log do `Sofmovel` ficou irreparável (`Sequência de escape não reconhecida (232)`). O schema documentado é para leitura; o `ConvertTo-Json` do script escapa corretamente
- novo `scripts/pg_test_token_consumption.ps1`: cobre a resolução de `session_id` (reutilização, isolamento entre agentes, falha sem sessão aberta, nada escrito em caso de falha), a severidade do validador (aviso vs erro) e o round-trip de um path com `\`
- efeito medido: 7 repos ficaram verdes (ENIGMAF, GBUK, givachoice, demo-gbn, Essani, Hipermercado, MIMO). Os 9 que restam são drift de `doc_templates`, que o `pg_ensure_framework_current` re-sincroniza na próxima sessão de cada repo; o `Sofmovel` mantém o erro da linha 17, que exige correcção manual do histórico

## v2.14.2 - 2026-07-28

Resumo:
- `TPL_MIGRACAO_DADOS_ODOO` v1.1.0 -> **v1.1.1**: removido bloco duplicado no Passo 2. A substituição de texto na v1.1.0 deixou intacto o bloco antigo que vinha depois da tabela de finalidades, pelo que o template passou a instruir as duas coisas ao mesmo tempo — usar as credenciais do Odoo PG e, mais abaixo, criar um ficheiro de ligação local. Instruções contraditórias são pior do que as antigas, porque o agente escolhe

## v2.14.1 - 2026-07-28

Status:
- rótulos do `PG_CONTEXT.md` voltam a ser preenchidos; `pg_test_context_hygiene.ps1` verde (estava vermelho na `main`)

Resumo:
- **`Versão do Odoo:`, `Edição:` e `Documentação *:` nunca eram preenchidos** no `PG_CONTEXT.md` da raiz. Os templates escrevem os rótulos acentuados (como manda a regra de redação em português europeu) mas os scripts pedem-nos em ASCII puro (obrigatório: o PS 5.1 lê `.ps1` sem BOM como ANSI) — o `[regex]::Escape('Versao do Odoo:')` nunca casava com a linha do ficheiro. Só passavam `Path do core:` e `Path source Enterprise:`, cujos rótulos não têm acentos. Afetava `pg_sync_pg_context.ps1`, `pg_apply_scope_sync.ps1` (`Última sincronização de âmbito:`, `Fonte do âmbito sincronizado:`), `pg_build_pg_context.ps1` e a leitura do `pg_clone_odoo_source.ps1` (que por isso exigia sempre `-Series` explícito). Detetado no onboarding do `odoosh`, onde o espelho não tapa o ficheiro da raiz por ser multi-projeto
- helpers de rótulos passam a viver **num sítio só** (`pg_file_io_common.ps1`): `Get-PgLabelPattern`, `Test-PgLabelPresent`, `Get-PgLabeledValue`, `Set-PgLabeledValue`, `Ensure-PgLabeledValue`. O padrão aceita as duas grafias e a reescrita **preserva o rótulo tal como está no ficheiro** (nunca troca o acentuado pelo ASCII). Eliminadas as 4 cópias divergentes da mesma função
- dois bugs latentes corrigidos pelo caminho: o `.*$` antigo engolia o `\r` e devolvia a linha em LF num ficheiro CRLF (agora `[^\r\n]*(?=\r?$)`), e a substituição por string interpretava um `$` no valor como referência de grupo (agora `MatchEvaluator`)
- **falso positivo de mojibake em português correcto**: `Get-PgTextMojibakeScore` contava caracteres líder isolados, e `Parâmetros`/`âmbito` chegavam para 5 pontos no próprio `templates/PG_CONTEXT.md` — todos os repos da frota tinham um `WARN: PG_CONTEXT.md contem padroes compativeis com mojibake` permanente. Passa a exigir o **par** (líder + outro caractere fora do ASCII), que é como o mojibake real aparece; o `U+FFFD` continua a valer por si
- `pg_test_context_hygiene.ps1`: estava a **falhar na `main`** por duas razões, ambas do harness. O fixture não materializava `doc_templates`, e o smoke test trata a ausência do `MANIFEST.json` como erro; e o `2>&1` sobre um executável nativo, com `ErrorActionPreference = Stop`, abortava o harness antes de a asserção poder mostrar o output recolhido (a falha aparecia como `NativeCommandError` sem diagnóstico). Acrescentados testes de regressão para os rótulos acentuados, para o CRLF, para valores com `$`, para o mojibake e um teste ponta a ponta do `pg_sync_pg_context.ps1` sobre o `PG_CONTEXT.md` do template

## v2.14.0 - 2026-07-28

Status:
- credenciais de migração passam a vir do Odoo PG; deixa de ser preciso escrever segredos para disco

Resumo:
- `pg_odoo_migration_guard.py`: novo `resolver_alvo_por_projeto(project_key, purpose)`, que obtém as credenciais do Odoo-alvo de `pg.odoo.connection` pelo canal Brodoo, **em memória**. Novo modo de CLI `--project-key/--purpose`. O caminho do ficheiro local (`resolver_alvo`) fica como alternativa para ligações ainda não registadas
- **corrige uma contradição minha com a política da framework.** O `AGENTS_SHARED.md` diz que as credenciais do cliente ficam centralizadas no Odoo PG e nunca em ficheiros nos repositórios de projeto; o guard v1 exigia exactamente esse ficheiro. Na primeira utilização real (carga de dados no `client_test` do reckon.ai) o classificador de segurança bloqueou a escrita do ficheiro com a API key — com razão
- `TPL_MIGRACAO_DADOS_ODOO` v1.0.0 -> **v1.1.0**: Passo 2 reescrito para o caminho preferido, com instrução explícita de não criar ficheiros de ligação e de registar a ligação em Brodoo quando não existir
- `AGENTS_SHARED.md`: a regra de migração passa a dizer de onde vêm as credenciais
- validado contra as três ligações do reckon.ai (`brodoo_dev`, `client_test`, `production`) sem qualquer ficheiro local

## v2.13.5 - 2026-07-28

Resumo:
- `TPL_CRIA_DEMO` v1.0.0 -> **v1.1.0**: abre com um aviso explícito de que é para dados **fictícios** em base criada de raiz, e remete para o `TPL_CRIA_DEMO_DADOS_CLIENTE` quando os dados são reais do cliente. O mapeamento do `AGENTS_SHARED.md` já bifurcava, mas quem abrisse o template directamente não tinha como saber que existe outro — e a regra dos dados é oposta nos dois

## v2.13.4 - 2026-07-28

Status:
- canal Odoo do cliente deixa de quebrar por `base_url` malformado; 10 ligações normalizadas

Resumo:
- **varrimento das 26 ligações `pg.odoo.connection`**: 10 tinham `base_url` malformado. Duas estavam **realmente quebradas** — `Limite-Crucial/production` com sufixo `/odoo` (confirmado `HTTPError` no `/web/database/list`; sem sufixo devolve a BD) e `FPVela/brodoo_dev` sem esquema `http(s)`. As outras oito eram barra final, inofensiva porque os helpers já faziam `TrimEnd('/')`. Todas normalizadas
- `pg_odoo_client_query.ps1` e `pg_odoo_resolve_db.ps1` passam a **normalizar o `base_url`** (sufixo `/odoo`, barra final, esquema em falta). Provado com as três formas malformadas a resolverem corretamente
- `pg_odoo_client_query.ps1`: **`database` deixa de ser obrigatório à entrada**. Era exigido antes de se chegar ao auto-heal, o que impedia o próprio mecanismo que existe para o dispensar — uma ligação de staging com o campo vazio (que é o recomendado, porque o nome muda a cada rebuild) falhava com "campo em falta" em vez de resolver
- `pg_odoo_migration_guard.py`: corrigido bug no `listar_bases()` — a construção do `Request` estava **fora** do `try`, pelo que um `base_url` sem esquema levantava `ValueError` com traceback em vez de devolver lista vazia. Acontece com ligações reais (o `FPVela` era uma)

## v2.13.3 - 2026-07-27

Status:
- guard de migração provado contra Odoo real; endurecido nos dois modos de falha que apareceram

Resumo:
- **provado ponta a ponta** contra os três Odoo do SmartEnergy (`brodoo_dev`, `client_test`, `production`), com as credenciais centralizadas em `pg.odoo.connection`. As três ligam; produção liga e **recusa escrita**, como deve
- `normalizar_base_url()`: remove o sufixo `/odoo` e barras finais do `base_url`. A partir do Odoo 17 o browser mostra o backoffice em `.../odoo` e é esse URL que se copia, mas os endpoints da API são servidos na raiz — o sufixo produzia 400 na autenticação **e** na resolução do nome da base, sem dizer porquê. Foi exactamente o que aconteceu nas três ligações criadas para o SmartEnergy (corrigidas), e o `Limite-Crucial` tem o mesmo problema à espera
- ficheiro de ligação passa a ser lido com `utf-8-sig`: no Windows o Notepad e o `Set-Content -Encoding utf8` escrevem BOM, e um BOM fazia o `json.load` rebentar com um traceback em vez de uma mensagem útil
- erros de configuração passam a sair como mensagem accionável (`FALHOU: ...`) em vez de traceback
- `.gitignore` (do framework e do template dos projetos): `.pg/migration/` e `conn*.json` passam a ser ignorados mecanicamente. O log tem `args_preview` que pode conter dados de clientes e o `*.log` não apanhava `.jsonl`; os ficheiros de ligação com API keys estavam protegidos só por um aviso no README. `conn.json.example` continua versionável

`PONTO POR VALIDAR` — o SmartEnergy tem **duas** cópias dos scripts de migração: `docs/wp1_migration_scripts/` (8 scripts, migrada para o guard) e `docs/runbook_cutover/scripts/` (17 scripts, **não migrada**, com o mesmo `PROD_DB` neutralizável em dois sítios). Confirmar qual é a autoritária antes de mexer na segunda.

## v2.13.2 - 2026-07-27

Resumo:
- espelho `pg_brodoo` sincronizado a partir de `parametro-odoo/Parametro_Global` (branch `brodoo`): `19.0.1.9.0` -> `19.0.1.13.0`. Estava quatro versões menor atrás e carregava 13 ficheiros que a produção já tinha removido. Importa porque **é alvo de teste**: o `pg_run_odoo_addon_tests.ps1` corre `-i pg_brodoo --test-tags /pg_brodoo` contra esta cópia, pelo que um espelho velho testava código que não é o deployado
- verificado que o `deliverables.json` continua a ser publicado pelo `github_repository_publisher`: a migração `19.0.1.12.0` removeu a camada de *templates* de entregável (0 adoção em produção), não o artefacto do espelho. O compromisso documental passa a vir dos `project.milestone` standard, e a fonte 7 do `AGENTS_SHARED.md` continua válida
- `depends` do módulo continua `['project']` — os testes instalam sem dependências novas

## v2.13.1 - 2026-07-27

Resumo:
- `pg_odoo_migration_guard.py`: a verificação de coerência entre nome da base e finalidade passa a correr **antes** de autenticar, e repete-se depois. Estava a correr só depois, pelo que nunca era alcançada quando as credenciais falhavam — e, com credenciais válidas, autenticava numa base de produção antes de verificar se devia. Passa também a validar o nome **resolvido** pelo auto-heal, não só o declarado
- `SmartEnergy`: `odoo_ro.py` passa a ser uma casca fina sobre o guard partilhado; o `cutover.py` deixa de repontar o `conn.json` em disco, de recarregar o módulo e de desligar o bloqueio de produção por atribuição (`PROD_DB = '___cutover_confirmado___'`). Os outros sete scripts não precisaram de alteração — a assinatura do `kw` é a mesma

## v2.13.0 - 2026-07-27

Status:
- o método de migração de dados e o fluxo de demonstração com dados do cliente passam a ter template próprio

Resumo:
- novo `TPL_MIGRACAO_DADOS_ODOO` (article 785): método de migração entre bases Odoo, extraído do WP1 do SmartEnergy. O Passo 0 classifica a migração — **promoção** (mesmo modelo nas duas pontas) ou **remodelação** (modelo diferente) — e é essa classificação que decide se o ledger campo-a-campo é obrigatório. Reconciliação de contagens é obrigatória nos dois casos
- novo `TPL_CRIA_DEMO_DADOS_CLIENTE` (article 786): demonstração com dados reais no ambiente do cliente (branch `brodoo`), com o guia imprimível como entregável e a promoção delegada no template de migração
- `TPL_CRIA_DEMO` deixa de ser ambíguo: o mapeamento passa a bifurcar pela **origem dos dados** (fictícios vs reais do cliente), porque a regra dos e-mails `@example.com` é oposta nos dois fluxos
- o guia HTML fecha dois defeitos dos guias existentes no SmartEnergy: dependência de folha de estilo externa (colapsa numa sala sem rede) e ausência de `@media print` apesar de serem para imprimir
- ambos publicados no Odoo com a técnica do bloco `<pre>`; round-trip verificado byte a byte nos 17 templates
- registada em `PG_TROUBLESHOOTING.md` a fonte real do `pg_brodoo`: `parametro-odoo/Parametro_Global`, staging `brodoo`, produção `main` — era a informação que faltava

## v2.12.0 - 2026-07-27

Status:
- escrita no Odoo do cliente passa a ter guarda partilhada; nasce a finalidade de validação

Resumo:
- novo `scripts/pg_odoo_migration_guard.py`: ponto único de passagem para qualquer script que escreva dados no Odoo de um cliente (promoção `brodoo_dev` → `client_test`, migração Studio → standard, correcções em massa). Extraído do método já provado no WP1 do SmartEnergy
- **a autoridade passa a ser a finalidade da ligação, não o nome da base de dados** — em Odoo.sh o nome muda a cada rebuild da branch, pelo que constantes com o nome da staging ficam obsoletas e passam a bloquear todo o trabalho; a ligação é identificada pelo `base_url`, que é estável
- cinco camadas para uma escrita acontecer: método classificado na lista branca (não classificado é bloqueado), finalidade que permite escrever, `--confirm`, `allow_write=True` por chamada e `--allow-prod` em produção. Acresce aborto quando uma base com `main` no nome é declarada com finalidade diferente de `production`
- resolução automática do nome da base por `POST /web/database/list` quando a autenticação falha (rebuild da branch), sem SSH
- finalidade `client_test` (base de testes/validação do cliente) aceite pelo `ValidateSet` de `pg_odoo_client_query.ps1`, `pg_export_projeto_settings.ps1` e `pg_import_projeto_settings.ps1`

`RESOLVIDO na v2.13.1` — a finalidade `client_test` foi acrescentada em `pg.odoo.connection` na branch `brodoo` (staging) de `parametro-odoo/Parametro_Global`, commit `25feab8`, versão `19.0.1.13.0`. Falta o merge para `main` para chegar a produção. O `pg_brodoo` deste repositório está em `19.0.1.9.0` mas o **módulo em produção está em `19.0.1.12.2`**: esta cópia está três versões menor atrás e **não é a fonte do que está deployado**. Acrescentar a finalidade aqui produziria um fork e, se fosse deployada, uma regressão. A alteração tem de ser feita na fonte real do `pg_brodoo` — `parametro-odoo/Parametro_Global`, branch `brodoo` (staging), confirmada na v2.13.0 — e deployada; até lá, o `client_test` usa-se pelo ficheiro de ligação do guard, que não depende do módulo. Ver "Cópia local do `pg_brodoo`" em `docs/PG_TROUBLESHOOTING.md`.
- `AGENTS_SHARED.md`: nova secção "Migração de dados entre bases Odoo" com a matriz de permissão e as regras de operação (dry-run primeiro, idempotência, reconciliação obrigatória no fim, desactivar em vez de apagar)

## v2.11.0 - 2026-07-27

Status:
- geração de decks PowerPoint passa a ser determinística e partilhada entre templates

Resumo:
- novo `doc_templates/TPL_PONTO_SITUACAO_PPTX.md`: template executável para o deck de Ponto de Situação, com gate de conteúdo, schema de payload, QA visual obrigatório e checklist de entrega (publicado no Odoo Knowledge, article 784)
- nova identidade visual em código (`scripts/pg_pptx_identity.py`), extraída do ficheiro da marca `Template_Parametro_PowerPoint_Completo 1.pptx`: paleta, tipografia e geometria exactas, mais componentes (capa, cabeçalho, rodapé, cartões, KPIs, tabela, barras, listas numeradas)
- novo gerador `scripts/pg_build_ponto_situacao_pptx.py`: payload JSON entra, deck sai; mesmo payload produz ficheiros byte a byte iguais
- novos assets da marca em `scripts/assets/`: deck base sem slides (preserva tema e masters) e os dois logótipos oficiais extraídos do ficheiro original
- `AGENTS_SHARED.md`: novo mapeamento para "ponto de situação em PPTX" e regra que proíbe redesenhar a identidade a partir de descrição escrita ou usar o script legado `create_parametro_powerpoint_template.py`
- `PG_DOC_TEMPLATES_VERSIONING.md`: documentado onde vive de facto o conteúdo dos templates (corpo do article, não `pg_template_body_md`) e a técnica do bloco `<pre>` que garante round-trip sem perdas no pull

Correcções de identidade face ao que estava documentado:
- azul do título `#0099FF` e de acento `#009FE3` (estava `#0094E9`), escuro `#111E2D` (estava `#151D2B`), texto `#111827` (estava `#1F2937`)
- tipo de letra dos títulos é `Aptos Display`, não `Aptos`
- a capa não tem canto preto — esse elemento não existe no ficheiro da marca

## v2.10.0 - 2026-07-02

Status:
- simplificacao estrutural do `pg_brodoo` para 3 pilares: espelho, onboarding e compromisso documental
- `pg_brodoo` alinhado com a versao validada em producao `19.0.1.6.1`

Resumo:
- removidos os fluxos de sync sem uso real (`status`, `decisions`, `risks`, `deliveries`, `requirements`, `project_plan`, `budget`): modelos, servicos, vistas, scripts `pg_validate_*`/`pg_apply_*`, artefactos `.pg/PG_*_SYNC.json` e blocos derivados no `PG_CONTEXT.md`
- mantidos os pilares e artefactos de suporte: espelho (`.pg/project|planning|tasks|chatter|attachments|history`), `PG_SCOPE_SYNC`, `PG_EFFORT_SYNC`, onboarding e compromisso documental em `project.milestone` + `pg.deliverable.template` + `mail.activity`
- limpeza transversal das pontas soltas em scripts, docs vivos, `config.toml`, contrato `AGENTS.md`/`AGENTS_SHARED.md`, template `PG_CONTEXT.md` e workflow `pg_refresh_pg_context.yml`
- specs historicas (`docs/PG_005_*`) e pacotes de handoff preservados como registo

## v2.9.1 - 2026-04-24

Status:
- melhoria incremental compativel sobre a baseline `v2.9.0`

Resumo:
- `pg_clone_odoo_source` passa a usar cache global por serie em `%USERPROFILE%\.pg\odoo_src` (ou `PG_ODOO_SOURCE_ROOT`)
- cada repositorio deixa de duplicar o source Odoo e passa a ter `vendor/odoo_src` como ligacao para o cache global
- documentacao de setup e README atualizados para o novo fluxo partilhado

## v2.9.0 - 2026-04-12

Status:
- release de fecho formal da iteracao `v2.9`

Resumo:
- fecho formal da iteracao `v2.9`
- baseline `grounded chatter signals` promovida a release `v2.9.0`
- pipeline de ingestao, filtro, classificacao, validacao, grounding e explainability de sinais do chatter de projeto e task
- enriquecimento controlado de `status draft`, `consultive draft` e `scope draft` com sinais validados do chatter
- dashboard operacional com visibilidade agregada sobre sinais `candidate`, `validated`, `stale` e `rejected`
- apoio LLM controlado apenas para mensagens ambiguas do chatter, com JSON estrito, validacao forte e fallback deterministico

## v2.8.3 - 2026-04-12

Status:
- melhoria incremental compativel sobre a baseline `v2.8.2`

Resumo:
- apoio LLM controlado para mensagens ambiguas do chatter, restrito a classificacao em JSON estrito com validacao forte e fallback deterministico
- rejeicao automatica de saidas LLM fora de schema, contraditorias ou sem evidencia textual presente na mensagem original
- endurecimento da classificacao de sinais de `approval` para excluir estados pendentes como `waiting for approval`, evitando falsos positivos no grounding dos drafts

## v2.8.2 - 2026-04-10

Status:
- melhoria incremental compativel sobre a baseline `v2.8.0`

Resumo:
- pipeline de sinais de chatter fechada na install/upgrade do addon com cron e vistas carregadas pelo manifesto
- `status draft`, `consultive draft` e `scope draft` passam a consumir sinais validados do chatter como grounding secundario e auditavel
- dashboard operacional passa a expor visibilidade agregada sobre sinais validados, candidatos, stale e targets com refresh em falta

## v2.8.1 - 2026-04-10

Status:
- melhoria incremental compativel sobre a baseline `v2.8.0`

Resumo:
- abertura formal da `v2.9` com backlog objetivo em `docs/PG_V29_BACKLOG.md`
- `grounded chatter signals` fixado como proxima frente estrutural da framework
- `README`, roadmap e backlog alinhados para preparar o arranque da implementacao da `v2.9`

## v2.8.0 - 2026-04-09

Status:
- release de fecho formal da iteracao `v2.8`

Resumo:
- fecho formal da iteracao `v2.8`
- baseline brownfield acceleration promovida a release `v2.8.0`
- draft heuristico de enriquecimento de scope na task para `Scope Summary`, `Acceptance Criteria` e `Scope Kind`
- geracao e aplicacao assistida em massa desses drafts ao nivel do projeto
- dashboard brownfield incorporado no dashboard operacional
- draft operacional reforcado para projetos antigos
- pre-preenchimento consultivo assistido na task

## v2.7.13 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.12`

Resumo:
- a `project.task` passa a suportar drafts consultivos assistidos para `Recommendation Class`, `Standard Review`, `Additional Module Review`, `Studio Review` e `Recommendation Justification`
- as sugestoes passam a ter score de confianca, feedback explicito e modulo adicional sugerido quando aplicavel
- a aplicacao continua assistida e so promove campos oficiais ainda vazios, mantendo a separacao entre draft consultivo e decisao final oficial

## v2.7.12 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.11`

Resumo:
- o draft operacional passa a considerar explicitamente sinais brownfield vindos do `approved_scope`, backlog operacional, drafts `needs_review` e runs com erro
- o feedback do draft no projeto passa a indicar quando a consolidacao brownfield ainda esta incompleta antes do publish manual
- blockers, risks, next steps e pending decisions ficam mais uteis em projetos antigos sem transformar o publish oficial em automatico

## v2.7.11 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.10`

Resumo:
- o `PG Operational Dashboard` passa a incluir um bloco brownfield para consolidacao inicial de projetos antigos
- novos contadores e listas destacam tasks `approved_scope` sem `Scope Summary`, sem `Acceptance Criteria`, sem `Scope Kind` e drafts `needs_review`
- a visibilidade brownfield fica agregada no dashboard existente, sem criar uma superficie operacional paralela

## v2.7.10 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.9`

Resumo:
- novas acoes no projeto para gerar drafts de enriquecimento de scope em massa e aplicar sugestoes elegiveis de alta confianca
- o projeto passa a expor contadores de consolidacao brownfield para drafts pendentes, casos `needs_review` e sugestoes aplicadas
- o `scope sync` continua a publicar apenas campos oficiais, mesmo quando os drafts sao gerados ao nivel do projeto

## v2.7.9 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.8`

Resumo:
- novo draft heuristico de enriquecimento de scope ao nivel da task para sugerir `Scope Kind`, `Scope Summary` e `Acceptance Criteria`
- as sugestoes passam a ter score de confianca, feedback e metadados de geracao, sem contaminar o `scope sync` factual ate aplicacao explicita
- nova cobertura automatizada garante que os campos sugeridos nao entram no `PG_SCOPE_SYNC.json` antes de serem promovidos a campos oficiais

## v2.7.8 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.7`

Resumo:
- nova abertura formal da `v2.8` com backlog objetivo em `docs/PG_V28_BACKLOG.md`
- `brownfield acceleration` fixado como proxima frente prioritaria da framework
- roadmap e documentacao central alinhados para colocar o enriquecimento de scope como `P0`

## v2.7.7 - 2026-04-09

Status:
- melhoria incremental compativel sobre a baseline `v2.7.6`

Resumo:
- novo `docs/PG_SCOPE_ENRICHMENT_TECHNICAL_DESIGN.md` com desenho tecnico do automatismo para reduzir dependencia manual de `Scope Summary`, `Acceptance Criteria` e `Scope Kind`
- roadmap atualizado para fixar `brownfield acceleration` como proxima frente recomendada apos a `v2.7`
- documentacao central alinhada para refletir a nova prioridade de automatismo

## v2.7.6 - 2026-04-02

Status:
- melhoria incremental compativel sobre a baseline `v2.7.5`

Resumo:
- novo `docs/PG_REAL_PROJECT_ADOPTION_RUNBOOK.md` com execucao A a Z para um colega testar a adocao da framework num projeto real em branch de testes e base de staging
- novo `docs/PG_REAL_PROJECT_ADOPTION_REPORT_TEMPLATE.md` para recolha estruturada de evidencias, SHAs, problemas e decisao `Go / No-Go`
- `docs/PG_REAL_PROJECT_ADOPTION_CHECKLIST.md` ajustada para branch de testes, base de staging, handoff entre colegas e entregaveis finais do executor

## v2.7.5 - 2026-04-02

Status:
- melhoria incremental compativel sobre a baseline `v2.7.4`

Resumo:
- novo `docs/PG_REAL_PROJECT_ADOPTION_CHECKLIST.md` com checklist executavel para a primeira adocao real da framework
- foco explicito em projetos `brownfield`, com consolidacao do estado atual em vez de reconstrucao do historico
- criterios de esforco, gates de saida e sinais objetivos para decidir quando a adocao ja justifica mais automatismo

## v2.7.4 - 2026-04-02

Status:
- hotfix compativel sobre a baseline `v2.7.3`

Resumo:
- dark mode do separador `AI Dev Assistant` passa a usar asset `.dark.scss` proprio do Odoo
- remocao do fallback por `prefers-color-scheme`, que prendia o separador ao tema do sistema operativo
- o separador volta a acompanhar corretamente a preferencia light/dark definida no perfil do utilizador

## v2.7.3 - 2026-04-02

Status:
- hotfix compativel sobre a baseline `v2.7.2`

Resumo:
- segundo ajuste de UX do separador `AI Dev Assistant` para dark mode no backend do Odoo
- fallback adicional para ambientes onde o dark mode nao expoe `data-bs-theme="dark"`
- grelha/lista embebida do historico consultivo passa a herdar a paleta escura correta

## v2.7.2 - 2026-04-02

Status:
- hotfix compativel sobre a baseline `v2.7.1`

Resumo:
- UX do separador `AI Dev Assistant` alinhada com o tema light/dark do backend do Odoo
- substituicao de superficies e inputs com cores fixas por tokens semanticos theme-aware
- melhoria de contraste em dark mode para cards, textos, badges, info notes e textareas

## v2.7.1 - 2026-04-01

Status:
- hotfix compativel sobre a baseline `v2.7.0`

Resumo:
- leitura explicita UTF-8 nos scripts de refresh, smoke test e materializacao de contexto
- eliminacao de falsos positivos de mojibake no `PG_CONTEXT.md` em Windows PowerShell
- correcao do runtime partilhado usado pela GitHub Action `PG Refresh Context`

## v2.7.0 - 2026-04-01

Status:
- baseline formal de automacao intuitiva sobre a referencia `v2.6.0`

Resumo:
- fecho formal da iteracao `v2.7`
- GitHub Action para regenerar `PG_CONTEXT.md` a partir dos snapshots `.pg`
- drafts factuais de status com revisao e publish manual
- wizard de onboarding do addon
- fluxo consultivo guiado na task
- dashboard operacional centralizado
- release pronta para adocao como baseline `v2.7.0`

## v2.6.5 - 2026-04-01

Status:
- melhoria incremental compativel sobre a baseline `v2.6.0`

Resumo:
- novo fluxo consultivo guiado na task, com etapas explicitas de discovery, fit-gap, recomendacao final e gate
- a task passa a mostrar qual o passo atual e o que falta para desbloquear AI
- a UX do fluxo AI deixa de depender tanto de memoria metodologica informal
- testes automatizados passam a cobrir a progressao guiada do fluxo consultivo

## v2.6.6 - 2026-04-01

Status:
- melhoria incremental compativel sobre a baseline `v2.6.0`

Resumo:
- novo dashboard operacional centralizado do addon
- agregacao de projetos com atencao de scope/status, tasks bloqueadas ou prontas para AI e runs falhadas
- dashboard passa a abrir diretamente as listas filtradas para acao operacional
- testes automatizados passam a cobrir a agregacao principal do dashboard

## v2.6.4 - 2026-04-01

Status:
- melhoria incremental compativel sobre a baseline `v2.6.0`

Resumo:
- novo wizard de onboarding do addon para configurar GitHub e projeto num unico fluxo
- import da conta GitHub, sync de branches e validacao de readiness passam a estar acessiveis no wizard
- o wizard aplica repositorio, branch e toggles de scope/status sync sem obrigar a navegar por settings dispersas
- testes automatizados passam a cobrir o novo fluxo de onboarding

## v2.6.3 - 2026-04-01

Status:
- melhoria incremental compativel sobre a baseline `v2.6.0`

Resumo:
- geracao automatica de draft operacional no projeto antes do `status sync` oficial
- novas acoes `Gerar Draft de Situacao` e `Aplicar Draft ao Status`
- separacao explicita entre `draft` revisto e `published` manual
- testes automatizados do addon reforcados para validar o novo fluxo de draft

## v2.6.2 - 2026-04-01

Status:
- melhoria incremental compativel sobre a baseline `v2.6.0`

Resumo:
- novo workflow GitHub para regenerar `PG_CONTEXT.md` quando `.pg/PG_SCOPE_SYNC.json` ou `.pg/PG_PROJECT_STATUS_SYNC.json` mudam no remoto
- bootstrap e sync de assets passam a introduzir este workflow nos projetos
- novo guia `docs/PG_GITHUB_CONTEXT_AUTOMATION.md` com secret, variaveis e fluxo de adocao
- smoke test passa a validar a presenca e a semantica minima do workflow

## v2.6.1 - 2026-04-01

Status:
- melhoria incremental compativel com abertura da iteracao `v2.7`

Resumo:
- nova `docs/PG_V27_BACKLOG.md` com backlog orientado a automacao intuitiva da framework
- abertura formal da `v2.7` sem alterar a baseline funcional `v2.6.0`
- roadmap e versioning passam a refletir a nova frente: GitHub Action para `PG_CONTEXT.md`, auto-draft de status, wizard de onboarding, fluxo guiado consultivo e dashboard operacional

## v2.6.0 - 2026-04-01

Status:
- release de fecho formal da iteracao `v2.6`

Resumo:
- gating consultivo antes de AI entregue na `project.task`
- classificacao final obrigatoria `standard`, `modulo adicional`, `Studio` ou `custom`
- separacao explicita entre `approved_scope`, backlog operacional e notas internas
- trilho minimo de decisao consultiva com historico proprio na task
- `status sync` manual-only confirmado com indicador de `Needs Publish` e feedback de revisao
- backlog da `v2.6` fechado e baseline promovida a release taggeada

## v2.5.6 - 2026-04-01

Resumo:
- reavaliacao dirigida do `status sync` confirma a politica `manual-only`
- o projeto passa a sinalizar `Status Sync Needs Publish` quando o estado operacional muda depois do ultimo publish
- novo `Status Sync Review Feedback` torna visivel quando o publish manual ainda esta em falta
- nova nota arquitetural com criterio explicito para futura reavaliacao do `status sync`

## v2.5.5 - 2026-04-01

Resumo:
- novo trilho de decisao consultiva na `project.task`
- snapshots minimos de decisao passam a ser registados para `gate_ready`, `prompt_generated` e `codex_queued`
- o contexto entregue ao AI passa a incluir historico consultivo minimo, deixando de depender apenas do texto livre atual
- cobertura automatizada adicionada para `PG-V26-004`

## v2.5.4 - 2026-04-01

Resumo:
- separacao explicita entre `approved_scope`, `operational_backlog` e `internal_note` na task
- `.pg/PG_SCOPE_SYNC.json` passa a incluir apenas tasks classificadas como `approved_scope`
- backlog operacional e notas internas deixam de entrar em `scope_items`
- `PG_CONTEXT.md` continua focado no ambito factual aprovado
- cobertura automatizada adicionada para `PG-V26-003`

## v2.5.3 - 2026-04-01

Resumo:
- classificacao consultiva final obrigatoria na task antes do fluxo AI
- quatro classes suportadas: `standard`, `modulo adicional`, `Studio`, `custom`
- revisoes minimas por etapa e justificacao final passam a ser exigidas antes do gate consultivo poder ficar `ready`
- a classificacao e validada contra as restricoes do projeto e entra no contexto entregue ao AI
- novos testes automatizados do addon para `PG-V26-002`

## v2.5.2 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo gate consultivo minimo na `project.task` antes de `Gerar Prompt AI` e `Executar com Codex`
- o gate exige notas minimas e contexto factual basico no projeto antes de poder ser marcado como `ready`
- alteracoes relevantes na task ou no contexto consultivo do projeto reabrem automaticamente o gate
- novo conjunto de testes automatizados do gate em Odoo 19
- fecho do item `PG-V26-001` do backlog objetivo da `v2.6`

## v2.5.1 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- nova `docs/PG_V26_BACKLOG.md` com backlog objetivo da iteracao consultiva seguinte
- roadmap e backlog da `v2.5` passam a deixar explicito que a baseline tecnica ficou fechada e que a frente seguinte e governacao consultiva
- abertura formal da `v2.6` sem alterar a baseline funcional `v2.5.0`

## v2.5.0 - 2026-04-01

Status:
- melhoria incremental compativel com fecho da iteracao `v2.5`

Resumo:
- novo `scripts/pg_bootstrap_assisted.ps1` para agregar bootstrap, sync de assets, sync opcional do addon, clone opcional do source Odoo e smoke test final
- README e checklist de bootstrap passam a documentar um fluxo curto assistido para arranque de novos repositorios
- fecho do item `PG-V25-007` e conclusao formal da iteracao `v2.5`

## v2.4.11 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo `docs/PG_AI_DEV_ASSISTANT_OPERATIONS.md` com operacao dedicada do addon `pg_brodoo`
- setup GitHub, separacao entre sync factual e AI delivery, permissoes recomendadas e troubleshooting Odoo 19 passam a estar documentados num unico guia
- fecho do item `PG-V25-006` do backlog objetivo da `v2.5`

## v2.4.10 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo `docs/PG_CONTENT_HYGIENE.md` com checklist curta para encoding, placeholders e coerencia semantica do conteudo
- `pg_smoke_test_repo.ps1` passa a sinalizar mojibake, placeholders publicados e sobreposicoes suspeitas entre `risks`, `blockers`, `next_steps` e `pending_decisions`
- fecho do item `PG-V25-005` do backlog objetivo da `v2.5`

## v2.4.9 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- `PG_PROJECT_STATUS_SYNC` fica formalmente definido como `manual-only` na baseline atual
- fecho do item `PG-V25-004` do backlog objetivo da `v2.5`
- backlog, roadmap, README, versioning e guia de testes alinhados com a decisao de produto

## v2.4.8 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- `pg_smoke_test_repo.ps1` passa a validar semantica minima dos snapshots publicados e dos blocos `PG_AUTO` do `PG_CONTEXT.md`
- o smoke test diferencia falhas estruturais de warnings documentais
- fecho do item `PG-V25-003` do backlog objetivo da `v2.5`

## v2.4.7 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- nova `docs/PG_RELEASE_POLICY.md` com politica operacional de release do `_pg_template`
- fecho do item `PG-V25-002` do backlog objetivo da `v2.5`
- alinhamento entre README, versioning e backlog para promover baselines validadas a releases utilizaveis

## v2.4.6 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- nova suite automatizada minima do addon `pg_brodoo` para Odoo 19
- novo `scripts/pg_run_odoo_addon_tests.ps1` para validar instalacao, upgrade e testes locais do addon
- fecho do item `PG-V25-001` do backlog objetivo da `v2.5`

## v2.4.5 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo `docs/PG_V25_BACKLOG.md` com backlog objetivo, priorizado e orientado a criterios de aceitacao
- ligacao explicita entre roadmap, backlog e a proxima iteracao operacional da framework
- clarificacao do ponto de chegada esperado para o fecho da `v2.5`

## v2.4.4 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo `docs/PG_TROUBLESHOOTING.md` com resolucao dos problemas reais encontrados no piloto
- clarificacao operacional de scripts, snapshots placeholder, GitHub token, acesso a `odoo/enterprise`, Odoo 19 e encoding
- melhoria da capacidade de suporte e onboarding sem alterar a base funcional da framework

## v2.4.3 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- `.gitattributes` do template e dos repositorios bootstrapados passa a cobrir tambem `ps1`, `cmd`, `toml`, `json`, `yaml` e `.editorconfig`
- reducao do ruido de `LF/CRLF` em ficheiros operacionais criticos do template
- endurecimento coerente com a politica de escrita explicita em UTF-8 introduzida em `v2.4.1`

## v2.4.2 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- novo `pg_smoke_test_repo.ps1` para validacao rapida de repositorios bootstrapados
- novo `pg_sync_shared_assets.ps1` para sincronizar ficheiros partilhados do template em repositorios ja existentes
- documentacao do bootstrap reforcada para suportar alinhamento continuo entre `_pg_template` e projetos piloto

## v2.4.1 - 2026-04-01

Status:
- melhoria incremental compativel

Resumo:
- scripts que materializam `PG_CONTEXT.md` e `PG_SCOPE_INTAKE.yaml` passam a escrever ficheiros em UTF-8 explicito
- bootstrap passa a copiar `.editorconfig` para novos repositorios
- endurecimento contra problemas de encoding e line endings observados durante a validacao do piloto

## v2.4 - 2026-04-01

Status:
- mudanca estrutural relevante no template

Resumo:
- addon `pg_brodoo` passa a suportar publicacao manual de `.pg/PG_PROJECT_STATUS_SYNC.json`
- novos modelos e vistas de `PG Status Sync Runs` para rastreabilidade operacional do snapshot
- `PG_CONTEXT.md` passa a materializar tambem `scope_items` em bloco auto-gerido proprio
- correcoes de compatibilidade Odoo 19 consolidadas no addon durante o ciclo de validacao real
- guia de testes atualizado para incluir `status sync` e a nova versao funcional do addon

## v2.3 - 2026-03-31

Status:
- mudanca estrutural relevante no template

Resumo:
- fluxo principal de consulta ao Odoo passa de instalacao local do ERP para `git clone` do source oficial
- novo layout `vendor/odoo_src/community` e `vendor/odoo_src/enterprise`
- novo script `pg_clone_odoo_source` e sincronizacao do `PG_CONTEXT.md` adaptada ao source checkout
- `pg_link_odoo_core` passa a wrapper legado de compatibilidade

## v2.2 - 2026-03-31

Status:
- mudanca estrutural relevante no template

Resumo:
- novo contrato `.pg/PG_SCOPE_SYNC.json` para sync factual de ambito vindo do Odoo
- novos scripts para validar, aplicar e orquestrar scope sync no `PG_CONTEXT.md`
- bootstrap, `config.toml` e documentacao atualizados para suportar scope sync

## v2.1 - 2026-03-24

Status:
- melhoria incremental compativel sobre o v2.0

Resumo:
- contrato tecnico mais explicito para `.pg/PG_PROJECT_STATUS_SYNC.json`
- validacao dedicada do snapshot factual antes de atualizar o `PG_CONTEXT.md`
- documento de integracao Odoo -> repositorio com campos, botao manual e regras do payload

## v2.0 - 2026-03-24

Status:
- mudanca estrutural relevante no template

Resumo:
- `AGENTS.md` local passa a ser wrapper leve por projeto
- `templates/AGENTS_SHARED.md` concentra as regras partilhadas do framework
- bootstrap cria `.pg_framework/` como referencia local ao framework partilhado
- formalizacao tecnica do modelo shared framework vs project-local state

## v1.2 - 2026-03-24

Status:
- melhoria incremental compativel

Resumo:
- `PG_SCOPE_INTAKE.yaml` como fonte estruturada local para ambito inicial do projeto
- `.pg/PG_PROJECT_STATUS_SYNC.json` como snapshot factual do estado operacional vindo do Odoo
- scripts para inicializar intake, materializar blocos auto-geridos do `PG_CONTEXT.md` e aplicar o ultimo snapshot factual
- clarificacao do modelo partilhado vs local no framework

## v1.1 - 2026-03-24

Status:
- melhoria incremental compativel

Resumo:
- camada leve de discovery antes do `PG_CONTEXT`
- novo `PG_DISCOVERY_PROMPT.md` para qualificar pedidos incompletos, ambiguos ou ainda imaturos para decisao
- gate explicito para seguir para contexto, aprofundar discovery ou pedir demo / validacao standard

## v1.0 - [YYYY-MM-DD]

Status:
- ready for production use

Resumo:
- bootstrap consultivo para repositorios Odoo
- ordem obrigatoria de decisao: standard -> modulo adicional -> Studio -> custom
- gestao explicita de evidencia, incerteza e validacao contra o source Odoo de referencia
- memoria consultiva leve e checklist de verificacao antes de recomendacoes finais
