# PG_CONSULTING_DECISION_PATTERNS

Este ficheiro funciona como biblioteca leve de padrões consultivos recorrentes em projetos Odoo.
Serve apenas como apoio ao raciocínio consultivo. Nunca substitui a validação do projeto atual contra `PG_CONTEXT.md`, código do projeto, `vendor/odoo_src` e documentação oficial da versão ativa.

## PADRAO 001 - Aprovações multi-nível
Tipo de pedido:
- aprovação em vários níveis por valor, equipa, departamento ou tipo de documento

Opções a avaliar primeiro:
- configurações standard do módulo atual
- módulos standard adicionais de approvals, purchase, expenses ou account
- regras de segurança e atividades standard

Cobertura standard tipica:
- parcial

Quando Studio pode chegar:
- quando a regra e simples, com poucos estados e poucas exceções

Quando custom pode ser necessário:
- quando ha matriz complexa de aprovadores, escalonamento automático ou lógica transversal a vários módulos

Riscos tipicos:
- fluxo demasiado complexo
- bypass operacional fora do sistema
- dependência de grupos e regras mal definidas

Nota consultiva:
- muitos pedidos de "workflow custom" são na verdade falta de configuração, módulo adicional ou clarificação de autoridade de aprovação

## PADRAO 002 - Campos adicionais e regras simples
Tipo de pedido:
- campos extra, obrigatoriedade condicional, pequenas validações e automatismos basicos

Opções a avaliar primeiro:
- campos standard já existentes
- Studio
- automações simples ou configuração nativa

Cobertura standard tipica:
- parcial com forte potencial via Studio

Quando Studio pode chegar:
- quando o requisito e local ao modelo, sem lógica transversal pesada

Quando custom pode ser necessário:
- quando a regra depende de múltiplos modelos, performance critica ou comportamento técnico não suportado em Studio

Riscos tipicos:
- proliferação de campos sem dono funcional
- regras isoladas que degradam UX

Nota consultiva:
- confirmar sempre se o pedido e necessidade real ou apenas preferência de layout

## PADRAO 003 - Contratos, subscrições e recorrência
Tipo de pedido:
- faturação recorrente, renovações, contratos de serviço, SLAs e recorrência comercial

Opções a avaliar primeiro:
- módulos standard de subscriptions, sales, helpdesk ou field service
- configuração de produtos recorrentes

Cobertura standard tipica:
- parcial a total, dependendo da edição e do processo

Quando Studio pode chegar:
- quando só faltam campos, vistas ou pequenas regras de suporte

Quando custom pode ser necessário:
- quando ha lógica contratual muito específica, calculo avancado, integração externa ou compliance setorial

Riscos tipicos:
- misturar contrato juridico com objeto operacional no Odoo
- recorrência mal modelada a partir de vendas avulsas

Nota consultiva:
- distinguir sempre entre contrato comercial, renovação operacional e mecanismo de faturação

## PADRAO 004 - Gestão documental e assinatura
Tipo de pedido:
- anexos, aprovações documentais, assinatura eletronica, controlo de versões e trilho de auditoria

Opções a avaliar primeiro:
- módulos standard de documents, sign, knowledge e attachments do módulo atual
- permissoes e estrutura documental standard

Cobertura standard tipica:
- parcial a total

Quando Studio pode chegar:
- quando faltam apenas campos, tags, classificação ou pequenas ações

Quando custom pode ser necessário:
- quando ha requisitos legais, integrações com DMS externo ou governança documental muito específica

Riscos tipicos:
- tratar problema operacional como mera organização de ficheiros
- excesso de anexos sem taxonomia

Nota consultiva:
- confirmar se a dor e assinatura, arquivo, pesquisa ou controlo de processo

## PADRAO 005 - CRM para projeto para faturação
Tipo de pedido:
- continuidade do processo desde lead ou oportunidade até entrega e faturação

Opções a avaliar primeiro:
- integração standard entre crm, sale, project, helpdesk, timesheets e accounting
- configuração de produtos e politicas de faturação

Cobertura standard tipica:
- parcial a total

Quando Studio pode chegar:
- quando faltam apenas checkpoints visuais ou pequenos campos de passagem

Quando custom pode ser necessário:
- quando ha regras de handoff muito específicas, calculo contratual especial ou orquestração entre várias entidades

Riscos tipicos:
- tentar resolver desalinhamento organizacional com automação excessiva
- fases comerciais e operacionais mal definidas

Nota consultiva:
- muitos gaps aparentes são configuração insuficiente de produtos, projetos ou politica de faturação

## PADRAO 006 - Compras com aprovação ou validação
Tipo de pedido:
- autorização de compras, limiares por valor, segregação de funções e controlo de exceções

Opções a avaliar primeiro:
- configuração standard de purchase
- módulos standard adicionais de approvals
- regras de acesso e atividades standard

Cobertura standard tipica:
- parcial

Quando Studio pode chegar:
- quando a necessidade e visibilidade, campos adicionais ou passos simples

Quando custom pode ser necessário:
- quando ha politica multicriterio complexa, integração com procurement externo ou controlo avancado por centro de custo

Riscos tipicos:
- criar workflow pesado para compensar politica interna pouco clara
- bloqueios operacionais em compras urgentes

Nota consultiva:
- validar primeiro se o objetivo e governance, compliance ou controlo de custo

## PADRAO 007 - Logistica com rastreabilidade
Tipo de pedido:
- lotes, séries, tracking, qualidade, localizações e histórico operacional

Opções a avaliar primeiro:
- configurações standard de inventory, barcode, quality, mrp e repair
- parametrização de tracking por produto e por operação

Cobertura standard tipica:
- parcial a total

Quando Studio pode chegar:
- quando faltam apenas campos complementares, etiquetas internas ou pequenas vistas

Quando custom pode ser necessário:
- quando ha rastreabilidade regulatoria específica, recolha de dados em hardware próprio ou cadeia logistica altamente especial

Riscos tipicos:
- desenho de processo físico incoerente com o sistema
- excesso de custom para compensar disciplina operacional fraca

Nota consultiva:
- antes de pensar em custom, confirmar se o problema esta na configuração de rotas, tracking ou qualidade

## PADRAO 008 - Reporting e dashboards
Tipo de pedido:
- indicadores, dashboards operacionais, análise de desempenho e relatórios executivos

Opções a avaliar primeiro:
- relatórios standard
- pivots, graphs, spreadsheets e dashboards nativos
- módulos standard adicionais relacionados com o domínio

Cobertura standard tipica:
- parcial a total para análise operacional

Quando Studio pode chegar:
- quando o gap e de apresentação simples ou pequenos campos auxiliares

Quando custom pode ser necessário:
- quando ha metricas compostas, consolidação multi-fonte, performance critica ou layout analitico muito específico

Riscos tipicos:
- pedir dashboard quando o problema real e qualidade de dados
- querer KPI definitivo sem definição funcional estável

Nota consultiva:
- validar sempre definição de indicador, periodicidade, fonte de dados e decisão que o relatório suporta
