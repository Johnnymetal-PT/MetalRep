# Janela de manutenção — `pg_brodoo` 19.0.1.14.2 (produção da Parâmetro Global)

Guião escrito por `TPL_JANELA_MANUTENCAO.md`. Destino: o Odoo da Parâmetro Global (`parametroglobal.odoo.com`), que implanta a partir da `main` de `parametro-odoo/Parametro_Global` pelo Odoo.sh.

PR: [Parametro_Global#23](https://github.com/parametro-odoo/Parametro_Global/pull/23). Framework: [_pg_template#79](https://github.com/bruno-pinheiro-pg/_pg_template/pull/79).

## 1. O que muda

### Patch único — uma chave API por protocolo na ligação ao Odoo do cliente

- **Módulo e ficheiros:** `pg_brodoo/models/pg_odoo_connection.py` (campo novo `api_key_mcp`; textos de `api_key` e `base_url`), `pg_brodoo/views/pg_ai_repository_views.xml` (coluna nova na tabela de ligações), `pg_brodoo/tests/test_odoo_connection.py` (dois testes), `__manifest__.py` (19.0.1.14.1 → 19.0.1.14.2).
- **Antes:** cada ligação guarda uma chave. Num Odoo 20 de cliente, uma chave só abre os endpoints do seu âmbito: com a chave RPC o MCP fica fechado, com a MCP o RPC dá «uid vazio». Uma segunda ligação com a mesma finalidade é recusada pela restrição de unicidade.
- **Depois:** a ligação tem as colunas «Odoo API Key (RPC)» e «Odoo API Key (MCP)». A segunda é opcional; vazia, os helpers usam a RPC nos dois canais, como até agora. Nada muda para as 81 ligações existentes.
- **Quem pediu:** Bruno Pinheiro, a 2026-10-14, a partir do caso animovel (Odoo 20.0+e), onde a ligação de produção ficou sem forma de servir os dois canais.
- **Classificação:** decisão nossa, documentada em `AGENTS_SHARED.md` («Uma ligação por finalidade, uma chave por protocolo»).

## 2. Linha de base — o travão

Medida contra o próprio destino a 2026-10-14, pelo canal Brodoo:

| | valor |
|---|---|
| série do Odoo no destino (módulo `base`) | **19.0**.1.3 — confirmada contra o destino |
| versão instalada do `pg_brodoo` | `19.0.1.14.1`, `write_date` 2026-10-09 |
| versão na `main` do repositório | `19.0.1.14.1` |
| módulos pendentes de atualização | 0 |
| ligações `pg.odoo.connection` (ativas e arquivadas) | 81, das quais 22 `brodoo_dev` |
| `fields_get` de `api_key` | presente, **sem `groups`** |
| `fields_get` de `api_key_mcp` | ausente |

**Se a versão instalada já não for a 19.0.1.14.1, ou houver módulos pendentes, abortar:** alguém publicou entretanto, e esta janela não lhe passa por cima. Em particular, se a 1.15.0 (PR #20) tiver entrado primeiro, este PR tem de ser rebaseado e o campo novo levar o mesmo `groups=`.

### Testes do addon

Corridos a 2026-10-14 contra o ramo `feat/chave-api-por-protocolo`: instalação e upgrade numa base nova, **0 falhas e 0 erros em 100 testes** nas duas passagens, incluindo os dois testes novos. Correram num PostgreSQL 12 temporário (`initdb` + `pg_ctl` com os binários da instalação local), porque o serviço `PostgreSQL_For_Odoo` exige administrador para arrancar. O Odoo avisa que o PostgreSQL 12 está abaixo do mínimo recomendado; não afetou a execução.

O Odoo.sh não corre testes em builds de produção: esta é a única execução que o código terá antes de chegar lá.

## 3. Reversão — escrita antes, não depois

- **Código:** `git revert` do merge na `main` do `Parametro_Global` e novo build do Odoo.sh.
- **Coluna na base:** um revert deixa a coluna `api_key_mcp` na tabela, órfã e inofensiva. **Não a apagar**: se houver chaves lá escritas, são segredos de clientes, e apagá-las não as revoga no Odoo de origem.
- **Base de dados:** o Odoo.sh mantém backups diários da produção. Não há ficheiros a resguardar à mão.

## 4. Os passos

1. **Correr os testes do addon** (feito a 2026-10-14; repetir se o PR mudar). Numa consola **como administrador**, ou com um PostgreSQL temporário:
   ```powershell
   Start-Service PostgreSQL_For_Odoo
   powershell -NoProfile -ExecutionPolicy Bypass -File <_pg_template>\scripts\pg_run_odoo_addon_tests.ps1 -AddonsRoot <Repos>\Parametro_Global
   ```
   Instala e depois atualiza o `pg_brodoo` numa base nova e corre a suite. Se falhar, a janela não abre.
2. **Confirmar a linha de base** da secção 2, em especial a versão instalada e os zero pendentes.
3. **Avisar** quem está na secção 7.
4. **Merge do PR #23** para a `main`. Dispara o build de produção no Odoo.sh.
5. **Esperar o build** e confirmar que o `pg_brodoo` passou a `19.0.1.14.2`. Se o upgrade falhar, o Odoo.sh deixa a produção no código antigo.
6. **Merge do PR #79** do `_pg_template` e sincronização da frota (`pg_align_fleet_framework.ps1`). A ordem não é crítica — o helper funciona com e sem o campo —, mas o `AGENTS_SHARED.md` só deve anunciar a coluna depois de ela existir.
7. **Verificar** (secção 5).

Reversíveis sozinhos: 4 e 5 (por `revert` e novo build) e 6 (por `revert`).

## 5. Verificação, no fim

Contra o destino, não contra o manifesto:

- `ir.module.module`: `pg_brodoo` com `installed_version = 19.0.1.14.2` e zero módulos pendentes;
- `fields_get` de `pg.odoo.connection` devolve `api_key_mcp`;
- contagem de ligações igual à da secção 2 (81, salvo as criadas entretanto);
- **a prova que interessa — o comportamento:** na ligação 58 (animovel, produção), guardar a chave RPC em `api_key` e a MCP em `api_key_mcp`, e depois:
  1. `pg_odoo_client_query.ps1 -ProjectKey odoo-animovel -Purpose production -Protocol rpc -Model ir.module.module ...` devolve os módulos instalados;
  2. o mesmo com `-Protocol mcp -Model res.users` devolve os utilizadores;
  3. uma consulta a outro cliente, sem `api_key_mcp`, continua a funcionar como antes.

  Só com os três é que «aplicado» vira «verificado».

A versão do manifest não prova o código; o que prova aqui é o `fields_get` devolver o campo novo e o comportamento dos três pontos.

## 6. O que este guião NÃO leva, e é deliberado

- **Não protege a chave nova com o grupo de credenciais.** Esse grupo só existe na 1.15.0 (PR #20), que não está instalada por decisão de 2026-10-07. A `api_key_mcp` fica exposta exatamente como a `api_key` está hoje (risco R1). O guião da 1.15.0 foi atualizado para cobrir os dois campos.
- **Não preenche chaves MCP nas outras ligações.** Só faz falta em clientes com Odoo 20+ que usem o MCP; vazio, nada muda.
- **Não atualiza o `pg_verificar_grupo_api_key.py`**, que só verifica a `api_key`. É da janela da 1.15.0.
- **Não passa pela staging `brodoo` do Parâmetro Global.** O rebuild invalidaria as 22 ligações `brodoo_dev`; os testes locais do passo 1 cobrem o que a staging cobriria para um campo novo.

## 7. Antes de abrir a janela

- **Avisar** quem cria e mantém ligações (lista da secção 7 do guião da 1.15.0: Pedro Coelho, Bruno Pinheiro, Nuno Oliveira, Lara Cunha, Cláudio Pereira, Miguel Dias). Durante o build, o canal Brodoo fica indisponível alguns minutos.
- **Coordenar com o PR #20**: se a 1.15.0 for para a frente primeiro, este guião tem de ser revisto (secção 2).
- **Produção exige confirmação explícita** para esta execução concreta.
