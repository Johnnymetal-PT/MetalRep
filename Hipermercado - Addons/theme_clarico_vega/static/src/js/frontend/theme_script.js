/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import OwlMixin from "@theme_clarico_vega/js/frontend/mixins";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { DynamicSnippet } from '@website/snippets/s_dynamic_snippet/dynamic_snippet';
import { utils as uiUtils } from "@web/core/ui/ui_service";
function ensureWebsiteSaleContainer() {
    if (!document.querySelector(".oe_website_sale")) {
        const container = document.createElement("div");
        container.className = "oe_website_sale";
        container.style.display = "none";
        document.body.appendChild(container);
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureWebsiteSaleContainer);
} else {
    ensureWebsiteSaleContainer();
}

/* Sticky Product Details */
export class StickyDetails extends Interaction {
    static selector = "#product_detail_main";
    dynamicContent = {
        _window: {
            "t-on-scroll": this.stickDetails,
        },
    }
    getDeviceType() {
        const width = $(window).width();
        return width >= 992 ? 'desktop' : 'mobile';
    }
    stickDetails(scroll) {
        const deviceType = this.getDeviceType();

        const $sticky = $('.product_details_sticky');
        const $price = $('div#product_details .product_price');
        const $footer = $('#footer');
        const $main = $('main');
        const $header = $('header');

        if (!$sticky.length) return;

        const footerOffset = $main.height() - $footer.height();
        const cookieHeight = $('.s_popup_size_full .modal-content').height() || 0;
        const productDetails = $('#product_details').height() - $('.main_payment_section').height();
        $('header#top').css('z-index', '1030');
        if (deviceType === 'desktop') {
            if (scroll.currentTarget.pageYOffset > productDetails && scroll.currentTarget.pageYOffset < footerOffset - 500) {
                $sticky.css('bottom', cookieHeight + 'px').fadeIn();
                const priceHtml = $(".js_product.js_main_product").hasClass("css_not_available") ? '' : $price.html();
                $('div#wrapwrap .prod_price').html(priceHtml);
            } else {
                $sticky.fadeOut();
            }
        }
        if (deviceType === 'mobile') {
            const productDetailsOffset = $('#add_to_cart_wrap').offset().top;
            if (scroll.currentTarget.pageYOffset > productDetailsOffset && scroll.currentTarget.pageYOffset < footerOffset + 500) {
                $sticky.css({'top': $header.height() + 'px', 'bottom': 'auto'}).fadeIn();
            } else {
                $sticky.fadeOut();
            }
        }
    }
}
registry.category("public.interactions").add("theme_clarico_vega.stickyDetails", StickyDetails);
registry.category("public.interactions.edit").add("theme_clarico_vega.stickyDetails", {Interaction: StickyDetails,});

/* Mobile Sidebar Menu */
publicWidget.registry.responsiveMobileHeader = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .header_sidebar': '_headerSidebar',
        'click .close_top_menu': '_closeLeftHeader',
    },
    init: function() {
        this._super(...arguments);
        this.header_height = 0;
        if ($('.o_main_navbar').length) {
            this.header_height = $('.o_main_navbar').height();
        }
    },
    _headerSidebar: function() {
        $("#top_menu_collapse").addClass("header_menu_slide").css('top', this.header_height).show('slow');
        $("#top_menu_collapse").animate({
            width: '100%'
        });
        $("#wrapwrap").addClass("wrapwrap_trans_header");
        $(".te_mega_menu_ept a.dropdown-toggle.o_mega_menu_toggle").attr('href', '#');
        $(".parent-category .mobile_cate_child").attr('href', '#');
    },
    _closeLeftHeader: function() {
        $("#top_menu_collapse").animate({
            width: '0'
        });
        $("#wrapwrap").removeClass("wrapwrap_trans_header");
    }
});

