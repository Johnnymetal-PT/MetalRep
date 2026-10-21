# PG_CONTEXT - Memória funcional e decisória

> Fonte de verdade do estado funcional, técnico e consultivo do projeto.
> Alguns blocos marcados com `PG_AUTO` podem ser atualizados automaticamente a partir de `PG_SCOPE_INTAKE.yaml`, `.pg/PG_PROJECT_STATUS_SYNC.json` e scripts do template.

## Estado Oficial do Projeto

### Identificação do projeto
<!-- PG_AUTO:IDENTIFICACAO:START -->
Nome do projeto: Odoo -Sofmovel
Cliente / unidade: Sofmovel - operação comercial e eCommerce (Momentos D Argumento, Lda)
Resumo funcional do repositorio: Evolução do Odoo 17 Enterprise da Sofmovel para vendas, eCommerce, POS, compras, stock/expedição e gestão de catálogo com addons custom PG.
Fase atual do projeto: [PONTO POR VALIDAR]
<!-- PG_AUTO:IDENTIFICACAO:END -->

### Parâmetros Odoo ativos
Versao do Odoo: 17.0
Edicao: enterprise
Ambiente: on_premise
Path do core: [PONTO POR VALIDAR]
Path source Enterprise: [NAO CONFIGURADO]
Documentação oficial base: [PONTO POR VALIDAR]
Documentação Studio: [PONTO POR VALIDAR]
Documentação Developer: [PONTO POR VALIDAR]
Última sincronização de âmbito: [NAO EXECUTADA]
Fonte do âmbito sincronizado: [PONTO POR VALIDAR]
Última sincronização automática: [NAO EXECUTADA]

### Restrições do projeto
<!-- PG_AUTO:RESTRICOES:START -->
Configuracao standard permitida?: yes
Modulos standard adicionais permitidos?: yes
Odoo Studio permitido?: yes
Custom permitido?: yes
Restricoes contratuais adicionais: Não alterar core Odoo nem vendor/odoo_src; manter compatibilidade com Odoo 17; usar prefixo pg nas customizações; validar standard, módulos adicionais e Stud...
<!-- PG_AUTO:RESTRICOES:END -->

### Pedido funcional atual
<!-- PG_AUTO:PEDIDO_ATUAL:START -->
Requisito / pedido atual: [PREENCHER]
Objetivo de negocio: Automatizar e estabilizar a operação comercial multicanal, reduzindo trabalho manual na atualização de produtos, preços, stock, compras e expedição.
Trigger: Necessidade de manter/evoluir o Odoo da Sofmovel para catálogo, eCommerce/POS, compras e logística com regras próprias
Frequencia: Recorrente - atualizações de catálogo, preços, stock, imagens e documentos conforme ficheiros/necessidade operacional...
Volumes: Catálogo com produtos, variantes, imagens, anexos, stocks, referências internas e múltiplos armazéns; dimensão exata...
Urgencia: unknown
Criterios de aceitacao:
- kave o produto está com quantidades em mão mas só que se formos ao nosso
- website ele diz que não tem stock.
- Os produtos da kave que estão a ser criados agora por defeito
- O ambito aprovado deve refletir eliminar recebimentos a mais.
- aos recursos humanos. Não queremos que eles tenham acesso à parte dos
- funcionários, pois estão a conseguir visualizar a informação privada de cada
- um, nomeadamente a parte dos recursos humanos.
- coincidir com o stock, porque neste momento só diz de 3 a 4 semanas
<!-- PG_AUTO:PEDIDO_ATUAL:END -->

### Processo atual
<!-- PG_AUTO:PROCESSO_ATUAL:START -->
Processo atual: [PREENCHER]
Utilizadores / papeis:
- [PREENCHER]
Excecoes conhecidas:
- [PREENCHER]
Aprovacoes:
- [PREENCHER]
Documentos envolvidos:
- [PREENCHER]
Integracoes:
- [PREENCHER]
Reporting esperado:
- [PREENCHER]
O que ja foi tentado ou validado no standard atual:
- [PREENCHER]
Porque foi considerado insuficiente:
- [PREENCHER]
<!-- PG_AUTO:PROCESSO_ATUAL:END -->

### Problema / dor
<!-- PG_AUTO:PROBLEMA_DOR:START -->
Problema / necessidade observada: [PREENCHER]
<!-- PG_AUTO:PROBLEMA_DOR:END -->

### Impacto no negócio
<!-- PG_AUTO:IMPACTO_NEGOCIO:START -->
Impacto de negocio: [PREENCHER]
<!-- PG_AUTO:IMPACTO_NEGOCIO:END -->

## Artefactos Fatuais Publicados

> Esta camada le snapshots oficiais publicados em `.pg/`.
> Os snapshots continuam a ser a source of truth factual primária; este ficheiro funciona apenas como consolidação derivada de leitura.

### Âmbito factual publicado
<!-- PG_AUTO:SCOPE_ITEMS:START -->
Resumo do scope sincronizado:
- Itens ativos: 150
- Itens validados: 0
- Itens propostos: 150
- Itens diferidos: 0
- Ultima alteracao de task: 2026-05-26 17:21:01

