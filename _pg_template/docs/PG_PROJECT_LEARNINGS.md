# PG_PROJECT_LEARNINGS

Este ficheiro guarda aprendizagens consultivas reutilizáveis observadas em projetos Odoo.
Serve para acelerar triagem, reconhecer sinais recorrentes e evitar erros repetidos.
Não substitui a validação do projeto atual contra `PG_CONTEXT.md`, código do projeto, `vendor/odoo_src` e documentação oficial da versão ativa.

## LEARNING 001 - Studio parecia suficiente, mas fragilizou o processo
Contexto:
- pedido de campos, regras e automações cresceu iterativamente sobre o mesmo fluxo

Sinal inicial:
- a solução parecia "leve" e rapida porque cada alteração isolada era pequena

O que aconteceu:
- a soma das pequenas regras criou dependência de Studio difícil de manter e explicar

Aprendizagem:
- Studio e bom para extensoes moderadas e bem delimitadas, não para substituir desenho funcional consistente

Heuristica reutilizável:
- se o requisito atravessa vários modelos, vários estados e várias exceções, reavaliar cedo se Studio continua adequado

## LEARNING 002 - Módulo standard adicional evitou custom desnecessario
Contexto:
- pedido parecia exigir desenvolvimento para approvals e governance operacional

Sinal inicial:
- a equipa assumiu que o módulo principal não cobria o caso

O que aconteceu:
- um módulo standard adicional do Odoo cobria a maior parte do requisito com adaptação de processo aceitável

Aprendizagem:
- limitar a análise aos módulos já instalados aumenta risco de customização prematura

Heuristica reutilizável:
- quando o gap parece estrutural, procurar primeiro módulos standard adicionais no `vendor/odoo_src` da versão ativa

## LEARNING 003 - O pedido era preferência, não necessidade real
Contexto:
- cliente pediu alteração funcional com forte componente de interface e conforto operativo

Sinal inicial:
- a justificação vinha em termos de preferência e não de risco, custo ou compliance

O que aconteceu:
- a necessidade real foi resolvida com configuração e treino, sem alterar o comportamento base

Aprendizagem:
- nem toda a fricção operacional e gap funcional do sistema

Heuristica reutilizável:
- antes de avaliar custom, perguntar sempre que decisão de negocio falha sem a alteração pedida

## LEARNING 004 - Parecia documental, mas era operacional
Contexto:
- pedido foi descrito como necessidade de anexos, documentos e assinatura

Sinal inicial:
- a conversa focava ficheiros e templates, mas os erros aconteciam no handoff entre equipas

O que aconteceu:
- o problema principal estava no fluxo operacional, não na camada documental

Aprendizagem:
- sintomas documentais podem esconder falha de processo, aprovação ou ownership

Heuristica reutilizável:
- se ha muitos anexos e exceções, validar primeiro o processo que gera esses documentos

## LEARNING 005 - Workflow parecia complexo, mas o problema era de processo
Contexto:
- equipa pediu múltiplos estados, aprovações e validações adicionais

Sinal inicial:
- cada interveniente queria um checkpoint próprio no sistema

O que aconteceu:
- a complexidade vinha da indefinição de responsabilidade e não de limite real do Odoo

Aprendizagem:
- desenhar workflow custom sobre processo mal definido cristaliza ineficiência

Heuristica reutilizável:
- se o pedido de estados cresce depressa, parar e clarificar ownership, exceções e critério de decisão antes de modelar o fluxo

## LEARNING 006 - Reporting falhou por dados, não por falta de dashboard
Contexto:
- pedido para dashboards executivos mais ricos e relatórios adicionais

Sinal inicial:
- havia pressão para ver melhor, mas pouca confianca nos números de origem

O que aconteceu:
- o gargalo principal estava em classificação, completude e disciplina de registo de dados

Aprendizagem:
- dashboard novo não corrige semantica de dados inconsistente

Heuristica reutilizável:
- antes de recomendar reporting adicional, validar definições de KPI, campos obrigatórios e qualidade dos dados base

## LEARNING 007 - O filtro não estava avariado; a migração 18 → 19 não recalculou o campo
Contexto:
- utilizador reportou que o filtro "Employees" na escolha de participantes do Calendar devolvia meia dúzia de nomes em vez de todos os colegas (observado no Odoo da Parâmetro Global, 2026-08-10: 4 nomes de 13 empregados activos, e 2 desses 4 já arquivados)

Sinal inicial:
- o sintoma parecia de vista, permissões ou multi-empresa, e o filtro é standard (`hr`, domínio `[('employee', '=', True)]`)

O que aconteceu:
- em Odoo 19 o campo `res.partner.employee` deixou de ser a checkbox manual do `base` e passou a `compute='_compute_employee', store=True, readonly=False` no módulo `hr`, dependente de `employee_ids` (ser `work_contact_id` de um `hr.employee` activo)
- a migração de 18 para 19 não recalculou a coluna dos registos existentes: só as fichas criadas ou alteradas depois do upgrade dispararam o cálculo, e arquivar um empregado também não dispara recálculo (o `work_contact_id` não muda), deixando flags a `True` a mais
- a correcção foi de dados, com reconciliação de contagens no fim; não houve código, Studio nem módulo novo