publicWidget.registry.attrSidebarcanvasAnimation = publicWidget.Widget.extend({
    selector: '.o_wsale_product_page',
    start: function() {
        /* Attribute popup/sidebar off-canvas animation */
        const offcanvasModelElement = $('.main_attribute_popup_data');
        offcanvasModelElement.on('show.bs.offcanvas', function () {
            $('header#top').css("z-index", "0");
        });
        offcanvasModelElement.on('hide.bs.offcanvas', function () {
            $('header#top').removeAttr("z-index");
        });
        offcanvasModelElement.on('show.bs.modal', function () {
            $('header#top').css("z-index", "0");
        });
        offcanvasModelElement.on('hide.bs.modal', function () {
            $('header#top').removeAttr("z-index");
        });
    },
});

/* Header Mobile Search Icon Toggle */
publicWidget.registry.themeSearch = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .te_srch_icon': '_onSearchClickOpen',
        'click .te_srch_close': '_onSearchClickClose',
        'click .te_srch_icon_5': '_onSearch5ClickOpen',
        'click .te_srch_close_5': '_onSearch5ClickClose',
    },
    start: function(){
        /* Add code for mega menu style 9 mobile view */
        $("#custom_menu_ept li").each(function() {
            let has_ctg = $(this).find("ul.t_custom_subctg").length > 0;
            if (has_ctg) {
                $(this).append("<a class='ctg_arrow float-end fa fa-angle-right py-2' />")
                $(this).click(function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    if($(ev.target).hasClass('categ_ept')){
                        globalThis.location.replace($(ev.target).attr('href'))
                        return
                    }
                    let self = $(this).find("ul.t_custom_subctg")[0];
                    if(!$(ev.target).find('ul').length && !$(ev.target).hasClass('ctg_arrow')) {
                        if($(ev.target).find('a').attr('href')){
                            globalThis.location.replace($(ev.target).find('a').attr('href'))
                        }
                        return
                    }
                    $(self).stop().animate({
                        width: "100%"
                    });
                    $(self).css({
                        "display": "block",
                        "transition": "0.3s easeout",
                        "z-index": 99
                    })
                    $(self).parent(".t_custom_subctg").css("overflow-y", "hidden");
                    $(self).parent(".t_custom_subctg").scrollTop(0);
                    $(this).parents("#custom_menu_ept").scrollTop(0);
                    $(this).parents("#custom_menu_ept").css("overflow-y", "hidden");
                });
                $(this).find("ul.t_custom_subctg").children(".te_prent_ctg_heading").click(function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    $(this).parent("ul#custom_recursive_ept").stop().animate({
                        width: "0"
                    }, function() {
                        $(this).css("display", "none")
                        $(this).parent().parent(".t_custom_subctg").css("overflow-y", "auto");
                    });
                });
            }
        });
        $("#custom_menu_ept > li > ul.t_custom_subctg > .te_prent_ctg_heading").click(function() {
            $(this).parents("#custom_menu_ept").css("overflow-y", "auto");
        });
    },
    _onSearchClickOpen: function(ev) {
        const searchbarInput = $('.o_searchbar_form input[name="search"]');
        const isRightHeaderStyle = $('.te_header_style_right').length;
        const isPopupSearchForm = $(".te_searchform__popup").length;
        setTimeout(() => searchbarInput.focus(), 500);

        if (isRightHeaderStyle) {
            $(".te_search_popover").addClass("visible");
            $(ev.currentTarget).hide();
            $(".te_srch_close").css('display', 'block');
        } else if (isPopupSearchForm) {
            $(".te_searchform__popup").addClass("open");
            $(".te_srch_close").show();
        }
    },
    _onSearchClickClose: function(ev) {
        const isRightHeaderStyle = $('.te_header_style_right').length;
        const isPopupSearchForm = $(".te_searchform__popup").length;

        if (isRightHeaderStyle) {
            $(".te_search_popover").removeClass("visible");
            $(ev.currentTarget).not('.te_srch_close_5').hide();
            $(".te_srch_icon").show();
        } else if (isPopupSearchForm) {
            $(".te_searchform__popup").removeClass("open");
            $(".te_srch_icon").show();
        }
    },
    _onSearch5ClickOpen: function(ev) {
        const searchbarInput = $('.o_searchbar_form input[name="search"]');
        const isRightHeaderStyle = $('.te_header_style_right').length;
        const isPopupSearchForm = $(".te_searchform__popup").length;
        setTimeout(() => searchbarInput.focus(), 500);

        if (isRightHeaderStyle) {
            $(".te_search_popover").addClass("visible");
            $('.te_header_style_right').slideDown(250);
            $(".te_srch_close").css('display', 'block');
        } else if (isPopupSearchForm) {
            $(".te_searchform__popup").addClass("open");
            $(".te_srch_close").show();
        }
    },
    _onSearch5ClickClose: function(ev) {
        const isRightHeaderStyle = $('.te_header_style_right').length;
        const isPopupSearchForm = $(".te_searchform__popup").length;

        if (isRightHeaderStyle) {
            $(".te_search_popover").removeClass("visible");
            $('.te_header_style_right').slideUp(250);
            $(".te_srch_icon_5").show();
        } else if (isPopupSearchForm) {
            $(".te_searchform__popup").removeClass("open");
            $(".te_srch_icon_5").show();
        }
    },
});

