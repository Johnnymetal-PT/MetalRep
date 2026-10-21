# TPL_TESTE_RPC_STAGING

Manual e guião operacional de validação funcional direta via RPC no ambiente de Staging (Odoo.sh / Brodoo) antes de qualquer promoção ou push para a branch `main`.

Cumpre a regra fundamental de garantia de qualidade e não-regressão: **nenhuma alteração é promovida a produção (`main`) sem validação funcional executada e provada no ambiente de staging com a base de dados real.**

> [!CAUTION]
> **REGRA DE OURO INVIOLÁVEL (HARD GATE):**
> É **estritamente proibido** fazer push ou merge para a branch `main` sem antes executar com sucesso comprovado o script de teste funcional via RPC no ambiente de staging.
> O agente deve demonstrar na conversa as asserções e o output de sucesso do teste RPC em staging **antes** de executar qualquer comando git direcionado à `main`.

---

## 1. Princípio e Fluxo Operacional Obrigatório

O ciclo de entrega segue obrigatoriamente a seguinte sequência em 7 passos:

```
[1. Código na brodoo]
       │
       ▼
[2. Push/Promoção para Branch de Staging (ex.: teste / brodoo)]
       │
       ▼
[3. Rebuild Odoo.sh & Resolução da BD de Staging]
       │
       ▼
[4. Execução do Script de Teste RPC em Staging]
       │
       ▼
[5. HARD GATE: Validação e Apresentação de Provas (100% OK)]
       │
       ▼
[6. Promoção para a main (cherry-pick + push)]
       │
       ▼
[7. Regresso Imediato à branch brodoo]
```

---

## 2. Passo 1: Identificação da Branch de Staging e Push Inicial

1. O desenvolvimento e correção são implementados inicialmente na branch de trabalho `brodoo`.
2. O agente deve identificar qual é a branch de staging ativa no Odoo.sh do projeto:
   - Consultar as branches remotas (`git branch -r`).
   - Identificar se a branch de staging é `teste`, `staging` ou `brodoo`.
3. Fazer push do commit para a `brodoo` e promover/enviar igualmente para a branch de staging identificada:
   ```powershell
   git push origin brodoo
   git checkout <branch_staging>
   git cherry-pick <commit_hash>
   git push origin <branch_staging>
   git checkout brodoo
   ```

---

## 3. Passo 2: Resolução Dinâmica da Base de Dados de Staging

No Odoo.sh, cada rebuild na branch de staging cria um container com um novo ID de build (ex.: `jmmgroup-teste-38493491`), pelo que o nome da base de dados e/ou o URL é dinâmico.

### Como resolver o nome real da BD:
Executar o helper do framework:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_odoo_resolve_db.ps1 -BaseUrl <staging_url>
```

Ou consultar via `pg_odoo_client_query.ps1`:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_odoo_client_query.ps1 -ProjectKey <project_key> -Purpose client_test -Model ir.module.module -Method search_read -Domain '[["name","=","<nome_modulo>"]]' -Fields name,state,latest_version
```

---

## 4. Passo 3: Autenticação e Verificação do Módulo

Utilizar as credenciais do utilizador obtidas por `pg_odoo_credentials.resolver_credenciais_pg()`.

```python
import sys, os, json, urllib.request, time

sys.path.insert(0, os.path.abspath('.pg_framework/scripts'))
import pg_odoo_credentials

cred = pg_odoo_credentials.resolver_credenciais_pg()
login = cred['login']
api_key = cred['api_key']

def rpc(url, db, service, method, args, retries=5):
    data = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'service': service, 'method': method, 'args': args}}).encode('utf-8')
    req = urllib.request.Request(url.rstrip('/') + '/jsonrpc', data=data, headers={'Content-Type': 'application/json'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('error'):
                    raise Exception(res['error'])
                return res.get('result')
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = (attempt + 1) * 3
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded on 429")

# 1. Autenticar no serviço common
uid = rpc(staging_url, db, 'common', 'authenticate', [db, login, api_key, {}])

# 2. Confirmar versão e estado do módulo alterado
mod = rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'ir.module.module', 'search_read', [[['name', '=', '<nome_do_modulo>']]], {'fields': ['name', 'state', 'latest_version']}])
assert mod and mod[0]['state'] == 'installed', f"Módulo não instalado: {mod}"
```

