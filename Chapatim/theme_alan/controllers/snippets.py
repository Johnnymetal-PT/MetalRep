# -*- coding: utf-8 -*-

import ast
import random
from odoo import http, _
from odoo.http import request, route

class ThemeAlan(http.Controller):

    @http.route('/select/data/fetch', type='jsonrpc', auth='user', website=True)
    def select_data_fetch(self, terms='', searchIn='[]', **kwargs):
        """ Return data for Alan Search select fields."""

        results = []
        parent_category = kwargs.get('parent_category', 0)
        website_domain = request.website.website_domain()

        try:
            if searchIn:
                searchIn = ast.literal_eval(searchIn)

                for search in searchIn:
                    domain = website_domain + [('name','ilike',terms)]
                    if search == 'product.public.category' and parent_category:
                        domain += [('parent_id','=',int(parent_category))]
                    if search in ['product.template', 'blog.post']:
                        domain += [('is_published','=',True)]

                    limit = kwargs.get('limit', 10)

                    if search == 'product.attribute':
                        domain = [('name','ilike',terms)]

                    if search == 'product.ribbon':
                        domain = [('name','ilike',terms)]

                    records = request.env[search].search(domain, limit=limit)
                    for record in records:
                        image_field = 'image_256'
                        if search == 'blog.post':
                            image_field = 'author_avatar'
                        elif search == 'product.template' and not record.image_256:
                            if not record.image_1920:
                                image_url = None
                        image_url = request.website.image_url(record, image_field)
                        data = {
                            'id': record.id,
                            'name': record.display_name if hasattr(record, 'display_name') else record.name,
                            'model': search,
                            'image': image_url,
                            'extra': None
                        }

                        results.append(data)

        except Exception as e:
            request.env.cr.rollback()
            return {'error': str(e)}

        return results

    @http.route('/theme_alan/get_snippet_builder_preview', type='http', auth="user", website=True, sitemap=False)
    def get_snippet_builder_preview(self, **kw):
        """ Return snippet builder preview."""

        return request.env['ir.ui.view']._render_template('theme_alan.as_snippet_builder_preview')

    @route('/get_hotspot_product', auth='public', type='jsonrpc', website=True)
    def getHotSpotInfo(self, product_tmpl_id=0, style='st1'):
        """ Return hotspot product info."""
        product_id = request.env['product.template'].sudo().browse(int(product_tmpl_id))
        template = request.env['ir.ui.view']._render_template('theme_alan.as_img_hotspot_product_popover', {
            'product':product_id,
            'style':style,
        })
        return {'template':template}

    def getSliderConfiguration(self, config):
        """Return Swiper slider configuration based on editor settings."""

        slider_config = {
            'loop': config.get("loop"),
            'spaceBetween': 15,
            'slidesPerView': config.get("default_col_mob"),
            'navigation': {
                'nextEl': ".swiper-button-next",
                'prevEl': ".swiper-button-prev",
            },
            'breakpoints': {
                640:  {'slidesPerView': config.get("default_col_mob")},
                768:  {'slidesPerView': config.get("default_col_mob")},
                1024: {'slidesPerView': config.get("default_col_desk")},
                1200: {'slidesPerView': config.get("default_col_desk")},
            },
            'observer': True,
            'observeSlideChildren': True,
            'observeParents': True,
        }

        if config.get('auto_slider'):
                slider_config.update({
                    'autoplay': {
                        'delay': int(config.get('slider_time', 4)) * 1000
                    }
                })

        if config.get("pagination"):
            pagination_style = {}
            if config.get("pagination") == 'simple':
                pagination_style = {
                    'el': ".swiper-pagination"
                }
            elif config.get("pagination") == 'dynamic':
                pagination_style = {
                    'el': ".swiper-pagination",
                    'dynamicBullets': True,
                }
            elif config.get("pagination") == 'progress_bar':
                pagination_style = {
                    'el': ".swiper-pagination",
                    'type': "progressbar",
                }
            elif config.get("pagination") == 'fraction':
                pagination_style = {
                    'el': ".swiper-pagination",
                    'type': "fraction",
                }
            elif config.get("pagination") == 'scroll_bar':
                pagination_style = {
                    'el': ".swiper-scrollbar",
                    'hide': True,
                }
            elif config.get("pagination") == 'coverflow':
                pagination_style = {
                    'el': ".swiper-pagination",
                }
                slider_config.update({
                    "effect": "coverflow",
                    "grabCursor": True,
                    "centeredSlides": True,
                })
            elif config.get("pagination") == 'cards':
                slider_config.update({
                    "effect": "cards",
                    "grabCursor": True,
                    "centeredSlides": True,
                })
            if config.get("pagination") == 'scroll_bar':
                slider_config.update({'scrollbar':pagination_style })
            else:
                slider_config.update({'pagination':pagination_style })
        return slider_config

    def getCustomDomain(self, configuration):
        filters = configuration.get('filters', [])
        match_type = configuration.get("filter_match", "and")

        domain_list = []

        for f in filters:
            field = f.get("field")
            operator = f.get("operator")
            value = f.get("value")

            if not field or not operator:
                continue

            # ---------- Skip empty values except for set/not_set ----------
            if operator not in ['set', 'not_set']:
                if value == '' or value is None or (isinstance(value, list) and len(value) == 0):
                    continue

            # ---------- Handle set/not_set operators ----------
            if operator == "set":
                operator = "!="
                value = False
            elif operator == "not_set":
                operator = "="
                value = False

            # ---------- Handle "starts with" operator (=ilike) ----------
            elif operator == '=ilike':
                if isinstance(value, str):
                    value = value.strip()
                    operator = 'ilike'
                    value = f"{value}%"

            # ---------- Handle "contains" operator (ilike) ----------
            elif operator == 'ilike':
                if isinstance(value, str):
                    value = value.strip()
                    if not value.startswith('%') and not value.endswith('%'):
                        value = f"%{value}%"

            # ---------- Handle "not contains" operator (not ilike) ----------
            elif operator == 'not ilike':
                if isinstance(value, str):
                    value = value.strip()
                    if not value.startswith('%') and not value.endswith('%'):
                        value = f"%{value}%"

            # ---------- Handle comparison operators for price field (>, <, =) ----------
            elif field == 'list_price' and operator in ['>', '<', '=']:
                try:
                    if isinstance(value, str):
                        value = float(value)
                    elif isinstance(value, (int, float)):
                        value = float(value)
                    else:
                        continue
                except (ValueError, TypeError):
                    continue

            # ---------- Handle equals/not equals with dropdown selections (=, !=) ----------
            elif operator in ['=', '!=']:
                if isinstance(value, list) and len(value) > 0:
                    try:
                        id_list = [int(v) if isinstance(v, str) else v for v in value]
                    except (ValueError, TypeError):
                        continue

                    if operator == '=' and len(id_list) == 1:
                        operator = '='
                        value = id_list[0]
                    elif operator == '=':
                        operator = 'in'
                        value = id_list
                    elif operator == '!=' and len(id_list) == 1:
                        operator = '!='
                        value = id_list[0]
                    else:
                        operator = 'not in'
                        value = id_list

            domain_tuple = (field, operator, value)
            domain_list.append(domain_tuple)

        if match_type == "or" and len(domain_list) > 1:
            final_domain = []
            for dom in domain_list:
                if final_domain:
                    final_domain = ['|'] + final_domain + [dom]
                else:
                    final_domain = [dom]
            return final_domain
        else:
            return domain_list

    def getProductSpotlightSnippet(self, configuration, env_model, record_limit, website_domain):
        records_by_tab = {}
        website = request.website
        for tab in configuration.get('tab_names', []):
            tab_key = tab.get('key')
            products = env_model.browse()

            if tab_key == 'best_seller':
                products = env_model._get_best_seller_product(
                    from_date=182,
                    website_id=website.id,
                    limit=record_limit
                )

            elif tab_key == 'new_arrival':
                products = env_model.search(
                    website_domain,
                    limit=record_limit,
                    order="create_date DESC"
                )

            elif tab_key == 'on_sale':
                products = env_model._get_on_sale_products(
                    website_id=website.id,
                    limit=record_limit
                )

            records_by_tab[tab_key] = products

        return records_by_tab

    @route('/get_snippet_template', auth='public', type='jsonrpc', website=True)
    def getProductSnippets(self, **kw):
        """ Return rendered snippet template and optional slider configuration."""
        # ---------- BASIC INIT ----------
        configuration = kw.get('design_editor') or {}
        snippet_key = kw.get('snippet')
        model_name = kw.get('model')
        get_details = kw.get('get_details', False)

        # ---------- EARLY VALIDATION ----------
        if not snippet_key or not model_name:
            return {}

        # ---------- USER VISIBILITY CHECK (EARLY EXIT) ----------
        user_visibility = configuration.get("user_visibility", "all")
        if not get_details:
            is_public = request.env.user._is_public()
            if user_visibility == "login" and is_public:
                return {}
            if user_visibility == "public" and not is_public:
                return {}

        # ---------- INITIALIZATION ----------
        website = request.website
        ids = kw.get('record_ids') or []
        record_limit = configuration.get('record_limit', 5)
        active_view = configuration.get('active_view')
        selection = configuration.get('selection_mode_default')
        active_quick = configuration.get("active_quick_selction")

        context = {}
        result = {}
        env_model = request.env[model_name]

        # ---------- PRE-BUILD CACHED DOMAINS ----------
        base_domain = website.website_domain()
        if model_name in ('product.template', 'product.product'):
            website_domain = base_domain + [('is_published', '=', True)]
        elif model_name == 'product.public.category':
            website_domain = base_domain + [('parent_id', '=', False)]
        else:
            website_domain = base_domain

        # ---------- RECORD FETCH ----------
        records = env_model.browse()

        if ids == [0] and selection != 'custom_rules':
            return result

        if (not ids and selection != 'custom_rules') or snippet_key == 'product_spotlight':
            if snippet_key == 'product_spotlight':
                records_by_tab = self.getProductSpotlightSnippet(configuration, env_model, record_limit, website_domain)
                context.update({
                    'tab_records': records_by_tab,
                    'tab_names': configuration.get('tab_names', [])
                })
                records = env_model.search([] + website_domain,limit=record_limit, order="create_date DESC")
            else:
                if snippet_key in ['brand_collection_showcase']:
                    record_limit = 6

                records = env_model.search(website_domain, limit=record_limit, order="create_date DESC")
                if snippet_key in ['BrandProduct', 'brand_products', 'CategoryProduct', 'categories_products', 'brand_collection_showcase']:
                    context.update({'tab_ids': records})

        elif selection == 'custom_rules' or configuration.get("active_selection"):
            custom_domain = self.getCustomDomain(configuration)
            full_domain = website_domain + custom_domain
            order = "create_date DESC"

            # ---------- Quick Selection Handlers ----------
            if active_quick == "best_seller" and snippet_key in ("products", "BestSellingProduct", "ProductBanner", "ProductSlider", "product_banner"):
                bs_records = env_model._get_best_seller_product(182, website.id, limit=record_limit * 2)
                bs_filtered = bs_records.filtered_domain(custom_domain) if custom_domain else bs_records
                records = bs_filtered[:record_limit]

            elif active_quick == "random":
                all_matching = env_model.search(full_domain, limit=record_limit * 3)
                if all_matching:
                    id_list = all_matching.ids
                    random.shuffle(id_list)
                    records = env_model.browse(id_list[:record_limit])
                else:
                    records = env_model.browse()

            elif snippet_key in ['BrandProduct', 'brand_products', 'brand_collection_showcase', 'CategoryProduct', 'categories_products']:
                records = env_model.browse(ids).exists()
                context.update({'tab_ids': records})

            else:
                order_map = {
                    "a_to_z": "name ASC",
                    "z_to_a": "name DESC",
                    "latest_product": "create_date DESC",
                    "top_related": "product_rating DESC",
                    "low_to_high": "list_price ASC",
                    "high_to_low": "list_price DESC",
                }
                order = order_map.get(active_quick, "create_date DESC")
                records = env_model.search(full_domain, limit=record_limit, order=order)

        elif ids:
            if snippet_key in ['BrandProduct', 'brand_products', 'brand_collection_showcase', 'CategoryProduct', 'categories_products']:
                records = env_model.browse(ids).exists()
                context.update({'tab_ids': records})
            elif snippet_key == 'product_spotlight':
                records_by_tab = self.getProductSpotlightSnippet(configuration, env_model, record_limit, website_domain)
                context.update({'tab_records': records_by_tab})
                records = env_model.browse()
            else:
                records = env_model.browse(ids).exists()

        result['record_ids'] = records.ids if records else []

        # ---------- SLIDER OR GRID CONFIGURATION ----------
        context.update({'records': records, 'configuration': configuration})

        if active_view != "slider":
            col_item = max(int(configuration.get('col_item') or 4), 1)
            context['col_item'] = int(12 / col_item)
        else:
            result["slider_config"] = self.getSliderConfiguration(configuration)

        # ---------- TEMPLATE RENDER ----------
        template_id = configuration.get('template_id')
        template_html = False


        if template_id:
            try:
                template_html = request.env['ir.ui.view']._render_template(template_id, context)
            except Exception as e:
                request.env.cr.rollback()

        result["template"] = template_html

        # ---------- RECORD DETAILS ----------
        if get_details and records:
            result['record_details'] = self.getDetailsInfos(records.ids, model_name)

        return result

    @route('/get_records_details', auth='public', type='jsonrpc', website=True)
    def getDetailsInfos(self, record_ids=[], model=False):
        """ Return details of records."""
        if record_ids and model:
            record_ids = [int(i) for i in record_ids]
            rec_info = request.env[model].browse(record_ids).exists()
            if model == 'blog.post':
                vals = []
                for rec in rec_info:
                    img = rec.cover_background
                    if img and "url" in img:
                        img = img.split('(')[1].split(')')[0].replace('"', '').replace("'", "")
                    else:
                        img = request.website.image_url(rec, 'author_avatar')

                    vals.append({
                        'id': rec.id,
                        'display_name': rec.display_name,
                        'name': rec.name,
                        'image': img
                    })
                return vals
            else:
                return [{'id': rec.id, 'display_name':rec.display_name,
                    'name':rec.name,
                    'image': request.website.image_url(rec,'image_1024') }
                    for rec in rec_info ]
        else:
            record_ids

    @route('/get/snippets_loader_gif', auth='public', type='jsonrpc', website=True)
    def getSnippetsLoader(self, **kw):
        """ Return snippets loader gif."""
        website = request.website
        gif_url = website.image_url(website, field='snippets_loader')
        return gif_url if website.snippets_loader else False

    def _normalize_ids(self, record_ids):
        if isinstance(record_ids, dict):
            return list(record_ids.values())
        return record_ids or []

    def _get_category_records(self, Category, section_conf, domain):
        record_ids = section_conf.get('record_ids')

        # ---------- MANUAL ----------
        if record_ids:
            return Category.browse(record_ids).exists()

        # ---------- AUTO ----------
        return Category.search(
            domain + [('parent_id', '=', False)],
            limit=section_conf.get('record_limit', 6),
            order='create_date DESC'
    )

    @route('/get_megamenu_snippet_template', auth='public', type='jsonrpc', website=True)
    def getMegamenuSnippets(self, **kw):
        """ Return megamenu snippet template."""
        # ---------- BASIC INIT ----------
        website = request.website
        configuration = kw.get('design_editor') or {}
        snippet_key = kw.get('snippet')
        model_name = kw.get('model')
        ids = kw.get('record_ids') or []
        record_limit = configuration.get('record_limit', 5)
        active_view = configuration.get('active_view')
        selection = configuration.get('selection_mode_default')
        col_item = int(configuration.get('col_item', 4))
        get_details = kw.get('get_details', False)
        context = {}
        result = {}

        # ---------- VALIDATION ----------
        if not snippet_key or not model_name:
            return result

        # ---------- DOMAIN CACHING (Build once, reuse) ----------
        base_domain = website.website_domain()

        # ---------- Pre-build common domain combinations ----------
        published_domain = base_domain + [('is_published', '=', True)]
        parent_false_domain = base_domain + [('parent_id', '=', False)]

        # ---------- Select appropriate domain for model ----------
        if model_name in ('product.template', 'product.product'):
            website_domain = published_domain
        elif model_name == 'product.public.category':
            website_domain = parent_false_domain
        else:
            website_domain = base_domain
        env_model = request.env[model_name]

        # ---------- RECORD FETCH ----------
        records = env_model.browse()
        if ids == [0] and selection != 'custom_rules':
             return result

        if ids:
            records = env_model.browse(ids).exists()
        elif not ids and selection != 'custom_rules':
            records = env_model.search([] + website_domain, limit=record_limit, order="create_date DESC")

        # ---------- DATA PROCESSING ----------
        if snippet_key in ['MegaMenuCategory', 'megamenu_category']:
            extra_info = configuration.get('extra_info')
            sub_data_by_id = {}
            if extra_info:
                all_child_ids = []
                for item in extra_info:
                    all_child_ids.extend([int(i) for i in item.get('childs', [])])

                all_children = env_model.browse(all_child_ids).exists() if all_child_ids else env_model.browse()
                child_map = {c.id: c for c in all_children}

                for item in extra_info:
                    p_id = int(item['parent'])
                    c_ids = [int(i) for i in item.get('childs', [])]
                    sub_data_by_id[p_id] = env_model.browse([cid for cid in c_ids if cid in child_map])

            data = {rec: sub_data_by_id.get(rec.id, env_model.browse()) for rec in records}

            result['record_ids'] = records.ids
            context.update({'data': data})

        elif snippet_key == "megamenu_shop_navigator":
            Category = request.env['product.public.category']
            Product = request.env['product.template']
            Brand = request.env['as.product.brand']
            sections = configuration.get('sections', {})
            default_mm_section = configuration.get('default_mm_section', {})

            # ---------- OPTIMIZED CATEGORIES (with batch sub-category fetch) ----------
            cat_conf = sections.get('category', {})
            sub_data_by_id = {}

            record_ids = self._normalize_ids(cat_conf.get('record_ids'))

            # ---------- MANUAL OR AUTO ----------
            if record_ids:
                categories = Category.browse(record_ids).exists()
            else:
                categories = Category.search(
                    base_domain + [('parent_id', '=', False)],
                    limit=cat_conf.get('record_limit', 6),
                    order='create_date DESC'
                )

            # ---------- BATCH FETCH SUB CATEGORIES (Eliminates N+1) ----------
            extra_info = cat_conf.get('extra_info', [])
            if extra_info:
                all_child_ids = []
                for item in extra_info:
                    all_child_ids.extend([int(i) for i in item.get('childs', [])])

                all_children = Category.browse(all_child_ids).exists() if all_child_ids else Category.browse()
                child_map = {c.id: c for c in all_children}

                # build map once
                extra_map = {
                    int(item['parent']): [int(i) for i in item.get('childs', [])]
                    for item in extra_info
                }

                # loop only categories (sequence safe)
                for cat in categories:
                    c_ids = extra_map.get(cat.id, [])
                    sub_data_by_id[cat] = Category.browse(
                        [cid for cid in c_ids if cid in child_map]
                    )
            else:
                if categories:
                    sub_cats_all = Category.search(
                        base_domain + [('parent_id', 'in', categories.ids)],
                        order='sequence ASC'
                    )
                    for cat in categories:
                        sub_data_by_id[cat] = sub_cats_all.filtered(lambda r: r.parent_id.id == cat.id)[:5]
                        child_ids = [child.id for child in sub_data_by_id[cat]]
                        if child_ids:
                            extra_info.append({
                                'parent': cat.id,
                                'childs': child_ids
                            })

            # ---------- OPTIMIZED PRODUCTS (Use cached domain) ----------
            prod_conf = sections.get('product', {})
            record_config = prod_conf.get('record_config', 'on_sale')
            prod_limit = prod_conf.get('record_limit', 3)

            # ---------- FETCH PRODUCTS ----------
            if record_config == 'on_sale':
                products = Product._get_on_sale_products(website_id=website.id, limit=prod_limit)
            elif record_config == 'new_arrival':
                products = Product.search(published_domain, limit=prod_limit, order='create_date DESC')
            elif record_config == 'best_seller':
                products = Product._get_best_seller_product(182, website.id, limit=prod_limit)
            else:
                products = Product.browse()
            if isinstance(products, list):
                products = Product.browse([p.id for p in products])

            # ---------- OPTIMIZED BRANDS (Use cached domain) ----------
            brand_conf = sections.get('brand', {})
            brand_ids = self._normalize_ids(brand_conf.get('record_ids'))

            if configuration.get('selection_mode_default') == 'manual' and brand_ids:
                brands = Brand.browse(brand_ids).exists().filtered('active')
            else:
                brands = Brand.search(base_domain, limit=brand_conf.get('record_limit', 6), order="create_date DESC")

            # ---------- CONTEXT UPDATE ----------

            context.update({
                'categories': sub_data_by_id,
                'products': products,
                'brands': brands,
                'record_config': record_config,
                'mm_style': configuration.get('mm_style'),
                'allow_link': configuration.get('allow_link', True),
            })

            if default_mm_section == "category":
                result['record_ids'] = categories.ids
            elif default_mm_section == "product":
                result['record_ids'] = products.ids
            elif default_mm_section == "brand":
                result['record_ids'] = brands.ids

            sections.setdefault('category', {})['record_ids'] = categories.ids
            sections.setdefault('product', {})['record_ids'] = products.ids
            sections.setdefault('brand', {})['record_ids'] = brands.ids
            sections.setdefault('category', {})['extra_info'] = extra_info
            result['sections'] = sections
            # ---------- SLIDER CONFIG FOR BRAND SWIPER ----------

        elif snippet_key == "megamenu_multi_category":
            Category = request.env['product.public.category']
            sub_data_by_id = {}

            sections = configuration.get('sections', {})
            category_1 = sections.get('category_1', {})
            category_2 = sections.get('category_2', {})
            category_3 = sections.get('category_3', {})
            category1_records = self._get_category_records(Category, category_1, base_domain)
            category2_records = self._get_category_records(Category, category_2, base_domain)
            category3_records = self._get_category_records(Category, category_3, base_domain)

            # ---------- BATCH FETCH SUB CATEGORIES (Eliminates N+1) ----------
            extra_info = category_2.get('extra_info', [])
            if extra_info:
                all_child_ids = []
                for item in extra_info:
                    all_child_ids.extend([int(i) for i in item.get('childs', [])])

                if all_child_ids:
                    all_children = Category.browse(all_child_ids).exists()
                    child_map = {c.id: c for c in all_children}

                    for item in extra_info:
                        p_id = int(item['parent'])
                        c_ids = [int(i) for i in item.get('childs', [])]
                        parent_cat = category2_records.filtered(lambda c: c.id == p_id)
                        if parent_cat:
                            sub_data_by_id[parent_cat[0]] = Category.browse([cid for cid in c_ids if cid in child_map])
            else:
                if category2_records:
                    sub_cats_all = Category.search(
                        base_domain + [('parent_id', 'in', category2_records.ids)],
                        order='sequence ASC'
                    )

                    for cat in category2_records:
                        sub_data_by_id[cat] = sub_cats_all.filtered(
                            lambda r: r.parent_id.id == cat.id
                        )[:5]

                        child_ids = [child.id for child in sub_data_by_id[cat]]
                        if child_ids:
                            extra_info.append({
                                'parent': cat.id,
                                'childs': child_ids
                            })
            context.update({
                'category_1': category1_records,
                'category_2': sub_data_by_id,
                'category_3': category3_records,
                'mm_style': configuration.get('mm_style'),
            })

            default_mm_section = configuration.get('default_mm_section', {})
            if default_mm_section == "category_1":
                result['record_ids'] = category1_records.ids
            elif default_mm_section == "category_2":
                result['record_ids'] = category2_records.ids
            elif default_mm_section == "category_3":
                result['record_ids'] = category3_records.ids

            # ---------- Update sections with record IDs ----------
            sections.setdefault('category_1', {})['record_ids'] = category1_records.ids
            sections.setdefault('category_2', {})['record_ids'] = category2_records.ids
            sections.setdefault('category_3', {})['record_ids'] = category3_records.ids
            sections.setdefault('category_2', {})['extra_info'] = extra_info
            result['sections'] = sections

        else:
            result['record_ids'] = records.ids
            context.update({'data': records})

        # ---------- SLIDER OR GRID ----------
        if active_view != "slider":
            style = configuration.get('grid_style', '')
            if col_item == 0:
                col_item = 4
            col_item = int(12 / col_item)

        else:
            style = configuration.get('slider_style', '')
            slider_config = {
                'slidesPerView': 1.5,
                'spaceBetween': 20,
                'pagination': {
                    'el': '.swiper-pagination',
                    'clickable': True,
                },
                'breakpoints': {
                    767: { 'slidesPerView': 2 },
                    1024: { 'slidesPerView': col_item },
                },
                'navigation': {
                    'nextEl': '.swiper-button-next',
                    'prevEl': '.swiper-button-prev',
                },
                'loop': configuration.get('loop', True),
            }
            if configuration.get('auto_slider', False):
                delay = int(configuration.get('slider_time', 4)) * 1000
                slider_config.update({'autoplay': {'delay': delay}})

            result["slider_config"] = slider_config

        context.update({'style': style,'col_item': col_item,'configuration': configuration})

        # ---------- TEMPLATE RENDER ----------
        template_id = configuration.get('template_id')
        template_html = False
        if template_id:
            try:
                template_html = request.env['ir.ui.view']._render_template(template_id, context)
            except Exception:
                request.env.cr.rollback()

        result["template"] = template_html

        # ---------- RECORD DETAILS ----------
        if get_details and records:
            result['record_details'] = self.getDetailsInfos(records.ids, model_name)
        return result

    @route('/tab/products', auth='public', type='jsonrpc', website=True)
    def tab_products(self, snippet_name, tab_id, **kw):
        """ Return products for tab."""
        tab_id = int(tab_id)
        configuration = kw.get('design_editor') or {}
        record_limit = configuration.get('record_limit', 10)
        domain = [('is_published', '=', True), ('sale_ok', '=', True)] + request.website.website_domain()
        if snippet_name == 'brand':
            products = request.env['product.template'].sudo().search([
                ('product_brand_id', '=', tab_id),
                ('is_published', '=', True),
                ('sale_ok', '=', True)
            ], limit=12)
            domain += [('product_brand_id', '=', tab_id)]
            main_class = 'as_brand_products'
        elif snippet_name == 'category':
            domain += [('public_categ_ids', 'in', tab_id)]
            main_class = 'as_category_products'
        else:
            main_class = ''
        products = request.env['product.template'].sudo().search(domain, limit=record_limit)
        context = {
            'products': products,
            'configuration': configuration,
            'website': request.website,
            'main_class': main_class,
        }
        if configuration.get('active_view') != 'slider':
            col_mob_size = configuration.get('default_col_mob')
            col_desk = int(configuration.get('default_col_desk') or 4)
            if col_desk == 5:
                col_size = 'five'
            else:
                col_size = int(12 / col_desk)
            context.update({
                'col_mob_size': col_mob_size,
                'col_size': col_size,
            })
        template_id = 'theme_alan.as_tab_product_inner'
        try:
            template_html = request.env['ir.ui.view']._render_template(template_id, context)
            return {'template': template_html}
        except Exception:
            request.env.cr.rollback()
            return {'template': False}


    @http.route('/save_collection', type='jsonrpc', auth='user', website=True)
    def save_collection(self, name, snippet_key, config_data, **kwargs):
        """Save a snippet configuration as a collection."""
        Collection = request.env['snippet.collection']
        collection = Collection.create({
            'name': name,
            'snippet_key': snippet_key,
            'config_data': config_data,
        })
        return {'id': collection.id, 'name': collection.name}

    @http.route('/get_collections', type='jsonrpc', auth='public', website=True)
    def get_collections(self, **kw):
        """Retrieve collections. If snippet_key is provided in kw, filter by it."""
        Collection = request.env['snippet.collection'].sudo()
        domain = [('active', '=', True)]
        snippet_key = kw.get('snippet_key')
        if snippet_key:
            domain.append(('snippet_key', '=', snippet_key))
        collections = Collection.search_read(
            domain,
            ['id', 'name', 'config_data', 'snippet_key']
        )
        return collections

    @http.route('/delete_collection', type='jsonrpc', auth='user', website=True)
    def delete_collection(self, collection_id, **kwargs):
        """Delete a snippet collection."""
        collection = request.env['snippet.collection'].browse(int(collection_id))
        if collection.exists():
            collection.unlink()
            return True
        return False
