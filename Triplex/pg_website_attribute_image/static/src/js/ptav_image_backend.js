/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ProductTemplateAttributeLine } from "@sale_product_configurator/js/product_template_attribute_line/product_template_attribute_line";

const TEMPLATE_XML = `
<templates xml:space="preserve">
    <t t-name="pgWebsiteAttributeImage.ptav-radio">
        <ul class="list-unstyled flex-grow-1 m-0">
            <li t-foreach="this.props.attribute_values" t-as="ptav" t-key="ptav.id"
                class="mb-2">
                <div class="form-check">
                    <label
                        class="form-check-label d-inline-flex align-items-center"
                        t-att-class="{ 'css_not_available': ptav.excluded }"
                        t-att-for="ptav.id">
                        <span t-out="ptav.name"/>
                        <BadgeExtraPrice
                            t-if="ptav.price_extra"
                            price="ptav.price_extra"
                            currencyId="this.env.currencyId"/>
                    </label>
                    <input
                        type="radio"
                        class="form-check-input"
                        t-att-id="ptav.id"
                        t-att-value="ptav.id"
                        t-att-checked="this.props.selected_attribute_value_ids.includes(ptav.id)"
                        t-att-name="'ptal-' + this.props.id"
                        t-on-change="updateSelectedPTAV"/>
                </div>
                <img class="attr_value_img" style="width: 100px;" t-if="ptav.image"
                    loading="lazy" decoding="async"
                    t-att-src="getImageUrl(ptav)"/>
            </li>
        </ul>
    </t>
</templates>
`;

registry.category("xml_templates").add(
    "pgWebsiteAttributeImage.ptav-radio",
    TEMPLATE_XML,
    { force: true }
);

const originalGetPTAVTemplate = ProductTemplateAttributeLine.prototype.getPTAVTemplate;
const ATTRIBUTE_VALUE_SHAPE = ProductTemplateAttributeLine.props?.attribute_values?.element?.shape;
if (ATTRIBUTE_VALUE_SHAPE) {
    ATTRIBUTE_VALUE_SHAPE.image_url = { type: String, optional: true };
}

patch(ProductTemplateAttributeLine.prototype, {
    getPTAVTemplate() {
        if (this.props.attribute.display_type === "radio") {
            return "pgWebsiteAttributeImage.ptav-radio";
        }
        return originalGetPTAVTemplate.call(this);
    },

    getImageUrl(ptav) {
        if (ptav?.image_url) {
            return ptav.image_url;
        }
        if (ptav?.image && ptav?.id) {
            return `/web/image/product.template.attribute.value/${ptav.id}/image?width=128&height=128`;
        }
        return "";
    },
});

