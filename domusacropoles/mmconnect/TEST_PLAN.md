# Plano de Testes MMConnect

## 1. Objetivo

Garantir cobertura funcional mínima para todos os domínios implementados no addon `mmconnect`, assegurando que:

- a instalação corre sem erros;
- os fluxos principais podem ser executados ponta a ponta;
- a segurança por perfil funciona;
- as integrações ficam preparadas para testes posteriores com hardware real.

## 2. Estratégia

Executar em três camadas:

1. testes automáticos Odoo;
2. testes funcionais guiados por processo;
3. testes de integração e aceitação.

## 3. Testes automáticos incluídos

- criação de estrutura RH e dados mestres;
- processamento simples de assiduidade;
- deteção de marcação em falta;
- fecho com criação de movimentos de banco;
- submissão e aprovação de distribuição de tempo;
- ciclo de visita e reservas;
- ciclo base de importação;
- segurança de colaborador e supervisor em serviço externo.

## 4. Matriz funcional manual

### RH base

- criar entidade, centro de custo, local, perfil e colaborador;
- validar relação colaborador-supervisor;
- validar campos de legado e chaves externas.

### Assiduidade

- criar marcação de entrada e saída;
- processar resultado diário;
- fechar resultado e validar banco de horas;
- testar cenário com marcação ímpar;
- testar ausência e serviço externo.

### Escalas e tempo

- criar plano e grupo de escala;
- submeter folha de distribuição de tempo;
- aprovar a folha com supervisor;
- validar totais por centro de custo/local.

### Operações

- registar visitante e empresa;
- marcar visita, aprovar, fazer check-in e check-out;
- reservar sala e validar conflito;
- reservar viatura e validar conflito.

### Dispositivos

- criar terminal;
- criar comando e mudar de `draft` para `queued`, `sent` e `done`;
- criar georreferência com pontos;
- criar template biométrico;
- criar permissão de acesso.

### RGPD e importações

- registar consentimento;
- submeter pedido RGPD e encerrá-lo;
- criar perfil de importação;
- abrir job, iniciar, concluir e validar logs.

### Verticais

- criar tarefa, iniciar e concluir;
- criar campanha Agro;
- criar contentor e rota de recolha;
- criar obra.

## 5. Testes de segurança

- colaborador só vê os seus pedidos/resultados;
- supervisor vê pedidos da sua equipa;
- gestor vê todos os registos;
- utilizador sem grupo MMConnect não deve operar modelos custom.

## 6. Testes de integração futura

- importação real de eventos de terminal;
- envio de biometrias;
- sincronização LDAP;
- exportação para Primavera;
- validação GPS/LPR.

## 7. Critérios de aceitação

- addon instala sem erros;
- todos os testes automáticos passam;
- todos os cenários manuais críticos passam;
- sem conflitos de segurança em dados pessoais;
- sem conflitos de reservas ou inconsistências de workflow.
