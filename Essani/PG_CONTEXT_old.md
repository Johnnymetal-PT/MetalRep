# PG_CONTEXT - Current Session

Source of truth for the current development state in this repository.

## Active Odoo Core

Odoo Version: 19.0
Database Version: 19.0
Reference path: `vendor/odoo_core/odoo/addons`

## Client Request / Objective

Stabilize 3D model support in Essani across backend product forms and website product pages.

## Rules and Constraints

- Mandatory prefix: `pg_`
- Do not modify Odoo core (`vendor/odoo_core` is read-only)
- Consult Odoo core patterns before proposing technical implementation

## Current Status

- `pg_3d_viewer` is active with a backend `model_viewer` field widget (OWL template + JS).
- `pg_product_model_viewer` adds product 3D fields and previewability logic.
- `pg_3d_ecommerce` now renders a `Visualizador 3D` trigger button and opens the model in a popup modal on website product pages (fullscreen still supported).
- Recent milestone (2026-02-09): backend template loading fixed and upload fallback for non-previewable formats improved.
- Custom modules detected without `pg_` prefix: `website_product_visibility`, `calendar_event_map_location`.
- Module icon standardization is now applied across all custom modules using the `pg_category_visibility_filter` icon asset.
- `pg_website_hide_unavailable_variant` now uses an Odoo 19-compatible standalone variants template plus frontend logic that hides impossible attribute values on initial page load and after variant changes.
- `pg_category_visibility_filter` now reuses `website_product_visibility` as its data source and filters website public categories from the products already allowed by `website.sale_product_domain()`.
- `website_product_visibility` now uses an Odoo 19-compatible Website Settings inheritance anchor in `res.config.settings`.
- `pg_crm_activity_report_highlight` now provides backend row highlighting for completed entries in the CRM activity analysis list view.
- `pg_crm_default_prospects` now makes the CRM app icon open the prospects/leads action directly instead of falling through to the default opportunities pipeline.
- `pg_product_update` now hardens Drive-based product reruns by serializing attribute/value/line creation, preferring canonical attribute records by normalized name, and merging duplicate product attribute lines when they already exist.
- `pg_product_update` now opens a live backend dashboard when a Drive import starts, showing phase, progress, queue counts, current item, elapsed time, and last error instead of leaving the user with only the generic Odoo loading indicator.
- `pg_product_update` now also exposes an `Import Jobs` stat button on the product form as a reliable fallback entry point to the latest/running import job, and the bound server action now correctly returns its action payload.
- `pg_product_update` now commits the newly created Drive job before returning and the product-form stat button targets the latest running job's live dashboard first, to avoid landing on the previously closed job record.
- `pg_product_update` now prioritizes queued pending imports before continuing deeper discovery, so a large discovery queue no longer starves actual product processing once importable items have already been found.
- `pg_web_attach_pdf_view` now prioritizes native `product.public.category.image_1920` and `cover_image` on the `/categorias` page, with fallback to legacy `product.category.cat_image_1` and `cat_image_2` only when the website-category images are empty.

## Decisions Made

- Keep `.fbx` and `.dxf` upload support, but only preview `.glb` and `.gltf` in browser.
- Load `pg_3d_viewer` OWL template in `web.assets_backend` to avoid missing-template runtime errors.
- Reuse core `BinaryField` inheritance pattern for the custom field widget.
- Keep website behavior graceful: show warning when file exists but is not previewable.
- Treat `website_product_visibility` and `calendar_event_map_location` as legacy naming exceptions until a dedicated rename/migration decision is taken.
- On the custom `/categorias` page, prefer native `product.public.category` image fields over name-based lookups into `product.category`.

## Risks / Pending Items

- No server-side conversion pipeline from `.fbx/.dxf` to previewable web formats.
- XPath dependency on `website_sale.product` structure (`#product_documents`) may break with upstream template changes.
- No automated tests yet for widget rendering, website conditions, and fullscreen flow.
- Cross-browser fullscreen behavior still depends on vendor-prefixed API support.
- Naming governance gap: two custom modules do not follow required `pg_` prefix (`website_product_visibility`, `calendar_event_map_location`).
- `pg_website_hide_unavailable_variant` still needs live website validation after asset rebuild because the Odoo 19 frontend patch cannot be executed in this terminal session.
- `pg_category_visibility_filter` still depends functionally on the legacy third-party module `website_product_visibility`, whose data model uses internal product categories (`product.category`) rather than website public categories directly.
- `website_product_visibility` may still contain additional legacy website-sale template assumptions beyond the fixed settings view anchor and should be regression-tested after upgrade.
- `pg_crm_activity_report_highlight` currently highlights all rows with a completion date in the CRM activity report; this matches core behavior because the report is designed for done activities, but should be confirmed against the exact business expectation.
- Historic duplicate `product.attribute` or `product.attribute.value` master records may still exist from older imports; the importer now reuses a canonical record and cleans duplicate product-level lines, but it does not automatically merge master data globally.
- The new import dashboard relies on backend assets loading correctly after module upgrade; a stale asset bundle could leave the old button behavior in place until assets are rebuilt.
- The live dashboard may still not open from the start button until the upgraded backend assets are loaded in the browser, so the stat button fallback should remain available for support/debugging.
- If the browser still has stale assets, the start button may stay on the form, but the stat button should still resolve the latest running job because job creation is now committed before the response returns.
- Jobs can still spend time in discovery when no pending `IMAGENS` folders have been queued yet, but once `pending_count > 0` the runner should now process those items first.
- The custom homepage in `pg_website` still uses legacy `product.category.cat_image_1` and `cat_image_2` matching by name, so category imagery can diverge between homepage and `/categorias` until that page is aligned too.

## Next Steps

- Add manual regression checklist (backend + website + mobile).
- Add automated tests for product fields and website template conditions.
- Confirm user messaging/translations for non-previewable format warnings.
- Validate interaction with product variants in real catalog data.
- Decide whether to keep or rename non-compliant custom modules and define migration impact (manifest names, dependencies, data references).
- Re-test installation/upgrade of `pg_website_hide_unavailable_variant` on Odoo 19, rebuild website assets, and validate that missing combinations are hidden on initial product page load as well as after attribute changes.
- Validate `pg_category_visibility_filter` against real partner/visitor visibility rules and confirm that deriving website public categories from allowed products matches business expectations.
- Re-run `pg_product_update` on products that previously showed duplicate attribute rows and review logs for canonicalization warnings and attribute-line merge events.
- Upgrade `pg_product_update`, rebuild backend assets if needed, and validate that starting an import opens the live dashboard and that the numbers update while cron processes the job.
- Validate that the `Import Jobs` stat button appears on the product form and opens the latest running job or latest finished job even if the live dashboard action has not yet loaded in the browser.
- Validate that starting a fresh job and immediately clicking the stat button opens the new running job rather than the just-closed previous one.
- Validate that a job with both `pending_count > 0` and `scan_remaining_count > 0` now advances `processed_count` on subsequent cron ticks instead of staying visually stuck in discovery.
- Validate `/categorias` with categories that have only `image_1920`, only `cover_image`, both fields, and only legacy `cat_image_1`/`cat_image_2`.
- Upgrade `pg_crm_default_prospects` and validate that clicking the CRM app icon opens the prospects/leads list while the existing pipeline submenu remains available.

## Odoo Core References Consulted (paths)

- `vendor/odoo_core/odoo/addons/web/static/src/views/fields/binary/binary_field.js`
- `vendor/odoo_core/odoo/addons/web/static/src/views/fields/binary/binary_field.xml`
- `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`
- `vendor/odoo_core/odoo/addons/website_sale/views/variant_templates.xml`
- `vendor/odoo_core/odoo/addons/website_sale/controllers/main.py`
- `vendor/odoo_core/odoo/addons/website_sale/models/product_public_category.py`
- `vendor/odoo_core/odoo/addons/website_sale/views/product_public_category_views.xml`
- `vendor/odoo_core/odoo/addons/website_sale/models/website_snippet_filter.py`

## PG Module References (paths)

- `pg_3d_viewer/__manifest__.py`
- `pg_3d_viewer/views/assets.xml`
- `pg_3d_viewer/static/src/js/web_widget_model_viewer.js`
- `pg_3d_viewer/static/src/xml/web_widget_model_viewer.xml`
- `pg_product_model_viewer/models/product.py`
- `pg_product_model_viewer/views/product_views.xml`
- `pg_3d_ecommerce/static/src/js/product_model_viewer.js`
- `pg_3d_ecommerce/views/frontend_templates.xml`

## Non-pg Custom Module References (paths)

- `website_product_visibility`
- `calendar_event_map_location`

---

## Milestones (History)

### Milestone - 3D viewer rollout and stabilization (2026-02-09)

**What changed** - Introduced/updated `pg_3d_viewer`, `pg_product_model_viewer`, and `pg_3d_ecommerce` to support product 3D files in backend and website. Added graceful fallback for non-previewable formats (`.fbx/.dxf`) while keeping upload capability.

**Decisions** - Preview restricted to `.glb/.gltf`; unsupported formats remain storable with warning. Backend OWL template explicitly included in `web.assets_backend`.

**Risks / Pending Items** - No format conversion pipeline; website inheritance points require regression checks after upstream template updates.

**Next steps** - Add automated tests and complete browser/device matrix validation.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/web/static/src/views/fields/binary/binary_field.js`, `vendor/odoo_core/odoo/addons/web/static/src/views/fields/binary/binary_field.xml`, `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`

### Milestone - Project governance/context baseline added (2026-02-12)

**What changed** - Added `AGENTS.md` and initialized `PG_CONTEXT.md` as project governance and persistent-memory files.

**Decisions** - Enforced `pg_` naming and core-consultation workflow in repository guidelines.

**Risks / Pending Items** - Keep context updated at each relevant milestone to avoid drift.

**Next steps** - Continue appending milestone entries before final PR/merge events.

**Odoo Core (refs)** - None (process/governance milestone).

### Milestone - Categorias page now uses native public-category images first (2026-04-21)

**What changed** - Updated `pg_web_attach_pdf_view/views/categories_page.xml` so the custom `/categories` and `/categorias` page uses `product.public.category.image_1920` as the primary image and `product.public.category.cover_image` as the secondary image. When those native website-category fields are empty, the page still falls back to the legacy `product.category.cat_image_1` and `cat_image_2` lookup by name, preserving backward compatibility.

**Decisions** - Followed the Odoo core `website_sale` pattern where `product.public.category` owns both `image_1920` and `cover_image`, and used `request.website.image_url(...)` for those fields. Kept the legacy fallback only for compatibility with existing imported data instead of making a breaking switch.

**Risks / Pending Items** - The fallback still depends on matching `product.public.category.name == product.category.name`, which is fragile. The homepage customization in `pg_website` has not yet been aligned and can still show a different image source than `/categorias`.

**Next steps** - Upgrade `pg_web_attach_pdf_view`, rebuild website assets if needed, and validate cards with all image combinations. Decide whether to align `pg_website` homepage cards to the same native public-category image strategy.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/models/product_public_category.py`, `vendor/odoo_core/odoo/addons/website_sale/views/product_public_category_views.xml`, `vendor/odoo_core/odoo/addons/website_sale/models/website_snippet_filter.py`