Itens em ambito:
1. Acesso a CCT a Vendedores
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Podiam colocar acesso
Criterios de aceitacao:
- aos vendedores da conta corrente dos clientes sff
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1261&model=project.task

2. Acompanhamento Importação Lista de Preços
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Acompanhamento Importação Lista de Preços
Criterios de aceitacao:
- O ambito aprovado deve refletir acompanhamento Importação Lista de Preços.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2056&model=project.task

3. Actualizar modulo PT-Exo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Actualizar modulo PT-Exo
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2146&model=project.task

4. Ajustes Website
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Alterar posição em mobile do logotipo com o menu burguer. ✔
Criterios de aceitacao:
- Ver possibilidade de por submenus de mobile como o de Laskasas.
- ticket support não cai na caixa ✔
- pagina termos e condições não aparece ✔
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=969&model=project.task

5. API Kave
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: No seguimento da conversa da minha colega Ana com a Aldana gostaríamos de proceder ao desenvolvimento da "ponte informática" entre a Sofmovel e a Kave Home para facilitação dos processos de pedidos no portal do B2B e...
Criterios de aceitacao:
- Deixo em CC o contacto dos nossos parceiros informáticos para que consigam estabelecer esta ponte.
- Obrigado, caso necessitem de alguma informação adicional, fico ao dispor.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=3583&model=project.task

6. Aplicação de Certicação de Documentos no Odoo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Aplicação de Certicação de Documentos no Odoo
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=948&model=project.task

7. Armazéns
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Fizemos uma venda a partir do Odoo. A encomenda depois devia passar para a
Criterios de aceitacao:
- compra mas alguns dos artigos não passaram. Ficaram reservados no stock da Kave
- e não pode. Apenas pode contabilizar o nosso real Freamunde e lojas.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=860&model=project.task

8. ARMZ e STK por armazem
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós reparamos quando entramos nos artigos e
Criterios de aceitacao:
- vamos em previstos (por causa do stock) não aparece nenhuma unidade em todos os
- Como nós passamos os recebimentos da empresa antiga para a empresa
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1029&model=project.task

9. Artigos Backoffice
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós estamos com uma duvida e precisamos de ajuda, se selecionarmos
Criterios de aceitacao:
- um artigo no BackOffice vai ter um campo nas vendas que se chama Aviso ao
- vender este Artigo, este campo serve para que apareça uma mensagem caso o
- Poderiam nos explicar como funciona este campo.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1178&model=project.task

10. Atualização de artigos e vendas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Têm que dar formação aos funcionários sobre esta questão!.
Criterios de aceitacao:
- Após por a lista de preços nos artigos da Sofmovel tem como
- atualizar a lista de preços que tem associado ás vendas? Porque se um vendedor
- fizer um orçamento a um cliente e nós atualizarmos a lista o vendedor vai estar
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2177&model=project.task

11. Atualização excel artigos Sofmovel
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Apoio na atualização de Excel com Preços Softmovel
Criterios de aceitacao:
- O ambito aprovado deve refletir atualização excel artigos Sofmovel.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2176&model=project.task

12. Atualizar Exo software
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Atualizar Exo software
Criterios de aceitacao:
- O ambito aprovado deve refletir atualizar Exo software.
Utilizadores atribuidos:
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2328&model=project.task

13. Bancos e Reconciliações
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Apoio na criação de Banco e reconciliação de Pagamentos
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1195&model=project.task

14. Bloquear Vendedores de mudar o vendedor
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Conseguem bloquear os funcionários das nossas lojas de conseguir mudar o funcionário de quem fez a venda.
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1172&model=project.task

15. Bloqueios a vendedoras a debloquear enc
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Bloqueios a vendedoras a debloquear enc
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1262&model=project.task

16. Certificação Odoo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=956&model=project.task

17. Chave API da Kave
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Chave API da Kave
Criterios de aceitacao:
- Estou a reencaminhar a resposta da kave para começar-mos a utilizar a chave api. De:* Aldana Signetti <asignetti@kavehome.com>
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=3893&model=project.task

18. Colocar impostos nos produtos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Pediu para sermos nós a colocar o iva nos produtos todos.
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1890&model=project.task

19. Colocar só um código promocional por cliente
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Fizeram uma parceria e querem que os clientes apliquem só um código de desconto.
Criterios de aceitacao:
- Aplicam o da newsletter ou o da parceria.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2185&model=project.task

20. Comissoes de vendedores Calculo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Claudia ligou a questionar como vai funcionar Calculo de comissões de vendedores
Criterios de aceitacao:
- O ambito aprovado deve refletir comissoes de vendedores Calculo.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1064&model=project.task

21. Compra falta descrição
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: No documento de solicitação de compra não está a aparecer a
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1238&model=project.task

22. Compras Erro e não tem Arm de Freamunde
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Estamos a tentar confirmar uma compra mas está a dar um erro e não
Criterios de aceitacao:
- E também não aparece para receber os produtos no armazém de
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1196&model=project.task

