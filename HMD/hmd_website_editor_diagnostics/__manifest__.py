{
    "name": "HMD Website Editor Diagnostics",
    "summary": "Endpoint admin para diagnosticar porque uma pagina do website nao e editavel.",
    "version": "18.0.1.0.0",
    "category": "Website",
    "author": "HMD / Parametro Global",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "views/templates.xml",
    ],
    "description": """
HMD Website Editor Diagnostics (HMD)
====================================

a) Objetivo de negocio
----------------------
Quando o publisher abre uma pagina do website e o botao "Edit" nao
aparece (ou aparece mas nao funciona), o diagnostico envolve correr
varias queries (groups do user, website.page records, views inherit
de website.layout, ir.assets com CSS escondendo barras, custom code
no website, modulos custom hmd_/pg_, etc.). Este modulo expoe um
endpoint backoffice que faz tudo isso de uma vez e mostra um
relatorio HTML com tudo o que e suspeito.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `website`.
- Acesso ao backoffice (utilizador interno).

c) Como funciona (tecnico)
--------------------------
1. `controllers/main.py`:
   - Constantes:
     - `STANDARD_VIEW_MODULE_PREFIXES`: prefixos de modulos
       considerados "standard" (excluidos do diagnostico).
     - `SUSPICIOUS_ARCH_PATTERNS` / `SUSPICIOUS_TEXT_PATTERNS`:
       padroes que sugerem CSS/JS a esconder a barra de edicao
       (`display:none`, `o_main_navbar`, `o_we_`, `pointer-events:
       none`, etc.).
   - Funcoes helper: normaliza paths, faz `has_group()` defensivo,
     extrai XML IDs, prepara previews.
   - Endpoints (a ler completos em controllers/main.py):
     - `/hmd/website_editor_diagnostic` (HTML)
     - `/hmd/website_editor_diagnostic.json` (JSON)
   - Para uma URL alvo agregam:
       a) website ativo, dominio;
       b) grupos do utilizador (com state);
       c) `website.page` candidatos para a URL;
       d) inherits ativos de `website.layout` para o site
          (filtrando standards);
       e) inherits da page view especifica;
       f) custom code do website (CSS/JS guardado em campos);
       g) views QWeb so na BD (sem arch_fs) com padroes
          suspeitos;
       h) `ir.asset` com paths/contents suspeitos +
          attachments associados;
       i) modulos instalados com prefixo `hmd_` ou `pg_` com
          `website` nas dependencias.
   - O relatorio HTML (views/templates.xml) renderiza em formato
     tabelar com avisos destacados.

2. Template QWeb `report` (`views/templates.xml`): HTML responsive
   com tabelas por seccao. Ver o ficheiro para o layout completo.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_website_editor_diagnostics`.
2. Como admin/publisher, navegar no browser para
   `https://<dominio>/hmd/website_editor_diagnostic?target=/<rota>`.
3. Ler o relatorio:
   - "Likely Issues" - resumo do que parece estar a esconder o
     editor.
   - "Relevant Group Flags" - confirma se o user pertence aos
     grupos certos (`website.group_website_publisher`,
     `website.group_website_designer`).
   - "Website Groups In This Database" - lista todos os grupos do
     app website e quais o user tem.
   - "Matched website.page Records" - paginas para a URL.
   - "Active Inherits On website.layout" - extensoes do layout
     (filtrando standards).
   - "Active Inherits On Matched Page View" - extensoes a propria
     pagina.
   - "Website Custom Code Fields" - HTML/CSS/JS injetado via
     website settings.
   - "Suspicious DB-Only qWeb Views" - views so na BD com padroes
     suspeitos.
   - "Suspicious ir.asset Records" + "Resolved Asset Attachment
      Contents" - assets que podem estar a esconder o editor.
   - "Installed Custom Website Modules" - hmd_/pg_ modules
     potencialmente conflitantes.

e) Exemplo pratico
------------------
Publisher reporta: /shop/sofa-lara nao deixa editar.
Admin abre /hmd/website_editor_diagnostic?target=/shop/sofa-lara.
O relatorio mostra um `ir.asset` com codigo `.o_we_ { display:
none; }` -> esta a esconder a barra do editor. Solucao: remover ou
ajustar esse asset.

Outro caso: o relatorio mostra que o user nao pertence a
`website.group_website_publisher` -> dar acesso.

f) FAQ / Resolucao de problemas
-------------------------------
P: Acesso negado ao endpoint. Porque?
R: O endpoint exige user interno (auth='user'). Garantir login.

P: "Likely Issues" vazio mas nao consigo editar.
R: Verificar manualmente as outras tabelas. O detetor de "likely"
   e heuristico - cobre os casos mais comuns mas nao todos.

P: O JSON output expoe segredos?
R: Inclui previews de CSS/JS de attachments. Nao usar em ambiente
   publico sem auth - mas como exige user interno, esta protegido.

g) Pontos de atencao / avisos
-----------------------------
- O detetor de padroes suspeitos e heuristico. Falsos positivos
  esperados (ex.: theme custom legitimo).
- O endpoint le `ir.attachment.datas` para inspecionar contents -
  custo memoria em assets grandes; aplicar limite quando o
  asset for > Xkb.
- Em upgrade Odoo 19, validar que os helpers (`has_group`,
  `get_external_id`) continuam a existir com a mesma assinatura.
""",
    "installable": True,
    "application": False,
}
