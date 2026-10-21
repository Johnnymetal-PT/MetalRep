# Janela de manutenção — `pg_brodoo` 19.0.1.15.0 (produção da Parâmetro Global)

> Guião por aprovar. Escrito segundo `TPL_JANELA_MANUTENCAO.md`. A execução em produção **não está coberta pelo mandato permanente** — cria registos de grupo e uma restrição SQL, e o mandato exclui alterações que toquem em dados ou esquema. Precisa de aval explícito para esta execução concreta.

Destino: `parametroglobal.odoo.com`, base `parametro-main-29950773` (Odoo.sh, projeto `parametro`, branch `main`).
Origem do código: `parametro-odoo/Parametro_Global`, PR **#20**, branch `feat/api-key-menor-privilegio`.

---

## 1. O que muda

### Patch A — a API key das ligações passa a exigir grupo

- **Módulo e ficheiros:** `pg_brodoo/models/pg_odoo_connection.py` (o campo `api_key` ganha `groups=`), `pg_brodoo/security/pg_brodoo_security.xml` (privilégio + grupo novos), `__manifest__.py` (versão e `data`).
- **Antes:** qualquer utilizador em `project.group_project_user` lê e escreve o `api_key` de todas as ligações, sem nenhuma `ir.rule` — as credenciais dos Odoo dos clientes, produção incluída. Confirmado na produção a 2026-09-29: o `fields_get` devolve `api_key` **sem atributo `groups`**.
- **Depois:** só quem tiver «Credenciais dos Odoo dos clientes: Ler credenciais» lê a chave. Quem não tiver continua a ver a ligação, mas não a chave.
- **Quem pediu:** é o **risco R1** da auditoria de credenciais (`docs/PG_SECURITY_CREDENTIALS_AUDIT.md`), o mais alto do levantamento. Foi pedido — não é uma correção à procura de problema.
- **Classificação:** defeito de segurança.
- **Atualização de 2026-10-14 — a 1.14.2 trouxe uma segunda chave.** A 19.0.1.14.2 (branch `feat/chave-api-por-protocolo`) acrescenta `api_key_mcp` ao mesmo modelo, pelo mesmo motivo que leva a este guião: é um segredo do Odoo do cliente. **Antes de abrir esta janela, a branch da 1.15.0 tem de ser rebaseada sobre a 1.14.2 e pôr o mesmo `groups=` também na `api_key_mcp`**, e a verificação da secção 5 passa a cobrir os dois campos (o `pg_verificar_grupo_api_key.py` ainda só olha para a `api_key`). Sem isto, a janela fecha uma chave e deixa a outra aberta.

### Patch B — RETIRADO

Este guião afirmava que o upgrade criaria, de boleia, a restrição de unicidade em falta desde 11/08. **Era falso, e o erro foi meu.**

A restrição existe: `pg_odoo_connection_pg_odoo_connection_repository_purpose_uniq`, `unique(repository_id, purpose)`, criada no upgrade de 2026-08-11. Consultei o `ir.model.constraint` com `-Limit 30`, recebi 30 linhas e li-as como total — são 75, e as de `odoo_connection` estavam para lá do limite que eu próprio impus. A tarefa 7588 foi retratada.

Fica escrito em vez de apagado porque a lição é a que interessa: um controlo positivo prova que a consulta responde, **não** que a lista veio inteira. São coisas diferentes.

**Esta janela leva um patch só: o A.**

## 2. Linha de base — o travão

Medida contra o próprio destino a 2026-09-29, pelo canal Brodoo:

