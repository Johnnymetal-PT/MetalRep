"""Descoberta automatica de termos protegidos.

A partir de uma query (categoria ou tema, ex.: "Smartphones", "Star Wars") e
de um modo (``heuristic``, ``gtin``, ``both``), procura nomes proprios (marcas,
modelos, designacoes de produto) em Wikipedia/Wikidata e (opcional) GTIN para
seedar a lista de ``translate_protected_terms`` do fornecedor.

Util quando se onboards um fornecedor novo: em vez de listar manualmente
dezenas de termos, lanca-se uma discovery e revoga-se o resultado.
"""

import logging
import re
from dataclasses import dataclass

import requests


_logger = logging.getLogger(__name__)

WIKIPEDIA_SEARCH_ENDPOINT = "https://{lang}.wikipedia.org/w/rest.php/v1/search/page"
WIKIPEDIA_RELATED_ENDPOINT = "https://{lang}.wikipedia.org/api/rest_v1/page/related/{title}"
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


@dataclass
class PgTermDiscoveryStats:
    query: str
    mode: str
    preset: str = ""
    wikipedia_en_count: int = 0
    wikipedia_pt_count: int = 0
    wikidata_count: int = 0
    gtin_count: int = 0
    seeded_count: int = 0
    total_terms: int = 0


