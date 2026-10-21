# TPL_MATRIZ_FUNCIONAL_RACI_EXECUTAVEL.md

## Objetivo

Converter a matriz funcional em modelo executável para configuração e controlo de acessos no Odoo.

## Instruções de preenchimento

1. Preencher uma linha por combinação real de `função + processo + módulo + ação`.
2. Em `RACI`, usar exatamente um `A` por linha.
3. Não deixar linhas com `owner`, `validador` ou `aprovador` em branco.
4. Identificar exceções com validade temporal e motivo.
5. Validar com cliente antes de aplicar grupos/permissões no Odoo.

## Legenda RACI

- `R` = Responsible (executa)
- `A` = Accountable (dono da decisão final)
- `C` = Consulted (consultado)
- `I` = Informed (informado)

## A. Matriz Executável (Núcleo)

| ID | Departamento | Função | Processo | Módulo Odoo | Ação | Objeto/Dados | R | A | C | I | Owner Funcional | Validador | Aprovador | Visibilidade | Multiempresa | Grupo Odoo Alvo | Record Rule / Domínio | Justificação de Acesso | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF-001 |  |  |  |  | Ler |  |  |  |  |  |  |  |  | Equipa / Empresa / Global / Privado | Sim/Não |  |  |  | Draft |
| MF-002 |  |  |  |  | Criar |  |  |  |  |  |  |  |  | Equipa / Empresa / Global / Privado | Sim/Não |  |  |  | Draft |
| MF-003 |  |  |  |  | Editar |  |  |  |  |  |  |  |  | Equipa / Empresa / Global / Privado | Sim/Não |  |  |  | Draft |
| MF-004 |  |  |  |  | Aprovar |  |  |  |  |  |  |  |  | Equipa / Empresa / Global / Privado | Sim/Não |  |  |  | Draft |
| MF-005 |  |  |  |  | Administrar |  |  |  |  |  |  |  |  | Equipa / Empresa / Global / Privado | Sim/Não |  |  |  | Draft |

## B. Mapeamento de Perfis para Grupos Odoo

| Perfil Funcional Alvo | Descrição | Módulos Cobertos | Grupo(s) Odoo | Permissões (R/W/C/D) | Limites de Visibilidade | Owner Funcional | Estado |
|---|---|---|---|---|---|---|---|
| Operacional |  |  |  |  |  |  | Draft |
| Coordenador de Área |  |  |  |  |  |  | Draft |
| Admin de Módulo |  |  |  |  |  |  | Draft |
| Admin Global |  |  |  |  |  |  | Draft |
| Exceção Crítica |  |  |  |  |  |  | Draft |

## C. Exceções e Segregação de Funções

| ID Exceção | Utilizador / Função | Tipo de Exceção | Risco | Mitigação | Aprovador | Data Início | Data Fim | Revisão Periódica | Estado |
|---|---|---|---|---|---|---|---|---|---|
| EX-001 |  | Multiempresa |  |  |  |  |  | Mensal/Trimestral | Proposta |
| EX-002 |  | Admin Global |  |  |  |  |  | Mensal/Trimestral | Proposta |

## D. Checklist de Qualidade (Gate antes de aplicar no Odoo)

| Critério | Sim | Não | Observações |
|---|---|---|---|
| Todos os processos críticos têm owner funcional definido |  |  |  |
| Cada linha da matriz tem exatamente um `A` (Accountable) |  |  |  |
| Perfis administrativos estão justificados e limitados |  |  |  |
| Exceções têm data fim e revisão periódica |  |  |  |
| Visibilidade por equipa/empresa/global está explicitada |  |  |  |
| Mapeamento para grupos Odoo está fechado |  |  |  |
| Cliente validou formalmente a matriz |  |  |  |

## E. Histórico de Versões

| Versão | Data | Autor | Alterações |
|---|---|---|---|
| 0.1 | DD/MM/AAAA |  | Versão inicial executável |
