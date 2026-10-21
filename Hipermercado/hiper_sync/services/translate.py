"""Servico de traducao com termos protegidos.

Suporta dois providers (``openai`` e ``google``) com a mesma interface
``BaseTranslationService.translate(text, *, field_name, context)``. O ponto
chave e a protecao de termos: marcas, referencias, codigos, EAN13 e palavras
da lista ``KNOWN_TECH_TERMS`` (Bluetooth, HDMI, OLED, etc.) sao mascaradas
antes do envio e restauradas depois, garantindo que nao sao traduzidas nem
parafraseadas pelo modelo IA.
"""

import html
import logging
import re

import requests


_logger = logging.getLogger(__name__)


# Termos tecnicos comuns que nao devem ser traduzidos -- protegidos
# automaticamente em todos os textos enviados aos provedores.
KNOWN_TECH_TERMS = [
    "A+++",
    "A++",
    "A+",
    "AI",
    "Bluetooth",
    "BTU",
    "Dolby Atmos",
    "Dolby Vision",
    "FHD",
    "Full HD",
    "Google TV",
    "HD",
    "HDMI",
    "HDR",
    "Hz",
    "LED",
    "Mini LED",
    "NFC",
    "OLED",
    "QLED",
    "SSD",
    "Smart TV",
    "UHD",
    "USB",
    "USB-C",
    "Wi-Fi",
    "WiFi",
]

UNIT_PATTERNS = [
    r"\b\d+(?:[.,]\d+)?\s?(?:cm|mm|m|kg|g|gr|l|lt|ml|w|kw|v|hz|mah|btu|db|gb|tb|rpm)\b",
    r"\b\d+(?:[.,]\d+)?\"",
    r"\b[A-Z]{1,5}-[A-Z0-9\-\/+.]{1,}\b",
]


class BaseTranslationService:
    def __init__(self, source_lang, target_lang):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self._cache = {}
        self._disabled = False
        self._warning = False

    def cache_key(self, text, field_name, context):
        provider = getattr(self, "provider_name", self.__class__.__name__)
        model = getattr(self, "model", False)
        protected_terms = tuple(context.get("protected_terms") or [])
        return (provider, model, self.source_lang, self.target_lang, field_name, protected_terms, text)

    def translate(self, text, field_name=False, context=None):
        if not text:
            return text
        if self._disabled:
            _logger.warning(
                "%s translation disabled; returning source field=%s",
                getattr(self, "provider_name", self.__class__.__name__),
                field_name or "-",
            )
            return text
        context = context or {}
        cache_key = self.cache_key(text, field_name, context)
        if cache_key in self._cache:
            _logger.debug(
                "%s translation cache hit field=%s chars=%s",
                getattr(self, "provider_name", self.__class__.__name__),
                field_name or "-",
                len(text),
            )
            return self._cache[cache_key]

        protected_text, replacements = self._protect_terms(text, context)
        try:
            translated = self._translate_text(protected_text, field_name=field_name, context=context) or text
        except requests.RequestException as exc:
            translated = text
            self._disable_due_to_error(exc)
        except Exception as exc:
            translated = text
            self._disable_due_to_error(exc)
        translated = html.unescape(translated)
        translated = self._restore_terms(translated, replacements)
        if translated.strip() == text.strip():
            _logger.info(
                "%s translation unchanged field=%s chars=%s",
                getattr(self, "provider_name", self.__class__.__name__),
                field_name or "-",
                len(text),
            )
        self._cache[cache_key] = translated
        return translated

    def _translate_text(self, text, field_name=False, context=None):
        raise NotImplementedError()

    def _protect_terms(self, text, context):
        replacements = {}
        protected_terms = list(context.get("protected_terms") or [])
        protected_terms.extend(self._extract_regex_terms(text))
        seen = set()
        ordered_terms = []
        for term in protected_terms:
            cleaned = str(term or "").strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            ordered_terms.append(cleaned)
        ordered_terms.sort(key=len, reverse=True)

        protected_text = text
        for index, term in enumerate(ordered_terms, start=1):
            if term not in protected_text:
                continue
            placeholder = "__HIPER_TERM_%s__" % index
            protected_text = protected_text.replace(term, placeholder)
            replacements[placeholder] = term
        return protected_text, replacements

    def _restore_terms(self, text, replacements):
        restored = text
        for placeholder, term in replacements.items():
            restored = restored.replace(placeholder, term)
        return restored

    def _extract_regex_terms(self, text):
        regex_terms = []
        for known_term in KNOWN_TECH_TERMS:
            if known_term in text:
                regex_terms.append(known_term)
        for pattern in UNIT_PATTERNS:
            regex_terms.extend(re.findall(pattern, text, flags=re.IGNORECASE))
        return regex_terms

    def _disable_due_to_error(self, exc):
        if self._warning:
            self._disabled = True
            return
        provider = getattr(self, "provider_name", self.__class__.__name__).capitalize()
        error_text = str(exc).strip() or exc.__class__.__name__
        self._warning = "%s translation skipped: %s" % (provider, error_text)
        self._disabled = True
        _logger.warning(self._warning)

    def get_warning(self):
        return self._warning


