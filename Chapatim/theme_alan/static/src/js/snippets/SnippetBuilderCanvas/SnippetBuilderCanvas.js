import { rpc } from "@web/core/network/rpc";
import { Component, useRef, onMounted, onWillUnmount, useState, onPatched } from "@odoo/owl";

// ─── Snippet Builder Canvas Component ─────────────────────────────────
export class SnippetBuilderCanvas extends Component {
    static template = "theme_alan.snippet_builder_canvas";
    static props = {
        editor: Object,
        config: Object,
        snippet_type: String,
        deviceView: { type: String, optional: true },
    };

    setup() {
        this.previewContainer = useRef("as-sb-preview-container");
        this.state = useState({ HasRecords: false })
        this._onConfigUpdated = (config) => this.onConfigUpdated(config);
        this.face = null;
        this.tooltip = null;
        this.emoji = null;
        this.isHoveringFace = false;
        this._mousemove = null;
        this.innerRoot = null;
        this.iframeLoaded = false;
        this.pendingRender = null;
        onPatched(() => this._updateHoverClasses());

        onMounted(async () => {
            this.env.bus.addEventListener("config_updated", this._onConfigUpdated);
            if (document.querySelector(".as-sb-canvas-empty-image")) {
                const findEl = (id) => {
                    let el = document.getElementById(id);
                    if (el) return { el, root: 'parent' };
                    try {
                        const iframe = this.previewContainer?.el;
                        if (iframe && iframe.contentDocument) {
                            el = iframe.contentDocument.getElementById(id);
                            if (el) return { el, root: 'iframe', iframe };
                        }
                    } catch (err) {
                        console.warn("Cannot access iframe document:", err);
                    }
                    return { el: null, root: null };
                };

                const faceFound = findEl("face");
                const tooltipFound = findEl("tooltip");
                const emojiFound = findEl("as-sb-emoji");
                this.face = faceFound.el;
                this.tooltip = tooltipFound.el;
                this.emoji = emojiFound.el;

                if (this.emoji) {
                    this.emoji.addEventListener("mouseenter", () => this.isHoveringFace = true);
                    this.emoji.addEventListener("mouseleave", () => {
                        this.isHoveringFace = false;
                        if (document.querySelector(".as-sb-canvas-empty-image")) {
                            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-height", "22px");
                        }
                    });
                }

                this._mousemove = (ev) => {
                    this.eyeball(ev);
                    const rect = (this.face && this.face.getBoundingClientRect) ? this.face.getBoundingClientRect() : { left: 0, width: window.innerWidth };
                    const centerX = rect.left + rect.width / 2;
                    let mood = (ev.pageX - centerX) / centerX;
                    mood = Math.max(-1, Math.min(1, mood));
                    this.updateCSSVariables(mood);
                    this.updateTooltip(mood, ev);
                };

                document.body.addEventListener("mousemove", this._mousemove);

                try {
                    const iframe = this.previewContainer?.el;
                    if (iframe && iframe.contentWindow && iframe.contentDocument) {
                        iframe.contentWindow.addEventListener("mousemove", this._mousemove);
                        iframe.contentDocument.addEventListener("mousemove", this._mousemove);
                    }
                } catch (err) {
                    console.warn("Could not attach to iframe (probably cross-origin):", err);
                }
            }
        });

        onWillUnmount(() => {
            if (this._renderTimeout) {
                clearTimeout(this._renderTimeout);
                this._renderTimeout = null;
            }

            if (this._mousemove) {
                document.body.removeEventListener("mousemove", this._mousemove);
                try {
                    const iframe = this.previewContainer?.el;
                    if (iframe && iframe.contentWindow && iframe.contentDocument) {
                        iframe.contentWindow.removeEventListener("mousemove", this._mousemove);
                        iframe.contentDocument.removeEventListener("mousemove", this._mousemove);
                    }
                } catch (err) {
                    console.error("Could not detach from iframe (probably cross-origin):", err);
                }
            }
            if (this.emoji) {
                this.emoji.removeEventListener("mouseenter", () => this.isHoveringFace = true);
                this.emoji.removeEventListener("mouseleave", () => {/*...*/ });
            }
            this.env.bus.removeEventListener("config_updated", this._onConfigUpdated);
        });
    }

