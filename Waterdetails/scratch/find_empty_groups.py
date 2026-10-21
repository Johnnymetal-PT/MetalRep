from lxml import etree

xml_path = r"C:\Projetos\Waterdetails\docs\SAF-T Faturação VIRGIN DETAILS, LDA (01_08_2026 a 31_08_2026).xml"

xml_doc = etree.parse(xml_path)
root = xml_doc.getroot()
ns_uri = root.nsmap.get(None, '')
ns_map = {'ns': ns_uri} if ns_uri else {}
prefix = 'ns:' if ns_uri else ''

products = root.xpath(f'//{prefix}MasterFiles/{prefix}Product', namespaces=ns_map)
print(f"Total Products in MasterFiles: {len(products)}")

for i, p in enumerate(products, 1):
    pcode = p.find(f'{prefix}ProductCode', namespaces=ns_map)
    pgroup = p.find(f'{prefix}ProductGroup', namespaces=ns_map)
    pdesc = p.find(f'{prefix}ProductDescription', namespaces=ns_map)
    
    code = pcode.text if pcode is not None else ''
    group_elem = pgroup
    group_text = pgroup.text if pgroup is not None else None
    desc = pdesc.text if pdesc is not None else ''
    
    # In XML, <ProductGroup></ProductGroup> has group_text == None or ''
    # If the tag is present but has no text, group_text is None
    if group_elem is not None and (group_text is None or len(group_text.strip()) == 0):
        print(f"-> Product[{i}] (Linha {p.sourceline}): Code='{code}', Desc='{desc}', Group Tag='{etree.tostring(group_elem).decode().strip()}'")

print("\nPrimeiros 5 produtos do XML:")
for i in range(1, 6):
    p = products[i-1]
    pcode = p.find(f'{prefix}ProductCode', namespaces=ns_map)
    pgroup = p.find(f'{prefix}ProductGroup', namespaces=ns_map)
    pdesc = p.find(f'{prefix}ProductDescription', namespaces=ns_map)
    code = pcode.text if pcode is not None else ''
    group_elem = pgroup
    desc = pdesc.text if pdesc is not None else ''
    print(f"Product[{i}] (Linha {p.sourceline}): Code='{code}', Desc='{desc}', Group Tag='{etree.tostring(group_elem).decode().strip() if group_elem is not None else 'NO TAG'}'")
