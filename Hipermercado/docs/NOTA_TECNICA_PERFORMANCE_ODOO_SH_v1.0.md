# Odoo - Hipermercado — Nota Técnica de Capacidade e Performance (Odoo.sh Dedicado)

**Versão:** 1.0
**Data:** 01/07/2026
**Autor:** João Barros — Parâmetro Global, Consultoria Informática S.A.
**Cliente:** J. V. Oliveira, Lda
**Estado:** Rascunho para revisão interna
**Revisão pendente:** interlocutor do cliente, data a definir

> **Nota de template:** não existe no framework um template dedicado a notas de capacidade/performance. Este documento adota o tom e o rigor do `TPL_PROPOSTA_TECNICA.md` (analítico, orientado ao negócio, a distinguir factos confirmados de pontos por validar), com uma estrutura adaptada ao tema.

---

## 1. Contexto e objetivo

O cliente pretende **certeza** de que a solução Odoo que está a implementar funcionará de forma **rápida e eficiente** num servidor **Odoo.sh dedicado**, considerando o projeto atual e a sua prospeção futura.

**Enquadramento técnico (FACTO OBSERVADO — `PG_CONTEXT.md` e parâmetros do projeto):**
- Odoo **19.0 Enterprise** em **Odoo.sh**.
- Substituição do CEGID PHC e migração do "cérebro" do PrestaShop; website de catálogo (template Clarico Vega), operação multi-armazém e sincronização recorrente de catálogos de fornecedores.

**Premissas de dimensionamento assumidas para esta nota (fixadas com o cliente):**
- Catálogo alvo: **~50 000 produtos ativos** e volume equivalente de produtos arquivados.
- Sincronização de fornecedores **3× por dia**: **08:00, 12:00 e 17:00**.
- Armazenamento: teto máximo de **500 GB** (limite de provisionamento, **não** tamanho previsto da base de dados).
- Infraestrutura em avaliação: **Odoo.sh dedicado com 4 workers**.

**Estado do projeto:** fase inicial. Não existe ainda operação madura nem tráfego real, pelo que **não é possível extrair métricas empíricas precisas** do sistema atual. Esta limitação é endereçada explicitamente na secção 3.

---

## 2. Resposta consultiva

**Sim. Um Odoo.sh dedicado com 4 workers é adequado para correr este projeto de forma rápida e eficiente.**

A dimensão prevista (≈50 000 produtos ativos, catálogo ecommerce) é **modesta** para a plataforma: o Odoo/Odoo.sh corre em produção catálogos significativamente maiores. **A plataforma não é o fator de risco de performance deste projeto.**

- `INFERÊNCIA FUNDAMENTADA`: 4 workers dedicados são suficientes para o tráfego típico deste tipo de operação, desde que cumpridas as condições da secção 4.
- `FACTO OBSERVADO`: os fatores que determinam "rápido vs. lento" neste caso estão **sob o nosso controlo** (arquitetura da sincronização, higiene da base de dados, qualidade de queries/índices, tier de hosting e CDN) — não são limites inerentes da plataforma.

**Classificação da recomendação:** `Configuração standard` (infraestrutura + processo), tendo o **teste de carga** como critério de aceitação antes do go-live.

Ponto de honestidade metodológica: uma afirmação de performance responsável não se dá por opinião, mas por **medição**. Em fase inicial, essa medição é feita de forma **sintética** (secção 3), não sobre um sistema que ainda não tem uso real.

---

## 3. Como se dá a certeza — três camadas

A certeza de performance não é um evento único pré-lançamento medido no sistema de hoje. Constrói-se em três camadas, e só a última depende de dados reais:

**Camada 1 — Agora (fase inicial): certeza por arquitetura + referência de plataforma.**
Garantir que as decisões estruturais estão corretas à partida:
- tier dedicado e workers dimensionados;
- sincronização de fornecedores **off-peak / incremental**;
- **retenção de logs, índices adequados, CDN e cache** desde o início.
Um sistema bem desenhado a esta escala é rápido em Odoo.sh dedicado; um mal desenhado seria lento em qualquer infraestrutura. É engenharia, não sorte.

**Camada 2 — Antes do go-live: prova por teste de carga sintético.**
Não é necessário tráfego real para provar capacidade. Gera-se um catálogo representativo de ~50 000 produtos, simula-se carga (ex.: k6 ou Locust) contra uma **meta assumida** de utilizadores concorrentes, e executa-se **em simultâneo com as 3 sincronizações** — testando o pior caso (pico de tráfego + sincronização em simultâneo). Isto prova a capacidade contra pressupostos, sem depender de dados que ainda não existem.

**Camada 3 — Depois do go-live: validação com métricas reais + escala reativa.**
Com tráfego real, monitorizam-se p95 de tempo de resposta, CPU e carga de base de dados, e **escalam-se workers em minutos** no Odoo.sh se necessário. Esta reversibilidade de baixo custo é o que torna o compromisso seguro: não é preciso acertar o número exato de workers hoje.

---

## 4. Fatores que determinam a performance (e o risco já identificado)

Os workers escalam a **concorrência HTTP**; **não** escalam a instância única de PostgreSQL, que é **partilhada** entre o website e a sincronização. Por isso, o dimensionamento correto não se resume ao número de workers.

