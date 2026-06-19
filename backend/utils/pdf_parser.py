"""
PDF Parser — ZR pricelist structuur
Parseert tekst op basis van x-coördinaten (kolom-layout).
"""

import re
import pdfplumber

# Kolomgrenzen gebaseerd op ZR 2026 BENELUX layout
COLS = {
    'item_no':     (0,   62),
    'article':     (62,  155),
    'price_excl':  (155, 192),
    'price_rrp':   (192, 228),
    'colors':      (228, 260),
    'width_cm':    (260, 294),
    'repeat':      (294, 323),
    'martindale':  (323, 355),
    'composition': (355, 470),
    'features':    (470, 600),
}

# Woorden die deel uitmaken van de kolomheader of paginanavigatie
SKIP_WORDS = {
    'Item', 'no.', 'Article', '€/m', 'excl.', 'RRP', 'Colors', 'Usable',
    'Repeat', 'Martindale', 'Composition', '%', 'Weighted', 'Features',
    'VAT', 'incl.', 'width', 'cm', '(approx.)', 'tape', 'TABLE', 'OF',
    'CONTENTS', 'PRICELIST', 'Alphabetical', 'Listing', 'Instructions',
    'Guidelines', 'Contact', 'General', 'Terms', 'Conditions',
}

ITEM_NO_RE = re.compile(r'^\d{5}$')


def _classify_x(x: float) -> str | None:
    for col, (x0, x1) in COLS.items():
        if x0 <= x < x1:
            return col
    return None


def _parse_page(page) -> list[dict]:
    words = page.extract_words()
    if not words:
        return []

    # Groepeer woorden per y-rij (4px bins)
    rows: dict[int, list] = {}
    for w in words:
        if w['text'] in SKIP_WORDS:
            continue
        y = round(w['top'] / 4) * 4
        rows.setdefault(y, []).append(w)

    items = []
    current = None

    for y in sorted(rows.keys()):
        line = sorted(rows[y], key=lambda w: w['x0'])
        if not line:
            continue
        first = line[0]

        if ITEM_NO_RE.match(first['text']):
            # Sla vorig artikel op
            if current and current['item_no']:
                items.append(current)
            current = {col: [] for col in COLS}
            for w in line:
                col = _classify_x(w['x0'])
                if col:
                    current[col].append(w['text'])
        elif current:
            # Vervolgregel binnen huidig artikel (bv. repeat breedte op r2)
            for w in line:
                col = _classify_x(w['x0'])
                if col and col != 'item_no':
                    current[col].append(w['text'])

    if current and current['item_no']:
        items.append(current)

    return items


def _flatten(raw: dict) -> dict:
    repeat = raw['repeat']
    martindale_raw = ' '.join(raw['martindale']).replace('.', '')
    martindale = int(martindale_raw) if martindale_raw.isdigit() else None

    price_excl_str = ' '.join(raw['price_excl']).replace(',', '.')
    price_rrp_str = ' '.join(raw['price_rrp']).replace(',', '.')

    try:
        price_excl = float(price_excl_str) if price_excl_str else None
    except ValueError:
        price_excl = None

    try:
        price_rrp = float(price_rrp_str) if price_rrp_str else None
    except ValueError:
        price_rrp = None

    features = ' '.join(raw['features'])
    is_fr = 'FR' in ' '.join(raw['article']) or 'FR' in features
    has_cs = 'CS' in ' '.join(raw['composition'])

    composition_parts = ' '.join(raw['composition'])
    # Verwijder CS label uit compositie
    composition = re.sub(r'\bCS\b', '', composition_parts).strip()

    missing = []
    if not ' '.join(raw['width_cm']):
        missing.append('breedte')
    if not composition:
        missing.append('samenstelling')
    if not ' '.join(raw['colors']):
        missing.append('kleuren')
    if not repeat:
        missing.append('rapport')

    return {
        'item_no':       ' '.join(raw['item_no']),
        'article':       ' '.join(raw['article']),
        'price_excl':    price_excl,
        'price_rrp':     price_rrp,
        'colors':        ' '.join(raw['colors']),
        'width_cm':      ' '.join(raw['width_cm']),
        'repeat_h_cm':   repeat[0] if repeat else '',
        'repeat_w_cm':   repeat[1] if len(repeat) > 1 else '',
        'martindale':    martindale,
        'composition':   composition,
        'flame_retardant': is_fr,
        'coating_cs':    has_cs,
        'features':      features,
        'missing_fields': missing,
    }


def parse_zr_pricelist(pdf_path: str) -> dict:
    """
    Parse een ZR pricelist PDF.
    Geeft dict terug met items, statistieken en gap-analyse.
    """
    raw_items = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # Collectie-pagina's: skip eerste 14 (TOC/intro) en laatste (info/contact)
        for page in pdf.pages[14:min(62, total_pages)]:
            raw_items.extend(_parse_page(page))

    items = [_flatten(r) for r in raw_items if r['item_no']]

    total = len(items)
    complete = sum(1 for i in items if not i['missing_fields'])
    completion_pct = round(complete * 100 / total) if total else 0

    gap_items = [
        {
            'item_no':        i['item_no'],
            'article':        i['article'],
            'missing_fields': i['missing_fields'],
        }
        for i in items if i['missing_fields']
    ]

    return {
        'items':              items,
        'total_items':        total,
        'complete_items':     complete,
        'incomplete_items':   total - complete,
        'completion_pct':     completion_pct,
        'gap_items':          gap_items,
    }