---

## 5. Passo 4: Criação de Cenários e Execução de Métodos Reais

### Regras Obrigatórias de Integridade:
- **Multi-empresa (`_check_company`):** Todos os registos relacionados num documento (Parceiro, Tipo de Operação, Armazém, Localização de Origem, Localização de Destino de Clientes) devem pertencer à mesma empresa (`company_id`) ou ter `company_id = False`.
- **Campos Standard vs Odoo 19:** Em Odoo 19, modelos como `stock.move` usam `description_picking` e `product_id`, sem campo `name`.
- **Acionar Métodos do Negócio:** Nunca forçar escrita direta de estados (`write({'state': 'done'})`). Acionar sempre os botões/métodos reais:
  - `action_confirm()`
  - Wizards e preenchimento de dependências (ex.: pesagem, lotes, embalamento)
  - `button_validate()` ou `action_done()`

### Exemplo de Cenário Misto:
```python
# Criar documento de teste
doc_id = rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'stock.picking', 'create', [{
    'partner_id': partner_id,
    'picking_type_id': picking_type_id,
    'company_id': company_id,
    'location_id': loc_src,
    'location_dest_id': loc_dest,
    'move_ids': [
        [0, 0, {'product_id': prod_a, 'product_uom_qty': 10, 'product_uom': uom_unit, 'location_id': loc_src, 'location_dest_id': loc_dest, 'company_id': company_id}],
        [0, 0, {'product_id': prod_b, 'product_uom_qty': 4.5, 'product_uom': uom_kg, 'location_id': loc_src, 'location_dest_id': loc_dest, 'company_id': company_id}],
    ]
}]])

# Confirmar
rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'stock.picking', 'action_confirm', [[doc_id]]])

# Validar
rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'stock.picking', 'button_validate', [[doc_id]]])
```

---

## 6. Passo 5: Asserções e Prova de Validação (Hard Gate)

Após a validação, reler os registos por RPC e efetuar asserções explícitas:

```python
doc = rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'stock.picking', 'read', [[doc_id]], {'fields': ['state', 'move_ids']}])[0]
assert doc['state'] == 'done', f"Documento em estado incorreto: {doc['state']}"

moves = rpc(staging_url, db, 'object', 'execute_kw', [db, uid, api_key, 'stock.move', 'read', [doc['move_ids']], {'fields': ['product_id', 'product_uom_qty', 'quantity', 'state', 'picked']}])
for m in moves:
    assert m['state'] == 'done', f"Linha {m['product_id'][1]} não está done: {m['state']}"
    assert m['quantity'] > 0, f"Linha {m['product_id'][1]} com quantidade zero/cancelada: {m['quantity']}"
    assert m['picked'] is True, f"Linha {m['product_id'][1]} sem picked ativo"

print(">>> TESTE EM STAGING CONCLUÍDO COM 100% DE SUCESSO! <<<")
```

---

## 7. Passo 6: Promoção para a `main`

**Apenas e só após a conclusão com sucesso comprovado do script de teste RPC em staging:**

1. Checkout da `main`:
   ```powershell
   git checkout main
   git pull origin main
   ```
2. Cherry-pick do commit validado:
   ```powershell
   git cherry-pick <commit_hash>
   ```
3. Push para a branch de produção:
   ```powershell
   git push origin main
   ```
4. Regresso imediato à branch `brodoo`:
   ```powershell
   git checkout brodoo
   ```

---

## 8. Checklist Obrigatória Pré-Promoção

Antes de executar qualquer comando em direção à `main`, verificar:
- [ ] Commit efetuado e enviado para a branch `brodoo`.
- [ ] Commit enviado para a branch de staging correspondente (`teste` ou `brodoo`).
- [ ] Base de dados de staging reconstruída no Odoo.sh com a versão atualizada do módulo.
- [ ] Script Python de teste RPC executado sem erros contra o staging.
- [ ] Asserções funcionais validadas a 100%.
- [ ] Evidência da execução exibida na resposta ao utilizador.