class PgTermDiscoveryService:
    def __init__(self, query, mode="heuristic", *, preset=False, max_terms=120, timeout=25):
        self.query = str(query or "").strip()
        self.mode = (mode or "heuristic").strip().lower()
        self.preset = (preset or "").strip().lower()
        self.max_terms = max(10, int(max_terms))
        self.timeout = max(5, int(timeout))
        self._headers = {
            "User-Agent": "HiperSyncTermDiscovery/1.0 (admin@hipermercado.pt)",
        }

    def discover_terms(self):
        if not self.query:
            return [], PgTermDiscoveryStats(query="", mode=self.mode, preset=self.preset)
        terms = [self.query]
        stats = PgTermDiscoveryStats(query=self.query, mode=self.mode, preset=self.preset)
        preset_terms = self._preset_seed_terms()
        stats.seeded_count = len(preset_terms)
        terms.extend(preset_terms)
        if self.mode in {"heuristic", "both"}:
            search_queries = self._build_search_queries()
            wiki_en = self._wikipedia_terms_for_queries(lang="en", queries=search_queries, limit=18, stats=stats)
            wiki_pt = self._wikipedia_terms_for_queries(lang="pt", queries=search_queries, limit=18, stats=stats)
            terms.extend(wiki_en)
            terms.extend(wiki_pt)
            terms.extend(self._wikipedia_related_terms(lang="en", titles=wiki_en[:3], stats=stats))
            terms.extend(self._wikipedia_related_terms(lang="pt", titles=wiki_pt[:3], stats=stats))
            terms.extend(self._wikidata_terms(limit=25, stats=stats))
        if self.mode in {"gtin", "both"}:
            stats.gtin_count = 0
            _logger.info(
                "PG term discovery GTIN step requested but not configured query=%s",
                self.query,
            )
        cleaned = self._clean_terms(terms)
        stats.total_terms = len(cleaned)
        if len(cleaned) > self.max_terms:
            cleaned = cleaned[: self.max_terms]
        return cleaned, stats

    def _wikipedia_terms_for_queries(self, *, lang, queries, limit, stats):
        titles = []
        for query in queries:
            titles.extend(self._wikipedia_terms(lang=lang, query=query, limit=limit, stats=stats))
        return titles

    def _wikipedia_terms(self, *, lang, query, limit, stats):
        url = WIKIPEDIA_SEARCH_ENDPOINT.format(lang=lang)
        params = {
            "q": query,
            "limit": limit,
        }
        try:
            response = requests.get(url, params=params, headers=self._headers, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:
            _logger.warning("PG term discovery Wikipedia search failed lang=%s query=%s error=%s", lang, self.query, exc)
            return []
        payload = response.json() if response.content else {}
        titles = [item.get("title") for item in payload.get("pages", []) if item.get("title")]
        if lang == "en":
            stats.wikipedia_en_count += len(titles)
        else:
            stats.wikipedia_pt_count += len(titles)
        return titles

    def _wikipedia_related_terms(self, *, lang, titles, stats):
        related = []
        for title in titles:
            if not title:
                continue
            url = WIKIPEDIA_RELATED_ENDPOINT.format(lang=lang, title=requests.utils.quote(title))
            try:
                response = requests.get(url, headers=self._headers, timeout=self.timeout)
                response.raise_for_status()
            except Exception as exc:
                _logger.warning(
                    "PG term discovery Wikipedia related failed lang=%s title=%s error=%s",
                    lang,
                    title,
                    exc,
                )
                continue
            payload = response.json() if response.content else {}
            pages = payload.get("pages") or []
            for page in pages[:20]:
                page_title = page.get("title")
                if page_title:
                    related.append(page_title)
        if related:
            _logger.info(
                "PG term discovery Wikipedia related fetched lang=%s seed_titles=%s related_count=%s",
                lang,
                len(titles),
                len(related),
            )
        return related

    def _wikidata_terms(self, *, limit, stats):
        query = """
            SELECT ?label WHERE {
              ?item rdfs:label ?label .
              FILTER(LANG(?label) IN ("en", "pt")) .
              FILTER(CONTAINS(LCASE(STR(?label)), LCASE("%(needle)s"))) .
            }
            LIMIT %(limit)s
        """ % {
            "needle": self.query.replace('"', ""),
            "limit": int(limit),
        }
        try:
            response = requests.get(
                WIKIDATA_SPARQL_ENDPOINT,
                params={"format": "json", "query": query},
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:
            _logger.warning("PG term discovery Wikidata search failed query=%s error=%s", self.query, exc)
            return []
        payload = response.json() if response.content else {}
        results = payload.get("results", {}).get("bindings", [])
        labels = [item.get("label", {}).get("value") for item in results if item.get("label", {}).get("value")]
        stats.wikidata_count = len(labels)
        return labels

    def _clean_terms(self, terms):
        seen = set()
        cleaned = []
        for term in terms:
            value = re.sub(r"\s+", " ", str(term or "").strip())
            if not value:
                continue
            if len(value) < 2 or len(value) > 90:
                continue
            if value.casefold() == self.query.casefold():
                cleaned.append(value)
                seen.add(value.casefold())
                continue
            if not self._looks_like_name(value):
                continue
            if self._is_noise_term(value):
                continue
            normalized = value.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(value)
        cleaned.sort(key=len, reverse=True)
        return cleaned

    def _build_search_queries(self):
        queries = [self.query]
        extra = self._preset_search_queries()
        queries.extend(extra)
        return [item for item in queries if item]

    def _preset_search_queries(self):
        if not self.preset:
            return []
        subcategory_queries = {
            "pg_informatica_portateis": ["laptop brands", "marcas de portateis", "notebook brands"],
            "pg_informatica_monitores": ["monitor brands", "marcas de monitores", "gaming monitor brands"],
            "pg_informatica_perifericos": ["perifericos pc marcas", "pc peripherals brands"],
            "pg_informatica_impressoras": ["printer brands", "marcas de impressoras"],
            "pg_informatica_consumiveis_impressao": ["toner brands", "tinteiro marcas", "ink cartridge brands"],
            "pg_informatica_cadeiras_gaming": ["gaming chair brands", "cadeiras gaming marcas"],
            "pg_informatica_teclados_gaming": ["gaming keyboard brands", "teclados gaming marcas"],
            "pg_informatica_ratos_gaming": ["gaming mouse brands", "ratos gaming marcas"],
            "pg_informatica_auscultadores_gaming": ["gaming headset brands", "auscultadores gaming marcas"],
            "pg_informatica_tapetes_gaming": ["gaming mousepad brands", "tapetes gaming marcas"],
            "pg_informatica_consolas": ["console brands", "marcas de consolas"],
            "pg_eletro_maquinas_lavar_roupa": ["washing machine brands", "marcas de maquina lavar roupa"],
            "pg_eletro_combinados": ["fridge freezer brands", "marcas de combinados"],
            "pg_eletro_placas": ["cooktop brands", "placas inducao marcas"],
            "pg_eletro_micro_ondas": ["microwave brands", "micro-ondas marcas"],
            "pg_eletro_lavar_secar_roupa": ["washer dryer brands", "marcas de maquina lavar e secar"],
            "pg_eletro_frigorificos": ["fridge brands", "marcas de frigorificos"],
            "pg_eletro_fogoes": ["stove brands", "fogoes marcas"],
            "pg_eletro_tratamento_aguas": ["water purifier brands", "tratamento de aguas marcas"],
            "pg_eletro_secar_roupa": ["dryer brands", "maquinas de secar roupa marcas"],
            "pg_eletro_side_by_side": ["side by side fridge brands", "frigorifico side by side marcas"],
            "pg_eletro_maquinas_cafe": ["coffee machine brands", "maquinas de cafe marcas"],
            "pg_eletro_climatizacao": ["air conditioner brands", "climatizacao marcas"],
            "pg_eletro_tratamento_roupa": ["ironing system brands", "ferro com caldeira marcas"],
            "pg_eletro_arcas": ["chest freezer brands", "arca frigorifica marcas"],
            "pg_eletro_preparacao_alimentar": ["kitchen robot brands", "preparacao alimentar marcas"],
            "pg_eletro_lava_loicas_misturadoras": ["lava loicas marcas", "misturadora cozinha marcas"],
            "pg_eletro_cuidados_lar": ["vacuum brands", "aspirador marcas"],
            "pg_eletro_lavar_louca": ["dishwasher brands", "maquina lavar louca marcas"],
            "pg_eletro_exaustores": ["extractor hood brands", "exaustor marcas"],
            "pg_eletro_cuidados_pessoais": ["personal care brands", "cuidados pessoais marcas"],
            "pg_eletro_fornos": ["oven brands", "fornos marcas"],
            "pg_eletro_hotelaria": ["industrial kitchen brands", "hotelaria equipamento marcas"],
            "pg_imagem_som_televisores": ["tv brands", "marcas de televisores"],
            "pg_imagem_som_videoprojetores": ["projector brands", "videoprojetor marcas"],
            "pg_imagem_som_home_cinema": ["home cinema brands", "soundbar brands"],
            "pg_imagem_som_home_audio": ["home audio brands", "speaker brands"],
            "pg_imagem_som_acessorios_tv": ["tv accessories", "suporte tv marcas"],
            "pg_imagem_som_car_audio": ["car audio brands", "car multimedia brands"],
            "pg_espaco_crianca_carros_eletricos": ["carros eletricos crianca marcas", "kids electric car brands"],
            "pg_espaco_crianca_motas_eletricas": ["motas eletricas crianca marcas", "kids electric bike brands"],
            "pg_espaco_crianca_piscinas": ["pool brands", "piscinas marcas"],
            "pg_espaco_crianca_brinquedos_exterior": ["outdoor toys brands", "brinquedos exterior marcas"],
            "pg_geek_funko": ["funko pop", "funko brands"],
            "pg_geek_disney": ["disney characters", "disney merchandise"],
            "pg_geek_anime_manga": ["anime merchandise", "manga brands"],
            "pg_geek_series_tv": ["tv series merchandise", "series de tv merch"],
            "pg_geek_filmes": ["movie merchandise", "filmes merch"],
            "pg_geek_super_herois": ["super hero merchandise", "super herois merch"],
            "pg_geek_jogos_brinquedos": ["toys brands", "jogos brinquedos marcas"],
            "pg_geek_videojogos": ["video game brands", "videojogos marcas"],
            "pg_geek_pre_reservas": ["collectibles preorder", "pre-reservas colecionaveis"],
            "pg_mobilidade_smartphones": ["smartphone brands", "marcas de smartphones"],
            "pg_mobilidade_smartwatch": ["smartwatch brands", "wearables brands"],
            "pg_mobilidade_trotinetes": ["electric scooter brands", "trotinetes marcas"],
            "pg_mobilidade_acessorios_telemovel": ["acessorios telemovel", "mobile accessories brands"],
        }
        if self.preset in subcategory_queries:
            return subcategory_queries[self.preset]
        if self.preset == "tv":
            return ["television brands", "marcas de TV", "televisores marcas"]
        if self.preset == "smartphones":
            return ["smartphone brands", "marcas de smartphones", "telemovel marcas"]
        if self.preset == "kitchen":
            return ["kitchen appliance brands", "marcas de eletrodomesticos", "marcas de cozinha"]
        if self.preset == "tech":
            return ["consumer electronics brands", "marcas de tecnologia", "eletronica de consumo marcas"]
        if self.preset == "pg_informatica":
            return ["informatica marcas", "computer brands", "laptop brands", "printer brands"]
        if self.preset == "pg_eletrodomesticos":
            return ["eletrodomesticos marcas", "home appliance brands", "marcas de cozinha"]
        if self.preset == "pg_imagem_som":
            return ["imagem e som marcas", "audio video brands", "home cinema brands"]
        if self.preset == "pg_espaco_crianca":
            return ["brinquedos marcas", "kids toys brands", "jogos e brinquedos marcas"]
        if self.preset == "pg_geek_zone":
            return ["geek merchandise brands", "franchise merchandise", "collectibles brands"]
        if self.preset == "pg_mobilidade":
            return ["mobilidade eletrica marcas", "electric scooter brands", "trotinetes marcas"]
        if self.preset == "pg_outlet_hot":
            return ["outlet electronics brands", "clearance electronics brands"]
        if self.preset == "pg_ofertas_flash_hot":
            return ["flash deals electronics brands", "promo electronics brands"]
        return []

    def _preset_seed_terms(self):
        if not self.preset:
            return []
        if self.preset == "pg_informatica_portateis":
            return ["Laptop", "Portátil", "Ultrabook", "SSD", "RAM", "Ryzen", "Intel", "GPU", "RTX", "USB-C", "HDMI", "Wi-Fi"]
        if self.preset == "pg_informatica_monitores":
            return ["IPS", "VA", "TN", "144Hz", "165Hz", "240Hz", "4K", "UHD", "Full HD", "HDMI", "DisplayPort", "FreeSync", "G-Sync"]
        if self.preset == "pg_informatica_perifericos":
            return ["Teclado", "Rato", "Auscultadores", "USB", "Bluetooth", "Wireless", "RGB"]
        if self.preset == "pg_informatica_impressoras":
            return ["Laser", "Jato de Tinta", "Multifunções", "Wi-Fi", "Duplex"]
        if self.preset == "pg_informatica_consumiveis_impressao":
            return ["Toner", "Tinteiro", "Cartucho", "Original", "Compatível"]
        if self.preset == "pg_informatica_cadeiras_gaming":
            return ["Ergonómica", "Reclinável", "Apoio lombar"]
        if self.preset == "pg_informatica_teclados_gaming":
            return ["Mecânico", "Membrana", "RGB", "Switch"]
        if self.preset == "pg_informatica_ratos_gaming":
            return ["DPI", "RGB", "Wireless"]
        if self.preset == "pg_informatica_auscultadores_gaming":
            return ["7.1", "Surround", "Microfone", "Bluetooth"]
        if self.preset == "pg_informatica_tapetes_gaming":
            return ["XL", "XXL", "Antiderrapante"]
        if self.preset == "pg_informatica_consolas":
            return ["PS5", "Xbox", "Nintendo", "4K", "HDR", "SSD"]
        if self.preset == "pg_eletro_maquinas_lavar_roupa":
            return ["kg", "rpm", "Inverter", "Classe A", "A+++", "Vapor"]
        if self.preset == "pg_eletro_combinados":
            return ["No Frost", "Litros", "Inox", "Classe A"]
        if self.preset == "pg_eletro_placas":
            return ["Indução", "Vitrocerâmica", "Gás", "Zona flexível"]
        if self.preset == "pg_eletro_micro_ondas":
            return ["Grill", "Litros", "W", "Inox"]
        if self.preset == "pg_eletro_lavar_secar_roupa":
            return ["kg", "Secagem", "Inverter"]
        if self.preset == "pg_eletro_frigorificos":
            return ["No Frost", "Litros", "Inox", "Classe A"]
        if self.preset == "pg_eletro_fogoes":
            return ["Gás", "Forno", "Inox"]
        if self.preset == "pg_eletro_tratamento_aguas":
            return ["Filtro", "Osmose", "Purificador"]
        if self.preset == "pg_eletro_secar_roupa":
            return ["Bomba de calor", "kg", "Classe A"]
        if self.preset == "pg_eletro_side_by_side":
            return ["No Frost", "Litros", "Dispenser"]
        if self.preset == "pg_eletro_maquinas_cafe":
            return ["Expresso", "Cápsulas", "Bar", "Moagem"]
        if self.preset == "pg_eletro_climatizacao":
            return ["BTU", "Inverter", "A++", "Wi-Fi"]
        if self.preset == "pg_eletro_tratamento_roupa":
            return ["Ferro", "Caldeira", "Vapor"]
        if self.preset == "pg_eletro_arcas":
            return ["Litros", "Congelador"]
        if self.preset == "pg_eletro_preparacao_alimentar":
            return ["Robot", "Liquidificador", "Batedeira"]
        if self.preset == "pg_eletro_lava_loicas_misturadoras":
            return ["Misturadora", "Inox", "Monocomando"]
        if self.preset == "pg_eletro_cuidados_lar":
            return ["Aspirador", "Robot", "HEPA", "Vassoura"]
        if self.preset == "pg_eletro_lavar_louca":
            return ["dB", "Programas", "Inox"]
        if self.preset == "pg_eletro_exaustores":
            return ["m3/h", "Filtro", "Inox"]
        if self.preset == "pg_eletro_cuidados_pessoais":
            return ["Barbear", "Secador", "Depiladora", "Escova"]
        if self.preset == "pg_eletro_fornos":
            return ["Convecção", "Pirolítico", "Inox"]
        if self.preset == "pg_eletro_hotelaria":
            return ["Industrial", "Profissional", "Inox"]
        if self.preset == "pg_imagem_som_televisores":
            return self._preset_seed_terms_for("tv")
        if self.preset == "pg_imagem_som_videoprojetores":
            return ["ANSI lumens", "Full HD", "4K", "Keystone", "Laser"]
        if self.preset == "pg_imagem_som_home_cinema":
            return ["Soundbar", "5.1", "7.1", "Dolby", "Dolby Atmos"]
        if self.preset == "pg_imagem_som_home_audio":
            return ["Bluetooth", "Wi-Fi", "Multiroom", "Hi-Fi"]
        if self.preset == "pg_imagem_som_acessorios_tv":
            return ["Suporte", "HDMI", "VESA", "Comando"]
        if self.preset == "pg_imagem_som_car_audio":
            return ["DIN", "Android Auto", "Apple CarPlay", "Bluetooth"]
        if self.preset == "pg_espaco_crianca_carros_eletricos":
            return ["12V", "24V", "Bateria"]
        if self.preset == "pg_espaco_crianca_motas_eletricas":
            return ["12V", "24V", "Bateria"]
        if self.preset == "pg_espaco_crianca_piscinas":
            return ["Litros", "Filtro", "Bomba"]
        if self.preset == "pg_espaco_crianca_brinquedos_exterior":
            return ["Trampolim", "Escorrega", "Baloiço"]
        if self.preset == "pg_geek_funko":
            return ["Funko Pop", "Vinyl", "Colecionável"]
        if self.preset == "pg_geek_disney":
            return ["Disney", "Pixar", "Marvel", "Star Wars"]
        if self.preset == "pg_geek_anime_manga":
            return ["Anime", "Manga", "Figura", "Colecionável"]
        if self.preset == "pg_geek_series_tv":
            return ["Série", "Box Set", "Blu-ray", "DVD"]
        if self.preset == "pg_geek_filmes":
            return ["Filme", "Blu-ray", "DVD", "Steelbook"]
        if self.preset == "pg_geek_super_herois":
            return ["Marvel", "DC Comics", "Hero", "Figura"]
        if self.preset == "pg_geek_jogos_brinquedos":
            return ["Brinquedos", "Jogos", "Figura", "Pelúcia"]
        if self.preset == "pg_geek_videojogos":
            return ["PS5", "Xbox", "Nintendo", "Switch"]
        if self.preset == "pg_geek_pre_reservas":
            return ["Pré-Reserva", "Edição Limitada", "Colecionável"]
        if self.preset == "pg_mobilidade_smartphones":
            return self._preset_seed_terms_for("smartphones")
        if self.preset == "pg_mobilidade_smartwatch":
            return ["AMOLED", "GPS", "Bluetooth", "IP68", "Wearables"]
        if self.preset == "pg_mobilidade_trotinetes":
            return ["Autonomia", "km/h", "W", "Wh", "Bateria"]
        if self.preset == "pg_mobilidade_acessorios_telemovel":
            return ["Capa", "Película", "Carregador", "USB-C"]
        if self.preset == "tv":
            return [
                "OLED",
                "QLED",
                "Mini LED",
                "MicroLED",
                "LCD",
                "LED",
                "HDR",
                "HDR10",
                "HDR10+",
                "Dolby Vision",
                "Dolby Atmos",
                "UHD",
                "4K",
                "8K",
                "HDMI",
                "HDMI 2.1",
                "eARC",
                "ARC",
                "Smart TV",
                "Google TV",
                "Android TV",
                "Tizen",
                "webOS",
            ]
        if self.preset == "smartphones":
            return [
                "5G",
                "4G",
                "LTE",
                "OLED",
                "AMOLED",
                "Snapdragon",
                "MediaTek",
                "Exynos",
                "Dimensity",
                "USB-C",
                "Wi-Fi",
                "WiFi",
                "NFC",
                "IP67",
                "IP68",
                "mAh",
                "Dual SIM",
                "eSIM",
                "Fast Charge",
            ]
        if self.preset == "kitchen":
            return [
                "Inox",
                "Classe A",
                "A+",
                "A++",
                "A+++",
                "No Frost",
                "Whirlpool",
                "Bosch",
            ]
        if self.preset == "tech":
            return [
                "Bluetooth",
                "USB",
                "USB-C",
                "Wi-Fi",
                "WiFi",
                "NFC",
                "SSD",
                "HDD",
                "RAM",
            ]
        if self.preset == "pg_informatica":
            return [
                "Portátil",
                "Laptop",
                "Monitor",
                "Teclado",
                "Rato",
                "SSD",
                "HDD",
                "RAM",
                "GPU",
                "USB",
                "USB-C",
                "HDMI",
                "Wi-Fi",
                "WiFi",
            ]
        if self.preset == "pg_eletrodomesticos":
            return [
                "No Frost",
                "Inox",
                "Classe A",
                "A+",
                "A++",
                "A+++",
                "Capacidade",
                "Litros",
            ]
        if self.preset == "pg_imagem_som":
            return [
                "Soundbar",
                "Home Cinema",
                "Bluetooth",
                "Dolby",
                "Dolby Atmos",
                "Dolby Vision",
                "HDMI",
                "UHD",
                "4K",
            ]
        if self.preset == "pg_espaco_crianca":
            return [
                "Brinquedos",
                "Jogos",
                "Piscinas",
                "Motas Elétricas",
                "Carros Elétricos",
            ]
        if self.preset == "pg_geek_zone":
            return [
                "Funko",
                "Disney",
                "Marvel",
                "DC Comics",
                "Star Wars",
                "Anime",
                "Manga",
            ]
        if self.preset == "pg_mobilidade":
            return [
                "Trotinete",
                "Autonomia",
                "km/h",
                "W",
                "Wh",
                "Bateria",
            ]
        if self.preset == "pg_outlet_hot":
            return ["Outlet", "Recondicionado"]
        if self.preset == "pg_ofertas_flash_hot":
            return ["Promoção", "Desconto", "Flash"]
        return []

    def _preset_seed_terms_for(self, preset):
        original = self.preset
        self.preset = preset
        try:
            return self._preset_seed_terms()
        finally:
            self.preset = original

    def _looks_like_name(self, value):
        letters = re.findall(r"[A-Za-zÀ-ÿ]", value)
        if not letters:
            return False
        upper = sum(1 for char in letters if char.isupper())
        ratio = upper / len(letters)
        if ratio > 0.9 and len(letters) > 4:
            return False
        if value.isdigit():
            return False
        if re.search(r"\b\d{4,}\b", value):
            return False
        return True

    def _is_noise_term(self, value):
        lowered = value.casefold()
        list_prefixes = (
            "list of ",
            "lists of ",
            "lista de ",
            "lista dos ",
            "lista das ",
            "characters of ",
            "teams and organizations ",
            "features of ",
        )
        if any(lowered.startswith(prefix) for prefix in list_prefixes):
            return True
        if " list of " in lowered or " lista de " in lowered:
            return True
        noise_contains = (
            "characters of the",
            "teams and organizations",
            "timeline",
            "phase ",
            "fase ",
        )
        if any(token in lowered for token in noise_contains):
            return True
        generic_equals = {
            "filme",
            "filmes",
            "film",
            "films",
            "série",
            "series",
            "tv series",
            "miniseries",
        }
        if lowered in generic_equals:
            return True
        return False
