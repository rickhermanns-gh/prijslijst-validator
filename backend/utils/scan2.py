"""
Scan 2 — Pattern Matching Enrichment
Tweede pass die ontbrekende velden aanvult op basis van:
1. Compositie-afkortingen uitschrijven (100%SE → 100% Silk)
2. Breedte extraheren uit artikelnaam als die ontbreekt
3. Kleuren extraheren uit artikel/features als die ontbreken
4. FR/CS flags opnieuw detecteren uit alle tekstvelden
5. missing_fields herberekenen na enrichment
"""

import re
import copy

# ─── Compositie-afkortingen ────────────────────────────────────────────────────
# ZR gebruikt Engelse afkortingen (Engelse pricelist)
COMPOSITION_ABBREVS = {
    'SE':  'Silk',
    'PES': 'Polyester',
    'CO':  'Cotton',
    'WO':  'Wool',
    'LI':  'Linen',
    'VI':  'Viscose',
    'PA':  'Polyamide',
    'AC':  'Acrylic',
    'CU':  'Cupro',
    'EL':  'Elastane',
    'PP':  'Polypropylene',
    'MA':  'Modal',
    'MD':  'Modal',
    'AR':  'Aramid',
    'CV':  'Viscose',
    'HL':  'Hemp',
    'LY':  'Lyocell',
    'TE':  'Lyocell',
    'NY':  'Nylon',
    'PL':  'Polyester',
    'AF':  'Acrylic',
    'AL':  'Alpaca',
    'AN':  'Angora',
    'CA':  'Cashmere',
    'KM':  'Camel',
    'MT':  'Metal',
    'PC':  'Cotton-Polyester',
    'RA':  'Ramie',
    'SI':  'Silk',
    'TA':  'Tencel',
    'TR':  'Triacetate',
    'PAN': 'Polyacrylnitrile',
    'CLY': 'Lyocell',
    'CMD': 'Modal',
    # Coating / technische materialen
    'PVC': 'PVC',
    'PU':  'Polyurethane',
    'HA':  'Hemp',
    'MTF': 'Metallic Fiber',
    'WM':  'Wool-Mohair',
    'ST':  'Steel',
}

# Regex: optioneel spatie, getal%, AFKORTING (bijv. "100%SE", "60% PES", "55%LI")
_ABBREV_RE = re.compile(
    r'(\d+)\s*%\s*([A-Z]{2,4})(?=\s|$|/|,|;)',
    re.IGNORECASE,
)

# Breedte-patronen in artikelnaam: "140cm", "140 cm", "140", "280", "300", "320"
_WIDTH_RE = re.compile(r'\b(100|120|130|137|138|140|150|160|200|280|290|300|310|320|330|340|350|360)\s*(?:cm)?\b', re.IGNORECASE)

# Kleurenpatroon: "12 col", "12 colours", "12 colors", "12 col."
_COLORS_RE = re.compile(r'\b(\d{1,3})\s*col(?:ou?rs?)?\b', re.IGNORECASE)


# ─── Hulpfuncties ─────────────────────────────────────────────────────────────

def _expand_composition(raw: str) -> str:
    """
    Schrijf compositie-afkortingen uit.
    "100%SE" → "100% Silk"
    "60%PES 40%CO" → "60% Polyester 40% Cotton"
    Geeft ongewijzigde string terug als geen patroon matcht.
    """
    if not raw:
        return raw

    def replace_match(m):
        pct = m.group(1)
        abbrev = m.group(2).upper()
        expanded = COMPOSITION_ABBREVS.get(abbrev)
        if expanded:
            return f"{pct}% {expanded}"
        return m.group(0)  # onbekende afkorting ongewijzigd laten

    result = _ABBREV_RE.sub(replace_match, raw)
    # Normaliseer dubbele spaties
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def _extract_width_from_text(text: str) -> str:
    """Zoek een breedtemaat (cm) in een tekststring."""
    if not text:
        return ''
    m = _WIDTH_RE.search(text)
    return m.group(1) if m else ''


def _extract_colors_from_text(text: str) -> str:
    """Zoek aantal kleuren in een tekststring."""
    if not text:
        return ''
    m = _COLORS_RE.search(text)
    return m.group(1) if m else ''


def _recompute_missing(item: dict) -> list[str]:
    """Herbereken missing_fields op basis van actuele item-waarden."""
    missing = []
    if not item.get('width_cm'):
        missing.append('breedte')
    if not item.get('composition'):
        missing.append('samenstelling')
    # Kleuren alleen als verplicht markeren als het een textielitem is
    # (wallpaper-items hoeven dit soms niet te hebben)
    if not item.get('colors'):
        missing.append('kleuren')
    # Prijs is altijd verplicht
    if not item.get('price_rrp') and not item.get('price_excl'):
        missing.append('prijs')
    return missing