23. Compras nao estão a ser geradas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Compras nao estão a ser geradas
Criterios de aceitacao:
- O ambito aprovado deve refletir compras nao estão a ser geradas.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1832&model=project.task

24. Configuração Guias Transporte
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1059&model=project.task

25. Configurar notificações em tempo real
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Configurar notificações em tempo real
Criterios de aceitacao:
- O ambito aprovado deve refletir configurar notificações em tempo real.
Utilizadores atribuidos:
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1153&model=project.task

26. Contas Correntes e Notas de Crédito
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Contas Correntes e Notas de Crédito
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1053&model=project.task

27. Criação de novo email carolinaresende@sofmovel.pt
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Criação de novo email carolinaresende@sofmovel.pt
Criterios de aceitacao:
- O ambito aprovado deve refletir criação de novo email carolinaresende@sofmovel.pt.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1030&model=project.task

28. Descontos nos Produtos. Implementação de Reconciliação Aumática de Faturas/Recibos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: ligar com Claudia Descontos nos Produtos. Implementação de Reconciliação Aumática de Faturas/Recibos
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1136&model=project.task

29. Deteção de erro POS
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Deteção de erro POS
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=873&model=project.task

30. Dias de entrega ao cliente no website
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Dias de entrega ao cliente no website
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2121&model=project.task

31. dúvida produtos categorias
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: dúvida produtos categorias
Criterios de aceitacao:
- Como nós conseguimos organizar os produtos nas categorias?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=874&model=project.task

32. Dúvidas com Artigos e Variantes
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Dúvidas com Artigos e Variantes
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1171&model=project.task

33. Eliminar as transações no POS e colocar novas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Eliminar as transações no POS e colocar novas
Criterios de aceitacao:
- O ambito aprovado deve refletir eliminar as transações no POS e colocar novas.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2081&model=project.task

34. Eliminar recebimentos a mais
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Eliminar recebimentos a mais
Criterios de aceitacao:
- O ambito aprovado deve refletir eliminar recebimentos a mais.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=812&model=project.task

35. Email de saída de Email Marketing
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Espero que este e-mail os encontre bem!
Criterios de aceitacao:
- Hoje enviei o e-mail marketing de inicio dos saldos e, quando recebi no meu e-mail pessoal, o nome aparecia "odooBot" em vez de "sofmovel" Conseguem-me ajudar, para substituir?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2271&model=project.task

36. Email Elton não funciona
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: O email do elton não está a funcionar, ele está a tentar enviar
Criterios de aceitacao:
- uma fatura a um cliente, mas não consegue.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1089&model=project.task

37. Empresa antiga não aparece
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: A empresa antiga já não está a aparecer e nós precisamos disso
Criterios de aceitacao:
- para poder gerir as nossas lojas, peço que resolvam este erro o mais rápido
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1252&model=project.task

38. encomenda / orç imprime em branco
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ao imprimir a encomenda/orçamento aparece sempre uma página em
Criterios de aceitacao:
- branco, dava para por só as folhas que tem informação dos artigos?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1291&model=project.task

39. Encomenda FORN desconfigurada
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: A nota de encomenda para fornecedores está desconfigurada e falta
Criterios de aceitacao:
- a informação de onde a mercadoria deve ser entrega a um dos nossos armazéns.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1048&model=project.task

40. encomendas on line
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Após ser envia um email á cliente a confirmar a sua encomenda
Criterios de aceitacao:
- notamos algumas palavras e uma imagens desconfigurada que gostávamos que
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1000&model=project.task

41. Entrada de Material ERRO
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Entrou Material que querem etiquetar porém esta a dar erro
Criterios de aceitacao:
- Ligaram Arm Seixal erro ao dar entrada 212 de material Urgente
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2001&model=project.task

42. Enviar emails de apoioaocliente@sofmovel.pt
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Enviar emails de apoioaocliente@sofmovel.pt
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=961&model=project.task

43. Erro 503
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2042&model=project.task

44. Erro artigo com desconto
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Teve uma cliente que foi á nossa loja, e quis fazer uma compra
Criterios de aceitacao:
- online por causa do klarma, mas nós ao ter acesso á conta da cliente para
- efetuar a compra notámos que os artigos todos do nosso website estavam com 20%
- Este erro precisa de ser resolvido hoje.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1170&model=project.task

45. Erro Encomenda on line valor de entrega diferentes
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro nos valores de Entrega ambos errados numa a 0 e outro com valor mas Errado Pedido por Andreia via
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1022&model=project.task

46. erro enviar email
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: A andreia está a tentar enviar um email pelo odoo para um cliente
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1214&model=project.task

47. erro envio de emails
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ainda está a falhar os emails de boas vindas aos clientes que
Criterios de aceitacao:
- criam a conta no nosso website, e também a newsletter não está a enviar nenhum
- email, eu fiz o teste de subscrever á uma semana e até agora não recebi nada.
- E também é preciso resolver o problema dos emails do nosso
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1271&model=project.task

48. Erro envio de emails
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro envio de emails
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1822&model=project.task