    _updateHoverClasses() {
        const iframe = this.previewContainer.el;

        if (!iframe || !iframe.contentDocument) return;

        const container = iframe.contentDocument.querySelector(".as-snippet-drop-container");
        if (!container) return;

        const deviceView = this.props.deviceView || 'desktop';
        const hasHoverDesktop = this.props.config.allow_hover_image;
        const hasHoverMobile = this.props.config.mob_allow_hover_image;

        container.classList.remove(
            "o_wsale_products_opt_img_secondary_show",
            "o_wsale_products_opt_img_hover_zoom_out_light"
        );

        let shouldShowHover = false;
        if (deviceView === 'mobile') {
            shouldShowHover = hasHoverMobile;
        } else {
            shouldShowHover = hasHoverDesktop;
        }

        if (shouldShowHover) {
            container.classList.add("o_wsale_products_opt_img_secondary_show");
            container.classList.add("o_wsale_products_opt_img_hover_zoom_out_light");
        }
    }

    onIframeLoaded() {
        this.iframeLoaded = true;
        if (this.pendingRender) {
            const config = this.pendingRender;
            this.pendingRender = null;
            this.renderPreview(config);
        }

        const iframe = this.previewContainer?.el;
        if (iframe?.contentDocument) {
            iframe.contentDocument.addEventListener('click', () => {
                this.env.bus.trigger("close_template_menu");
            });
        }
    }

    // Canvas Face
    eyeball(event) {
        document.querySelectorAll(".eye-inner").forEach((eye) => {
            let x = eye.getBoundingClientRect().left + eye.clientWidth / 2;
            let y = eye.getBoundingClientRect().top + eye.clientHeight / 2;

            let rad = Math.atan2(event.pageX - x, event.pageY - y);
            let rot = (rad * (180 / Math.PI) * -1) + 270;

            eye.style.transform = `rotate(${rot}deg)`;
        });
    }

    updateTooltip(mood, ev) {
        if (!this.tooltip) return;
        const canvasArea = document.querySelector('.as-sb-canvas-area');
        if (!canvasArea) return;

        const canvasRect = canvasArea.getBoundingClientRect();
        const isWithinCanvas = (
            ev.clientX >= canvasRect.left &&
            ev.clientX <= canvasRect.right &&
            ev.clientY >= canvasRect.top &&
            ev.clientY <= canvasRect.bottom
        );

        if (!isWithinCanvas) {
            this.tooltip.style.opacity = 0;
            return;
        }

        // Show and position tooltip only within canvas area
        this.tooltip.style.left = (ev.pageX - 16) + "px";
        this.tooltip.style.top = (ev.pageY + 44) + "px";
        this.tooltip.style.opacity = 1;

        let label = "";
        if (mood > 0) {
            const w = Math.floor(mood * 1);
            const d = Math.floor(mood * 4);
            label = "No" + "o".repeat(w) + ".".repeat(d);
        } else {
            const w = Math.floor(Math.abs(mood) * 3);
            const d = Math.floor(Math.abs(mood) * 5);
            label = "Yes" + "s".repeat(w) + ".".repeat(d);
        }
        this.tooltip.textContent = label;
    }

    updateCSSVariables(mood) {
        const green = ["#84f069", "#29a429", "#57CC02", "#D6FFB8", "#5BAF1E", "87,204,2"];
        const red = ["#FFACAC", "#FD4040", "#FD3A3A", "#FFC5C5", "#E92D2D", "253,58,58"];
        const t = (mood + 1) / 2;
        function mixColor(c1, c2) {
            const r1 = parseInt(c1.slice(1, 3), 16);
            const g1 = parseInt(c1.slice(3, 5), 16);
            const b1 = parseInt(c1.slice(5, 7), 16);
            const r2 = parseInt(c2.slice(1, 3), 16);
            const g2 = parseInt(c2.slice(3, 5), 16);
            const b2 = parseInt(c2.slice(5, 7), 16);

            return (
                "#" +
                Math.round(r1 + (r2 - r1) * t).toString(16).padStart(2, "0") +
                Math.round(g1 + (g2 - g1) * t).toString(16).padStart(2, "0") +
                Math.round(b1 + (b2 - b1) * t).toString(16).padStart(2, "0")
            );
        }

        // Face gradient colors
        if (document.querySelector(".as-sb-canvas-empty-image")) {
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-1", mixColor(green[0], red[0]));
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-2", mixColor(green[1], red[1]));
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-3", mixColor(green[2], red[2]));
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-4", mixColor(green[3], red[3]));
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-5", mixColor(green[4], red[4]));

            // Mouth movement
            const mouthTop = 24 + (51 - 24) * t;
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-top", mouthTop + "px");
            const m = Math.abs(mood);
            const mouthWidth = 14 + (24 - 14) * m;
            const mouthHeight = 3 + (22 - 3) * m;
            const gRGB = green[5].split(",").map(Number);
            const rRGB = red[5].split(",").map(Number);
            const rgb = gRGB.map((v, i) => Math.round(v + (rRGB[i] - v) * t)).join(",");
            document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--emoji-color-3-rgb", rgb);

            if (this.isHoveringFace) {
                document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-width", "24px");
                document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-height", mouthHeight + "px");
            } else {
                document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-width", mouthWidth + "px");
                document.querySelector(".as-sb-canvas-empty-image").style.setProperty("--mouth-height", "22px");
            }
        }

    }

