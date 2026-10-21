odoo.define('portal_users_expense.portal_users_expense', function (require){
'use_strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;
    var session = require('web.session');

    publicWidget.registry.PortalHrExpense =publicWidget.Widget.extend({
        selector: '.o_expense_request',
        events: {
            'change #product_id': '_onChangeProduct',
        },
        /**
         * @constructor
         */
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },
        /**
         * @private
         */
        render_monetary_field: function (value, currency_id) {
            value = value.toFixed(2);
            var currency = session.get_currency(currency_id);
            if (currency) {
                if (currency.position === "after") {
                    value += currency.symbol;
                } else {
                    value = currency.symbol + value;
                }
            }
            return value;
        },
        /**
         * @private
         */
        _onChangeProduct: function () {
            var selectProduct = $("select[name='product_id']");
            var self = this;
            if (!selectProduct.val()) {
                return;
            } else{
                ajax.jsonRpc("/onchange/product", 'call', {'product_id': selectProduct.val()}).then(function (data) {
                    $('.price_unit').attr('value', data.unit_price)
                });
            }
        },
    });
});