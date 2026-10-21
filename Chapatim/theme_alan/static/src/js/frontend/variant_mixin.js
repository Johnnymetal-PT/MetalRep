import { rpc } from '@web/core/network/rpc';
import { patch } from "@web/core/utils/patch";
import VariantMixin from '@website_sale/js/variant_mixin';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

// ─── Variant Mixin Extended for Alan Theme ─────────────────────────────────────────────────
VariantMixin._onChangeCombinationIntercalReference = function (ev, parent, combination) {
    const activeB2BMode = Boolean(combination.active_b2b_mode)
    const isPublicUser = Boolean(combination.is_public_user)
    const proDetailSection = parent.querySelector('.as_product_details_content_section_sci_info');

    // Show/Hide Additional Product Info Section
    if (proDetailSection) {
        if (combination.active_product_brand || combination.active_product_advance_info || combination.active_product_category || combination.active_product_reference || combination.active_shop_product_barcode) {
            proDetailSection.classList.remove('d-none');
        }
        else {
            proDetailSection.classList.add('d-none');
        }
    }

    // SKU update
    const productSKU = parent.querySelector('.as_product_sku');
    if (productSKU) {
        if (combination && combination.default_code) {
            productSKU.innerHTML = `<label>SKU:</label><span>${combination.default_code}</span>`;
            productSKU.classList.remove("d-none");
        } else {
            productSKU.innerHTML = "";
            productSKU.classList.add("d-none");
        }
    }

    // Offer Timer update
    const timerDiv = parent.querySelector('.as_offer_timer');
    if (timerDiv) {
        if (combination && combination.product_offer_timer && combination.product_offer_timer.date_end) {
            timerDiv.setAttribute('data-offer-end', combination.product_offer_timer.date_end || '');
            timerDiv.setAttribute('data-offer-start', combination.product_offer_timer.date_start || '');
            timerDiv.setAttribute('data-pricelist-item', combination.product_offer_timer.pricelist_item_id || '');
            timerDiv.setAttribute('data-applied-on', combination.product_offer_timer.applied_on || '');
            timerDiv.classList.remove('d-none');
        } else {
            timerDiv.classList.add('d-none');
        }
    }

    // Current Viewers update
    const currentViewer = parent.querySelector('.as_product_current_viewers');
    if (currentViewer) {
        if (combination && combination.current_viewers) {
            currentViewer.innerHTML = combination.current_viewers;
            currentViewer.classList.remove('d-none');
        } else {
            currentViewer.innerHTML = '';
            currentViewer.classList.add('d-none');
        }
    }

    // Product sold out info update
    const productSoldOutInfo = parent.querySelector('.as_product_sold_out_info');
    if (productSoldOutInfo) {
        if (combination.product_sold_count_info != false) {
            productSoldOutInfo.innerHTML = combination.product_sold_count_info
            productSoldOutInfo.classList.remove('d-none');

        }
        else {
            if (productSoldOutInfo) {
                productSoldOutInfo.innerHTML = ' '
                productSoldOutInfo.classList.add('d-none');
            }
        }
    }

    // Bulk Save Offer update
    const productBulkSaveOffer = parent.querySelector('.as_product_bulk_save_offer');
    const productBulkSaveOfferDiv = parent.querySelector('.as-wsale-product-details-extra-section');
    if (!productBulkSaveOffer) return;
    if (!productBulkSaveOfferDiv) return;
    if (combination.product_pricelist_item_ids && combination.product_pricelist_item_ids.length > 0) {
        const filteredRules = combination.product_pricelist_item_ids.filter(rule => rule.min_quantity > 0);
        const input = document.querySelector('input[name="add_qty"]');
        if (!input) return;
        const qty = parseInt(input.value, 10) || 0;
        if (filteredRules.length > 0 && !(activeB2BMode && isPublicUser)) {
            let html = `
                <div class="alan-bulk-title">
                    <i></i>
                    <span class="bulk-title">Discounts on Bulk Orders!</span>
                </div>
                <ul class="o_wsale_product_price_list">
            `;

            filteredRules.forEach(rule => {
                html += `
                    <li class="as-offer-item" data-min-qty="${Math.round(rule.min_quantity)}">
                        <div class="alan-bulk-text">
                            <span>
                                Buy <span class="as-offer-qty">${Math.round(rule.min_quantity)}</span>
                                <span>${combination.uom_name || "units"}</span>
                                <span class="d-block fw-normal">at</span>
                            </span>
                        </div>
                        <div class="alan-bulk-price">
                            <span>
                                <span class="alan-price">${rule.currency}${parseFloat(rule.price).toFixed(2)} </span>
                            </span>
                            <span> /units </span>
                        </div>
                    </li>
                `;
            });

            html += `</ul>
            <ul class="as-bulk-footer"><li class="as-selected-offer-item"><div class="as-bulk-total">Total : <span> ${filteredRules[0].currency}</span>${(filteredRules[0].price * filteredRules[0].min_quantity).toFixed(2)} </div><div class="as-bulk-save"><span class="as-save">(Save ${Math.round((((combination.list_price * filteredRules[0].min_quantity) - (filteredRules[0].price * filteredRules[0].min_quantity)) / (combination.list_price * filteredRules[0].min_quantity)) * 100)}%)</span><span class="as-bulk-total"> You save ${filteredRules[0].currency}${(combination.list_price * filteredRules[0].min_quantity).toFixed(2) - (filteredRules[0].price * filteredRules[0].min_quantity).toFixed(2)}  </span></div></li></ul>`;
            productBulkSaveOffer.innerHTML = html;
            productBulkSaveOffer.classList.remove("d-none");
            productBulkSaveOfferDiv.classList.remove("d-none");

            // Calculate maxMinQty once before the loop
            const allOfferItems = productBulkSaveOffer.querySelectorAll(".as-offer-item");
            const allMinQtys = Array.from(allOfferItems).map(offerItem =>
                parseInt(offerItem.dataset.minQty, 10) || 0
            );
            const maxMinQty = Math.max(...allMinQtys);

            // Bind click events to change product quantity
            allOfferItems.forEach((item, index) => {
                const minQty = parseInt(item.dataset.minQty, 10) || 0;

                // Mark as selected if minQty matches qty
                if (minQty === qty) {
                    item.classList.add("selected-offer");
                }

                // If qty exceeds all offers, mark the maxMinQty item as selected
                if (qty > maxMinQty && minQty === maxMinQty) {
                    item.classList.add("selected-offer");
                }

                item.addEventListener("click", () => {
                    if (minQty > 0) {
                        const addQtyInput = document.querySelector('input[name="add_qty"]');
                        if (addQtyInput) {
                            addQtyInput.value = minQty;
                            addQtyInput.dispatchEvent(new Event("change", { bubbles: true }));
                        }
                    }

                    productBulkSaveOffer.querySelectorAll(".as-offer-item").forEach(i => i.classList.remove("selected-offer"));
                    item.classList.add("selected-offer");
                    sessionStorage.setItem("as_bulk_selected_index", Array.from(productBulkSaveOffer.querySelectorAll(".as-offer-item")).indexOf(item));

                    // Update Total
                    const rule = filteredRules[index];
                    const totalDisplay = productBulkSaveOffer.querySelector(".as-selected-offer-item");
                    if (totalDisplay && rule) {
                        const total = (rule.price * rule.min_quantity).toFixed(2);
                        const saved = ((combination.list_price * rule.min_quantity).toFixed(2) - total).toFixed(2);
                        const percentage = Math.round((saved / (combination.list_price * rule.min_quantity)) * 100);
                        totalDisplay.innerHTML = `<div class="as-bulk-total">Total : ${total} <span> ${rule.currency}</span></div><div class="as-bulk-save"><span class="as-save">(Save ${percentage}%)</span> <span class="as-bulk-total"> You save ${saved} ${rule.currency} </span></div>`;
                    }
                });
            });
            const savedIndex = sessionStorage.getItem("as_bulk_selected_index");
            if (savedIndex !== null && productBulkSaveOffer.querySelectorAll(".as-offer-item")[savedIndex]) {
                // Update Total for restored item
                const rule = filteredRules[savedIndex];
                const totalDisplay = productBulkSaveOffer.querySelector(".as-selected-offer-item");
                if (totalDisplay && rule) {
                    const total = (rule.price * rule.min_quantity).toFixed(2);
                    const saved = ((combination.list_price * rule.min_quantity).toFixed(2) - total).toFixed(2);
                    const percentage = Math.round((saved / (combination.list_price * rule.min_quantity)) * 100);
                    totalDisplay.innerHTML = `<div class="as-bulk-total"> Total : ${total} <span> ${rule.currency}</span></div><div class="as-bulk-save"><span class="as-save">(Save ${percentage}%)</span> <span class="as-bulk-total"> You save ${saved} ${rule.currency} </span></div>`;
                }
            }
        } else {
            productBulkSaveOffer.innerHTML = "";
            productBulkSaveOffer.classList.add("d-none");
        }
    } else {
        productBulkSaveOfferDiv.classList.add("d-none");
        productBulkSaveOffer.innerHTML = "";
        productBulkSaveOffer.classList.add("d-none");
    }

    // Barcode update
    const productBarcode = parent.querySelector('.as_product_barcode');
    if (productBarcode) {
        if (combination && combination.barcode) {
            productBarcode.innerHTML = `<label>Barcode:</label> <span>${combination.barcode}</span>`;
            productBarcode.classList.remove("d-none");
        }
        else {
            productBarcode.innerHTML = "";
            productBarcode.classList.add("d-none");
        }
    }

    // Product Check Delivery Info update
    const zipInput = parent.querySelector('.as_zip_code_input');
    const checkBtn = parent.querySelector('#check_zip_btn');
    const zipResult = parent.querySelector('#zip_result');

    if (zipInput && checkBtn && zipResult) {
        checkBtn.addEventListener('click', async () => {
            const enteredZip = zipInput.value?.trim();
            if (!enteredZip) {
                zipResult.textContent = "Please enter a ZIP / Pincode";
                zipResult.className = "text-warning mt-1 d-block";
                return;
            }
            try {
                const response = await rpc('/shop/check_zip_code', {
                    zip_code: enteredZip
                });

                if (response && response.message) {
                    zipResult.textContent = response.message;
                    zipResult.className = `${response.css_class} mt-1 d-block`;
                }
            } catch (err) {
                console.error(err);
            }
        });
    }
    // Discount update
    const discount = parent.querySelector('.as-product-discounted');
    if (discount) {
        if (combination.has_discounted_price && combination.as_offer_discount) {
            discount.innerHTML = combination.as_offer_discount + ' %';
            discount.classList.remove('d-none');
        } else {
            discount.innerHTML = "";
            discount.classList.add('d-none');
        }
    }
}

// ─── Quick view hide extra div ─────────────────────────────────────────────────
patch(WebsiteSale.prototype, {
    _onChangeCombination(ev, parent, combination) {
        const availabilityContainer = parent.querySelector('div.availability_messages');
        if (availabilityContainer) {
            availabilityContainer.innerHTML = '';
        }
        super._onChangeCombination(...arguments);
        VariantMixin._onChangeCombinationIntercalReference(...arguments);
    },
});