### Milestone - CRM app default landing changed to prospects (2026-04-22)

**What changed** - Added a new custom module, `pg_crm_default_prospects`, that updates the existing CRM root menu record so the CRM app icon opens `crm.crm_lead_all_leads` directly. This changes the app landing page from the default opportunities pipeline to the prospects/leads list without modifying Odoo core.

**Decisions** - Followed the core CRM menu/action structure instead of replacing the pipeline action itself. The override is limited to `crm.crm_menu_root`, because core leaves that root menu without an action and the web client therefore lands on the first actionable child (`crm.action_your_pipeline`).

**Risks / Pending Items** - This is a static menu override and still needs live validation in the target database after module upgrade. If the business later wants role-specific landing pages, that would require a more dynamic server-action approach rather than a single menu action.

**Next steps** - Upgrade `pg_crm_default_prospects`, refresh the backend menu cache/session if needed, and confirm the CRM app icon now opens prospects while `Sales > My Pipeline` still opens opportunities.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/crm/views/crm_menu_views.xml`, `vendor/odoo_core/odoo/addons/crm/views/crm_lead_views.xml`, `vendor/odoo_core/odoo/addons/crm/data/ir_action_data.xml`, `vendor/odoo_core/odoo/addons/crm/models/crm_team.py`

### Milestone - Non-pg custom modules and DB version clarified (2026-02-12)

**What changed** - Registered two existing custom modules without `pg_` prefix (`website_product_visibility`, `calendar_event_map_location`) and explicitly documented that the database version is 19.0.

**Decisions** - Keep these modules active as existing exceptions for now; no immediate rename applied.

**Risks / Pending Items** - Prefix inconsistency can create governance and maintenance ambiguity unless normalized later.

**Next steps** - Evaluate a controlled rename/migration plan to align with `pg_` naming policy if required.

**Odoo Core (refs)** - None (context/governance update only).

### Milestone - Website 3D popup trigger (2026-02-20)

**What changed** - Replaced inline website product rendering of `model-viewer` with a trigger button (`Visualizador 3D` + cube icon) that opens a Bootstrap modal popup containing the 3D viewer.

**Decisions** - Kept existing previewability guard (`gltf_3d_model_is_previewable`) and warning flow for non-previewable formats; removed the prior behavior that hid the `product_documents` section when a preview existed.

**Risks / Pending Items** - Modal sizing is currently static (`70vh`), so very small devices may still need UI fine-tuning.

**Next steps** - Validate on mobile Safari/Chrome and confirm desired button placement/styling with business users.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/static/src/xml/website_sale_image_viewer.xml`, `vendor/odoo_core/odoo/addons/website_sale/static/src/js/components/website_sale_image_viewer.js`

### Milestone - 3D popup z-index fix (2026-02-20)

**What changed** - Added module-scoped frontend SCSS to force `pg_3d_ecommerce` modal/viewer layers above website carousel stacking contexts.

**Decisions** - Kept fix isolated to `.o_pg_3d_viewer_modal` and bundled the stylesheet through `web.assets_frontend` to avoid global modal behavior changes.

**Risks / Pending Items** - If external theme CSS sets very high z-index values (`> 20000`), values may need another adjustment.

**Next steps** - Rebuild frontend assets and validate modal layering on affected product pages.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/web/static/lib/bootstrap/scss/_variables.scss`, `vendor/odoo_core/odoo/addons/web/static/lib/bootstrap/scss/_modal.scss`, `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`

### Milestone - Manifest BOM fix (2026-02-20)

**What changed** - Removed UTF-8 BOM from `pg_3d_ecommerce/__manifest__.py`, which was causing Odoo to fail parsing the manifest at line 1.

**Decisions** - Keep manifest files BOM-free (UTF-8 without BOM) to match Odoo core manifest style and avoid invisible-character syntax errors.

**Risks / Pending Items** - Any file rewritten with Windows PowerShell `Set-Content -Encoding UTF8` may reintroduce BOM.

**Next steps** - Keep using UTF-8 no BOM for Python manifests and recheck first bytes when parser errors mention line 1 near an empty token.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/__manifest__.py`

### Milestone - 3D modal reparent fix (2026-02-20)

**What changed** - Added frontend logic in `pg_3d_ecommerce` to move 3D viewer modals (`.o_pg_3d_viewer_modal`) to `document.body` before opening.

**Decisions** - Kept the modal trigger and Bootstrap data API flow, but forced DOM reparenting to avoid nested stacking-context conflicts with product carousel layout.

**Risks / Pending Items** - If external scripts replace product DOM dynamically after widget init, reparenting still depends on click-time targeting (covered by `_onOpenViewer`).

**Next steps** - Rebuild frontend assets and validate layering on desktop/mobile product pages.

### Milestone - Sale order popup for partner comments (2026-04-23)

**What changed** - Added a new custom module, `pg_sale_partner_comment_popup`, that extends `sale.order` with an `@api.onchange('partner_id')`. When a user selects a contact/customer on the sales order and that partner has the `comment` field filled, Odoo now shows a warning popup with the comment content.

**Decisions** - Kept the implementation server-side and minimal by reusing the standard onchange warning mechanism instead of adding custom JavaScript or altering the sale order form view. Converted the partner comment from HTML to plain text before showing it in the popup to avoid raw markup in the message.

**Risks / Pending Items** - `vendor/odoo_core` is empty in this workspace, so the mandatory local validation against the actual Odoo core source could not be completed for this milestone. The popup depends on the standard Odoo onchange warning UX, so it should be validated on a live Odoo 19 form after module upgrade.

**Next steps** - Upgrade/install `pg_sale_partner_comment_popup` in the target database and validate the behavior with contacts that have and do not have a comment, including company/contact variants.

**Odoo Core (refs)** - Unable to consult the required local references because `vendor/odoo_core` is empty in this workspace; implementation follows the standard Odoo `@api.onchange(...)->{'warning': ...}` pattern and should be cross-checked once the core checkout is available locally.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/web/static/lib/bootstrap/js/dist/modal.js`, `vendor/odoo_core/odoo/addons/web/static/lib/bootstrap/scss/_variables.scss`, `vendor/odoo_core/odoo/addons/website_sale/static/src/scss/website_sale.scss`

### Milestone - Product page carousel/docs layout tuning (2026-02-24)

**What changed** - Added frontend CSS overrides in `pg_web_attach_pdf_view/static/src/css/styles.css` to reduce product image carousel width on desktop and left-align the product documents accordion block.

**Decisions** - Kept the fix in module-scoped CSS (no core edits) and targeted existing website sale selectors (`#product_detail`, `#o-carousel-product`, `#product_accordion`) for low-risk UI adjustments.

**Risks / Pending Items** - Validate against real product variants/documents and ensure no unintended layout regressions on narrow desktops and mobile breakpoints.

**Next steps** - Rebuild frontend assets and run manual regression on product pages with multiple images and document groups.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/static/src/scss/website_sale.scss`

### Milestone - PHC sync deferred for CRM-created contacts (2026-03-06)

**What changed** - Updated `pg_phc_api` so CRM and other Odoo flows can create `res.partner` records without PHC-only fields being mandatory on first save. PHC completeness is now validated only when the user explicitly runs `Sync PHC` or when an already linked contact is updated.

**Decisions** - Followed Odoo core CRM partner creation flow instead of forcing PHC requirements into `res.partner.create()`. Kept automatic PHC updates only for partners that already have a PHC `ref`; removed automatic PHC creation on first save.

**Risks / Pending Items** - Existing databases may still contain legacy manual-field metadata or Studio remnants that should be checked if required flags appear in the UI. Manual regression in CRM lead conversion and direct contact creation is still needed in a live database.

**Next steps** - Validate lead conversion from CRM, manual contact creation from the CRM partner field, explicit `Sync PHC` on an incomplete contact, and update behavior after a PHC `ref` is assigned.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/crm/wizard/crm_lead_to_opportunity.py`, `vendor/odoo_core/odoo/addons/crm/models/crm_lead.py`, `vendor/odoo_core/odoo/addons/crm/views/crm_lead_views.xml`, `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - PHC configuration moved to company and invoice sync aligned with 17.0 (2026-03-06)

**What changed** - Moved PHC credentials from user-level configuration to `res.company` in `pg_phc_api`, exposed them in Accounting settings through `res.config.settings`, switched partner PHC sync and invoice PHC sync to read company credentials, added a migration to copy existing user credentials to company records, and ported the 17.0 invoice improvements for sale-document guards, company-aware PHC partner ref lookup, and newline-preserving PHC description splitting.

**Decisions** - Kept `pg_phc_api` as the single source of truth for PHC credentials instead of reviving the dormant `pg_phc_api_integration` settings fields. Did not port 17.0 changes that alter PHC business semantics without confirmation, namely downpayment doctype differences and alternative product-type ref mappings.

**Risks / Pending Items** - If multiple users in the same company had conflicting PHC credentials, the migration keeps the first non-empty values found per company and logs conflicts. Existing database columns on `res_users` may remain unused after upgrade, which is acceptable but should be documented operationally.

**Next steps** - Run an upgrade on a staging database, confirm migrated company credentials in Settings, validate partner manual PHC sync under the active company, validate invoice sync on sale documents only, and confirm company-specific partner PHC refs behave correctly if `x_studio_ref_ofc22` exists in that database.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/account/models/res_config_settings.py`, `vendor/odoo_core/odoo/addons/account/views/res_config_settings_views.xml`, `vendor/odoo_core/odoo/addons/base/models/res_company.py`

