# -*- coding: utf-8 -*-
"""
Home Page Demo: backend controller for generating full homepage HTML
from the 12-step wizard configuration.
"""

from odoo import http
from odoo.http import request, route


class HomePageDemoController(http.Controller):

    # ── Snippet key → template_id & model mapping ────────────────────────────
    SNIPPET_MAP = {
        "products": {
            "model": "product.template",
            "slider_template": "theme_alan.s_product_slider",
            "grid_template": "theme_alan.s_product_grid",
        },
        "highlighted_product_grid": {
            "model": "product.template",
            "grid_template": "theme_alan.s_product_highlighted_grid",
        },
        "categories": {
            "model": "product.public.category",
            "slider_template": "theme_alan.s_category_slider",
            "grid_template": "theme_alan.s_category_grid",
        },
        "brand_collection_showcase": {
            "model": "as.product.brand",
            "slider_template": "theme_alan.s_brand_collection_showcase_slider",
            "grid_template": "theme_alan.s_brand_collection_showcase_grid",
        },
        "product_spotlight": {
            "model": "product.template",
            "grid_template": "theme_alan.s_product_spotlight",
        },
        "blogs": {
            "model": "blog.post",
            "slider_template": "theme_alan.s_blog_slider",
            "grid_template": "theme_alan.s_blog_grid",
        },
        "brands": {
            "model": "as.product.brand",
            "slider_template": "theme_alan.s_brand_slider",
            "grid_template": "theme_alan.s_brand_grid",
        },
    }

    # ── Website builder template lookup  ─────────────────────────────────────
    BUILDER_TEMPLATE_MAP = {
        "e_slider":    "slider_temp{}",
        "e_features":  "feature_temp{}",
        "e_title_style": "title_{}",
        "e_banner":    "banner_temp{}",
    }

    @route('/theme_alan/get_homepage_demo_stats', type='jsonrpc', auth='user', website=True)
    def get_homepage_demo_stats(self, **kw):
        """
        Returns count of records for products, categories, blogs, and brands
        to raise warning validation if no records exist.
        """
        website = request.website
        domain = website.website_domain()

        product_count = request.env['product.template'].search_count(domain + [('is_published', '=', True)]) if 'product.template' in request.env else 0
        category_count = request.env['product.public.category'].search_count(domain + [('parent_id', '=', False)]) if 'product.public.category' in request.env else 0
        blog_count = request.env['blog.post'].search_count(domain) if 'blog.post' in request.env else 0
        brand_count = request.env['as.product.brand'].search_count(domain) if 'as.product.brand' in request.env else 0

        return {
            'product': product_count,
            'category': category_count,
            'blog': blog_count,
            'brand': brand_count,
        }

    @route('/theme_alan/generate_home_page_demo', type='jsonrpc', auth='user', website=True)

    def generate_home_page_demo(self, sections=None, **kw):
        """
        Receives the 12-step configuration from the wizard and returns
        the complete homepage HTML as a string.
        """
        if not sections:
            return {'error': 'No sections provided'}

        view = request.env['ir.ui.view']
        website = request.website
        website_domain = website.website_domain()
        html_parts = []

        for section in sections:
            try:
                section_html = self._render_section(section, view, website, website_domain)
                if section_html:
                    html_parts.append(section_html)
            except Exception as e:
                request.env.cr.rollback()
                # Skip failed section but continue
                continue

        if not html_parts:
            return {'error': 'No sections could be rendered'}

        return {'html': '\n'.join(html_parts)}

    def _render_section(self, section, view, website, website_domain):
        """Render a single step's section and return HTML string."""
        output_type = section.get('type', '')
        dynamic_key = section.get('dynamic_snippet')
        title_text = section.get('title_text', 'Section')
        view_mode = section.get('view', 'slider')
        record_limit = int(section.get('record_limit') or 5)
        record_ids = section.get('record_ids') or []
        quick_selection = section.get('quick_selection')
        template_num = section.get('template_num')
        template_category = section.get('template_category', '')

        parts = []

        # ── Website builder static template ─────────────────────────────────
        if output_type == 'website_builder':
            template_name = self._get_builder_template_name(template_category, template_num)
            if template_name:
                try:
                    html = view._render_template(template_name, {})
                    parts.append(html)
                except Exception:
                    pass

        # ── Composite: Title + Dynamic ───────────────────────────────────────
        elif output_type == 'title+dynamic':
            title_num = section.get('title_template_num') or 8
            title_name = f"theme_alan.title_{title_num}"
            try:
                title_html = view._render_template(title_name, {'title_text': title_text})
                parts.append(title_html)
            except Exception:
                # Fallback plain title
                parts.append(
                    f'<section class="as-section-title text-center py-4">'
                    f'<h2 class="as-title">{title_text}</h2>'
                    f'</section>'
                )

            if dynamic_key:
                dyn_html = self._render_dynamic_snippet(
                    dynamic_key, view, website, website_domain,
                    view_mode, record_limit, record_ids, quick_selection
                )
                if dyn_html:
                    parts.append(dyn_html)

        # ── Pure Dynamic ─────────────────────────────────────────────────────
        elif output_type == 'dynamic':
            if dynamic_key:
                dyn_html = self._render_dynamic_snippet(
                    dynamic_key, view, website, website_domain,
                    view_mode, record_limit, record_ids, quick_selection
                )
                if dyn_html:
                    parts.append(dyn_html)

        return '\n'.join(parts) if parts else ''

    def _get_builder_template_name(self, category, num):
        """Map website builder category + number → template XML id."""
        prefix_map = {
            'e_slider':      'theme_alan.slider_temp{}',
            'e_features':    'theme_alan.feature_temp{}',
            'e_title_style': 'theme_alan.title_{}',
            'e_banner':      'theme_alan.banner_temp{}',
            'e_about':       'theme_alan.about_temp{}',
            'e_cta':         'theme_alan.cta_temp{}',
            'e_category':    'theme_alan.category_temp{}',
            'e_collection':  'theme_alan.collection_temp{}',
        }
        tpl_fmt = prefix_map.get(category)
        if tpl_fmt and num:
            return tpl_fmt.format(int(num))
        return None

    def _render_dynamic_snippet(
        self, snippet_key, view, website, website_domain,
        view_mode, record_limit, record_ids, quick_selection
    ):
        """Fetch records and render the appropriate dynamic snippet template."""
        cfg = self.SNIPPET_MAP.get(snippet_key)
        if not cfg:
            return ''

        model_name = cfg['model']
        env_model = request.env[model_name]

        # ── Domain building ──────────────────────────────────────────────────
        if model_name in ('product.template', 'product.product'):
            domain = website_domain + [('is_published', '=', True)]
        elif model_name == 'product.public.category':
            domain = website_domain + [('parent_id', '=', False)]
        else:
            domain = website_domain

        # ── Record fetch ─────────────────────────────────────────────────────
        records = env_model.browse()
        context = {}

        if record_ids:
            records = env_model.browse([int(i) for i in record_ids]).exists()
            if snippet_key in ('brand_collection_showcase', 'brand_products',
                               'categories_products', 'brands'):
                context['tab_ids'] = records
        elif snippet_key == 'product_spotlight':
            records_by_tab = {}
            for tab_key in ('best_seller', 'new_arrival', 'on_sale'):
                if tab_key == 'best_seller':
                    products = env_model._get_best_seller_product(
                        from_date=182, website_id=website.id, limit=record_limit
                    )
                elif tab_key == 'new_arrival':
                    products = env_model.search(domain, limit=record_limit, order='create_date DESC')
                elif tab_key == 'on_sale':
                    products = env_model._get_on_sale_products(website_id=website.id, limit=record_limit)
                else:
                    products = env_model.browse()
                records_by_tab[tab_key] = products
            context['tab_records'] = records_by_tab
            context['tab_names'] = [
                {'key': 'best_seller', 'label': 'Best Seller', 'enabled': True},
                {'key': 'new_arrival', 'label': 'New Arrival', 'enabled': True},
                {'key': 'on_sale', 'label': 'On Sale', 'enabled': True},
            ]
            records = env_model.search(domain, limit=record_limit, order='create_date DESC')
        else:
            if quick_selection == 'best_seller' and 'product.template' == model_name:
                records = env_model._get_best_seller_product(
                    from_date=182, website_id=website.id, limit=record_limit
                )
                if isinstance(records, list):
                    records = env_model.browse([r.id for r in records])
            else:
                order_map = {
                    'a_to_z': 'name ASC', 'z_to_a': 'name DESC',
                    'latest_product': 'create_date DESC',
                    'low_to_high': 'list_price ASC', 'high_to_low': 'list_price DESC',
                }
                order = order_map.get(quick_selection, 'create_date DESC')
                records = env_model.search(domain, limit=record_limit, order=order)

            if snippet_key in ('brand_collection_showcase', 'brand_products',
                               'categories_products', 'brands'):
                context['tab_ids'] = records

        # ── Template selection ───────────────────────────────────────────────
        if view_mode == 'grid':
            template_id = cfg.get('grid_template')
        else:
            template_id = cfg.get('slider_template') or cfg.get('grid_template')

        if not template_id:
            return ''

        # ── Configuration dict (mirrors SnippetBuilderRegistries defaults) ───
        configuration = {
            'technical_name': snippet_key,
            'model': model_name,
            'active_view': view_mode,
            'record_limit': record_limit,
            'loop': True,
            'auto_slider': True,
            'slider_time': 6,
            'slide_one_item': True,
            'display_all_items': False,
            'pagination': 'none',
            'default_col_mob': 2,
            'default_col_desk': '5',
            'grid_style': 'as-grid-1',
            'slider_style': 'as-slider-1',
            'allow_add_to_cart': True,
            'allow_quick_view': True,
            'allow_wishlist': True,
            'allow_label': True,
            'allow_link': True,
            'allow_product_discount': True,
            'allow_color_variant': True,
            'template_id': template_id,
        }
        if snippet_key == 'product_spotlight':
            configuration['tab_names'] = context.get('tab_names', [])

        context.update({'records': records, 'configuration': configuration})

        try:
            html = view._render_template(template_id, context)
            return f'<section class="as-dynamic-section s-{snippet_key}">{html}</section>'
        except Exception:
            request.env.cr.rollback()
            return ''
