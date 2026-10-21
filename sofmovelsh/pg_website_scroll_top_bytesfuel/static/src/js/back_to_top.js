/* PG Website Scroll Back To Top — botão "voltar ao topo".
 * Port V17 -> V19: convertido de jQuery para JS vanilla (o `$` global deixou
 * de ser garantido no frontend em v18/v19). Comportamento inalterado.
 */
(function () {
    "use strict";

    function init() {
        var btn = document.querySelector(".btn-top");
        var scroller = document.getElementById("wrapwrap");
        if (!btn || !scroller) {
            return;
        }
        btn.style.display = "none";

        scroller.addEventListener("scroll", function () {
            btn.style.display = scroller.scrollTop > 100 ? "block" : "none";
        });

        btn.addEventListener("click", function (ev) {
            ev.preventDefault();
            scroller.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
