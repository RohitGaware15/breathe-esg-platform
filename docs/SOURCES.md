# SOURCES.md — Source Research

## 1. SAP — Fuel & Procurement

**Format researched:** SAP SE16/SE16N flat file export (CSV/TXT)

**What I learned:**

SAP stores material movements in table MSEG (material document segment) and purchase orders in EKKO (header) + EKPO (items). Transaction SE16 lets any SAP user with the right authorization export any table to a local file. This is the primary way sustainability teams get data out of SAP — not via API or IDoc, but via a manual export.

Key observations from SAP documentation and community resources (SCN, SAP Help Portal):
- Export delimiter is configurable: semicolon in EU-locale installs, comma in US/India. Tab-delimited also common.
- Column headers reflect the SAP system language. German installs produce "Buchungsdatum" (posting date), "Werk" (plant), "Menge" (quantity), "Mengeneinheit" (unit of measure). English installs use English equivalents. Mixed is common when Indian companies use German SIs.
- Quantities use locale-specific decimal separators: EU uses 1.234,56 format.
- Material numbers are 18-character padded strings (leading zeros, e.g. "000000000100000142").
- Dates exported as YYYYMMDD (SAP internal format) or DD.MM.YYYY depending on display settings.
- Plant codes (Werk) are 4-character internal codes meaningless without a plant master lookup. "IN01" might be "Mumbai Manufacturing" — there's no way to know without a separate plant table.
- Movement type 101 = goods receipt, 201 = goods issue to cost center (fuel drawdown). Relevant for identifying actual consumption vs transfers.
- Units: SAP uses its own unit codes — L (litre), GAL (US gallon), KG, M3, TO (metric tonne), KWH. These differ from ISO units in some cases.

**What my sample data looks like and why:**

Sample uses semicolon delimiter (EU SAP install), German headers (realistic for Indian enterprises using German SI), EU number format for quantities (1.234,56), dates as YYYYMMDD. Material numbers are realistic 9-digit numbers padded. Includes edge cases: zero-quantity row (failed reading), very high quantity row (statistical outlier), LPG and natural gas alongside diesel/petrol. Plant codes are 4-char codes. Mix of fuel types covers real procurement patterns.

**What would break in real deployment:**

