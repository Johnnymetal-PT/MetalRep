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

    if ($LASTEXITCODE -ne 0) {
        throw "Odoo call failed: $Model.$Method"
    }
    return ($raw | Out-String).Trim()
}

$demoDescription = @'
<div class="pg-product-story">
  <section class="container py-5">
    <div class="row align-items-center g-0 bg-dark text-white">
      <div class="col-lg-7">
        <img src="/web/image/product.template/17/image_1920" alt="Base Roll-Line Dance - imagem de demonstra&#231;&#227;o" class="img-fluid w-100" style="min-height:420px;object-fit:cover;" loading="lazy"/>
      </div>
      <div class="col-lg-5 p-4 p-lg-5">
        <p class="small text-uppercase mb-3" style="letter-spacing:.12em;color:#f2cf00;">Conte&#250;do de demonstra&#231;&#227;o</p>
        <h2 class="display-6 mb-4">Precis&#227;o em cada movimento</h2>
        <p class="mb-0">A Base Roll-Line Dance foi desenvolvida para oferecer controlo, fluidez e estabilidade nas disciplinas de dan&#231;a. Este bloco demonstra como uma fotografia editorial e uma mensagem curta podem apresentar o benef&#237;cio principal do produto.</p>
      </div>
    </div>
  </section>

  <section class="container py-5 border-top">
    <div class="row g-5">
      <div class="col-lg-6">
        <p class="small text-uppercase text-muted mb-2" style="letter-spacing:.1em;">Descri&#231;&#227;o</p>
        <h2 class="h3 mb-3">Base Roll-Line Dance</h2>
        <p>A Roll-Line Dance &#233; uma base desenvolvida especificamente para as disciplinas de dan&#231;a, oferecendo elevada precis&#227;o nos edges, excelente manobrabilidade e estabilidade nos movimentos mais exigentes.</p>
        <p class="mb-0">A constru&#231;&#227;o em Ergal, combinada com o sistema de regula&#231;&#227;o Click-Action e bases diferenciadas para o p&#233; direito e esquerdo, proporciona uma resposta precisa e consistente.</p>
      </div>
      <div class="col-lg-6">
        <p class="small text-uppercase text-muted mb-2" style="letter-spacing:.1em;">Caracter&#237;sticas</p>
        <ul class="list-unstyled border-top mb-0">
          <li class="py-3 border-bottom d-flex gap-3"><span aria-hidden="true">&#10003;</span><span>Estrutura leve e resistente em Ergal.</span></li>
          <li class="py-3 border-bottom d-flex gap-3"><span aria-hidden="true">&#10003;</span><span>Sistema Click-Action para uma regula&#231;&#227;o precisa.</span></li>
          <li class="py-3 border-bottom d-flex gap-3"><span aria-hidden="true">&#10003;</span><span>Geometria otimizada para dan&#231;a e movimentos t&#233;cnicos.</span></li>
          <li class="py-3 border-bottom d-flex gap-3"><span aria-hidden="true">&#10003;</span><span>Bases espec&#237;ficas para o p&#233; direito e esquerdo.</span></li>
        </ul>
      </div>
    </div>
  </section>

  <section class="py-5" style="background:#f4f4f2;">
    <div class="container">
      <div class="row g-5">
        <div class="col-lg-5">
          <p class="small text-uppercase text-muted mb-2" style="letter-spacing:.1em;">Materiais</p>
          <h2 class="h3 mb-3">Constru&#231;&#227;o</h2>
          <p class="mb-2"><strong>Estrutura:</strong> liga de alum&#237;nio Ergal.</p>
          <p class="mb-2"><strong>Componentes:</strong> a&#231;o e elast&#243;meros t&#233;cnicos.</p>
          <p class="small text-muted mb-0">Texto provis&#243;rio para valida&#231;&#227;o visual. Confirmar a composi&#231;&#227;o final com a ficha t&#233;cnica do fabricante.</p>
        </div>
        <div class="col-lg-7">
          <p class="small text-uppercase text-muted mb-2" style="letter-spacing:.1em;">Tecnologia</p>
          <h2 class="h3 mb-3">Sistema Click-Action</h2>
          <p>O bloco de tecnologia permite explicar, com mais espa&#231;o, o funcionamento e as vantagens de cada componente. Nesta vers&#227;o de demonstra&#231;&#227;o destaca-se a possibilidade de afinar a resposta da base de forma progressiva e repet&#237;vel.</p>
          <a href="/contactus" class="btn btn-outline-dark rounded-0 mt-2">Pedir aconselhamento</a>
        </div>
      </div>
    </div>
  </section>
</div>
'@