### Milestone - Partner sync blockers ported from 17.0 without re-enabling first-save create sync (2026-03-06)

**What changed** - Ported the remaining safe 17.0 partner-sync behaviors into `pg_phc_api`: duplicate VAT now blocks only PHC sync and no longer blocks plain Odoo contact creation/update, manual sync/update now records PHC blocker reasons in `phc_last_response`, PHC create calls are forced to update when a partner already has a PHC ref, autosync now normalizes `is_phc_synced` for imports and existing-ref cases, portal/public-only contacts are excluded from PHC autosync, and PHC VAT-lock responses now restore the old VAT locally on failed update.

**Decisions** - Kept the 19.0 rule that unsynced contacts are not auto-created in PHC on normal save. Did not port the 17.0 relaxation that weakens PHC required-field validation, because this database should still enforce completeness when the user explicitly syncs to PHC.

**Risks / Pending Items** - Duplicate VAT is now tolerated in Odoo and only prevented at PHC sync time, so reporting and operational processes should assume that duplicates may exist before sync. PHC VAT-lock detection depends on message-text matching and should be validated against real PHC responses.

**Next steps** - Validate duplicate-VAT contact creation from CRM, manual `Sync PHC` blocker messaging, import-created contact behavior, portal-created contact behavior, and PHC update after a VAT change that is rejected by PHC.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/crm/models/crm_lead.py`, `vendor/odoo_core/odoo/addons/crm/wizard/crm_lead_to_opportunity.py`

### Milestone - pg_product_update variant IMAGENS misclassification fix (2026-03-17)

**What changed** - Tightened the Drive-folder validation in `pg_product_update` so the job only treats an `IMAGENS` folder as product-level when its parent folder actually yields a valid variant structure. Added a second safeguard to skip `product.template` creation when a folder has custom subfolders but no valid variant references, preventing bogus templates named after variant references and categories built from the full attribute path.

**Decisions** - Kept the fix isolated to `pg_product_update/models/product_update.py` and reused the importer's own variant-structure parser instead of adding heuristics based only on folder names. This is custom development; there is no Odoo core pattern for this Google Drive hierarchy, so the decision was to align only with the core product/category behavior while hardening the custom importer.

**Risks / Pending Items** - Existing bad `product.template` records already created by previous runs are not cleaned up automatically by this patch and may still need manual cleanup. Any legitimate product folder that contains non-metadata custom subfolders but does not resolve into valid variant references will now be skipped and should be reviewed in the Drive structure.

**Next steps** - Re-run the import on a staging database, confirm that `IMAGENS` folders under variant reference folders are skipped, confirm that the main template still imports and updates correctly, and manually remove or archive any previously duplicated templates created before this fix.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_product.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/product/models/product_category.py`

### Milestone - Website variant XPath compatibility and module icon standardization (2026-03-25)

**What changed** - Updated `pg_website_hide_unavailable_variant/views/templates.xml` so its website product page integration works on Odoo 19 without relying on brittle inheritance inside `website_sale.variants`. The patch evolved from nested xpath fixes to a more stable approach: replace the `t-call` to `website_sale.variants` inside `website_sale.product` and render a standalone custom variants template (`pg_variants`) that follows the Odoo 19 core structure while preserving the module's legacy data attributes and first-available-combination logic. Standardized `static/description/icon.png` across all custom modules by copying the icon from `pg_category_visibility_filter`.

**Decisions** - Followed the Odoo 19 website-sale template structure from core instead of keeping the inherited legacy XPath. Kept the shared icon rollout at the conventional module path (`static/description/icon.png`) so Odoo Apps can resolve icons without manifest changes.

**Risks / Pending Items** - `pg_website_hide_unavailable_variant` may still require additional Odoo 19 runtime refactoring in JS/model logic after the installation blocker is removed. `pg_category_visibility_filter` remains partially outdated for Odoo 19 because it relies on a missing custom model and an obsolete controller hook.

**Next steps** - Retry module install/upgrade on a 19.0 database, validate variant selection on a product page, and decide whether to modernize `pg_category_visibility_filter` to the current Odoo 19 controller/search flow.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/views/variant_templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/controllers/main.py`

### Milestone - Category visibility filter aligned to website_product_visibility (2026-03-25)

**What changed** - Reworked `pg_category_visibility_filter` to stop referencing the nonexistent `res.partner.product.visibility` model. The module now depends on `website_product_visibility`, reuses `website.sale_product_domain()` as the source of truth for visible products, derives visible website public categories from those products, and filters `website_sale.categories_recursive` accordingly.

**Decisions** - Followed the Odoo 19 shop controller flow by overriding the `shop` route only for qcontext post-processing, instead of reviving the obsolete `_get_search_domain` hook. Reused the existing third-party visibility configuration instead of creating a second custom model for the same purpose.

**Risks / Pending Items** - The upstream visibility module stores internal product categories, not website public categories, so category visibility is derived indirectly from allowed products and their `public_categ_ids`. This should be validated with real catalog structures.

**Next steps** - Upgrade both modules in a test database, enable website product visibility, assign allowed products/categories to a partner or visitors, and verify that only matching public categories remain in the website shop sidebar.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/controllers/main.py`

### Milestone - website_product_visibility settings view aligned to Odoo 19 (2026-03-25)

**What changed** - Updated `website_product_visibility/views/res_partner_view.xml` so its `res.config.settings` inheritance no longer targets the removed `website_email_marketing` block. The module now inserts its visitor-product configuration under the Odoo 19 Website app container.

**Decisions** - Followed the current Website settings structure from core (`//app[@name='website']`) instead of trying to preserve the removed pre-19 settings block anchor.

**Risks / Pending Items** - The module may still have other 19.0 compatibility issues in its website-sale template overrides, but this specific upgrade blocker in settings is fixed.

**Next steps** - Retry upgrade of `website_product_visibility`, then retry upgrade/install of `pg_category_visibility_filter`, and validate Website Settings plus `/shop` behavior for visitors and logged-in partners.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website/views/res_config_settings_views.xml`, `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`

### Milestone - CRM activity report completed-row highlight (2026-03-25)

**What changed** - Added a new custom module, `pg_crm_activity_report_highlight`, that inherits the core CRM activity report list view and applies `decoration-success` when the report row has a completion date. Added backend SCSS to turn that decoration into a subtle green row background for easier visual confirmation.

**Decisions** - Followed the core CRM activity report model and view instead of modifying the base CRM module. Reused the built-in list decoration mechanism from the web client and limited custom styling to the specific report list via a dedicated CSS class.

**Risks / Pending Items** - The core `crm.activity.report` is already a report of completed activities, so in practice most or all rows may appear highlighted. If the business wants only a subset of completions emphasized, the condition will need to be refined.

**Next steps** - Install `pg_crm_activity_report_highlight`, rebuild backend assets if needed, and validate the CRM Activities list in both dark and light themes for readability and desired emphasis level.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/crm/report/crm_activity_report.py`, `vendor/odoo_core/odoo/addons/crm/report/crm_activity_report_views.xml`, `vendor/odoo_core/odoo/addons/web/static/src/views/list/list_renderer.js`, `vendor/odoo_core/odoo/addons/web/static/src/views/utils.js`

### Milestone - Website variant hiding defaults aligned to Odoo 19 product interaction (2026-03-25)

**What changed** - Updated `pg_website_hide_unavailable_variant` so the website product page now hides impossible attribute values by default on first render and re-applies the filtering after each variant change. The frontend logic was rewritten as an Odoo 19 patch of `website_sale`'s `WebsiteSale` interaction, the module default for new product attributes now sets `unavailable_value_view_type` to `hide`, and the patch now also overrides the core `_disableInput` flow so values marked by Odoo as `css_not_available` are hidden instead of merely greyed out.

**Decisions** - Followed the Odoo 19 website-sale interaction pattern instead of keeping the legacy jQuery widget approach. Chose to hide impossible values unconditionally on the website, because the business requirement is to avoid showing combinations that do not exist even when legacy attributes were still configured with the old `None` default.

**Risks / Pending Items** - Existing website/browser caches can keep serving stale frontend assets until the module is upgraded and assets are rebuilt. The frontend patch was validated statically against Odoo 19 core paths, but not executed in a live browser from this terminal session.

**Next steps** - Upgrade `pg_website_hide_unavailable_variant`, clear/rebuild website assets, and validate a product with a missing combination such as `Superficie / Branco` so that the invalid value disappears as soon as the first attribute is selected by default.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/website_sale/views/templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/views/variant_templates.xml`, `vendor/odoo_core/odoo/addons/website_sale/static/src/interactions/website_sale.js`, `vendor/odoo_core/odoo/addons/website_sale/static/src/js/variant_mixin.js`, `vendor/odoo_core/odoo/addons/website_sale/static/src/js/website_sale_utils.js`

### Milestone - Shop/product page crash fixed for hidden variants with no default combination (2026-04-02)

**What changed** - Fixed `pg_website_hide_unavailable_variant/models/models.py` so its override of `product.template._get_first_possible_combination()` no longer changes the core behavior globally. The custom filtering now applies only under `special_call`, and when no visible combination exists it returns an empty `product.template.attribute.value` recordset instead of `None`.

**Decisions** - Followed the Odoo 19 core contract from `product_template.py`: `_get_first_possible_combination()` must always return a PTAV recordset, even when empty. Kept the hidden-variant behavior only for the module's explicit website context instead of affecting generic calls such as website shop variant prefetch.

**Risks / Pending Items** - Python compilation could not be run from this terminal because `python.exe` is unavailable here, so the validation is based on code inspection and the core method contract. Live shop/product page regression still needs to be checked after module upgrade.

**Next steps** - Upgrade `pg_website_hide_unavailable_variant`, then re-open `/shop` and a product page that previously crashed. If there is any remaining error, capture the new traceback because it will likely be a separate edge case from the same module.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/website_sale/controllers/main.py`

### Milestone - PHC bulk sync added to Contacts list (2026-03-26)

**What changed** - Extended `pg_phc_api` so the Contacts list view now shows a persistent `Sync PHC` button for bulk operations. The button is backed by a list-bound `ir.actions.server` and reuses the existing `res.partner.action_sync_phc()` logic, which already decides per record whether to create or update in PHC. Manual PHC actions now also resolve `active_ids` from list context and raise a clear error if no contact is selected.