- Plant code → location name mapping requires a separate plant master export (we flag the raw code but can't enrich it without a lookup table)
- If the client's SAP uses a non-standard unit code we haven't mapped (e.g. "BBL" for barrel in oil companies), that unit silently falls through to "unknown"
- German number format detection assumes comma = decimal if there's no period, but some exports use period-as-thousands in German locale — we handle the common case, not all cases
- MSEG has millions of rows in large companies; a full export without date filtering would be unmanageable. We assume clients pre-filter by date range before exporting
- Movement type filtering: we don't distinguish goods receipt (incoming) from goods issue (consumption). A rigorous implementation would filter to movement type 201/261 for actual consumption

---

## 2. Utility — Electricity

**Format researched:** Indian DISCOM portal CSV export (MSEDCL, BESCOM pattern)

**What I learned:**

India's major DISCOMs (MSEDCL covering Maharashtra, BESCOM covering Bangalore, CESC covering Kolkata, TNEB covering Tamil Nadu) all have consumer portals with bill history and consumption export. The export formats are similar but not identical.

Key observations:
- MSEDCL portal exports include: consumer number, location, billing period (from/to), opening reading, closing reading, units consumed, amount. No API — portal scrape or manual CSV download only.
- Billing periods are NOT calendar months. MSEDCL bills on a 60-day cycle for some HT consumers, monthly for LT. Periods starting mid-month are common.
- Industrial consumers (HT connections) are billed on kVAh (kilovolt-ampere hours) to account for power factor. For GHG reporting, kVAh ≈ kWh is a reasonable approximation (power factor correction).
- Multiple meters per facility: a large plant may have separate HT and LT connections, a DG set meter, a canteen meter. Each appears as a separate row.
- "Units consumed" is the standard field in Indian billing = kWh.
- Some portal exports omit opening/closing readings and show only consumption delta. We handle both.

**What my sample data looks like and why:**

Sample covers multiple facilities (Mumbai, Pune, Bangalore, Hyderabad, Delhi), multiple meters per city, different tariff categories (HT-I, HT-II, LT-I, LT-II reflecting actual DISCOM tariff categories). Billing periods mostly December 2023 but one Delhi meter has a shifted period (03/12 to 04/01) — realistic for 30+ day billing cycles. Includes: zero consumption row (server room — suspicious, should be flagged), row with missing opening/closing readings but direct consumption figure (common on portal exports), and a high-consumption data center row.

**What would break in real deployment:**

- Each DISCOM has slightly different column names. Our flexible column alias detection covers common variants but won't cover every DISCOM's export format
- PDF bills: if a facilities team can't export CSV and only has PDFs, we can't parse them without pdfplumber + layout-specific parsing per utility — brittle
- Grid emission factor is hardcoded at India national average (0.716 kg CO2e/kWh, CEA 2022). Production should use state-level or regional grid factors — Maharashtra's grid is cleaner than the national average, UP's is dirtier
- We don't handle time-of-use (TOU) tariffs where consumption is split into peak/off-peak — not relevant for Scope 2 kWh totals but matters for cost analysis

---

## 3. Corporate Travel — Flights, Hotels, Ground Transport

**Format researched:** SAP Concur Standard Accounting Extract (CSV)

**What I learned:**

Concur's Standard Accounting Extract is the primary export format for expense data. Documented in SAP Concur's "Expense: Standard Accounting Extract" guide (available in Concur's developer portal). Key fields:

- ExpenseTypeName / Expense Type Code: AIRFR, HOTEL, CARRT, MILEAGE, TRAIN — these are the standard Concur codes. Custom expense types also appear (client-specific).
- For flights: departure and arrival airport IATA codes (3-letter). No distance. No fuel consumption. You derive emissions from distance × passenger-km factor.
- Travel class: Economy, Business, First — field name varies (Class of Service, Cabin Class). Matters because DEFRA 2023 factors are 0.0882 kg CO2e/pkm economy, 0.2652 business, 0.4412 first.
- For hotels: check-in date, location/city, sometimes number of nights, sometimes just amount.
- Dates: YYYY-MM-DD in most Concur configs.
- Currency: whatever the employee submitted in — USD, INR, GBP, EUR all in the same file.

Navan (formerly TripActions) has a similar CSV export structure. The column names differ slightly but the data shape is identical.

DEFRA emission factor source: "UK Government GHG Conversion Factors for Company Reporting 2023," Table 9 (passenger transport) and Table 14 (business travel). Publicly available at gov.uk. Radiative forcing multiplier for flights is 1.891× for economy — we omit it for simplicity and note the omission.

Airport coordinates: OpenFlights dataset (openflights.org/data) covers ~7,000 airports with IATA codes and lat/lon. We use a hardcoded subset of ~20 major airports for the prototype.

**What my sample data looks like and why:**

Sample includes realistic Indian corporate travel: BOM-DEL short-haul (economy, round trip with hotel), BOM-LHR long-haul (business class — this is where a sales exec would fly), BLR-HYD domestic (economy, car rental), DEL-DXB (economy), BOM-SIN (business). Includes a JFK-DEL first class route (large outlier — statistical flag expected). All IATA codes are in our airport lookup so distances and CO2e are calculable. Employee names and departments match realistic Indian corporate naming. Multiple expense types per trip (flight + hotel + taxi).

**What would break in real deployment:**

- Airport lookup gap: ~7,000 airports in OpenFlights, we cover ~20. A route through a secondary airport (e.g. Coimbatore-CBE or Bhopal-BHO) would produce null distance and null CO2e
- Class of service parsing: Concur uses fare codes (Y, Q, M for economy; J, C, D for business; F, A for first) not plain English. Our normalize_class() function handles common patterns but Concur sometimes exports raw GDS fare basis codes like "YOWUS" — we'd default to economy for unrecognized codes
- Ground transport: we assume car rental distance is in km. Concur sometimes stores miles. No unit label on the distance field — this would silently halve or double emissions for US-based employees
- Multi-leg itineraries: Concur sometimes exports each leg as a row, sometimes aggregates. We handle row-per-leg; aggregated itineraries would show one row for a BOM-DXB-LHR routing with only origin/destination
- Hotels: we use HCMI global average (31 kg CO2e/room-night). City-level factors vary widely — a London hotel is much higher than a Pune hotel. This is a known accuracy gap.
