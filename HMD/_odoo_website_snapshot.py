"""Fotografia SO-LEITURA do estado dos websites.

Serve para provar, antes e depois de um deploy de tema, que os websites que
nao eram alvo ficaram intactos: compara-se a impressao digital de cada site.

Uso:
    python3 _odoo_website_snapshot.py antes.json
    # ... deploy ...
    python3 _odoo_website_snapshot.py depois.json
    python3 _odoo_website_snapshot.py --diff antes.json depois.json
"""
import xmlrpc.client, json, hashlib, sys

def carregar_env(caminho='data_local/odoo_hmd.env'):
    env = {}
    for linha in open(caminho, encoding='utf-8'):
        if '=' in linha and not linha.strip().startswith('#'):
            k, v = linha.strip().split('=', 1)
            env[k] = v
    return env

def fotografar(destino):
    env = carregar_env()
    URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
    uid = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True).authenticate(DB, LOGIN, KEY, {})
    if not uid:
        sys.exit('Autenticacao falhou: confirmar ODOO_LOGIN/ODOO_KEY em data_local/odoo_hmd.env')
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

    def rpc(modelo, metodo, *args, **kw):
        assert metodo in {'search_read', 'read', 'search_count'}, metodo
        return models.execute_kw(DB, uid, KEY, modelo, metodo, list(args), kw)

    snap = {}
    for w in rpc('website', 'search_read', [], fields=['name', 'domain', 'theme_id', 'sequence']):
        wid = w['id']
        vistas = rpc('ir.ui.view', 'search_read', [('website_id', '=', wid)], fields=['key', 'active'], order='key')
        paginas = rpc('website.page', 'search_read', [('website_id', '=', wid)], fields=['url', 'is_published'], order='url')
        menus = rpc('website.menu', 'search_read', [('website_id', '=', wid)], fields=['name', 'url', 'sequence'], order='sequence,id')
        corpo = {
            'nome': w['name'], 'dominio': w['domain'],
            'tema': w['theme_id'] and w['theme_id'][1] or None,
            'n_vistas': len(vistas), 'n_paginas': len(paginas), 'n_menus': len(menus),
            'vistas': [f"{v['key']}:{int(v['active'])}" for v in vistas],
            'paginas': [f"{p['url']}:{int(p['is_published'])}" for p in paginas],
            'menus': [f"{x['name']}|{x['url']}" for x in menus],
        }
        corpo['impressao_digital'] = hashlib.sha256(
            json.dumps(corpo, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        snap[str(wid)] = corpo

    json.dump(snap, open(destino, 'w'), indent=1, ensure_ascii=False)
    for wid, b in sorted(snap.items(), key=lambda kv: int(kv[0])):
        print(f"  site {wid}  {b['nome']:<20} tema={str(b['tema']):<16} "
              f"vistas={b['n_vistas']:<4} paginas={b['n_paginas']:<3} menus={b['n_menus']:<3} "
              f"impressao={b['impressao_digital']}")
    print('\nguardado em', destino)

def comparar(antes, depois):
    a = json.load(open(antes)); d = json.load(open(depois))
    for wid in sorted(set(a) | set(d), key=int):
        va, vd = a.get(wid), d.get(wid)
        if va is None:
            print(f"  site {wid}: NOVO ({vd['nome']})"); continue
        if vd is None:
            print(f"  site {wid}: DESAPARECEU ({va['nome']})"); continue
        if va['impressao_digital'] == vd['impressao_digital']:
            print(f"  site {wid} {va['nome']:<20} INTACTO ({va['impressao_digital']})")
        else:
            print(f"  site {wid} {va['nome']:<20} ALTERADO")
            print(f"      tema   {va['tema']} -> {vd['tema']}")
            print(f"      vistas {va['n_vistas']} -> {vd['n_vistas']}   "
                  f"paginas {va['n_paginas']} -> {vd['n_paginas']}   "
                  f"menus {va['n_menus']} -> {vd['n_menus']}")
            for campo in ('vistas', 'paginas', 'menus'):
                novos = set(vd[campo]) - set(va[campo])
                perdidos = set(va[campo]) - set(vd[campo])
                if novos:
                    print(f"      + {len(novos)} {campo}: {sorted(novos)[:6]}")
                if perdidos:
                    print(f"      - {len(perdidos)} {campo}: {sorted(perdidos)[:6]}")

if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--diff':
        comparar(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2:
        fotografar(sys.argv[1])
    else:
        sys.exit(__doc__)
