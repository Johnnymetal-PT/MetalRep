/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Mega-menu de categorias do cabecalho.
 *
 * No desenho (Home.svg, Component_1_12) o cabecalho abre para 345px de altura
 * revelando cinco colunas de categorias. Abre por hover em desktop e por
 * teclado (focus) para navegacao acessivel.
 */
publicWidget.registry.HmdMegaMenu = publicWidget.Widget.extend({
    selector: ".hmd-header",
    events: {
        "mouseenter .hmd-nav__trigger": "_onOpen",
        "focusin .hmd-nav__trigger": "_onOpen",
        "mouseleave": "_onClose",
        "keydown": "_onKeydown",
    },

    start() {
        this.$menu = this.$(".hmd-megamenu");
        this._onScroll = this._onScroll.bind(this);
        window.addEventListener("scroll", this._onScroll, { passive: true });
        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener("scroll", this._onScroll);
        return this._super(...arguments);
    },

    // O mega-menu do desenho esta sempre visivel; estes metodos ficam sem
    // efeito pratico mas mantem o widget compativel com quem lhe chame.
    _onOpen() {
        this.$menu.addClass("is-open");
    },

    _onClose() {
        this.$menu.removeClass("is-open");
    },

    _onKeydown(ev) {
        if (ev.key === "Escape") {
            this._onClose();
        }
    },

    _onScroll() {
        this.el.classList.toggle("hmd-header--scrolled", window.scrollY > 8);
    },
});

/**
 * Painel de categorias em ecra inteiro no mobile.
 * Origem: Website_Design/Mobile/MENU CATEGORIAS.svg
 */
publicWidget.registry.HmdMobileMenu = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        "click .hmd-burger": "_onToggle",
        "click .hmd-mobile-menu__close": "_onToggle",
        "click .hmd-mobile-menu__into": "_onInto",
        "click .hmd-mobile-menu__back": "_onBack",
    },

    _panel() {
        return this.el.querySelector(".hmd-mobile-menu");
    },

    /**
     * Mostra um dos niveis do painel. Os niveis estao todos no HTML e
     * trocam-se por classe, sem ir ao servidor.
     */
    _show(name) {
        const panel = this._panel();
        if (!panel) {
            return;
        }
        let achou = false;
        panel.querySelectorAll(".hmd-mobile-menu__level").forEach((level) => {
            const activo = level.dataset.hmdLevel === name;
            level.classList.toggle("is-active", activo);
            achou = achou || activo;
        });
        // Se o nivel pedido nao existir, nao deixamos o painel em branco.
        if (!achou) {
            const raiz = panel.querySelector('[data-hmd-level="root"]');
            if (raiz) {
                raiz.classList.add("is-active");
            }
        }
        panel.scrollTop = 0;
    },

    _onToggle(ev) {
        ev.preventDefault();
        const panel = this._panel();
        if (!panel) {
            return;
        }
        const open = panel.classList.toggle("is-open");
        document.body.style.overflow = open ? "hidden" : "";
        // Fechar devolve o painel ao primeiro nivel: reabrir a meio de uma
        // subcategoria era desorientador.
        if (!open) {
            this._show("root");
        }
    },

    _onInto(ev) {
        ev.preventDefault();
        this._show(ev.currentTarget.dataset.hmdTarget);
    },

    _onBack(ev) {
        ev.preventDefault();
        this._show("root");
    },
});

/**
 * Paginacao da galeria de ambiente da pagina de produto ("1_2_3_4_5").
 */
publicWidget.registry.HmdLifestyleGallery = publicWidget.Widget.extend({
    selector: ".hmd-lifestyle",
    events: {
        "click .hmd-lifestyle__dot": "_onSelect",
    },

    start() {
        this.slides = Array.from(this.el.querySelectorAll(".hmd-lifestyle__slide"));
        this.dots = Array.from(this.el.querySelectorAll(".hmd-lifestyle__dot"));
        this._show(0);
        return this._super(...arguments);
    },

    _show(index) {
        this.slides.forEach((slide, i) => {
            slide.hidden = i !== index;
        });
        this.dots.forEach((dot, i) => {
            dot.classList.toggle("is-active", i === index);
        });
    },

    _onSelect(ev) {
        this._show(this.dots.indexOf(ev.currentTarget));
    },
});