**Decisions** - Followed the core list-view header button pattern instead of adding custom JS. Reused the existing PHC sync method to preserve current validation, blocker handling, and notifications rather than creating a second batch-specific sync flow.

**Risks / Pending Items** - This was validated statically from the codebase and XML parsing only. A live Odoo upgrade is still needed to confirm the button placement in the Contacts list and the exact UX when no rows are selected.

**Next steps** - Upgrade `pg_phc_api`, open Contacts list, select multiple contacts, click `Sync PHC`, and confirm that unsynced contacts are created, linked contacts are updated, and blocked records keep their reason in `Ultima resposta PHC`.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`, `vendor/odoo_core/odoo/addons/web/views/partner_view.xml`, `vendor/odoo_core/odoo/addons/crm/wizard/crm_merge_opportunities_views.xml`, `vendor/odoo_core/odoo/addons/crm/wizard/crm_lead_to_opportunity_mass_views.xml`, `vendor/odoo_core/odoo/addons/stock/views/product_views.xml`

### Milestone - PHC batch sync errors now identify the contact (2026-03-26)

**What changed** - Updated `pg_phc_api` manual PHC actions so when a batch sync or batch update fails with an exception, the raised error now includes the contact name that triggered the failure. This makes the list-view batch action usable for troubleshooting without guessing which selected partner caused the PHC rejection.

**Decisions** - Kept the existing fail-fast behavior for manual sync exceptions and only improved the message payload, instead of redesigning the batch flow to aggregate all failures in a custom wizard or notification.

**Risks / Pending Items** - The batch action still stops on the first hard exception, so if multiple selected contacts would fail, users will see them one at a time as each blocking contact is corrected.

**Next steps** - Upgrade `pg_phc_api`, retry the failing multi-contact PHC sync, and confirm the dialog now names the exact contact that triggered the PHC error.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`, `vendor/odoo_core/odoo/addons/web/views/partner_view.xml`

### Milestone - PHC internal responsible mapped from Odoo users with cleaned names (2026-03-26)

**What changed** - Extended `pg_phc_api` with a new `pg_responsavel_interno_user_id` field on `res.partner` so users can choose an internal Odoo user for the PHC internal responsible. The PHC payload no longer sends the raw Odoo display name directly; it now strips the database prefix before the last `|`, so names like `ESSANI® | Hugo Rios` are sent to PHC as `Hugo Rios`. The PHC tab now shows both the Odoo user selector and the resulting PHC text value.

**Decisions** - Kept the existing `responsavel_interno` char field as the persisted PHC-facing field for compatibility with existing databases and hooks, and added a `pg_` helper field for the Odoo UI instead of replacing the original field type. Followed the core `res.partner.user_id` pattern for user selection by using `res.users` with the `many2one_avatar_user` widget.

**Risks / Pending Items** - The automatic user match from existing `responsavel_interno` text depends on the cleaned name matching exactly one internal Odoo user after prefix removal. If two internal users clean down to the same final name, the first match found will be used in the selector.

**Next steps** - Upgrade `pg_phc_api`, open a contact, pick the internal responsible from the new Odoo user field, and validate that the PHC request sends the clean value without the `ESSANI® |` prefix.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`, `vendor/odoo_core/odoo/addons/contacts/views/contact_views.xml`

### Milestone - Native Odoo contact import bypasses PHC outbound validation and sync (2026-04-06)

**What changed** - Updated `pg_phc_api` so the native Odoo record import flow (`context['import_file']`) can update PHC-linked contacts without being blocked by PHC required-field validation, the custom PT VAT-format constraint, or the custom posted-document VAT-change lock. Automatic outbound PHC sync on save was already disabled for native imports and remains disabled.

**Decisions** - Followed Odoo core's native import context flag instead of inventing a custom import mode. Treated the native import as an inbound data-load channel, so PHC-side outbound checks should not block those writes.

**Risks / Pending Items** - Native imports can now write values that would normally be blocked by these PHC/custom validations, so operationally this import path should be treated as a controlled administrative tool for inbound PHC data loads only.

**Next steps** - Upgrade `pg_phc_api`, retry the Excel import through Odoo's native import wizard, confirm the records update without PHC validation blockers, and confirm no outbound PHC sync/update is triggered by that import.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/orm/models.py`, `vendor/odoo_core/odoo/addons/base_import/models/base_import.py`, `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`

### Milestone - PHC price table now defaults to 1 during validation and sync (2026-04-13)

**What changed** - Updated `pg_phc_api` so `res.partner.x_studio_tabela_precos` now has an explicit Python default of `1`, and PHC validation plus outbound XML generation now both fall back to `1` whenever the field is empty. This prevents PHC sync from incorrectly blocking contacts with the intended default price table.

**Decisions** - Followed the core pattern of defining selection defaults directly on the Python field instead of relying on external/studio defaults only. Kept the business rule local to the PHC helper methods so existing contacts with empty DB values do not need an immediate data migration.

**Risks / Pending Items** - Existing contacts with blank `x_studio_tabela_precos` will now sync as table `1`, which matches the stated business expectation. If any contact should truly sync without a price table, that business rule would need to be clarified because the connector now treats blank as `1`.

**Next steps** - Upgrade `pg_phc_api`, retry PHC sync on the affected contact, and confirm the blocker for `x_studio_tabela_precos` no longer appears.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`, `vendor/odoo_core/odoo/addons/account/models/account_account_tag.py`

### Milestone - PHC create response parsing hardened for missing-reference errors (2026-04-13)

**What changed** - Hardened `pg_phc_api` PHC response parsing so create-sync can extract the PHC reference from more payload shapes, including JSON dict/list structures and multiple key variants (`Numero`, `No`, `Ref`). Also improved the create-sync error path so when PHC does not return a parsable reference, the popup now includes the PHC message when available instead of only showing the generic fallback.

**Decisions** - No clear Odoo core pattern applies here because this is custom PHC SOAP/JSON integration logic. Kept the change local to the response parser and create-sync branch instead of altering the sync flow semantics.

**Risks / Pending Items** - The parser is now more permissive and may accept non-numeric references if PHC legitimately returns them. If PHC returns malformed success payloads with ambiguous fields, further tightening may be needed after inspecting real responses in `Ultima resposta PHC`.

**Next steps** - Upgrade `pg_phc_api`, retry sync on the affected contact, inspect `Ultima resposta PHC`, and confirm whether the issue was a parser miss or a real PHC-side rejection.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - PT-only PHC validation now follows PHC country code first (2026-04-13)

**What changed** - Updated `pg_phc_api` PT detection so PHC-specific country rules now prefer `x_studio_country_code` over `country_id.code`. The Portuguese zip-format validation now uses that same PHC-aware country detection, which prevents non-PT contacts from being blocked just because the Odoo country field is stale or inconsistent with the PHC country code.

**Decisions** - No clear Odoo core pattern exists for this PHC-specific validation, so this remains custom development. The chosen rule is that PHC-country-dependent validation must follow the PHC country field first, because that is the value actually sent to PHC.

**Risks / Pending Items** - If a contact has conflicting `country_id` and `x_studio_country_code`, PHC validation will now trust `x_studio_country_code`. That is intentional for the connector, but data cleanup may still be desirable to keep both fields aligned.

**Next steps** - Upgrade `pg_phc_api`, retry sync on the UK contact, and confirm that the Portuguese ZIP-format blocker no longer appears.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - PHC price table no longer mandatory for contact sync (2026-04-13)

**What changed** - Updated `pg_phc_api` so `x_studio_tabela_precos` is no longer treated as a mandatory PHC field in `_phc_validate_sync_requirements()`. The connector still keeps the existing fallback behavior that sends price table `1` when the field is empty, but sync is no longer blocked by the mandatory-field checker.

**Decisions** - This is custom development because the mandatory PHC field list is defined only in `pg_phc_api`, not by Odoo core. Kept the payload fallback to `1` in place so blank values still produce a deterministic PHC payload without forcing users to maintain that field.

**Risks / Pending Items** - Contacts with empty `x_studio_tabela_precos` will continue to sync using fallback value `1`. If PHC-side business rules later require a different fallback or true null handling, that will need a separate change.

**Next steps** - Upgrade `pg_phc_api`, retry PHC sync on the affected contact, and confirm the blocker for `x_studio_tabela_precos` no longer appears anywhere in `Ultima resposta PHC`.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - PHC partner sync now logs detailed validation, payload, and response traces (2026-04-13)

**What changed** - Added detailed diagnostic logging to `pg_phc_api/models/res_partner.py` for manual PHC partner sync. The connector now logs a compact partner snapshot, validation failures, the final parameter XML sent to PHC, the raw HTTP response body, the parsed `RunCodeResult`, and the create/update parse summary including extracted reference and message. This is intended to isolate whether a sync failure happens in local validation, outbound payload composition, PHC transport, or PHC response parsing.

**Decisions** - No clear Odoo core pattern exists for PHC-specific SOAP diagnostics, so this remains custom development. Kept the logs bounded with excerpt helpers instead of dumping unlimited payloads, and kept the new instrumentation local to `res.partner` sync helpers rather than introducing a separate logging model.

**Risks / Pending Items** - The new logs increase verbosity during PHC sync and may expose business data in server logs, so they should be treated as temporary troubleshooting instrumentation if log volume becomes a concern. The salesperson-number validation branch still has no dedicated warning log; the main sync path diagnostics were prioritized first because they are more relevant to the current failure.

**Next steps** - Upgrade `pg_phc_api`, retry sync on the failing contact, and inspect the new server log lines for `PHC parameter XML built`, `PHC RunCode request`, `PHC RunCode raw HTTP response`, and `PHC create parse summary`. Use those exact entries to confirm the effective `tabprecost`, country code, and PHC response payload before making any further connector changes.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - PHC partner payload extended with free-shipping flag and Odoo notes (2026-04-14)

**What changed** - Extended `pg_phc_api` partner sync so `res.partner` now has a new boolean field `pg_portes_gratuitos`, exposed on the PHC tab, and the outbound PHC payload now sends it as `portesgratuitos` with values `0` or `1`. The connector also now reads the standard Odoo `comment` field, converts its HTML notes to plain text using Odoo's `html2plaintext`, and sends that value to PHC as `obsint` without applying a connector-side character limit. While touching the payload builder, all PHC XML tag values are now XML-escaped before being wrapped in the CDATA request body.

**Decisions** - Followed the core `res.partner` pattern where `comment` is a standard HTML notes field on the base model, and followed Odoo's own `html2plaintext` utility pattern when exporting HTML content to plain-text integration targets. Kept the new PHC-specific free-shipping field under the required `pg_` prefix instead of reusing a Studio-style name. Escaped outbound XML values centrally in the PHC payload builder because the connector sends an XML fragment inside CDATA and values like `R & M ...` were otherwise producing invalid inner XML.

**Risks / Pending Items** - The `obsint` payload now carries the plain-text rendering of Odoo notes, which may differ slightly from the visual HTML formatting users see in the UI. The XML escaping changes the literal payload text for reserved characters (`&`, `<`, `>`), but that is the correct transport format and may also help explain previous empty PHC `RunCodeResult` responses on contacts whose values contained reserved XML characters.

**Next steps** - Upgrade `pg_phc_api`, set `Portes Gratuitos (PHC)` on a test contact, add notes in the Odoo `comment` field, retry `Sync PHC`, and confirm in the server log excerpt that the payload now includes `<portesgratuitos>0|1</portesgratuitos>` and `<obsint>...</obsint>` with escaped XML-safe content.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`, `vendor/odoo_core/odoo/tools/mail.py`, `vendor/odoo_core/odoo/addons/account_followup/models/account_followup_report.py`

