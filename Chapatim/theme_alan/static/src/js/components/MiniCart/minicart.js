/** @odoo-module alias=theme_alan.MiniCart **/

import { rpc } from "@web/core/network/rpc";
import { Dialog } from "@web/core/dialog/dialog";
import { useDebounced } from "@web/core/utils/timing";
import { Component, onWillStart, useState } from "@odoo/owl";
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { useService } from "@web/core/utils/hooks";

// ─── MiniCart Line ─────────────────────────────────────────────────
export class MiniCartLine extends Component {
    static template = "theme_alan.Minicartline";
    static props = {
        line_id: Number,
        productId: Number,
        product_tmp_id: Number,
        image_url: String,
        website_url: String,
        line_header: String,
        description_lines: Array,
        combination_name: Object,
        has_multiple_uoms: Boolean,
        formated_product_price: String,
        product_uom: String,
        show_strikethrough_price: Boolean,
        strikethrough_price: String,
        main_obj: Object,
        product_uom_qty: Number,
        cart_quantity: { type: Number, optional: true },
        is_reward_line: { type: Boolean, optional: true },
        reward_type: { type: String, optional: true },
    };

    setup() {
        super.setup();
        this.state = useState({
            add_quantity: this.props.product_uom_qty,
            cart_quantity: this.props.cart_quantity || 0,
        });

        this.wishlistProductIDs = JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
        this.debouncedUpdateQuantity = useDebounced(this._updateQuantity.bind(this), 500, {
            execBeforeUnmount: true,
        });
    }

    async _updateQuantity() {
        const data = await rpc('/shop/cart/update', {
            line_id: parseInt(this.props.line_id),
            product_id: parseInt(this.props.product_id),
            quantity: this.state.add_quantity,
        });
        wSaleUtils.updateCartNavBar(data);
        await this.props.main_obj.loadMiniCart();
    }

    onIncreaseQuantity() {
        if (this.props.is_reward_line && this.props.reward_type === 'product') {
            return;
        }
        this.state.add_quantity++;
        this.state.cart_quantity++;
        this.debouncedUpdateQuantity();
    }

    onDecreaseQuantity(event) {
        if (this.props.is_reward_line && this.props.reward_type === 'product') {
            event.target.value = this.state.add_quantity;
            return;
        }

        if (this.state.add_quantity === 1 && $('.as_mini_cart_products').find('li.as_mini_cart_product_line').length === 1) {
            this.props.main_obj.clearCart();
        } else if (this.state.add_quantity > 0) {
            this.state.add_quantity--;
            this.state.cart_quantity--;
            this.debouncedUpdateQuantity();
        }
    }

    onQuantityInputChange(event) {
        const quantity = parseInt(event.target.value, 10);
        this.state.add_quantity = isNaN(quantity) || quantity <= 0 ? 1 : quantity;
        event.target.value = this.state.add_quantity;
        this.debouncedUpdateQuantity();
    }

    get disableRemove() {
        return this.state.add_quantity <= 0;
    }

    async removeProduct() {
        if ($('.as_mini_cart_products').find('li.as_mini_cart_product_line').length == 1) {
            await this.props.main_obj.clearCart()
        }
        else {
            this.state.add_quantity = 0
            this.debouncedUpdateQuantity();
        }
    }

    async saveForLater() {
        if (this.props.product_id) {
            await this.removeProduct()
            if (!this.wishlistProductIDs.includes(parseInt(this.props.product_id))) {
                await rpc('/shop/wishlist/add', {
                    product_id: parseInt(this.props.product_id),
                }).then(function () {
                    const $navButton = $('header .o_wsale_my_wish').first();
                    const $wishButton = $('.o_wsale_my_wish');
                    const qty = $wishButton.find('.my_wish_quantity').html();
                    wSaleUtils.animateClone($navButton, $('.form'), 25, 40);
                    $wishButton.find('.my_wish_quantity').text(parseInt(qty) + 1);
                })
            }
        }
    }
}

// ─── MiniCart ─────────────────────────────────────────────────
export class MiniCart extends Component {
    static template = "theme_alan.Minicart";
    static components = { Dialog, MiniCartLine };
    static props = { card_qty: { type: Number, optional: true } };

    setup() {
        this.state = useState({
            product_lines: [],
            suggested_products: [],
            cart_summary: {},
            showCouponForm: false,
            coupon_error: null,
            coupon_success: null,
            promo_code: null,
            website_sale_order: null,
            isProcessing: false,
        });
        this.cartService = useService("cart");
        onWillStart(this.loadMiniCart);
    }