    async onConfigUpdated(config) {
        document.querySelector(".as-sb-preview-container").classList.remove("d-none")
        this.renderPreview(config);
    }

    async renderPreview(config = this.props.config) {
        if (this._renderTimeout) {
            clearTimeout(this._renderTimeout);
        }
        this._renderTimeout = setTimeout(() => {
            this._doRenderPreview(config);
        }, 300);
    }

    async _doRenderPreview(config = this.props.config) {
        if (!this.iframeLoaded) {
            this.pendingRender = config;
            return;
        }

        if (!this.previewContainer.el || !this.previewContainer.el.contentDocument) {
            return;
        }

        const endpoint = this.props.snippet_type === "as_mega_menu" ? "/get_megamenu_snippet_template" : "/get_snippet_template";
        let record_ids = this.props.config.selected_records || [];
        const context = {
            snippet: this.props.config.technical_name,
            record_ids: record_ids,
            model: this.props.config.model,
            design_editor: this.props.config,
            get_details: true,
        };

        try {
            const response = await rpc(endpoint, context);
            if (!response) return;
            let html = response.template || (config && config.html) || "<div class='as-sb-canvas-container d-flex justify-content-center align-items-center'><img src='/theme_alan/static/src/img/snippets/selection.png' alt='Select Features'/></div>";
            if (response.record_ids) {
                this.props.config.selected_records = response.record_ids;
            }
            if (this.props.config.sections && response.sections) {
                this.props.config.sections = response.sections;
            }
            if (response.record_ids && response.record_ids.length === 0) {
                html = "<div class='as-sb-canvas-container d-flex justify-content-center align-items-center'><img src='/theme_alan/static/src/img/snippets/no-record.png' alt='No record Found'/></div>";
            }
            this.props.config.record_info = response.record_details || [];
            this._updateIframeContent(html, response.slider_config);

        } catch (err) {
            console.error("Failed to fetch snippet template:", err);
        }
    }

    _updateIframeContent(html, sliderConfig) {
        const doc = this.previewContainer.el.contentDocument;
        const container = doc.querySelector('.as-snippet-drop-container');
        const wrapper = doc.querySelector('#as_sb_wrap');

        if (container) {
            container.innerHTML = html;

            const hasHoverDesktop = this.props.config.allow_hover_image;
            const hasHoverMobile = this.props.config.mob_allow_hover_image;

            container.classList.remove(
                "o_wsale_products_opt_img_secondary_show",
                "o_wsale_products_opt_img_hover_zoom_out_light"
            );

            if (hasHoverDesktop || hasHoverMobile) {
                container.classList.add("o_wsale_products_opt_img_secondary_show");
                container.classList.add("o_wsale_products_opt_img_hover_zoom_out_light");
            }
            const mobileBottomHeaders = doc.querySelectorAll('.header-mobile-bottom');
            mobileBottomHeaders.forEach(element => {
                element.classList.add('d-none');
            });

            // Handle Swiper
            const swiperElement = doc.querySelector(".as_page_swiper");
            if (swiperElement && sliderConfig) {
                const iframeWindow = this.previewContainer.el.contentWindow;
                if (iframeWindow.Swiper) {
                    const swiperWrapper = swiperElement.querySelector(".swiper-wrapper");
                    if (swiperWrapper && swiperWrapper.children.length > 0) {
                        try {
                            // Destroy existing Swiper if any to prevent memory leaks
                            if (swiperElement.swiper) {
                                swiperElement.swiper.destroy(true, true);
                            }
                            new iframeWindow.Swiper(swiperElement, sliderConfig);
                        } catch (e) {
                            console.warn("Swiper initialization failed:", e);
                        }
                    }
                }
            }
        }

        if (wrapper) {
            wrapper.dispatchEvent(new CustomEvent("as-sb-reload", { bubbles: true }));
        }
    }
}
