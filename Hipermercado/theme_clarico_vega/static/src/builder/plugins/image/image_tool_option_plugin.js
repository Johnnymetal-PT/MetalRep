/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Plugin } from "@html_editor/plugin";
import { BuilderAction } from "@html_builder/core/builder_action";
import { BaseOptionComponent } from "@html_builder/core/utils";

const HOTSPOT_ACTION_CLASSES = ["redirect_url", "redirect_product", "display_card", "display_adv_card"];
const HOTSPOT_SHAPE_CLASSES = ["circle", "square", "drop"];
const HOTSPOT_ANIMATION_CLASSES = ["fade_hotspot", "blink"];
const HOTSPOT_THEME_CLASSES = ["light_theme", "dark_theme"];
const HOTSPOT_DRAG_BOUND = new WeakSet();

export class HotspotToolOption extends BaseOptionComponent {
    static template = "theme_clarico_vega.HotspotToolOption";
    static selector = ".hotspot_element";
    static name = "hotspotToolOption";
}

function getHotspotImage(container) {
    if (!container) return null;
    return container.querySelector("img.img_hotspot_setting") || container.querySelector("img");
}

function resolveHotspotImage(editingElement) {
    if (!editingElement) return null;
    if (editingElement.tagName === "IMG") return editingElement;
    const figure = editingElement.closest?.("figure");
    const container = figure?.parentElement || editingElement.parentElement;
    return getHotspotImage(container);
}

function enableDrag(el) {
    if (!el) {
        return;
    }
    const doc = el.ownerDocument || document;
    if (!doc?.body) {
        return;
    }
    el.classList.add("oe_unmovable");
    el.setAttribute("contenteditable", "false");
    el.style.userSelect = "none";
    const parent = el.parentElement;
    if (parent && getComputedStyle(parent).position === "static") {
        parent.style.position = "relative";
    }
    if (HOTSPOT_DRAG_BOUND.has(el)) {
        return;
    }
    HOTSPOT_DRAG_BOUND.add(el);

    // Avoid conflicts with native drag and old inline transforms.
    el.style.transform = "";
    el.setAttribute("draggable", "false");
    el.addEventListener("dragstart", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
    });
    const dot = el.querySelector(".hotspot_dot");
    if (dot) {
        dot.setAttribute("draggable", "false");
        dot.setAttribute("contenteditable", "false");
        dot.style.userSelect = "none";
        dot.addEventListener("dragstart", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
        });
    }

    const DRAG_THRESHOLD = 3;
    const onPointerDown = (ev) => {
        if (ev.button !== undefined && ev.button !== 0) {
            return;
        }
        const parent = el.parentElement;
        if (!parent) return;

        const parentRect = parent.getBoundingClientRect();
        const startX = ev.clientX;
        const startY = ev.clientY;
        const startLeft = el.offsetLeft;
        const startTop = el.offsetTop;
        let dragging = false;

        const move = (e) => {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            if (!dragging) {
                if (Math.abs(dx) + Math.abs(dy) < DRAG_THRESHOLD) {
                    return;
                }
                dragging = true;
                ev.stopPropagation();
                if (el.setPointerCapture && e.pointerId !== undefined) {
                    try { el.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
                }
            }
            let x = Math.min(Math.max(0, startLeft + dx), parentRect.width);
            let y = Math.min(Math.max(0, startTop + dy), parentRect.height);
            el.style.left = `${(x / parentRect.width) * 100}%`;
            el.style.top = `${(y / parentRect.height) * 100}%`;
        };

        const stop = (e) => {
            doc.removeEventListener("pointermove", move, true);
            doc.removeEventListener("pointerup", stop, true);
            doc.removeEventListener("pointercancel", stop, true);
            if (dragging) {
                e.preventDefault();
                e.stopPropagation();
            }
        };

        doc.addEventListener("pointermove", move, true);
        doc.addEventListener("pointerup", stop, true);
        doc.addEventListener("pointercancel", stop, true);
    };

    el.addEventListener("pointerdown", onPointerDown, true);
}

function getHotspotsForImage(img) {
    if (!img) return [];
    const scope = img.closest(".o_editable") || img.parentElement;
    if (!scope) return [];
    const uid = ensureHotspotUid(img);
    let hotspots = Array.from(
        scope.querySelectorAll(`.hotspot_element[data-hotspot-for="${uid}"]`)
    );
    if (!hotspots.length) {
        const parent = img.parentElement;
        hotspots = parent ? Array.from(parent.querySelectorAll(".hotspot_element")) : [];
    }
    return hotspots;
}

function hasHotspots(editingElement) {
    if (!editingElement) return false;
    if (editingElement.classList?.contains("hotspot_element")) {
        return true;
    }
    if (editingElement.closest?.(".hotspot_element")) {
        return true;
    }
    const img = resolveHotspotImage(editingElement);
    return img ? getHotspotsForImage(img).length > 0 : false;
}

function getHotspot(editingElement) {
    if (!editingElement) return null;
    if (editingElement.classList?.contains("hotspot_element")) {
        return editingElement;
    }
    const closestHotspot = editingElement.closest?.(".hotspot_element");
    if (closestHotspot) {
        return closestHotspot;
    }
    return null;
}

