$ErrorActionPreference = 'Stop'

$repoPath = 'C:\Users\Utilizador\Desktop\Repos\Chapatim'
$queryScript = Join-Path $repoPath '.pg_framework\scripts\pg_odoo_client_query.ps1'

function Invoke-ClientOdoo {
    param([string]$Method, [string]$ArgumentsJson)
    $raw = & $queryScript `
        -ProjectKey 'odoo-chapatim' `
        -Purpose 'production' `
        -Model 'ir.ui.view' `
        -Method $Method `
        -ArgsJson $ArgumentsJson
    if ($LASTEXITCODE -ne 0) { throw "ir.ui.view.$Method failed" }
    return ($raw | Out-String).Trim()
}

$arch = @'
<data>
  <xpath expr="//header" position="before">
    <style>
      /* Chapatim: align desktop mega menus with the responsive header container. */
      @media (min-width: 992px) and (max-width: 1199.98px) {
        header nav.navbar .o_mega_menu.dropdown-menu {
          width: 960px;
          max-width: 960px;
          left: 0 !important;
          right: 0 !important;
          margin-inline: auto !important;
        }
      }
      @media (min-width: 1200px) {
        header nav.navbar .o_mega_menu.dropdown-menu {
          width: 100%;
          max-width: 1440px;
          left: 0 !important;
          right: 0 !important;
          margin-inline: auto !important;
        }
      }
    </style>
  </xpath>
</data>
'@

$values = [ordered]@{
    name = 'Chapatim - largura responsiva do mega menu'
    active = $true
    arch_db = $arch
}
$valuesJson = ConvertTo-Json -InputObject $values -Depth 20 -Compress
[void](Invoke-ClientOdoo -Method 'write' -ArgumentsJson ('[[5909],' + $valuesJson + ']'))

$checkRaw = Invoke-ClientOdoo -Method 'read' -ArgumentsJson '[[5909],["active","website_id","arch_db"]]'
$check = $checkRaw | ConvertFrom-Json
if (-not $check.active -or [int]$check.website_id[0] -ne 7) {
    throw 'Mega-menu width view is not active on website 7.'
}
if (-not ([string]$check.arch_db).Contains('max-width: 1199.98px') -or -not ([string]$check.arch_db).Contains('width: 960px') -or -not ([string]$check.arch_db).Contains('max-width: 1440px')) {
    throw 'Responsive mega-menu rules were not persisted.'
}

Write-Output 'OK view=5909 website=7 breakpoints=960/1440'
