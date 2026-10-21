
function DynShoppingCart(){

    this.init = () => {
        if (typeof prestashop !== 'undefined') {
            this.attach();
            this.eventListner();
            this.refreshCartContent();
        }else{
            return;

        }
    };

    this.refreshCartContent = () => {
        $('#dyncart>.item-list').html('');
        $('[data-cart="total"]').html(prestashop.cart.totals.total.value);
        $('[data-cart="total-products"]').html(prestashop.cart.subtotals.products.value);
        $('[data-cart="total-shipping"]').html(prestashop.cart.subtotals.shipping.value);
        for (var i = 0; i < prestashop.cart.products.length; i++) {
            $('#dyncart>.item-list').append(`
            <div class="cart-row">
              <div class="cart-image">
                <img src="`+prestashop.cart.products[i].cover.bySize.cart_default.url+`" title="">
              </div>
              <div class="item-info">
                <span class="name">`+prestashop.cart.products[i].name+`</span>
                <span class="attrsmall">`+prestashop.cart.products[i].attributes_small+`</span>
                <div class="item-qty">
                  <span class="qty"> <button data-action="qtydown"><i class="ti-minus"></i></button> <span class="quantity_wanted">`+prestashop.cart.products[i].quantity_wanted+`</span> <button data-action="qtyup"><i class="ti-plus"></i></button></span>
                  <span class="total">`+prestashop.cart.products[i].total+`</span>
                </div>
              </div>

              <span class="remove">
                <a href="`+prestashop.cart.products[i].remove_from_cart_url+`" data-action="remove"><i class="ti-close"></i></a>
              </span>
            </div>`);
        }
    };

    this.attach = () => {
    };

    this.toggle = () => {
        $('#dyncart').toggleClass('open');
        $('.cart-overlay').toggleClass('open');
    };

    this.eventListner = () => {
        var self = this;
        $('body').on('click', '[data-card="preview"]', function (event) {
            event.preventDefault();
            self.toggle();
        });
        $('body').on('click', '[data-action]', function (event) {
            event.preventDefault();
            var action = $(this).attr('data-action');
            if( action == 'remove' ){
              $.ajax({ type: 'GET', cache: false, url: $(this).attr('href'), data : {ajax:1},
                  complete: function(){},
                  beforeSend: function(){},
                  success: function( data ){
                      self.refreshCartContent();
                  },
                  error: function (xhr, ajaxOptions, thrownError){}
              });
            }else if( action == 'qtydown' || action == 'qtyup' ){

            }
        });
        $(document).click(function(event) {
            var $target = $(event.target);
            console.log($target);
            if($target.closest('.cart-overlay').length) {
                $('#dyncart').removeClass('open');
                $('.cart-overlay').removeClass('open');
            }
        });
        prestashop.on(
            'updateCart',
            function (event) {
                self.refreshCartContent();
                $('#dyncart').addClass('open');
                $('.cart-overlay').addClass('open');
            }
        );
    }
}

var _shoppingcart_ = new DynShoppingCart();

$(document).ready( function(){
    _shoppingcart_.init();
});