/* Lazyload Image */
publicWidget.registry.Lazyload = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    start() {
        if ($('#id_lazyload').length) {
            $("img.lazyload").lazyload();
        }
        this._super(...arguments);
    },
});

/* Brand Listing Page */
publicWidget.registry.brandPage = publicWidget.Widget.extend({
    selector: ".featured-all-brands",

    read_events: {
        'click .has-brands': '_onClickAlpha',
        'click #all-brands': '_showAllBrands',
        'keyup #search_box': '_onKeyupInput'
    },

    _onClickAlpha: function(ev) {
        this.showAllBrands();
        let $this = $(ev.currentTarget);
        let value = $('#search_box').val();
        $this.children().toggleClass('selected');
        let selected_letter_arr = []
        $('.selected').each(function(i) {
            selected_letter_arr.push($.trim($(this).text()))
        });
        if ($.inArray("0-9", selected_letter_arr) != -1){
            selected_letter_arr.push('1', '2', '3', '4', '5', '6', '7', '8', '9');
        }
        $('.brand-alpha-main').each(function(e) {
            let first_letter = $(this).find('.brand-name').attr('brand_name').substring(0, 1).toLowerCase();
            if ($.inArray(first_letter, selected_letter_arr) == -1 && selected_letter_arr.length != 0) {
                $(this).addClass('d-none');
            }
        });
        if (value) {
            this.removeBlocks(value);
        }
    },

    _showAllBrands: function(ev) {
        $('.selected').removeClass('selected');
        this.showAllBrands();
        let value = $('#search_box').val();
        this.removeBlocks(value);
    },

    _onKeyupInput: function(ev) {
        $('.selected').removeClass('selected');
        let value = $(ev.currentTarget).val();
        this.showAllBrands();
        this.enableBrandBox();
        if (value.length >= 1) {
            this.removeBlocks(value);
            this.disableBox(value);
        }
    },

    showAllBrands: function() {
        $('.brand-alpha-main').each(function(e) {
            $(this).find('.brand-item.d-none').each(function(e) {
                $(this).removeClass('d-none');
            });
            $(this).removeClass('d-none');
        });
    },

    removeBlocks: function(value) {
        $('.brand-alpha-main').each(function(i) {
            let flag = 0
            $(this).find('.brand-item').each(function(i) {
                let brand = $(this).find('.brand-name').attr('brand_name')
                if (!brand.toLowerCase().includes(value.toLowerCase())) {
                    $(this).addClass('d-none');
                }
                if (!$(this).hasClass('d-none')) {
                    flag = 1;
                }
            });
            if (flag == 0) {
                $(this).addClass('d-none');
            }
        });
    },

    enableBrandBox: function() {
        $('.has-brands.active').each(function(i) {
            if ($(this).hasClass('disabled')) {
                $(this).removeClass('disabled');
            }
        });
    },

    disableBox: function(value) {
        let enabled_array = new Array();
        $('.brand-alpha-main').each(function(i) {
            let flag = 0;
            $(this).find('.brand-item').each(function(i) {
                if (flag == 0) {
                    let brand = $(this).find('.brand-name').attr('brand_name');
                    if (brand.toLowerCase().includes(value.toLowerCase())) {
                        enabled_array.push($(this).find('.brand-name').attr('brand_name').substring(0, 1).toLowerCase());
                        flag = 1;
                    }
                } else {
                    return false;
                }
            });
        });
        if (enabled_array.length == 0) {
            $('.has-brands.active').each(function(i) {
                $(this).addClass('disabled');
            });
        } else {
            enabled_array.forEach(function(item) {
                $('.has-brands.active').each(function(i) {
                    if ($.inArray($.trim($(this).children('.brand-alpha').text()), enabled_array) == -1) {
                        $(this).addClass('disabled');
                    }
                });
            });
        }
    }
});

 /* Attribute value tooltip */
