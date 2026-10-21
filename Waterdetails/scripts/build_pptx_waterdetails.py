"""
Gera o PPTX de orçamento para Virgin Details, Lda
Baseado no template visual do deck existente (outro cliente).
Preserva layout, cores e logo; substitui apenas o conteúdo.
"""
import copy
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pptx import Presentation
from lxml import etree

SRC = "c:/Projetos/Waterdetails/docs/WaterDetails.pptx"
DST = "c:/Projetos/Waterdetails/docs/WaterDetails_Orcamento_v1.pptx"
DST_TMP = "c:/Projetos/Waterdetails/docs/WaterDetails_Orcamento_v1_new.pptx"

# ---------------------------------------------------------------------------
# Mapas de substituição por slide (índice 0-based)
# Chave = texto completo do shape (concatenação de todos os parágrafos).
# Valor = novo texto a aplicar.
# \xa0 = non-breaking space tal como está no ficheiro original.
# ---------------------------------------------------------------------------

S0 = {  # Slide 1 — Capa
    "Mercado Abastecedor do Porto": "Virgin Details, Lda",
    "Proposta comercial para implementação Odoo, localização PT+, serviços de arranque e opção de Controlo de Acessos / TimeCloud.":
        "Proposta de implementação Odoo Enterprise — Fase 1: Faturação. Cobrindo configuração inicial, localização PT (l10n_pt), vendas, faturação certificada AT e migração de dados PHC GO.",
    "33\xa0891,40 €": "5\xa0400 €",
    "Total 1.º ano estimado s/IVA": "Serviços Fase 1",
    "240h": "7\xa0752 €",
    "Serviços de implementação": "Total 1.º ano s/IVA ⚠",
    "7\xa0258,00 €": "5\xa0340 €",
    "Recorrência anual": "Recorrência anual ⚠",
    "Versão comercial · 22/05/2026 · válido até 19/06/2026 – REF S01705":
        "Versão 1.0 · 25/05/2026 · válido até 20/06/2026",
}

S1 = {  # Slide 2 — Resumo executivo
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "Implementação Odoo 19 Enterprise com PT+, serviços de levantamento, parametrização, formação e suporte de arranque. O Controlo de Acessos / TimeCloud surge como componente adicional identificada no orçamento.":
        "Implementação Odoo Enterprise (saas~19.3) — Fase 1: Faturação. Cobre configuração inicial, localização PT (l10n_pt), contactos, vendas, faturação certificada AT, financeiro e migração de dados PHC GO. 5 utilizadores, arranque em ~6 semanas.",
    # Caixas de métrica
    "20\xa0236,40 €": "5\xa0400 €",
    "Odoo principal": "Serviços Fase 1",
    "13\xa0655,00 €": "7\xa0752 €",
    "Acessos/TimeCloud": "Total 1.º ano s/IVA ⚠",
    "30d": "5\xa0340 €",
    "Dias estimados": "Recorrência anual ⚠",
    # Caixa de decisão financeira (direita)
    "Total 1.º ano: 33\xa0891,40 €": "Total 1.º ano: 7\xa0752 € s/IVA ⚠",
    "Recorrência anual: 7\xa0258,00 €": "Recorrência: 5\xa0340 €/ano s/IVA ⚠",
    # Dois parágrafos sem separador — starts-with apanha
    "Parâmetros-base: 10 utilizadores, 12 meses, desconto Odoo 20%Este valor tem uma taxa de aproximação de 70% face aos requisitos levantados.":
        "⚠ Licenciamento Odoo (1\xa0824 €) + plugin AT (528 €): valores placeholder — confirmar Stefano Biglieri",
    "Este valor tem uma taxa de aproximação de 70% face aos requisitos levantados.":
        "Fase 2 (Operação Comercial): ~4\xa0360 € s/IVA (indicativo)",
}

S2 = {  # Slide 3 — Âmbito
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "Componentes principais da fase inicial": "Módulos e entregas da Fase 1 — Faturação",
    "Base Odoo + PT+": "Base Odoo + l10n_pt",
    "Ambiente Odoo 19 Enterprise, módulos standard, localização/certificação portuguesa e preparação metodológica.":
        "Odoo Enterprise saas~19.3. Localização PT (l10n_pt), SAF-T, configuração inicial (5 utilizadores, grupos de acesso, e-mail).",
    "Dados mestre": "Contactos e Produtos",
    "Contactos, operadores, fornecedores, utentes, produtos, serviços, taxas, listas de preços e impostos.":
        "Clientes, fornecedores, produtos e serviços. Importação a partir de PHC GO e Excel.",
    "Faturação e portal": "Vendas e Faturação",
    "Subscrições, faturação recorrente, faturação manual, POS, portal, helpdesk, documentos e compras.":
        "Orçamentos, encomendas, faturas, notas de crédito e faturação certificada AT.",
    "Operação interna": "Financeiro l10n_pt",
    "RH, frota, manutenção, perfis de utilizador, reporting standard e suporte de arranque.":
        "Plano de contas PT, IVA, SAF-T, plugin AT, condições de pagamento e reconciliação bancária.",
    "Migração inicial": "Migração PHC GO",
    "Templates e apoio à importação de dados selecionados, saldos e arranque controlado.":
        "Importação de produtos, clientes e saldos em aberto a partir de PHC GO.",
    "A app/mapa do mercado abastecedor está excluída deste orçamento principal e foi tratada em ficheiro separado.":
        "CRM, Compras, Inventário e Logística são Fase 2 (Operação Comercial). Migração Pipedrive é Fase 2.",
    "Integrações técnicas com SCA, FileDoc, DIMEP, POS/hardware e migração histórica integral ficam sujeitas a validação própria.":
        "CRM, Pipedrive, Compras, Inventário e Logística excluídos da Fase 1. Expansão (BoM, Multiempresa, Analítica) reservada para Fase 3.",
}

