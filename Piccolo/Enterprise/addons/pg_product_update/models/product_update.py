import os
import re
import base64
import logging
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from odoo import models, fields, api
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProductUpdate(models.Model):
    _name = 'product.update'
    _description = 'Product Update'

    def upload_file(self, model, record_id, field_name, file_path):
        with open(file_path, 'rb') as file:
            file_data = base64.b64encode(file.read())
        try:
            self.env[model].browse(record_id).write({field_name: file_data})
        except Exception as e:
            _logger.info(f"Error uploading file: {e}{model} {record_id} {field_name} {file_path}")

    def get_full_category_name(self, category):
        if category.parent_id:
            return self.get_full_category_name(category.parent_id) + '/' + category.name
        else:
            return category.name

    def normalize_folder_name(self, folder_name):
        return re.sub(r'^\d+\.', '', folder_name).strip()

    def load_folder_tree(self, root_folder):
        folder_tree = []
        for root, dirs, _ in os.walk(root_folder):
            for dir_name in dirs:
                original_path = os.path.join(root, dir_name).replace("\\", "/")
                normalized_path = os.path.join(root, self.normalize_folder_name(dir_name)).replace("\\", "/")
                folder_tree.append({
                    'path': original_path,
                    'changed_path': normalized_path
                })
        return folder_tree

    def find_category_folder(self, category_folder, folder_tree):
        normalized_category_folder = category_folder
        for folder in folder_tree:
            if normalized_category_folder in folder['changed_path']:
                return folder['path']
        return None

    def create_or_get_category(self, name, parent_id=None, img_path=None):
        category = self.env['product.category'].search([('name', '=', name), ('parent_id', '=', parent_id)], limit=1)
        if not category:
            category = self.env['product.category'].create({'name': name, 'parent_id': parent_id})

            if parent_id:
                parent_category = self.env['product.category'].browse(parent_id)
                if parent_category.name.upper() == "ALL" and img_path:
                    # Upload images if path is provided
                    image_files = [f for f in os.listdir(img_path) if os.path.isfile(os.path.join(img_path, f))]
                    image_files.sort()  # Sort to ensure consistent order

                    vals = {}
                    if len(image_files) > 0:
                        with open(os.path.join(img_path, image_files[0]), 'rb') as image_file:
                            vals['cat_image_1'] = base64.b64encode(image_file.read())
                    if len(image_files) > 1:
                        with open(os.path.join(img_path, image_files[1]), 'rb') as image_file:
                            vals['cat_image_2'] = base64.b64encode(image_file.read())
                    if vals:
                        category.write(vals)

        return category

    def create_or_get_web_category(self, category_name, parent_id=None):
        web_category = self.env['product.public.category'].search([('name', '=', category_name), ('parent_id', '=', parent_id)], limit=1)
        if not web_category:
            web_category = self.env['product.public.category'].create({'name': category_name, 'parent_id': parent_id})
        return web_category

    @api.model
    def add_categoria_attribute_to_product(self, product_id, variant_name):
        contains_variant_info = any(
            keyword.upper() in variant_name.upper() for keyword in ['3D', 'FICHA', 'CERTIFICADO'])

        if not contains_variant_info:
            # Fetch the product template
            product_template = self.env['product.template'].browse(product_id)

            if not product_template.exists():
                _logger.info(f'Product template with ID {product_id} does not exist')
                return

            # Search for the existing attribute values
            attribute_value = self.env['product.attribute.value'].search([('name', '=', variant_name)], limit=1)

            # Skip if the attribute value does not exist
            if not attribute_value:
                _logger.info(f'Attribute value {variant_name} does not exist')
                return

            categoria_attribute = attribute_value.attribute_id

            # Check if the attribute line already exists for the product
            attribute_line = self.env['product.template.attribute.line'].search([
                ('product_tmpl_id', '=', product_template.id),
                ('attribute_id', '=', categoria_attribute.id)
            ], limit=1)

            if not attribute_line:
                # Create the attribute line and add it to the product template
                attribute_line = self.env['product.template.attribute.line'].create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': categoria_attribute.id,
                    'value_ids': [(6, 0, [attribute_value.id])]
                })
            else:
                # Add the variant value to the existing attribute line if it's not already added
                if attribute_value.id not in attribute_line.value_ids.ids:
                    attribute_line.write({
                        'value_ids': [(4, attribute_value.id)]
                    })

            return product_template

        return None

    def get_variants_from_path(self, path):
        """
        Helper method to extract variant names from the relative image path.
        Assumes that each folder level represents an attribute value.
        """
        parts = path.split(os.sep)
        if len(parts) > 1:
            return parts[:-1]  # Exclude the file name part
        return []

    def get_variants_by_attributes(self, product_template_id, variant_names):
        """
        Helper method to find the product variants that match the given attribute values.
        """
        domain = [('product_tmpl_id', '=', product_template_id)]
        for variant_name in variant_names:
            domain.append(('product_template_attribute_value_ids.name', '=', variant_name))
        return self.env['product.product'].search(domain)


    def resize_image(self, image_data, max_width=1920, max_height=1920):
        """
        Resize an image to fit within a maximum width and height.
        """
        image = Image.open(BytesIO(image_data))
        image.thumbnail((max_width, max_height), Image.ANTIALIAS)
        output = BytesIO()
        
        # Convert RGBA to RGB before saving as JPEG
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        image.save(output, format='JPEG')
        return output.getvalue()

    def upload_images(self, folder_path, product, is_main_product=True, variant_names=None):
        if variant_names is None:
            variant_names = []
        main_image_uploaded = False
        processed_images = set()

        _logger.info(f"Uploading images from folder: {folder_path} for {'main product' if is_main_product else 'variant'}")

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower() != 'thumbs.db':
                    image_path = os.path.join(root, file)
                    relative_path = os.path.relpath(image_path, folder_path)
                    current_variant_names = self.get_variants_from_path(relative_path)

                    _logger.info(f"Processing image: {image_path}, variant names: {current_variant_names}")

                    with open(image_path, 'rb') as image_file:
                        image_data = image_file.read()

                    try:
                        image = Image.open(BytesIO(image_data))
                        if image.size[0] * image.size[1] > 50_000_000:
                            image_data = self.resize_image(image_data)

                        image_encoded = base64.b64encode(image_data)
                        image_hash = base64.b64encode(image_data)  # Use entire image data for hash

                        if (image_hash, tuple(current_variant_names)) in processed_images:
                            _logger.info(f"Skipping duplicate image: {image_path} with variants: {current_variant_names}")
                            continue

                        processed_images.add((image_hash, tuple(current_variant_names)))

                        if is_main_product and 'IMAGENS' in root.upper() and len(current_variant_names) == 0:
                            # Handle main product images
                            if not main_image_uploaded:
                                self.env['product.template'].browse(product.id).write({'image_1920': image_encoded})
                                main_image_uploaded = True
                            else:
                                self.env['product.image'].create({
                                    'product_tmpl_id': product.id,
                                    'name': file,
                                    'image_1920': image_encoded,
                                    'sequence': 1,
                                })
                        elif not is_main_product or (is_main_product and current_variant_names):
                            # Handle variant images
                            variants = self.get_variants_by_attributes(product.id, current_variant_names)
                            if variants:
                                for variant in variants:
                                    _logger.info(f"Uploading image to variant: {variant.name}")
                                    self.env['product.image'].create({
                                        'product_variant_id': variant.id,
                                        'name': file,
                                        'image_1920': image_encoded,
                                    })
                            else:
                                _logger.info(f"No matching variants found for image: {image_path}, uploading as extra media")
                                # Upload as extra media if no matching variants found
                                if not main_image_uploaded and is_main_product:
                                    self.env['product.image'].create({
                                        'product_tmpl_id': product.id,
                                        'name': file,
                                        'image_1920': image_encoded,
                                        'sequence': 1,
                                    })
                                    main_image_uploaded = True

                    except UnidentifiedImageError as e:
                        _logger.warning(f"UnidentifiedImageError for file {image_path}: {e}")
                    except Exception as e:
                        _logger.error(f"Error processing image {image_path}: {e}")

    def process_product(self, category_id, web_category_id, product_path, product_name, images_folder):
        _logger.info(f'Processing product: {product_name.upper()}')
        if '(PRODUTO)' in product_name.upper():
            _logger.info(f'Skipping folder marked as product placeholder: {product_name}')
            return

        product = self.env['product.template'].search([('name', '=', self.normalize_folder_name(product_name))], limit=1)
        if not product:
            _logger.info(f'Product not found: {product_name}')
            return

        product.write({
            'categ_id': category_id,
            'public_categ_ids': [(6, 0, [web_category_id])],
            'is_published': True,
        })

        _logger.info(f'Found product: {product.name}')

        # Remove all attachments and extra images from the main product
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', product.id),
        ])
        attachments.unlink()

        product_images = self.env['product.image'].search([('product_tmpl_id', '=', product.id)])
        product_images.unlink()

        # Remove images from variants
        for variant in product.product_variant_ids:
            variant_images = self.env['product.image'].search([('product_variant_id', '=', variant.id)])
            variant_images.unlink()

        # Upload images for main product
        if os.path.exists(images_folder):
            self.upload_images(images_folder, product, is_main_product=True)

        # Upload attachments and variant images
        self.process_additional_content(product, product_path)

    def process_additional_content(self, product, product_path):
        """
        Process additional content such as documents and variant images.
        """
        for folder, _, files in os.walk(product_path):
            for file in files:
                try:
                    if file.lower() != 'thumbs.db' and 'IMAGENS' not in folder.upper():
                        attachment_path = os.path.join(folder, file)
                        attachment_name = re.sub(r'[\\/]', ' » ', folder.replace(product_path, '') + ' » ' + file)
                        self.env['product.document'].create({
                            'name': attachment_name[3:],
                            'datas': base64.b64encode(open(attachment_path, 'rb').read()),
                            'res_id': product.id,
                            'res_model': 'product.template',
                            'active': True,
                            'shown_on_product_page': True,
                        })
                except Exception as X:
                    _logger.error(f'Error creating attachment for {product.name}: {X}')

            # Process attributes and upload variant images
            if 'IMAGENS' not in folder.upper():
                contains_variant_info = any(
                    keyword.upper() in folder.upper() for keyword in ['3D', 'FICHA', 'CERTIFICADO'])
                if contains_variant_info:
                    for subfolder in next(os.walk(folder))[1]:
                        subfolder_path = os.path.join(folder, subfolder)
                        if 'IMAGENS' not in subfolder_path.upper():
                            variant_name = os.path.basename(subfolder_path)
                            _logger.info(f"Processing variant: {variant_name} in subfolder: {subfolder_path}")
                            self.add_categoria_attribute_to_product(product.id, variant_name)
                            variant_images_folder = os.path.join(os.path.dirname(subfolder_path), 'IMAGENS', variant_name)
                            if os.path.exists(variant_images_folder):
                                self.upload_images(variant_images_folder, product, is_main_product=False, variant_names=[variant_name])

    def process_complementos_folder(self, complementos_folder, category_id):
        """
        Processes the COMPLEMENTOS folder, updating the corresponding products
        with images and linking them as accessories to the main product.
        """
        main_product_name = os.path.basename(os.path.dirname(complementos_folder))
        main_product_name_normalized = self.normalize_folder_name(main_product_name)
        main_product = self.env['product.template'].search([('name', '=', main_product_name_normalized)], limit=1)

        if not main_product:
            _logger.info(f'Main product not found for COMPLEMENTOS folder: {complementos_folder}')
            return

        for folder_name in os.listdir(complementos_folder):
            product_path = os.path.join(complementos_folder, folder_name)
            if os.path.isdir(product_path):
                product_name = self.normalize_folder_name(folder_name)
                _logger.info(f'Processing COMPLEMENTOS product: {product_name.upper()}')

                product_template = self.env['product.template'].search([('name', '=', product_name)], limit=1)
                if not product_template:
                    _logger.info(f'COMPLEMENTOS product not found: {product_name}')
                    continue

                # Clear existing images for the product
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'product.template'),
                    ('res_id', '=', product_template.id),
                ])
                attachments.unlink()

                product_images = self.env['product.image'].search([('product_tmpl_id', '=', product_template.id)])
                product_images.unlink()

                # Remove images from variants
                for variant in product_template.product_variant_ids:
                    variant_images = self.env['product.image'].search([('product_variant_id', '=', variant.id)])
                    variant_images.unlink()

                # Process images within the COMPLEMENTOS product
                self.process_complementos_images(product_template, product_path)

                # Link the COMPLEMENTOS product variants to the main product as accessories
                for variant in product_template.product_variant_ids:
                    main_product.write({'accessory_product_ids': [(4, variant.id)]})

    def process_complementos_images(self, product_template, product_path):
        try:
            for folder_name in os.listdir(product_path):
                normalized_folder_name = self.normalize_folder_name(folder_name)
                _logger.info(f"Checking folder: {folder_name}, normalized to: {normalized_folder_name}")
                if normalized_folder_name.upper() == 'IMAGENS':
                    images_folder = os.path.join(product_path, folder_name)
                    _logger.info(f"Processing main images in: {images_folder}")
                    self.upload_images(images_folder, product_template, is_main_product=True)

                    for variant_folder in os.listdir(images_folder):
                        variant_folder_path = os.path.join(images_folder, variant_folder)
                        if os.path.isdir(variant_folder_path):
                            variant_name = self.normalize_folder_name(variant_folder)
                            _logger.info(f"Found variant folder: {variant_folder}, normalized to: {variant_name}")

                            self.add_categoria_attribute_to_product(product_template.id, variant_name)

                            variants = self.get_variants_by_attributes(product_template.id, [variant_name])
                            if variants:
                                for variant in variants:
                                    _logger.info(f"Uploading images to variant: {variant.name}")
                                    self.upload_images(variant_folder_path, variant, is_main_product=False, variant_names=[variant_name])
                            else:
                                _logger.info(f"No matching variants found for: {variant_name}.")
                                # Additional logging for no match found
                                attribute_values = self.env['product.attribute.value'].search([('name', '=', variant_name)])
                                if not attribute_values:
                                    _logger.warning(f"Attribute value {variant_name} not found in the database.")
                                else:
                                    _logger.warning(f"Attribute value {variant_name} found, but no matching variant.")
        except Exception as e:
            _logger.error(f"Error processing COMPLEMENTOS images: {e}")
            self.env.cr.rollback()

    @api.model
    def update_products(self):
        all_category = self.create_or_get_category('All', None, None)
        all_web_category = self.create_or_get_web_category('Todas')

        root_folder = r"\\192.168.5.5\partilha geral\1.PRODUTOS"
        #root_folder = r"C:\1.PRODUTOS_2"
        if not os.path.exists(root_folder):
            _logger.error(f"Root folder does not exist: {root_folder}")
            return

        folder_tree = self.load_folder_tree(root_folder)
        _logger.info(f"Loaded folder tree")

        def process_folders(current_path, parent_category, web_category):
            for folder_name in os.listdir(current_path):
                folder_path = os.path.join(current_path, folder_name)
                if os.path.isdir(folder_path):
                    folder_with_images = next(
                        (os.path.join(folder_path, f) for f in os.listdir(folder_path)
                        if os.path.isdir(os.path.join(folder_path, f)) and 'IMAGENS' in f.upper()),
                        None
                    )

                    if folder_with_images:
                        # Process the main product images
                        self.process_product(parent_category.id, web_category.id, folder_path, folder_name, folder_with_images)
                        
                        # Check for "COMPLEMENTOS" folder in the same root
                        complementos_folder = next(
                            (os.path.join(folder_path, f) for f in os.listdir(folder_path)
                            if os.path.isdir(os.path.join(folder_path, f)) and 'COMPLEMENTOS' in f.upper()),
                            None
                        )

                        if complementos_folder:
                            # Process the "COMPLEMENTOS" folder separately
                            self.process_complementos_folder(complementos_folder, parent_category.id)
                        continue

                    normalized_folder_name = self.normalize_folder_name(folder_name)

                    contains_noncateg = any(
                        keyword.upper() in normalized_folder_name.upper() for keyword in ['3D', 'FICHA', 'CERTIFICADO'])

                    if not contains_noncateg:
                        category = self.create_or_get_category(normalized_folder_name, parent_category.id, folder_path)
                        webcategory = self.create_or_get_web_category(normalized_folder_name, web_category.id)
                    else:
                        category = parent_category
                        webcategory = web_category

                    process_folders(folder_path, category, webcategory)

        process_folders(root_folder, all_category, all_web_category)

        current_datetime = datetime.now()
        date_made = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        _logger.info(f"Product update completed: {date_made}")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_product_data(self):
        self.env['product.update'].update_products()

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
