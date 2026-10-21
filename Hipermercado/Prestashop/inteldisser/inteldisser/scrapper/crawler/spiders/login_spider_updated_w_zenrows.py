import scrapy
import requests
from dotenv import load_dotenv
import os
from crawler.helper import parse_code_gama, parse_energy_class, parse_stock_qty, verify_price_format_and_return_original
from crawler.items import ProductDetailsItem # Ensure this is correctly imported
from scrapy_playwright.page import PageMethod

# Load environment variables from .env
load_dotenv()
username_credentials = os.getenv("USERNAME_CREDENTIALS")
password_credentials = os.getenv("PASSWORD_CREDENTIALS")
login_url = os.getenv("LOGIN_URL")
allowed_domain = os.getenv("ALLOWED_DOMAIN", "b2b.eldisser.com")  # Default to the actual domain if not set
start_url_after_login = os.getenv("START_URL") # Renamed for clarity
client_code_value = os.getenv("CLIENT_CODE_VALUE", "007063") # Get client code from .env, default if not set
image_url = os.getenv("IMAGE_URL") # Unused in current snippet, keep if needed elsewhere
extra_information_url = os.getenv("EXTRA_INFORMATION_URL")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY") # Your ZenRows API Key

if not ZENROWS_API_KEY:
    raise ValueError("ZENROWS_API_KEY not found in environment variables. Please set it in your .env file.")