### Milestone - PHC partner payload extended with dedicated telephone field (2026-04-14)

**What changed** - Extended `pg_phc_api` partner sync with a new custom field `pg_telefone` on `res.partner`, exposed on the PHC tab and sent to the PHC payload as `<telefone>...</telefone>`. The new field uses the same 45-character limit as the existing `telemovel` mapping and is included in the connector's generic PHC length validation and debug snapshot.

**Decisions** - Checked Odoo core first and confirmed that `res.partner` only provides the standard `phone` field; there is no separate base-model `telefone` field. This is therefore custom development. Kept the existing `phone -> telemovel` mapping untouched for compatibility, and added a separate `pg_telefone` field for the PHC-specific `telefone` parameter instead of overloading the standard Odoo phone field semantics.

**Risks / Pending Items** - This adds a second phone-like field to the contact UI, so users need to understand that `phone` continues to feed `telemovel` in PHC while `pg_telefone` feeds the PHC `telefone` parameter. If the business later decides that Odoo `phone` should map to PHC `telefone` instead, that should be handled as a separate semantic change.

**Next steps** - Upgrade `pg_phc_api`, fill in `Telefone (PHC)` on a test contact, retry `Sync PHC`, and confirm in the PHC payload log that both `<telemovel>...</telemovel>` and `<telefone>...</telefone>` are present with the expected values.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - Odoo.sh schema mismatch recovered by module version bump and upgrade (2026-04-14)

**What changed** - Confirmed operationally on Odoo.sh that when `pg_phc_api` introduces new stored fields on `res.partner` and the running database still lacks the corresponding columns, bumping the module version and upgrading the module is sufficient for Odoo to create the missing columns. This resolved the `UndefinedColumn` crash for newly added partner fields without needing manual SQL.

**Decisions** - Treat module version bump plus module upgrade as the first recovery step on Odoo.sh for future schema mismatches caused by newly added stored fields. Keep manual SQL only as an emergency fallback when the upgrade path is blocked.

**Risks / Pending Items** - This relies on the module upgrade being able to start and complete on the affected branch. If a future deployment gets stuck before upgrade can run, manual SQL may still be required as a recovery path.

**Next steps** - For future Odoo.sh incidents of `column ... does not exist` after adding stored fields, first bump the module version, trigger the module upgrade, and only consider manual PostgreSQL intervention if the upgrade cannot be executed.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`

### Milestone - Partner header phone icons refined for PHC telephone field (2026-04-14)

**What changed** - Refined the inherited `base.view_partner_form` in `pg_phc_api` so the standard Odoo `phone` field shown in the partner header now uses a mobile icon, reflecting its current PHC mapping to `telemovel`. The custom PHC field `pg_telefone` is now rendered directly below it in the same header contact block with a landline phone icon, and the duplicate `pg_telefone` field was removed from the PHC tab to avoid redundant display.

**Decisions** - Followed the existing core partner form layout in `base.view_partner_form` instead of adding custom JS or CSS. Kept the change local to view inheritance using targeted `xpath` expressions on the header contact block.

**Risks / Pending Items** - The `xpath` targets the specific header `phone` block of the current core partner form. If Odoo changes that markup significantly in a future version, the inheritance may need to be adjusted.

**Next steps** - Upgrade `pg_phc_api`, open a contact form, confirm the standard phone now shows a mobile icon, and confirm `pg_telefone` appears immediately below with the phone icon and correct value.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`

### Milestone - Product update attribute dedupe and rerun hardening (2026-03-26)

**What changed** - Hardened `pg_product_update` against duplicated attributes, attribute values, and product attribute lines during repeated or overlapping Drive imports. The importer now uses transaction-level advisory locks for product, attribute, attribute value, and attribute-line creation; normalizes names when selecting canonical attribute records; merges duplicate `product.template.attribute.line` rows on the product; and reduces repeated variant/image lookups in the post-sync phase.

**Decisions** - Kept the fix inside `pg_product_update` rather than altering Odoo core or adding global uniqueness constraints on translated product attribute names. Existing duplicated master attribute/value rows are not merged automatically across the whole database; the importer now prefers a canonical record and cleans the visible product-level duplication.

**Risks / Pending Items** - Old duplicate master data may still need targeted cleanup if other processes rely on exact attribute/value IDs. Runtime validation in a live Odoo environment is still required because the local Windows Store Python launcher in this terminal session could not execute a compile check.

**Next steps** - Re-run the Drive import on a previously affected product, confirm the attributes tab no longer shows duplicate rows after multiple runs, and inspect logs for `Duplicate product attributes`, `Duplicate product attribute values`, and `Merging duplicate attribute lines` warnings.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_attribute.py`, `vendor/odoo_core/odoo/addons/product/models/product_attribute_value.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_value.py`, `vendor/odoo_core/odoo/addons/product/models/product_product.py`

### Milestone - Product update live progress dashboard (2026-03-26)

**What changed** - Extended `pg_product_update` so starting the Drive import now opens a live backend dashboard instead of leaving the user on the product form with only the bottom-right loading indicator. The dashboard polls the persisted `product.update.drive.job` record and shows current phase, progress percentage, processed/pending counts, discovery queue size, current item, elapsed time, and last error. Added standard list/form views for import jobs as a fallback/history screen.

**Decisions** - Reused the existing `product.update.drive.job` model as the single source of truth for progress instead of creating a second transient tracker. Followed Odoo backend client-action patterns for the live screen and standard form/list views for inspectability without custom core changes.

**Risks / Pending Items** - Live updates depend on backend assets being refreshed after upgrade. Polling is intentionally lightweight but still requires a running browser tab; it is not a push/bus implementation.

**Next steps** - Upgrade `pg_product_update`, verify the button opens the dashboard immediately, let a real import run for several minutes, and confirm the dashboard numbers advance as cron commits progress.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base_import/static/src/import_data_progress/import_data_progress.js`, `vendor/odoo_core/odoo/addons/base_import/static/src/import_data_progress/import_data_progress.xml`, `vendor/odoo_core/odoo/addons/web/static/src/webclient/actions/action_service.js`, `vendor/odoo_core/odoo/addons/web/static/src/views/fields/gauge/gauge_field.js`

### Milestone - Product update job smartbutton fallback (2026-03-26)

**What changed** - Added an `Import Jobs` stat button to the `product.template` form so users can open the latest running import job or latest finished job directly from the product page. Also corrected the bound server action code so it assigns the returned action to `action`, allowing Odoo to propagate the dashboard open action when the import is launched from the action menu. The latest adjustment commits the newly created import job before returning and makes the stat button target the latest running job's live dashboard first.

**Decisions** - Followed the core `oe_button_box` / `oe_stat_button` pattern on product forms instead of adding more custom JS for fallback navigation. Kept the smartbutton target as a standard `act_window` form/list action so it works even when the custom dashboard client action assets are stale.

**Risks / Pending Items** - The smartbutton count is global to import jobs, not product-specific, because the import job model tracks Drive runs globally rather than per product.

**Next steps** - Upgrade `pg_product_update`, confirm the smartbutton appears beside the other product stat buttons, start a new import, and verify the smartbutton opens the newly created running job dashboard instead of the previous completed job.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/views/product_views.xml`, `vendor/odoo_core/odoo/addons/product/views/product_template_views.xml`

### Milestone - Product update pending-first runner flow (2026-03-30)

**What changed** - Adjusted `pg_product_update` job execution so the cron processes queued pending `IMAGENS` items before continuing discovery. Added a shared `_process_next_job_pending_item()` helper and updated dashboard phase calculation so jobs with queued work display as `Processing` instead of looking indefinitely stuck in `Discovery`.

**Decisions** - Kept discovery and processing in the same job model, but changed scheduling priority to favor visible import progress once actionable work exists. This avoids queue starvation without redesigning the job structure.

**Risks / Pending Items** - If a job has no pending items yet, discovery can still take time on very large Drive trees. This fix addresses starvation after pending work is available; it does not replace the need to optimize discovery itself if root-folder traversal is inherently too slow.

**Next steps** - Upgrade `pg_product_update`, refresh the stuck job screen, and verify that jobs with non-zero pending counts start increasing `processed_count` again on the next cron executions.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/views/product_template_views.xml`, `vendor/odoo_core/odoo/addons/product/views/product_views.xml`

### Milestone - Product update progress now uses discovered products instead of folder queue heuristics (2026-03-30)

**What changed** - Adjusted `pg_product_update` dashboard progress so it is based on actual discovered product folders rather than the remaining discovery-folder stack. Added a persisted `discovered_count` on `product.update.drive.job`, incremented it whenever discovery finds a new product-level `IMAGENS` folder, and changed the dashboard to show `Processed / Total Products` once discovery is complete. While discovery is still running, the UI now explicitly labels the bar as an estimate and shows how many products have been discovered so far.

**Decisions** - Kept the current mixed discovery/processing runner instead of reverting to full discovery before any processing, because earlier runs showed that discovery-only waiting can be too slow for users. The dashboard is now explicit about when totals are exact versus still being estimated.

