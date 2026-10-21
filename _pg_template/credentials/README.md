# credentials/ — acesso ao Odoo da Parâmetro Global

A credencial de acesso ao Odoo da Parâmetro Global é **pessoal e por máquina**. Desde 2026-09-28 deixou de existir uma chave partilhada por toda a equipa.

## Configurar (uma vez por máquina)

1. No Odoo: **Definições > Utilizadores > (o meu utilizador) > Segurança da conta > Novas chaves API**.
2. Correr, em qualquer projeto com a framework:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1
```

O comando pede o login e a chave (a chave não aparece no ecrã), **valida antes de escrever** e mostra o nome de quem autenticou. Se aparecer o nome de outra pessoa, a chave está errada — e é melhor descobri-lo aqui do que quando uma escrita aparecer assinada por ela.

### Sobre a validade da chave

No Odoo 19 a duração máxima de uma chave depende do grupo de quem a cria: `Persistent Key` só aparece a quem tiver **Administração/Definições**, e os restantes ficam limitados ao teto do seu grupo (`api_key_duration`). Se a lista de durações só oferecer **1 dia**, não é uma restrição deliberada — é o campo `api_key_duration` a zero em todos os grupos, e o Odoo a usar o seu *fallback*. Ver `docs/PG_SECURITY_CREDENTIALS_AUDIT.md`.

Na Parâmetro Global isso resolve-se pelo módulo `pg_api_key_persistent`: quem estiver no grupo **API keys persistentes** passa a ter a opção `Persistent Key`, sem ganhar Administração. Se a opção não aparecer, é o grupo que falta — pedir a quem administra, não criar uma chave de um dia.

Quando a chave tem validade, o setup guarda a data e:

- o **preflight avisa com 14 dias de antecedência**, e avisa também depois de expirar — sem fazer nenhuma chamada à rede;
- a falha de autenticação passa a **nomear a expiração** como causa provável, em vez do «uid vazio» que o Odoo devolve e que não sugere nada sobre datas.

A data só é guardada quando é **certa**: o Odoo não expõe o índice da chave, pelo que com mais do que uma chave válida no mesmo utilizador não há como saber qual está em uso. Nesse caso não se guarda nada, e o comando diz porquê — um aviso inventado treina quem o lê a ignorar todos os outros.

Para conferir o que está configurado, sem escrever nada:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_init_odoo_credentials.ps1 -Verificar
```

## O que fica onde

| | onde | versionado |
|---|---|---|
| `login` + `api_key` | `%USERPROFILE%\.pg\odoo_credentials.json` | **não** — fora de qualquer repositório |
| `url` + `db` | `credentials/pg_odoo_endpoint.json` | sim — não são segredo |

Por máquina ficam dois campos, não quatro. O endereço e a base são mantidos num sítio só: se o Odoo PG mudar de endereço, a frota acompanha sem ninguém mexer na sua configuração.

Cascata de resolução, implementada uma única vez em `scripts/pg_odoo_credentials_common.ps1` e no gémeo `scripts/pg_odoo_credentials.py`:

1. `PG_ODOO_API_KEY` + `PG_ODOO_LOGIN` — override por sessão e via de CI;
2. `PG_ODOO_KNOWLEDGE_TOKEN` — alias legado, ainda aceite;
3. o ficheiro da máquina — a via normal, e a última.

Houve um quarto degrau: uma chave partilhada guardada no repositório. Saiu a 2026-09-28, depois de a conta de serviço ser arquivada e de se provar, pela negativa, que a chave deixou de autenticar. Sem esse degrau, uma máquina por configurar falha logo com o comando que resolve, em vez de falhar com «uid vazio» depois de usar uma chave morta.

## Porque é que a chave partilhada acabou

Duas razões, e a segunda é a que pesa mais.

**A chave estava no histórico do git.** Entrou no repositório em 2026-07-09 e lá fica: apagar o ficheiro não revoga nada. Quem saísse da equipa mantinha uma cópia válida no clone e no *reflog*, e a única revogação real é do lado do Odoo.

**Nada era atribuível.** Todas as escritas feitas pelos scripts apareciam como «Brodoo» — as ligações `pg.odoo.connection`, os artigos do Knowledge, as correções de dados. Não havia como saber quem tinha feito o quê, o que é exactamente a cegueira que o campo `operator` do log de tokens veio corrigir do lado de cá. Com chave pessoal, o Odoo regista quem foi.

Havia ainda o sinal de que o modelo já não servia: existiam **duas** chaves do utilizador de serviço, uma delas emitida para uma pessoa em concreto. Quando alguém precisa de uma chave só sua e a forma de a obter é emitir outra chave da conta partilhada, o modelo já estava a ser contornado.

## O que isto NÃO resolve

Qualquer utilizador de projeto no Odoo PG continua a poder ler as API keys dos Odoo dos clientes em `pg.odoo.connection` — não há regra de registo sobre o modelo e o acesso é dado a `project.group_project_user`. A chave deixou de ser partilhada; continua a ser uma chave com muito alcance.

Tratar isso é menor privilégio sobre o modelo, não sobre a credencial, e está registado como fase posterior do `PG-011`. Ver `docs/PG_SECURITY_CREDENTIALS_AUDIT.md`, risco R1.

## Regras que se mantêm

- **nunca** copiar credenciais para repositórios de projeto ou de cliente. O sync de assets partilhados não lhes toca, e o `.gitignore` que os projetos recebem cobre-as como salvaguarda dupla;
- as credenciais dos **Odoo dos clientes** vivem centralizadas no Odoo PG (`pg.odoo.connection`) e resolvem-se em memória — nunca em ficheiros de ligação com chaves dentro dos repositórios;
- quem sai da equipa: revogar a **chave dessa pessoa** no Odoo. Deixou de ser preciso rodar a chave de toda a gente.