S3 = {  # Slide 4 — Investimento Fase 1
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "Serviços, software e recorrência anual": "Serviços, software e recorrência — Fase 1",
    "Serviços": "Serviços",  # manter label intacto
    "15\xa0800,00 € · 240h / 30 dias estimados em 3 meses.":
        "5.400 € · 80h / 10 dias estimados em ~6 semanas.",
    "Licenciamento": "Licenciamento",
    "2\xa0900,40 € no 1.º ano · 2\xa0688,00 €/ano recorrente · 10 utilizadores com desconto Odoo de 20% no 1º ano. Proposta diretamente da Odoo.":
        "1.824 € no 1.º ano · 2.280 €/ano recorrente ⚠ · valores placeholder — confirmar c/ Stefano Biglieri.",
    "PT+ / plugins": "Plugin AT",
    "1\xa0536,00 € no 1.º ano · 1\xa0920,00 €/ano recorrente · faturação, contabilidade e salários.":
        "528 € no 1.º ano · 660 €/ano recorrente ⚠ · valor placeholder — confirmar c/ Stefano Biglieri.",
    "Suporte": "Suporte",
    "2\xa0400,00 €/ano em contrato separado pós go-live.":
        "2.400 €/ano em contrato separado pós go-live.",
    "Total Odoo": "Total Fase 1",
    "20\xa0236,40 € no 1.º ano · 7\xa0008,00 €/ano recorrente.":
        "7.752 € no 1.º ano · 5.340 €/ano recorrente ⚠",
    "Formação fiscal acrescentada no Excel: RH/salários, contabilidade e imobilizado. Valores s/IVA conforme folha Resumo.":
        "⚠ Licenciamento Odoo + plugin AT: valores placeholder — confirmar Stefano Biglieri. Valores s/IVA.",
    "Odoo principal → 20\xa0236,40 € no 1.º ano → 7\xa0008,00 €/ano recorrente":
        "Serviços Fase 1: 5.400 € · Total 1.º ano: 7.752 € s/IVA ⚠",
}

S4 = {  # Slide 5 — Fases Seguintes (era Controlo de Acessos)
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "4. Controlo de Acessos / TimeCloud": "4. Fases Seguintes — Operação e Expansão",
    "Cotação S01686": "Valores indicativos · a confirmar após go-live Fase 1",
    "Software": "Fase 2 — Operação Comercial",
    "TimeCloud RH: 2\xa0900,00 € · licença base uma só vez.":
        "4.360 € · 8 dias · CRM, Pipedrive [POR VALIDAR], Compras, Inventário.",
    "Alojamento": "Fase 3 — Expansão",
    "Cloud MMC: 250,00 €/ano · atualizações e redundâncias.":
        "4.680 € · 9 dias [POR VALIDAR] · BoM, Multiempresa (Starplast SRLE), Analítica.",
    "Hardware": "Módulos Adicionais",
    "6\xa0480,00 € · 18 terminais M-Bio II + 200 cartões.":
        "[POR VALIDAR] · Sign, Barcode, Documents, Helpdesk.",
    "Serviços": "Total estimado",
    "4\xa0025,00 € · instalação, configuração API e testes.":
        "~9.040 € s/IVA (excl. módulos adicionais [POR VALIDAR])",
    "Total acessos": "Nota",
    "13\xa0655,00 € s/IVA · inclui 250,00 € de recorrência anual.":
        "Início de cada fase após aceite e go-live da fase anterior. Valores s/IVA.",
    "Opção ativa": "Arranque",
    "OPÇÃO A RFID considerada no Excel. OPÇÃO B LPR está a zero e funciona como alternativa. Monitores e PCs existentes ficam sujeitos a revisão técnica.":
        "Fase 1 (Faturação) → go-live → Fase 2 (Operação) → go-live → Fase 3 (Expansão).",
    "Não inclui cabos de rede/energia, carpintaria, serralharia ou eletricista.":
        "Cada fase tem orçamento e proposta própria.",
}

