/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.searchPlaceholderCarousel = publicWidget.Widget.extend({
    selector: ".te_search_placeholder_carousel",
    start() {
        this.trackEl = this.el.querySelector(".te_search_placeholder_track");
        this.items = Array.from(this.el.querySelectorAll(".te_search_placeholder_item"));
        this.interval = parseInt(this.el.dataset.interval, 10) || 2500;
        this.index = 0;
        this.itemHeight = 0;

        if (!this.trackEl || this.items.length <= 1) {
            return this._super(...arguments);
        }

        this._ensureHeight();
        this._timer = setInterval(() => this._next(), this.interval);
        return this._super(...arguments);
    },
    _ensureHeight() {
        if (this.itemHeight || !this.items.length) {
            return;
        }
        const height = this.items[0].getBoundingClientRect().height;
        if (height) {
            this.itemHeight = height;
            this.el.style.height = `${height}px`;
        }
    },
    _next() {
        this._ensureHeight();
        if (!this.itemHeight) {
            return;
        }
        this.index = (this.index + 1) % this.items.length;
        this.trackEl.style.transform = `translateY(-${this.itemHeight * this.index}px)`;
    },
    destroy() {
        if (this._timer) {
            clearInterval(this._timer);
        }
        this._super(...arguments);
    },
});
