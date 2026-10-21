/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { WebsiteSale } from '@website_sale/interactions/website_sale';
import { patch } from "@web/core/utils/patch";
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { Interaction } from "@web/public/interaction";
import { registry } from '@web/core/registry';

export class QuickView extends Interaction {
    static selector = '#wrapwrap';
    dynamicContent = {
        '.quick-view-a': { 't-on-click': this._initQuickView },
        '.ajax_cart_popup': { 't-on-click': this._initQuickView },
        '.quick_close': { 't-on-click': this._quick_close },
        '#quick_view_model .modal-body #add_to_cart': { 't-on-click': this._quickAddToCart },
        '#quick_view_model .modal-body .js_add_cart_json': { 't-on-click': this._quickChangeQty },
        '#quick_view_model .modal-body input.quantity': { 't-on-change': this._quickQtyChanged },
    };
    async _initQuickView(ev) {
        ev.preventDefault()
        let element = ev.currentTarget;
        let product_id = $(element).attr('data-id');
        let params = {
            'product_id': product_id,
        }
        if (product_id){
            if($(ev.currentTarget).hasClass('quick-view-a')){
                $("#quick_view_model_shop .modal-body").addClass('quick_view_clicked');
            }

            rpc('/quick_view_item_data', params).then((data) => {
                const body = $("#quick_view_model .modal-body");
                body.html(data);
                $('#quick_view_model').modal('show');
                const publicInteractions = this.services['public.interactions'];
                publicInteractions.stopInteractions(body[0]);
                publicInteractions.startInteractions(body[0]);
                $('[data-bs-toggle="tooltip"]').tooltip({animation: true,delay: {show: 300,hide: 100} })
            });
        }
    }
    async _quick_close(){
        $('#quick_view_model_shop, #quick_view_model, #quick_view_model_popup').modal('hide');
        $("#quick_view_model_shop .modal-body, #quick_view_model .modal-body").html('');
    }
    async _priceTotalQuickView(ev){
        const locale = document.documentElement.lang || 'en-US';
        const orderId = $('.o_wsale_my_cart sup.my_cart_quantity').attr('data-order-id');
        const totalData = await rpc("/shop/cart/get_total", { order_id: parseInt(orderId) });
        const totalElement = document.querySelector(".my_cart_total");
        if (totalElement) {
            const formattedNumber = totalData.cart_total.toLocaleString(locale, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            if (totalData.cart_currency_position === "before") {
                totalElement.textContent = `${totalData.cart_currency} ${formattedNumber}`;
            } else {
                totalElement.textContent = `${formattedNumber} ${totalData.cart_currency}`;
            }
        }
    }
    // New: handle +/- buttons inside quick view modal
    async _quickChangeQty(ev){
        ev.preventDefault();
        const $modalBody = $('#quick_view_model').find('.modal-body');
        const $input = $modalBody.find('input.quantity');
        if (!$input || $input.length === 0) return;
        const $btn = $(ev.currentTarget);
        // Determine if button is minus or plus by icon or aria-label
        const isMinus = $btn.find('i').hasClass('fa-minus') || $btn.attr('aria-label') === 'Remove one';
        const min = parseInt($input.data('min') || 1);
        const max = parseFloat($input.data('max') || Infinity);
        let val = parseInt($input.val() || 0);
        if (isNaN(val)) val = min;
        val = isMinus ? val - 1 : val + 1;
        if (val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        $input.val(val).trigger('change');

        /* Passed cart summary details for header style 9 only */
        if ($('.header_style_9').length > 0){
            this._priceTotalQuickView(ev);
        }
    }
    // New: sanitize manual input changes in qty field
    async _quickQtyChanged(ev){
        const $input = $(ev.currentTarget);
        let val = parseInt($input.val() || 0);
        const min = parseInt($input.data('min') || 1);
        const max = parseFloat($input.data('max') || Infinity);
        if (isNaN(val) || val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        $input.val(val);

        /* Passed cart summary details for header style 9 only */
        if ($('.header_style_9').length > 0){
            this._priceTotalQuickView(ev);
        }
    }
    /**
     * Handle add to cart click inside the quick view modal using ajax (quick_add).
     * It collects product ids and quantity from the modal, calls '/shop/cart/quick_add'
     * and updates the cart/navbar with the returned data.
     */
    _quickAddToCart(ev){
        ev.preventDefault();
        const $modal = $('#quick_view_model');
        // Gather values from the quick view content
        const product_id = parseInt($modal.find('.product_id').val() || 0);
        const product_template_id = parseInt($modal.find('.product_template_id').val() || 0);
        let qty = parseInt($modal.find('.quantity').val() || 1);
        if (isNaN(qty) || qty < 1) qty = 1;

        if (!product_template_id || !product_id) {
            console.error('Quick View: missing product ids', product_template_id, product_id);
            return;
        }

        const params = {
            product_template_id: product_template_id,
            product_id: product_id,
            quantity: qty,
        };
        // Call quick_add which returns cart templates & quantities suitable to update the UI
        rpc('/shop/cart/quick_add', params).then(function(data){
            try{
                // 1) Update cart quantity in sessionStorage and navbar safely
                try{
                    if (typeof data.cart_quantity !== 'undefined' && data.cart_quantity !== null) {
                        try{
                            sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
                        }catch(e){
                            // sessionStorage may be unavailable in some contexts
                        }
                        const cartQuantityElements = document.querySelectorAll('.my_cart_quantity');
                        if (cartQuantityElements && cartQuantityElements.length) {
                            for (const cartQuantityElement of cartQuantityElements) {
                                try{
                                    if (data.cart_quantity === 0) {
                                        cartQuantityElement.classList.add('d-none');
                                    } else {
                                        const cartIconElement = document.querySelector('li.o_wsale_my_cart');
                                        if (cartIconElement) cartIconElement.classList.remove('d-none');
                                        cartQuantityElement.classList.remove('d-none');
                                        cartQuantityElement.classList.add('o_mycart_zoom_animation');
                                        setTimeout(() => {
                                            try{ cartQuantityElement.textContent = data.cart_quantity; }catch(err){}
                                            cartQuantityElement.classList.remove('o_mycart_zoom_animation');
                                        }, 300);
                                        /* Passed cart summary details for header style 9 only */
                                        if ($('.header_style_9').length > 0){
                                            const locale = document.documentElement.lang || 'en-US';
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
                                        }
                                    }
                                }catch(err){ console.warn('Failed to update cart quantity element', err); }
                            }
                        }
                    }
                }catch(err){ console.warn('Error updating cart quantity', err); }

                // 2) Insert cart lines if present on page and if server returned them
                try{
                    if (typeof $ !== 'undefined' && $('.js_cart_lines').length > 0 && data['website_sale.cart_lines']){
                        try{ $('.js_cart_lines').first().before(data['website_sale.cart_lines']).end().remove(); }catch(err){ console.warn('Failed to insert cart lines', err); }
                    }
                }catch(err){ console.warn('Error checking/inserting cart lines', err); }

                // 3) Update totals if target exists
                try{
                    if (data['website_sale.total'] && document.querySelectorAll('div.o_cart_total').length > 0){
                        try{ document.querySelectorAll('div.o_cart_total').forEach(div => div.innerHTML = data['website_sale.total']); }catch(err){ console.warn('Failed to update cart total', err); }
                    }
                }catch(err){ console.warn('Error updating cart total', err); }

                // 4) Update shorter cart summary if the element exists (use wSaleUtils helper if available)
                try{
                    if (data['website_sale.shorter_cart_summary'] && document.querySelector('.o_wsale_shorter_cart_summary')){
                        try{ wSaleUtils.updateCartSummary && wSaleUtils.updateCartSummary(data); }catch(err){
                            // Fallback: set innerHTML safely
                            try{ document.querySelector('.o_wsale_shorter_cart_summary').innerHTML = data['website_sale.shorter_cart_summary']; }catch(e){ console.warn('Failed to set shorter cart summary', e); }
                        }
                    }
                }catch(err){ console.warn('Error updating shorter cart summary', err); }

                // 5) Update quick reorder history if present
                try{
                    if (data['website_sale.quick_reorder_history'] && document.querySelector('#quick_reorder_sidebar .offcanvas-body')){
                        try{ document.querySelector('#quick_reorder_sidebar .offcanvas-body').insertAdjacentHTML('afterbegin', data['website_sale.quick_reorder_history']); }catch(err){ console.warn('Failed to update quick reorder history', err); }
                    }
                }catch(err){ console.warn('Error updating quick reorder history', err); }

                // 6) Show any warning/notification
                try{
                    if (typeof wSaleUtils !== 'undefined'){
                        try{ wSaleUtils.showWarning(data.notification_info && data.notification_info.warning); }catch(err){ console.warn('wSaleUtils.showWarning failed', err); }
                    } else if (data.notification_info && data.notification_info.warning){
                        console.warn('Cart warning:', data.notification_info.warning);
                    }
                }catch(err){ console.warn('Error showing cart warning', err); }

                // 7) Track products if needed
                try{
                    if (data.tracking_info) {
                        try{ document.querySelector('.oe_website_sale')?.dispatchEvent(new CustomEvent('add_to_cart_event', {'detail': data.tracking_info})); }catch(e){/* ignore */}
                    }
                }catch(err){ /* ignore */ }

            }catch(err){
                console.error('Error updating cart UI after quick_add', err);
            }
            // Close and clear modal
            $modal.modal('hide');
            $modal.find('.modal-body').html('');
            // Optionally redirect to cart if server requested it (controller could set cart redirect by returning quantity and flags)
            if (data && data.should_redirect) {
                window.location = '/shop/cart';
            }
        }).catch(function(err){
            console.error('Quick add to cart failed', err);
        });
    }
}
registry.category('public.interactions').add('theme_clarico_vega.quick_view', QuickView);

/*override base method and remove quick view popup because optional product popup was not editable when quick view is render*/
patch(WebsiteSale.prototype, {
    onClickAdd(ev){
        $('#quick_view_model_shop, #quick_view_model, #quick_view_model_popup').modal('hide');
        $("#quick_view_model_shop .modal-body, #quick_view_model .modal-body").html('');
        return super.onClickAdd(...arguments);
    },
});