$(function() {
    $('[data-bs-toggle="tooltip"]').tooltip({animation: true,delay: {show: 300,hide: 100} })
    /* Brands owl Slider for Mega Menu Style 1 */
    $('.te_menu_brand_img').each(function(index){
        let responsive = { 0: {items: 2}, 576: {items: 3}, 991: {items: 4}, 1200: {items: 4} };
        OwlMixin.initOwlCarousel('.te_menu_brand_img', 10, responsive, true, 1, false, false, true, true, false, false, true, false);
    });
});

/* See All */
publicWidget.registry.seeAll = publicWidget.Widget.extend({
    selector: ".js_attributes",

    read_events: {
        'click .theme_view_more_btn': '_seeAll',
        'click .te_color-name': '_filter_color_attribute_click',
    },

    _seeAll: function(ev) {
        ev.preventDefault();
        let $this = $(ev.currentTarget);
        let attr_type = $this.attr("attr_type");
        let attr_id = $this.attr("attr_id");
        let attrib_set = $this.attr("attrib_set");
        let counts = $('#counts').val();

        if(attr_type == 'multi_radio'){
            $("#o_products_attributes_"+attr_id+" div.form-check").each(function(index){
                $(this).removeClass('d-none');
            });
        }
        else{
            $("#o_products_attributes_"+attr_id+" label").each(function(index){
                $(this).removeClass('d-none');
            });
        }

        $("div#o_wsale_view_more_"+attr_id+"_header").addClass('d-none');
    },
    /*======= color attribute click=========== */
    _filter_color_attribute_click: function(ev){
        $(ev.target).find('.css_attribute_color').trigger('click');
        if(ev.target.classList.contains('te_color-name')){
            $(ev.target).prev().trigger('click');
        }
    },
});

publicWidget.registry.productTabs = publicWidget.Widget.extend({
    selector: '.product_tabs_ept',
    start() {
        // Optimised code due to old js code.
        const desktopTabs = document.querySelectorAll('#nav-tab button');
        const mobileTabs = document.querySelectorAll('#prd-tab-content .tab-pane');

        desktopTabs.forEach((btn, i) => {
            const desktopTabId = btn.id;
            const mobileTabId = mobileTabs[i]?.id;

            if (!desktopTabId || !mobileTabId) return;

            const desktopSpans = document.querySelectorAll(`#${desktopTabId} a > span`);
            const mobileSpans = document.querySelectorAll(`#${mobileTabId} a > span`);

            if (!desktopSpans.length || !mobileSpans.length) return;

            if (desktopSpans[0].classList.contains('fa')) {
                // Case: FontAwesome icon + text
                const iconClass = desktopSpans[0].className;
                const textVal = desktopSpans[1]?.innerText?.trim();

                if (mobileSpans[0]) mobileSpans[0].className = iconClass;
                if (mobileSpans[1] && textVal) mobileSpans[1].innerText = textVal;
            } else {
                // Case: nested span for icon
                const nestedIcon = document.querySelector(`#${desktopTabId} a > span span`)?.className;
                if (nestedIcon && mobileSpans[0]) {
                    mobileSpans[0].className = nestedIcon;
                }
            }
        });
    }
});

publicWidget.registry.shopQty = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    read_events: {
        'change #input_qty_list': '_onChangeQty',
    },

    _onChangeQty: function(ev) {
        ev.preventDefault();
        let $this = $(ev.currentTarget);
        let minQty = Number.parseInt($this.attr("data-min"), 10);
        let qtyValue = Number.parseInt($this.val(), 10);
        if (qtyValue < minQty) {
            $this.val(minQty);
        }
    },
});

