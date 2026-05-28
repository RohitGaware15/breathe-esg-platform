# MODEL.md — Data Model

## Overview

The data model is designed around one core tension: **raw data must never be lost or mutated**, but analysts need a clean, normalized view to work with. We solve this with two separate record layers — raw and normalized — linked by a foreign key, with a third audit layer for every analyst action.

---

## Entity Relationship

```
Tenant
  └── IngestionBatch (one per file upload)
        └── RawRecord (one per row in the file, immutable)
              └── NormalizedRecord (one per successfully parsed row)
                    └── ReviewAction (one per analyst action, immutable)
```

---

## Tenant

Multi-tenancy via foreign key scoping, not schema separation. Every data table has a `tenant` FK. Simpler to query across tenants for internal analytics; schema separation only justified if hard isolation guarantees (separate DB users, RLS) are required.

```
Tenant: id (UUID), name, slug (unique), created_at, is_active
```

---

## IngestionBatch

One row per file upload event. Tracks provenance: who, what, when, which source, and outcome.

```
IngestionBatch:
  id, tenant FK, source_type (sap|utility|travel),
  uploaded_by FK User, uploaded_at, file_name, file (stored),
  total_rows, parsed_rows, failed_rows,
  status (pending|processing|done|failed), error_message
```

File is stored so normalization can be re-run if emission factors or parser logic change.

Parsed vs failed tracked separately — a 90% successful file should not discard good data.

---

## RawRecord

Immutable. One row per source file row. raw_data stores the full row as JSON with original column names.

```
RawRecord:
  id, batch FK, row_index (original line number),
  raw_data (JSON — full row), parse_status (ok|failed|skipped),
  parse_error, created_at
```

JSON for raw_data because columns differ completely across sources (SAP: Buchungsdatum/Werk; utility: meter_id/period_start; travel: expense_type/origin). Never mutated — auditors can ask "what exactly did the client send on Jan 15?" and get a precise answer.

---

## NormalizedRecord

The cleaned, unit-normalized, scope-tagged record analysts review.

```
NormalizedRecord:
  id, tenant FK, batch FK, raw_record FK (OneToOne)

  scope (1|2|3), source_type, category (diesel|electricity|flight|hotel|car_rental)

  activity_date, quantity (normalized), unit (kwh|litre|km|room_night), co2e_kg (nullable)

  facility, cost_center, description, extra_data (JSON)

  review_status (pending|approved|flagged|rejected)
  is_suspicious (bool), suspicion_reasons (JSON array)

  created_at, updated_at, is_manually_edited, locked_at (set on approve)
```

**Unit normalization:**
- SAP fuel → litres (liquid) or kg (solid). DEFRA factors are per-litre.
- Electricity → kWh. kVAh (industrial tariffs) treated as ~kWh for Scope 2.
- Travel flights → km great-circle from IATA codes + DEFRA 2023 kg CO2e/passenger-km.
- Hotels → room-nights.

**co2e_kg nullable because:** flights with unknown airport coords, utility with unknown grid factor cannot produce CO2e at ingest. Analyst sees "n/a" and investigates.

**Scope assignment:**
- SAP → Scope 1 (direct combustion)
- Utility → Scope 2 (purchased electricity)
- Travel → Scope 3 Category 6 (business travel)

**Suspicion flags (automatic, non-blocking):**
- quantity = 0 or null
- activity_date missing
- co2e_kg < 0
- quantity > 3σ from batch mean

---

## ReviewAction

Append-only audit log. Never deleted. One row per analyst action.

```
ReviewAction:
  id, record FK, performed_by FK User, performed_at,
  action (approved|flagged|rejected|edited|comment),
  comment, field_changed, old_value, new_value
```

Separate from NormalizedRecord so a record's full review history (flagged → re-reviewed → approved) is preserved. NormalizedRecord.review_status is the current derived state; ReviewAction is the ledger. locked_at on NormalizedRecord freezes the record for audit export.

---

## Indexes

```sql
INDEX (tenant, scope)           -- scope-level reporting per tenant
INDEX (tenant, review_status)   -- analyst dashboard filtering
INDEX (batch)                   -- all records from one upload
```

---

## Deliberate Omissions

- **Emission factor versioning**: factors hardcoded. Production needs EmissionFactor table with effective_from/effective_to.
- **Multi-currency FX**: value stored as-is with currency code; no conversion.
- **User-tenant membership**: any auth'd user sees all tenants. Production needs UserTenantMembership join table.
- **Scope 2 market-based**: only location-based (grid factor). Market-based requires energy attribute certificate input.
