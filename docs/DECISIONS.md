# DECISIONS.md — Every Ambiguity Resolved

## SAP: Format Choice

**Ambiguity:** SAP exposes data via IDoc, OData, BAPI, RFC, flat file export, and more.

**Decision:** Flat file (CSV/TXT) via SE16/SE16N transaction export.

**Why:** IDocs require SAP middleware (ALE/EDI) and an active integration layer — not something a sustainability team can produce on demand. OData and BAPI require a live SAP system with API access, which clients rarely grant to third parties. Flat file exports are what sustainability leads actually produce: they open SE16, run the query, hit "Export to Local File." This is the realistic shape of what arrives in a client email.

**What I ignored:** IDoc format entirely. BAPI/RFC (requires live system). Multi-currency purchase orders (complex FX handling). MIRO (invoice verification) tables — out of scope for fuel/procurement.

**What I'd ask the PM:** "Do clients export these themselves or do they have SAP admins? If admins, we might get BAPI access. If sustainability leads doing it manually, flat file is the right assumption." Also: "Which SAP module — MM (Materials Management) for procurement, or FI (Finance) for cost postings? The tables differ."

---

## SAP: German Headers

**Ambiguity:** Not all SAP installs use German column names — system locale depends on the SAP install.

**Decision:** Handle both German and English headers via a mapping dict. Try German first (Buchungsdatum, Werk, Menge), fall back to English variants.

**Why:** Enterprise clients often have SAP installed by a German SI (systems integrator) with German locale. Mixed environments are common. Handling both costs little and avoids failures on real data.

---

## SAP: Number Format

**Ambiguity:** EU SAP installs use comma as decimal separator (1.234,56 = one thousand two hundred thirty-four point five six).

**Decision:** Detect both EU and US formats. If both period and comma present, determine which is the thousands separator by position.

**Why:** Getting this wrong silently converts 500,00 litres → 50000 litres → 10x the emissions. It's a silent data corruption issue that would sail through without flagging. Detecting it explicitly is safer than assuming.

---

## Utility: Format Choice

**Ambiguity:** Utility data could come as PDF bills, portal CSV exports, or direct API (where available).

**Decision:** Portal CSV export.

**Why:** ~70% of enterprise clients have portal access that produces CSV. PDF parsing adds OCR complexity and layout sensitivity that varies by utility. APIs are available from some utilities (e.g. Green Button in the US, some DISCOM APIs in India) but require per-utility integration work. CSV is the universal fallback and what facilities teams actually use when asked to "send the electricity data."

**What I ignored:** PDF bills (pdfplumber could handle it, but layout parsing is fragile). Green Button API (US-specific, not relevant for India-first client base). Multi-site aggregation portals (Urjanet, etc.) — these are a production concern.

**What I'd ask the PM:** "Are clients in India or globally? Indian DISCOMs (MSEDCL, BESCOM, etc.) all have different portal formats. Do we need to handle a specific set, or is a generic CSV approach with flexible column detection sufficient for now?"

---

## Utility: Billing Period Alignment

**Ambiguity:** Billing periods don't align with calendar months (e.g. 18-Jan to 21-Feb). How do we attribute consumption to a reporting period?

**Decision:** Use period_end date as the activity_date. Store both period_start and period_end in extra_data.

**Why:** For GHG reporting, you typically report the period in which the bill was issued (period_end). Pro-rating across calendar months (splitting a 45-day bill proportionally into two months) adds complexity with marginal accuracy benefit at this stage. Store both dates so analysts can apply their own period logic if needed.

**What I ignored:** Pro-rata allocation across calendar months. Demand charge attribution (kVA/kW) — not relevant for Scope 2 kWh reporting.

---

## Travel: Format Choice

**Ambiguity:** Concur exposes data via REST API (OAuth 2.0) and via Standard Accounting Extract (CSV).

**Decision:** CSV export (Standard Accounting Extract format).

**Why:** Concur's API requires OAuth enterprise setup per client, a developer key, and client IT involvement. The CSV extract is available to any expense administrator without IT involvement. In practice, sustainability teams get handed a CSV. The API path is correct for production but adds 2-3 days of auth/integration work that isn't the point of this prototype.

**What I ignored:** Concur REST API. Navan's GraphQL API. Rail travel (minor emissions volume). Personal vehicle mileage claims (need separate factor for vehicle type). Per-diem expense lines (no emissions).

---

## Travel: Flight Distance

**Ambiguity:** Concur exports give airport IATA codes, not distances. DEFRA factors are per passenger-km.

**Decision:** Compute great-circle distance from a hardcoded airport coordinate lookup table (major airports). Flag records where both airports aren't in the lookup.

**Why:** This is what DEFRA's own methodology tool does — great-circle distance with a ~9% uplift factor for indirect routing (we omit the uplift for simplicity; note in SOURCES.md). A full airport DB (OpenFlights, ~7k airports) would cover real-world needs; the prototype covers the ~100 most common business travel airports.

**What I'd ask the PM:** "Should we apply the ICAO/DEFRA radiative forcing multiplier for flights? It roughly doubles the CO2e figure for high-altitude flights. Some clients want it, some don't — it's a reporting choice, not a data choice."

---

## Travel: Emission Factors

**Decision:** DEFRA 2023 GHG Conversion Factors for flights. HCMI global average for hotels. DEFRA average petrol car for ground transport.

**Why:** DEFRA is the most widely cited publicly available factor set for corporate GHG reporting in India and the UK. HCMI is the Hotel Carbon Measurement Initiative standard. Using one authoritative source for each category avoids inconsistency.

**What I ignored:** Radiative forcing multiplier (would double flight emissions — noted as omission). City-level hotel factors (HCMI provides these; we use global average). Vehicle-specific car factors (we don't know rental car type).

---

## Multi-tenancy: FK vs Schema

**Decision:** FK-based multi-tenancy (tenant column on every data table).

**Why:** Schema-per-tenant (e.g. via django-tenants) is justified when tenants need hard isolation — separate DB roles, no cross-tenant query risk. For a prototype and for Breathe ESG's internal analyst tools (where staff need to query across clients), FK scoping is simpler and sufficient. The tradeoff is that a misconfigured query could accidentally expose cross-tenant data; mitigated by view-layer filtering.

---

## Review: Approve Locks Record

**Decision:** Approving a record sets locked_at and freezes it for audit.

**Why:** Auditors need to know that the data they're certifying wasn't modified after sign-off. locked_at provides a timestamp and a state gate. In production, approved records would be exported to a separate read-only audit schema or PDF report.

**What I ignored:** Unlocking approved records (requires a supervisor role and a reason — out of scope). Bulk approve (useful but adds UI complexity).
