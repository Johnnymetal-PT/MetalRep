from lxml import etree

xml_path = r"C:\Projetos\Waterdetails\docs\SAF-T Faturação VIRGIN DETAILS, LDA (01_08_2026 a 31_08_2026).xml"

xml_doc = etree.parse(xml_path)
root = xml_doc.getroot()
ns_uri = root.nsmap.get(None, '')
ns_map = {'ns': ns_uri} if ns_uri else {}
prefix = 'ns:' if ns_uri else ''

products = root.xpath(f'//{prefix}MasterFiles/{prefix}Product', namespaces=ns_map)
print(f"Total Products in MasterFiles: {len(products)}")

invalid_products = []
for i, p in enumerate(products, 1):
    ptype = p.find(f'{prefix}ProductType', namespaces=ns_map)
    pcode = p.find(f'{prefix}ProductCode', namespaces=ns_map)
    pgroup = p.find(f'{prefix}ProductGroup', namespaces=ns_map)
    pdesc = p.find(f'{prefix}ProductDescription', namespaces=ns_map)
    pnum = p.find(f'{prefix}ProductNumberCode', namespaces=ns_map)
    
    ptype_text = ptype.text if ptype is not None else ''
    pcode_text = pcode.text if pcode is not None else ''
    pgroup_text = pgroup.text if pgroup is not None else None
    pdesc_text = pdesc.text if pdesc is not None else ''
    pnum_text = pnum.text if pnum is not None else ''
    
    issues = []
    if pgroup is not None and (pgroup.text is None or len(pgroup.text.strip()) == 0):
        issues.append(f"ProductGroup vazio (tag existe mas valor está vazio)")
    if pdesc is None or len(pdesc_text.strip()) == 0:
        issues.append("ProductDescription vazio")
    if pcode is None or len(pcode_text.strip()) == 0:
        issues.append("ProductCode vazio")
    if pnum is None or len(pnum_text.strip()) == 0:
        issues.append("ProductNumberCode vazio")
        
    if issues or pgroup_text is None:
        invalid_products.append({
            'index': i,
            'line': p.sourceline,
            'type': ptype_text,
            'code': pcode_text,
            'group': pgroup_text,
            'desc': pdesc_text,
            'num': pnum_text,
            'issues': issues
        })

print(f"\nProdutos com tags vazias / anomalias encontradas ({len(invalid_products)}):")
for ip in invalid_products:
    print(f"\n[Product #{ip['index']}] Linha XML: {ip['line']}")
    print(f"  Código: {ip['code']}")
    print(f"  Descrição: {ip['desc']}")
    print(f"  Grupo (ProductGroup): {repr(ip['group'])}")
    print(f"  Problemas: {ip['issues']}")

# Also let's inspect all products 1..len(products) to print them completely
print("\n" + "="*80)
print("LISTA COMPLETA DOS PRODUTOS NO FICHEIRO XML:")
for i, p in enumerate(products, 1):
    pcode = p.find(f'{prefix}ProductCode', namespaces=ns_map)
    pgroup = p.find(f'{prefix}ProductGroup', namespaces=ns_map)
    pdesc = p.find(f'{prefix}ProductDescription', namespaces=ns_map)
    code = pcode.text if pcode is not None else ''
    group = pgroup.text if pgroup is not None else 'SEM TAG ProductGroup'
    desc = pdesc.text if pdesc is not None else ''
    print(f"Product[{i:2d}] | Linha {p.sourceline:4d} | Code: {code:25s} | Group: {repr(group):30s} | Desc: {desc}")
