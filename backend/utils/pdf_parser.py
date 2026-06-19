"""
PDF Parser — auto-detectie van kolomposities
Werkt voor ZR, Artex, Eijffinger en andere leveranciers met tabelstructuur.
"""

import re
import pdfplumber

# ZR-specifieke kolomgrenzen (fallback)
ZR_COLS = {
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

SKIP_WORDS = {
    'Item', 'no.', 'Article', '€/m', 'excl.', 'RRP', 'Colors', 'Usable',
    'Repeat', 'Martindale', 'Composition', '%', 'Weighted', 'Features',
    'VAT', 'incl.', 'width', 'cm', '(approx.)', 'tape', 'TABLE', 'OF',
    'CONTENTS', 'PRICELIST', 'Alphabetical', 'Listing', 'Instructions',
    'Guidelines', 'Contact', 'General', 'Terms', 'Conditions',
    'Page', 'page',
}

ITEM_NO_RE = re.compile(r'^\d{4,6}$')  # 4-6 cijfers (ZR=5, Artex kan anders zijn)
PRICE_RE   = re.compile(r'^\d+[.,]\d{2}$')


def _detect_columns(page) -> dict | None:
    """
    Detecteer kolomgrenzen door de header-rij te vinden.
    Zoekt naar rijen met 'Item' + 'Article' + '€' of 'Price'.
    Geeft None als geen header gevonden.
    """
    words = page.extract_words()
    if not words:
        return None

    # Groepeer per y-rij
    rows = {}
    for w in words:
        y = round(w['top'] / 4) * 4
        rows.setdefault(y, []).append(w)

    for y in sorted(rows.keys()):
        texts = [w['text'].lower() for w in rows[y]]
        # Header herkend als rij met 'item' of artikelnummer-achtige woorden
        if ('item' in texts or 'article' in texts or 'artikel' in texts) and \
           any(t in texts for t in ['€/m', 'price', 'prijs', 'excl']):
            # Bouw kolomgrenzen op basis van x-posities van headers
            cols = {}
            for w in sorted(rows[y], key=lambda x: x['x0']):
                t = w['text'].lower()
                x = w['x0']
                if t in ('item', 'art.', 'artikel', 'nr', 'no.'):
                    if 'item_no' not in cols:  # eerste match wint — 'Item' (x=31) mag niet overschreven worden door 'no.' (x=44)
                        cols['item_no'] = x
                elif t in ('article', 'artikel', 'naam', 'name', 'omschrijving'):
                    cols['article'] = x
                elif '€' in w['text'] or t in ('price', 'prijs', 'excl.'):
                    if 'price_excl' not in cols:
                        cols['price_excl'] = x
                    else:
                        cols['price_rrp'] = x
                elif t in ('colors', 'kleuren', 'col.', 'col'):
                    cols['colors'] = x
                elif t in ('usable', 'width', 'breedte', 'breed'):
                    cols['width_cm'] = x
                elif t in ('repeat', 'rapport'):
                    cols['repeat'] = x
                elif t in ('martindale',):
                    cols['martindale'] = x
                elif t in ('composition', 'samenstelling', 'comp.'):
                    cols['composition'] = x
                elif t in ('features', 'kenmerken'):
                    cols['features'] = x
            if cols:
                return cols
    return None


def _build_col_ranges(col_starts: dict, page_width: float = 600) -> dict:
    """Converteer startposities naar (x0, x1) ranges."""
    keys = list(col_starts.keys())
    xs = [col_starts[k] for k in keys]
    ranges = {}
    for i, key in enumerate(keys):
        x0 = xs[i]
        x1 = xs[i + 1] if i + 1 < len(xs) else page_width
        ranges[key] = (x0, x1)
    return ranges


def _classify_x(x: float, cols: dict) -> str | None:
    for col, (x0, x1) in cols.items():
        if x0 <= x < x1:
            return col
    return None


def _parse_page(page, cols: dict) -> list[dict]:
    words = page.extract_words()
    if not words:
        return []

    rows: dict[int, list] = {}
    for w in words:
        if w['text'] in SKIP_WORDS:
            continue
        y = round(w['top'] / 4) * 4
        rows.setdefault(y, []).append(w)

    items = []
    current = None
    col_keys = list(cols.keys())

    for y in sorted(rows.keys()):
        line = sorted(rows[y], key=lambda w: w['x0'])
        if not line:
            continue
        first = line[0]

        if ITEM_NO_RE.match(first['text']):
            if current and current.get('item_no'):
                items.append(current)
            current = {col: [] for col in col_keys}
            for w in line:
                col = _classify_x(w['x0'], cols)
                if col:
                    current[col].append(w['text'])
        elif current:
            for w in line:
                col = _classify_x(w['x0'], cols)
                if col and col != 'item_no':
                    current[col].append(w['text'])

    if current and current.get('item_no'):
        items.append(current)

    return items


def _flatten(raw: dict) -> dict:
    repeat = raw.get('repeat', [])
    martindale_raw = ' '.join(raw.get('martindale', [])).replace('.', '')
    martindale = int(martindale_raw) if martindale_raw.isdigit() else None

    price_excl_str = ' '.join(raw.get('price_excl', [])).replace(',', '.')
    price_rrp_str  = ' '.join(raw.get('price_rrp', [])).replace(',', '.')

    try:
        price_excl = float(price_excl_str) if price_excl_str else None
    except ValueError:
        price_excl = None

    try:
        price_rrp = float(price_rrp_str) if price_rrp_str else None
    except ValueError:
        price_rrp = None

    article_parts = raw.get('article', [])
    composition_parts = ' '.join(raw.get('composition', []))
    is_fr = 'FR' in ' '.join(article_parts) or 'FR' in composition_parts
    has_cs = 'CS' in composition_parts

    # Cleanup samenstelling: verwijder layout-artefacten die uit de features-kolom lekken
    COMPOSITION_NOISE = {'Optional', 'optional', 'Weighted', 'weighted', 'Features', 'features'}
    composition_words = raw.get('composition', [])
    composition_words = [w for w in composition_words
                         if w not in COMPOSITION_NOISE
                         and not re.match(r'^-+$', w)]  # filter "---"
    composition = re.sub(r'\bCS\b', '', ' '.join(composition_words)).strip()
    composition = re.sub(r'\s+', ' ', composition).strip()  # normaliseer dubbele spaties

    # Breedte: alleen het eerste numerieke token (voorkomt "300 16" artefacten)
    width_raw = raw.get('width_cm', [])
    width_cm = ''
    for tok in width_raw:
        clean = tok.replace(',', '.').strip()
        try:
            float(clean)
            width_cm = clean
            break
        except ValueError:
            continue

    missing = []
    if not width_cm:
        missing.append('breedte')
    if not composition:
        missing.append('samenstelling')
    if not ' '.join(raw.get('colors', [])):
        missing.append('kleuren')
    # rapport is optioneel — effen stoffen hebben geen patroonrapport
    # if not repeat:
    #     missing.append('rapport')

    return {
        'item_no':        ' '.join(raw.get('item_no', [])),
        'article':        ' '.join(article_parts),
        'price_excl':     price_excl,
        'price_rrp':      price_rrp,
        'colors':         ' '.join(raw.get('colors', [])),
        'width_cm':       width_cm,
        'repeat_h_cm':    repeat[0] if repeat else '',
        'repeat_w_cm':    repeat[1] if len(repeat) > 1 else '',
        'martindale':     martindale,
        'composition':    composition,
        'flame_retardant': is_fr,
        'coating_cs':     has_cs,
        'features':       ' '.join(raw.get('features', [])),
        'missing_fields': missing,
    }


def parse_pricelist(pdf_path: str) -> dict:
    """
    Parse een leveranciers-pricelist PDF.
    Auto-detecteert kolomposities per pagina.
    Valt terug op ZR-layout als geen header gevonden.
    """
    raw_items = []
    current_cols = ZR_COLS.copy()  # default fallback

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for page in pdf.pages:
            # Probeer header te detecteren op elke pagina
            detected = _detect_columns(page)
            if detected:
                pw = page.width or 600
                current_cols = _build_col_ranges(detected, pw)

            page_items = _parse_page(page, current_cols)
            raw_items.extend(page_items)

    items = [_flatten(r) for r in raw_items if r.get('item_no')]

    # Dedupliceer op item_no (bij overlappende pagina's)
    seen = set()
    unique_items = []
    for item in items:
        item_no = item['item_no']
        # Filter garbage van contact/adres-pagina's:
        # Echte item-nummers zijn altijd puur numeriek (geen spaties, letters, of meer dan 6 cijfers)
        if not re.match(r'^\d{4,6}$', item_no):
            continue
        if item_no not in seen:
            seen.add(item_no)
            unique_items.append(item)

    total = len(unique_items)
    complete = sum(1 for i in unique_items if not i['missing_fields'])
    completion_pct = round(complete * 100 / total) if total else 0

    gap_items = [
        {
            'item_no':        i['item_no'],
            'article':        i['article'],
            'missing_fields': i['missing_fields'],
        }
        for i in unique_items if i['missing_fields']
    ]

    return {
        'items':            unique_items,
        'total_items':      total,
        'complete_items':   complete,
        'incomplete_items': total - complete,
        'completion_pct':   completion_pct,
        'gap_items':        gap_items,
    }


# Backwards-compatible alias
parse_zr_pricelist = parse_pricelist