Aprendizagem:
- quando uma versão nova converte um campo manual em calculado e armazenado, os dados antigos não se corrigem sozinhos; o sintoma chega ao utilizador como "o filtro está avariado" e leva a equipa a procurar na camada errada

Heuristica reutilizável:
- perante um filtro standard que devolve resultados incompletos, comparar primeiro a contagem do critério com a contagem da fonte que o devia alimentar (aqui: `res.partner` com `employee = True` vs `hr.employee` com `work_contact_id` preenchido); se divergirem, é drift de dados e não configuração
- confirmar no `vendor/odoo_src` se o campo mudou de natureza entre a versão de origem e a de destino da migração — a definição do campo na versão nova explica o sintoma melhor do que a vista
- tratar como defeito latente de frota: qualquer base que tenha migrado de 18 para 19 com `hr` instalado tem o mesmo desvio até ser recalculada

## LEARNING 008 - O histórico importado do SAF-T batia certo, mas as declarações não o viam
Contexto:
- contabilidade passada para o Odoo a meio do ano (Reckon.AI, Odoo 19 com Exo PT+, 2026): movimentos de janeiro a julho importados do SAF-T de contabilidade do sistema antigo

Sinal inicial:
- o balancete batia ao cêntimo com o SAF-T, e por isso a importação parecia concluída

O que aconteceu:
- a declaração periódica da Exo só mostrava os campos de regularização: só conta linhas ligadas a um imposto, e as linhas importadas vêm só com a conta
- o Balanço e a DR da Exo saíam a zeros: somam pela taxonomia SNC da conta, e nenhuma conta a tinha (nem em produção)
- a Modelo 10 da Exo lê as retenções dos impostos de retenção; as retenções importadas também não estão ligadas a imposto
- os relatórios financeiros do Odoo estavam certos o tempo todo, porque somam por código de conta; há dois "Balanços" no menu e validou-se o errado

Aprendizagem:
- importar movimentos não é o mesmo que eles contarem nas declarações; cada declaração da localização tem a sua fonte (imposto na linha, grelha, taxonomia) e cada uma tem de ser preenchida e verificada

Heuristica reutilizável:
- validar sempre com as declarações da localização (Exo › Reporting › Portugal), não com os relatórios financeiros do Odoo
- num histórico importado, ligar as linhas de IVA e as bases aos impostos e atribuir a taxonomia das contas a partir do `TaxonomyCode` do SAF-T
- método completo: `doc_templates/TPL_MIGRACAO_CONTABILIDADE_MEIO_ANO.md`

## LEARNING 009 - O importador de SAF-T criou fichas duplicadas e parceiros errados sem dar erro
Contexto:
- importação do SAF-T de contabilidade com a Exo PT+ (Reckon.AI, 2026)

Sinal inicial:
- os totais batiam e a contabilidade validou primeiro os valores, não as fichas

O que aconteceu:
- o importador só reconhece um parceiro existente quando o NIF vem escrito igual; com espaço, sem o prefixo do país ou com ele, cria outra ficha — 56 NIF ficaram em duas ou três fichas, com as faturas numa e os pagamentos noutra
- nos lançamentos de bancos agregados (um por mês, com dezenas de entidades), o SAF-T traz uma só entidade no cabeçalho e o importador põe-na em todas as linhas
- foi a contabilidade que os encontrou, ao comparar os extratos de clientes e fornecedores com o balancete

Aprendizagem:
- uma verificação de saldos por conta não apanha erros de parceiro: o total da conta bate mesmo com as linhas no parceiro errado

Heuristica reutilizável:
- comparar cada linha de clientes e fornecedores com a entidade da sua subconta no SAF-T (lançamento, valores e descrição) e exigir 0 diferentes
- fundir as fichas pelo NIF normalizado (sem espaços nem prefixo) antes de atribuir parceiros, com a fusão de contactos do Odoo; fica a ficha que já existia ou a que tem documentos certificados

## LEARNING 010 - Mudar a conta de uma linha refez o IVA do lançamento
Contexto:
- consolidação do plano de contas sobre lançamentos importados já ligados a impostos (Reckon.AI, 2026)

Sinal inicial:
- o passo de juntar subcontas falhou com "The following entries are unbalanced", e parecia que nada tinha sido escrito

O que aconteceu:
- escrever numa linha de um lançamento com impostos fez o Odoo recalcular o IVA: apagou as linhas de IVA originais, criou outras sem as grelhas e, num lançamento, uma "Automatic Balancing Line" de 460 € na conta transitória
- só o último lote, o que falhou, foi revertido; os anteriores ficaram escritos e a base teve de ser refeita

Aprendizagem:
- em lançamentos com impostos, qualquer escrita nas linhas (conta, parceiro, grelha, data) passa pelo recálculo do IVA, salvo com o contexto `skip_invoice_sync`

