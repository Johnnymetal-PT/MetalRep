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

$productViewRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'read' -ArgumentsJson '[[5892],["arch_db"]]'
$productViews = @(Convert-ResultArray $productViewRaw)
if ($productViews.Count -ne 1) { throw 'Website product view 5892 was not found.' }
$productArch = [string]$productViews[0].arch_db

$ctaCss = @'
   .pg-product-geox #product_full_spec { display: none !important; }
   .pg-product-geox .o_wsale_product_details_content_section_contact:has(#contact_us_wrapper.d-none) { display: none; }
   .pg-product-geox #o_wsale_cta_wrapper { width: 100%; margin-bottom: 1.25rem !important; }
   .pg-product-geox #add_to_cart_wrap { width: 100%; flex-basis: 100%; }
   .pg-product-geox #add_to_cart { display: inline-flex; width: 100%; min-height: 3.5rem; flex: 1 0 100%; align-items: center; justify-content: center; border: 1px solid #111; border-radius: 0; background: #111; color: #fff; font-size: .82rem; font-weight: 700; letter-spacing: .055em; line-height: 1; text-transform: uppercase; transition: background-color .18s ease, border-color .18s ease, color .18s ease; }
   .pg-product-geox #add_to_cart .fa-shopping-cart { display: none; }
   .pg-product-geox #add_to_cart:hover, .pg-product-geox #add_to_cart:focus { border-color: #2b2b2b; background: #2b2b2b; color: #fff; }
   .pg-product-geox #add_to_cart:focus-visible { outline: 2px solid #111; outline-offset: 3px; box-shadow: none; }
   .pg-product-geox #add_to_cart.disabled, .pg-product-geox #add_to_cart[aria-disabled='true'] { border-color: #b8b8b8; background: #b8b8b8; color: #fff; opacity: 1; }
'@

$legacyCtaPattern = '(?s)   \.pg-product-geox #add_to_cart \{.*?\}\s*   \.pg-product-geox #add_to_cart:hover \{.*?\}'
$refinedCtaPattern = '(?s)   \.pg-product-geox #product_full_spec \{.*?\.pg-product-geox #add_to_cart\.disabled, \.pg-product-geox #add_to_cart\[aria-disabled=''true''\] \{.*?\}'
if ([regex]::IsMatch($productArch, $refinedCtaPattern)) {
    $updatedArch = [regex]::Replace($productArch, $refinedCtaPattern, $ctaCss.TrimEnd(), 1)
}
else {
    $updatedArch = [regex]::Replace($productArch, $legacyCtaPattern, $ctaCss.TrimEnd(), 1)
}
$aftercarePattern = '(?s)\s*<xpath expr="//div\[@id=''product_full_description''\]" position="after">\s*<section class="pg-aftercare">.*?</xpath>'
$updatedArch = [regex]::Replace($updatedArch, $aftercarePattern, '', 1)
if (-not $updatedArch.Contains('#product_full_spec { display: none !important; }') -or -not $updatedArch.Contains('#add_to_cart_wrap { width: 100%')) {
    throw 'Could not apply the specification and add-to-cart styles.'
}

$productViewValues = [ordered]@{ arch_db = $updatedArch }
$productViewValuesJson = ConvertTo-Json -InputObject $productViewValues -Depth 20 -Compress
[void](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'write' -ArgumentsJson ('[[5892],' + $productViewValuesJson + ']'))

# This website-specific copy enabled the specifications accordion near the CTA.
# Keep variant selectors intact and disable only the repeated informational block.
[void](Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'write' -ArgumentsJson '[[5893],{"active":false}]')

$ctaCheckRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'read' -ArgumentsJson '[[5892],["arch_db"]]'
$ctaCheck = @(Convert-ResultArray $ctaCheckRaw)[0]
if (-not ([string]$ctaCheck.arch_db).Contains('#product_full_spec { display: none !important; }') -or -not ([string]$ctaCheck.arch_db).Contains('.o_wsale_product_details_content_section_contact:has(#contact_us_wrapper.d-none) { display: none; }') -or -not ([string]$ctaCheck.arch_db).Contains('#add_to_cart_wrap { width: 100%') -or ([string]$ctaCheck.arch_db).Contains('background: var(--pg-accent)') -or ([string]$ctaCheck.arch_db).Contains('<section class="pg-aftercare">')) {
    throw 'The refined add-to-cart styles did not validate.'
}

$accordionCheckRaw = Invoke-ClientOdoo -Model 'ir.ui.view' -Method 'read' -ArgumentsJson '[[5893],["active","website_id","key"]]'
$accordionCheck = @(Convert-ResultArray $accordionCheckRaw)[0]
if ($accordionCheck.active -or [int]$accordionCheck.website_id[0] -ne 7 -or [string]$accordionCheck.key -ne 'website_sale_comparison.accordion_specs_item') {
    throw 'The website-specific specifications accordion was not disabled.'
}

Write-Output 'OK website=7 bottom_specifications=hidden accordion_specifications=disabled aftercare=removed product_view=5892 cta=refined'