**Risks / Pending Items** - For in-flight jobs created before this field existed, `discovered_count` starts by reconciling from the current pending/processed state and becomes accurate as discovery continues, but the very first refresh after upgrade may still not reflect the full final total until more discovery steps commit. Exact current-run percentages are only possible after discovery finishes; before that, the dashboard still needs an estimate.

**Next steps** - Upgrade `pg_product_update`, reload backend assets, start a new import, and verify the dashboard shows `Discovered Products`, an estimated total while discovery is active, and an exact `processed / total products` percentage once discovery completes.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base_import/static/src/import_data_progress/import_data_progress.js`, `vendor/odoo_core/odoo/addons/base_import/static/src/import_data_progress/import_data_progress.xml`, `vendor/odoo_core/odoo/addons/web/static/src/views/fields/progress_bar/progress_bar_field.js`

### Milestone - Product update throughput improved without reducing sync scope (2026-03-30)

**What changed** - Optimized `pg_product_update` throughput in three safe areas: reused a single `_GDriveHelper` instance per runtime so Drive `get`/`list_children` caches actually persist across nested calls; stopped forcing image/document refresh when Drive metadata already shows the file is unchanged; and changed the cron runner so one execution can process multiple products within its existing time budget instead of effectively stopping after one product.

**Decisions** - Kept the full sync scope intact: the importer still traverses the same folders, compares the same files, removes stale media/docs, and preserves all existing business logic. The speedup comes from avoiding repeated Drive metadata calls, avoiding unnecessary file downloads/writes when MD5 matches, and using the already configured cron budget more efficiently.

**Risks / Pending Items** - The biggest remaining heavy area is category/media work that still depends on Drive traversal and binary downloads when files truly changed. If more speed is needed after this, the next candidates are category-image deduping and deeper batch instrumentation to measure per-phase timings in logs.

**Next steps** - Upgrade `pg_product_update`, run a fresh import job, compare products/hour before and after, and watch whether the dashboard `Processed` count advances several items per cron cycle instead of only one.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`, `vendor/odoo_core/odoo/addons/base/tests/test_ir_cron.py`, `vendor/odoo_core/odoo/addons/base_import/static/src/import_data_progress/import_data_progress.js`

### Milestone - Product update Drive helper cache fixed for Odoo recordset constraints (2026-03-30)

**What changed** - Fixed a regression in `pg_product_update` where the shared Google Drive helper was cached on the `product.update` recordset instance. On Odoo 19, model recordsets use `__slots__`, so assigning arbitrary attributes like `_pg_gdrive_helper` raises `AttributeError`. The helper cache now lives in a class-level per-database dictionary and is cleared through the existing runtime cache reset path.

**Decisions** - Reused the same class-cache pattern already used by the importer’s attribute and IMAGENS caches instead of introducing a custom environment-side storage layer. This keeps the Drive metadata cache available across importer calls without violating Odoo model constraints.

**Risks / Pending Items** - Existing running jobs that already hit this error need a module upgrade and a retry of the action. The fix is safe, but live validation still depends on redeploying the updated module to the Odoo instance.

**Next steps** - Upgrade `pg_product_update`, retry `Force Start Import`, and confirm the action opens the dashboard without the previous `AttributeError` on `_pg_gdrive_helper`.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/orm/models.py`

### Milestone - Archived product templates are now reactivated during Drive import (2026-04-02)

**What changed** - Updated `pg_product_update/models/product_update.py` so Drive product imports no longer ignore archived `product.template` records. The importer now searches templates with `active_test=False`, reactivates exact archived matches, and falls back to a unique `product.product.default_code` overlap match when the Drive folder name changed but the variant references are still the same. This allows cases like historical `Spot30` templates to be revived and updated from newer Drive folders such as `LED Spot30`.

**Decisions** - Kept the fallback match conservative: it only reuses a template when the discovered variant `default_code` values point to exactly one template. Avoided fuzzy name matching so archived unrelated templates are not accidentally revived.

**Risks / Pending Items** - If multiple templates share overlapping variant references, the importer will log a warning and refuse the fallback reuse. Products whose Drive folder names changed but have no stable `default_code` overlap still require a separate matching strategy.

**Next steps** - Upgrade `pg_product_update`, rerun the import for archived examples like `LED Spot30`, and verify that the archived template is reactivated instead of a new product being skipped or recreated.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/product/models/product_product.py`

### Milestone - Drive import jobs now track skipped product folders explicitly (2026-04-07)

**What changed** - Added persistent skip tracking to `product.update.drive.job` in `pg_product_update`. Jobs now store `skipped_count` plus a capped list of skipped IMAGENS items and reasons. The current silent revalidation path in `_process_next_job_pending_item()` now records every queued item that gets dropped before processing, instead of only shrinking `pending_imagens_json`. The job form and live dashboard were updated to show the skip count and the last skipped items.

**Decisions** - Kept the change focused on job telemetry instead of changing discovery semantics. The goal is to explain mismatches like `discovered_count > processed_count` first, using explicit reasons such as missing custom folders or invalid reference-folder structure, before deciding whether discovery or processing rules should change.

**Risks / Pending Items** - The new tracking explains items dropped during pending revalidation, which is the main silent path found so far. It does not yet classify every possible no-op outcome inside a successfully processed item; if needed later, `process_multi_variant_product()` can be extended to return structured per-item outcomes as well.

**Next steps** - Upgrade `pg_product_update`, run a fresh import, and verify whether the dashboard/job record now shows the skipped 8 items and their exact reasons when discovered and processed counts diverge.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`

### Milestone - PHC sync restricted to company contacts only (2026-04-22)

**What changed** - Updated `pg_phc_api` so PHC-specific behavior now applies only to `res.partner` records flagged as companies. Person contacts no longer auto-sync or update in PHC, PHC validation rules no longer run for persons, and the PHC buttons/tab/custom phone field are hidden on person contacts in the standard partner form.

**Decisions** - Followed the Odoo core partner pattern where `is_company` is the business-logic field and `company_type` is only the UI interface. Kept the list-level PHC action available because the core list action binding does not provide row-level visibility, but manual PHC actions now treat person contacts as ineligible and block them cleanly.

**Risks / Pending Items** - Existing person contacts may still keep historic PHC reference data in fields such as `ref`, but they will no longer sync while they remain persons. The list-view `Sync PHC` action is still globally visible and should be regression-tested with mixed selections of companies and persons.

**Next steps** - Upgrade `pg_phc_api` and validate these scenarios in Odoo: company contact sync, company contact update, person contact form visibility, mixed list selection, and converting a person back into a company.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`, `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`

### Milestone - PHC payload now sends a second notes field through obs (2026-04-22)

**What changed** - Extended `pg_phc_api` with a new custom field `res.partner.pg_obs` for PHC-specific notes. The existing Odoo `comment` field continues to be converted and sent to PHC as `obsint`, and the new `pg_obs` field is now sent separately in the PHC payload as `obs`.

**Decisions** - Reused the Odoo core partner note pattern where the standard internal notes live in `comment`, instead of repurposing that field for two PHC destinations. Added a dedicated `pg_` field so the business can manage `obs` independently from the normal partner internal notes that already feed `obsint`.

**Risks / Pending Items** - No field-length constraint was added for `obs` because the current PHC integration codebase does not define a known limit for that parameter. This should be validated against the PHC side if a strict maximum exists.

**Next steps** - Upgrade `pg_phc_api`, test a company contact with both note fields filled, and confirm in PHC that `comment -> obsint` and `pg_obs -> obs` are both received correctly on create and update.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`, `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`

### Milestone - Delivery contacts now sync to PHC through Cria_MoradaEntregaCL (2026-04-22)

**What changed** - Extended `pg_phc_api` so `res.partner` records with `type = 'delivery'` can sync to PHC through the `Cria_MoradaEntregaCL` service, while normal person contacts remain excluded from PHC sync. Added the new field `pg_contacto_entrega`, reused `pg_telefone` plus `phone` for the two delivery phone numbers, validated the delivery-specific PHC limits from the integration sheet, and built a dedicated payload with `descritivo`, parent PHC customer number, address, contact, email, and phone data. Delivery contacts now auto-create in PHC on save when valid and not already synced.

**Decisions** - Followed the Odoo core partner model where delivery addresses are child `res.partner` records with `type = 'delivery'` and typically `is_company = False`, instead of relaxing the global no-person-sync rule. Kept the company customer flow (`CriaCL` / `UpdateCL`) separate from the delivery-address flow because they use different PHC scripts, required fields, and length limits.

**Risks / Pending Items** - This delivery flow currently assumes create-only behavior through `Cria_MoradaEntregaCL`; no delivery-specific PHC update service has been implemented. Also, `descritivo` is mapped directly from Odoo `name` as requested, so PHC-side uniqueness conflicts may still need business handling if duplicate delivery names exist.

**Next steps** - Upgrade `pg_phc_api`, create/edit a delivery child contact under a PHC-synced company, and confirm the PHC morada de entrega is created with the expected `descritivo`, `contacto`, `telefone`, and `telemovel` mappings. Validate how PHC responds when `descritivo` is duplicated.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/res_partner.py`, `vendor/odoo_core/odoo/addons/base/views/res_partner_views.xml`

### Milestone - Duplicate cleanup no longer aborts on core variant-limit during line normalization (2026-04-17)

**What changed** - Patched `pg_product_update/models/product_update.py` so the manual duplicate-variant cleanup treats the Odoo core `product.dynamic_variant_limit` `UserError` as a skip condition for duplicate attribute-line normalization, instead of aborting the whole cleanup action. The cleanup now detects the core limit message, logs a warning with the affected product/attribute, and continues to the duplicate-variant archival pass for already existing variants.

**Decisions** - Kept the fix generic and local to the cleanup action. The button's purpose is to clean duplicates safely; it should not fail the entire operation just because normalizing template attribute lines would trigger Odoo core variant regeneration above the configured limit. The line-cleanup phase is therefore best-effort on high-combination products.

**Risks / Pending Items** - Products that hit the variant-limit path may keep duplicate attribute lines visible on the template form, because the cleanup now prefers safety over forcing line normalization. Duplicate existing variants should still be archivable. If the button still throws the same popup after upgrade, the traceback must be captured because that would indicate another path outside the current line-normalization guard.