function getHotspotDot(hotspot) {
    return hotspot?.querySelector(".hotspot_dot");
}

function ensureHotspotUid(img) {
    if (!img) return null;
    if (!img.dataset.hotspotUid) {
        img.dataset.hotspotUid = `hs_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    }
    return img.dataset.hotspotUid;
}

function linkHotspotToImage(hotspot, img) {
    if (!hotspot || !img) return;
    hotspot.dataset.hotspotFor = ensureHotspotUid(img);
}

function getHotspotLink(hotspot) {
    return getHotspotDot(hotspot)?.closest("a") || hotspot?.querySelector("a");
}

function getHotspotProductId(hotspot) {
    const raw = hotspot?.dataset?.productTemplateIds || hotspot?.getAttribute("data-product-template-ids");
    const id = parseInt(raw || "", 10);
    return Number.isNaN(id) ? null : id;
}

function ensureHotspotLink(hotspot) {
    const dot = getHotspotDot(hotspot);
    if (!dot) return null;

    let link = dot.closest("a");
    if (!link) {
        link = document.createElement("a");
        link.className = "btn border-0 hotspot_link";
        dot.replaceWith(link);
        link.appendChild(dot);
    } else if (!link.classList.contains("hotspot_link")) {
        link.classList.add("hotspot_link");
    }
    return link;
}

function removeHotspotLink(hotspot) {
    const link = getHotspotLink(hotspot);
    if (!link) return;

    const dot = link.querySelector(".hotspot_dot");
    if (dot) {
        link.replaceWith(dot);
    } else {
        link.remove();
    }
}

function normalizeUrl(url) {
    if (!url) return "";
    if (url.startsWith("/") || url.startsWith("#") || /^([a-zA-Z]*.):.+$/gm.test(url)) {
        return url;
    }
    return `http://${url}`;
}

function setHotspotProductLink(hotspot, productId) {
    if (!productId) return;
    const link = ensureHotspotLink(hotspot);
    if (link) {
        link.setAttribute("href", `/shop/product/${productId}`);
    }
}

function setHotspotDataId(hotspot, productId) {
    if (!productId) return;
    hotspot.dataset.id = productId;
}

function createHotspot() {
    const hotspot = document.createElement("section");
    hotspot.className =
        "hotspot_draggable hotspot_element oe_unmovable o_not_editable s_col_no_resize s_col_no_bgcolor fade_hotspot circle";
    hotspot.setAttribute("contenteditable", "false");
    hotspot.setAttribute("name", "Hotspot-Block");
    hotspot.setAttribute("data-exclude", ".s_col_no_resize, .s_col_no_bgcolor");
    hotspot.style.cssText = `
        position: absolute;
        left: 50%;
        top: 50%;
        cursor: grab;
        pointer-events: auto;
        z-index: 99999;
    `;

    const icon = document.createElement("span");
    icon.className = "hotspot_dot fa fa-shopping-bag o_editable_media";
    icon.setAttribute("draggable", "false");
    icon.setAttribute("contenteditable", "false");

    hotspot.appendChild(icon);
    return hotspot;
}

class HotspotPlugin extends Plugin {
    static id = "HotspotPlugin";

    resources = {
        builder_actions: {
            onHotspot: EnableHotspot,
            offHotspot: RemoveHotspot,
            hotspotAction: SetHotspotAction,
            hotspotSetUrl: SetURL,
            hotspotNewWindow: SetNewWindow,
            hotspotProduct: SetHotspotProduct,
            hotspotShape: SetHotspotShape,
            hotspotAnimation: SetHotspotAnimation,
            hotspotTheme: SetHotspotTheme,
        },
        builder_options: [HotspotToolOption],
        trigger_dom_updated: this.bindExistingHotspots.bind(this),
    };

    setup() {
        if (!this.editable) return;
        this.bindExistingHotspots();
    }

    bindExistingHotspots(rootEl = this.editable) {
        if (!rootEl) return;
        rootEl.querySelectorAll(".hotspot_element").forEach((hotspot) => {
            const parent = hotspot.parentElement;
            const img = getHotspotImage(parent);
            if (img) {
                linkHotspotToImage(hotspot, img);
            }
            enableDrag(hotspot);
        });
    }
}

class EnableHotspot extends BuilderAction {
    static id = "onHotspot";

    isApplied({ editingElement }) {
        return hasHotspots(editingElement);
    }

    async apply({ editingElement }) {
        const img = resolveHotspotImage(editingElement);
        const parent = img?.parentElement || editingElement.parentElement;
        if (!parent || !img) return;

        if (getComputedStyle(parent).position === "static") {
            parent.style.position = "relative";
        }

        const hotspot = createHotspot();
        parent.appendChild(hotspot);
        linkHotspotToImage(hotspot, img);
        enableDrag(hotspot);
    }
}

class RemoveHotspot extends BuilderAction {
    static id = "offHotspot";

    isApplied({ editingElement }) {
        return !hasHotspots(editingElement);
    }

    async apply({ editingElement }) {
        const img = resolveHotspotImage(editingElement);
        const parent = img?.parentElement || editingElement.parentElement;
        if (!parent) return;
        const uid = img?.dataset?.hotspotUid;
        let hotspots = Array.from(
            parent.querySelectorAll(
                uid ? `.hotspot_element[data-hotspot-for="${uid}"]` : ".hotspot_element"
            )
        );
        if (!hotspots.length && uid) {
            hotspots = Array.from(parent.querySelectorAll(".hotspot_element"));
        }
        hotspots.forEach((el) => el.remove());
    }
}

export class SetHotspotAction extends BuilderAction {
    static id = "hotspotAction";

    isApplied({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) {
            return !value;
        }
        if (!value) {
            return HOTSPOT_ACTION_CLASSES.every((cls) => !hotspot.classList.contains(cls));
        }
        return hotspot.classList.contains(value);
    }

    async apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_ACTION_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
        hotspot.classList.remove("quick-view-a");

        if (value) {
            hotspot.classList.add(value);
            if (value === "display_adv_card") {
                hotspot.classList.add("quick-view-a");
            }
        }

        if (value === "redirect_url" || value === "redirect_product") {
            const productId = getHotspotProductId(hotspot);
            const link = ensureHotspotLink(hotspot);
            if (value === "redirect_product" && link && productId) {
                setHotspotProductLink(hotspot, productId);
            }
        } else {
            removeHotspotLink(hotspot);
        }

        if (value === "display_adv_card") {
            const productId = getHotspotProductId(hotspot);
            if (productId) {
                setHotspotDataId(hotspot, productId);
            }
        } else {
            hotspot.removeAttribute("data-id");
        }
    }
}

