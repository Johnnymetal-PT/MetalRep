# TPL_AUDITORIA_CODIGO_INTERNA.md

# TPL_AUDITORIA_CODIGO_INTERNA.md

# Template - Relatório de Auditoria de Código

## Finalidade

Template base para auditorias internas ou para relatórios finais de auditoria a entregar a cliente, com foco em cobertura integral, justiça técnica, rastreabilidade e utilidade para decisão.

## Princípios de redação

- Distinguir sempre `facto observado`, `leitura técnica`, `impacto percebido` e `ação sugerida`
- Distinguir requisito legítimo de falha técnica
- Distinguir código PG, código de parceiro, standard Odoo e configuração
- Incluir obrigatoriamente otimização/performance, risco residual e limitações
- Não omitir gaps de testes ou dependências externas

---

# [Título da Auditoria]

**Versão:** 1.0  
**Data:** DD/MM/AAAA  
**Autor:** [Nome / Equipa]  
**Estado:** Rascunho / Em revisão / Final

---

## 1. Enquadramento e objetivo

[Descrever o contexto da auditoria, o motivo do pedido e o objetivo principal.]

Responder explicitamente:

- o que foi auditado;
- por que razão foi auditado;
- que tipo de decisão esta auditoria deve suportar.

---

## 2. Baseline auditada

- **Repositório:** [repo]
- **Branch:** [branch]
- **Commit / referência temporal:** [commit / data]
- **Versão Odoo:** [versão]
- **Edição:** [Community / Enterprise]
- **Ambiente de referência:** [local / staging / produção / Odoo.sh / outro]
- **Projeto / Cliente:** [nome]

### Fontes consultadas

- [fonte 1]
- [fonte 2]
- [fonte 3]

---

## 3. Âmbito auditado

[Descrever o perímetro coberto.]

### Incluído

- [item]
- [item]

### Excluído

- [item]
- [item]

---

## 4. Metodologia aplicada

[Explicar como a auditoria foi executada.]

Incluir obrigatoriamente:

- inventário do perímetro;
- análise estática ao código;
- validação guiada por contexto funcional;
- comparação com standard Odoo;
- avaliação de otimização/performance;
- consolidação por severidade, origem e confiança.

---

## 5. Inventário consolidado por origem

### 5.1 Módulos Custom PG

| Módulo | Estado de revisão | Leitura consolidada |
|---|---|---|
| `[modulo]` | [estado] | [leitura] |

### 5.2 Módulos de parceiro / third-party

| Módulo | Estado de revisão | Leitura consolidada |
|---|---|---|
| `[modulo]` | [estado] | [leitura] |

### 5.3 Módulos standard Odoo / Odoo S.A.

| Módulo | Estado de revisão | Leitura consolidada |
|---|---|---|
| `[modulo]` | [estado] | [leitura] |

---

## 6. Sumário executivo dos findings

| ID | Tema | Origem | Tipo | Severidade | Confiança | Leitura consolidada |
|---|---|---|---|---|---|---|
| `AUD-001` | [tema] | [origem] | [tipo] | [sev] | [confiança] | [síntese] |

---

## 7. Desenvolvimento dos findings confirmados

### 7.1 [ID] - [Título]

**Facto observado**

[Descrever o comportamento encontrado em código, módulo, rota, regra, teste ou configuração.]

**Leitura técnica**

[Explicar o que o código faz, por que razão parece ter sido implementado e se o comportamento aparenta ser requisito, workaround, fragilidade ou desvio.]

**Impacto percebido**

- [impacto]
- [impacto]

**Ação sugerida**

- [corrigir / manter / documentar / validar / aceitar risco / otimizar]
- [passo concreto]

**Classificação**

- **Origem:** [PG / parceiro / Odoo standard / configuração / processo]
- **Tipo:** [segurança / dados / funcional / performance / governança / teste / operação / manutenibilidade]
- **Severidade:** [Crítica / Alta / Média / Baixa / Observação]
- **Confiança:** [Confirmado / Provável / Por validar]

**Evidência**

- [ficheiro / módulo / teste / artefacto / observação]

Repetir esta estrutura para cada finding confirmado.

---

## 8. Oportunidades de otimização e simplificação

Esta secção é obrigatória mesmo quando não existam findings críticos.

Organizar por:

- código que funciona mas deve ser otimizado;
- pontos com risco de performance;
- dívida técnica aceitável no curto prazo;
- simplificações possíveis face ao standard Odoo;
- componentes que merecem refatoração futura.

### 8.1 [Tema / módulo]

**Situação atual**

[descrição]

**Porque merece otimização**

- [motivo]
- [motivo]

**Sugestão**

- [ação]

---

## 9. Leitura global da solução

[Fazer uma leitura executiva equilibrada.]

Responder:

- o que está globalmente sólido;
- o que está funcionalmente alinhado;
- onde a solução depende de governação reforçada;
- onde existe dependência técnica consciente.

---

## 10. Risco residual e limitações da auditoria

Registar obrigatoriamente:

- o que depende de configuração ativa em staging/produção;
- o que foi analisado predominantemente de forma estática;
- lacunas de testes;
- dependências de validação funcional ou do cliente;
- limitações de ambiente, dados, acessos ou tempo;
- riscos que permanecem mesmo após a presente leitura.

---

## 11. Recomendações prioritárias

1. [recomendação]
2. [recomendação]
3. [recomendação]

---

## 12. Plano sugerido de seguimento

Separar por horizonte:

### Curto prazo

- [ação]

### Médio prazo

- [ação]

### Dívida técnica aceite / a reavaliar

- [ação]

---

## 13. Conclusão final

[Fechar com leitura profissional, equilibrada e defensável.]

---

## 14. Documentação de suporte

- [documento]
- [documento]
- [documento]
