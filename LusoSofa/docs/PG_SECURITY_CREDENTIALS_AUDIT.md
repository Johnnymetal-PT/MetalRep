# PG_SECURITY_CREDENTIALS_AUDIT

## Finalidade

Registar o que foi **observado** sobre a gestão de credenciais da framework e deixar um prompt de
trabalho pronto a usar, para que quem pegar nesta frente não tenha de repetir o levantamento.

Este documento **não** é uma auditoria fechada nem um plano aprovado: é o levantamento factual feito
a 2026-07-30, durante a correção do bootstrap (ver `v2.16.1` no `CHANGELOG.md`), mais as perguntas
que ficaram sem resposta.

## Contexto do levantamento

A correção de `v2.16.1` fez o pull de doc templates passar a usar a credencial partilhada do
utilizador de serviço Brodoo (`credentials/brodoo_credentials.json`) quando não há
`$env:PG_ODOO_KNOWLEDGE_TOKEN`. Não acrescentou nenhum segredo — o ficheiro já existia e já era lido
pelo `pg_odoo_query.ps1` — mas alargou o número de fluxos que dependem dessa chave, o que torna útil
olhar para o modelo todo de uma vez.

## O que está contido (verificado)

`FACTO OBSERVADO`, cada ponto confirmado no repositório a 2026-07-30:

- `_pg_template` é um repositório **privado** (`gh repo view`: `isPrivate: true`).
- o `.gitignore` que os projetos recebem (`templates/.gitignore`) bloqueia
  `credentials/brodoo_credentials.json` e `brodoo_credentials.json`.
- `scripts/pg_sync_shared_assets.ps1` não tem **nenhuma** referência a `credentials`: o sync copia
  `templates/` e `doc_templates/`, e a pasta de credenciais não entra.
- num projeto bootstrapado de fresco (`vendaspp`) não existe pasta `credentials/`; o acesso em runtime
  é feito pelo symlink `.pg_framework/credentials/…`.
- nenhum segredo está escrito em código nos scripts; o `pg_pull_doc_templates.ps1` imprime a via de
  resolução e o login, nunca a chave.
- o caminho do pull é de **leitura** (`search_read` em `knowledge.article` e `ir.attachment`).

Nota: passar de uma API key de **conta pessoal** (o default anterior era o login de um colaborador)
para uma **conta de serviço** é, em si, uma melhoria: permite rotação sem tocar na conta de ninguém e
não deixa credenciais pessoais em fluxos operacionais.

## Riscos abertos

### R1 — a chave Brodoo dá acesso às credenciais dos Odoo dos clientes

O risco mais alto, e o que muda a natureza do problema.

`scripts/pg_odoo_client_query.ps1:141-142` autentica-se com a chave Brodoo e faz `search_read` em
`pg.odoo.connection` pedindo explicitamente o campo `api_key`. O mesmo padrão está em
`scripts/pg_odoo_migration_guard.py:188`. Ou seja: quem tiver a chave Brodoo consegue ler as API keys
dos Odoo dos clientes — incluindo ligações de finalidade `production` — desde que as regras de
registo e as ACL de campo do Odoo PG lho permitam (é o que os scripts pressupõem para funcionar).

Consequência: a chave Brodoo não é "uma credencial de leitura para consultas de apoio". É, na
prática, uma **chave mestra** do acesso programático aos clientes. Um ficheiro de texto simples num
clone git de cada colaborador é um sítio pouco adequado para isso.

### R2 — segredo partilhado em texto simples, propagado por `git pull`

`credentials/brodoo_credentials.json` é versionado no `_pg_template` privado e chega a cada máquina
pelo passo 2 do ritual. Implicações:

- quem sair da equipa continua com uma cópia válida no clone local e no *reflog* — a revogação só é
  real com **rotação**, não com a remoção do acesso ao repositório;
- a chave fica no histórico do git: rodar a chave não apaga as anteriores do histórico;
- não há registo de quem a usou (o Odoo vê apenas o utilizador Brodoo, igual para toda a equipa),
  pelo que uma utilização indevida não é atribuível.

`credentials/README.md` já prevê rotação na saída de um colaborador. Ficou por confirmar se está a
ser cumprida e qual foi a última data.

### R3 — a chave viaja na linha de comandos

`scripts/pg_pull_doc_templates.ps1:102` invoca o helper Python com `--api-key $apiKey`. Enquanto o
processo corre, a chave é legível na lista de processos da máquina (por exemplo
`Get-CimInstance Win32_Process | Select CommandLine`) por qualquer processo do utilizador, e pode ser
capturada por auditoria de criação de processos ou por ferramentas de EDR que registem linhas de
comando. Alternativas: variável de ambiente do processo filho, `stdin`, ou ficheiro temporário com
ACL restrita.

Este comportamento é anterior à `v2.16.1`; o que mudou é a frequência, porque o pull passou a correr
com sucesso em mais máquinas.

### R4 — o utilizador Brodoo não é read-only

`scripts/pg_odoo_query.ps1` aceita `-ArgsJson` e é usado com `-Method write` para persistir o
`database` em `pg.odoo.connection` (documentado em `templates/AGENTS_SHARED.md`, secção do nome da
base de dados). Logo, a mesma chave que serve consultas de apoio também escreve. O
`pg_odoo_migration_guard.py` protege as escritas **nos Odoo dos clientes**, mas não limita o que a
chave Brodoo pode fazer no Odoo da Parâmetro Global.

### R5 — sem inventário de onde a chave já esteve

Não existe registo de quais máquinas têm o clone, quantas cópias do ficheiro existem fora dele
(backups, pastas sincronizadas, screenshots de sessão), nem de exposições anteriores. Sem isso, não é
possível dizer se uma rotação é preventiva ou corretiva.

