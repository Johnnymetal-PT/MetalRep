import openpyxl, re, unicodedata
from collections import Counter

def norm(s):
    if s is None: return ''
    s = str(s).strip()
    if s == '': return ''
    s = re.sub(r'^ESSANI\S*\s*\|\s*', '', s, flags=re.I)
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode('ascii')
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

def load(fn, sheet, ref_col, cols):
    wb = openpyxl.load_workbook(fn, read_only=True, data_only=True)
    ws = wb[sheet]; it = ws.iter_rows(values_only=True); next(it)
    out = {}
    for r in it:
        ref = r[ref_col]
        if ref is None: continue
        try: key = int(str(ref).strip())
        except: continue
        out[key] = {k: r[i] for k,i in cols.items()}
    wb.close(); return out

odoo = load('lista_clientes_odoo.xlsx','Sheet1',1,{'nome':2,'vendedor':12,'nrvendedor':13,'respint':16})
phc  = load('lista_clientes_phc.xlsx','lista_clientes_phc',0,{'nome':1,'vendedor':12,'nrvendedor':11,'respinterno':20})
bkp  = load('backup_phc_20251117.xlsx','clientes',1,{'nome':2,'vendedor':11})

# tabela vendedor: nrvendedor -> nomes encontrados em cada origem
def gather_vendor_table():
    table = {}
    for ref,r in odoo.items():
        nr = r.get('nrvendedor')
        if nr is None: continue
        table.setdefault(nr,{'odoo':set(),'phc':set()})['odoo'].add(str(r.get('vendedor') or '').strip())
    for ref,r in phc.items():
        nr = r.get('nrvendedor')
        if nr is None: continue
        table.setdefault(nr,{'odoo':set(),'phc':set()})['phc'].add(str(r.get('vendedor') or '').strip())
    return table

vt = gather_vendor_table()
print('== Mapa nrvendedor -> nome em cada sistema ==')
for nr in sorted(vt.keys(), key=lambda x: (x is None, x)):
    o = sorted(vt[nr]['odoo']); p = sorted(vt[nr]['phc'])
    print(f'  nr={nr!r:>6}  odoo={o}  phc={p}')

# comparacao por nrvendedor (ID inteiro)
common = set(odoo) & set(phc)
diff_id = 0; same_id = 0; nrv_pairs = Counter()
for ref in common:
    a = odoo[ref].get('nrvendedor'); b = phc[ref].get('nrvendedor')
    if a is None or b is None: continue
    if a == b: same_id += 1
    else:
        diff_id += 1
        nrv_pairs[(a,b)] += 1
print(f'\n== Comparacao Odoo vs PHC actual por nrvendedor (ID): {same_id} iguais, {diff_id} diferentes ==')
print('Top transicoes (odoo_nrv -> phc_nrv):')
for (a,b),n in nrv_pairs.most_common(15):
    print(f'  {a} -> {b} : {n} clientes')

# 11 alteracoes PHC actual vs backup, com detalhe
print('\n== PHC backup -> PHC actual: alteracoes de vendedor (refs presentes nos 2) ==')
both = set(phc) & set(bkp)
changes = []
for ref in sorted(both):
    vp = phc[ref].get('vendedor'); vb = bkp[ref].get('vendedor')
    if norm(vp) != norm(vb) and norm(vp) and norm(vb):
        changes.append((ref, phc[ref].get('nome'), vb, vp))
for ref, nome, vb, vp in changes:
    print(f'  ref={ref:>5}  {nome[:50]!s:<52}  backup={vb!r}  ->  actual={vp!r}')
print(f'  total: {len(changes)}')

# respinterno: top mismatches
print('\n== Responsavel interno: top mismatches Odoo vs PHC actual ==')
mm = Counter()
for ref in common:
    ro = norm(odoo[ref].get('respint')); rp = norm(phc[ref].get('respinterno'))
    if ro != rp and (ro or rp):
        mm[(ro or '<vazio>', rp or '<vazio>')] += 1
for (a,b), n in mm.most_common(20):
    print(f'  odoo={a!r:<25} phc={b!r:<25} : {n}')
