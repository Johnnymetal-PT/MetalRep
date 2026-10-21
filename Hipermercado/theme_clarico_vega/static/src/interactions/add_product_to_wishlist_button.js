import { patch } from "@web/core/utils/patch";
import { AddProductToWishlistButton } from '@website_sale_wishlist/interactions/add_product_to_wishlist_button';
import { rpc } from "@web/core/network/rpc";

patch(AddProductToWishlistButton.prototype, {
    async addProduct(ev) {
        $('#wishlist_toast').toast("show");
        $('#wishlist_toast .add_to_collection').attr('data-product-id',$(ev.currentTarget).attr('data-product-product-id'));
        await this.waitFor(super.addProduct(...arguments));
    },
});