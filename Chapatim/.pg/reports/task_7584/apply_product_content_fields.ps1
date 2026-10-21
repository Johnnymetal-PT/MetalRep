$ErrorActionPreference = 'Stop'

$repoPath = 'C:\Users\Utilizador\Desktop\Repos\Chapatim'
$queryScript = Join-Path $repoPath '.pg_framework\scripts\pg_odoo_client_query.ps1'

function Invoke-ClientOdoo {
    param(
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$ArgumentsJson
    )
    $raw = & $queryScript `
        -ProjectKey 'odoo-chapatim' `
        -Purpose 'production' `
        -Model $Model `
        -Method $Method `
        -ArgsJson $ArgumentsJson
    if ($LASTEXITCODE -ne 0) { throw "Odoo call failed: $Model.$Method" }
    return ($raw | Out-String).Trim()
}

function Convert-ResultArray([string]$Raw) {
    $parsed = $Raw | ConvertFrom-Json
    return @($parsed | ForEach-Object { $_ })
}

$productModelId = 392
$labelTitle = 'T' + [char]0x00ED + 'tulo editorial'
$labelDescription = 'Descri' + [char]0x00E7 + [char]0x00E3 + 'o'
$labelCharacteristics = 'Caracter' + [char]0x00ED + 'sticas'
$editorialTitle = 'Precis' + [char]0x00E3 + 'o em cada movimento'
$fieldSpecs = @(
    [ordered]@{ name = 'x_chapatim_editorial_image'; field_description = 'Imagem editorial'; ttype = 'binary' },
    [ordered]@{ name = 'x_chapatim_editorial_title'; field_description = $labelTitle; ttype = 'char' },
    [ordered]@{ name = 'x_chapatim_editorial_text'; field_description = 'Texto editorial'; ttype = 'html' },
    [ordered]@{ name = 'x_chapatim_page_description'; field_description = $labelDescription; ttype = 'html' },
    [ordered]@{ name = 'x_chapatim_characteristics'; field_description = $labelCharacteristics; ttype = 'html' },
    [ordered]@{ name = 'x_chapatim_materials'; field_description = 'Materiais'; ttype = 'html' },
    [ordered]@{ name = 'x_chapatim_technologies'; field_description = 'Tecnologias'; ttype = 'html' }
)

foreach ($spec in $fieldSpecs) {
    $domainJson = '[[["model","=","product.template"],["name","=","' + $spec.name + '"]],["id","name","ttype"]]'
    $existing = @(Convert-ResultArray (Invoke-ClientOdoo -Model 'ir.model.fields' -Method 'search_read' -ArgumentsJson $domainJson))
    if ($existing.Count -eq 0) {
        $values = [ordered]@{
            model_id = $productModelId
            name = $spec.name
            field_description = $spec.field_description
            ttype = $spec.ttype
            state = 'manual'
            copied = $true
        }
        $valuesJson = ConvertTo-Json -InputObject $values -Depth 20 -Compress
        [void](Invoke-ClientOdoo -Model 'ir.model.fields' -Method 'create' -ArgumentsJson ('[' + $valuesJson + ']'))
    }
    elseif ([string]$existing[0].ttype -ne [string]$spec.ttype) {
        throw "Field $($spec.name) exists with type $($existing[0].ttype), expected $($spec.ttype)."
    }
    else {
        $fieldLabelValues = [ordered]@{ field_description = $spec.field_description }
        $fieldLabelJson = ConvertTo-Json -InputObject $fieldLabelValues -Depth 10 -Compress
        [void](Invoke-ClientOdoo -Model 'ir.model.fields' -Method 'write' -ArgumentsJson ('[[' + [int]$existing[0].id + '],' + $fieldLabelJson + ']'))
    }
}

$backendViewKey = 'pg_chapatim.product_page_content_backend'
$backendViewArch = @'
<data>
  <xpath expr="//page[@name='sales']" position="after">
    <page string="Conte&#250;do da p&#225;gina" name="chapatim_product_page_content">
      <group string="Bloco editorial" col="2">
        <group>
          <field name="x_chapatim_editorial_image" widget="image" options="{'size': [0, 420]}"/>
          <field name="x_chapatim_editorial_title"/>
        </group>
        <group>
          <field name="x_chapatim_editorial_text" widget="html" nolabel="1" colspan="2"/>
        </group>
      </group>
      <separator string="Descri&#231;&#227;o"/>
      <field name="x_chapatim_page_description" widget="html" nolabel="1" colspan="2"/>
      <separator string="Caracter&#237;sticas"/>
      <field name="x_chapatim_characteristics" widget="html" nolabel="1" colspan="2"/>
      <separator string="Materiais"/>
      <field name="x_chapatim_materials" widget="html" nolabel="1" colspan="2"/>
      <separator string="Tecnologias"/>
      <field name="x_chapatim_technologies" widget="html" nolabel="1" colspan="2"/>
    </page>
  </xpath>
</data>
'@

$backendViewRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'search_read' -ArgumentsJson '[[["key","=","pg_chapatim.product_page_content_backend"]],["id","key"]]'
$backendViews = @(Convert-ResultArray $backendViewRaw)
$backendViewValues = [ordered]@{
    name = 'Chapatim - conteudo especifico da pagina de produto'
    key = $backendViewKey
    type = 'form'
    model = 'product.template'
    mode = 'extension'
    inherit_id = 2540
    priority = 99
    active = $true
    arch_db = $backendViewArch
}
$backendValuesJson = ConvertTo-Json -InputObject $backendViewValues -Depth 30 -Compress
if ($backendViews.Count -gt 0) {
    $backendViewId = [int]$backendViews[0].id
    [void](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'write' -ArgumentsJson ('[[' + $backendViewId + '],' + $backendValuesJson + ']'))
}
else {
    $backendViewId = [int](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'create' -ArgumentsJson ('[' + $backendValuesJson + ']'))
}

$websiteViewRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'read' -ArgumentsJson '[[5892],["arch_db"]]'
$websiteViews = @(Convert-ResultArray $websiteViewRaw)
if ($websiteViews.Count -ne 1) { throw 'Website product view 5892 was not found.' }
$websiteArch = [string]$websiteViews[0].arch_db

$extraCss = @'
   .pg-product-geox .pg-editorial { max-width: 1320px; margin: 1rem auto 0; padding: 0 1.5rem 3.5rem; }
   .pg-product-geox .pg-editorial-grid { display: grid; grid-template-columns: 1.35fr 1fr; min-height: 420px; background: var(--pg-dark); color: #fff; }
   .pg-product-geox .pg-editorial-media img { width: 100%; height: 100%; min-height: 420px; object-fit: cover; }
   .pg-product-geox .pg-editorial-copy { display: flex; flex-direction: column; justify-content: center; padding: 3rem; }
   .pg-product-geox .pg-editorial-copy h2 { color: #fff; font-size: clamp(1.75rem, 3vw, 2.7rem); text-transform: none; }
   .pg-product-geox .pg-editorial-copy p { color: #ddd9e1; }
   .pg-product-geox .pg-content-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4rem; }
   .pg-product-geox .pg-content-panel { padding-top: 1rem; }
   .pg-product-geox .pg-content-panel h2 { margin-bottom: 1.25rem; }
   .pg-product-geox .pg-content-panel ul { padding-left: 1.15rem; }
   .pg-product-geox .pg-content-panel li { margin-bottom: .7rem; }
   .pg-product-geox .pg-technical-content { padding-block: 3.5rem; background: #f4f4f2; }
   .pg-product-geox .pg-technical-content .pg-product-description { padding-block: 0; }
'@
if (-not $websiteArch.Contains('.pg-product-geox .pg-editorial {')) {
    $websiteArch = $websiteArch.Replace('   @media (max-width: 991.98px)', $extraCss + "`n   @media (max-width: 991.98px)")
}
$mobileExtras = ' .pg-product-geox .pg-editorial-grid, .pg-product-geox .pg-content-grid { grid-template-columns: 1fr; } .pg-product-geox .pg-editorial-copy { padding: 2rem; }'
$websiteArch = $websiteArch.Replace($mobileExtras, '')
$websiteArch = $websiteArch.Replace('.pg-product-geox .pg-aftercare-grid { grid-template-columns: 1fr; gap: 1.5rem; }', '.pg-product-geox .pg-aftercare-grid { grid-template-columns: 1fr; gap: 1.5rem; }' + $mobileExtras)