def _recompute_missing_pdf_style(item: dict) -> list[str]:
    """
    PDF-stijl missing check (breedte + samenstelling + kleuren, geen prijs).
    Gebruik dit als originele missing_fields geen 'prijs' bevat.
    """
    missing = []
    if not item.get('width_cm'):
        missing.append('breedte')
    if not item.get('composition'):
        missing.append('samenstelling')
    if not item.get('colors'):
        missing.append('kleuren')
    return missing


# ─── Hoofd-enrichment ─────────────────────────────────────────────────────────

def enrich_items(items: list[dict]) -> dict:
    """
    Verwerk een lijst items uit scan1_result en probeer ontbrekende velden aan te vullen.

    Retourneert:
    {
        "items": [...],              # verbeterde items
        "total_items": int,
        "complete_items": int,
        "incomplete_items": int,
        "completion_percentage": int,
        "items_improved": int,       # items waar minstens 1 veld aangevuld is
        "fields_filled": {           # per veldtype hoeveel keer aangevuld
            "samenstelling": int,
            "breedte": int,
            "kleuren": int,
            "fr_flag": int,
        }
    }
    """
    enriched = []
    stats = {
        'items_improved': 0,
        'fields_filled': {
            'samenstelling': 0,
            'breedte': 0,
            'kleuren': 0,
            'fr_flag': 0,
        }
    }

    # Detecteer of we PDF-stijl missing_fields gebruiken (geen 'prijs' in missings)
    # door te kijken naar het eerste item met missing_fields
    uses_pdf_style = True
    for it in items:
        if 'prijs' in it.get('missing_fields', []):
            uses_pdf_style = False
            break

    for item in items:
        it = copy.deepcopy(item)
        improved = False
        original_missing = set(it.get('missing_fields', []))

        # ── 1. Compositie uitschrijven ──────────────────────────────────────
        comp = it.get('composition', '')
        if comp:
            expanded = _expand_composition(comp)
            if expanded != comp:
                it['composition'] = expanded
                if 'samenstelling' not in original_missing:
                    # Was al aanwezig maar nu genormaliseerd — telt als verbeterd
                    improved = True

        # ── 2. Breedte extraheren uit artikelnaam als ontbreekt ─────────────
        if not it.get('width_cm'):
            article = it.get('article', '')
            features = it.get('features', '')
            width = _extract_width_from_text(article) or _extract_width_from_text(features)
            if width:
                it['width_cm'] = width
                stats['fields_filled']['breedte'] += 1
                improved = True

        # ── 3. Kleuren extraheren als ontbreekt ─────────────────────────────
        if not it.get('colors'):
            article = it.get('article', '')
            features = it.get('features', '')
            colors = _extract_colors_from_text(article) or _extract_colors_from_text(features)
            if colors:
                it['colors'] = colors
                stats['fields_filled']['kleuren'] += 1
                improved = True

        # ── 4. FR/CS flags opnieuw detecteren ──────────────────────────────
        all_text = ' '.join([
            it.get('article', ''),
            it.get('features', ''),
            it.get('composition', ''),
        ]).upper()

        new_fr = bool(re.search(r'\bFR\b', all_text))
        new_cs = bool(re.search(r'\bCS\b', all_text))

        if new_fr and not it.get('flame_retardant'):
            it['flame_retardant'] = True
            stats['fields_filled']['fr_flag'] += 1
            improved = True
        if new_cs and not it.get('coating_cs'):
            it['coating_cs'] = True
            improved = True

        # ── 5. Samenstelling tellen (na expansie) ──────────────────────────
        if it.get('composition') and 'samenstelling' in original_missing:
            stats['fields_filled']['samenstelling'] += 1
            improved = True

        # ── 6. Herbereken missing_fields ────────────────────────────────────
        if uses_pdf_style:
            it['missing_fields'] = _recompute_missing_pdf_style(it)
        else:
            it['missing_fields'] = _recompute_missing(it)

        if improved:
            stats['items_improved'] += 1

        enriched.append(it)

    # ── Stats berekenen ──────────────────────────────────────────────────────
    total = len(enriched)
    complete = sum(1 for i in enriched if not i.get('missing_fields'))
    incomplete = total - complete
    pct = round(complete / total * 100) if total > 0 else 0

    return {
        'items': enriched,
        'total_items': total,
        'complete_items': complete,
        'incomplete_items': incomplete,
        'completion_percentage': pct,
        'items_improved': stats['items_improved'],
        'fields_filled': stats['fields_filled'],
    }
