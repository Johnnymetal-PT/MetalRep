/**
 * Lusosofá — movimento do website.
 *
 * Duas coisas, e nada mais: revelar secções à medida que entram no ecrã, e
 * condensar o cabeçalho depois do primeiro scroll.
 *
 * A regra que governa este ficheiro: **o conteúdo nunca depende deste script
 * para ser visível**. Os estados de partida da animação só se aplicam depois
 * de a classe `pg-movimento` estar no <html>, e é este ficheiro que a põe lá.
 * Se ele não carregar, falhar, ou for bloqueado, a página fica exactamente
 * como ficaria sem animação nenhuma — visível. O contrário, esconder por CSS
 * e contar com o JS para mostrar, transforma qualquer falha de script numa
 * página em branco.
 *
 * No editor do site não corre: quem está a montar a página tem de ver tudo o
 * que lá está, não o que uma animação decidiu esconder até ao scroll.
 */

(function () {
    "use strict";

    const raiz = document.documentElement;

    // O editor do Odoo marca o body; em modo de edição não há movimento.
    if (document.body.classList.contains("editor_enable")
        || document.querySelector("#oe_snippets")) {
        return;
    }

    // Quem pediu menos movimento ao sistema operativo não leva nenhum.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }

    // Sem IntersectionObserver não se esconde nada — degradação limpa.
    if (!("IntersectionObserver" in window)) {
        return;
    }

    raiz.classList.add("pg-movimento");

    // --- revelação ---------------------------------------------------------

    const ALVOS = [
        "#wrapwrap section",
        "#wrapwrap .oe_product",
        "#wrapwrap .pg-frame",
    ].join(", ");

    const observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (!entrada.isIntersecting) {
                return;
            }
            entrada.target.classList.add("pg-visivel");
            observador.unobserve(entrada.target);
        });
    }, {
        // Começa a revelar um pouco antes de a secção chegar ao fundo do ecrã:
        // ao chegar lá, já está feita, e não se vê a animação a acontecer.
        rootMargin: "0px 0px -12% 0px",
        threshold: 0.02,
    });

    function observar(raizDom) {
        // O que já está no ecrã não se esconde para depois reaparecer.
        //
        // Este ficheiro é servido no bundle `lazy`, ou seja, corre depois de a
        // página já ter pintado. Se escondêssemos tudo, o visitante via o
        // conteúdo, via-o desaparecer e via-o voltar — um pestanejo, logo na
        // primeira dobra, e pior quanto mais lenta for a ligação.
        //
        // Animar só o que ainda não foi visto é também o que faz sentido: uma
        // revelação serve para acompanhar a descida, não para repetir o que já
        // está diante dos olhos.
        const alturaEcra = window.innerHeight || document.documentElement.clientHeight;

        raizDom.querySelectorAll(ALVOS).forEach(function (el, i) {
            if (el.getBoundingClientRect().top < alturaEcra) {
                return;
            }
            // O escalonamento é por posição entre irmãos, não por ordem global:
            // uma grelha de produtos entra em cascata, uma secção sozinha não
            // espera por nada.
            const irmaos = el.parentElement
                ? Array.prototype.indexOf.call(el.parentElement.children, el)
                : i;
            el.style.setProperty("--pg-atraso", Math.min(irmaos, 6) * 70 + "ms");
            el.classList.add("pg-revela");
            observador.observe(el);
        });
    }

    observar(document);

    // Conteúdo que o Odoo injecta depois (filtros da loja, paginação) também
    // entra no mesmo tratamento.
    new MutationObserver(function (mutacoes) {
        mutacoes.forEach(function (m) {
            m.addedNodes.forEach(function (n) {
                if (n.nodeType === 1) {
                    observar(n);
                }
            });
        });
    }).observe(document.body, { childList: true, subtree: true });

    // --- carrossel ---------------------------------------------------------
    //
    // As setas são acrescentadas aqui, e não escritas na página, por uma razão:
    // **sem este ficheiro o carrossel continua a funcionar**. A faixa é uma
    // caixa com `overflow-x: auto` e pontos de encaixe, ou seja, arrasta-se com
    // o dedo, com o trackpad e com as teclas sem JavaScript nenhum. Escrever as
    // setas no HTML daria botões mortos quando isto falhasse.
    //
    // É a mesma regra que os filetes violaram até 2026-09-28: nada que se veja
    // pode depender de JavaScript para existir.

    function montarCarrossel(faixa) {
        if (faixa.dataset.pgMontado) { return; }
        faixa.dataset.pgMontado = "1";

        const raiz = faixa.closest(".pg-carrossel");
        if (!raiz) { return; }

        const espanhol = (document.documentElement.lang || "").slice(0, 2) === "es";
        const rotulos = espanhol ? ["Anterior", "Siguiente"] : ["Anterior", "Seguinte"];

        const setas = [-1, 1].map(function (sentido, i) {
            const b = document.createElement("button");
            b.type = "button";
            b.className = "pg-carrossel-seta pg-carrossel-seta--" + (sentido < 0 ? "tras" : "frente");
            b.setAttribute("aria-label", rotulos[i]);
            b.innerHTML = sentido < 0 ? "&#8592;" : "&#8594;";
            b.addEventListener("click", function () {
                const passo = faixa.firstElementChild
                    ? faixa.firstElementChild.getBoundingClientRect().width + 24
                    : faixa.clientWidth * 0.6;
                faixa.scrollBy({ left: passo * sentido, behavior: "smooth" });
            });
            raiz.appendChild(b);
            return b;
        });

        // Uma seta que não leva a lado nenhum é pior do que não existir.
        const acertarSetas = function () {
            const sobra = faixa.scrollWidth - faixa.clientWidth;
            raiz.classList.toggle("pg-carrossel--sem-sobra", sobra < 8);
            setas[0].disabled = faixa.scrollLeft < 8;
            setas[1].disabled = faixa.scrollLeft > sobra - 8;
        };
        faixa.addEventListener("scroll", function () {
            window.requestAnimationFrame(acertarSetas);
        }, { passive: true });
        window.addEventListener("resize", acertarSetas, { passive: true });
        acertarSetas();
    }

    const montarTodos = function () {
        document.querySelectorAll(".pg-carrossel-faixa").forEach(montarCarrossel);
    };
    montarTodos();
    new MutationObserver(montarTodos).observe(document.body, { childList: true, subtree: true });

    // --- cabeçalho ---------------------------------------------------------

    const cabecalho = document.querySelector("#wrapwrap header");
    if (cabecalho) {
        let ultimo = null;
        const aoRolar = function () {
            const condensado = window.scrollY > 40;
            if (condensado !== ultimo) {
                cabecalho.classList.toggle("pg-condensado", condensado);
                ultimo = condensado;
            }
        };
        window.addEventListener("scroll", function () {
            window.requestAnimationFrame(aoRolar);
        }, { passive: true });
        aoRolar();
    }
})();