$accessoryRaw = Invoke-ClientOdoo -Model 'product.product' -Method 'search_read' -ArgumentsJson '[[["product_tmpl_id","in",[52,65,75]]],["id","product_tmpl_id","name"]]'
$accessoryParsed = $accessoryRaw | ConvertFrom-Json
$accessoryVariants = @($accessoryParsed | ForEach-Object { $_ })
$accessoryVariantIds = @(
    foreach ($templateId in @(52, 65, 75)) {
        $match = $accessoryVariants | Where-Object { [int]$_.product_tmpl_id[0] -eq $templateId } | Select-Object -First 1
        if (-not $match) { throw "No product variant found for accessory template $templateId." }
        [int]$match.id
    }
)

$productValues = [ordered]@{
    website_description = $demoDescription
    alternative_product_ids = @(, @(6, 0, @(5, 7, 9, 15)))
    accessory_product_ids = @(, @(6, 0, $accessoryVariantIds))
}

[string]$productValuesJson = ConvertTo-Json -InputObject $productValues -Depth 30 -Compress
[void](Invoke-ClientOdoo -Model 'product.template' -Method 'write' -ArgumentsJson ('[[17],' + $productValuesJson + ']'))

$parentRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'search_read' -ArgumentsJson '[[["key","=","website_sale.alternative_products"]],["id","key","name"]]'
$parentParsed = $parentRaw | ConvertFrom-Json
$parentViews = @($parentParsed | ForEach-Object { $_ })
if (-not $parentViews -or @($parentViews).Count -ne 1) {
    throw 'Could not resolve website_sale.alternative_products uniquely.'
}
$parentId = [int]@($parentViews)[0].id

$viewKey = 'pg_chapatim.alternative_products_heading_geox'
$viewRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'search_read' -ArgumentsJson '[[["key","=","pg_chapatim.alternative_products_heading_geox"],["website_id","=",7]],["id","key","active"]]'
$viewParsed = $viewRaw | ConvertFrom-Json
$existingViews = @($viewParsed | ForEach-Object { $_ })

$viewArch = @'
<data>
  <xpath expr="//section[contains(@class, 'o_wsale_alternative_products')]//h4" position="replace">
    <h2 class="h3 mb-2">Tamb&#233;m poder&#225; gostar de</h2>
  </xpath>
  <xpath expr="//section[contains(@class, 'o_wsale_alternative_products')]//p[contains(@class, 'lead')]" position="replace">
    <p class="text-muted mb-0">Outras bases Roll-Line selecionadas para comparar.</p>
  </xpath>
</data>
'@

$viewValues = @{
    name = 'Chapatim - heading de produtos relacionados'
    key = $viewKey
    type = 'qweb'
    mode = 'extension'
    inherit_id = $parentId
    website_id = 7
    priority = 99
    active = $true
    arch_db = $viewArch
}

if ($existingViews.Count -gt 0 -and $existingViews[0]) {
    [string]$viewValuesJson = ConvertTo-Json -InputObject $viewValues -Depth 30 -Compress
    [void](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'write' -ArgumentsJson ('[[' + [int]$existingViews[0].id + '],' + $viewValuesJson + ']'))
    $viewId = [int]$existingViews[0].id
}
else {
    [string]$viewValuesJson = ConvertTo-Json -InputObject $viewValues -Depth 30 -Compress
    $viewId = [int](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'create' -ArgumentsJson ('[' + $viewValuesJson + ']'))
}

$productCheckRaw = Invoke-ClientOdoo -Model 'product.template' -Method 'read' -ArgumentsJson '[[17],["website_description","alternative_product_ids","accessory_product_ids"]]'
$productCheckParsed = $productCheckRaw | ConvertFrom-Json
$productCheck = @($productCheckParsed | ForEach-Object { $_ })[0]
if (-not ([string]$productCheck.website_description).Contains('pg-product-story')) {
    throw 'The editorial product content was not persisted.'
}
if (@($productCheck.alternative_product_ids).Count -ne 4) {
    throw 'The product recommendation set was not persisted.'
}
if (@($productCheck.accessory_product_ids).Count -ne 3) {
    throw 'The accessory set was not persisted.'
}

$viewCheckRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'read' -ArgumentsJson ('[[' + $viewId + '],["active","website_id","arch_db"]]')
$viewCheckParsed = $viewCheckRaw | ConvertFrom-Json
$viewCheck = @($viewCheckParsed | ForEach-Object { $_ })[0]
if (-not $viewCheck.active -or [int]$viewCheck.website_id[0] -ne 7 -or -not ([string]$viewCheck.arch_db).Contains('o_wsale_alternative_products')) {
    throw 'The website-specific recommendation heading view did not validate.'
}

Write-Output "OK validated product=17 related_templates=[5,7,9,15] accessory_variants=[$($accessoryVariantIds -join ',')] view=$viewId website=7"
