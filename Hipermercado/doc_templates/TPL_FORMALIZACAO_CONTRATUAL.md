# TPL_FORMALIZACAO_CONTRATUAL.md

## 12. Instruções para o Agente Brodoo
Este template é a fonte de verdade para o agente perceber que entregáveis devem ser preparados, enviados e acompanhados em cada projeto.
Sempre que estiver a trabalhar num projeto, o agente deve:
1. Ler a matriz de entregáveis contratados do projeto.2. Identificar os entregáveis ativos com base na fase atual, cadência e momento previsto.3. Verificar se há entregáveis semanais, quinzenais, mensais, por fase ou pontuais que estejam pendentes.4. Alertar o Project Leader quando existir um entregável que deve ser preparado ou enviado.5. Indicar sempre:   - Nome do entregável.   - Fase do projeto.   - Cadência.   - Momento previsto.   - Template/base a usar.   - Dados obrigatórios em falta.   - Responsável pela preparação.   - Destinatário/aprovador.6. Se o entregável tiver template associado, sugerir explicitamente o template a preencher.7. Se faltarem dados obrigatórios, pedir esses dados antes de gerar ou recomendar o envio.8. Se a cadência contratada não estiver clara, assinalar como risco operacional e pedir validação.9. Se um entregável obrigatório não estiver ativo ou estiver sem data/momento, alertar o Project Leader.10. Se houver alteração aos entregáveis no onboarding, assumir que a matriz deve ser sincronizada para o contexto do projeto/repositório.
### Formato de resposta esperado do agente
Quando houver entregáveis a preparar, responder neste formato:
| Prioridade | Entregável | Quando enviar | Template/base | Dados em falta | Responsável | Próxima ação ||---|---|---|---|---|---|---|| Obrigatório/Recomendado/Opcional | Nome do entregável | Data, semana ou momento | Caminho do template/asset | Lista de campos em falta | Nome/papel | Preparar / Validar / Enviar / Aguardar dados |
### Regra de alerta
O agente deve alertar quando:
- Existe entregável obrigatório contratado ainda não preparado.- Existe entregável recorrente com cadência semanal, quinzenal ou mensal.- A fase atual exige validação, sign-off, plano, relatório ou comunicação ao cliente.- O Go-Live está próximo e faltam plano, treino, bugs/issues ou sign-off.- O projeto já passou o Go-Live e existem entregáveis de estabilização ou Fase 2.- A matriz de entregáveis foi alterada e ainda não foi sincronizada para o contexto do projeto.
### Exemplo de alerta
> Este projeto tem entregáveis contratados para esta fase.  > Para a semana atual, deves preparar o `Relatório de Progresso Semanal` usando `assets/10_Impl_Weekly_Progress_Report.docx` ou `TPL_STATUS_SEMANAL_V1.md`.  > Antes de enviar faltam: estado geral, trabalho realizado, próximos passos, riscos/bloqueios e consumo de budget.
