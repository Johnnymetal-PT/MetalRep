import { registry } from '@web/core/registry';

const websiteBuilderRegistry = registry.category("website_builder");

const snippetCategories = Object.freeze({
    e_slider: "Slider",
    e_banner: "Banner",
    e_about: "About",
    e_title_style: "Title Style",
    e_cta: "Call To Action",
    e_category: "Category",
    e_our_client: "Our Client",
    e_collection: "Collection",
    e_contact_us: "Contact Us",
    e_features: "Features",
    e_our_team: "Our Team",
    e_portfolio: "Portfolio",
    e_price_table: "Price Table",
    e_promotion: "Promotion",
    e_services: "Services",
    e_shop_banner: "Shop Banner",
    e_testimonial: "Testimonial",
    e_video_popup: "Video Popup",
    e_subscribe_newsletter: "Subscribe Newsletter",
});

// Register custom snippet categories
websiteBuilderRegistry.add("as_snippet_categories", snippetCategories);