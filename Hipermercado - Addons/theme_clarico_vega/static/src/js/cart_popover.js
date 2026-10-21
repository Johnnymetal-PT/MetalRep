import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from '@website_sale/js/website_sale_utils';

// Safe replacement for wSaleUtils.updateCartNavBar that checks DOM elements before touching them
function safeUpdateCartNavBar(data){
    try{
        try{ sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity); }catch(e){}
        const cartQuantityElements = document.querySelectorAll('.my_cart_quantity');
        for (const cartQuantityElement of cartQuantityElements) {
            try{
                if (data.cart_quantity === 0) {
                    cartQuantityElement.classList.add('d-none');
                } else {
                    const cartIconElement = document.querySelector('li.o_wsale_my_cart');
                    if (cartIconElement && cartIconElement.classList) {
                        cartIconElement.classList.remove('d-none');
                    }
                    if (cartQuantityElement.classList) {
                        cartQuantityElement.classList.remove('d-none');
                        cartQuantityElement.classList.add('o_mycart_zoom_animation');
                        setTimeout(() => {
                            try{ cartQuantityElement.textContent = data.cart_quantity; }catch(e){}
                            try{ cartQuantityElement.classList.remove('o_mycart_zoom_animation'); }catch(e){}
                        }, 300);
                    }
                }
            }catch(e){ console.warn('safeUpdateCartNavBar: per-element failure', e); }
        }

        // Insert cart lines if the element exists (jQuery required)
        try{
            if (typeof $ !== 'undefined' && $('.js_cart_lines').length > 0 && data['website_sale.cart_lines']){
                try{ $('.js_cart_lines').first().before(data['website_sale.cart_lines']).end().remove(); }catch(err){ console.warn('safeUpdateCartNavBar: insert cart_lines failed', err); }
            }
        }catch(e){ /* ignore */ }

        // Update cart summary safely
        try{
            if (data['website_sale.shorter_cart_summary'] && document.querySelector('.o_wsale_shorter_cart_summary')){
                try{ wSaleUtils.updateCartSummary && wSaleUtils.updateCartSummary(data); }catch(err){
                    try{ document.querySelector('.o_wsale_shorter_cart_summary').innerHTML = data['website_sale.shorter_cart_summary']; }catch(e){ console.warn('safeUpdateCartNavBar: update shorter summary failed', e); }
                }
            }
        }catch(e){ console.warn('safeUpdateCartNavBar: updateCartSummary guard failed', e); }

        // Update totals safely
        try{
            if (data['website_sale.total'] && document.querySelectorAll('div.o_cart_total').length > 0){
                try{ document.querySelectorAll('div.o_cart_total').forEach(div => div.innerHTML = data['website_sale.total']); }catch(err){ console.warn('safeUpdateCartNavBar: update total failed', err); }
            }
        }catch(e){ /* ignore */ }

        // Toggle .oe_cart class safely
        try{
            const oeCart = document.querySelector('.oe_cart');
            if (oeCart && oeCart.classList) oeCart.classList.toggle('col-lg-7', !!data.cart_quantity);
        }catch(e){ /* ignore */ }

        // Enable/disable main checkout button safely
        try{
            const mainBtn = document.querySelector("a[name='website_sale_main_button']");
            if (mainBtn && mainBtn.classList) {
                if (data.cart_ready) mainBtn.classList.remove('disabled'); else mainBtn.classList.add('disabled');
            }
        }catch(e){ /* ignore */ }
    }catch(err){ console.warn('safeUpdateCartNavBar failed', err); }
}