    loadMiniCart = async () => {
        try {
            const data = await rpc("/get_mini_cart");
            Object.assign(this.state, {
                product_lines: data.website_order_lines,
                suggested_products: data.suggested_products,
                cart_summary: data.cart_summary,
            });
            this.props.card_qty = data.cart_quantity;
            if (data.claimable_rewards && data.claimable_rewards.length > 0) {
                this.state.website_sale_order = {
                    claimable_rewards: data.claimable_rewards,
                    reward_amount: data.cart_summary.reward_amount || 0,
                };
            }
        } catch (error) {
            console.error("Error loading mini cart:", error);
        }
    };

    async clearCart() {
        await rpc("/as_clear_cart");
        Object.assign(this.state, {
            product_lines: [],
            suggested_products: [],
            cart_summary: {},
            coupon_error: null,
            coupon_success: null,
            promo_code: null,
            website_sale_order: null,
        });
        this.props.card_qty = 0;
        const badge = document.querySelector(".my_cart_quantity");
        if (badge) badge.textContent = "0";
    }

    async addSuggestedProduct(product_id, product_tmpl_id) {
        await this.cartService.add({
            productTemplateId: parseInt(product_tmpl_id, 10),
            productId: parseInt(product_id, 10),

        }, {
            isBuyNow: true,
            isConfigured: false,
            showQuantity: true,
            redirectToCart: false,
        });
        await this.loadMiniCart();
    }

    toggleCouponForm() {
        this.state.showCouponForm = !this.state.showCouponForm;
    }

    async applyCoupon(ev) {
        ev.preventDefault();

        if (this.state.isProcessing) {
            return;
        }

        const form = ev.target.closest("form");
        const promoInput = form.querySelector("input[name='promo']");
        const promo = promoInput.value.trim();

        if (!promo) {
            this.state.coupon_error = "Please enter a promo code";
            return;
        }

        try {
            this.state.isProcessing = true;
            this.state.coupon_error = null;
            this.state.coupon_success = null;
            this.state.website_sale_order = null;
            const result = await rpc("/apply_coupon", { promo });

            if (result.error || result.promo_error) {
                this.state.coupon_error = result.promo_error || result.error;
                this.state.website_sale_order = result.website_sale_order;
                const miniCart = await rpc('/get_mini_cart', {});
                this.state.claimable_rewards = miniCart.claimable_rewards;
            } else if (result.promo_success) {
                this.state.promo_code = result.promo_code || promo;
                this.state.coupon_success = result.promo_success;
                this.state.website_sale_order = result.website_sale_order;
                promoInput.value = '';
                await this.loadMiniCart();
            } else {
                this.state.coupon_error = "Unable to apply promo code. Please try again.";
            }
        } catch (error) {
            console.error("Error applying coupon:", error);
            this.state.coupon_error = error.message || "Failed to apply promo code";
        } finally {
            this.state.isProcessing = false;
        }
    }

    async claimReward(ev) {
        ev.preventDefault();
        if (this.state.isProcessing) {
            return;
        }
        const form = ev.target.closest("form");
        const rewardId = form.querySelector("input[name='reward_id']").value;
        const code = form.querySelector("input[name='code']").value;
        const productSelect = form.querySelector("select[name='product_id']");
        const productId = productSelect ? productSelect.value : null;

        try {
            this.state.isProcessing = true;
            this.state.coupon_error = null;

            const result = await rpc("/claim_reward", {
                reward_id: parseInt(rewardId, 10),
                code: code,
                product_id: productId ? parseInt(productId, 10) : null,
            });

            if (result.error) {
                this.state.coupon_error = result.error;
                if (result.website_sale_order) {
                    this.state.website_sale_order = result.website_sale_order;
                }
            } else if (result.success) {
                this.state.coupon_success = result.message || "Reward claimed successfully!";
                if (result.website_sale_order) {
                    this.state.website_sale_order = result.website_sale_order;
                }
                await this.loadMiniCart();
                wSaleUtils.updateCartNavBar({ cart_quantity: this.props.card_qty });
                if (!result.website_sale_order.claimable_rewards ||
                    result.website_sale_order.claimable_rewards.length === 0) {
                    setTimeout(() => {
                        this.state.coupon_success = null;
                    }, 3000);
                }
            }
        } catch (error) {
            console.error("Error claiming reward:", error);
            this.state.coupon_error = error.message || "Failed to claim reward";
        } finally {
            this.state.isProcessing = false;
        }
    }
}

export default {
    MiniCartLine,
    MiniCart,
};
