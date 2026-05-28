"""
Normalization layer.

Takes parsed row dicts (output of parsers) and RawRecord instances,
creates NormalizedRecord instances with:
- Correct scope assignment
- Consistent units
- Suspicion flags for analyst attention
"""

import numpy as np
from datetime import date
from typing import Optional
from apps.normalization.models import NormalizedRecord, Scope

# DEFRA 2023 emission factors
# Scope 1: kg CO2e per litre of fuel
FUEL_EMISSION_FACTORS = {
    'diesel': 2.68224,      # kg CO2e / litre
    'petrol': 2.31378,
    'lpg': 1.55481,
    'natural_gas': 2.04,    # kg CO2e / m3
    'heating_oil': 2.68,
    None: 2.68,             # default to diesel when unknown
}

# Scope 2: UK/IN grid average (in prod: use location-specific grid factor)
# India grid: ~0.716 kg CO2e / kWh (CEA 2022)
# UK grid: ~0.207 kg CO2e / kWh (DEFRA 2023)
ELECTRICITY_FACTOR_KG_PER_KWH = 0.716


def parse_date_safe(date_str) -> Optional[date]:
    if not date_str:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None


def normalize_sap(parsed: dict) -> dict:
    """SAP → Scope 1."""
    quantity = parsed.get('quantity')
    unit = parsed.get('unit', 'litre')
    fuel_type = parsed.get('fuel_type')

    # Estimate CO2e if fuel type known and unit is litre
    co2e_kg = None
    if quantity and unit == 'litre':
        factor = FUEL_EMISSION_FACTORS.get(fuel_type, FUEL_EMISSION_FACTORS[None])
        co2e_kg = quantity * factor

    return {
        'scope': Scope.SCOPE_1,
        'category': fuel_type or 'fuel',
        'activity_date': parse_date_safe(parsed.get('activity_date')),
        'quantity': quantity,
        'unit': unit,
        'co2e_kg': co2e_kg,
        'facility': parsed.get('plant_code', ''),
        'cost_center': parsed.get('cost_center', ''),
        'description': parsed.get('description', ''),
        'extra_data': {
            'material_number': parsed.get('material_number', ''),
            'vendor': parsed.get('vendor', ''),
            'po_number': parsed.get('po_number', ''),
            'value': parsed.get('value'),
            'currency': parsed.get('currency', ''),
        },
    }


def normalize_utility(parsed: dict) -> dict:
    """Utility → Scope 2."""
    kwh = parsed.get('consumption_kwh')
    co2e_kg = kwh * ELECTRICITY_FACTOR_KG_PER_KWH if kwh else None

    return {
        'scope': Scope.SCOPE_2,
        'category': 'electricity',
        'activity_date': parse_date_safe(parsed.get('activity_date')),
        'quantity': kwh,
        'unit': 'kwh',
        'co2e_kg': co2e_kg,
        'facility': parsed.get('facility', ''),
        'cost_center': '',
        'description': f"Meter: {parsed.get('meter_id', 'unknown')}",
        'extra_data': {
            'meter_id': parsed.get('meter_id', ''),
            'period_start': parsed.get('period_start'),
            'period_end': parsed.get('period_end'),
            'tariff': parsed.get('tariff', ''),
            'unit_original': parsed.get('unit_original', ''),
        },
    }


def normalize_travel(parsed: dict) -> dict:
    """Travel → Scope 3 (cat 6: business travel)."""
    category = parsed.get('category', 'other')

    if category == 'flight':
        quantity = parsed.get('distance_km')
        unit = 'km'
    elif category == 'hotel':
        quantity = parsed.get('nights')
        unit = 'room_night'
    else:
        quantity = parsed.get('distance_km')
        unit = 'km'

    return {
        'scope': Scope.SCOPE_3,
        'category': category,
        'activity_date': parse_date_safe(parsed.get('activity_date')),
        'quantity': quantity,
        'unit': unit,
        'co2e_kg': parsed.get('co2e_kg_estimated'),
        'facility': parsed.get('department', ''),
        'cost_center': parsed.get('department', ''),
        'description': f"{parsed.get('origin', '')} → {parsed.get('destination', '')}",
        'extra_data': {
            'travel_class': parsed.get('travel_class', ''),
            'employee': parsed.get('employee', ''),
            'origin': parsed.get('origin', ''),
            'destination': parsed.get('destination', ''),
            'amount': parsed.get('amount'),
            'currency': parsed.get('currency', ''),
        },
    }


NORMALIZERS = {
    'sap': normalize_sap,
    'utility': normalize_utility,
    'travel': normalize_travel,
}


def flag_suspicious(record: NormalizedRecord, all_quantities: list[float]) -> tuple[bool, list[str]]:
    """
    Simple statistical flagging. Analyst sees these as warnings, not errors.
    """
    reasons = []

    if record.quantity is None or record.quantity == 0:
        reasons.append('Zero or missing quantity')

    if record.activity_date is None:
        reasons.append('Missing activity date')

    if record.co2e_kg is not None and record.co2e_kg < 0:
        reasons.append('Negative CO2e value')

    if record.quantity and all_quantities:
        arr = np.array([q for q in all_quantities if q is not None])
        if len(arr) > 5:
            mean, std = arr.mean(), arr.std()
            if std > 0 and abs(record.quantity - mean) > 3 * std:
                reasons.append(f'Statistical outlier: value {record.quantity:.2f} is >3σ from batch mean {mean:.2f}')

    return bool(reasons), reasons


def normalize_records(pairs: list[tuple], batch, tenant) -> list[NormalizedRecord]:
    """
    pairs: list of (RawRecord, parsed_dict)
    Creates NormalizedRecord for each, runs suspicion flagging.
    """
    source_type = batch.source_type
    normalizer_fn = NORMALIZERS.get(source_type)
    if not normalizer_fn:
        return []

    normalized = []
    for raw_record, parsed in pairs:
        fields = normalizer_fn(parsed)
        rec = NormalizedRecord(
            tenant=tenant,
            batch=batch,
            raw_record=raw_record,
            source_type=source_type,
            **fields,
        )
        normalized.append(rec)

    # Collect quantities for outlier detection per batch
    quantities = [r.quantity for r in normalized if r.quantity is not None]

    # Flag suspicious before bulk create
    for rec in normalized:
        is_susp, reasons = flag_suspicious(rec, quantities)
        rec.is_suspicious = is_susp
        rec.suspicion_reasons = reasons

    NormalizedRecord.objects.bulk_create(normalized)
    return normalized