| | valor |
|---|---|
| série do Odoo no destino (módulo `base`) | **19.0**.1.3 — confirmada contra o destino, não presumida |
| versão instalada do `pg_brodoo` | `19.0.1.14.0`, `write_date` **2026-08-11** |
| versão na `main` do repositório | `19.0.1.14.0` (a `1.15.0` está só no PR #20) |
| registos XML do `pg_brodoo` | 591 |
| restrições do `pg_brodoo` na base | **75**, das quais 4 de `pg.odoo.connection` — a unicidade **existe** |
| grupos do `pg_brodoo` na base | **0** |
| `api_key` em `fields_get` | presente, **sem `groups`** |
| ligações configuradas | 71 (69 na primeira medição; a equipa está a criá-las hoje) |
| pares `(repository_id, purpose)` duplicados | **0** — e a restrição já os impedia |
| módulos pendentes de atualização | 0 |

**Se algum destes valores não bater no momento da execução, abortar.** Em especial os duplicados: se entretanto aparecer um par repetido, a criação da restrição falha e o upgrade fica a meio.

### O que não está provado

`PONTO POR VALIDAR`: os testes que acompanham o PR #20 **nunca correram** — foram escritos sem instância Odoo (confirmado pela sessão que os escreveu). Estão bem desenhados e cobrem a assimetria nos dois sentidos, mas nunca passaram por um interpretador.

O Odoo.sh não corre testes em builds de produção. Um merge direto para a `main` põe o código a correr **sem nunca ter sido executado**. Se existir branch de staging ligada ao projeto, é lá que se corrige isto, e custa minutos.

Não escrever «testado» sobre esta janela enquanto isto não mudar.

**Porque se decidiu não passar pela staging, e o que essa decisão custa.** A staging existe (branch `brodoo`) e o `cherry-pick` aplica limpo. Não se usou por dois custos concretos: o rebuild invalida as **19 ligações de finalidade `brodoo_dev`**, e a branch está 38 commits à frente da `main` com trabalho de outra pessoa por promover, o que misturaria o que se quer testar com o que não se quer.

**Correção ao argumento com que esta decisão foi defendida.** Escreveu-se que a verificação na produção é «mais forte» do que os testes unitários. **Não é mais forte — é mais tarde.** A staging apanha antes de alguém ser afetado; a verificação no destino confirma depois de já estar aplicado. São garantias diferentes, e não a mesma garantia em momentos diferentes. Aqui a troca compensa porque o raio de dano é conhecido e limitado e o desfazer é um `revert` mais build; numa alteração maior, «antes» volta a valer mais do que «no sítio real».

**O que a plataforma cobre, e o que não cobre.** No Odoo.sh, se a atualização do módulo falhar durante o build de produção, o build falha e a produção **fica no código antigo** — o modo de falha «código mau chega a produção» está em boa parte coberto. O que não está coberto é «o código instala bem e tranca as pessoas de fora», e é contra esse que a atribuição imediata do grupo (passo 6) está desenhada.

**O que substitui os testes, e deve ficar dito assim.** As três afirmações negativas dos testes que nunca correram — sem o grupo o `read` falha, o `write` falha, o `fields_get` não devolve o campo — são exatamente as três da verificação da secção 5. Os testes ficam por correr; o que os substitui é a verificação no destino, feita depois.

## 3. Reversão — escrita antes, não depois

- **Código:** `git revert` do merge na `main` do `Parametro_Global` e novo build do Odoo.sh. Não há ficheiros a substituir à mão — o Odoo.sh implanta a partir do git.
- **Registos:** o grupo e o privilégio são criados pelo módulo; reverter o código deixa-os órfãos e inofensivos. **Não apagar** — desactivar, se for preciso.
- **Restrição SQL:** uma vez criada, fica. Não se reverte, e não se quer reverter: é a proteção que faltava.
- **Base de dados:** o Odoo.sh mantém backups diários da produção. Não é preciso resguardo manual de ficheiros, ao contrário de um servidor on-premise.
- **Atribuições de grupo:** anotar quem ficou no grupo, para saber o que desfazer.

## 4. Os passos

1. **Coordenar com a sessão que abriu o #20.** É trabalho em curso de outra pessoa; esta janela não lhe passa por cima.
2. **Confirmar a linha de base** da secção 2 — em especial os zero duplicados e os zero módulos pendentes.
3. **Avisar** quem está listado na secção 7, **antes** de abrir.
4. **Merge do PR #20** para a `main`. Dispara o build do Odoo.sh.
5. **Esperar o build** e confirmar que o módulo passou a `19.0.1.15.0`. Sem isto, o passo 6 não faz sentido.
6. **Atribuir o grupo** aos utilizadores da secção 7, **imediatamente a seguir**. Entre o passo 5 e este, ninguém lê credenciais de cliente.
7. **Verificar** (secção 5).

Reversíveis sozinhos: 4 e 5 (por `revert` e novo build). O passo 6 desfaz-se retirando o grupo.

## 5. Verificação, no fim

Contra o destino, não contra o manifesto:

- o grupo existe: `ir.model.data` com `module=pg_brodoo`, `name=group_pg_odoo_connection_secret`;
- o campo está fechado: `fields_get` de `pg.odoo.connection` devolve `api_key` **com** `groups`, ou não o devolve de todo a quem está fora;
- a restrição existe: `ir.model.constraint` do `pg_brodoo` passa a incluir uma de `odoo_connection`;
- os utilizadores da secção 7 estão no grupo;
- **e a prova que interessa, pelos três lados** (sugestão da sessão que escreveu o patch, mais forte do que a minha):
  1. um **membro** do grupo lê a `api_key`;
  2. um **não-membro** não a lê;
  3. o `fields_get` de `pg.odoo.connection` **não devolve** `api_key` ao não-membro.

  O terceiro é o que apanha o caminho por RPC, que é por onde os helpers falam com o modelo. Só com os três é que «aplicado» vira «verificado».
- correr um `pg_odoo_client_query.ps1` real contra um cliente, para provar que a ferramenta da equipa sobreviveu à restrição.

## 6. O que este guião NÃO leva, e é deliberado

- **Não mexe nas chaves API dos clientes em si.** Fecha quem as lê; não as roda. Rodar é trabalho à parte e de outra escala.
- **Não retira o acesso a `pg.odoo.connection` como modelo.** Quem perde é o campo da chave; a ligação continua visível, porque é preciso vê-la para trabalhar.
- **Os consumidores headless — ponto fechado.** O utilizador de serviço `Brodoo` (uid 191) está `active: False` desde 2026-09-28 ~14:17 UTC, e a última autenticação dele foi às 14:16:44 desse dia. Um utilizador arquivado não é encontrado pelo `search` do `res.users._login`, pelo que nenhuma chave dele autentica — provado pela negativa com `pg_retire_shared_brodoo_key.ps1 -Provar`. As 42 alterações que assina são históricas. Esta janela não lhe tira leitura nenhuma: ele já não tem nada a tirar.
- **O `auto-heal` sobrevive.** Lê `api_key` (passa a exigir o grupo) e escreve `database` (não é restringido). Com a lista da secção 7, quem o corre tem as duas coisas.
- **O grupo tem `noupdate="1"`.** A pertença sobrevive a upgrades — era a intenção —, mas alterações à definição do grupo também não se reaplicam. Mudar nome ou descrição exige mão ou migração.
- **Clones anteriores à v2.41.0 do `_pg_template`** recebem o erro cru do Odoo em vez do nome do grupo em falta. Não é defeito desta janela.
- **Não corrige a numeração de releases** nem propaga à frota. São outras conversas.

## 7. Antes de abrir a janela

**Avisar, porque durante o intervalo entre os passos 5 e 6 os canais de cliente estão calados:** quem estiver a meio de uma migração de dados, de uma consulta a produção de cliente, ou do workflow de adoção.

**Quem deve ficar no grupo** — proposto por evidência, não por cargo. Lista de quem criou ou alterou ligações na produção:

| utilizador | uid | criou | alterou |
|---|---|---|---|
| Pedro Coelho | 80 | 26 | 7 |
| Bruno Pinheiro | 176 | 13 | 12 |
| Nuno Oliveira | 173 | 6 | 7 |
| Lara Cunha | 188 | 4 | 2 |
| Cláudio Pereira | 2 | 3 | — |
| Miguel Dias | 174 | 2 | — |

Nota que vale a decisão: uma lista feita a partir de quem tem acesso de escrita ao repositório da framework **teria falhado o Pedro Coelho**, que é de longe o maior utilizador destas ligações e não é colaborador desse repositório. O critério certo é quem trabalha com Odoo de clientes, não quem escreve na framework.

Ficam de fora, por não terem tocado em ligação nenhuma: José Couto e João Barros. Se algum deles precisar, acrescenta-se — é um clique, e é reversível.
