
import { rpc } from "@web/core/network/rpc";
import { registry } from '@web/core/registry';
import { _t } from "@web/core/l10n/translation";
import { Interaction } from '@web/public/interaction';
import { ProductShareDialog } from "theme_alan.ProductShareDialog";
import { ProductQueriesDialog } from "theme_alan.ProductQueriesDialog";
import { ProductAdvanceInfoDialog } from "theme_alan.ProductAdvanceInfoDialog";

// ─── Product Detail Info ─────────────────────────────────────────────────
export class ProductDetailInfo extends Interaction {
    static selector = '.as-product-details-page';
    dynamicContent = {
        _document: {
            "t-on-scroll": this.onScrollStickyCart,
        },
        ".as_sticky_action": {
            "t-on-click": this.onClickStickyBtn,
        },
    };

    setup() {
        new Swiper(".as-al-ass-swiper", {
            slidesPerView: 1.75,
            spaceBetween: 10,
            navigation: {
                nextEl: ".swiper-button-ass-next",
                prevEl: ".swiper-button-ass-prev",
            },
            breakpoints: {
                640: {
                    slidesPerView: 2,
                    spaceBetween: 24,
                },
                768: {
                    slidesPerView: 3,
                    spaceBetween: 24,
                },
                1024: {
                    slidesPerView: 4,
                    spaceBetween: 24,
                },

            },
        });

        new Swiper(".as-al-alt-swiper", {
            slidesPerView: 1.75,
            spaceBetween: 10,
            navigation: {
                nextEl: ".swiper-button-alt-next",
                prevEl: ".swiper-button-alt-prev",
            },
            breakpoints: {
                640: {
                    slidesPerView: 2,
                    spaceBetween: 24,
                },
                768: {
                    slidesPerView: 3,
                    spaceBetween: 24,
                },
                1024: {
                    slidesPerView: 4,
                    spaceBetween: 24,
                },
            },
        });
    }

    async onScrollStickyCart() {
        const addToCartBtns = this.el.querySelectorAll('#add_to_cart_wrap');
        const stickyCart = this.el.querySelector('.as-product-sticky-cart');
        if (document.querySelector('.as-sticky-cart-active') && addToCartBtns.length > 0) {
            const firstProduct = addToCartBtns[0];
            const top = firstProduct.getBoundingClientRect().top + window.scrollY;
            const bottom = top + firstProduct.offsetHeight;

            const bottom_screen = window.scrollY + window.innerHeight;
            const top_screen = window.scrollY;

            if ((bottom_screen > top) && (top_screen < bottom)) {
                if (stickyCart && stickyCart.classList.contains("as-stikcy-show")) {
                    stickyCart.classList.remove("as-stikcy-show");
                }
            } else {
                if (top) {
                    if (stickyCart && !stickyCart.classList.contains("as-stikcy-show")) {
                        stickyCart.classList.add("as-stikcy-show");
                    }
                }
            }
        }

        const offset = 450;
        const backToTop = document.querySelector('.as-scroll-to-top');
        if (backToTop) {
            if (window.scrollY > offset) {
                backToTop.classList.add('as-bt-visible');
            } else {
                backToTop.classList.remove('as-bt-visible');
            }
        }
    }

    async onClickStickyBtn(ev) {
        const targetId = ev.currentTarget.dataset.target_id;
        const targetElement = this.el.querySelector(targetId);

        if (targetElement) {
            targetElement.click();
        }
    }
}
registry.category('public.interactions').add('theme_alan.product_detail_info', ProductDetailInfo);

//─── Product Pager ────────────────────────────────────────────────────
export class ProductPager extends Interaction {
    static selector = ".as-pager-prod";
    dynamicContent = {
        _root: {
            "t-on-mouseenter": this.onMouseEnter,
            "t-on-mouseleave": this.onMouseLeave,
        },
    };
    onMouseEnter(ev) {
        const type = ev.currentTarget.dataset.type;
        if (type == "pre") {
            const preProdInfo = document.querySelector(".as-pre-prod-info");
            if (preProdInfo) preProdInfo.classList.remove("d-none");
        } else {
            const nextProdInfo = document.querySelector(".as-next-prod-info");
            if (nextProdInfo) nextProdInfo.classList.remove("d-none");
        }
    };