export class SetURL extends BuilderAction {
    static id = "hotspotSetUrl";

    setup() {
        this.preview = false;
    }

    apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        const link = ensureHotspotLink(hotspot);
        if (!link) return;

        let url = normalizeUrl(value);
        if (!url) {
            link.removeAttribute("href");
            return;
        }
        link.setAttribute("href", url);
    }

    getValue({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        const link = getHotspotLink(hotspot);
        return link?.getAttribute("href") || "";
    }
}

export class SetNewWindow extends BuilderAction {
    static id = "hotspotNewWindow";

    setup() {
        this.preview = false;
    }
    apply({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        const link = hotspot ? ensureHotspotLink(hotspot) : null;
        if (link) {
            link.setAttribute("target", "_blank");
        }
    }
    clean({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        const link = getHotspotLink(hotspot);
        if (link) {
            link.removeAttribute("target");
        }
    }
    isApplied({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        const link = getHotspotLink(hotspot);
        return link?.getAttribute("target") === "_blank";
    }
}

export class SetHotspotProduct extends BuilderAction {
    static id = "hotspotProduct";

    apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        const parsed = value ? JSON.parse(value) : {};
        const id = parsed.id ? parseInt(parsed.id, 10) : null;

        if (id) {
            hotspot.dataset.productTemplateIds = id;
            if (hotspot.classList.contains("redirect_product")) {
                setHotspotProductLink(hotspot, id);
            }
            if (hotspot.classList.contains("display_adv_card")) {
                setHotspotDataId(hotspot, id);
            }
        }
    }

    clean({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        delete hotspot.dataset.productTemplateIds;
        hotspot.removeAttribute("data-product-template-ids");
        if (hotspot.classList.contains("display_adv_card")) {
            hotspot.removeAttribute("data-id");
        }
        const link = getHotspotLink(hotspot);
        if (link) {
            link.removeAttribute("href");
        }
    }

    getValue({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        const id = hotspot?.dataset?.productTemplateIds;
        if (id) {
            return JSON.stringify({ id: parseInt(id, 10) });
        }
    }
}

export class SetHotspotShape extends BuilderAction {
    static id = "hotspotShape";

    isApplied({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        return hotspot ? hotspot.classList.contains(value) : false;
    }

    apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_SHAPE_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
        if (value) {
            hotspot.classList.add(value);
        }
    }

    clean({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_SHAPE_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
    }
}

export class SetHotspotAnimation extends BuilderAction {
    static id = "hotspotAnimation";

    isApplied({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        return hotspot ? hotspot.classList.contains(value) : false;
    }

    apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_ANIMATION_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
        if (value) {
            hotspot.classList.add(value);
        }
    }

    clean({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_ANIMATION_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
    }
}

export class SetHotspotTheme extends BuilderAction {
    static id = "hotspotTheme";

    isApplied({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        return hotspot ? hotspot.classList.contains(value) : false;
    }

    apply({ editingElement, value }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_THEME_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
        if (value) {
            hotspot.classList.add(value);
        }
    }

    clean({ editingElement }) {
        const hotspot = getHotspot(editingElement);
        if (!hotspot) return;

        HOTSPOT_THEME_CLASSES.forEach((cls) => hotspot.classList.remove(cls));
    }
}

registry.category("builder-plugins").add(HotspotPlugin.id, HotspotPlugin);