patch(DynamicSnippet.prototype, {
    renderContent() {
        super.renderContent(...arguments);
        $("img.lazyload").lazyload();
        /*$('.s_product_brand_style_3 .dynamic-owl-carousel').each(function(index){
            let responsive = { 0: {items: 2}, 576: {items: 3}, 991: {items: 1}, 1200: {items: 1} };
            OwlMixin.initOwlCarousel('.s_product_brand_style_3 .dynamic-owl-carousel', 15, responsive, true, 1, false, true, false, false, false, false, true, false);
        });
        const $templateArea = $(this.el).find('.dynamic_snippet_template');
        if ($templateArea.find('img').toArray().some(img => img.classList.contains('lazyload'))) {
            $("img.lazyload").lazyload();
        }
        let interval = $(this.el).data("carouselInterval");
        let mobile_element_count = $(this.el).data("numberOfElementsSmallDevices");
        $('.dynamic-owl-carousel:not(.product_builder_banner .dynamic-owl-carousel, .dynamic_columns_snippet .dynamic-owl-carousel,.brand_builder_banner .dynamic-owl-carousel)').each(function(index) {
            let owl_rtl = false;
            if ($('#wrapwrap').hasClass('o_rtl')) {
                owl_rtl = true;
            }
            let $items = $(this);
            let item = $items.attr('data-slide-size') || 1;

            let slider_len = $items.find(".item").length === 0 ? $items.find(".card").length : $items.find(".item").length;
            let getItemLength = slider_len > 4;
            let dots = $items.parents('.dynamic_columns_snippet').length > 0;

            let autoplay = true;
            if(slider_len > item){
                getItemLength = true;
            }
            if($items.parents('.product_slider_style9')){
                autoplay = false;
            }
            $items.owlCarousel({
                loop: getItemLength,
                margin: 15,
                nav: true,
                navText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                autoplay: autoplay,
                autoplayTimeout: interval,
                autoplayHoverPause:true,
                items: item,
                dots: dots,
                rtl: owl_rtl,
                responsive: {
                    0: { items: mobile_element_count == undefined ? 1.5 : Number.parseInt(mobile_element_count) + 0.5},
                    576: { items: item > 1 ? 2.5 : Number.parseInt(item) + 0.5 },
                    991: { items: item > 1 ? item - 0.5 : Number.parseInt(item) + 0.5 },
                    1200: { items: Number.parseInt(item) + 0.5 },
                },
            });
            if( $items.find('.owl-nav').hasClass('disabled')){
                if(slider_len > item){
                    $items.find('.owl-nav').show();
                }
            }
            if($items.parents('.s_product_template_style_4')){
                $items.find('.owl-dots').show();
            }
        });
        $('.product_builder_banner .dynamic-owl-carousel, .dynamic_columns_snippet .dynamic-owl-carousel,.brand_builder_banner .dynamic-owl-carousel, .dynamic-owl-carousel').each(function(index) {
            let owl_rtl = false;
            if ($('#wrapwrap').hasClass('o_rtl')) {
                owl_rtl = true;
            }
            let $items = $(this);
            let item = $items.attr('data-slide-size') || 1;
            const slider_len = $items.find(".item").length === 0 ? $items.find(".card").length : $items.find(".item").length;
            const getItemLength = slider_len > 4;
            const dots = $items.parents('.dynamic_columns_snippet').length > 0;
            let autoplay = true;
            if(slider_len > item){
                let getItemLength = true;
            }
            if($items.parents('.product_slider_style9')){
                autoplay = false;
            }
            $items.owlCarousel({
                loop: getItemLength,
                margin: 15,
                nav: true,
                navText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                autoplay: autoplay,
                autoplayTimeout: interval,
                autoplayHoverPause:true,
                items: item,
                dots: dots,
                rtl: owl_rtl,
                responsive: {
                    0: { items: mobile_element_count == undefined ? 1 : Number.parseInt(mobile_element_count)},
                    576: { items: item > 1 ? 2 : item },
                    991: { items: item > 1 ? item - 1 : item },
                    1200: { items: item },
                },
            });
            if( $items.find('.owl-nav').hasClass('disabled')){
                if(slider_len > item){
                    $items.find('.owl-nav').show();
                }
            }
            if($items.parents('.s_product_template_style_4')){
                $items.find('.owl-dots').show();
            }
        });
        $("img.lazyload").lazyload();*/
    },
});


