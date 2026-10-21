import { patch } from '@web/core/utils/patch';
import { patchDynamicContent } from '@web/public/utils';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            '.js_add_cart_json': {
                't-on-click': this.onChangeCartQuantity.bind(this),
            },
            /*'input.js_quantity[data-product-id]': {
                't-on-change': this.onChangeCartQuantity.bind(this),
            },
            '.js_delete_product': {
                't-on-click': this.onClickRemoveItem.bind(this),
            },*/
        });
    },

    onChangeCartQuantity: function (ev) {
//        debugger;
//        alert('sdfsdf');
    },
    /*onClickRemoveItem(ev){
        $(ev.currentTarget).parent().siblings().find('.js_quantity').val(0).trigger('change');
        $(ev.currentTarget).parent().parent().remove();
        this.onClickFreeShipTextUpdate(ev);
    },
    onClickFreeShipTextUpdate(ev){
        setTimeout(function(){
            let $order_total_price = parseFloat($('#order_total .oe_currency_value').text().replace(/[^0-9.]/g, ''));
            let $offer_cart_price = parseFloat($('.offer_price').text().replace(/[^0-9.]/g, ''));
            let result = $order_total_price - $offer_cart_price;
            *//*Progress bar design*//*
            let progressPercent = Math.min(($order_total_price / $offer_cart_price) * 100, 100);

            if($order_total_price < $offer_cart_price) {
                $('.main_free_ship_data .oe_currency_value').text(Math.abs(result).toFixed(2));
                $('.not_free_ship_text').removeClass('d-none');
                $('.final_msg_ship').addClass('d-none');
                $('.first_main_freeship_price').removeClass('d-none');
                $('.free_ship_not_added').removeClass('d-none');
                $('.progress-fill').css('width', `${progressPercent}%`);
                $('.progress-percentage').text(`${Math.floor(progressPercent)}%`);
            }
            else{
                $('.main_free_ship_data .oe_currency_value').text('0');
                $('.not_free_ship_text').addClass('d-none');
                $('.final_msg_ship').removeClass('d-none');
                $('.first_main_freeship_price').addClass('d-none');
                $('.free_ship_not_added').addClass('d-none');
                $('.progress-fill').css('width', `${progressPercent}%`);
                $('.progress-percentage').text(`${Math.floor(progressPercent)}%`);
            }
        }, 2000);
    },*/
});