    onMouseLeave(ev) {
        const type = ev.currentTarget.dataset.type;
        if (type == "pre") {
            const preProdInfo = document.querySelector(".as-pre-prod-info");
            if (preProdInfo) preProdInfo.classList.add("d-none");
        } else {
            const nextProdInfo = document.querySelector(".as-next-prod-info");
            if (nextProdInfo) nextProdInfo.classList.add("d-none");
        }
    }
}
registry.category('public.interactions').add('theme_alan.product_pager', ProductPager);

//─── Product Queries ────────────────────────────────────────────────────
export class ProductQueries extends Interaction {
    static selector = '.product_queries';
    dynamicContent = {
        "#any_queries": { "t-on-click": this.onClickQueries },
    };
    async onClickQueries() {
        const queryMsg = document.querySelector('.query-msg');
        if (queryMsg) {
            queryMsg.classList.add("d-none");
        }
        const inputElement = this.el.querySelector("#product");
        const inputproduct = inputElement ? inputElement.value : null;
        try {
            const response = await rpc("/product_queries", {
                product_id: inputproduct,
                _t: Date.now()
            });
            if (response.allow === false) {
                const queryMsg = document.querySelector('.query-msg');
                if (queryMsg) {
                    queryMsg.classList.remove("d-none");
                }
            } else {
                this.services.dialog.add(ProductQueriesDialog, {
                    product_id: inputproduct,
                    user_email: response.user_email,
                    user_phone: response.user_phone || '',
                    user_id: response.user_id,
                    user_name: response.user_name,
                    is_public_user: response.is_public_user,
                    dialog_header: response.dialog_header,
                    dialog_header_desc: response.dialog_header_desc,
                    acknowledgement_message: response.acknowledgement_message,
                });
            }
        } catch (error) {
            console.error("Error fetching product queries:", error);
        }
    }
}

registry.category('public.interactions').add('theme_alan.product_queries', ProductQueries);

//─── Product Share ──────────────────────────────────────────────────────────
export class ProductShare extends Interaction {
    static selector = '.as_product_share';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickShare,
        },
    };
    async onClickShare() {
        this.services.dialog.add(ProductShareDialog, { product_link: window.location.href });
    }
}
registry.category('public.interactions').add('theme_alan.product_share', ProductShare);

//─── Product Advance Info ────────────────────────────────────────────────────
export class ProductAdvanceInfo extends Interaction {
    static selector = '.as_product_advance_att_info';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickAdvanceInfo,
        },
    };
    async onClickAdvanceInfo() {
        const dataInfo = this.el.getAttribute('data-info_id');
        this.services.dialog.add(ProductAdvanceInfoDialog, { infoId: dataInfo });
    }
}
registry.category('public.interactions').add('theme_alan.product_advance_info', ProductAdvanceInfo);

//─── Product Rating View ────────────────────────────────────────────────────
export class ParoductRatingView extends Interaction {
    static selector = '.o_website_rating_static';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickReviewsTab,
        },
    };

    async onClickReviewsTab() {
        const reviewsTabButton = document.querySelector('#nav-reviews-tab');
        if (reviewsTabButton) {
            reviewsTabButton.click();
            $('html, body').animate({
                scrollTop: $(".product-details-tabs").offset().top - 100
            }, 800);
        }
    }
}
registry.category('public.interactions').add('theme_alan.product_rating', ParoductRatingView);

// ─── Scroll to Top ──────────────────────────────────────────────────────────
export class AlanScrolltoTop extends Interaction {
    static selector = '#wrapwrap';
    dynamicContent = {
        ".as_sticky_scroll_top": { "t-on-click": this.onClickStickyBtn },
    };
    async onClickStickyBtn() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}
registry.category('public.interactions').add('theme_alan.alan_scroll_to_top', AlanScrolltoTop);