49. Erro envio de emails novidades@sofmovel.pt
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro envio de emails novidades@sofmovel.pt
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1821&model=project.task

50. Erro Finalizar Compra
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Estamos a tentar finalizar uma compra mas só que está a dar este
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1140&model=project.task

51. Erro gerar as compras com serviços nas linhas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro gerar as compras com serviços nas linhas
Criterios de aceitacao:
- O ambito aprovado deve refletir erro gerar as compras com serviços nas linhas.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2106&model=project.task

52. Erro impressão Braga
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro impressão Braga
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2166&model=project.task

53. Erro na Impressão de etiquetas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro na Impressão de etiquetas
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Eduardo Pacheco
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2067&model=project.task

54. Erro valores Faturas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro valores Faturas
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1859&model=project.task

55. Erros
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erro ao enviar emails quando fazemos um orçamento ✔ Entrega quando fazemos orçamento ✔
Criterios de aceitacao:
- A equipa de vendas não está configurada só está a loja
- Não conseguem criar contactos os vendedores ✔
- Ver se ponto de venda sai na impressora da loja
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=996&model=project.task

56. Erros nas Permissões de Funcionários
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Erros nas Permissões de Funcionários
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=992&model=project.task

57. Etiqueta de produtos ZPL
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Etiqueta de produtos ZPL
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1049&model=project.task

58. etiquetas Impressoras
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Poderiam resolver a parte
Criterios de aceitacao:
- das impressoras e etiquetas, porque essa parte é muito importante para as lojas
- pois sem está configurado os nossos funcionários das lojas não conseguem
Utilizadores atribuidos:
- Hugo Ferreira
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1115&model=project.task

59. excel Kave
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Seria possível enviar um email ou uma notificação quando corresse
Criterios de aceitacao:
- o Excel da kave para ver se correu todo bem ou não, como o João fez ao correr
- as pastas das imagens, eu queria isso também para o Excel, isso é
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=984&model=project.task

60. excel produtos sofmovel
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Têm possibilidade de quando extraímos o Excel para por preços dos
Criterios de aceitacao:
- produtos Sofmovel, inserir o preço só no Excel que extraímos na primeira vez
- porque neste momento temos de extrair dois excel's para inserir os preços
- e esta solução está a ser inviável para nós, tem alguma forma de por os preços
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1973&model=project.task

61. FA corrigir report impressão
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Como podem ver no lado
Criterios de aceitacao:
- O ambito aprovado deve refletir fA corrigir report impressão.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1283&model=project.task

62. Fatura ainda com Palavras em Inglês
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nas faturas ainda tem palavras em inglês, e também se fosse
Criterios de aceitacao:
- possivél dava para tirar o que diz due data e também carga e descargas.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1113&model=project.task

63. fatura e vias
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ao confirmar a encomenda ao cliente está a ser enviado dois
Criterios de aceitacao:
- documentos que são: a fatura e a fatura multi-via. Sabem porque que está a ser
- enviado a fatura multi-via para os clientes?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1175&model=project.task

64. Faturas Simplificadas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1083&model=project.task

65. Filtros no site mandam para página login
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Filtros no site mandam para página login
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1210&model=project.task

66. Fotos formularios
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Tenho recibo muitas
Criterios de aceitacao:
- queixas de clientes que não consegue colocar as fotos no formulário porque
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=908&model=project.task

67. Funcionários permissões
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Como Nós sabemos quais são os funcionários que estão bloqueados de
Criterios de aceitacao:
- Como é que nós sabemos que o "código" se refere ao
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1124&model=project.task

68. GT Erro
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós estivemos a resolver um problema que não dava para tirar uma
Criterios de aceitacao:
- guia de transporte com o João, mas esse erro ainda está a acontecer pois na
- série documental não está a preencher automático com waybill.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1137&model=project.task

69. GT não estão a confirmar
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: GT não estão a confirmar
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2098&model=project.task

70. Guia de Transporte Alterações
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Tem algumas alterações na guia de transporte que gostaríamos que
Criterios de aceitacao:
- Em vez de ter a data de
- expedição trocar para a Data/Hora de carga
- Data/Hora de descarga e a matrícula
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1194&model=project.task

71. IBANs alteração
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós precisávamos que fizessem uma alteração em todos os
Criterios de aceitacao:
- documentos, pois na informação do cliente está a aparecer o número antes do
- código postal (neste caso é o 11) mas estes números não fazem referência a nada
- das informações dos clientes. E já temos recebido anotações dos clientes em
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1138&model=project.task

