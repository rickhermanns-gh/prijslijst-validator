"""
Parser Router — detecteert formaat en leverancier, stuurt door naar juiste parser.
"""

import os


def parse_pricelist(file_path: str, supplier: str = '') -> dict:
    """
    Detecteer bestandstype en leverancier, parse naar BMS-formaat.
    Geeft altijd een dict terug met items, stats en gap_items.
    """
    ext = os.path.splitext(file_path)[1].lower()
    supplier_lower = supplier.lower()
    filename_lower = os.path.basename(file_path).lower()

    if ext in ('.xlsx', '.xls'):
        return _route_xlsx(file_path, supplier_lower, filename_lower)
    elif ext == '.pdf':
        return _route_pdf(file_path, supplier_lower, filename_lower)
    else:
        raise ValueError(f"Niet-ondersteund bestandstype: {ext}")


def _route_xlsx(path: str, supplier: str, filename: str) -> dict:
    from utils.xlsx_parser import parse_zr_xlsx, parse_artex_xlsx

    # Artex: meerdere sheets, Nederlandse kolomnamen
    if 'artex' in supplier or 'artex' in filename or \
       'artelux' in filename or 'loft79' in filename or 'kendix' in filename:
        return parse_artex_xlsx(path)

    # ZR (Zimmer + Rohde)
    if 'zr' in supplier or 'zimmer' in supplier or 'zr' in filename or 'pricesheet' in filename:
        return parse_zr_xlsx(path)

    # Probeer ZR-formaat als fallback voor onbekende XLSX
    try:
        result = parse_zr_xlsx(path)
        if result['total_items'] > 0:
            return result
    except Exception:
        pass

    # Probeer Artex-formaat als tweede fallback
    return parse_artex_xlsx(path)


def _route_pdf(path: str, supplier: str, filename: str) -> dict:
    from utils.pdf_parser import parse_pricelist as parse_pdf_generic
    from utils.xlsx_parser import (
        parse_eijffinger_pdf,
        parse_eijffinger_voering_pdf,
        parse_eijffinger_stoffen_pdf,
    )

    if 'eijffinger' in supplier or 'eijffinger' in filename:
        # Voeringstoffen: 7699-x itemnummers, breedte + samenstelling
        if 'voering' in filename:
            return parse_eijffinger_voering_pdf(path)
        # Stoffencollecties: 3-koloms, alleen collectienaam + prijs
        if 'stoff' in filename:
            return parse_eijffinger_stoffen_pdf(path)
        # Default: behang (6-cijferige itemnummers, WALLPOWER)
        return parse_eijffinger_pdf(path)

    # ZR, Artex, en alle andere textielleveranciers → generieke PDF parser
    return parse_pdf_generic(path)