**Next steps** - Upgrade `pg_product_update`, rerun the single-product cleanup on a high-combination case, and verify the action completes with a notification instead of the variant-limit popup. If needed, inspect whether the remaining issue is a different write path still calling `_create_variant_ids()`.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Duplicate cleanup now emits detailed product-level diagnostics in server logs (2026-04-17)

**What changed** - Added explicit `_logger.info/_logger.warning/_logger.exception` tracing around the manual duplicate cleanup flow in `pg_product_update/models/product_update.py`. The cleanup now logs: start/end of the overall run, start/end per product, estimated logical variant count versus `product.dynamic_variant_limit`, each duplicate attribute-line normalization attempt, runtime skips triggered by the core variant limit, non-limit cleanup exceptions, duplicate variant archival attempts, and the final summary.

**Decisions** - Kept diagnostics in the server log instead of adding new persistent models or UI fields. The immediate goal is to identify whether a given product reaches line normalization, fails during that phase, or only fails later during duplicate variant archival, with enough context to correlate to the exact product and attribute.

**Risks / Pending Items** - The logs are more verbose during manual cleanup actions, especially on products with many duplicate groups. This is acceptable because the buttons are operational/admin tools, not high-frequency background tasks.

**Next steps** - Upgrade `pg_product_update`, rerun the failing cleanup action, and capture the new log block around the affected product. Use the new entries to determine whether the remaining popup comes from line normalization, duplicate variant archival, or another write path.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Removed website-category assignment from product update import (2026-04-16)

**What changed** - Updated `pg_product_update/models/product_update.py` so the Drive import no longer creates `product.public.category` records during hierarchy traversal and no longer writes `public_categ_ids` on imported `product.template` records. The import now keeps only the standard backoffice category assignment through `categ_id`, while preserving the existing internal category tree creation, POS category behavior, publishing flag, and image/document sync flow.

**Decisions** - Followed the core split between internal product categories and eCommerce categories instead of keeping both in the importer. The reference pattern comes from core `product.template.categ_id` in `vendor/odoo_core/odoo/addons/product/models/product_template.py` and the separate website-only `product.template.public_categ_ids` extension in `vendor/odoo_core/odoo/addons/website_sale/models/product_template.py`. Based on that split, the importer now treats website category population as out of scope for this custom sync flow.

**Risks / Pending Items** - Existing `product.public.category` records and previous product-to-website-category links already created by older imports are not cleaned up by this change; the patch only stops creating/updating them going forward. The `product.update.drive.job.all_web_category_id` field remains in the model for backward compatibility with existing databases, but it is no longer populated or used by the import runner.

**Next steps** - Upgrade `pg_product_update`, run a fresh import, and confirm that newly imported or updated products keep the correct `Product Category` (`categ_id`) in backoffice while no new website categories are created and no new `public_categ_ids` links are added.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/website_sale/models/product_template.py`

### Milestone - Precise per-item queue and processing diagnostics added to Drive jobs (2026-04-10)

**What changed** - Expanded `pg_product_update/models/product_update.py` telemetry so Drive jobs now persist more precise lifecycle events for each IMAGENS item: `discovery_queue` with queue size, `pending_revalidation_skip`, `processing_claimed`, `processing_exception` with exception class, `processing_retry` with requeue note, `processing_skip` for explicit non-import outcomes, `processing_derived`, `processing_product_updated`, `processing_complementos`, and `job_done_unaccounted`. `_process_one_imagens_folder()` now returns explicit outcome dictionaries instead of silently early-returning, so the runner can classify those cases as skipped instead of leaving them ambiguous. `unaccounted_items_preview` now includes each item's last known trace stage and message, and trace retention/preview size were increased for post-run diagnosis.

**Decisions** - Kept the patch generic and queue-centric rather than product-specific. Chose to record lifecycle state directly on the job model because the browser dashboard and job form are the quickest way to inspect missing items without relying only on transient Odoo.sh worker logs.

**Risks / Pending Items** - The larger trace ledger increases JSON writes and retained text size, though both remain capped. If runs become much larger, traces may need to move to a dedicated child model. This patch improves observability and outcome classification; it does not by itself guarantee that the upstream interruption cause is fixed.

**Next steps** - Upgrade `pg_product_update`, run a fresh import, and inspect `Unaccounted Items` together with the new last-stage detail. For any remaining missing items, use the exact last trace stage to determine whether they were only queued, removed during revalidation, claimed and interrupted, or ended in an explicit skip outcome.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Variant duplication prevented by logical attribute-line merge (2026-04-17)

**What changed** - Patched `pg_product_update/models/product_update.py` so `_ensure_attribute_line()` now merges template attribute lines by normalized logical attribute name, not only by exact `attribute_id`. This prevents reruns from creating visually duplicate attribute rows and duplicate logical variant combinations when master data already contains duplicate `product.attribute` records such as two different `Acabamento` rows. The importer now canonicalizes values into the chosen attribute, reuses an existing canonical line when available, or creates one canonical line and removes the duplicate logical lines tied to duplicate attribute records.

**Decisions** - Followed Odoo core’s line/variant lifecycle rather than bypassing it with custom variant creation. Kept the fix at the importer level instead of attempting a global destructive merge of master `product.attribute` records, which would be riskier and broader in impact. Added more explicit warning logs for duplicate logical attribute lines to make future data issues visible.

**Risks / Pending Items** - Existing duplicate logical attributes in master data are still present globally; this patch neutralizes their effect during import on the touched products but does not clean the master records database-wide. Attribute-line unlink/write still triggers Odoo’s standard variant regeneration, so products with heavy variant sets may incur some extra work during the first clean-up rerun.

**Next steps** - Upgrade `pg_product_update`, rerun the problematic imports, and verify that products like the `Acabamento/Preto` case keep a single logical attribute line across reruns. If duplicates still appear, inspect the new warning logs to see whether the remaining issue is duplicate master attributes, duplicate values, or a different path.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Manual duplicate-variant cleanup actions added (2026-04-17)

**What changed** - Added manual cleanup actions on `product.template` in `pg_product_update` to archive duplicate logical variants and normalize duplicate logical attribute lines on demand. A product-level stat button now shows the duplicate-variant count and runs cleanup for the current product. A second button on the product form runs the cleanup across all products. The cleanup reuses the importer’s normalization and canonical attribute helpers, searches attribute lines with `active_test=False`, locks each product during cleanup, normalizes duplicate logical lines into one canonical line, then archives redundant variants that still share the same logical combination.

**Decisions** - Chose archiving over destructive deletion for duplicate variants to reduce risk of breaking references in orders, documents, or other linked records. Kept the cleanup generic and product-template based instead of creating a separate wizard, since the user explicitly wanted direct buttons for current-product and all-product cleanup. Used the existing `product_template_only_form_view` inheritance and core stat-button pattern.

**Risks / Pending Items** - The bulk cleanup can touch many templates and may take some time on large databases. Archived duplicate variants are hidden from normal views but remain in the database for safety. This action does not globally merge duplicate master `product.attribute` records; it neutralizes their effect on product templates being cleaned.

**Next steps** - Upgrade `pg_product_update`, test the current-product cleanup on a known duplicate case, then run the global cleanup if the result is correct. After cleanup, rerun imports and confirm duplicates are not recreated on the affected products.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/views/product_template_views.xml`, `vendor/odoo_core/odoo/addons/product/views/product_views.xml`, `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Duplicate cleanup made safe for multi-attribute products (2026-04-17)

**What changed** - Fixed the `Cursor already closed` crash in the manual duplicate-variant cleanup for products with multiple duplicated attribute lines. The cleanup no longer iterates on live ORM recordsets while mutating those same attribute lines. Instead it snapshots each product’s duplicate-line data into plain Python structures, then re-browses the product fresh before calling the importer’s canonical line merge and Odoo variant regeneration. The variant cleanup loop was also changed to iterate by template ids with fresh browses.

**Decisions** - Kept the cleanup logic generic and reused the importer’s canonicalization helpers, but changed the execution model to avoid stale lazy field access after write/unlink side effects. This is safer than trying to suppress Odoo’s normal invalidation behavior around `product.template.attribute.line` updates.

**Risks / Pending Items** - The cleanup still performs real line normalization and variant regeneration, so it remains a significant operation on heavily configured products. The fix addresses the stale-recordset crash; it does not change the cleanup’s functional scope.

**Next steps** - Upgrade `pg_product_update`, retest the same multi-attribute duplicate product, and confirm the single-product cleanup completes without RPC failure. If another edge case appears, inspect whether it happens during attribute-line normalization or duplicate variant archival.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Attribute caches made cursor-safe across requests (2026-04-17)

**What changed** - Fixed the importer’s `_attribute_cache` and `_attribute_value_cache` in `pg_product_update/models/product_update.py` so they no longer store live ORM recordsets across requests. They now store ids and always re-browse fresh records before use. The getters also tolerate old in-memory cache entries that still contain recordsets by converting them to ids on access.

**Decisions** - Kept the cache optimization, but changed the cached payload from recordsets to scalar ids because class-level caches outlive request cursors on Odoo.sh workers. This is a safer generic pattern than trying to prevent all cross-request reuse of the cache buckets.

**Risks / Pending Items** - Minimal. The cache still works, but each hit now performs a cheap browse/exists() to guarantee a live recordset. This should eliminate the `Cursor already closed` failure pattern caused by stale cached records.

**Next steps** - Upgrade `pg_product_update`, retry the duplicate cleanup on the failing multi-attribute products, and confirm the action completes. If any later trace still points into `_ensure_attribute_line()`, inspect for another stale-recordset path, but the main attribute/value cache issue should now be closed.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template_attribute_line.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Duplicate cleanup made variant-limit safe (2026-04-17)

**What changed** - Adjusted the manual duplicate cleanup in `pg_product_update/models/product_update.py` so it no longer forces `_create_variant_ids()` during the cleanup action. Duplicate attribute-line normalization is now skipped on products whose estimated logical variant combination count exceeds the Odoo core `product.dynamic_variant_limit`, and the action still archives duplicate variants based on the currently existing variants. The notification now reports how many products had line cleanup skipped because of the variant limit.

**Decisions** - Aligned the cleanup safety check with Odoo core’s own variant limit parameter instead of letting the manual action trigger full variant regeneration and fail. Kept the button focused on duplicate variant remediation first; logical line cleanup is now best-effort and intentionally conservative on high-combination products.

**Risks / Pending Items** - On products above the variant limit, duplicate attribute rows may remain visible after the cleanup because line normalization is skipped for safety. Duplicate variants should still be archivable based on the existing variants, but full attribute-line normalization may need a more specialized path if later required.

**Next steps** - Upgrade `pg_product_update`, retry the failing high-combination products, and confirm the button completes without the variant-limit popup. If the remaining visible duplicate attribute rows become a problem, design a separate normalization path that does not rely on Odoo’s full variant regeneration.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/product/models/product_template.py`

