import { patch } from "@web/core/utils/patch";
import { ProductWishlist } from '@website_sale_wishlist/interactions/product_wishlist';
import wishlistUtils from '@website_sale_wishlist/js/website_sale_wishlist_utils';
import { rpc } from "@web/core/network/rpc";

patch(ProductWishlist.prototype, {
    async _removeProduct(button, emptyRedirectUrl) {
        const article = button.closest('article');
        const wish = article.dataset.wishId;
        const productId = parseInt(article.dataset.productId);

        await this.waitFor(rpc(`/shop/wishlist/remove/${wish}`));
        article.style.display = 'none';

        wishlistUtils.removeWishlistProduct(productId);
        wishlistUtils.updateWishlistView();

        let totalWishlistProductIDs = wishlistUtils.getWishlistProductIds();
        await rpc('/shop/wishlist/all_products', {}).then(function (data) {
            totalWishlistProductIDs = JSON.parse(data);
        });

        this.wishlistProductIDs = totalWishlistProductIDs.filter((p) => p !== productId);
        sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(this.wishlistProductIDs));
        if (!wishlistUtils.getWishlistProductIds().length && emptyRedirectUrl) {
            redirect(emptyRedirectUrl);
        }
        wishlistUtils.updateWishlistNavBar();
    },
});