$contentBlock = @'
 <xpath expr="//div[@id='product_full_description']" position="before">
  <section t-if="product.x_chapatim_editorial_image or product.x_chapatim_editorial_title or product.x_chapatim_editorial_text" class="pg-editorial">
   <div class="pg-editorial-grid">
    <div class="pg-editorial-media">
     <img t-if="product.x_chapatim_editorial_image" t-att-src="request.website.image_url(product, 'x_chapatim_editorial_image')" t-att-alt="product.x_chapatim_editorial_title or product.name" loading="lazy"/>
     <img t-else="" t-att-src="request.website.image_url(product, 'image_1920')" t-att-alt="product.name" loading="lazy"/>
    </div>
    <div class="pg-editorial-copy">
     <h2 t-if="product.x_chapatim_editorial_title" t-field="product.x_chapatim_editorial_title"/>
     <div t-if="product.x_chapatim_editorial_text" t-field="product.x_chapatim_editorial_text"/>
    </div>
   </div>
  </section>
  <section t-if="product.x_chapatim_page_description or product.x_chapatim_characteristics or (not product.x_chapatim_page_description and product.description_ecommerce)" class="pg-product-description">
   <div class="pg-content-grid">
    <div t-if="product.x_chapatim_page_description or product.description_ecommerce" class="pg-content-panel">
     <h2>Descri&#231;&#227;o</h2>
     <div t-if="product.x_chapatim_page_description" t-field="product.x_chapatim_page_description"/>
     <div t-else="" t-field="product.description_ecommerce"/>
    </div>
    <div t-if="product.x_chapatim_characteristics" class="pg-content-panel">
     <h2>Caracter&#237;sticas</h2>
     <div t-field="product.x_chapatim_characteristics"/>
    </div>
   </div>
  </section>
  <section t-if="product.x_chapatim_materials or product.x_chapatim_technologies" class="pg-technical-content">
   <div class="pg-product-description">
    <div class="pg-content-grid">
     <div t-if="product.x_chapatim_materials" class="pg-content-panel">
      <h2>Materiais</h2>
      <div t-field="product.x_chapatim_materials"/>
     </div>
     <div t-if="product.x_chapatim_technologies" class="pg-content-panel">
      <h2>Tecnologias</h2>
      <div t-field="product.x_chapatim_technologies"/>
     </div>
    </div>
   </div>
  </section>
  <section t-if="not (product.x_chapatim_page_description or product.x_chapatim_characteristics or product.x_chapatim_materials or product.x_chapatim_technologies or product.description_ecommerce) and request.env.user._is_admin()" class="pg-product-description">
   <div class="alert alert-warning"><strong>Conte&#250;do em falta.</strong> Preencher o separador Conte&#250;do da p&#225;gina no produto.</div>
  </section>
 </xpath>
