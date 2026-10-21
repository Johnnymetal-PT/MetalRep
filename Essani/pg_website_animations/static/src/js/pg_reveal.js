/* PG Website Animações — entrada ao fazer scroll.
 *
 * Põe `pg-reveal` nos blocos que ainda não estão à vista e tira-lhes o efeito quando
 * entram no ecrã. Não escreve HTML nem altera vistas: se falhar, o site fica como estava.
 */
(function () {
    "use strict";

    // Blocos que entram a deslizar. Um snippet novo só anima se for acrescentado aqui.
    var ALVOS = [
        "#wrapwrap main .card",
        "#wrapwrap main .s_ecomm_categories_showcase_block",
        "#wrapwrap main .s_key_benefits [class*='col-']",
        "#wrapwrap main .s_features [class*='col-']",
        "#wrapwrap main .s_product_catalog_dish",
        "#wrapwrap main .oe_product",
        "#wrapwrap main .s_dynamic_snippet_title"
    ];
    // Já têm animação do Odoo, ou pediram para ficar quietos.
    var EXCLUIR = ".o_animate, .o_animate *, .pg-no-anim, .pg-no-anim *, .carousel *";
    var ATRASO_MAXIMO = 5;   // passos de 80 ms, para a cascata não demorar uma eternidade
    var PASSO_MS = 80;

    function semMovimento() {
        return window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function noEditor() {
        // No editor do website os blocos têm de estar sempre visíveis e editáveis.
        var b = document.body;
        return !b || b.classList.contains("editor_enable") ||
            document.documentElement.classList.contains("editor_enable") ||
            !!document.querySelector("#oe_main_menu_navbar, .o_edit_website_container");
    }

    function jaEstaAVista(el) {
        var r = el.getBoundingClientRect();
        var h = window.innerHeight || document.documentElement.clientHeight;
        return r.top < h && r.bottom > 0;
    }

    function iniciar() {
        if (semMovimento() || noEditor() || !("IntersectionObserver" in window)) {
            return;
        }
        var visto = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add("pg-in");
                    visto.unobserve(e.target);
                }
            });
        }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });

        var elementos = document.querySelectorAll(ALVOS.join(","));
        // Cascata dentro do mesmo pai: o 1.º entra já, o 2.º 80 ms depois, etc.
        var posicao = new Map();
        Array.prototype.forEach.call(elementos, function (el) {
            if (el.matches(EXCLUIR) || jaEstaAVista(el)) {
                return;
            }
            var pai = el.parentElement;
            var n = posicao.get(pai) || 0;
            posicao.set(pai, n + 1);
            el.style.setProperty("--pg-delay", (Math.min(n, ATRASO_MAXIMO) * PASSO_MS) + "ms");
            el.classList.add("pg-reveal");
            visto.observe(el);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
