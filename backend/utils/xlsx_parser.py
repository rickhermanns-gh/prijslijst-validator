"""
XLSX Parser — ZR en Artex formaten
Detecteert leverancier op basis van kolomkoppen en parseert naar BMS-formaat.
"""

import openpyxl
import re


def _clean(val) -> str:
    if val is None:
        return ''
    return str(val).strip()


def _missing_fields(item: dict) -> list[str]:
    missing = []
    if not item.get('width_cm'):
        missing.append('breedte')
    if not item.get('composition'):
        missing.append('samenstelling')
    if not item.get('price_rrp') and not item.get('price_excl'):
        missing.append('prijs')
    return missing


# ─── ZR XLSX ──────────────────────────────────────────────────────────────────

ZR_COL_MAP = {
    'item no.':           'item_no',
    'item no':            'item_no',
    'item':               'article',
    'variant':            'variant',
    'purchase price':     'price_excl',
    'excl.':              'price_excl',
    'rrp':                'price_rrp',
    'incl. vat':          'price_rrp',
    'width':              'width_cm',
    'width cm':           'width_cm',
    'gram':               'weight_g',
    'no. colors':         'colors',
    'no colors':          'colors',
    'composition %':      'composition',
    'composition':        'composition',
    'repeat \nheight':    'repeat_h_cm',
    'repeat \nwidth':     'repeat_w_cm',
    'repeat height':      'repeat_h_cm',
    'repeat width':       'repeat_w_cm',
    'additional':         'features',
}


def _map_zr_header(headers: list) -> dict:
    """Geeft {col_index: field_name} mapping voor ZR formaat."""
    mapping = {}
    for i, h in enumerate(headers):
        if h is None:
            continue
        key = str(h).lower().strip().replace('\n', ' ')
        for pattern, field in ZR_COL_MAP.items():
            if key.startswith(pattern.lower()):
                if field not in mapping.values():  # eerste match wint
                    mapping[i] = field
                break
    return mapping


def parse_zr_xlsx(path: str) -> dict:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return _empty_result()

    # Eerste niet-lege rij = header
    header_row = None
    header_idx = 0
    for i, row in enumerate(rows):
        if any(c is not None for c in row):
            header_row = row
            header_idx = i
            break

    if header_row is None:
        return _empty_result()

    col_map = _map_zr_header(list(header_row))

    items = []
    for row in rows[header_idx + 1:]:
        if not any(c is not None for c in row):
            continue

        item = {}
        for col_idx, field in col_map.items():
            if col_idx < len(row):
                item[field] = _clean(row[col_idx])

        item_no = item.get('item_no', '')
        if not item_no or not re.match(r'^\d+', item_no):
            continue

        # Normaliseer
        item['item_no'] = item_no
        item['repeat_h_cm'] = item.get('repeat_h_cm', '')
        item['repeat_w_cm'] = item.get('repeat_w_cm', '')
        item['martindale'] = None
        item['flame_retardant'] = 'FR' in item.get('features', '').upper() or \
                                   'FR' in item.get('composition', '').upper()
        item['coating_cs'] = 'CS' in item.get('composition', '').upper()
        item['missing_fields'] = _missing_fields(item)

        # Verwijder 0-waarden voor repeat
        if item.get('repeat_h_cm') in ('0', '0.0'):
            item['repeat_h_cm'] = ''
        if item.get('repeat_w_cm') in ('0', '0.0'):
            item['repeat_w_cm'] = ''

        items.append(item)

    return _build_result(items)


# ─── ARTEX XLSX ───────────────────────────────────────────────────────────────

ARTEX_COL_MAP = {
    'naam':                  'article',
    'hoogte / breedte':      'width_cm',
    'hoogte/breedte':        'width_cm',
    'rapport ca. cm':        'repeat_h_cm',
    'rapport':               'repeat_h_cm',
    'gewicht gr/m1':         'weight_g',
    'gewicht':               'weight_g',
    'wasadvies':             'wash_advice',
    'samenstelling in %':    'composition',
    'samenstelling':         'composition',
    'vlamvertragend':        'flame_retardant_raw',
    'kamerhoog':             'full_height',
    'verkoopprijs incl':     'price_rrp',
    'verkoopprijs':          'price_rrp',
}


def _map_artex_header(headers: list) -> dict:
    mapping = {}
    for i, h in enumerate(headers):
        if h is None:
            continue
        key = str(h).lower().strip()
        for pattern, field in ARTEX_COL_MAP.items():
            if key.startswith(pattern.lower()):
                if field not in mapping.values():
                    mapping[i] = field
                break
    return mapping