ZENROWS_WS_URL = f"wss://browser.zenrows.com?apikey={ZENROWS_API_KEY}"
busqueda_data_first_page_template = "datosformulario[0][name]=filtroPromo&datosformulario[0][value]=0&datosformulario[1][name]=AlmacenAsociado&datosformulario[1][value]=0&datosformulario[2][name]=customerno&datosformulario[2][value]={client_code}&datosformulario[3][name]=keynav&datosformulario[3][value]=pageNumber&datosformulario[4][name]=Ofertas&datosformulario[4][value]=0&datosformulario[5][name]=OfertaDegisa&datosformulario[5][value]=0&datosformulario[6][name]=orderbyfield&datosformulario[6][value]=&datosformulario[7][name]=orderbytype&datosformulario[7][value]=&datosformulario[8][name]=NAVEGADOR&datosformulario[8][value]=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36&datosformulario[9][name]=PLATAFORMA&datosformulario[9][value]=MacIntel&datosformulario[10][name]=RESOLUCION&datosformulario[10][value]=Alto: 857 x Ancho: 1512&datosformulario[11][name]=ANCHOPANTALLA&datosformulario[11][value]=1512&datosformulario[12][name]=Es_OFE_FOLLET&datosformulario[12][value]=0&datosformulario[13][name]=OfertaTodos&datosformulario[13][value]=0&datosformulario[14][name]=ES_Promociones&datosformulario[14][value]=0&datosformulario[15][name]=FILTRO_ATRIBUTOS&datosformulario[15][value]=&datosformulario[16][name]=cantidadDisponibleTemporalAnyadirProducto&datosformulario[16][value]=&datosformulario[17][name]=descatalogadoDisponibleTemporalAnyadirProducto&datosformulario[17][value]=&datosformulario[18][name]=ispost&datosformulario[18][value]=1&datosformulario[19][name]=Blocked_Hidden_eq_Filter&datosformulario[19][value]=0&datosformulario[20][name]=Blocked_Hidden_eq_Filter_12&datosformulario[20][value]=12&datosformulario[21][name]=No_Text_eq_Filter&datosformulario[21][value]=&datosformulario[22][name]=_x003C_Cód_gama_x003E__Text_eq_Filter&datosformulario[22][value]=&datosformulario[23][name]=_x003C_Cód_gama_x003E__Text_eq_Filter_5&datosformulario[23][value]=5&datosformulario[24][name]=Product_Group_Code_Text_eq_Filter&datosformulario[24][value]=&datosformulario[25][name]=Product_Group_Code_Text_eq_Filter_6&datosformulario[25][value]=6&datosformulario[26][name]=Subfamilia_Text_eq_Filter&datosformulario[26][value]=&datosformulario[27][name]=Subfamilia_Text_eq_Filter_7&datosformulario[27][value]=7&datosformulario[28][name]=comentarios_1&datosformulario[28][value]=&datosformulario[29][name]=Tipo_Oferta_Hidden&datosformulario[29][value]=&datosformulario[30][name]=Tipo_Oferta_Select&datosformulario[30][value]=&datosformulario[31][name]=mostrarExclusivos&datosformulario[31][value]=0&datosformulario[32][name]=Mostrar_Competitividad_Hidden&datosformulario[32][value]=1&datosformulario[33][name]=Mostrar_Competitividad_Select&datosformulario[33][value]=1&datosformulario[34][name]=Mostrar_Stock_Hidden&datosformulario[34][value]=2&datosformulario[35][name]=Ordenar_Filter&datosformulario[35][value]=5&datosformulario[36][name]=Ordenar_Filter_Hidden&datosformulario[36][value]=Relevancia&datosformulario[37][name]=VistaCalendario&datosformulario[37][value]=0&datosformulario[38][name]=centroLogisticoCercano&datosformulario[38][value]=0&datosformulario[39][name]=attributos_gama&datosformulario[39][value]=&datosformulario[40][name]=attributos_familia&datosformulario[40][value]=&codigos=&codigosOferta=&valorescheckbox=preescompra_vt,0#mostrarpvp,0#mostrarpvp-encabezado-fijo,0"
busqueda_data_next_page_template = "datosformulario[0][name]=filtroPromo&datosformulario[0][value]=0&datosformulario[1][name]=AlmacenAsociado&datosformulario[1][value]=0&datosformulario[2][name]=customerno&datosformulario[2][value]={client_code}&datosformulario[3][name]=keynav&datosformulario[3][value]=pageNumber&datosformulario[4][name]=Ofertas&datosformulario[4][value]=0&datosformulario[5][name]=OfertaDegisa&datosformulario[5][value]=0&datosformulario[6][name]=orderbyfield&datosformulario[6][value]=&datosformulario[7][name]=orderbytype&datosformulario[7][value]=&datosformulario[8][name]=NAVEGADOR&datosformulario[8][value]=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36&datosformulario[9][name]=PLATAFORMA&datosformulario[9][value]=MacIntel&datosformulario[10][name]=RESOLUCION&datosformulario[10][value]=Alto: 857 x Ancho: 1512&datosformulario[11][name]=ANCHOPANTALLA&datosformulario[11][value]=1512&datosformulario[12][name]=Es_OFE_FOLLET&datosformulario[12][value]=0&datosformulario[13][name]=OfertaTodos&datosformulario[13][value]=0&datosformulario[14][name]=ES_Promociones&datosformulario[14][value]=0&datosformulario[15][name]=FILTRO_ATRIBUTOS&datosformulario[15][value]=&datosformulario[16][name]=cantidadDisponibleTemporalAnyadirProducto&datosformulario[16][value]=&datosformulario[17][name]=descatalogadoDisponibleTemporalAnyadirProducto&datosformulario[17][value]=&datosformulario[18][name]=ispost&datosformulario[18][value]=1&datosformulario[19][name]=Blocked_Hidden_eq_Filter&datosformulario[19][value]=0&datosformulario[20][name]=Blocked_Hidden_eq_Filter_12&datosformulario[20][value]=12&datosformulario[21][name]=No_Text_eq_Filter&datosformulario[21][value]=&datosformulario[22][name]=_x003C_Cód_gama_x003E__Text_eq_Filter&datosformulario[22][value]=&datosformulario[23][name]=_x003C_Cód_gama_x003E__Text_eq_Filter_5&datosformulario[23][value]=5&datosformulario[24][name]=Product_Group_Code_Text_eq_Filter&datosformulario[24][value]=&datosformulario[25][name]=Product_Group_Code_Text_eq_Filter_6&datosformulario[25][value]=6&datosformulario[26][name]=Subfamilia_Text_eq_Filter&datosformulario[26][value]=&datosformulario[27][name]=Subfamilia_Text_eq_Filter_7&datosformulario[27][value]=7&datosformulario[28][name]=comentarios_1&datosformulario[28][value]=&datosformulario[29][name]=Tipo_Oferta_Hidden&datosformulario[29][value]=&datosformulario[30][name]=Tipo_Oferta_Select&datosformulario[30][value]=&datosformulario[31][name]=mostrarExclusivos&datosformulario[31][value]=0&datosformulario[32][name]=Mostrar_Competitividad_Hidden&datosformulario[32][value]=1&datosformulario[33][name]=Mostrar_Competitividad_Select&datosformulario[33][value]=1&datosformulario[34][name]=Mostrar_Stock_Hidden&datosformulario[34][value]=2&datosformulario[35][name]=Mostrar_Stock_Hidden&datosformulario[35][value]=2&datosformulario[36][name]=Mostrar_Stock_Select&datosformulario[36][value]=2&datosformulario[37][name]=Ordenar_Filter&datosformulario[37][value]=5&datosformulario[38][name]=Ordenar_Filter_Hidden&datosformulario[38][value]=Relevancia&datosformulario[39][name]=VistaCalendario&datosformulario[39][value]=0&datosformulario[40][name]=centroLogisticoCercano&datosformulario[40][value]=0&datosformulario[41][name]=attributos_gama&datosformulario[41][value]=&datosformulario[42][name]=attributos_familia&datosformulario[42][value]=&codigos=&codigosOferta=&valorescheckbox=preescompra_vt,0#mostrarpvp,0#mostrarpvp-encabezado-fijo,0"

