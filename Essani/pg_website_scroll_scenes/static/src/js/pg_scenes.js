/* PG Scroll Scenes — secções fixas cuja animação avança com o scroll.
 *
 * Cada `.pg-scene` fica fixa no ecrã enquanto se faz scroll; uma timeline com um passo por
 * `data-pg-step` avança e recua com a posição do scroll (como no site da Halemeier).
 *
 * Só liga em ecrã largo, sem "reduzir movimento" e fora do editor. Em qualquer outro caso
 * a classe `pg-scene--live` nunca é posta e o CSS mostra os passos todos, em coluna.
 * O motor não escreve HTML nem mexe em vistas.
 */
(function () {
    "use strict";

    var ECRA_LARGO = "(min-width: 992px)";
    var COM_MOVIMENTO = "(prefers-reduced-motion: no-preference)";
    // Quanto scroll gasta cada passo, em múltiplos da altura do ecrã.
    var VH_POR_PASSO = 0.9;

    function noEditor() {
        var b = document.body;
        return !b || b.classList.contains("editor_enable") ||
            document.documentElement.classList.contains("editor_enable") ||
            !!document.querySelector("#oe_main_menu_navbar, .o_edit_website_container");
    }

    // No Odoo quem faz scroll costuma ser o #wrapwrap e não a janela.
    function quemFazScroll() {
        var w = document.getElementById("wrapwrap");
        if (w) {
            var o = window.getComputedStyle(w).overflowY;
            if ((o === "auto" || o === "scroll") && w.scrollHeight > w.clientHeight + 1) {
                return w;
            }
        }
        return window;
    }

    // Altura do cabeçalho quando ele fica por cima do conteúdo ao fazer scroll.
    function alturaCabecalho() {
        var h = document.querySelector("#wrapwrap > header");
        if (!h) {
            return 0;
        }
        var pos = window.getComputedStyle(h).position;
        return (pos === "fixed" || pos === "sticky") ? Math.round(h.getBoundingClientRect().height) : 0;
    }

    // Um `transform`/`filter`/`perspective` num ancestral faz dele o ponto de referência do
    // `position: fixed`, e a cena "fixa" passa a deslizar com o scroll.
    function criaReferenciaParaFixed(el) {
        var c = window.getComputedStyle(el);
        return c.transform !== "none" || c.filter !== "none" || c.perspective !== "none" ||
            /transform|filter|perspective/.test(c.willChange) || /paint|layout/.test(c.contain);
    }

    function ancestralQueQuebraFixed(el) {
        for (var p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
            if (criaReferenciaParaFixed(p)) { return p; }
        }
        return null;
    }

    // O V4 põe no #wrapwrap uma animação de entrada (`animation: ... both`) que, depois de
    // acabar, deixa um transform ativo. O estado final dela é o normal, por isso retira-se.
    function soltarAnimacaoDeEntrada() {
        var w = document.getElementById("wrapwrap");
        if (!w || !w.getAnimations || !criaReferenciaParaFixed(w)) {
            return Promise.resolve();
        }
        return Promise.all(w.getAnimations().map(function (a) {
            return a.finished.catch(function () {});
        })).then(function () {
            w.style.animation = "none";
        });
    }

    function deslocamento(el) {
        var de = el.getAttribute("data-pg-from") || "up";
        return {
            up: { y: 36 }, down: { y: -36 }, left: { x: -60 }, right: { x: 60 },
            zoom: { scale: 0.92 }, fade: {}
        }[de] || { y: 36 };
    }

    function montar(cena, sc, hdr) {
        var passos = {};
        var n = 0;
        Array.prototype.forEach.call(cena.querySelectorAll("[data-pg-step]"), function (el) {
            var k = parseInt(el.getAttribute("data-pg-step"), 10);
            if (!k) { return; }
            (passos[k] = passos[k] || []).push(el);
            n = Math.max(n, k);
        });
        if (!n) { return null; }

        // `data-pg-vh` na secção: ecrãs de scroll por passo (por omissão VH_POR_PASSO).
        var vh = parseFloat(cena.getAttribute("data-pg-vh")) || VH_POR_PASSO;
        cena.style.setProperty("--pg-hdr", hdr + "px");
        cena.classList.add("pg-scene--live");

        var fundo = cena.querySelector(".pg-scene__bg");
        var veu = cena.querySelector(".pg-scene__veil");
        var camadas = Array.prototype.slice.call(cena.querySelectorAll(".pg-scene__layer"));
        var barra = cena.querySelector(".pg-scene__bar i");
        var pontos = [];
        var caixaPontos = cena.querySelector(".pg-scene__dots");
        if (caixaPontos && !caixaPontos.children.length) {
            for (var i = 0; i < n; i++) {
                var p = document.createElement("span");
                caixaPontos.appendChild(p);
                pontos.push(p);
            }
        }

        var desfazer = [];
        var indices = Array.prototype.slice.call(cena.querySelectorAll("[data-pg-index]"));

        // Parte o texto em palavras com máscara, para a revelação palavra a palavra.
        function dividirPalavras(el) {
            var original = el.innerHTML;
            var texto = el.textContent.trim().replace(/\s+/g, " ");
            el.setAttribute("aria-label", texto);
            el.innerHTML = texto.split(" ").map(function (w) {
                return '<span class="pg-w" aria-hidden="true"><span class="pg-wi">' +
                    w.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</span></span>";
            }).join(" ");
            desfazer.push(function () {
                el.innerHTML = original;
                el.removeAttribute("aria-label");
            });
            return Array.prototype.slice.call(el.querySelectorAll(".pg-wi"));
        }

        var tl = window.gsap.timeline({ defaults: { ease: "none" } });
        // Cada passo ocupa 1 unidade da timeline: entra, aguenta, sai (menos o último).
        for (var k = 1; k <= n; k++) {
            (passos[k] || []).forEach(function (el, idx) {
                var t = k - 1;
                var ultimo = k === n || el.hasAttribute("data-pg-keep");
                var de = deslocamento(el);
                var camada = el.classList.contains("pg-scene__layer");
                // `data-pg-dur`: quanto dura a entrada, em fração de um passo (por omissão 0.3).
                var dur = parseFloat(el.getAttribute("data-pg-dur")) || 0.3;

                // Contadores: o número sobe com o scroll.
                Array.prototype.forEach.call(el.querySelectorAll("[data-pg-count]"), function (c) {
                    var alvo = parseFloat(c.getAttribute("data-pg-count"));
                    var pref = c.getAttribute("data-pg-prefix") || "";
                    var original = c.textContent;
                    var o = { v: 0 };
                    desfazer.push(function () { c.textContent = original; });
                    tl.fromTo(o, { v: 0 }, {
                        v: alvo, duration: k === 1 ? 0.6 : dur + 0.4, ease: "power1.out",
                        onUpdate: function () { c.textContent = pref + Math.round(o.v); }
                    }, k === 1 ? 0 : t + 0.02);
                });

                if (k === 1) {
                    // O primeiro passo já está à vista quando a cena chega ao topo.
                    window.gsap.set(el, { autoAlpha: 1 });
                } else if (camada) {
                    tl.fromTo(el, { autoAlpha: 0 },
                        { autoAlpha: 1, duration: dur, ease: "none" }, t);
                } else {
                    // O passo aparece depressa; o que está dentro entra em cascata.
                    var palavras = [], regras = [], outros = [];
                    Array.prototype.forEach.call(el.children, function (c) {
                        if (c.classList.contains("pg-rule")) { regras.push(c); }
                        else if (c.hasAttribute("data-pg-split")) {
                            palavras = palavras.concat(dividirPalavras(c));
                        } else { outros.push(c); }
                    });
                    var base = t + 0.02 + 0.04 * idx;
                    tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.08, ease: "none" }, t);
                    if (outros.length) {
                        tl.fromTo(outros, Object.assign({ autoAlpha: 0 }, de),
                            { autoAlpha: 1, x: 0, y: 0, scale: 1, duration: dur, ease: "power3.out", stagger: 0.07 },
                            base);
                    }
                    if (palavras.length) {
                        tl.fromTo(palavras, { yPercent: 118 },
                            { yPercent: 0, duration: dur + 0.1, ease: "power3.out", stagger: 0.05 }, base);
                    }
                    if (regras.length) {
                        tl.fromTo(regras, { scaleX: 0 },
                            { scaleX: 1, duration: dur + 0.25, ease: "power2.inOut" }, base + 0.1);
                    }
                }
                if (!ultimo && !camada) {
                    tl.to(el, { autoAlpha: 0, y: -28, duration: 0.22, ease: "power1.in" }, t + 0.78);
                }
                if (camada) {
                    // A imagem aproxima-se devagar enquanto está à vista (menos as ilustrações).
                    var img = el.querySelector("img");
                    if (img && !el.closest(".pg-scene__layers--contain")) {
                        tl.fromTo(img, { scale: 1.1 }, { scale: 1, duration: 1.5, ease: "none" }, t);
                    }
                }
                if (camada && k < n) {
                    // Só se esconde depois de a camada seguinte a cobrir por completo.
                    var seguinte = (passos[k + 1] || []).filter(function (e) {
                        return e.classList.contains("pg-scene__layer");
                    })[0];
                    var durSeg = seguinte ? (parseFloat(seguinte.getAttribute("data-pg-dur")) || 0.3) : 0.3;
                    tl.set(el, { autoAlpha: 0 }, t + 1 + durSeg + 0.05);
                }
            });
        }
        var brilho = cena.querySelector(".pg-scene__glow");
        if (brilho) {
            tl.fromTo(brilho, { opacity: 0.3, scale: 0.8, xPercent: -6 },
                { opacity: 1, scale: 1.3, xPercent: 6, duration: n, ease: "none" }, 0);
        }
        if (fundo) {
            var z = parseFloat(cena.getAttribute("data-pg-zoom")) || 1.12;
            tl.fromTo(fundo, { scale: 1 }, { scale: z, duration: n, ease: "none" }, 0);
        }
        if (veu) {
            var v = (cena.getAttribute("data-pg-veil") || "0.25,0.65").split(",");
            tl.fromTo(veu, { opacity: parseFloat(v[0]) },
                { opacity: parseFloat(v[1]), duration: n, ease: "none" }, 0);
        }
        if (barra) {
            tl.fromTo(barra, { scaleX: 0 }, { scaleX: 1, duration: n, ease: "none" }, 0);
        }
        tl.to({}, { duration: 0.001 }, n);   // fixa a duração total em n

        var st = window.ScrollTrigger.create({
            trigger: cena,
            scroller: sc,
            pin: true,
            // Se ainda houver um ancestral a quebrar o `fixed`, fixa por transform.
            pinType: ancestralQueQuebraFixed(cena) ? "transform" : (sc === window ? "fixed" : "transform"),
            anticipatePin: 1,
            start: "top top+=" + hdr,
            end: function () { return "+=" + Math.round(n * vh * window.innerHeight); },
            scrub: 0.7,
            animation: tl,
            invalidateOnRefresh: true,
            onUpdate: function (s) {
                var ativo = Math.min(n - 1, Math.floor(s.progress * n - 0.0001));
                pontos.forEach(function (p, i) { p.classList.toggle("on", i === Math.max(0, ativo)); });
                indices.forEach(function (li) {
                    var k2 = parseInt(li.getAttribute("data-pg-index"), 10);
                    li.classList.toggle("on", k2 === Math.max(0, ativo) + 1);
                    li.classList.toggle("past", k2 < Math.max(0, ativo) + 1);
                });
            }
        });
        return function () {
            st.kill();
            tl.kill();
            cena.classList.remove("pg-scene--live");
            cena.style.removeProperty("--pg-hdr");
            // O gsap.matchMedia repõe os estilos que as animações tocaram.
            desfazer.forEach(function (f) { f(); });
            indices.forEach(function (li) { li.classList.remove("on", "past"); });
            pontos.forEach(function (p) { p.remove(); });
        };
    }

    function iniciar() {
        var cenas = document.querySelectorAll("[data-pg-scene]");
        if (!cenas.length || noEditor() || !window.gsap || !window.ScrollTrigger) {
            return;
        }
        window.gsap.registerPlugin(window.ScrollTrigger);
        soltarAnimacaoDeEntrada().then(arrancar);
    }

    function arrancar() {
        var cenas = document.querySelectorAll("[data-pg-scene]");
        var sc = quemFazScroll();
        var mm = window.gsap.matchMedia();
        mm.add(ECRA_LARGO + " and " + COM_MOVIMENTO, function () {
            var hdr = alturaCabecalho();
            var limpar = [];
            Array.prototype.forEach.call(cenas, function (c) {
                var f = montar(c, sc, hdr);
                if (f) { limpar.push(f); }
            });
            // As imagens carregam depois e mexem nas alturas.
            window.addEventListener("load", function () { window.ScrollTrigger.refresh(); });
            return function () { limpar.forEach(function (f) { f(); }); };
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
