"""
SAP Flat File Parser

Research basis:
SAP most commonly exports via transaction SE16/SE16N or SM30 to CSV/TXT.
For fuel & procurement, relevant tables are EKKO (purchase orders header),
EKPO (purchase order items), and MSEG (material document segments for goods movement).

Real SAP exports have:
- Semicolon or pipe delimiters (not comma) in European configs
- German column headers in some system locales (e.g. "Buchungsdatum" for posting date)
- Dates as YYYYMMDD or DD.MM.YYYY
- Quantities with comma as decimal separator in EU locales
- Plant codes (Werk) that are internal 4-char codes with no meaning without lookup
- Material numbers as 18-char padded strings
- Units: L (litre), KG, GAL, M3, KWH (SAP internal unit codes)

We handle: fuel purchases (diesel, petrol, LPG) and procurement items.
We do NOT handle: IDocs (require SAP middleware), OData (requires live SAP system),
multi-currency POs (complex FX handling out of scope).
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import io

# SAP internal unit → standard unit mapping
SAP_UNIT_MAP = {
    'L': 'litre',
    'LT': 'litre',
    'GAL': 'gallon_us',
    'GL': 'gallon_us',
    'KG': 'kg',
    'G': 'g',
    'M3': 'm3',
    'KWH': 'kwh',
    'TO': 'tonne',  # metric tonne in SAP
    'ST': 'unit',   # Stück = piece
}

# German → English column header map (common SAP locale exports)
GERMAN_HEADER_MAP = {
    'Buchungsdatum': 'posting_date',
    'Belegdatum': 'document_date',
    'Werk': 'plant_code',
    'Material': 'material_number',
    'Menge': 'quantity',
    'Mengeneinheit': 'unit',
    'Bewegungsart': 'movement_type',
    'Kostenstelle': 'cost_center',
    'Bezeichnung': 'description',
    'Lieferant': 'vendor',
    'Bestellnummer': 'po_number',
    'Wert': 'value',
    'Wahrung': 'currency',
    # English variants also present in mixed configs
    'Posting Date': 'posting_date',
    'Document Date': 'document_date',
    'Plant': 'plant_code',
    'Material Number': 'material_number',
    'Quantity': 'quantity',
    'Unit': 'unit',
    'Movement Type': 'movement_type',
    'Cost Center': 'cost_center',
    'Description': 'description',
    'Vendor': 'vendor',
    'PO Number': 'po_number',
    'Value': 'value',
    'Currency': 'currency',
}

# Material description keywords → fuel type classification
FUEL_KEYWORDS = {
    'diesel': ['diesel', 'dieselkraftstoff', 'gasoil', 'gas oil', 'hsd'],
    'petrol': ['petrol', 'benzin', 'gasoline', 'unleaded', 'ulp'],
    'lpg': ['lpg', 'propan', 'propane', 'butane', 'autogas'],
    'natural_gas': ['erdgas', 'natural gas', 'cng', 'lng', 'methane'],
    'heating_oil': ['heizol', 'heating oil', 'furnace oil', 'fo'],
}


def detect_delimiter(raw_text: str) -> str:
    """SAP exports use semicolons in EU locale, pipes in some configs, tabs in others."""
    first_line = raw_text.split('\n')[0]
    for delim in [';', '|', '\t', ',']:
        if delim in first_line:
            return delim
    return ','


def parse_sap_date(date_str: str) -> Optional[datetime]:
    """SAP uses YYYYMMDD or DD.MM.YYYY depending on system config."""
    if not date_str or pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    for fmt in ['%Y%m%d', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_sap_quantity(qty_str) -> Optional[float]:
    """EU locale uses comma as decimal, period as thousands separator: '1.234,56' → 1234.56"""
    if qty_str is None or (isinstance(qty_str, float) and np.isnan(qty_str)):
        return None
    qty_str = str(qty_str).strip()
    # EU format: 1.234,56
    if ',' in qty_str and '.' in qty_str:
        if qty_str.index('.') < qty_str.index(','):
            qty_str = qty_str.replace('.', '').replace(',', '.')
        else:
            qty_str = qty_str.replace(',', '')
    elif ',' in qty_str:
        qty_str = qty_str.replace(',', '.')
    try:
        return float(qty_str)
    except ValueError:
        return None


def classify_fuel(description: str, material_number: str = '') -> Optional[str]:
    """Best-effort fuel type from description text."""
    text = (description + ' ' + material_number).lower()
    for fuel_type, keywords in FUEL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return fuel_type
    return None


def parse_sap_file(file_content: bytes) -> list[dict]:
    """
    Main entry point. Returns list of parsed row dicts.
    Each dict has standardized keys ready for normalization.
    """
    raw_text = file_content.decode('utf-8', errors='replace')
    delimiter = detect_delimiter(raw_text)

    df = pd.read_csv(
        io.StringIO(raw_text),
        delimiter=delimiter,
        dtype=str,  # read everything as string; we parse types ourselves
        skipinitialspace=True,
    )

    # Normalize column headers
    df.columns = [GERMAN_HEADER_MAP.get(col.strip(), col.strip().lower().replace(' ', '_'))
                  for col in df.columns]

    records = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        # Strip whitespace from all string values (SAP pads many fields)
        row_dict = {k: v.strip() if isinstance(v, str) else v for k, v in row_dict.items()}

        quantity = parse_sap_quantity(row_dict.get('quantity'))
        unit_raw = str(row_dict.get('unit', '')).upper().strip()
        standard_unit = SAP_UNIT_MAP.get(unit_raw, unit_raw.lower())
        posting_date = parse_sap_date(row_dict.get('posting_date') or row_dict.get('document_date'))
        description = str(row_dict.get('description', ''))
        fuel_type = classify_fuel(description, str(row_dict.get('material_number', '')))

        records.append({
            '_row_index': idx,
            '_parse_ok': quantity is not None and posting_date is not None,
            '_parse_error': '' if (quantity is not None and posting_date is not None)
                           else f"quantity={row_dict.get('quantity')}, date={row_dict.get('posting_date')}",
            'source_type': 'sap',
            'activity_date': posting_date.isoformat() if posting_date else None,
            'quantity': quantity,
            'unit': standard_unit,
            'description': description,
            'fuel_type': fuel_type,
            'plant_code': row_dict.get('plant_code', ''),
            'material_number': row_dict.get('material_number', ''),
            'cost_center': row_dict.get('cost_center', ''),
            'vendor': row_dict.get('vendor', ''),
            'po_number': row_dict.get('po_number', ''),
            'value': parse_sap_quantity(row_dict.get('value')),
            'currency': row_dict.get('currency', ''),
            '_raw': row_dict,
        })

    return records