/**
 * Desenho de dimensoes para junto da fotografia do produto.
 *
 * A prancha poe o desenho tecnico logo abaixo da fotografia, dentro do bloco
 * branco de compra. No conteudo real ele vive dentro do campo de HTML da
 * galeria do produto (website_gallery_html), montado no Construtor pela HMD —
 * ou seja, noutra seccao da pagina.
 *
 * Nao se resolve com CSS: sao subarvores diferentes do documento, e nenhuma
 * regra move um elemento de uma para a outra. Nao se resolve com xpath: o
 * conteudo do campo e entregue como um bloco unico e nao e alcancavel por
 * heranca de vista. Resta mover o no no navegador, que e o que este widget faz.
 *
 * Salvaguardas, por esta ordem de importancia:
 *
 * 1. disabledInEditableMode: no Construtor o widget NAO corre. Se corresse, a
 *    Monica estaria a editar um elemento que nos tinhamos mudado de sitio, e a
 *    gravacao escrevia-o no lugar errado. Em edicao a pagina fica como esta na
 *    base de dados.
 * 2. Idempotente: se ja foi movido, nao repete.
 * 3. Se nao encontrar nada, nao faz nada — a pagina continua valida.
 *
 * Como reconhece o desenho: pela legenda comecada por "Dimens" (serve o
 * ingles "Dimensions in" e o portugues "Dimensoes em") ou pelo nome do
 * ficheiro conter "Medida", que e a convencao usada pela HMD. Se um dia essa
 * convencao mudar, o desenho deixa de ser movido e volta ao lugar antigo —
 * degrada, nao parte.
 *
 * A alternativa duradoura e um campo proprio no produto para o desenho
 * tecnico, e deixar de depender de onde o conteudo foi montado. Fica registado
 * no ponto 10 do documento da reuniao, estimado em meio dia.
 */
publicWidget.registry.HmdDimensions = publicWidget.Widget.extend({
    selector: ".hmd-product-page",
    disabledInEditableMode: true,

    start() {
        const media = this.el.querySelector(".hmd-buy__media");
        if (!media) {
            return this._super(...arguments);
        }
        // #8376: com o campo "Desenho de medidas" preenchido, o desenho ja vem
        // do servidor (.hmd-dimensions--campo). Esconde-se o da galeria, se o
        // houver, para nao aparecer duas vezes.
        if (media.querySelector(".hmd-dimensions")) {
            for (const figura of this.el.querySelectorAll('[data-oe-field="website_gallery_html"] figure')) {
                const legenda = (figura.querySelector("figcaption")?.textContent || "").trim();
                const origem = decodeURIComponent(figura.querySelector("img")?.getAttribute("src") || "");
                if (/^Dimens/i.test(legenda) || /Medida/i.test(origem)) {
                    figura.style.display = "none";
                    const seccao = figura.closest("section");
                    if (seccao && ![...seccao.querySelectorAll("img")].some((i) => i.closest("figure")?.style.display !== "none")) {
                        seccao.style.display = "none";
                    }
                }
            }
            return this._super(...arguments);
        }

        const figuras = this.el.querySelectorAll(
            '[data-oe-field="website_gallery_html"] figure'
        );

        for (const figura of figuras) {
            const legenda = (figura.querySelector("figcaption")?.textContent || "").trim();
            const imagem = figura.querySelector("img");
            const origem = decodeURIComponent(imagem?.getAttribute("src") || "");

            if (!/^Dimens/i.test(legenda) && !/Medida/i.test(origem)) {
                continue;
            }

            const seccao = figura.closest("section");
            const caixa = document.createElement("div");
            caixa.className = "hmd-dimensions";
            caixa.appendChild(figura);

            // O desenho fica na coluna da fotografia, por baixo dela
            // (pedido da HMD, 07/09/2026).
            //
            // Basta acrescenta-lo ao fim dessa coluna: a fotografia e o unico
            // conteudo que la esta, por isso "no fim" e "por baixo da imagem"
            // sao a mesma coisa — e continua a se-lo se o carrossel mudar de
            // marcacao, o que nao aconteceria com uma ancora presa a um
            // elemento concreto dele.
            //
            // Passou por duas moradas antes desta, ambas na coluna da direita:
            // a seguir a descricao, e depois a seguir ao bloco B2B. As duas
            // dependiam de elementos que nem todas as paginas tem — o bloco
            // B2B, por exemplo, so existe para quem nao tem sessao iniciada.
            // Aqui nao ha essa dependencia.
            media.appendChild(caixa);

            // A seccao de origem fica sem imagens: esconde-se para nao deixar
            // uma faixa vazia no meio da pagina.
            if (seccao && !seccao.querySelector("img")) {
                seccao.style.display = "none";
            }
            break;
        }

        return this._super(...arguments);
    },
});

/**
 * Dispoe o configurador nativo do Odoo como na prancha do produto.
 *
 * A descricao e os documentos ficam na coluna direita. O formulario de
 * variantes/carrinho passa para uma linha posterior, na coluna esquerda,
 * abaixo do desenho tecnico. Move-se o proprio formulario: toda a logica
 * standard de variantes, preco, quantidade, wishlist e comparacao permanece
 * ligada aos mesmos elementos.
 */
publicWidget.registry.HmdBuyLayout = publicWidget.Widget.extend({
    selector: ".hmd-buy",
    disabledInEditableMode: true,

    start() {
        const formulario = this.el.querySelector(
            ":scope > .hmd-buy__details > .hmd-buy__form"
        );
        if (formulario) {
            this.el.appendChild(formulario);
        }
        return this._super(...arguments);
    },
});

