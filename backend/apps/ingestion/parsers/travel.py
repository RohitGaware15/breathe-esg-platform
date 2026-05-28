"""
Corporate Travel Parser — Concur/Navan Style CSV Export

Research basis:
Concur Travel & Expense exports (via Reports > Extract) produce CSV with columns
documented in SAP Concur's "Standard Accounting Extract" format. Navan exports
are similar. Key characteristics:

- Expense type codes: AIRFR (airfare), HOTEL, CARRT (car rental), TRAIN, TAXI
- For flights: departure/arrival airport IATA codes (3-letter), not distances
- Class of travel: ECONOMY, BUSINESS, FIRST — matters for emission factors
  (business class ~3x economy per DEFRA/BEIS guidance)
- Hotels: room nights + city, no direct energy consumption given
- Car rental/taxi: sometimes miles/km given, sometimes just cost
- Ground transport: fuel type not always specified

Emission factor approach:
- Flights: use ICAO distance calculator approximation via great-circle distance
  between airport IATA codes, then apply DEFRA 2023 kg CO2e/passenger-km factors
- Hotels: use average industry factor (kg CO2e per room-night) from HCMI
- Car rental: use average car emission factor if fuel type unknown

We handle: flights (most Scope 3 cat 6 volume), hotels, car rental.
We do NOT handle: personal vehicle mileage claims, rail (minor), per-diem.

Justification for CSV over API: Concur's API requires OAuth + enterprise setup.
CSV export is universally available and what sustainability teams actually use.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import math
import io

# IATA airport code → (lat, lon) for major airports
# In prod this would be a full airport DB (openflight data ~7k airports)
AIRPORT_COORDS = {
    'BOM': (19.0896, 72.8656),  # Mumbai
    'DEL': (28.5562, 77.1000),  # Delhi
    'BLR': (13.1979, 77.7063),  # Bangalore
    'MAA': (12.9900, 80.1693),  # Chennai
    'HYD': (17.2313, 78.4298),  # Hyderabad
    'CCU': (22.6520, 88.4463),  # Kolkata
    'LHR': (51.4775, -0.4614),  # London Heathrow
    'JFK': (40.6413, -73.7781), # New York JFK
    'CDG': (49.0097, 2.5479),   # Paris CDG
    'DXB': (25.2532, 55.3657),  # Dubai
    'SIN': (1.3644, 103.9915),  # Singapore
    'SYD': (-33.9399, 151.1753),# Sydney
    'NRT': (35.7720, 140.3929), # Tokyo Narita
    'ORD': (41.9742, -87.9073), # Chicago O'Hare
    'LAX': (33.9425, -118.4081),# Los Angeles
    'FRA': (50.0379, 8.5622),   # Frankfurt
    'AMS': (52.3086, 4.7639),   # Amsterdam
    'DOH': (25.2609, 51.6138),  # Doha
    'HKG': (22.3080, 113.9185), # Hong Kong
}

# DEFRA 2023 emission factors (kg CO2e per passenger-km)
# Includes radiative forcing multiplier for flights
FLIGHT_FACTORS = {
    'economy': 0.0882,     # short haul avg; long haul lower per km but higher total
    'business': 0.2652,    # ~3x economy (DEFRA GHG conversion factors 2023)
    'first': 0.4412,       # ~5x economy
    'unknown': 0.0882,     # default to economy
}

# kg CO2e per room-night (HCMI global average by region)
HOTEL_FACTOR_PER_ROOM_NIGHT = 31.0  # global average; in prod use city-level factors

# kg CO2e per km for car rental (avg petrol car, DEFRA 2023)
CAR_FACTOR_PER_KM = 0.17064

EXPENSE_TYPE_MAP = {
    'AIRFR': 'flight', 'AIR': 'flight', 'AIRFARE': 'flight',
    'AIRLINE': 'flight', 'FLIGHT': 'flight',
    'HOTEL': 'hotel', 'LODGING': 'hotel', 'ACCOMMODATION': 'hotel',
    'CARRT': 'car_rental', 'CAR': 'car_rental', 'CAR RENTAL': 'car_rental',
    'RENTAL': 'car_rental', 'VEHICLE': 'car_rental',
    'TAXI': 'taxi', 'RIDESHARE': 'taxi', 'UBER': 'taxi', 'LYFT': 'taxi',
    'TRAIN': 'train', 'RAIL': 'train', 'AMTRAK': 'train',
    'MILEAGE': 'personal_car',
}

COLUMN_ALIASES = {
    'expense_type': ['expense_type', 'expense type', 'category', 'expense_category',
                     'type', 'transaction_type'],
    'travel_date': ['travel_date', 'departure_date', 'check_in_date', 'date',
                    'transaction_date', 'expense_date', 'trip_date'],
    'origin': ['origin', 'from', 'departure', 'departure_airport', 'departure_city',
               'from_airport', 'origin_airport'],
    'destination': ['destination', 'to', 'arrival', 'arrival_airport', 'arrival_city',
                    'to_airport', 'destination_airport'],
    'travel_class': ['travel_class', 'class', 'cabin_class', 'service_class', 'fare_class'],
    'amount': ['amount', 'cost', 'total', 'charge', 'total_amount'],
    'currency': ['currency', 'curr', 'currency_code'],
    'nights': ['nights', 'room_nights', 'num_nights', 'number_of_nights', 'duration'],
    'distance_km': ['distance_km', 'distance', 'mileage', 'km', 'miles'],
    'employee': ['employee', 'employee_name', 'traveler', 'traveller', 'user', 'name'],
    'department': ['department', 'dept', 'cost_center', 'business_unit'],
}


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def flight_distance_km(origin_iata: str, dest_iata: str) -> Optional[float]:
    o = AIRPORT_COORDS.get(origin_iata.upper().strip() if origin_iata else '')
    d = AIRPORT_COORDS.get(dest_iata.upper().strip() if dest_iata else '')
    if o and d:
        return haversine_km(*o, *d)
    return None


def find_column(df, aliases):
    df_cols_lower = {col.lower().replace(' ', '_'): col for col in df.columns}
    for alias in aliases:
        norm = alias.lower().replace(' ', '_')
        if norm in df_cols_lower:
            return df_cols_lower[norm]
        if alias in df.columns:
            return alias
    return None


def parse_travel_date(date_str) -> Optional[datetime]:
    if not date_str or (isinstance(date_str, float) and np.isnan(date_str)):
        return None
    date_str = str(date_str).strip()
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y',
                '%d-%b-%Y', '%Y%m%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def normalize_class(class_str: str) -> str:
    if not class_str:
        return 'unknown'
    c = class_str.upper().strip()
    if any(x in c for x in ['BUS', 'J', 'C', 'D']):
        return 'business'
    if any(x in c for x in ['FIRST', 'F', 'A']):
        return 'first'
    if any(x in c for x in ['ECO', 'Y', 'Q', 'M', 'K']):
        return 'economy'
    return 'unknown'


def parse_travel_file(file_content: bytes) -> list[dict]:
    raw_text = file_content.decode('utf-8', errors='replace')
    first_line = raw_text.split('\n')[0]
    delimiter = ';' if ';' in first_line else ('|' if '|' in first_line else ',')

    df = pd.read_csv(io.StringIO(raw_text), delimiter=delimiter, dtype=str, skipinitialspace=True)
    df.columns = [col.strip() for col in df.columns]

    expense_col = find_column(df, COLUMN_ALIASES['expense_type'])
    date_col = find_column(df, COLUMN_ALIASES['travel_date'])
    origin_col = find_column(df, COLUMN_ALIASES['origin'])
    dest_col = find_column(df, COLUMN_ALIASES['destination'])
    class_col = find_column(df, COLUMN_ALIASES['travel_class'])
    amount_col = find_column(df, COLUMN_ALIASES['amount'])
    currency_col = find_column(df, COLUMN_ALIASES['currency'])
    nights_col = find_column(df, COLUMN_ALIASES['nights'])
    distance_col = find_column(df, COLUMN_ALIASES['distance_km'])
    employee_col = find_column(df, COLUMN_ALIASES['employee'])
    dept_col = find_column(df, COLUMN_ALIASES['department'])

    records = []
    for idx, row in df.iterrows():
        row_dict = {k: v.strip() if isinstance(v, str) else v for k, v in row.to_dict().items()}

        raw_type = str(row_dict.get(expense_col, '')).upper().strip() if expense_col else ''
        category = EXPENSE_TYPE_MAP.get(raw_type, 'other')

        travel_date = parse_travel_date(row_dict.get(date_col) if date_col else None)

        # Calculate distance and emissions by category
        distance_km = None
        co2e_kg = None
        travel_class = 'unknown'
        parse_ok = travel_date is not None

        if category == 'flight':
            origin = str(row_dict.get(origin_col, '')).strip() if origin_col else ''
            dest = str(row_dict.get(dest_col, '')).strip() if dest_col else ''
            travel_class = normalize_class(str(row_dict.get(class_col, '')) if class_col else '')
            distance_km = flight_distance_km(origin, dest)
            if distance_km:
                factor = FLIGHT_FACTORS.get(travel_class, FLIGHT_FACTORS['unknown'])
                co2e_kg = distance_km * factor
                parse_ok = True
            else:
                parse_ok = False

        elif category == 'hotel':
            nights_raw = row_dict.get(nights_col) if nights_col else None
            try:
                nights = float(str(nights_raw).replace(',', '')) if nights_raw else 1.0
            except (ValueError, AttributeError):
                nights = 1.0
            co2e_kg = nights * HOTEL_FACTOR_PER_ROOM_NIGHT

        elif category in ('car_rental', 'taxi'):
            dist_raw = row_dict.get(distance_col) if distance_col else None
            if dist_raw:
                try:
                    dist = float(str(dist_raw).replace(',', ''))
                    co2e_kg = dist * CAR_FACTOR_PER_KM
                    distance_km = dist
                except (ValueError, AttributeError):
                    pass

        try:
            amount = float(str(row_dict.get(amount_col, '')).replace(',', '')) if amount_col else None
        except (ValueError, AttributeError):
            amount = None

        records.append({
            '_row_index': idx,
            '_parse_ok': parse_ok,
            '_parse_error': '' if parse_ok else
                            f"date={row_dict.get(date_col)}, category={category}, origin/dest missing or unknown",
            'source_type': 'travel',
            'activity_date': travel_date.isoformat() if travel_date else None,
            'category': category,
            'origin': str(row_dict.get(origin_col, '')) if origin_col else '',
            'destination': str(row_dict.get(dest_col, '')) if dest_col else '',
            'travel_class': travel_class,
            'distance_km': distance_km,
            'co2e_kg_estimated': co2e_kg,
            'nights': float(str(row_dict.get(nights_col, 1)).replace(',', '')) if nights_col and row_dict.get(nights_col) else None,
            'amount': amount,
            'currency': str(row_dict.get(currency_col, '')) if currency_col else '',
            'employee': str(row_dict.get(employee_col, '')) if employee_col else '',
            'department': str(row_dict.get(dept_col, '')) if dept_col else '',
            '_raw': row_dict,
        })

    return records
