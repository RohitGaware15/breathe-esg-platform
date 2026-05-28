# Breathe ESG — Data Ingestion Platform

Django REST + React prototype for ingesting, normalizing, and reviewing ESG emissions data from three source types.

## Live Demo
Login: admin 
Password: admin123

## Stack

- **Backend:** Django 4.2, Django REST Framework, PostgreSQL
- **Frontend:** React 18, Vite, Tailwind CSS
- **Deploy:** Docker + Railway (or Render/Fly)

## Local Setup

### Prerequisites
- Python 3.11+
- Node 20+
- PostgreSQL 15+

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your DB credentials

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Docker (full stack)

```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## First Run

1. Log in at `/login`
2. Create a Tenant at `/admin` (or via API: `POST /api/tenants/`)
3. Go to Upload, select tenant, drop a CSV file
4. Go to Review to see normalized records and approve/flag them

## Sample Data

`/sample_data/` contains realistic test files:
- `sap_export.csv` — SAP SE16 flat file (German headers, EU number format)
- `utility_export.csv` — MSEDCL-style portal CSV
- `travel_concur.csv` — Concur Standard Accounting Extract

## API Endpoints

```
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/me/

GET    /api/tenants/
POST   /api/tenants/

POST   /api/ingestion/upload/
GET    /api/ingestion/batches/
GET    /api/ingestion/raw-records/

GET    /api/normalization/records/

POST   /api/review/records/{id}/approve/
POST   /api/review/records/{id}/flag/
POST   /api/review/records/{id}/reject/
GET    /api/review/records/summary/
```

## Docs

- [MODEL.md](docs/MODEL.md) — Data model and design decisions
- [DECISIONS.md](docs/DECISIONS.md) — Every ambiguity resolved
- [TRADEOFFS.md](docs/TRADEOFFS.md) — What was deliberately not built
- [SOURCES.md](docs/SOURCES.md) — Source format research