| Fator | Sob o nosso controlo | Ação |
|---|---|---|
| Tier de hosting (dedicado) + nº de workers | Sim — configuração | Dedicado + 4 workers como ponto de partida; escala reativa depois |
| Timing/arquitetura da sincronização | Sim — processo | Ver risco abaixo |
| Higiene da base de dados (retenção, autovacuum, purga de arquivados) | Sim — manutenção | Retenção obrigatória nos logs de sincronização; manutenção periódica |
| Qualidade de queries/índices + cache/CDN | Sim — configuração + código | CDN nativo, cache de páginas anónimas, índices de pesquisa |

**Risco já identificado (PONTO POR VALIDAR quanto à magnitude, mas evidente na conceção):**
Duas das três sincronizações — **12:00 e 17:00** — coincidem com janelas típicas de pico de tráfego (almoço e fim de tarde). Como a base de dados é partilhada, uma sincronização pesada nessas janelas degrada o tempo de resposta do website **independentemente do número de workers**. É o principal candidato a otimização e é uma decisão inteiramente nossa.

Mitigações a avaliar (após medição da duração e carga real de cada execução):
- manter **08:00 como sincronização completa** (antes do pico) e tornar **12:00 e 17:00 incrementais** (apenas deltas de preço/stock), muito mais leves;
- aplicar **throttling** ao processo (lotes menores, commits espaçados) para não saturar a base de dados;
- só depois disto reavaliar se 4 workers são suficientes.

Nota de código (FACTO OBSERVADO): o módulo `hiper_sync` já escreve nos produtos com `tracking_disable`/`mail_notrack`, o que é positivo. Falta-lhe, contudo, uma **política de retenção** para a tabela de linhas de sincronização, hoje inexistente.

---

## 5. Metas de performance propostas (critério de aceitação)

Sem metas concretas, "rápido" é subjetivo e não há certeza possível. Propõem-se as seguintes metas, **a validar com o cliente**, que se tornam o critério de aceitação do teste de carga:

- **Tempo de resposta:** páginas de `/shop` e de produto com **p95 < 2 s** para visitante anónimo, com CDN e cache ativos.
- **Concorrência alvo:** **[POR VALIDAR — nº de utilizadores concorrentes em pico esperado pelo cliente]**. Na ausência deste número, propõe-se dimensionar para uma banda de referência e testar com folga de 2× sobre essa banda.
- **Sincronização:** cada execução completa dentro de uma janela definida **[POR VALIDAR]** e **mantém o p95 do website dentro da meta** durante a sua execução.
- **Estabilidade:** taxa de erro HTTP < 0,5% sob carga de pico.

---

## 6. Plano do teste de carga sintético (pré-go-live)

1. Preparar ambiente **dedicado** representativo com ~50 000 produtos e imagens.
2. Ativar CDN, cache de páginas anónimas e confirmar índices de pesquisa.
3. Instrumentar (k6/Locust) percursos reais: navegação de categorias, página de produto, pesquisa, carrinho.
4. Executar o cenário de **pior caso**: carga na meta de concorrência **em simultâneo** com uma execução real da sincronização.
5. Medir p95, CPU, RAM e carga de PostgreSQL; identificar queries lentas (`pg_stat_statements`).
6. Afinar (timing/arquitetura do sync, índices, workers) até as metas da secção 5 serem cumpridas.
7. Go-live apenas após cumprimento das metas; monitorização contínua e escala reativa em produção.

---

## 7. Pressupostos

- As premissas de dimensionamento da secção 1 mantêm-se válidas (≈50 000 produtos ativos; sincronização 3×/dia).
- O cliente valida as metas de performance da secção 5 antes do teste de carga.
- É disponibilizado acesso técnico (SSH ao contentor Odoo.sh e/ou painel de monitorização) para medição e afinação.
- A arquitetura da sincronização pode ser ajustada (timing/incremental/throttling) sem restrição funcional impeditiva.

---

## 8. Pontos por validar

- [ ] Nº de utilizadores concorrentes em pico esperado — responsável: cliente.
- [ ] Janela aceitável de duração de cada sincronização — responsável: cliente + equipa técnica.
- [ ] Duração e carga de base de dados reais de cada execução da sincronização — via medição por SSH.
- [ ] Configuração real do contentor (workers, RAM) e queries mais lentas — via SSH / painel Odoo.sh.

---

## 9. Recomendação classificada

**`Configuração standard`** — Odoo.sh dedicado com 4 workers como ponto de partida, com a sincronização isolada das janelas de pico e a base de dados mantida leve; **teste de carga sintético como critério de aceitação** antes do go-live, e escala reativa de workers em produção.

Nenhuma parte desta recomendação exige customização estrutural. O único ajuste de código previsto é `Customização leve` no `hiper_sync` (política de retenção de logs e criação de produtos sem log de mensagens), destinado a manter as tabelas quentes leves.

---

## Referências consultadas

- `PG_CONTEXT.md` (versão, edição, ambiente, âmbito e restrições do projeto).
- Código do projeto: `hiper_sync/models/product_template.py`, `hiper_sync/models/sync_run_line.py`, `hiper_sync/data/ir_cron.xml`.
- Medição direta na base de dados de produção (XML-RPC/JSON-RPC), como contexto de escala e comportamento da sincronização.
- Documentação oficial Odoo 19.0 — Deployment/Odoo.sh (dimensionamento de workers e limites de memória).

---

## Histórico de versões

| Versão | Data | Autor | Alterações |
|---|---|---|---|
| 1.0 | 01/07/2026 | João Barros | Versão inicial — resposta de capacidade Odoo.sh dedicado + método de certeza em 3 camadas |