S5 = {  # Slide 6 — Plano de trabalho
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "Distribuição indicativa em 9 semanas": "6 semanas (Fase 1 — 10 dias)",
    "Set-up": "Kick-off + Configuração",
    "10h · 1,25d": "1,5d",
    "Levantamento requisitos": "Contactos e Produtos",
    "24h · 3d": "1d",
    "Parametrização áreas mestre": "Vendas e Faturação",
    "128h · 16d": "2d",
    "Migração de dados": "Financeiro l10n_pt",
    "16h · 2d": "2d",
    "Relatórios": "Migração PHC GO",
    "8h · 1d": "2d",
    "Perfis utilizador": "Testes faturação",
    "6h · 0,75d": "1d",
    "Arranque e formação": "Formação + Arranque",
    "40h · 5d": "1d",
    "Gestão de projeto": "Gestão Projeto",
    "Total: 240 horas / 30 dias · pico de esforço nas semanas 5 a 7":
        "Total Fase 1: 10 dias · ~6 semanas · início 2-3 semanas após assinatura",
}

S6 = {  # Slide 7 — Pressupostos
    "orcamento_map | Odoo 19": "waterdetails | Odoo 19",
    "10 utilizadores, 12 meses, desconto Odoo de 20% e taxas horárias conforme folha artigos.":
        "5 utilizadores · Odoo SH cloud · l10n_pt · Fase 1 sem custom · interlocutor disponível 4h/semana.",
    "Dados de operadores, produtos, taxas e saldos revistos pelo cliente antes de migração.":
        "Cliente fornece produtos, clientes e saldos em aberto de PHC GO em Excel limpo antes do início da migração.",
    "App/mapa, migração histórica integral FileDoc, integrações técnicas e relatórios custom fora do âmbito inicial.":
        "CRM, Pipedrive, Compras, Inventário, Logística excluídos da Fase 1. Fase 2 e Fase 3 têm propostas próprias.",
    "Custom development sujeito a validação posterior de fit-gap e aprovação específica.":
        "Plugin AT licenciado antes do arranque do módulo financeiro. Licenciamento Odoo confirmar c/ Stefano Biglieri.",
    "Aprovação até 19/06/2026, nomeação de SPOC, agenda de levantamento e kick-off.":
        "Aprovação até 20/06/2026. Nomeação de SPOC, agenda de levantamento e kick-off.",
    "Aprovação → SPOC → validação de dados/licenças → kick-off → fit-gap standard/Studio/custom":
        "Aprovação → SPOC → dados PHC GO → plugin AT → kick-off → go-live faturação",
}

SLIDE_MAPS = [S0, S1, S2, S3, S4, S5, S6]


def set_tf_text(tf, new_text):
    """
    Substitui todo o conteúdo do text_frame por new_text,
    preservando a formatação do primeiro run do primeiro parágrafo.
    """
    if not tf.paragraphs:
        return
    first_para = tf.paragraphs[0]
    ref_run_xml = None
    if first_para.runs:
        ref_run_xml = copy.deepcopy(first_para.runs[0]._r)

    ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    p_elems = tf._txBody.findall(f"{ns}p")

    # Remover todos os parágrafos excepto o primeiro
    for p in p_elems[1:]:
        tf._txBody.remove(p)

    # Limpar runs do primeiro parágrafo
    p0 = p_elems[0]
    for r in p0.findall(f"{ns}r"):
        p0.remove(r)

    # Inserir novo run
    if ref_run_xml is not None:
        new_r = copy.deepcopy(ref_run_xml)
        t_elem = new_r.find(f"{ns}t")
        if t_elem is None:
            t_elem = etree.SubElement(new_r, f"{ns}t")
        t_elem.text = new_text
        p0.append(new_r)
    else:
        new_r = etree.SubElement(p0, f"{ns}r")
        t_elem = etree.SubElement(new_r, f"{ns}t")
        t_elem.text = new_text


def replace_in_shape(shape, rep_map):
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    full_text = "".join(p.text for p in tf.paragraphs).strip()

    # Exact match
    if full_text in rep_map:
        new_val = rep_map[full_text]
        if new_val != full_text:
            set_tf_text(tf, new_val)
        return

    # Starts-with match (cobre shapes com múltiplos parágrafos)
    for key, val in rep_map.items():
        if full_text.startswith(key):
            set_tf_text(tf, val)
            return

    # Run-a-run para textos curtos simples
    for para in tf.paragraphs:
        for run in para.runs:
            t = run.text.strip()
            if t and t in rep_map and rep_map[t] != t:
                run.text = rep_map[t]


def main():
    prs = Presentation(SRC)
    for si, slide in enumerate(prs.slides):
        rep_map = SLIDE_MAPS[si] if si < len(SLIDE_MAPS) else {}
        for shape in slide.shapes:
            replace_in_shape(shape, rep_map)
            if shape.shape_type == 6:  # GROUP
                for s in shape.shapes:
                    replace_in_shape(s, rep_map)
    import os, shutil
    prs.save(DST_TMP)
    try:
        if os.path.exists(DST):
            os.remove(DST)
        shutil.move(DST_TMP, DST)
        print(f"Guardado: {DST}")
    except PermissionError:
        print(f"Ficheiro destino bloqueado. Guardado como: {DST_TMP}")
        print("Fechar o PowerPoint e renomear manualmente, ou usar o ficheiro _tmp.")


if __name__ == "__main__":
    main()