72. Implementação formulário em artigos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós queremos se possível, implementar um formulário em todos os artigos da Kave e os nossos, o formulário pode ser igual á imagem (site
Criterios de aceitacao:
- Este formulário vai servir para que se os clientes quiserem por as medidas que preferem que tenham os artigos para nós fazermos.
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1174&model=project.task

73. Importar Clientes
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=421&model=project.task

74. Importar Fornecedores
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=422&model=project.task

75. Impressão reduzir opções
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Seria possível numa ordem de venda ao imprimir o documento aparece
Criterios de aceitacao:
- várias opções, mas nós só precisamos da Fatura Pró-Forma e Orçamento /
- Encomenda, tudo o resto se possível podem tirar para não causar confusão aos
- que estão a trabalhar nas nossas lojas.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1090&model=project.task

76. Impressora Zebra em Rede Braga
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Os nossos funcionários da loja de braga informaram-nos que é preciso cabo de rede
Criterios de aceitacao:
- nossos funcionários da loja de braga informaram-nos que é preciso cabo de rede
- para ligar a impressora para poder imprimir em todos os computadores, mas a
- impressora não pode ser ligada por USB?
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1269&model=project.task

77. Impressoras não estão a funcionar
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Impressoras não estão a funcionar
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
- Mariana Oliveira
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1918&model=project.task

78. informação encomendas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ao visualizar as encomendas e orçamentos as informações não
Criterios de aceitacao:
- aparecem todas, podem por a verse a informação dos artigos?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1161&model=project.task

79. informação STK e prazo entrega
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Vocês conseguem por no nosso website o prazo de entrega a
Criterios de aceitacao:
- coincidir com o stock, porque neste momento só diz de 3 a 4 semanas
- independente do stock que tenha, e nós queríamos que consoante o stock tenha
- apareça datas diferentes no nosso website para os clientes tivessem a
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=836&model=project.task

80. Instalar google_auth no python
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ao instalar app social_marketing, aparece esse erro
Criterios de aceitacao:
- O ambito aprovado deve refletir instalar google_auth no python.
Utilizadores atribuidos:
- Mariana Oliveira
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1999&model=project.task

81. Instalar Modulo de certificação
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Instalar Modulo de certificação
Criterios de aceitacao:
- O ambito aprovado deve refletir instalar Modulo de certificação.
Utilizadores atribuidos:
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=937&model=project.task

82. Integração catálogo de produtos META + Instalação de Google Tag Manager no Website
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Venho por este meio solicitar um orçamento para integração do catálogo de Produtos no Meta Business Suite e instalação da etiqueta do Google (código) para poder rastrear o comportamento do cliente no website, conversõ...
Criterios de aceitacao:
- Este assunto já foi falado com o Cláudio, e foi pedido para ser reencaminhado para o
- Aguardo uma resposta, o mais breve possível!
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=3584&model=project.task

83. Integração MBWay
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Integração MBWay
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2088&model=project.task

84. Invalid Operation para artigo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Invalid Operation para artigo
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1109&model=project.task

85. Inventário faltam imagens
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Estamos a fazer o inventário da loja de braga e precisamos de
Criterios de aceitacao:
- imprimir, mas ao imprimir não está a sair com as fotos do produto, mas quando
- fizemos o inventário de lisboa ao imprimir saia com as imagens.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1240&model=project.task

86. Inventario Ficheiro
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ligar com Gabriel
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=825&model=project.task

87. KAVE entregas em STK
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: As entregas continuam a aparecer no inventário. Mas a kave só
Criterios de aceitacao:
- existe para saber o stock do armazém deles. Não rececionamos nem entregamos
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1215&model=project.task

88. Layout Listagem
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=849&model=project.task

89. Ligação a Bancos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Antigamente eu ia ao
Criterios de aceitacao:
- banco e conectava os pagamentos. Depois o João perguntou-me se não queria isso
- automático e eu disse que sim. Mas agora reparei que ele não fax a conecção com
- o extrato do banco. Podem retirar para voltar a ser manual?
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1997&model=project.task

90. Ligar com a Andreia para redes sociais
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ligar com a Andreia para redes sociais
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=739&model=project.task

91. Ligar com Andreia para Transferências Internas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: que mudem as guias de transporte sff
Criterios de aceitacao:
- Preciso que conste sempre a morada fiscal do cliente, o local de carga, local
- de descarga e o contacto do cliente.
- O local de carga para saber se está a sair de braga, seixal ou freamunde. Local
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1245&model=project.task

92. Lista de Preço de Artigos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ligar com Claudia
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=909&model=project.task

93. Loja Seixal erro Criar FA
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Loja Seixal erro Criar FA
Criterios de aceitacao:
- O ambito aprovado deve refletir loja Seixal erro Criar FA.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1100&model=project.task

94. M2 no website, não funcionam
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: M2 no website, não funcionam
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1971&model=project.task

95. Migrar Odoo para odoo.sh
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Migrar Odoo para odoo.sh
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2369&model=project.task

96. Motivos de Isenção Imposto
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Onde pode selecionar motivos de isenção imposto
Criterios de aceitacao:
- Tipo para qdo é mercada Espanhol entre outros
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1055&model=project.task

97. Newsletter instântanea
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Newsletter instântanea
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=814&model=project.task

98. newsletter nao funciona
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: A newsletter ainda não está a funcionar, fizemos hoje um teste
Criterios de aceitacao:
- mas até agora não recebemos nenhum email com a newsletter.
- Precisamos que esta parte fique a funcionar para os clientes
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2010&model=project.task

99. NIF Obrigatório para utilizadores sem conta
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: NIF Obrigatório para utilizadores sem conta
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1256&model=project.task

100. Notas Notificação
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ver possibilidade de implementação de notificações em tempo real sem necessidade de atualizar página web.
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1092&model=project.task

101. Novos produtos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós estamos a acrescentar produtos nas coleções, mas está a ter um
Criterios de aceitacao:
- erro que ao acrescentar aparece os produtos sem a imagem.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1176&model=project.task

102. Odoo não abre erro 503
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Odoo não abre erro 503
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1994&model=project.task

103. OR A /00057 erro
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: OR A /00057 erro
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1122&model=project.task

104. ORÇ e NE Circuito
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: ORÇ e NE Circuito Boa Tarde
Criterios de aceitacao:
- Está a ocorrer um erro nas vendas, quando passamos de um orçamento
- para uma encomenda o programa está a "duplicar" o orçamento, em vez
- de nesse orçamento passar para ordem de venda.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1072&model=project.task

105. Orçamento Integração Facebook Business Suite
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: 15 dias, primeira intervenção portanto requer pesquisa, testes intensivos e primeiro migração para SH
Criterios de aceitacao:
- O ambito aprovado deve refletir orçamento Integração Facebook Business Suite.
Utilizadores atribuidos:
- Cláudio Pereira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2939&model=project.task

106. Orçamento para SH
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Falar com Marcelo Odoo
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-26 17:21:01
Origem: https://parametroglobal.odoo.com/web#id=5553&model=project.task

107. Orçamento public user
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Orçamento public user
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=813&model=project.task

108. Parametrização de certificação Odoo
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Parametrização de certificação Odoo
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=951&model=project.task

109. pedido de cotação desconfigurado
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ao enviar um pedido de cotação para um fornecedor, o pdf está
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1116&model=project.task

110. Permissões
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Temos um problema nos acessos dos vendedores no que diz respeito
Criterios de aceitacao:
- aos recursos humanos. Não queremos que eles tenham acesso à parte dos
- funcionários, pois estão a conseguir visualizar a informação privada de cada
- um, nomeadamente a parte dos recursos humanos.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=835&model=project.task

111. Pesquisa Preço da Encomenda
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Pesquisa Preço da Encomenda
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1106&model=project.task

112. Pixel Meta
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Leandro Alves
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=811&model=project.task

113. plataforma pagamento
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Esta empresa é do banco
Criterios de aceitacao:
- do Millennium. É para eles verem connosco como podem colocar a plataforma de
- pagamento para a nossa página online.
- None Image None Image None Image None Image
Utilizadores atribuidos:
- Cláudio Pereira
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2220&model=project.task

114. Pontos de Venda users alteração
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: No ponto de venda tem funcionários que criamos que alterassem que
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1032&model=project.task

115. Pos Braga e Seixal erro impressora
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Na nossa loja braga fizeram agora uma venda no ponto de venda, e
Criterios de aceitacao:
- eles tiraram uma fs. Saiu na impressora normal em A4 e saio só a original.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1078&model=project.task

116. Preços de artigos com Variantes erro
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Na conta da nossa funcionária, o produto com variantes tem sempre
Criterios de aceitacao:
- o mesmo preço, mas alguns produtos das variantes tem preços diferentes mas na
- conta dela aparece-lhe sempre um preço.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1239&model=project.task

117. Preços não atualizam
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Após atualização de preços os mesmos não atualizam
Criterios de aceitacao:
- O ambito aprovado deve refletir preços não atualizam.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1069&model=project.task

118. Preços Produtos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós estamos a fazer os preços para os produtos da Sofmovel
Criterios de aceitacao:
- extraímos o Excel para inserir os preços e depois inserimos no site, mas quando
- extraímos de novo o Excel os preços ficam a zeros em vez de ter os preços que
- Como podemos fazer para que ao extrair venha com os preços que já
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1114&model=project.task

119. Problema tirar Guia de Transporte
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Problema tirar Guia de Transporte
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1254&model=project.task

120. problema venda on line
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: A cliente enviou um
Criterios de aceitacao:
- print de como não aparece a venda online. Fui aos contactos e tem duas contas
- criadas com o mesmo e-mail, mas o Odoo não devia deixar se já está criado.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1247&model=project.task

121. Produtos Com 100% desconto site
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Os produtos que estão no nosso website estão na maioria com 100%
Criterios de aceitacao:
- de desconto e também não dá para comprar, precisamos que resolvam este problema
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2015&model=project.task

122. Produtos com Ref. Int. repetida
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Produtos com Ref. Int. repetida
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2277&model=project.task

123. Produtos Kave com desconto
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Produtos Kave com desconto
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1071&model=project.task

124. Produtos Kave fora de linha
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós temos alguns produtos nas lojas que a Kave já não faz, esses
Criterios de aceitacao:
- produtos não tão visíveis no nosso website, mas ao pesquisar pela referência no
- google aparece o nosso site com esse produto mas ao selecionar o site dá um
- Podem resolver este erro pois ao pesquisar a referencia no google
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1160&model=project.task

125. Produtos Unicos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Estamos a inserir produtos únicos para que possam ser vendidos
Criterios de aceitacao:
- mas ao criar se retirarmos o visto do "Pode ser Comprado" depois do
- artigo ser vendido ele já não dá para vender mais?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1158&model=project.task

126. Receber Email de rodar as pastas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Receber Email de rodar as pastas
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=810&model=project.task

127. Referencia dos pedidos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: As referências dos pedidos estão diferentes, ou seja, nós temos
Criterios de aceitacao:
- uma referência para a venda, temos outra referência diferente para a
- compra e também temos outra diferente para as entregas.
- Seria possível por a referencia toda igual á das vendas?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1091&model=project.task

128. Reformulação de processo de compras e armazéns
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Reverter o processo de verificação de stocks
Criterios de aceitacao:
- Vendas gera SEMPRE compras (independentemente do Stock). Mas têm de ser geradas através de botão em vez de automático.
- Conta Gabriel mostra preços sem IVA
- Pesquisa de Resultados mostra sempre desconto mesmo quando não tem
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2057&model=project.task

129. Retirar texto do recibo POS
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Retirar texto do recibo POS
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2272&model=project.task

130. Reunião Interna para estudar novos pedidos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Reunião Interna para estudar novos pedidos
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2066&model=project.task

131. Reunião Ponto Situação
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=934&model=project.task

132. SAFT gerado com Nome Errado
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: O nome do ficheiro saft está a ser gerado com o nome errado, envio
Criterios de aceitacao:
- um anexo com o nome que pretendemos que fique o nome do ficheiro.
- A nossa contabilidade também referiu que as faturas não estão a
- ser comunicadas automaticamente, também foi necessário comunicar o ficheiro
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1211&model=project.task

133. Serviços de Montagem relatório de vendas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Serviços de Montagem relatório de vendas
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1117&model=project.task

134. Site erro variantes
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Está a dar um erro no nosso website, quando selecionamos alguma
Criterios de aceitacao:
- variante do artigo está a dar-nos um erro. Esse erro só dá nos nossos produtos
- As variantes estavam a funcionar corretamente no nosso website
- mas a partir de ontem (quando reparamos no erro) não está a funcionar
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2486&model=project.task

135. SofMovel - Integração de emails com Odoo.
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: SofMovel - Integração de emails com Odoo.
Criterios de aceitacao:
- O ambito aprovado deve refletir sofMovel - Integração de emails com Odoo.
Utilizadores atribuidos:
- Hugo Ferreira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=899&model=project.task

136. STK ARMAZENS
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Nós reparamos quando entramos nos artigos e vamos em previstos
Criterios de aceitacao:
- (por causa do stock) não aparece nenhuma unidade em todos os armazéns que nós
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=988&model=project.task

137. Suporte
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: [PONTO POR VALIDAR]
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=819&model=project.task

138. Template etiquetas - Mariana
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Template etiquetas - Mariana
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Mariana Oliveira
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=658&model=project.task

139. Todas as vendas têm gerar compras
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Todas as vendas têm gerar compras
Criterios de aceitacao:
- O ambito aprovado deve refletir todas as vendas têm gerar compras.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2043&model=project.task

140. transferencia de armz
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Estamos com uma dúvida que precisamos de esclarecer, como é que
Criterios de aceitacao:
- nós fazemos uma transferência de armazéns e como requisitámos produtos?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1218&model=project.task

141. Users Lojas a criar artigos
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Como podemos fazer para com que os funcionários das nossas lojas
Criterios de aceitacao:
- não tenham permissão para criar artigos?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1099&model=project.task

142. venda Perdida
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Um funcionário da loja de lisboa
Criterios de aceitacao:
- fez uma venda de 2000€, mas com a restauração que fizeram por causa dos preços
- estar todos a 100% desconto ele perdeu a venda. O nosso funcionário não tem
- agora nenhum dado do cliente, precisamos que resolvam este problema o mias
Utilizadores atribuidos:
- João Barros
- Mariana Oliveira
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2108&model=project.task

143. Vendedores bloqueios
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Tem alguns funcionários das nossas lojas que estão a conseguir
Criterios de aceitacao:
- desbloquear e cancelar notas de encomenda, e nós não queremos que eles mexam
- podem bloquear los para eles não conseguirem mexer. Alguns funcionários das
- lojas já estão bloqueados outras coseguem mexer.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1264&model=project.task

144. vendedores Vendas
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: O extrato de vendas dos vendedores consta apenas as notas de
Criterios de aceitacao:
- encomendas que estão totalmente faturadas, e nós precisamos que o extrato
- contenha as faturas juntamente com as notas de crédito.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1179&model=project.task

145. Ver situação do Servidor
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ver situação do Servidor
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=815&model=project.task

146. Ver situação do Servidor
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Ver situação do Servidor
Criterios de aceitacao:
- Sem criterios de aceitacao factuais publicados.
Utilizadores atribuidos:
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=816&model=project.task

147. Verificar o servidor
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Servidor instável, não guarda coisas e o Odoo está lento.
Criterios de aceitacao:
- O ambito aprovado deve refletir verificar o servidor.
Utilizadores atribuidos:
- Mariana Oliveira
- Vitor Costa
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2204&model=project.task

148. Vias GT
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Conseguia-nos tirar uma dúvida que é, quando nós tiramos uma guia
Criterios de aceitacao:
- de transporte o odoo também tira o duplicado e triplicado dessa guia ?
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1033&model=project.task

149. web site vai abaixo constantemente
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: O nosso website já foi abaixo 2 vezes.
Criterios de aceitacao:
- Vocês também podiam enviar um contacto de emergência, para caso
- aconteça estas situações poder-se resolver logo.
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=1248&model=project.task

150. Website/Problemas STK
Track: approved_scope
Estado: proposed
Tipo: requirement
Sequencia: 10
Resumo: Está a haver um erro no stock ou no website, em alguns artigos da
Criterios de aceitacao:
- kave o produto está com quantidades em mão mas só que se formos ao nosso
- website ele diz que não tem stock.
- Os produtos da kave que estão a ser criados agora por defeito
Utilizadores atribuidos:
- João Barros
Atualizado em: 2026-05-15 16:06:41
Origem: https://parametroglobal.odoo.com/web#id=2548&model=project.task
<!-- PG_AUTO:SCOPE_ITEMS:END -->

### Estado operacional factual publicado
<!-- PG_AUTO:STATUS_SYNC:START -->
Schema do snapshot: [PONTO POR VALIDAR]
Última atualização recebida do Odoo: [NAO SINCRONIZADA]
Fase reportada no último sync: [PONTO POR VALIDAR]
Estado geral reportado: [PONTO POR VALIDAR]
Sistema de origem: [PONTO POR VALIDAR]
Modelo Odoo de origem: [PONTO POR VALIDAR]
Record Odoo de origem: [PONTO POR VALIDAR]
URL do record Odoo: [PONTO POR VALIDAR]
Publicado no repositório em: [PONTO POR VALIDAR]
Publicado por: [PONTO POR VALIDAR]
Trigger de sync: [PONTO POR VALIDAR]
Branch de sync: [PONTO POR VALIDAR]
Milestones:
- [PREENCHER]
Bloqueios:
- [PREENCHER]
Riscos operacionais:
- [PREENCHER]
Próximos passos operacionais:
- [PREENCHER]
Decisões pendentes:
- [PREENCHER]
Go-live alvo: [PONTO POR VALIDAR]
Owner atual: [PONTO POR VALIDAR]
Fonte Odoo / referência: [PONTO POR VALIDAR]
<!-- PG_AUTO:STATUS_SYNC:END -->

### Decisões factuais publicadas

Derivado de `.pg/PG_DECISIONS_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

### Riscos factuais publicados

Derivado de `.pg/PG_RISKS_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

### Entregáveis, requisitos, plano e budget publicados

Os snapshots `.pg/PG_DELIVERIES_SYNC.json`, `.pg/PG_REQUIREMENTS_SYNC.json`,
`.pg/PG_PROJECT_PLAN_SYNC.json` e `.pg/PG_BUDGET_SYNC.json` continuam a ser os
artefactos factuais primários. A sua integração textual neste contexto deve ser
sempre derivada, curta e explicitamente não canónica.

## Consolidação e Gaps

### Gaps factuais ainda por consolidar

- [PREENCHER]

### Dependências de refresh e validação

- [PREENCHER]

## Curadoria Assistida e Itens Por Promover

> Drafts, chatter e backlog operacional vivem aqui apenas como apoio a curadoria.
> Nada desta secção deve competir com os campos oficiais ou com os snapshots publicados.

### Drafts e sinais em revisão

- [PREENCHER]

### Itens por promover a oficial

- [PREENCHER]

## Análise Consultiva e Decisão

### Análise de solução

### 1. Standard já existente no projeto
Estado: [NAO ANALISADO]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 2. Standard adicional Odoo
Estado: [NAO ANALISADO]
Módulos / funcionalidades a avaliar:
- [PREENCHER]
Cobertura do requisito: [PONTO POR VALIDAR]
Implicações de adoção:
- [PREENCHER]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 3. Odoo Studio
Estado: [NAO ANALISADO]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 4. Custom
Estado: [NAO ANALISADO]
Escopo mínimo se for necessário:
- [PREENCHER]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### Decisão atual
Classificação final: [PONTO POR VALIDAR]
Decisão: [PREENCHER]
Justificação: [PREENCHER]

### Riscos
- [PREENCHER]

### Próximos passos
- [PREENCHER]

## Referências e Histórico

### Referências consultadas

#### Documentação Odoo
- [PREENCHER]

#### Core Odoo
- [PREENCHER]

#### Código do projeto
- [PREENCHER]

### Histórico de marcos de decisão

#### YYYY-MM-DD - [Titulo curto]
Contexto:
- [PREENCHER]

Decisão:
- [PREENCHER]

Riscos / pendências:
- [PREENCHER]

Referências:
- [PREENCHER]