def parse_artex_xlsx(path: str) -> dict:
    wb = openpyxl.load_workbook(path, data_only=True)

    all_items = []
    seen_names = set()  # Artex heeft geen unieke artikel nummers

    for sheet_name in wb.sheetnames:
        # Sla alfabet-overzicht sheet over
        if 'alfabet' in sheet_name.lower() or 'overzicht' in sheet_name.lower():
            continue

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        # Zoek header rij
        header_row = None
        header_idx = 0
        for i, row in enumerate(rows[:5]):
            if row[0] is not None and str(row[0]).lower().strip() in ('naam', 'name', 'artikel'):
                header_row = row
                header_idx = i
                break
            if row[0] is not None and i == 0:
                header_row = row
                header_idx = i

        if header_row is None:
            continue

        col_map = _map_artex_header(list(header_row))
        if not col_map:
            continue

        for row_idx, row in enumerate(rows[header_idx + 1:], header_idx + 1):
            if not any(c is not None for c in row):
                continue

            item = {}
            for col_idx, field in col_map.items():
                if col_idx < len(row):
                    item[field] = _clean(row[col_idx])

            name = item.get('article', '')
            if not name or name.lower() in ('naam', 'name'):
                continue

            # Unieke sleutel: naam + sheet
            key = f"{sheet_name}::{name}"
            if key in seen_names:
                continue
            seen_names.add(key)

            # Artex heeft geen artikelnummers — gebruik naam als ID
            item['item_no'] = f"{sheet_name[:3].upper()}-{name}"
            item['collection'] = sheet_name
            item['repeat_h_cm'] = item.get('repeat_h_cm', '')
            item['repeat_w_cm'] = ''
            item['martindale'] = None
            item['price_excl'] = ''

            # Vlamvertragend
            fr_raw = item.get('flame_retardant_raw', '')
            cs_in_comp = 'trevira cs' in item.get('composition', '').lower() or \
                         'cs' in item.get('composition', '').lower()
            item['flame_retardant'] = bool(fr_raw and fr_raw.strip() not in ('', '-', 'None'))
            item['coating_cs'] = cs_in_comp
            item['missing_fields'] = _missing_fields(item)

            all_items.append(item)

    return _build_result(all_items)


# ─── EIJFFINGER PDF ───────────────────────────────────────────────────────────

def parse_eijffinger_pdf(path: str) -> dict:
    """Eijffinger: behang, twee kolommen per pagina, 6-cijferig itemnummer."""
    import pdfplumber

    ITEM_RE = re.compile(r'^\d{6}$')

    # Twee kolommen: links x≈38, rechts x≈293
    LEFT_COLS  = {'item_no': (0, 80), 'width_cm': (80, 160), 'length_m': (160, 210),
                  'price_roll': (210, 285), 'price_m2': (285, 293)}
    RIGHT_COLS = {'item_no': (293, 335), 'width_cm': (335, 415), 'length_m': (415, 460),
                  'price_roll': (460, 535), 'price_m2': (535, 600)}

    def classify(x, cols):
        for field, (x0, x1) in cols.items():
            if x0 <= x < x1:
                return field
        return None

    def parse_side(words, cols):
        rows = {}
        for w in words:
            y = round(w['top'] / 4) * 4
            rows.setdefault(y, []).append(w)

        items = []
        current_collection = ''
        for y in sorted(rows.keys()):
            line = sorted(rows[y], key=lambda w: w['x0'])
            first = line[0]
            x0 = first['x0']

            # Collectienaam (geen nummer, staat ver links op eigen rij)
            if x0 >= cols['item_no'][0] and x0 < cols['item_no'][0] + 60:
                if ITEM_RE.match(first['text']):
                    item = {f: [] for f in cols}
                    for w in line:
                        f = classify(w['x0'], cols)
                        if f:
                            item[f].append(w['text'])
                    items.append(item)
                elif not any(c.isdigit() for c in first['text']):
                    current_collection = first['text']

        return items, current_collection

    all_items = []
    current_coll = ''

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue

            # Split in linker en rechter helft
            left_words  = [w for w in words if w['x0'] < 290]
            right_words = [w for w in words if w['x0'] >= 290]

            left_items, coll = parse_side(left_words, LEFT_COLS)
            if coll:
                current_coll = coll
            right_items, _ = parse_side(right_words, RIGHT_COLS)

            for raw in left_items + right_items:
                item_no = ' '.join(raw.get('item_no', []))
                if not ITEM_RE.match(item_no):
                    continue
                price_m2 = ' '.join(raw.get('price_m2', [])).replace('€', '').replace(',', '.').strip()
                price_roll = ' '.join(raw.get('price_roll', [])).replace('€', '').replace(',', '.').strip()
                try:
                    price_m2_f = float(price_m2) if price_m2 else None
                except ValueError:
                    price_m2_f = None

                all_items.append({
                    'item_no':        item_no,
                    'article':        current_coll,
                    'collection':     current_coll,
                    'width_cm':       ' '.join(raw.get('width_cm', [])),
                    'length_m':       ' '.join(raw.get('length_m', [])),
                    'repeat_h_cm':    '',
                    'repeat_w_cm':    '',
                    'composition':    '',
                    'martindale':     None,
                    'flame_retardant': False,
                    'coating_cs':     False,
                    'price_excl':     None,
                    'price_rrp':      price_m2_f,
                    'price_roll':     price_roll,
                    'colors':         '',
                    'missing_fields': ['samenstelling', 'rapport'] if not price_m2_f else ['samenstelling'],
                })

    # Dedup
    seen = set()
    unique = []
    for i in all_items:
        if i['item_no'] not in seen:
            seen.add(i['item_no'])
            unique.append(i)

    return _build_result(unique)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _empty_result() -> dict:
    return {'items': [], 'total_items': 0, 'complete_items': 0,
            'incomplete_items': 0, 'completion_pct': 0, 'gap_items': []}


def _build_result(items: list) -> dict:
    total = len(items)
    complete = sum(1 for i in items if not i.get('missing_fields'))
    pct = round(complete * 100 / total) if total else 0
    gap = [{'item_no': i['item_no'], 'article': i.get('article', ''),
            'missing_fields': i['missing_fields']}
           for i in items if i.get('missing_fields')]
    return {'items': items, 'total_items': total, 'complete_items': complete,
            'incomplete_items': total - complete, 'completion_pct': pct, 'gap_items': gap}
