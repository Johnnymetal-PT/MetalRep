import os
import re

def parse_code_gama(code):
    code_mapping = {
        "00BLANCA": "BLANCA (Frig, Lvd, Lvj, Cong, Sec, etc)",
        "01MARRON": "MARRÓN (TV, Video, DVD, Bluray)",
        "02COCCION": "COCCIÓN (Cocinas, Horn, Encim, Camp, Micr, etc)",
        "03SONIDO": "SONIDO (HiFi, MP3, Radcas, RadCD, etc)",
        "04CALEF Y VENTI": "CLIMATIZACIÓN (Estufas, Termos, cal) (Vent, Acon)",
        "05MAT. ELECTRIC": "MATERIAL ELÉCTRICO (Adap, Cables, Reg, Pilas, etc)",
        "06MENAJE": "MENAJE (Ollas, Basc, Sart, Cafet, etc)",
        "07PAE": "P.A.E. (Batid, Afeit, Freid, Tost, Aspi, Sec, etc)",
        "08TELEFONIA": "TELEFONÍA (Smartphone, Seniorphone, Tablets, Dect)",
        "09VARIOS": "VARIOS (Acces, Cintas, Mesas, Soport, etc, etc)",
        "10INFORMATICA": "INFORMÁTICA (Portatiles, accesorios)",
        "11VIDEOCONSOLAS": "VIDEOCONSOLAS, JUEGOS Y ACCESORIOS",
        "12FOTOGRAFIA": "FOTOGRAFIA Y ACCESORIOS",
        "ALIMENTACION": "ALIMENTACION",
        "CAFE": "CAFÉ",
        "DESCANSO": "DESCANSO",
        "ENERGIA": "ENERGIA (Bombillas, Pilas, Lámparas, Linternas)",
        "GARANTIAS": "GARANTIAS DE PRODUCTO",
        "MARKETING": "MARKETING",
        "OCIO Y TIEMPO LIBRE": "OCIO Y TIEMPO LIBRE (Movilidad, Fitness, Drones..)",
        "SMART HOME": "SMART HOME",
        "SUPLEMENTACION": "SUPLEMENTACION",
    }
    
    if code in code_mapping:
        return code_mapping[code]
    else:
        return "Unknown code"

def parse_energy_class(energy_class):
    if energy_class is None or not energy_class:
        return ("No Information", "No Information")
        
    energy_link = energy_class.split("/Images/")[1]
    code_mapping = {
        "etiqueta-A-mielectro.png": "A",
        "etiqueta-B-mielectro.png": "B",
        "etiqueta-C-mielectro.png": "C",
        "etiqueta-D-mielectro.png": "D",
        "etiqueta-E-mielectro.png": "E",
        "etiqueta-F-mielectro.png": "F",
        "etiqueta-G-mielectro.png": "G",
    }

    if energy_link in code_mapping:
        return (code_mapping[energy_link], os.getenv("IMAGE_URL") + energy_class)
    else:
        return ("No Information", "No Information")
    
def parse_stock_qty(stock_Value):
    parts = stock_Value.strip().split(' ')
    stock = int(parts[0])
    qtyLinear = int(parts[1][1:-1])
    
    return stock, qtyLinear

def html_to_oneliner(html_content):
    """
    Converts HTML content into a single line by removing unnecessary whitespace and empty lines.
    
    Args:
        html_content (str): The HTML content to process
        
    Returns:
        str: The cleaned HTML content as a single line
    """
    whitespace_to_strip = ' \n\t\r\f\v\xa0'
    lines = html_content.splitlines()
    processed_lines = []
    for line in lines:
        # Strip leading and trailing whitespace (including NBSP) from each line
        stripped_line = line.strip(whitespace_to_strip)
        if stripped_line:  # Only add non-empty lines
            processed_lines.append(stripped_line)

    # Join the processed lines to form the one-liner
    return "".join(processed_lines)

def verify_price_format_and_return_original(price_input, log_verification_failure=False):
    """
    Checks if price_input can be converted to a float.
    Returns the original input if valid, False if invalid.
    
    Args:
        price_input: The value to verify (string, int, float, etc)
        log_verification_failure: If True, prints a message when verification fails
        
    Returns:
        The original price_input if valid, False if invalid
    """
    print(f"[PRICE VERIFICATION] Processing input: {price_input} (type: {type(price_input)})")
    
    if isinstance(price_input, (int, float)):
        print(f"[PRICE VERIFICATION] Valid numeric input: {price_input}")
        return price_input
        
    if not isinstance(price_input, str):
        if log_verification_failure:
            print(f"[VERIFICATION INFO] Invalid price format: {price_input}")
        print(f"[PRICE VERIFICATION] Failed: Input is not a string or number")
        return False
        
    # Clean the string
    price_str = price_input.strip()
    if not price_str:
        if log_verification_failure:
            print(f"[VERIFICATION INFO] Empty price string")
        print(f"[PRICE VERIFICATION] Failed: Empty string after stripping")
        return False
    
    try:
        # Try direct conversion first
        float(price_str)
        print(f"[PRICE VERIFICATION] Success: Valid price format with period: {price_str}")
        return price_input
    except ValueError:
        # Try with comma as decimal separator
        try:
            float(price_str.replace(',', '.'))
            print(f"[PRICE VERIFICATION] Success: Valid price format with comma: {price_str}")
            return price_input
        except ValueError:
            # Try handling thousand separators (e.g., "1.060,80")
            try:
                # Remove thousand separators (dots) and replace comma with dot for decimal
                cleaned_price = price_str.replace('.', '').replace(',', '.')
                float(cleaned_price)
                print(f"[PRICE VERIFICATION] Success: Valid price format with thousand separators: {price_str}")
                return price_input
            except ValueError:
                if log_verification_failure:
                    print(f"[VERIFICATION INFO] Invalid price format: {price_input}")
                print(f"[PRICE VERIFICATION] Failed: Could not convert to float with any format")
                return False