/**
 * Indice numerado sob a fotografia de ambiente da galeria.
 *
 * A prancha poe "1__2__3__4__5" alinhado a direita, sob a imagem grande. Esse
 * carrossel e o nosso .hmd-lifestyle, alimentado pelas imagens extra do
 * produto — que hoje estao vazias em praticamente todos os artigos, porque as
 * fotografias foram montadas dentro de snippets do Construtor.
 *
 * Enquanto for assim, a fotografia de ambiente que existe e a do bloco de
 * maconaria. Este widget da-lhe o mesmo indice numerado da prancha.
 *
 * Porque SPAN e nao BUTTON: com uma imagem so, um botao nao teria nada para
 * fazer. Um controlo que nao controla nada e pior do que um numero que nunca
 * prometeu ser clicavel. Quando as fotografias passarem para as imagens extra
 * do produto, o .hmd-lifestyle assume — e ai os numeros SAO botoes, porque ai
 * ha por onde navegar.
 *
 * Nao corre no Construtor, pela mesma razao do HmdDimensions: nao mexer no DOM
 * enquanto a HMD edita.
 */
publicWidget.registry.HmdGalleryIndex = publicWidget.Widget.extend({
    selector: ".hmd-product-page",
    disabledInEditableMode: true,

    start() {
        const seccao = this.el.querySelector(
            '[data-oe-field="website_gallery_html"] section.s_masonry_block'
        );
        if (!seccao || seccao.querySelector(".hmd-gallery-index")) {
            return this._super(...arguments);
        }

        const imagens = seccao.querySelectorAll("img");
        if (!imagens.length) {
            return this._super(...arguments);
        }

        const tira = document.createElement("div");
        tira.className = "hmd-gallery-index";
        tira.setAttribute("aria-hidden", "true");
        for (let i = 0; i < imagens.length; i++) {
            const numero = document.createElement("span");
            numero.className = "hmd-gallery-index__n";
            if (i === 0) {
                numero.classList.add("is-active");
            }
            numero.textContent = String(i + 1);
            tira.appendChild(numero);
        }
        seccao.appendChild(tira);

        return this._super(...arguments);
    },
});

/**
 * Contador de quantidade do bloco de compra.
 * Delega no input nativo do website_sale para nao perder a logica do Odoo.
 */
publicWidget.registry.HmdQuantity = publicWidget.Widget.extend({
    selector: ".hmd-qty",
    events: {
        "click .hmd-qty__minus": "_onStep",
        "click .hmd-qty__plus": "_onStep",
    },

    _onStep(ev) {
        ev.preventDefault();
        const input = this.el.querySelector("input");
        if (!input) {
            return;
        }
        const step = ev.currentTarget.classList.contains("hmd-qty__plus") ? 1 : -1;
        const min = parseFloat(input.getAttribute("min") || "0");
        const next = Math.max(min, (parseFloat(input.value) || 0) + step);
        input.value = next;
        input.dispatchEvent(new Event("change", { bubbles: true }));
    },
});

/**
 * Newsletter do rodape (e do menu mobile).
 *
 * O formulario fazia POST para /website_mass_mailing/is_subscriber, rota que
 * so VERIFICA se o email ja esta inscrito, e a copia do rodape gravada pelo
 * editor (website 3) leva um csrf_token fixo: ninguem ficava inscrito
 * (verificado a 20/10/2026, #8116). A HMD quer a newsletter ligada.
 *
 * Em vez de mexer nas vistas (o rodape tem copia propria do editor), o
 * envio passa a ser feito aqui, pela mesma rota que os blocos de newsletter
 * do Odoo usam (website_mass_mailing/controllers/main.py, subscribe), que
 * nao precisa do csrf do formulario.
 *
 * Lista: "Newsletter" (id 1, publica), salvo data-list-id no <form>.
 */
const HMD_NEWSLETTER_LIST_ID = 1;

publicWidget.registry.HmdNewsletter = publicWidget.Widget.extend({
    selector: ".hmd-newsletter",
    events: { submit: "_onSubmit" },

    async _onSubmit(ev) {
        ev.preventDefault();
        const input = this.el.querySelector('input[name="email"]');
        const button = this.el.querySelector('button[type="submit"]');
        const email = (input.value || "").trim();
        if (!email || !input.checkValidity()) {
            input.reportValidity();
            return;
        }
        button.disabled = true;
        try {
            const result = await rpc("/website_mass_mailing/subscribe", {
                list_id: parseInt(this.el.dataset.listId, 10) || HMD_NEWSLETTER_LIST_ID,
                value: email,
                subscription_type: "email",
            });
            const ok = result && result.toast_type === "success";
            input.value = "";
            input.placeholder = ok ? "Thank you for subscribing" : (result && result.toast_content) || "Please try again";
        } catch {
            input.placeholder = "Please try again";
        } finally {
            button.disabled = false;
        }
    },
});