class GoogleTranslateService(BaseTranslationService):
    provider_name = "google"

    def __init__(self, api_key, source_lang, target_lang):
        super().__init__(source_lang, target_lang)
        self.api_key = api_key

    def _translate_text(self, text, field_name=False, context=None):
        response = requests.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": self.api_key},
            data={
                "q": text,
                "source": self.source_lang,
                "target": self.target_lang,
                "format": "html",
            },
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        return (
            payload.get("data", {})
            .get("translations", [{}])[0]
            .get("translatedText")
            or text
        )


class OpenAITranslateService(BaseTranslationService):
    provider_name = "openai"

    def __init__(self, api_key, source_lang, target_lang, model):
        super().__init__(source_lang, target_lang)
        self.api_key = api_key
        self.model = self._normalize_model(model)

    def _normalize_model(self, model):
        cleaned = str(model or "").strip()
        if not cleaned:
            return "gpt-4.1-mini"
        normalized = re.sub(r"\s+", "-", cleaned.lower())
        normalized = normalized.replace("gpt4", "gpt-4")
        normalized = re.sub(r"gpt-?4\.?1[-_ ]?mini", "gpt-4.1-mini", normalized)
        normalized = re.sub(r"gpt-?4\.?1[-_ ]?nano", "gpt-4.1-nano", normalized)
        normalized = re.sub(r"gpt-?4\.?1$", "gpt-4.1", normalized)
        return normalized

    def _translate_text(self, text, field_name=False, context=None):
        context = context or {}
        prompt = (
            "Translate ecommerce product content from {source} to {target}. "
            "Return only the translated text. "
            "Preserve HTML structure exactly. "
            "Do not translate placeholders like __HIPER_TERM_1__. "
            "Do not translate brand names, model codes, EANs, references, sizes, units, or technical acronyms. "
            "Do not invent marketing language. "
            "Keep the wording natural in Portuguese while staying faithful to the source."
        ).format(source=self.source_lang, target=self.target_lang)
        if (self.target_lang or "").lower().startswith("pt"):
            prompt += (
                " Use European Portuguese (pt-PT), never Brazilian Portuguese (pt-BR). "
                "Prefer wording, spelling, and product terminology natural in Portugal."
            )
        if field_name == "name_pt":
            prompt += (
                " Product names must stay concise and must preserve brand-first naming when present. "
                "Translate common nouns and adjectives in product names, but keep brand/model codes, "
                "measurements, units, and technical acronyms unchanged."
            )

        translated = self._call_openai(prompt, text, field_name=field_name)
        if self._should_retry_translation(text, translated, field_name=field_name):
            retry_prompt = (
                f"{prompt} If the output would be identical to the input, translate any normal words "
                "that are clearly in the source language while still preserving brand/model codes, "
                "units, measurements, and technical acronyms."
            )
            translated_retry = self._call_openai(retry_prompt, text, field_name=field_name, retry=True)
            if translated_retry:
                return translated_retry
        return translated or text

    def _call_openai(self, prompt, text, field_name=False, retry=False):
        _logger.info(
            "OpenAI translate request model=%s field=%s retry=%s chars=%s source=%s target=%s",
            self.model,
            field_name or "-",
            bool(retry),
            len(text or ""),
            self.source_lang,
            self.target_lang,
        )
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": "Bearer %s" % self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "instructions": prompt,
                "input": text,
                "text": {
                    "format": {"type": "text"},
                    "verbosity": "medium",
                },
                "truncation": "auto",
            },
            timeout=180,
        )
        if not response.ok:
            error_body = response.text.strip()
            if error_body:
                raise requests.HTTPError(
                    "OpenAI translation failed (%s): %s" % (response.status_code, error_body[:1200]),
                    response=response,
                )
        response.raise_for_status()
        payload = response.json()
        output_text = payload.get("output_text")
        if output_text:
            return output_text.strip()
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"].strip()
        return ""

    def _should_retry_translation(self, source, translated, field_name=False):
        if not source:
            return False
        if not translated:
            return True
        if source.strip() != translated.strip():
            return False
        if field_name not in {"name_pt", "description_pt", "description_short_pt", "category", "sub_category"}:
            return False
        if (self.source_lang or "").lower() == (self.target_lang or "").lower():
            return False
        if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", source):
            return False
        return True


def build_translation_service(provider, api_key, source_lang, target_lang, model=False):
    if not provider or not api_key:
        return False
    if provider == "openai":
        return OpenAITranslateService(api_key, source_lang, target_lang, model)
    if provider == "google":
        return GoogleTranslateService(api_key, source_lang, target_lang)
    return False