// Helper: attach qty/plus/minus/delete handlers inside given container
function attachCartHandlers($container){
    if (!$container || $container.length === 0) return;
    // If global delegation is attached, avoid per-container binding to prevent duplicate handlers
    if (typeof window !== 'undefined' && window._themeCartPopoverDelegationAttached) {
        console.debug('attachCartHandlers: delegation active, skipping per-container bindings');
        return;
    }
    console.debug('attachCartHandlers: attaching handlers, container length=', $container.length);
    // +/- buttons
    $container.find('.js_add_cart_json').off('click').on('click', function(ev){
        ev.preventDefault();
        console.debug('attachCartHandlers: js_add_cart_json clicked');
        const $btn = $(this);
        const $qtyInput = $btn.closest('.css_quantity').find('input.js_quantity');
        if (!$qtyInput || $qtyInput.length === 0) return;
        const isMinus = $btn.find('i').hasClass('fa-minus') || $btn.attr('aria-label') === 'Remove one';
        const min = parseInt($qtyInput.data('min') || 1);
        const max = parseFloat($qtyInput.data('max') || Infinity);
        let val = parseInt($qtyInput.val() || 0);
        if (isNaN(val)) val = min;
        val = isMinus ? val - 1 : val + 1;
        if (val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        // update via rpc
        updateCartLineFromInput($qtyInput, val);
    });

    // manual change
    $container.find('input.js_quantity').off('change').on('change', function(ev){
        console.debug('attachCartHandlers: js_quantity change');
        const $input = $(this);
        let val = parseInt($input.val() || 0);
        const min = parseInt($input.data('min') || 1);
        const max = parseFloat($input.data('max') || Infinity);
        if (isNaN(val) || val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        $input.val(val);
        updateCartLineFromInput($input, val);
    });

    // delete product (set quantity 0)
    $container.find('.js_delete_product').off('click').on('click', function(ev){
        ev.preventDefault();
        console.debug('attachCartHandlers: js_delete_product clicked');
        const $row = $(this).closest('.o_cart_product, .cart_line');
        const $input = $row.find('input.js_quantity');
        if ($input && $input.length) {
            updateCartLineFromInput($input, 0);
        } else {
            const lineId = $(this).data('line-id') || $(this).attr('data-line-id');
            if (lineId) {
                const $tmp = $('<input/>').attr('data-line-id', lineId);
                updateCartLineFromInput($tmp, 0);
            }
        }
    });
}

// Helper to perform rpc update from an input element
async function updateCartLineFromInput($input, quantity){
    console.debug('updateCartLineFromInput', {lineId: $input.data('line-id'), productId: $input.data('product-id'), quantity: quantity});
    const lineId = parseInt($input.data('line-id') || 0);
    const productId = parseInt($input.data('product-id') || 0);
    try{
        const data = await rpc('/shop/cart/update', { line_id: lineId, product_id: productId, quantity: quantity });
        if (!data.cart_quantity) {
            try { sessionStorage.setItem('website_sale_cart_quantity', 0); }catch(e){}
            return window.location = '/shop/cart';
        }
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
        // Update all matching inputs
        $(`input.js_quantity[data-line-id="${lineId}"]`).each(function(){ $(this).val(data.quantity); });
        try{
            // Only call the core helper if the expected navbar elements exist
            const cartIcon = document.querySelector('li.o_wsale_my_cart');
            const cartQtyElems = document.querySelectorAll('.my_cart_quantity');
            if (typeof wSaleUtils !== 'undefined' && cartIcon && cartQtyElems.length > 0) {
                try{ safeUpdateCartNavBar(data); }catch(e){ console.warn('safeUpdateCartNavBar failed', e); }
            } else {
                // Fallback: update quantity elements safely without relying on the utility
                try{
                    if (typeof data.cart_quantity !== 'undefined'){
                        try{ sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity); }catch(e){}
                        const elems = document.querySelectorAll('.my_cart_quantity');
                        elems.forEach(el => {
                            try{
                                if (data.cart_quantity === 0) {
                                    el.classList.add('d-none');
                                } else {
                                    // ensure cart icon is visible if present
                                    if (cartIcon) cartIcon.classList.remove('d-none');
                                    el.classList.remove('d-none');
                                    el.textContent = data.cart_quantity;
                                }
                            }catch(err){ /* ignore per-element errors */ }
                        });
                    }
                }catch(err){ console.warn('Fallback cart nav update failed', err); }
            }
        }catch(e){ console.warn('updateCartNavBar guard failed', e); }
        try{
            // Only call updateQuickReorderSidebar if the quick reorder button exists
            // The utility accesses the button and calls .click(), so it must be present.
            const quickReorderButton = document.getElementById('quick_reorder_button');
            const quickReorderBody = document.querySelector('#quick_reorder_sidebar .offcanvas-body');
            if (typeof wSaleUtils !== 'undefined' && quickReorderButton && quickReorderBody) {
                try{ wSaleUtils.updateQuickReorderSidebar(data); }catch(e){ console.warn('updateQuickReorderSidebar failed', e); }
            } else {
                console.debug('Skipping updateQuickReorderSidebar: quick reorder elements missing', {quickReorderButton: !!quickReorderButton, quickReorderBody: !!quickReorderBody});
            }
        }catch(e){ console.warn('updateQuickReorderSidebar guard failed', e); }
        try{ wSaleUtils.showWarning && wSaleUtils.showWarning(data.warning || (data.notification_info && data.notification_info.warning)); }catch(e){ /* ignore */ }
        // Refresh popover content if present
        try{
            if (typeof $ !== 'undefined' && $('#cartoffcanvasWithBackdrop .offcanvas-body').length){
                const fresh = await $.get('/shop/cart_popover');
                const $container = $("#cartoffcanvasWithBackdrop .offcanvas-body");
                $container.html(fresh);
                attachCartHandlers($container);
            }
        }catch(err){ console.warn('Could not refresh cart popover after update', err); }
    }catch(err){ console.error('Cart update failed', err); }
}

// Ensure handlers attach when the offcanvas is shown (covers server-rendered popover)
$(document).on('shown.bs.offcanvas', '#cartoffcanvasWithBackdrop', function(){
    const $container = $("#cartoffcanvasWithBackdrop .offcanvas-body");
    attachCartHandlers($container);
});

// Attach delegated handlers once for the offcanvas to reliably catch events in server-rendered templates
if (typeof window !== 'undefined' && !window._themeCartPopoverDelegationAttached) {
    window._themeCartPopoverDelegationAttached = true;

    // +/- buttons (delegated)
    $(document).on('click', '#cartoffcanvasWithBackdrop .js_add_cart_json', function(ev){
        ev.preventDefault();
        const $btn = $(this);
        const $qtyInput = $btn.closest('.css_quantity').find('input.js_quantity');
        if (!$qtyInput || $qtyInput.length === 0) return;
        const isMinus = $btn.find('i').hasClass('fa-minus') || $btn.attr('aria-label') === 'Remove one';
        const min = parseInt($qtyInput.data('min') || 1);
        const max = parseFloat($qtyInput.data('max') || Infinity);
        let val = parseInt($qtyInput.val() || 0);
        if (isNaN(val)) val = min;
        val = isMinus ? val - 1 : val + 1;
        if (val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        updateCartLineFromInput($qtyInput, val);
    });

    // manual change (delegated)
    $(document).on('change', '#cartoffcanvasWithBackdrop input.js_quantity', function(ev){
        const $input = $(this);
        let val = parseInt($input.val() || 0);
        const min = parseInt($input.data('min') || 1);
        const max = parseFloat($input.data('max') || Infinity);
        if (isNaN(val) || val < min) val = min;
        if (isFinite(max) && val > max) val = max;
        $input.val(val);
        updateCartLineFromInput($input, val);
    });

    // delete product (delegated)
    $(document).on('click', '#cartoffcanvasWithBackdrop .js_delete_product', function(ev){
        ev.preventDefault();
        const $row = $(this).closest('.o_cart_product, .cart_line');
        const $input = $row.find('input.js_quantity');
        if ($input && $input.length) {
            updateCartLineFromInput($input, 0);
        } else {
            const lineId = $(this).data('line-id') || $(this).attr('data-line-id');
            if (lineId) {
                const $tmp = $('<input/>').attr('data-line-id', lineId);
                updateCartLineFromInput($tmp, 0);
            }
        }
    });
}

publicWidget.registry.websiteSaleCartLinkEpt = publicWidget.Widget.extend({
    selector: '.o_wsale_my_cart #main_cart_popover_content',
    events: {
        'click': '_cartPopupData',
    },

    // Fetch popover HTML and attach handlers
    _cartPopupData: async function(ev) {
        ev.preventDefault();
        try{
            const data = await $.get('/shop/cart_popover');
            const $container = $("#cartoffcanvasWithBackdrop .offcanvas-body");
            $container.html(data);

            // Attach clear cart handler
            $container.find(".te_clear_cart_popover").off('click').on('click', (ev) => {
                ev.preventDefault();
                rpc('/shop/clear_cart', {}).then(function (res) {
                    location.reload();
                    $(".my_cart_quantity").html('0');
                });
            });

            // Attach quantity handlers
            attachCartHandlers($container);
        }catch(err){
            console.error('Failed to load cart popover', err);
        }
    },
});
