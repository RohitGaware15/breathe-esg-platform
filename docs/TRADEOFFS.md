# TRADEOFFS.md — Three Things Deliberately Not Built

## 1. Real-time API Pull (vs File Upload)

**What it would be:** Instead of requiring clients to export files, the app would directly pull from SAP OData, utility APIs, or Concur's REST API on a schedule.

**Why I didn't build it:**
API integrations are correct for production but each one is a separate project. SAP OData requires RFC access, system configuration, and an active connection to the client's SAP instance. Concur requires OAuth 2.0 enterprise setup per client. Utility APIs (where they exist — many Indian DISCOMs don't have them) require per-utility credentials.

The file upload approach reflects how sustainability data actually arrives at Breathe ESG today: a CSV in an email. Building an API integration layer without a real client credential to test against would produce untestable, theoretical code. File upload is a real, working ingestion path.

**What would need to change:** An `IngestorBase` class with `pull()` and `parse()` methods, a scheduler (Celery Beat or cron), and per-client credential storage. The parser modules would be unchanged — they take `bytes` in regardless of how those bytes arrived.

---

## 2. Emission Factor Versioning

**What it would be:** An `EmissionFactor` table with `factor_type`, `value`, `unit`, `source`, `effective_from`, `effective_to` columns. Normalization would look up the factor valid for the record's `activity_date`, not use a hardcoded value.

**Why I didn't build it:**
DEFRA publishes annual updates. A record from 2022 should use 2022 factors; a record from 2023 should use 2023 factors. Without versioning, re-running normalization after a factor update would silently produce different CO2e figures for historical records — which breaks audit consistency.

I didn't build it because the correct data to populate it (multi-year DEFRA factor tables for every relevant category) requires structured data extraction from DEFRA's annual spreadsheets, which is a data pipeline task outside the scope of a 4-day prototype. Hardcoding 2023 factors is accurate for data uploaded now; the architectural gap is documented.

**What would need to change:** `EmissionFactor` model, a loader script to populate from DEFRA CSV, and a `get_factor(category, date)` function in the normalizer replacing the hardcoded dicts.

---

## 3. Role-Based Access Control (RBAC)

**What it would be:** Users assigned to tenants with roles (e.g. `data_uploader`, `analyst`, `admin`). Uploaders can ingest data but not approve. Analysts can review but not create tenants. Admins can do everything. Access scoped so User X can only see Tenant Y's data.

**Why I didn't build it:**
RBAC adds non-trivial complexity to both the auth layer (custom permission classes, middleware) and every API view (per-object permission checks). For a prototype reviewed by 3 people, any authenticated user accessing any tenant is an acceptable shortcut. The data model is already multi-tenant; the only missing piece is the enforcement layer.

The risk of omitting this is real: without tenant scoping, a misconfigured API call could return another client's data. This would be a serious issue in production and is the first thing I would add before onboarding a second client.

**What would need to change:** A `UserTenantMembership` model (user, tenant, role), a `TenantPermission` base class, and `get_queryset()` overrides in every viewset that filter by `request.user`'s permitted tenants.
