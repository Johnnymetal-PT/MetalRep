import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class LoadMore extends Interaction {
    static selector = "#products_grid";
    dynamicContent = {
        _window: { "t-on-scroll": this.startLoadMore },
        ".load_more_button": { "t-on-click": this.startLoadMoreNextClick },
        ".load_more_button_top": { "t-on-click": this.startLoadMorePrevClick },
    };

    setup() {
        super.setup();
        this.next_call = true;
        this.prev_call = true;
        this.$pagerEl = null;
    }

    start() {
        super.start();
        this.$pagerEl = $(".load_more_next_page");
        const initialPage = parseInt(this.$pagerEl.attr('current-page-number'));
        const totalPage = parseInt(this.$pagerEl.attr('total-page'));
        this.updateLoadMoreButtons(initialPage, totalPage);
    }

    getPagerValues() {
        const el = this.$pagerEl;
        return {
            page_url: el.attr('next-page-url'),
            prev_page_url: el.attr('prev-page-url'),
            first_page_url: el.attr('first-page-url'),
            last_page_url: el.attr('last-page-url'),
            current_url: el.attr('current-page-url'),
            total_page: parseInt(el.attr('total-page')),
        };
    }

    toggleNextLoading(show) {
        $(".cus_theme_loader_layout_next").toggleClass("d-none", !show);
        $('.load_more_button').toggleClass("d-none", show);
    }

    togglePrevLoading(show) {
        $(".cus_theme_loader_layout_prev").toggleClass("d-none", !show);
        $('.load_more_button_top').toggleClass("d-none", show);
    }

    updatePagerAttrs(attrs) {
        Object.entries(attrs).forEach(([k, v]) => this.$pagerEl.attr(k, v));
    }

    appendProducts($data, method = "append") {
        const products = $data.find("#products_grid .oe_product");
        if (products.length) {
            $("#products_grid #o_wsale_products_grid")[method](products);
        }
    }

    processResponse($data, val, isNext = true) {
        this.updatePaginationFromResponse($data);

        const pageData = $data.find('.load_more_next_page');

        const current_page_num = parseInt(pageData.attr('current-page-number'));
        const current_page = pageData.attr('current-page-url');

        const attrs = {
            'current-page-number': current_page_num,
            'current-page-url': current_page,
        };

        if (isNext) {
            attrs['next-page-url'] = pageData.attr('next-page-url');
            attrs['next-page-num'] = pageData.attr('next-page-num');
        } else {
            attrs['prev-page-url'] = pageData.attr('prev-page-url');
            attrs['prev-page-num'] = pageData.attr('prev-page-num');
        }

        this.updatePagerAttrs(attrs);
        this.updateLoadMoreButtons(current_page_num, val.total_page);

        window.history.replaceState(null, null, current_page);

        if ($('#id_lazyload').length) {
            $("img.lazyload").lazyload();
        }

        return current_page_num;
    }

    LoadMoreNext() {
        const val = this.getPagerValues();
        if (!this.next_call || val.current_url === val.last_page_url) return;
        this.next_call = false;
        this.toggleNextLoading(true);
        $.ajax({
            url: val.page_url,
            type: 'GET',
            success: (data) => {
                this.toggleNextLoading(false);
                const $data = $(data);
                const currentPage = this.processResponse($data, val, true);
                this.appendProducts($data, "append");
                // Reinitialize all public interactions for the updated product grid
                const publicInteractions = this.services['public.interactions'];
                const wrap = document.querySelector("#wrapwrap");
                publicInteractions.stopInteractions(wrap);
                publicInteractions.startInteractions(wrap);
                if (currentPage < val.total_page) {
                    this.next_call = true;
                }
            },
            error: () => this.next_call = true
        });
    }

    LoadMorePrev() {
        const val = this.getPagerValues();
        if (!this.prev_call || val.current_url === val.first_page_url) return;
        this.prev_call = false;
        this.togglePrevLoading(true);
        $.ajax({
            url: val.prev_page_url,
            type: 'GET',
            success: (data) => {
                this.togglePrevLoading(false);
                const $data = $(data);
                const currentPage = this.processResponse($data, val, false);
                this.appendProducts($data, "prepend");
                // Reinitialize all public interactions for the updated product grid
                const publicInteractions = this.services['public.interactions'];
                const wrap = document.querySelector("#wrapwrap");
                publicInteractions.stopInteractions(wrap);
                publicInteractions.startInteractions(wrap);
                if (currentPage > 1) {
                    this.prev_call = true;
                }
            },
            error: () => this.prev_call = true
        });
    }

    startLoadMore(scroll) {
        if (this.$pagerEl.attr('button-scroll') !== 'automatic') return;
        const $grid = $("#products_grid #o_wsale_products_grid");
        const last = $grid.find(".oe_product:last");
        const first = $grid.find(".oe_product:first");
        if (last.length && scroll.currentTarget.pageYOffset > last.offset().top - 150) {
            this.LoadMoreNext();
        }
        if (first.length && scroll.currentTarget.pageYOffset <= 0) {
            this.LoadMorePrev();
        }
    }

    startLoadMoreNextClick() {
        if (!$('body').hasClass('editor_enable')) {
            this.LoadMoreNext();
        }
    }

    startLoadMorePrevClick() {
        if (!$('body').hasClass('editor_enable')) {
            this.LoadMorePrev();
        }
    }

    updatePaginationFromResponse($data) {
        const active_page = parseInt($data.find(".load_more_next_page").attr('page-number'));
        const $pagerItems = $("ul.pagination li").not(":first,:last");
        $("ul.pagination li").removeClass("active");
        let found = false;
        $pagerItems.each(function () {
            if (parseInt($(this).text()) === active_page) {
                $(this).addClass("active");
                found = true;
            }
        });
        if (!found) {
            const half = Math.floor($pagerItems.length / 2);
            $pagerItems.each(function (index) {
                const newNum = active_page - half + index;
                if (newNum > 0) {
                    $(this).find("a").attr("href", "/shop/page/" + newNum).text(newNum);
                    if (newNum === active_page) {
                        $(this).addClass("active");
                    }
                }
            });
        }
    }
    updateLoadMoreButtons(currentPage, totalPage) {
        $('.load_more_button_top').toggleClass('d-none', currentPage <= 1);
        $('.load_more_button').toggleClass('d-none', currentPage >= totalPage);
    }
}

registry.category("public.interactions").add("emipro_theme_base.load_more", LoadMore);
registry.category("public.interactions.edit").add("emipro_theme_base.load_more", { Interaction: LoadMore });
