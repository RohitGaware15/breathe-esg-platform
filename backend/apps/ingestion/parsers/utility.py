"""
Utility Data Parser — Electricity Portal CSV Export

Research basis:
Major utility portals (MSEDCL, BESCOM, Tata Power, CESC in India; National Grid,
EDF, Enel internationally) export consumption data as CSV with consistent but
non-identical schemas. Key characteristics:

- Billing periods DON'T align with calendar months (e.g. 18-Jan to 21-Feb)
- Meter readings: opening + closing, or just consumption delta
- Units: kWh, MWh, kVAh (for industrial tariffs with power factor)
- Multiple meters per facility (HT and LT connections)
- Tariff components: energy charge, demand charge, fuel surcharge, taxes
- Contracted demand in kVA or kW separate from actual consumption

We handle: consumption data (kWh), billing period, meter ID, facility.
We do NOT handle: PDF bill parsing (complex, needs OCR), demand charges
(not relevant for Scope 2 emissions), multi-tariff breakdowns.

Justification for CSV over PDF: Portal CSV exports are structured and
machine-readable. PDF parsing adds significant complexity for marginal gain —
the same consumption figure appears in both. In practice, ~70% of enterprise
clients have portal access for CSV export.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import io
import re

# Known column name variants across utility portals
COLUMN_ALIASES = {
    'meter_id': ['meter_id', 'meter id', 'meter no', 'meter_no', 'meter number',
                 'account_number', 'consumer_number', 'service_point_id'],
    'facility': ['facility', 'location', 'site', 'premise', 'address', 'plant', 'building'],
    'period_start': ['period_start', 'billing_from', 'from_date', 'start_date',
                     'reading_from', 'bill_from', 'from'],
    'period_end': ['period_end', 'billing_to', 'to_date', 'end_date',
                   'reading_to', 'bill_to', 'to'],
    'consumption': ['consumption', 'units_consumed', 'kwh', 'energy_kwh',
                    'net_consumption', 'billed_units', 'consumption_kwh', 'energy'],
    'unit': ['unit', 'uom', 'unit_of_measurement'],
    'opening_reading': ['opening_reading', 'opening', 'prev_reading', 'previous_reading'],
    'closing_reading': ['closing_reading', 'closing', 'curr_reading', 'current_reading'],
    'tariff': ['tariff', 'rate_schedule', 'tariff_category', 'rate_code'],
    'sanctioned_load': ['sanctioned_load', 'contracted_demand', 'contract_demand', 'cd_kva'],
}

UNIT_TO_KWH = {
    'kwh': 1.0,
    'kWh': 1.0,
    'mwh': 1000.0,
    'MWh': 1000.0,
    'kvah': 1.0,   # kVAh approximated to kWh (power factor ~1 for Scope 2 reporting)
    'kVAh': 1.0,
    'units': 1.0,  # "units" in Indian billing = kWh
}


def find_column(df: pd.DataFrame, aliases: list) -> Optional[str]:
    """Find first matching column name from aliases list."""
    df_cols_lower = {col.lower().replace(' ', '_'): col for col in df.columns}
    for alias in aliases:
        norm = alias.lower().replace(' ', '_')
        if norm in df_cols_lower:
            return df_cols_lower[norm]
        # Try original
        if alias in df.columns:
            return alias
    return None


def parse_utility_date(date_str) -> Optional[datetime]:
    if not date_str or (isinstance(date_str, float) and np.isnan(date_str)):
        return None
    date_str = str(date_str).strip()
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y',
                '%d-%b-%Y', '%d %b %Y', '%b %Y', '%Y%m%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_consumption(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        # Remove commas from thousands formatting
        return float(str(val).replace(',', '').strip())
    except (ValueError, AttributeError):
        return None


def infer_consumption(row_dict: dict, consumption_col, opening_col, closing_col) -> Optional[float]:
    """If direct consumption missing, derive from opening/closing meter readings."""
    if consumption_col:
        val = parse_consumption(row_dict.get(consumption_col))
        if val is not None:
            return val
    if opening_col and closing_col:
        opening = parse_consumption(row_dict.get(opening_col))
        closing = parse_consumption(row_dict.get(closing_col))
        if opening is not None and closing is not None:
            return closing - opening
    return None


def parse_utility_file(file_content: bytes) -> list[dict]:
    raw_text = file_content.decode('utf-8', errors='replace')

    # Try to skip metadata rows that utilities sometimes prepend
    lines = raw_text.split('\n')
    start_row = 0
    for i, line in enumerate(lines):
        if any(alias in line.lower() for alias in ['meter', 'consumption', 'kwh', 'period', 'from']):
            start_row = i
            break

    cleaned = '\n'.join(lines[start_row:])

    # Detect delimiter
    first_data_line = cleaned.split('\n')[0]
    delimiter = ';' if ';' in first_data_line else ('|' if '|' in first_data_line else ',')

    df = pd.read_csv(io.StringIO(cleaned), delimiter=delimiter, dtype=str, skipinitialspace=True)
    df.columns = [col.strip() for col in df.columns]

    # Identify columns
    meter_col = find_column(df, COLUMN_ALIASES['meter_id'])
    facility_col = find_column(df, COLUMN_ALIASES['facility'])
    period_start_col = find_column(df, COLUMN_ALIASES['period_start'])
    period_end_col = find_column(df, COLUMN_ALIASES['period_end'])
    consumption_col = find_column(df, COLUMN_ALIASES['consumption'])
    unit_col = find_column(df, COLUMN_ALIASES['unit'])
    opening_col = find_column(df, COLUMN_ALIASES['opening_reading'])
    closing_col = find_column(df, COLUMN_ALIASES['closing_reading'])
    tariff_col = find_column(df, COLUMN_ALIASES['tariff'])

    records = []
    for idx, row in df.iterrows():
        row_dict = {k: v.strip() if isinstance(v, str) else v for k, v in row.to_dict().items()}

        period_start = parse_utility_date(row_dict.get(period_start_col) if period_start_col else None)
        period_end = parse_utility_date(row_dict.get(period_end_col) if period_end_col else None)

        consumption_kwh_raw = infer_consumption(row_dict, consumption_col, opening_col, closing_col)

        # Unit conversion to kWh
        unit_raw = str(row_dict.get(unit_col, 'kwh')).strip() if unit_col else 'kwh'
        multiplier = UNIT_TO_KWH.get(unit_raw, 1.0)
        consumption_kwh = (consumption_kwh_raw * multiplier) if consumption_kwh_raw is not None else None

        parse_ok = consumption_kwh is not None and period_start is not None

        records.append({
            '_row_index': idx,
            '_parse_ok': parse_ok,
            '_parse_error': '' if parse_ok else
                            f"consumption={row_dict.get(consumption_col)}, period_start={row_dict.get(period_start_col)}",
            'source_type': 'utility',
            'activity_date': period_end.isoformat() if period_end else
                             (period_start.isoformat() if period_start else None),
            'period_start': period_start.isoformat() if period_start else None,
            'period_end': period_end.isoformat() if period_end else None,
            'consumption_kwh': consumption_kwh,
            'unit': 'kwh',
            'unit_original': unit_raw,
            'meter_id': str(row_dict.get(meter_col, '')) if meter_col else '',
            'facility': str(row_dict.get(facility_col, '')) if facility_col else '',
            'tariff': str(row_dict.get(tariff_col, '')) if tariff_col else '',
            '_raw': row_dict,
        })

    return records