### Milestone - Oversized/broken Drive file tracing and safeguards added (2026-04-10)

**What changed** - Extended `pg_product_update/models/product_update.py` with file-level tracing and pre-download size guards. The importer now records `image_candidate`, `image_download`, `image_resize`, `image_skip`, `image_error`, `document_candidate`, `document_download`, and `document_skip` events with file id, md5, and size. It also skips oversized images and documents based on Drive metadata before download, instead of only reacting after the payload is already in memory. The thumbnail fallback paths were updated to use the same image-size guard.

**Decisions** - Kept the protection generic and importer-wide rather than targeting specific products or folders. Used conservative hard limits to prevent a single huge file from killing the whole worker while still allowing typical media/doc payloads through. Preserved per-file try/except behavior so a bad file should not abort the whole product item by itself.

**Risks / Pending Items** - Hard limits can cause a specific oversized asset to be skipped rather than imported. This is intentional because it is preferable to losing the entire product item or worker. If the limits prove too strict in production, the next step is to move them to config parameters rather than removing the guard.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and inspect `Trace Log` for the recurring unaccounted items. If one of them contains a bad or oversized file, the job should now show a file-level `image_skip`, `image_error`, `document_skip`, or `document_error` event with the exact filename and size.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`

### Milestone - Drive import jobs now persist discovered and processed item ledgers (2026-04-09)

**What changed** - Extended `pg_product_update` job diagnostics beyond skip tracking. Each `product.update.drive.job` now persists a ledger of discovered IMAGENS items and successfully processed IMAGENS items, and computes an `unaccounted_count` plus preview for any discovered items that finish the job without ever being marked processed or skipped. The completion log now also warns when a job ends with unaccounted items.

**Decisions** - Kept the ledger data on the job model itself rather than depending on transient server logs. This makes post-run investigation possible directly from the dashboard/job form, which is important for mismatches like `489 discovered` vs `481 processed` where the previous skip telemetry stayed at zero.

**Risks / Pending Items** - The ledger adds some extra JSON writes during discovery and processing. The scale is still small relative to the overall Drive sync workload, but if import volume grows significantly, this may need pruning or a dedicated child model. The root cause of the unaccounted items is not yet fixed by this change; it is only made visible.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and inspect the new `Unaccounted` section in the dashboard/job form. Use those exact item names/IMAGENS ids to identify whether the remaining gap comes from discovery false-positives, mid-run accounting loss, or a hidden early-return path.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`

### Milestone - Fixed drive job telemetry regression on importer model (2026-04-09)

**What changed** - Fixed a regression introduced by the new discovered/processed ledger diagnostics in `pg_product_update/models/product_update.py`. The `product.update` model was incorrectly calling `_safe_json_load()`, which only exists on `product.update.drive.job`, causing jobs to fail early with `'product.update' object has no attribute '_safe_json_load'`. The importer now consistently uses its own `_json_load(..., [])` helper for job JSON fields.

**Decisions** - Kept the fix minimal and local to the importer model so the new telemetry remains intact. Did not duplicate `_safe_json_load()` across models because `product.update` already had an equivalent generic JSON loader.

**Risks / Pending Items** - This restores job execution, but it does not yet explain the underlying `489 discovered / 481 processed` mismatch. The next clean run is still required so the new `Unaccounted` telemetry can expose the actual missing items.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and inspect `Unaccounted` in the dashboard/job form. If items still disappear without being processed or skipped, use the new ledger output to trace the exact early-return path.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`

### Milestone - Drive dashboard unaccounted count now excludes in-flight items (2026-04-09)

**What changed** - Adjusted the `pg_product_update` dashboard/job telemetry so `unaccounted_count` no longer treats queued or currently processing IMAGENS folders as missing. The compute now subtracts `pending_imagens_json` and `current_item_id` from the discovered-vs-processed-vs-skipped diff. Also fixed the error path in `_process_next_job_pending_item()` so items dropped after exhausting max retries are recorded as skipped with reason `max_retries_exhausted` instead of silently becoming unaccounted.

**Decisions** - Kept `unaccounted` for true accounting gaps only. In-flight items are operationally normal and should not appear as missing. Exhausted-retry items are operational failures, so they now belong in `skipped` with an explicit reason instead of inflating `unaccounted`.

**Risks / Pending Items** - This should remove the early false-positive `Unaccounted=1` cases and reclassify real hard failures as skipped. If `unaccounted_count` still increases after this, the remaining path is likely a genuine ledger mismatch elsewhere in the processing flow.

**Next steps** - Upgrade `pg_product_update`, refresh the running dashboard, and verify that early in-progress jobs no longer show transient unaccounted items. If a final job still ends with unaccounted items, inspect those specific folders because they now represent a narrower set of true accounting leaks.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`

### Milestone - Generic fix for variant document sync and atomic processed accounting (2026-04-09)

**What changed** - Patched `pg_product_update/models/product_update.py` so variant-level Drive documents are no longer created as `shown_on_product_page=True`. Template documents remain website-visible; variant documents are now attached to the variant record without being flagged for the product page, which avoids the runtime validation errors seen during imports like `LED Évora LV`. Also made successful item accounting atomic by writing `processed_count`, clearing `current_item_id`, and updating `processed_items_json` in one committed step, instead of split commits that could leave items discovered but unaccounted if a worker died mid-accounting.

**Decisions** - Applied the fix generically at the importer layer rather than special-casing affected products. Kept the website-visible behavior only for template documents because the codebase and runtime behavior both indicate variant-restricted product-page documents are not supported cleanly in this stack. Added a reusable merge helper for job ledgers so processed/skipped item recording stays deduplicated.

**Risks / Pending Items** - This should reduce repeated document-attachment failures and remove one major source of false `unaccounted` items. It does not fully solve Odoo.sh worker memory limits if some products still have very heavy media payloads; if workers continue to be killed, the next investigation should focus on image/document download volume and cache lifetime per item.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and verify that products like `LED Évora LV` and `LED Spot30` move out of `Unaccounted`. If any still remain, inspect whether the worker is still being killed mid-item or whether another non-atomic path remains.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`, `vendor/odoo_core/odoo/addons/product/models/product_template.py`, `vendor/odoo_core/odoo/addons/documents_product/models/document.py`

### Milestone - Drive job trace logging added for unaccounted-item diagnosis (2026-04-09)

**What changed** - Added persistent per-item trace logging to `product.update.drive.job`. Jobs now store capped trace events covering processing start, processing success, retries/drops, and document-sync errors. The trace is exposed in both the job form and live dashboard through a new `Trace Log` section. This makes it possible to inspect the last persisted steps for an unaccounted product directly from Odoo, without relying only on raw server logs after the fact.

**Decisions** - Kept the trace generic and importer-wide instead of targeting specific products. Logged the stages most relevant to current failures: lifecycle transitions in `_process_next_job_pending_item()` and document attachment failures in `_process_additional_docs()`. Limited the stored event count so the job record remains bounded.

**Risks / Pending Items** - The trace increases write frequency slightly because it persists key lifecycle events to the job record. This is a deliberate tradeoff for observability. If extremely large runs make the trace too noisy, the next step would be per-item trace compaction rather than removing visibility.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and inspect `Trace Log` for the next unaccounted item. If `LED Évora LV` still becomes unaccounted, the trace should now show the last completed stage and whether document-sync errors or an abrupt interruption happened immediately before the item disappeared from accounting.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`, `vendor/odoo_core/odoo/addons/documents_product/models/document.py`

### Milestone - Drive job dashboard scroll fixed (2026-04-09)

**What changed** - Fixed the live dashboard layout in `pg_product_update/static/src/xml/drive_job_dashboard.xml` so the page scrolls normally. The dashboard template no longer nests an extra `.o_action` inside the client action wrapper and now uses a simple `h-100 overflow-auto` container for the dashboard body.

**Decisions** - Followed the Odoo web client layout behavior instead of adding ad hoc JavaScript scrolling. The outer action wrapper already exists in the web client, so keeping another inner `.o_action` was unnecessary and likely interfered with the expected scroll container.

**Risks / Pending Items** - This is a low-risk UI fix. Backend asset refresh is still required for the browser to pick up the updated template.

**Next steps** - Upgrade `pg_product_update`, refresh backend assets, and confirm the dashboard can scroll down to `Skipped Items`, `Unaccounted Items`, and `Trace Log`.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/web/static/src/webclient/webclient_layout.scss`

### Milestone - Interrupted current-item recovery added to Drive job runner (2026-04-10)

**What changed** - Patched `pg_product_update/models/product_update.py` so the Drive job runner now recovers stranded `current_item_id` values before processing the next queue item. If a worker dies after claiming an IMAGENS folder but before finishing it, the job now requeues that item with a `processing_recovered` trace instead of letting it disappear from `pending_imagens_json`. If recovery hits the retry limit, the item is recorded as skipped with source `interrupted_recovery_drop`. The runner also now clears `current_item_id` on retry and refuses to mark the job done while a current item is still set. Discovery now records `discovery_queue` trace events when items enter the queue.

**Decisions** - Kept the fix generic at the job-runner level because the issue affects any product claimed right before an interruption, not only the currently known unaccounted examples. Preserved the existing retry cap and reused the job trace/skipped-item telemetry rather than creating a separate recovery model.

**Risks / Pending Items** - This should close the main accounting gap for items that were discovered, claimed, and then lost after a worker interruption. If some products still end up unaccounted after this patch, the remaining issue is likely a different path than interrupted current-item loss.

**Next steps** - Upgrade `pg_product_update`, rerun the import, and inspect whether previously recurring unaccounted products like `LED Évora LV` and `LED Spot30` now show either `processing_recovered`, `processing_success`, or an explicit skipped reason instead of vanishing from accounting.

**Odoo Core (refs)** - `vendor/odoo_core/odoo/addons/base/models/ir_cron.py`