'@

$descriptionPattern = '(?s) <xpath expr="//div\[@id=''product_full_description''\]" position="before">.*?</xpath>'
$updatedWebsiteArch = [regex]::Replace($websiteArch, $descriptionPattern, $contentBlock, 1)
if ($updatedWebsiteArch -eq $websiteArch -or -not $updatedWebsiteArch.Contains('x_chapatim_characteristics')) {
    throw 'Could not replace the product content block in website view 5892.'
}
$websiteViewValues = [ordered]@{ arch_db = $updatedWebsiteArch; name = 'Chapatim - pagina de produto editorial' }
$websiteValuesJson = ConvertTo-Json -InputObject $websiteViewValues -Depth 30 -Compress
[void](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'write' -ArgumentsJson ('[[5892],' + $websiteValuesJson + ']'))

$productRaw = Invoke-ClientOdoo -Model 'product.template' -Method 'read' -ArgumentsJson '[[17],["image_1920","description_ecommerce"]]'
$productRows = @(Convert-ResultArray $productRaw)
if ($productRows.Count -ne 1) { throw 'Product 17 was not found.' }
$product = $productRows[0]

$productValues = [ordered]@{
    x_chapatim_editorial_image = $product.image_1920
    x_chapatim_editorial_title = $editorialTitle
    x_chapatim_editorial_text = '<p class="small text-uppercase" style="letter-spacing:.12em;color:#f2cf00;">Conte&#250;do de demonstra&#231;&#227;o</p><p>A Base Roll-Line Dance foi desenvolvida para oferecer controlo, fluidez e estabilidade nas disciplinas de dan&#231;a. Este texto pode ser alterado individualmente no backoffice do produto.</p>'
    x_chapatim_page_description = $product.description_ecommerce
    x_chapatim_characteristics = '<ul><li>Estrutura leve e resistente em Ergal.</li><li>Sistema Click-Action para uma regula&#231;&#227;o precisa.</li><li>Geometria otimizada para dan&#231;a e movimentos t&#233;cnicos.</li><li>Bases espec&#237;ficas para o p&#233; direito e esquerdo.</li></ul>'
    x_chapatim_materials = '<p><strong>Estrutura:</strong> liga de alum&#237;nio Ergal.</p><p><strong>Componentes:</strong> a&#231;o e elast&#243;meros t&#233;cnicos.</p><p class="small text-muted">Texto provis&#243;rio. Confirmar a composi&#231;&#227;o final com a ficha t&#233;cnica do fabricante.</p>'
    x_chapatim_technologies = '<h3 class="h4">Sistema Click-Action</h3><p>Conte&#250;do de demonstra&#231;&#227;o para explicar o funcionamento e as vantagens de cada componente. Substituir pela informa&#231;&#227;o t&#233;cnica validada pelo fabricante.</p>'
    website_description = $false
}
$productValuesJson = ConvertTo-Json -InputObject $productValues -Depth 30 -Compress
[void](Invoke-ClientOdoo -Model 'product.template' -Method 'write' -ArgumentsJson ('[[17],' + $productValuesJson + ']'))

$validationFields = ($fieldSpecs | ForEach-Object { '"' + $_.name + '"' }) -join ','
$validationRaw = Invoke-ClientOdoo -Model 'product.template' -Method 'read' -ArgumentsJson ('[[17],[' + $validationFields + ',"website_description"]]')
$validation = @(Convert-ResultArray $validationRaw)[0]
foreach ($spec in $fieldSpecs) {
    if (-not $validation.($spec.name)) { throw "Product 17 field $($spec.name) is empty." }
}
if ($validation.website_description) { throw 'Legacy website_description was not cleared after migration.' }

$backendCheckRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'get_combined_arch' -ArgumentsJson ('[[' + $backendViewId + ']]')
if (-not $backendCheckRaw.Contains('x_chapatim_technologies')) { throw 'Backend combined form does not contain the new product fields.' }

Write-Output "OK product content fields=7 backend_view=$backendViewId website_view=5892 product=17 migrated"