# Form data for product details
details_data_template = "codProductoDetalle=detailId&codClienteDetalle={client_code}&ocultarPVD=0&AlmacenAsociadoDetalle=0&NAVEGADORITEM=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%3B+rv%3A121.0%29+Gecko%2F20100101+Firefox%2F121.0&PLATAFORMAITEM=Win32&RESOLUCIONITEM=Alto%3A+1307+x+Ancho%3A+2560"

# Common Playwright arguments for ZenRows
playwright_meta_for_zenrows = {
    "playwright": True,
    "playwright_include_page": True,
    "playwright_connect_kwargs": {
        "ws_endpoint": ZENROWS_WS_URL
    },
    "playwright_page_methods": [
        PageMethod("route", "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,eot}", lambda route: route.abort()),
        # Add other common methods if any, like waiting for network idle for a short period
        # PageMethod("wait_for_load_state", "domcontentloaded"), # Or "networkidle" with a timeout
    ]
}

class HipermercadosSpider(scrapy.Spider):
    name = "spider-hipermercados-updated-zenrows"
    allowed_domains = [allowed_domain] if allowed_domain else [] # Ensure allowed_domain is not None
    # start_url is now effectively login_url for the first step
    # start_urls is not strictly needed if start_requests is defined

    def __init__(self, *args, **kwargs):
        super(HipermercadosSpider, self).__init__(*args, **kwargs)
        self.pending_requests = 0
        self.current_page = int(kwargs.get('start_page', 1))
        self.client_code_value = client_code_value # Store for later use
        self.logger.info(f"Spider initialized. Client code: {self.client_code_value}, User: {username_credentials}")
        self.logger.info(f"Allowed domains: {self.allowed_domains}")  # Debug: show what domains are allowed
        if not login_url:
            self.logger.error("LOGIN_URL is not set in environment variables!")
            raise ValueError("LOGIN_URL is required.")
        if not username_credentials or not password_credentials:
            self.logger.error("USERNAME_CREDENTIALS or PASSWORD_CREDENTIALS are not set!")
            raise ValueError("Login credentials are required.")

    def start_requests(self):
        self.logger.info(f"Attempting login via ZenRows to: {login_url}")
        # Form data for login
        formdata = {
            "ReturnUrl": "/",
            "dominio": "ELDISSER.NAV",
            "login": username_credentials,
            "password": password_credentials,
        }

        # Create meta for the login request with more robust page handling
        login_meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_connect_kwargs": {
                "ws_endpoint": ZENROWS_WS_URL
            },
            "playwright_page_methods": [
                PageMethod("wait_for_load_state", "domcontentloaded"),
                PageMethod("wait_for_selector", "input[type='text']", timeout=30000),
                PageMethod("fill", "input[type='text']", username_credentials),
                PageMethod("fill", "input[type='password']", password_credentials),
                PageMethod("click", "input[type='submit']"),
                PageMethod("wait_for_load_state", "networkidle", timeout=30000),
            ],
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 30000
            }
        }
        try:
            request = scrapy.FormRequest(
                start_url_after_login,
                method='POST',
                formdata=formdata,
                meta=login_meta,
                callback=self.after_login,
                errback=self.errback_login,
                dont_filter=True
            )
            self.logger.info("Login FormRequest created successfully")
            yield request
            self.logger.info("Login FormRequest yielded")
        except Exception as e:
            print("Error in Login FormRequest")
            print("e",e)
            self.logger.error(f"Failed to create/yield login FormRequest: {str(e)}", exc_info=True)
            raise

    async def errback_login(self, failure):
        print("Inside Errback Login")
        print("failure",failure)
        self.logger.error(f"Login failed. Failure: {repr(failure)}")
        # You might want to call the generic errback or handle differently
        await self.errback(failure)


    def after_login(self, response):
        page = response.meta.get("playwright_page")
        self.logger.info(f"After login attempt. URL: {response.url}, Page URL via Playwright: {page.url if page else 'N/A'}")

        # Check if we're still on the login page
        if login_url and login_url in (page.url if page else ""):
            self.logger.error("Still on login page after login attempt. Login may have failed.")
            return

        # Add detailed logging for debugging the 404 issue
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Response URL: {response.url}")
        if response.status != 200:
            self.logger.error(f"Response status: {response.status}")
            self.logger.error(f"Response URL: {response.url}")
            self.logger.error(f"Response headers: {dict(response.headers) if hasattr(response, 'headers') else 'N/A'}")
            # Log a snippet of the response body
            response_text_snippet = response.text[:1000] if hasattr(response, 'text') else str(response.body)[:1000]
            self.logger.error(f"Response body (first 1000 chars): {response_text_snippet}")
            self.logger.error(f"=== END DEBUG INFO ===")
            return

        print("Login successful. Starting product scraping.")
        self.logger.info("Login successful. Starting product scraping.")

        # Now start scraping the actual product pages
        form_data_str = busqueda_data_first_page_template.format(client_code=self.client_code_value)
        form_data_dict = {}
        for item in form_data_str.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                form_data_dict[key] = value
        form_data_dict['datosformulario[3][value]'] = str(self.current_page)
        # Meta for the first product listing page request
        product_page_meta = {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_connect_kwargs": {
                "ws_endpoint": ZENROWS_WS_URL
            },
            "playwright_page_methods": [
                PageMethod("wait_for_load_state", "networkidle", timeout=30000),
                PageMethod("wait_for_selector", ".resultados", timeout=30000),  # Wait for product results
            ],
            "page": self.current_page
        }
        if not start_url_after_login:
            self.logger.error("START_URL (start_url_after_login) is not set for post-login navigation!")
            return
        
        request_after_login = scrapy.FormRequest(
            start_url_after_login,
            method='POST',
            formdata=form_data_dict,
            meta=product_page_meta,
            callback=self.parse_page,
            errback=self.errback,
        )
        print("After FormRequest")
        print(f"FormRequest response status: {request_after_login.status if hasattr(request_after_login, 'status') else 'N/A'}")
        print(f"FormRequest response URL: {request_after_login.url if hasattr(request_after_login, 'url') else 'N/A'}")
        yield request_after_login
        
    def parse_page(self, response):
        print("Inside Parse Page")
        page_num = response.meta.get('page')
        self.logger.info(f"[Page {page_num}] START parse_page. URL: {response.url}, Status: {response.status}")
        playwright_page_instance = response.meta.get("playwright_page")

        self.logger.info(f"[Page {page_num}] Response status: {response.status}")
        self.logger.info(f"[Page {page_num}] Response URL: {response.url}")
        
        # Log page content length and first 500 chars
        page_content = response.text if hasattr(response, 'text') else str(response.body)
        self.logger.info(f"[Page {page_num}] Page content length: {len(page_content)}")
        self.logger.info(f"[Page {page_num}] Page content (first 500 chars): {page_content[:500]}")
        
        # Check if we're on the right page
        if "login" in response.url.lower():
            self.logger.error(f"[Page {page_num}] Still on login page! Login failed.")
            return
        
        # Check for common error indicators - be very specific to avoid false positives
        page_content_lower = page_content.lower()
        is_error_page = False
        
        # Only consider it an error page if we see specific error patterns
        if any(pattern in page_content_lower for pattern in [
            "404 not found",
            "page not found", 
            "error 404",
            "not found",
            "the page you are looking for",
            "this page doesn't exist",
            "page cannot be found"
        ]):
            is_error_page = True
        # Or if it's a very short page (likely an error)
        elif len(page_content) < 1000:
            is_error_page = True
            
        if is_error_page:
            self.logger.error(f"[Page {page_num}] Error page detected in content")
            return

        try:
            if playwright_page_instance and playwright_page_instance.is_closed():
                self.logger.error(f"[Page {page_num}] Playwright page was ALREADY CLOSED at the start of parse_page. Aborting.")
                return

            # Debug the product selector
            product_blocks = response.css('.resultados .bloque-producto-tienda')
            self.logger.info(f"[Page {page_num}] Found {len(product_blocks)} product blocks.")
            
            # Try alternative selectors if the main one fails
            if not product_blocks:
                self.logger.warning(f"[Page {page_num}] No products found with '.resultados .bloque-producto-tienda'")
                # Try alternative selectors
                alt_selectors = [
                    '.resultados .producto',
                    '.producto',
                    '.bloque-producto',
                    '.item-producto',
                    '[class*="producto"]',
                    '[class*="item"]'
                ]
                for selector in alt_selectors:
                    alt_products = response.css(selector)
                    self.logger.info(f"[Page {page_num}] Alternative selector '{selector}' found {len(alt_products)} items")
                    if alt_products:
                        product_blocks = alt_products
                        self.logger.info(f"[Page {page_num}] Using alternative selector: {selector}")
                        break
                
                # If still no products, log the page structure
                if not product_blocks:
                    self.logger.error(f"[Page {page_num}] No products found with any selector!")
                    # Log all elements with 'producto' in class name
                    all_producto_elements = response.css('[class*="producto"]')
                    self.logger.info(f"[Page {page_num}] All elements with 'producto' in class: {len(all_producto_elements)}")
                    for i, elem in enumerate(all_producto_elements[:5]):  # Log first 5
                        self.logger.info(f"[Page {page_num}] Element {i+1} classes: {elem.attrib.get('class', 'N/A')}")
                    
                    # Log all elements with 'resultado' in class name
                    all_resultado_elements = response.css('[class*="resultado"]')
                    self.logger.info(f"[Page {page_num}] All elements with 'resultado' in class: {len(all_resultado_elements)}")
                    
                    # Log page title and main content areas
                    page_title = response.css('title::text').get()
                    self.logger.info(f"[Page {page_num}] Page title: {page_title}")
                    
                    # Check if we're on a search results page
                    search_indicators = response.css('h1, h2, h3').getall()
                    self.logger.info(f"[Page {page_num}] Page headings: {[h.strip() for h in search_indicators[:3]]}")
                    
                    self.logger.error(f"[Page {page_num}] === END DEBUGGING - NO PRODUCTS FOUND ===")
                    return

            if not product_blocks:
                self.logger.warning(f"[Page {page_num}] No products found on this page. Will skip product loop and proceed to pagination check.")
            else:
                
                self.logger.info(f"[Page {page_num}] Starting product processing loop for {len(product_blocks)} products...")
                
                # Create a list to store all requests
                requests_to_process = []
                
                for i, item_selector in enumerate(product_blocks):
                    self.logger.debug(f"[Page {page_num}] Processing product {i+1}/{len(product_blocks)}.")
                    current_product_ref_for_log = "N/A" # For logging in case of early error
                    try:
                        reference_id = item_selector.css('.codigo-producto-marca a::attr(data-ean-no)').extract_first()
                        current_product_ref_for_log = reference_id or "N/A" # Update for logging
                        
                        if not reference_id:
                            self.logger.warning(f"[Page {page_num}] Product {i+1} missing 'data-ean-no' (reference_id). Skipping.")
                            continue

                        a_element_text = item_selector.css('a::text').get()
                        if not a_element_text: # Skip if the main link/identifier is missing
                            self.logger.warning(f"[Page {page_num}] Product {i+1} skipped due to missing 'a_element_text'.")
                            continue

                        codes_str = item_selector.css('a::attr(data-ean-ubicacion)').get()
                        if not codes_str:
                            self.logger.warning(f"[Page {page_num}] Product {i+1} missing 'data-ean-ubicacion'. Skipping.")
                            continue
                        codes = codes_str.split(" -> ")
                        if len(codes) < 2:
                            self.logger.warning(f"[Page {page_num}] Product {i+1} 'data-ean-ubicacion' format error: {codes_str}. Skipping.")
                            continue
                        gama_code = codes[0]
                        familia_code = codes[1]

                        code_brand_elements = item_selector.css('.codigo-producto-marca::text').extract()
                        code_brand_list = None # Initialize
                        if len(code_brand_elements) > 1:
                            code_brand_text = code_brand_elements[1].strip()
                            if code_brand_text:
                                 code_brand_list = code_brand_text.split()
                        
                        details_form_data_str = details_data_template.format(client_code=self.client_code_value or "UNKNOWN_CLIENT").replace("detailId", reference_id)
                        
                        form_data_dict_details = {}
                        for form_pair in details_form_data_str.split('&'):
                            if '=' in form_pair:
                                key_detail, value_detail = form_pair.split('=', 1)
                                form_data_dict_details[key_detail] = value_detail
                        
                        stock_text = item_selector.css('.boton-disponibilidad label span::text').extract_first()
                        stock, qtyLinear = parse_stock_qty(stock_text) 
                        
                        energy_class_img_src = item_selector.css("div.contenido-producto div[id^='etiquetaEnergIEFI'] > span > img::attr(src)").get() or \
                                               item_selector.css("div.contenido-producto > div:nth-child(8) > span > img::attr(src)").get() or \
                                               item_selector.css("div.contenido-producto > div:nth-child(8) > span > a > img::attr(data-src)").get()
                                               
                        self.logger.info(f"[Page {page_num}] Energy class img src: {energy_class_img_src}")
                        class_energy, stamp_energy = parse_energy_class(energy_class_img_src)
                        self.logger.info(f"[Page {page_num}] Energy class: {class_energy}, Stamp energy: {stamp_energy}")
                        specific_price_raw = item_selector.css('div.columna-producto-2 div.subcolumna-producto-2 p span:first-child span:first-child::text').extract_first()
                        self.logger.info(f"[Page {page_num}] Specific price raw: {specific_price_raw}")
                        if not specific_price_raw:
                            self.logger.warning(f"[Page {page_num}] Product {i+1} (Ref: {reference_id}) missing price. Skipping.")
                            continue
                        verified_price = verify_price_format_and_return_original(specific_price_raw, True)
                        if not verified_price:
                            self.logger.warning(f"[Page {page_num}] Product {i+1} (Ref: {reference_id}) invalid price format: {specific_price_raw}. Skipping.")
                            continue
                        
                        link_img = item_selector.css('div.imagen-producto img::attr(data-src)').extract_first()

                        self.logger.debug(f"[Page {page_num}] Creating detail request for product {reference_id}")
                        request = scrapy.FormRequest(
                            extra_information_url,
                            method='POST',
                            formdata=form_data_dict_details,
                            meta=dict(
                                playwright=True,
                                playwright_include_page=True,
                                playwright_page_methods=[
                                    PageMethod("wait_for_load_state", "networkidle", timeout=15000),
                                ],
                                price=verified_price,
                                gama_code=gama_code,
                                familia_code=familia_code,
                                stamp_energy=stamp_energy,
                                class_energy=class_energy,
                                qtyLinear=qtyLinear,
                                code_brand=code_brand_list, 
                                stock=stock,
                                link_img=link_img,
                                detail_request_source_page_num=page_num,
                                detail_request_product_ref=reference_id,
                                retry_times=0,  # Track retry attempts
                                max_retries=3,  # Maximum number of retries
                                retry_http_codes=[500, 502, 503, 504, 408, 429]  # HTTP codes to retry on
                            ),
                            callback=self.parse_details_page,
                            errback=self.errback,
                            dont_filter=True  # Allow retrying the same URL
                        )

                        requests_to_process.append(request)
                        self.pending_requests += 1
                        self.logger.info(f"[Page {page_num}] Successfully added request for product {reference_id}. Current pending count: {self.pending_requests}")

                    except AttributeError as ae:
                        self.logger.error(f"[Page {page_num}] ATTRIBUTE_ERROR while processing product {i+1} (Ref: {current_product_ref_for_log}). Error: {ae}", exc_info=True)
                        continue
                    except Exception as e:
                        self.logger.error(f"[Page {page_num}] EXCEPTION while processing product {i+1} (Ref: {current_product_ref_for_log}). Error: {e}", exc_info=True)
                        continue

                self.logger.info(f"[Page {page_num}] Finished collecting requests. Processing {len(requests_to_process)} requests...")
            
                # Now yield all requests
                for request in requests_to_process:
                    self.logger.info(f"[Page {page_num}] Yielding request for product {request.meta.get('detail_request_product_ref')}")
                    yield request
                
                self.logger.info(f"[Page {page_num}] All requests yielded. Proceeding to pagination check.")

            # "VER MAS" load-more pattern: keep requesting the next batch as long as
            # products were returned. The server returns an empty/short response when
            # there are no more products.
            if product_blocks:
                next_page = page_num + 1
                form_data_str = busqueda_data_next_page_template.format(client_code=self.client_code_value)
                next_form_data_dict = {}
                for item in form_data_str.split('&'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        next_form_data_dict[key] = value
                next_form_data_dict['datosformulario[3][value]'] = str(next_page)
                self.logger.info(f"[Page {page_num}] Found {len(product_blocks)} products, requesting next batch: {next_page}")
                yield scrapy.FormRequest(
                    start_url_after_login,
                    method='POST',
                    formdata=next_form_data_dict,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_connect_kwargs": {
                            "ws_endpoint": ZENROWS_WS_URL
                        },
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "networkidle", timeout=30000),
                            PageMethod("wait_for_selector", ".resultados", timeout=30000),
                        ],
                        "page": next_page
                    },
                    callback=self.parse_page,
                    errback=self.errback,
                    dont_filter=True
                )
            else:
                self.logger.info(f"[Page {page_num}] No products returned — reached end of catalogue.")

        except Exception as e:
            self.logger.error(f"[Page {page_num}] UNHANDLED EXCEPTION in parse_page main try block. Error: {e}", exc_info=True)
        finally:
            self.logger.info(f"[Page {page_num}] END parse_page (finally block).")
        
    
    def parse_details_page(self, response): # Product Detail Page
        print("Inside Parse Details Page")
        self.logger.info(f"PARSE-DETAILS-PAGE: Entered callback for product {response.meta.get('detail_request_product_ref')}")
        page = response.meta.get("playwright_page") # Playwright page from ZenRows

        try:
            if response.status != 200:
                self.logger.error(f"Invalid response status {response.status} for {response.url}")
                # Log full request and response details for debugging
                request = response.request
                self.logger.error(f"Request URL: {getattr(request, 'url', 'N/A')}")
                self.logger.error(f"Response status: {response.status}")
                # Log a snippet of the response body for inspection (limit to 1000 chars)
                response_text_snippet = response.text[:1000] if hasattr(response, 'text') else str(response.body)[:1000]
                # Check if it's a session expiration (though ZenRows session should be active)
                if "login" in response.url.lower() or "session" in response.text.lower():
                    self.logger.error("Session appears to have expired even with ZenRows. This is unexpected.")
                    # Consider re-login or stopping.
                    return
                return

            # Your existing parsing logic for s = scrapy.Selector(text=response.text)
            html_content_after_click = response.text # or await page.content() if needed
            s = scrapy.Selector(text=html_content_after_click) 
            reference_product = s.css('h1 > span::text').get()
            title_product = s.css('h1::text').get()
            
            if not reference_product or not title_product:
                self.logger.error(f"Could not find product reference or title in {response.url}")
                return
            
            self.logger.info(f"Processing product: {reference_product} - {title_product.strip() if title_product else ''}")
        
            nome_marca = s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(1) > td:first-child::text").get() == "Marca" and \
                        s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(1) > td.celda-caracteristicas-producto::text").get() or None
            ean = s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(3) > td:first-child::text").get() == "EAN" and \
                        s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(3) > td.celda-caracteristicas-producto::text").get() or None
            part_nr = s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(2) > td:first-child::text").get() == "Modelo" and \
                        s.css("#contenido-2 > table:nth-child(2) > tbody > tr:nth-child(2) > td.celda-caracteristicas-producto::text").get() or None
            
            peso_dimensiones_section = None
            for h3 in s.css("#contenido-2 h3::text").getall():
                if "Peso y dimensiones" in h3: # Make sure this matches the text
                    peso_dimensiones_section = h3
                    break
            
            peso, peso_paquete, comprimento, comprimento_paquete, largura, largura_paquete, altura, altura_paquete = (None,) * 8
            
            if peso_dimensiones_section:
                # Assuming the table is the next sibling table or identified correctly
                # This selector might need adjustment: "#contenido-2 > table:nth-child(4) > tbody > tr"
                # It's better to find the h3, then find the next table.
                # Example: rows = s.xpath("//h3[contains(text(),'Peso y dimensiones')]/following-sibling::table[1]/tbody/tr")
                # For CSS, it's harder to get "next sibling table". Let's assume current selector is okay for now.
                rows = s.css("#contenido-2 > table:nth-child(4) > tbody > tr") 
                
                for row in rows:
                    label = row.css("td:first-child::text").get()
                    value = row.css("td.celda-caracteristicas-producto::text").get()
                    
                    if not label or not value: continue
                    label = label.strip(); value = value.strip()
                    
                    if label == "Peso": peso = value
                    elif label == "Peso del paquete": peso_paquete = value
                    elif label == "Profundidad": comprimento = value
                    elif label == "Profundidad del paquete": comprimento_paquete = value
                    elif label == "Ancho": largura = value
                    elif label == "Ancho del paquete": largura_paquete = value
                    elif label == "Altura": altura = value
                    elif label == "Altura del paquete": altura_paquete = value
            
            peso_used = peso_paquete if peso_paquete else (peso if peso else '-')
            comprimento_used = comprimento_paquete if comprimento_paquete else (comprimento if comprimento else '-')
            largura_used = largura_paquete if largura_paquete else (largura if largura else '-')
            altura_used = altura_paquete if altura_paquete else (altura if altura else '-')
            
            outras_fotos = s.css('div.galleria-image img::attr(src)').getall()
            link_energy_class = s.css('#descripcion > nav > ul > li:nth-child(3) > a::attr(href)').get()
            if link_energy_class: link_energy_class = link_energy_class.strip()

            code_brand_meta = response.meta['code_brand'][0] if response.meta.get('code_brand') and response.meta['code_brand'] else None
            
            item = ProductDetailsItem()
            item['Referencia'] = reference_product
            item['NOME_PRODUTO'] = title_product.strip() if title_product else None
            item['CodMarca'] = code_brand_meta
            item['NOME_MARCA'] = nome_marca.strip() if nome_marca else None
            item['Cod_Gama'] = response.meta.get('gama_code')
            item['NOME_GAMA'] = parse_code_gama(response.meta.get('gama_code'))
            item['Cod_Familia'] = response.meta.get('familia_code')
            item['NOME_FAMILIA'] = response.meta.get('familia_code') 
            item['SUBFAMILIA'] = "-" 
            item['NOME_SUBFAMILIA'] = "-"
            item['PR_LIQUIDO'] = response.meta.get('price')
            item['PartNr'] = part_nr.strip() if part_nr else None
            item['EAN'] = ean.strip() if ean else None
            item['Peso_kg'] = peso_used
            item['Comprimento_mm'] = comprimento_used
            item['Largura_mm'] = largura_used
            item['Altura_mm'] = altura_used
            item['Volume_dm3'] = "-"
            item['LinkImagem'] = response.meta.get('link_img') 
            item['OutrasFotos'] = outras_fotos
            item['Stock'] = response.meta.get('stock')
            item['QtdLinear'] = response.meta.get('qtyLinear')
            item['Classe_energetica'] = response.meta.get('class_energy')
            item['Selo_Classe_Energetica'] = response.meta.get('stamp_energy')
            item['Link_Classe_Energetica'] = link_energy_class
            
            self.logger.info(f"Yielding item for product {reference_product}")
            yield item
            
        except Exception as e:
            self.logger.error(f"Error processing page {response.url} in parse_details_page: {e}", exc_info=True)
            if page and not page.is_closed():
                page.screenshot(path=f"error_parse_details_{response.meta.get('detail_request_product_ref', 'unknown')}.png")
        finally:
            self.pending_requests -= 1
            self.logger.info(f"Decremented pending requests. Current count: {self.pending_requests}")
            # Playwright page closure is usually handled by scrapy-playwright when the context is done or per request if not reusing context.
            # If you explicitly manage contexts, you'd close it there. For now, this is fine.
            # self.logger.info(f"Playwright page interaction ended for {response.url}")


    async def errback(self, failure): # Generic errorback
        print("Inside Errback")
        print("failure",failure)
        print("request",failure.request)
        print("page",failure.request.meta.get("playwright_page"))
        request = failure.request
        page = failure.request.meta.get("playwright_page")
        
        self.logger.error(f"Request failed: {failure.value}")

        # Your existing retry logic
        retry_times = request.meta.get('retry_times', 0)
        max_retries = request.meta.get('max_retries', 3)
        
        if hasattr(failure.value, 'response'):
            self.logger.error(f"Response status: {failure.value.response.status}")
            # ... (rest of your logging)
        else:
            self.logger.error(f"Request failed without response: {failure.value}")
            # ... (rest of your logging)
        
        if retry_times < max_retries:
            retry_times += 1
            self.logger.info(f"Retrying request (attempt {retry_times}/{max_retries})")
            delay = 2 ** retry_times # Exponential backoff
            self.logger.info(f"Waiting {delay} seconds before retry")
            
            # Ensure Playwright meta is correctly copied for retries
            new_request_meta = request.meta.copy()
            new_request_meta['retry_times'] = retry_times
            # If playwright_page was part of meta and closed, it shouldn't be reused.
            # scrapy-playwright should handle creating a new page on retry.
            # Ensure playwright_connect_kwargs is still there for ZenRows.
            if 'playwright_connect_kwargs' not in new_request_meta and playwright_meta_for_zenrows['playwright_connect_kwargs']:
                 new_request_meta['playwright_connect_kwargs'] = playwright_meta_for_zenrows['playwright_connect_kwargs']

            new_request = request.replace(meta=new_request_meta, dont_filter=True)
            return new_request
        else:
            self.logger.error(f"Max retries ({max_retries}) exceeded for request to {request.url}")
            if 'detail_request_product_ref' in request.meta : # if it was a detail page request
                 self.pending_requests -=1 # Decrement only if it was a pending product detail
            return None