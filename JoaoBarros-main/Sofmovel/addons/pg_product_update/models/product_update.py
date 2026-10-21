import os
import re
import base64
import logging
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from odoo import models, fields, api
from datetime import datetime
import hashlib
from psycopg2.errors import SerializationFailure
try:
    import psutil
except ImportError:
    psutil = None
    
_logger = logging.getLogger(__name__)

class ProductUpdate(models.Model):
    _name = 'product.update'
    _description = 'Product Update'

    def upload_file(self, model, record_id, field_name, file_path):
        try:
            with open(file_path, 'rb') as file:
                file_data = base64.encodebytes(file.read()).decode()
            self.env[model].browse(record_id).write({field_name: file_data})
        except Exception as e:
            _logger.error(f"Error uploading file: {e} | {model} {record_id} {field_name} {file_path}")

    def get_full_category_name(self, category):
        if category.parent_id:
            return self.get_full_category_name(category.parent_id) + '/' + category.name
        else:
            return category.name

    def normalize_folder_name(self, folder_name):
        return re.sub(r'^\d+\.', '', folder_name).strip()

    def load_folder_tree(self, root_folder):
        for root, dirs, _ in os.walk(root_folder):
            for dir_name in dirs:
                yield {
                    'path': os.path.join(root, dir_name).replace("\\", "/"),
                    'changed_path': os.path.join(root, self.normalize_folder_name(dir_name)).replace("\\", "/"),
                }
                
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
        """Uploads images for a product or its variants."""
        variant_names = variant_names or []
        processed_images = set()
        main_image_uploaded = False

        _logger.info(f"Uploading images from folder: {folder_path} for {'main product' if is_main_product else 'variant'}")

        for root, _, files in os.walk(folder_path):
            for file in sorted(files):
                if file.lower() == 'thumbs.db':
                    continue

                image_path = os.path.join(root, file)
                try:
                    with open(image_path, 'rb') as image_file:
                        image_data = image_file.read()

                    # Resize large images
                    if len(image_data) > 50_000_000:
                        image_data = self.resize_image(image_data)

                    # Deduplicate images
                    image_hash = hashlib.sha256(image_data).hexdigest()
                    if image_hash in processed_images:
                        _logger.info(f"Skipping duplicate image: {image_path}")
                        continue
                    processed_images.add(image_hash)

                    image_encoded = base64.b64encode(image_data)

                    # Handle main product images
                    if is_main_product and 'IMAGENS' in root.upper() and not variant_names:
                        if not main_image_uploaded:
                            # First image is the thumbnail
                            product.write({'image_1920': image_encoded})
                            main_image_uploaded = True
                            _logger.info(f"Set first image as thumbnail: {file}")
                        else:
                            # Add remaining images as extra media
                            self.env['product.image'].create({
                                'product_tmpl_id': product.id,
                                'name': file,
                                'image_1920': image_encoded,
                                'sequence': 10,
                            })
                            _logger.info(f"Added extra media: {file}")
                    else:
                        # Handle variant images
                        variants = self.get_variants_by_attributes(product.id, variant_names)
                        if variants:
                            for variant in variants:
                                self.env['product.image'].create({
                                    'product_variant_id': variant.id,
                                    'name': file,
                                    'image_1920': image_encoded,
                                })
                                _logger.info(f"Added image to variant: {variant.name}")
                        else:
                            _logger.warning(f"No matching variants found for image: {image_path}")

                except UnidentifiedImageError as e:
                    _logger.warning(f"UnidentifiedImageError for file {image_path}: {e}")
                except Exception as e:
                    _logger.error(f"Error processing image {image_path}: {e}")


    def process_product(self, category_id, web_category_id, pos_category_id, product_path, product_folder_name, images_folder):
        product = self.env['product.template'].search([('default_code', '=', self.normalize_folder_name(product_folder_name))], limit=1)
        if not product:
            _logger.info(f'Product not found: {product_folder_name}')
            return

        try:
            product.categ_id = category_id
            product.public_categ_ids = [(4, web_category_id)]
            product.write({'pos_categ_ids': [(4, pos_category_id)]})
            product.is_published = True

            # Remove images and attachments in small batches
            attachments = self.env['ir.attachment'].search([('res_model', '=', 'product.template'), ('res_id', '=', product.id)])
            attachments.unlink()

            product_images = self.env['product.image'].search([('product_tmpl_id', '=', product.id)])
            product_images.unlink()

            for variant in product.product_variant_ids:
                variant_images = self.env['product.image'].search([('product_variant_id', '=', variant.id)])
                variant_images.unlink()

            self.upload_images(images_folder, product, is_main_product=True)
            self.process_additional_content(product, product_path)

        except Exception as e:
            _logger.error(f"Error processing product {product.default_code}: {e}")

    def process_additional_content(self, product, product_path):
        for folder, _, files in os.walk(product_path):
            for file in files:
                if 'IMAGENS' in folder.upper() or file.lower() == 'thumbs.db':
                    continue

                try:
                    attachment_path = os.path.join(folder, file)
                    attachment_name = os.path.relpath(attachment_path, product_path).replace(os.sep, ' » ')

                    with open(attachment_path, 'rb') as f:
                        file_data = base64.b64encode(f.read())

                    self.env['product.document'].create({
                        'name': attachment_name,
                        'datas': file_data,
                        'res_id': product.id,
                        'res_model': 'product.template',
                        'active': True,
                        'shown_on_product_page': True,
                    })

                except Exception as e:
                    _logger.error(f"Error processing additional content for {product.name}: {e}")

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
                                    _logger.warning(f"Attribute value {variant_name} found, 	but no matching variant.")
        except Exception as e:
            _logger.error(f"Error processing COMPLEMENTOS images: {e}")
            self.env.cr.rollback()

    @api.model
    def update_products(self):
        """Main method to update products with retry logic and email notifications."""
        retry_count = 5

        for attempt in range(retry_count):
            try:
                all_category = self.create_or_get_category('All', None)
                all_web_category = self.create_or_get_web_category('Todas')

                root_folder = r"/ProgGest/Odoo/Clientes/SofMovel/1.PRODUTOS"
                if not os.path.exists(root_folder):
                    _logger.error(f"Root folder does not exist: {root_folder}")
                    return  # No email needed since the process didn't run

                self.log_memory_usage("Start of update_products")
                self.process_folders_iteratively(root_folder, all_category, all_web_category)
                self.log_memory_usage("End of update_products")

                _logger.info(f"Product update completed at {datetime.now()}")
                self.send_email_notification()  # Send email on success
                break  # Exit loop if successful

            except SerializationFailure as e:
                if attempt < retry_count - 1:
                    _logger.warning(f"Serialization failure on attempt {attempt + 1}. Retrying...")
                else:
                    _logger.error(f"Maximum retries reached: {str(e)}")
                    raise e  # Let the exception propagate after all retries

    def send_email_notification(self):
        """Send email using template ID 79."""
        try:
            template = self.env['mail.template'].browse(79)  # Fetch by numeric ID
            if template and template.exists():
                template.send_mail(self.id, force_send=True)
                _logger.info("Email sent successfully using template ID 79.")
            else:
                _logger.error("Email template with ID 79 not found.")
        except Exception as e:
            _logger.error(f"Error sending email notification: {e}")

    def process_folders_iteratively(self, root_folder, parent_category, web_category):
        """Process folders iteratively to avoid recursion depth issues."""
        stack = [(root_folder, parent_category, web_category, None)]
        while stack:
            current_path, parent_cat, web_cat, pos_cat = stack.pop()
            _logger.info(f"Processing folder: {current_path}")

            for folder_name in os.listdir(current_path):
                folder_path = os.path.join(current_path, folder_name)
                if os.path.isdir(folder_path):
                    _logger.info(f"Found subfolder: {folder_name}")
                    folder_with_images = self.find_images_folder(folder_path)

                    if folder_with_images:
                        _logger.info(f"Processing images in folder: {folder_with_images}")
                        self.process_product(
                            parent_cat.id, web_cat.id, 
                            pos_cat.id if pos_cat else None, 
                            folder_path, folder_name, folder_with_images
                        )
                        complementos_folder = self.find_complementos_folder(folder_path)
                        if complementos_folder:
                            _logger.info(f"Processing COMPLEMENTOS folder: {complementos_folder}")
                            self.process_complementos_folder(complementos_folder, parent_cat.id)
                    else:
                        normalized_name = self.normalize_folder_name(folder_name)
                        contains_noncateg = any(
                            keyword.upper() in normalized_name.upper()
                            for keyword in ['3D', 'FICHA', 'CERTIFICADO']
                        )

                        if not contains_noncateg:
                            category = self.create_or_get_category(normalized_name, parent_cat.id)
                            web_category = self.create_or_get_web_category(normalized_name, web_cat.id)
                            pos_category = self.env['pos.category'].search(
                                [('name', '=', normalized_name)], limit=1
                            )
                            if not pos_category:
                                pos_category = self.env['pos.category'].create({'name': normalized_name})
                        else:
                            category, web_category, pos_category = parent_cat, web_cat, pos_cat

                        stack.append((folder_path, category, web_category, pos_category))

    def find_images_folder(self, folder_path):
        """Find the IMAGENS folder within a given path."""
        return next(
            (os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if os.path.isdir(os.path.join(folder_path, f)) and 'IMAGENS' in f.upper()),
            None
        )

    def find_complementos_folder(self, folder_path):
        """Find the COMPLEMENTOS folder within a given path."""
        return next(
            (os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if os.path.isdir(os.path.join(folder_path, f)) and 'COMPLEMENTOS' in f.upper()),
            None
        )

    def log_memory_usage(self, message=""):
        if psutil:
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert bytes to MB
            _logger.info(f"[Memory Usage] {message}: {memory_usage:.2f} MB")
        else:
            _logger.warning("psutil is not installed; skipping memory logging.")
          

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_product_data(self):
        self.env['product.update'].update_products()

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
