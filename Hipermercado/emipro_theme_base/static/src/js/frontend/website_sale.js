import { patch } from '@web/core/utils/patch';
import { patchDynamicContent } from '@web/public/utils';
import publicWidget from "@web/legacy/js/public/public_widget";
import { WebsiteSale } from '@website_sale/interactions/website_sale';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { redirect, url } from '@web/core/utils/urls';
import { rpc } from "@web/core/network/rpc";
import { CartLine } from "@website_sale/interactions/cart_line";
import { CartService } from "@website_sale/js/cart_service";
let timer;

/* Update Cart Summary Helper Function */
async function updateCartSummary() {
    if (!$('.header_style_9').length) return;

    const locale = document.documentElement.lang || 'en-US';
    const orderId = parseInt($('.o_wsale_my_cart sup.my_cart_quantity').attr('data-order-id'));
    if (!orderId) return;

    const totalData = await rpc("/shop/cart/get_total", { order_id: orderId });
    const totalElement = document.querySelector(".my_cart_total");
    if (!totalElement) return;

    const formattedNumber = totalData.cart_total.toLocaleString(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    totalElement.textContent =
        totalData.cart_currency_position === "before"
            ? `${totalData.cart_currency} ${formattedNumber}`
            : `${formattedNumber} ${totalData.cart_currency}`;
}

patch(CartService.prototype, {
    async _makeRequest(data) {
        const result = await super._makeRequest.call(this, data);
        await updateCartSummary();
        return result;
    },
});

patch(CartLine.prototype, {
    async deleteProduct(ev) {
        await super.deleteProduct(ev);
        await updateCartSummary();
    },
    async _changeQuantity(input) {
        await super._changeQuantity.call(this, input);
        /* Passed cart summary details for header style 9 only */
        if ($('.header_style_9').length > 0){
            const locale = document.documentElement.lang || 'en-US';
            const lineId = parseInt(input.dataset.lineId);
            const productId = parseInt(input.dataset.productId);
            const quantity = parseInt(input.value || 0);

            const data = await rpc('/shop/cart/update', {
                line_id: lineId,
                product_id: productId,
                quantity: quantity,
            });
            const orderId = $('.o_wsale_my_cart sup.my_cart_quantity').attr('data-order-id');
            const totalElement = document.querySelector(".my_cart_total");
            if (totalElement) {
                const formattedNumber = data.cart_total.toLocaleString(locale, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                });
                if (data.cart_currency_position === "before") {
                    totalElement.textContent = `${data.cart_currency} ${formattedNumber}`;
                } else {
                    totalElement.textContent = `${formattedNumber} ${data.cart_currency}`;
                }
            }
            return data;
        }
    },
});

patch(WebsiteSale.prototype, {
    async setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            '.pricelist_table_row .table_content': {
                't-on-click': this._onClickQty.bind(this),
            },
//            'input[type="range"]': { 't-on-newRangeValue': this.onRangeSelected }
        });
        await updateCartSummary();
    },
     _onChangeCombination(ev, parent, combination) {
        super._onChangeCombination(...arguments);

         /* Offer timer changed while combination update */
        const current_date = combination.current_date
        const start_date = combination.start_date
        const end_date = combination.end_date
        const msg = combination.offer_msg || ''
        let append_date = '';
        if (end_date != parseInt($(".end_date").val())) {
            if (combination.is_offer && combination.current_date !== 'undefined') {
                append_date = "<div class='timer_input'><input type='hidden' class='current_date' value=" + current_date + "></input><input type='hidden' class='start_date' value=" + start_date + "></input><input type='hidden' class='end_date' value=" + end_date + "></input><div class='te_offer_timer_msg_div'><h6 class='te_offer_timer_prod fw-normal'>" + msg + "</p></h6></div></div>"
                $(".timer_data").html(append_date);
                $(".current_date").trigger('change');
            } else {
                $("#timer_portion_content_ept").removeClass("d-none");
                append_date = "<div class='timer_input'><input type='hidden' class='current_date' value=" + 0 + "></input><input type='hidden' class='start_date' value=" + 0 + "></input><input type='hidden' class='end_date' value=" + 0 + "></input></div>"
                $(".timer_data").html(append_date);
                $(".current_date").trigger('change');
            }
        }
        /* Update SKUs */
        $(".js_sku_div").html('N/A');
        if (combination.sku_details) {
            $(".js_sku_div").html(combination.sku_details);
        }
        if (combination.price_table_details) {
            $('.te_price_table').removeClass('d-none').html(combination.price_table_details)
        }

        /* Price table selection and qty will be set based on it */
        let getCurrQty = parseInt($('#product_detail .css_quantity .quantity').val());
        if(getCurrQty > 0){
            var finalSelection = this._checkPricelistArr(getCurrQty);
        }
        let blockQty = $(ev.currentTarget).attr('qty');
        if (blockQty){
            $('#product_detail .css_quantity .quantity').html(blockQty);
        }
        if (finalSelection != null){
            $('.table_content').removeClass('active');
            $('.table_content[qty="' + finalSelection + '"]').addClass('active');
        }
    },
    _setUrlHash() {
        super._setUrlHash();
        // Detect if quick view model and prevent to add attribute_values on the Url
        const isQuickView = document.querySelector('#quick_view_model') !== null;

        if (isQuickView) {
            const params = new URLSearchParams(window.location.search);
            params.delete('attribute_values');  // remove param entirely
            history.replaceState(null, '', window.location.pathname);  // clean URL
            return;
        }
    },
    _onClickQty(ev) {
        const $target = $(ev.currentTarget);
        const $qtyInput =  $(this.el.querySelector(".js_main_product input[name='add_qty']"));
        $(".table_content").removeClass("active");
        $target.addClass("active");
        const qtyValue = $target.find(".product_qty_span:first").text().trim();
        $qtyInput.val(qtyValue).trigger("change");
    },

    _checkPricelistArr(inputQty){
        const qtyValues = $(".pricelist_table_row .product_qty_span").map((_, el) => parseInt($(el).text().trim(), 10)).get().reverse();
        return qtyValues.find(qty => qty <= inputQty) ?? null;
    },

    onChangeAttribute(ev) {
        const productGrid = this.el.querySelector('.o_wsale_products_grid_table_wrapper');
        if (productGrid) {
            productGrid.classList.add('opacity-50');
        }

        const form = wSaleUtils.getClosestProductForm(ev.currentTarget);
        const filters = form.querySelectorAll("input:checked, select, input[name='attrib_range']");
        const attributeValues = new Map();
        const tags = new Set();
        const ratings = new Set();
        const out_of_stock = new Set();
        const range_filters = new Map();

        for (const filter of filters) {
            if (filter.value) {
                if (filter.name === 'attribute_value') {
                    const [attributeId, attributeValueId] = filter.value.split('-');
                    const valueIds = attributeValues.get(attributeId) ?? new Set();
                    valueIds.add(attributeValueId);
                    attributeValues.set(attributeId, valueIds);
                } else if (filter.name === 'tags') {
                    tags.add(filter.value);
                }
                else if (filter.name === 'rating') {
                    ratings.add(filter.value);
                }
                else if (filter.name === 'out_of_stock') {
                    out_of_stock.add(filter.value);
                }
                else if (filter.name === 'attrib_range') {
                    if(filter.valueLow !== undefined && filter.valueHigh !== undefined && ((filter.max != filter.valueHigh) || (filter.min != filter.valueLow))) {
                        range_filters.set(filter.id, `${filter.id},${filter.valueLow},${filter.valueHigh}`);
                    }
                }
            }
        }

        const url = new URL(form.action);
        const searchParams = url.searchParams;

        for (const entry of attributeValues.entries()) {
            searchParams.append('attribute_values', `${entry[0]}-${[...entry[1]].join(',')}`);
        }

        if (tags.size) {
            searchParams.set('tags', [...tags].join(','));
        }

        if (ratings.size) {
            for (const rating of ratings) {
                searchParams.append('rating', rating);
            }
        }

        if (out_of_stock.size) {
            searchParams.append('out_of_stock', 1);
        }

        for (const rangeValue of range_filters.values()) {
            searchParams.append('attrib_range', rangeValue);
        }

        redirect(`${url.pathname}?${searchParams.toString()}`);
    },

    async _addToCart(el) {
        const addToCart = await this.waitFor(super._addToCart(...arguments));
        await updateCartSummary();
        return addToCart;
    },
});

