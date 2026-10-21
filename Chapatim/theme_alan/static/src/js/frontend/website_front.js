import { registry } from "@web/core/registry";
import { _t } from '@web/core/l10n/translation';
import { Interaction } from "@web/public/interaction";
import { ProductVariantDialog } from "theme_alan.ProductVariantDialog";
import { LoginPopup } from "@theme_alan/js/components/LoginPopup/login_popup";

// ─── Login Popup ─────────────────────────────────────────────────────────
export class AlanLoginPopup extends Interaction {
    static selector = '.as_login_popup';

    dynamicContent = {
        _root: {
            "t-on-click": this.onClickLoginPopup,
        },
    };

    async onClickLoginPopup(ev) {
        ev.preventDefault();
        const offcanvasEl = document.getElementById("top_menu_collapse_mobile");
        if (offcanvasEl && offcanvasEl.classList.contains('show')) {
            offcanvasEl.classList.remove('show');
            document.body.classList.remove('offcanvas-backdrop', 'modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            offcanvasEl.setAttribute('aria-hidden', 'true');
            offcanvasEl.setAttribute('aria-expanded', 'false');
            const backdrop = document.querySelector('.offcanvas-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
        this.services.dialog.add(LoginPopup, {});
    }
}

registry.category('public.interactions').add('AlanLoginPopup', AlanLoginPopup);

// ─── Product Variant Preview Dialog ───────────────────────────────────────
export class ProductVariantPreviewDialog extends Interaction {
    static selector = '.oe_product_cart.o_has_variations';

    dynamicContent = {
        '.o_product_variant_preview': {
            "t-on-click": this._onClick,
        },
    };

    async _onClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const productCard = ev.target.closest('.oe_product_cart');
        const templateId = this._getTemplateId(productCard);
        if (!templateId) return;
        this.services.dialog.add(ProductVariantDialog, {
            productTemplateId: templateId,
        });
    }

    _getTemplateId(productCard) {
        const input = productCard.querySelector('input[name="product_template_id"]');
        return input ? parseInt(input.value) : null;
    }
}
registry.category('public.interactions').add('theme_alan.product_variant_preview_dialog', ProductVariantPreviewDialog);


// ─── Comparison Differences ─────────────────────────────────────────────────
export class ComparisonDifferences extends Interaction {
    static selector = '.o_wsale_comparison_page';

    dynamicContent = {
        '#showOnlyDifferences': {
            "t-on-change": this.onToggleDifferences,
        },
    };

    setup() {
        super.setup();
        this.markAttributeRows();
        this.markTagsRow();
        this.markBrandRow();
    }

    markRow(row, getValue) {
        const values = [...row.querySelectorAll('li.o_wsale_compare_table_column')].map(getValue).map(v => v || '');
        const allSame = values.length && values.every(v => v === values[0]);
        row.dataset.allSame = allSame ? 'true' : 'false';
    }

    markAttributeRows() {
        this.el.querySelectorAll('ul[class*="o_ws_category_"]').forEach(row => {
            this.markRow(row, li => {
                const box = li.querySelector('#o_comparelist_attribute');
                if (!box) return '';

                const values = [...box.querySelectorAll('small')].map(el => el.textContent.trim());
                return values.length ? values.join(', ') : box.querySelector('h6.text-muted')?.textContent.trim() || '';
            });
        });
    }

    markTagsRow() {
        const tagsHeader = [...this.el.querySelectorAll('h6.d-table.position-sticky')].find(h => h.textContent.trim() === 'Tags');
        const tagsRow = tagsHeader?.nextElementSibling;
        if (!tagsRow) return;

        this.markRow(tagsRow, li =>
            [...li.querySelectorAll('span.text-nowrap.small')].map(t => t.textContent.trim()).filter(Boolean).sort().join(', ')
        );

        tagsRow.dataset.comparisonRow = 'tags';
    }

    markBrandRow() {
        const brandRow = [...this.el.querySelectorAll('ul.list-unstyled.d-flex')]
            .find(ul => ul.querySelector('#o_comparelist_brand'));

        if (!brandRow) return;
        this.markRow(brandRow, li => {
            const brand = li.querySelector('#o_comparelist_brand h6.small');
            return brand ? brand.textContent.trim() : '-';
        });
        brandRow.dataset.comparisonRow = 'brand';
    }

    onToggleDifferences(ev) {
        const showAll = !ev.currentTarget.checked;
        this.toggleAttributeRows(showAll);
        this.toggleTags(showAll);
        this.toggleBrand(showAll);
        showAll ? this.showAllCategoryHeaders() : this.updateCategoryHeaders();
    }

    toggleAttributeRows(show) {
        this.el.querySelectorAll(
            'ul[class*="o_ws_category_"][data-all-same="true"]'
        ).forEach(row => {
            row.style[show ? 'removeProperty' : 'setProperty']('display', 'none', 'important');
        });
    }

    // Tags (row + header)
    toggleTags(show) {
        const row = this.el.querySelector('ul[data-comparison-row="tags"]');
        if (!row || row.dataset.allSame !== 'true') return;

        const header = [...this.el.querySelectorAll('h6.d-table.position-sticky')]
            .find(h => h.textContent.trim() === 'Tags');

        [row, header].forEach(el => {
            if (!el) return;
            el.style[show ? 'removeProperty' : 'setProperty']('display', 'none', 'important');
        });
    }

    // Brand (row + header)
    toggleBrand(show) {
        const row = this.el.querySelector('ul[data-comparison-row="brand"]');
        if (!row || row.dataset.allSame !== 'true') return;

        const header = row.previousElementSibling?.classList.contains('w-100')
            ? row.previousElementSibling
            : null;

        [row, header].forEach(el => {
            if (!el) return;
            el.style[show ? 'removeProperty' : 'setProperty']('display', 'none', 'important');
        });
    }

    // Category headers
    updateCategoryHeaders() {
        this.el.querySelectorAll('div.w-100.py-3.bg-light').forEach(header => {
            if (header.textContent.includes('Brand')) return;

            let el = header.nextElementSibling;
            let visible = false;

            while (el && !el.classList.contains('w-100')) {
                if (el.tagName === 'UL' && el.offsetParent !== null) {
                    visible = true;
                    break;
                }
                el = el.nextElementSibling;
            }

            header.style[visible ? 'removeProperty' : 'setProperty']('display', 'none', 'important');
        });
    }

    showAllCategoryHeaders() {
        this.el.querySelectorAll('div.w-100.py-3.bg-light')
            .forEach(h => h.style.removeProperty('display'));
    }
}

registry.category('public.interactions').add('ComparisonDifferences', ComparisonDifferences);

// ─── Advance Megamenu ───────────────────────────────────────────────────────
export class AdvanceMegaMenu extends Interaction {
    static selector = '.as-advance-header';

    dynamicContent = {
        '.as-ah-mobile_menu': {
            "t-on-click": this.onClickLevel1,
        },
        '.as-ah-mobile_menu-l2': {
            "t-on-click": this.onClickLevel2,
        },
        '.as-ah-mobile_menu-l3': {
            "t-on-click": this.onClickLevel3,
        },
    };

    async onClickLevel1(ev) {
        ev.stopPropagation();
        const parent = ev.currentTarget.closest('.as-l1-items');
        if (parent) {
            parent.classList.add('as-ah-h1-open');
        }
    }

    async onClickLevel2(ev) {
        ev.stopPropagation();
        const parent = ev.currentTarget.closest('.as-l2-items');
        if (parent) {
            parent.classList.add('as-ah-h2-open');
        }
    }

    async onClickLevel3(ev) {
        ev.stopPropagation();
        const parent = ev.currentTarget.closest('.as-l3-items');
        if (parent) {
            parent.classList.add('as-ah-h3-open');
        }
    }
}

registry.category('public.interactions').add('AdvanceMegaMenu', AdvanceMegaMenu);

// ─── Mobile Menu ──────────────────────────────────────────────────────────
export class MobileMenu extends Interaction {
    static selector = '.as-mob-2nd-menu';

    dynamicContent = {
        // Open 2nd level menu
        '.as_mob_2nd_btn': {
            "t-on-click": this.onOpenSecondLevel,
        },

        // Close main menu
        '.as-bbl-1': {
            "t-on-click": this.onCloseMainMenu,
        },

        // Close Level 1 menu
        '.as-bbl-2': {
            "t-on-click": this.onCloseLevel1,
        },

        // Close Level 2 menu
        '.as-bbl-3': {
            "t-on-click": this.onCloseLevel2,
        },

        // Close Level 3 menu
        '.as-bbl-4': {
            "t-on-click": this.onCloseLevel3,
        },
    };

    // Handlers
    async onOpenSecondLevel(ev) {
        const nextEl = ev.currentTarget.nextElementSibling;
        if (nextEl) {
            nextEl.classList.add('as-advance-header-open');
        }
    }

    async onCloseMainMenu(ev) {
        const parent = ev.currentTarget.closest('.as-advance-header');
        if (parent) {
            parent.classList.remove('as-advance-header-open');
        }
    }

    async onCloseLevel1(ev) {
        const parent = ev.currentTarget.closest('.as-l1-items');
        if (parent) {
            parent.classList.remove('as-ah-h1-open');
        }
    }

    async onCloseLevel2(ev) {
        const parent = ev.currentTarget.closest('.as-l2-items');
        if (parent) {
            parent.classList.remove('as-ah-h2-open');
        }
    }

    async onCloseLevel3(ev) {
        const parent = ev.currentTarget.closest('.as-l3-items');
        if (parent) {
            parent.classList.remove('as-ah-h3-open');
        }
    }
}

registry.category('public.interactions').add('MobileMenu', MobileMenu);
