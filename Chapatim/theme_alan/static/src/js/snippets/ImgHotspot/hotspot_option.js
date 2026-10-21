import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";

// ─── Alan Image Hotspot Option Component ───────────────────────────────────
export class AlanImageHotspotOption extends BaseOptionComponent {
    static template = "theme_alan.ImageHotspotOption";
    static selector = ".hs_icon";
    static exclude = ".s_category img, .s_brand img";
    setup() {
        super.setup();
        this.state = useDomState((editingElement) => ({
            hasStaticType: this.hasStaticType(editingElement),
        }));
    }

    hasStaticType(editingElement) {
        if (!editingElement) {
            return false;
        }
        const classList = editingElement ? Array.from(editingElement.classList) : []
        return classList.includes("static_type");
    }
}
