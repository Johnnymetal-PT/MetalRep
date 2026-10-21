/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Carrossel de uma colecao da pagina Fabrics.
 * O QWeb renderiza os produtos; o widget Odoo gere setas e See all.
 */
publicWidget.registry.HmdFabricCarousel = publicWidget.Widget.extend({
    selector: ".hmd-fabric-carousel",
    events: {
        "click .hmd-fabric-carousel__arrow--prev": "_onPrevious",
        "click .hmd-fabric-carousel__arrow--next": "_onNext",
        "click .hmd-fabric-carousel__all": "_onToggleAll",
        // Materials (#8367, video da Monica de 20/10/2026): por instinto
        // carrega-se no nome da familia ou numa amostra para ver mais. Nos
        // Materials, o nome abre/fecha como o "View all" e uma amostra abre.
        // Nos Fabrics nao: la a amostra leva a pagina da serie.
        // O seletor de um evento procura-se DENTRO do carrossel (this.el), por
        // isso nao pode incluir a classe do proprio carrossel: confirma-se se
        // e dos Materials dentro da funcao.
        "click .hmd-fabric-carousel__head h2": "_onMaterialTitle",
        "click .hmd-fabric-card": "_onMaterialCard",
    },

    start() {
        this.track = this.el.querySelector(".hmd-fabric-carousel__track");
        this.cards = Array.from(this.el.querySelectorAll(".hmd-fabric-card"));
        this.previous = this.el.querySelector(".hmd-fabric-carousel__arrow--prev");
        this.next = this.el.querySelector(".hmd-fabric-carousel__arrow--next");
        this.showAll = this.el.querySelector(".hmd-fabric-carousel__all");
        this.showAllLabel = this.el.querySelector(".hmd-fabric-carousel__all-label");
        this.index = 0;
        this._onResize = this._update.bind(this);
        window.addEventListener("resize", this._onResize, { passive: true });
        this._update();
        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener("resize", this._onResize);
        return this._super(...arguments);
    },

    _visibleCount() {
        return window.matchMedia("(max-width: 991.98px)").matches ? 2 : 4;
    },

    _update() {
        const visible = this._visibleCount();
        const maximum = Math.max(0, this.cards.length - visible);
        this.index = Math.max(0, Math.min(this.index, maximum));
        const firstCard = this.cards[0];
        const gap = parseFloat(getComputedStyle(this.track).columnGap) || 0;
        const step = firstCard ? firstCard.getBoundingClientRect().width + gap : 0;
        this.track.style.transform = `translateX(${-this.index * step}px)`;
        this.previous.disabled = this.index === 0;
        this.next.disabled = this.index >= maximum;
    },

    _onPrevious(ev) {
        ev.preventDefault();
        this.index = Math.max(0, this.index - this._visibleCount());
        this._update();
    },

    _onNext(ev) {
        ev.preventDefault();
        const maximum = Math.max(0, this.cards.length - this._visibleCount());
        this.index = Math.min(maximum, this.index + this._visibleCount());
        this._update();
    },

    _onMaterialTitle(ev) {
        if (this.el.classList.contains("hmd-material-carousel")) {
            this._onToggleAll(ev);
        }
    },

    _onMaterialCard(ev) {
        if (!this.el.classList.contains("hmd-material-carousel")
                || ev.target.closest("a") || this.el.classList.contains("is-expanded")) {
            return;
        }
        this._onToggleAll(ev);
    },

    _onToggleAll(ev) {
        ev.preventDefault();
        // O texto de "ver tudo" vem da vista (hoje "View all fabrics" em Fabrics,
        // "See all" nos Materials); guarda-se o original para o repor.
        this.showAllText = this.showAllText || this.showAllLabel.textContent;
        const expanded = this.el.classList.toggle("is-expanded");
        this.showAllLabel.textContent = expanded ? "Show less" : this.showAllText;
        this.showAll.setAttribute("aria-expanded", String(expanded));
        if (!expanded) {
            this.index = 0;
            this._update();
        }
    },
});