publicWidget.registry.ImageCompare = publicWidget.Widget.extend({
    selector: ".compare-img-wrapper",
    start: function () {
        const wrapper = this.el;
        let dragging = false;
        const setPosition = (clientX) => {
            const rect = wrapper.getBoundingClientRect();
            let percent = ((clientX - rect.left) / rect.width) * 100;
            percent = Math.max(0, Math.min(100, percent));
            wrapper.style.setProperty("--compare-handle-position", percent + "%");
        };
        const start = (e) => {
            if (document.body.classList.contains("editor_enable")) {
                return;
            }
            dragging = true;
            e.preventDefault();
        };
        const stop = () => dragging = false;
        const move = (e) => {
            if (!dragging) return;
            e.preventDefault();
            const clientX = e.touches
                ? e.touches[0].clientX
                : e.clientX;
            setPosition(clientX);
        };
        wrapper.addEventListener("mousedown", start);
        window.addEventListener("mouseup", stop);
        window.addEventListener("mousemove", move);
        wrapper.addEventListener("touchstart", start, {passive:false});
        window.addEventListener("touchend", stop);
        window.addEventListener("touchmove", move, {passive:false});
        return this._super.apply(this, arguments);
    },
});

export class HotspotPopover extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        ".hotspot_element.display_card": {
            "t-on-mouseenter": this._onMouseEnter,
            "t-on-mouseleave": this._onMouseLeave,
        },
    };
    setup() {
        this._hotspotTimeout = null;
    }
    _getProductId(target) {
        const raw = target.getAttribute("data-product-template-ids") || target.dataset.productTemplateIds || "";
        const parsed = parseInt(raw, 10);
        return Number.isNaN(parsed) ? null : parsed;
    }
    async _onMouseEnter(ev) {
        if (document.body.classList.contains("editor_enable")) {
            return;
        }
        const target = ev.currentTarget;
        clearTimeout(this._hotspotTimeout);
        $(".hotspot_element.display_card").not(target).popover("hide");
        this._hotspotTimeout = setTimeout(async () => {
            const productId = this._getProductId(target);
            if (!productId) return;
            try {
                const data = await $.get("/get-pop-up-product-details", { product: productId });
                const $target = $(target);
                $target.popover("dispose");
                $target.popover({
                    trigger: "manual",
                    animation: true,
                    html: true,
                    container: "body",
                    placement: "auto",
                    sanitize: false,
                    template:
                        '<div class="popover hotspot-popover" role="tooltip"><div class="tooltip-arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>',
                    content: data,
                });
                $target.popover("show");
                const popoverId = $target.attr("aria-describedby");
                const $popover = popoverId ? $(`#${popoverId}`) : $(".hotspot-popover");
                $popover.off("mouseleave.hotspot").on("mouseleave.hotspot", () => {
                    $target.popover("hide");
                });
                $popover.find(".hotspot_add_to_cart_btn").off("click.hotspot").on("click.hotspot", async (e) => {
                    e.preventDefault();
                    const $form = $(e.currentTarget).closest("form");
                    const productTemplateId = parseInt($form.find("input[name='product_template_id']").val() || 0, 10);
                    const productId = parseInt($form.find("input[name='product_id']").val() || 0, 10);
                    if (!productTemplateId) return;
                    try {
                        await this.services["cart"].add({
                            productTemplateId: productTemplateId,
                            productId: productId || undefined,
                            quantity: 1,
                        });
                    } catch (err) {
                        console.warn("Hotspot add to cart failed", err);
                    }
                });
            } catch (err) {
                console.warn("Hotspot popover load failed", err);
            }
        }, 300);
    }
    _onMouseLeave(ev) {
        if (document.body.classList.contains("editor_enable")) {
            return;
        }
        const target = ev.currentTarget;
        clearTimeout(this._hotspotTimeout);
        setTimeout(() => {
            if ($(".hotspot-popover:hover").length) {
                return;
            }
            $(target).popover("hide");
        }, 1000);
    }
}
registry.category("public.interactions").add("theme_clarico_vega.hotspotPopover", HotspotPopover);