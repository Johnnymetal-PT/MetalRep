from lxml import etree

xml_path = r"C:\Projetos\Waterdetails\docs\SAF-T Faturação VIRGIN DETAILS, LDA (01_08_2026 a 31_08_2026).xml"

xml_doc = etree.parse(xml_path)
root = xml_doc.getroot()

print("A procurar todos os nós no XML com texto vazio ou só espaços...")
empty_nodes = []
for elem in root.iter():
    # Ignore container elements that have child elements
    if len(elem) == 0:
        if elem.text is None or len(elem.text.strip()) == 0:
            tag_name = etree.QName(elem.tag).localname
            parent_tag = etree.QName(elem.getparent().tag).localname if elem.getparent() is not None else ''
            ancestors = [etree.QName(a.tag).localname for a in elem.iterancestors()]
            ancestors.reverse()
            path = '/' + '/'.join(ancestors) + '/' + tag_name
            empty_nodes.append((elem.sourceline, path, tag_name, elem.text))

print(f"Total de nós vazios encontrados no XML: {len(empty_nodes)}")
for line, path, tag, val in empty_nodes:
    print(f"Linha {line:4d} | Tag: {tag:20s} | Caminho: {path}")