## Pontos por validar

`PONTO POR VALIDAR` — nada disto foi inspecionado e cada ponto altera a gravidade do que está acima:

1. permissões efetivas do utilizador Brodoo no Odoo PG: grupos, regras de registo e ACL do campo
   `api_key` em `pg.odoo.connection`. É isto que confirma ou desmente o alcance de R1.
2. data da última rotação da chave Brodoo e se existe procedimento a correr de facto.
3. se o Odoo PG está em Odoo Online, Odoo.sh ou on-premise, e que opções de gestão de segredos a
   edição permite (por exemplo restrição de API keys por IP ou por âmbito).
4. se as API keys dos clientes em `pg.odoo.connection` estão guardadas cifradas ou em claro na base
   de dados, e quem as vê na interface.
5. se algum repositório de projeto/cliente já tem, no histórico, uma cópia do ficheiro de credenciais
   (o `.gitignore` protege o presente, não o passado).

## Prompt de trabalho

Para colar num chat novo, no repositório `_pg_template`. Substituir o que estiver entre `<>`.

```
Trabalho de segurança de credenciais na framework PG.

Antes de qualquer análise, cumprir o ritual obrigatório do arranque definido em
.pg_framework/templates/AGENTS_SHARED.md e ler docs/PG_SECURITY_CREDENTIALS_AUDIT.md por
inteiro — o levantamento factual já está feito lá (riscos R1 a R5 e pontos por validar).
Não repetir o levantamento; partir dele.

Objetivo: reduzir o risco da credencial partilhada do utilizador de serviço Brodoo, sem
quebrar os fluxos que dependem dela (pg_odoo_query.ps1, pg_odoo_client_query.ps1,
pg_pull_doc_templates.ps1, pg_odoo_migration_guard.py).

Ordem de trabalho:
1. Fechar os pontos por validar 1 a 4 do documento. O ponto 1 é o mais importante: confirmar,
   com evidência, se o utilizador Brodoo consegue ler o campo api_key de pg.odoo.connection.
   Usar o canal de consulta da própria framework para o verificar e citar o que foi corrido.
   Se o alcance de R1 se confirmar, dizê-lo explicitamente antes de propor qualquer solução.
2. Só depois propor opções, na ordem de decisão obrigatória da framework (standard já
   disponível → standard adicional → Studio → custom). Avaliar pelo menos:
   - menor privilégio para o Brodoo: separar leitura de escrita, e separar o acesso à
     Knowledge do acesso a pg.odoo.connection (eventualmente contas de serviço distintas por
     finalidade, em vez de uma chave para tudo);
   - deixar de versionar o segredo em texto simples: gestor de segredos, cofre da máquina
     (Windows Credential Manager / DPAPI), ou chave por colaborador em vez de partilhada —
     comparar com o custo de operação atual, que é "quem tem o framework tem a credencial",
     e dizer o que se perde em conveniência;
   - atribuição de uso: conseguir saber quem usou o quê (hoje o Odoo vê sempre "Brodoo").
3. Corrigir R3 (chave na linha de comandos, scripts/pg_pull_doc_templates.ps1:102) — é
   contido, local e não depende de nenhuma decisão de arquitetura. Passar a chave por
   variável de ambiente do processo filho ou por stdin, e validar com um dry-run do pull.
4. Definir e documentar o procedimento de rotação: gatilhos (saída de colaborador, suspeita
   de exposição, periodicidade), quem executa, e o que fazer com as chaves antigas no
   histórico do git. Atualizar credentials/README.md.

Restrições, todas obrigatórias:
- nunca escrever segredos em repositórios de projeto/cliente, nem em ficheiros de ligação
  novos: as credenciais dos clientes resolvem-se em memória a partir de pg.odoo.connection;
- não colar nenhuma chave em documentos, mensagens, commits ou output de scripts;
- não rodar nem revogar chaves sem confirmação explícita do responsável — uma rotação
  às cegas parte a frota (workflows headless leem o `database` persistido e as ligações
  dos clientes);
- não alterar o contrato de pg_odoo_query.ps1 / pg_odoo_client_query.ps1 sem verificar todos
  os chamadores;
- distinguir sempre FACTO OBSERVADO, INFERENCIA e PONTO POR VALIDAR, e citar os paths.

Entregáveis:
- atualização de docs/PG_SECURITY_CREDENTIALS_AUDIT.md com os pontos por validar fechados e a
  gravidade de R1 confirmada ou desmentida;
- recomendação classificada segundo as categorias da framework, com impacto na operação diária
  da equipa (não só o desenho técnico);
- correção de R3 aplicada e testada;
- entrada no CHANGELOG.md.
```

## Referências

- `credentials/README.md` — modelo atual do segredo partilhado e regra de rotação
- `templates/AGENTS_SHARED.md` — canais de dados Brodoo e do cliente, política de credenciais e
  regra de migração de dados
- `scripts/pg_odoo_query.ps1` — canal Brodoo (leitura e escrita via `-ArgsJson`)
- `scripts/pg_odoo_client_query.ps1:141-142` — leitura de `api_key` das ligações dos clientes
- `scripts/pg_odoo_migration_guard.py:188` — mesmo padrão, no caminho das migrações
- `scripts/pg_pull_doc_templates.ps1:36-71` — cascata de resolução da credencial; `:102` — chave na
  linha de comandos
- `templates/.gitignore` — salvaguarda nos repositórios de projeto
- `CHANGELOG.md`, entrada `v2.16.1` — alteração que originou este levantamento