publicWidget.registry.timer_data = publicWidget.Widget.extend({
    selector: ".timer_data",
    events: {
        'change .current_date': 'initOfferTimer',
    },
    start: function() {
        this.redrow();
    },
    stop: function() {
        this.clean();
    },
    redrow: function(debug) {
        this.clean(debug);
        this.build(debug);
    },
    clean: function(debug) {
        this.$target.empty();
    },
    build: function(debug) {},
    initOfferTimer: function() {
        /* This method is called for initialize and update the offer timer in at product page*/
        let product_offer;
        clearInterval(timer);
        let count_start_date = parseInt($(".start_date").val());
        let count_end_date = parseInt($(".end_date").val());
        let current_date_time = parseInt($(".current_date").val());
        $("#timer_portion_content_ept").addClass("d-none");
        timer = setInterval(function() {
            if (count_start_date <= current_date_time && count_end_date >= current_date_time) {
                var duration = count_end_date - current_date_time;
                product_offer = true;
            } else {
                product_offer = false;
            }
            let seconds = "00";
            let days = "00";
            let minutes = "00";
            let hours = "00";
            if (duration > 0) {
                days = Math.floor(duration / (1000 * 60 * 60 * 24));
                hours = Math.floor((duration % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
                seconds = Math.floor((duration % (1000 * 60)) / 1000);

                if ((seconds + '').length == 1) {
                    seconds = "0" + seconds;
                }
                if ((days + '').length == 1) {
                    days = "0" + days;
                }
                if ((hours + '').length == 1) {
                    hours = "0" + hours;
                }
                if ((minutes + '').length == 1) {
                    minutes = "0" + minutes;
                }
                if (product_offer == true) {
                    $("#days").text(days);
                    $("#hours").text(hours);
                    $("#minutes").text(minutes);
                    $("#seconds").text(seconds);
                    $(".te_offer_timer_prod").css("display", "block");
                    $("#timer_portion_content_ept").removeClass("d-none");
                }
            }
            current_date_time += 1000
        }, 1000);
    }
});

publicWidget.registry.product_pager = publicWidget.Widget.extend({
    selector: ".next_prev_btn_main",
    events: {
        'mouseenter .product_next_btn, .product_prev_btn': 'getProductInfo',
        'mouseleave .product_next_btn, .product_prev_btn': 'removeProductInfo',
    },
    getProductInfo: function(ev) {
        const windowWidth = $(window).width();
        if (windowWidth > 992) {
            let product_id = $(ev.currentTarget).attr('product-id') || false;
            let params = {'product_id': product_id};
            rpc('/get_product_info', params).then(function (data) {
                $(ev.currentTarget).find('.main_product_container_append').html(data);
            });
        }
    },
    removeProductInfo: function(ev) {
        const windowWidth = $(window).width();
        if (windowWidth > 992) {
            $(ev.currentTarget).find('.main_product_container_append').html('');
        }
    },
});