Heuristica reutilizável:
- toda a escrita em linhas contabilísticas por script passa `skip_invoice_sync`, e também `button_draft` e `action_post`
- a verificação compara cada linha de IVA com a fonte (SAF-T) e conta as linhas de equilíbrio automático; com uma só diferente, a base não se repara: refaz-se o ensaio

## LEARNING 011 - O SAF-T de faturação de outro programa não entra pelo importador da Exo
Contexto:
- vendas de agosto e setembro faturadas no programa antigo (PHC) depois da data de corte da contabilidade (Reckon.AI, 2026)

Sinal inicial:
- o importador SAF-T da Exo processou o ficheiro sem erro, mas só encontrou clientes: 0 lançamentos, 0 artigos, e 6 clientes "a criar" que já existiam com o NIF noutro formato

O que aconteceu:
- o importador só lê parceiros, contas, produtos e lançamentos contabilísticos; um SAF-T de faturação não tem lançamentos
- as vendas não podem ser reemitidas no Odoo (já foram comunicadas à AT); o PT+ tem séries de "Integração" (Método de Origem "I") para documentos emitidos noutra aplicação

Aprendizagem:
- a fatura integrada fica com o número, o ATCUD, o hash e a data de sistema do original, e sai no SAF-T do Odoo com SourceBilling "I"; o que não está documentado: Nº do Doc. Integrado com o tipo ("FT FT1/467", sem ele o XSD falha), HashControl "certificado.versão", artigo com categoria em cada linha, e notas de crédito ligadas à linha da fatura de origem
- um documento integrado lançado não volta a rascunho nem se apaga; um rascunho deixado parte a exportação do SAF-T

Heuristica reutilizável:
- o próximo número da sequência acerta-se imediatamente antes de cada lançamento (também nas repetições), para o nome ficar igual ao original
- ensaiar até bater certo, reconstruir a base de testes e fazer um ensaio final limpo; notas de crédito cuja origem é anterior ao corte entram como lançamentos (o "rappel" não serve)

## LEARNING 012 - Ligar os bancos a meio do ano: o IBAN arquivado e a data que o ecrã não calcula
Contexto:
- associação das contas bancárias já ligadas em agosto aos diários das contas da contabilidade, depois da passagem a produção (Reckon.AI, 2026)

Sinal inicial:
- diários criados com IBAN ficavam sem IBAN, sem aviso; a sincronização ia criar diários e contas novas

O que aconteceu:
- o IBAN existia como conta bancária arquivada do parceiro da empresa: o Odoo encontra-a, ignora-a por estar arquivada e não cria outra
- a outra empresa da base (a criada por defeito) tinha diários com os mesmos IBAN, e a procura do diário corre em todas as empresas marcadas no seletor
- o ecrã Online Synchronization associa diário e conta online sem calcular a data de arranque; o assistente calcula-a, mas só existe numa ligação nova

Aprendizagem:
- antes de criar diários, procurar as contas bancárias por número com `active_test=False` e desarquivar; arquivar os diários de outras empresas com os mesmos IBAN
- associar no ecrã, pondo também "Last Transaction Synchronized on" no dia a seguir à data de corte, e confirmar por leitura antes de buscar movimentos

Heuristica reutilizável:
- moeda estrangeira: taxas do BCE desde o início do ano e atualização diária antes de qualquer movimento; diário criado já na moeda
- se o saldo inicial calculado não bater com o extrato, procurar pagamentos com cartão pendentes no momento da sincronização

## LEARNING 013 - A cópia de ensaio não mostra que a série de integração tem de estar Em Curso
Contexto:
- importação em produção das vendas faturadas no programa antigo (PHC) como documentos integrados, depois de um ensaio final de 40 de 40 numa base de testes copiada da produção (Reckon.AI, 2026)

Sinal inicial:
- o primeiro documento foi recusado em produção: "You're trying to issue a fiscal document using a non registered series"; na base de testes as mesmas séries, também em rascunho, lançaram sem erro

O que aconteceu:
- as duas bases tinham o mesmo código de subscrição da Exo; a diferença era o Serviço de Certificação da empresa (`l10n_pt_cert_service_backend`): "Test" na cópia, "Exo Software" em produção; só o da Exo verifica o estado da série
- a mensagem manda registar a série, mas as séries de integração não se registam na AT; o botão "Registar" nem aparece nelas, e o próprio é "Set Running" (`action_set_running`), documentado pela Exo em Registo de Séries

Aprendizagem:
- antes de uma operação irreversível em produção, comparar a configuração da empresa entre a cópia e a produção (subscrição, serviço de certificação, séries) em vez de assumir que a cópia é igual
- numa série de integração em curso, nunca usar "Cancelar" nem "Finalizar": comunicam à AT uma série que pertence a outro programa

Heuristica reutilizável:
- em produção, importar primeiro um só documento e conferir o hash, o ATCUD e o HashControl com o SAF-T de origem; depois os restantes
- o "preparar" do script põe as séries de integração Em Curso; o "cannot marshal None" do XML-RPC nesse método não é erro (o método correu)
