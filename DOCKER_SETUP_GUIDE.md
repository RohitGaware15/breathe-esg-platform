COMPLETE DOCKER AUTOMATION GUIDE
================================

STEP 1: SETUP (ONE TIME)
------------------------

1.1 Navigate to project root
bash
cd breathe-esg

1.2 Copy environment file
bash
cp .env.example .env

1.3 (Optional) Edit .env for production:
- Change SECRET_KEY to something random
- Change DB_PASSWORD to something strong
- Set ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS for your domain

STEP 2: BUILD AND RUN (ZERO MANUAL STEPS)
------------------------------------------

2.1 Start all services
bash
docker-compose up --build

This ONE command will:
✓ Build PostgreSQL image
✓ Build Django backend image
✓ Build React frontend image
✓ Start all 3 services
✓ Run Django migrations automatically
✓ Create admin user (admin/admin123) + demo tenant automatically
✓ Compile React app
✓ Start Nginx reverse proxy

Wait 30-40 seconds for everything to be healthy.

2.2 Verify all services are running
bash
docker-compose ps

Expected output:
NAME                COMMAND                  STATUS
breathe-pg          postgres                 Up (healthy)
breathe-backend     gunicorn ...             Up (healthy)
breathe-frontend    serve ...                Up
breathe-nginx       nginx ...                Up

STEP 3: ACCESS THE APP
----------------------

Option A — Via Nginx (production-like, port 80):
- Frontend: http://localhost/
- Backend API: http://localhost/api/
- Admin: http://localhost/admin/

Option B — Direct to services:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Postgres: localhost:5432

Default credentials:
- Username: admin
- Password: admin123

STEP 4: STOP EVERYTHING
-----------------------

bash
docker-compose down

To also remove PostgreSQL data:
bash
docker-compose down -v

STEP 5: VIEW LOGS
-----------------

All services:
bash
docker-compose logs -f

Just backend:
bash
docker-compose logs -f backend

Just frontend:
bash
docker-compose logs -f frontend

Just database:
bash
docker-compose logs -f postgres

STEP 6: EXECUTE MANAGEMENT COMMANDS
------------------------------------

Run Django management commands inside the container:

bash
docker-compose exec backend python manage.py <command>

Examples:

Create a new superuser:
bash
docker-compose exec backend python manage.py createsuperuser

Reset database:
bash
docker-compose exec backend python manage.py migrate zero ingestion
docker-compose exec backend python manage.py migrate

Shell (interactive Python):
bash
docker-compose exec backend python manage.py shell

STEP 7: TROUBLESHOOTING
-----------------------

Problem: Port 5432 already in use
Solution: Change port in docker-compose.yml:
  postgres:
    ports:
      - "5433:5432"  # Use 5433 instead

Problem: Port 8000 already in use
Solution: Stop other services or change docker-compose.yml:
  backend:
    ports:
      - "8001:8000"  # Use 8001 instead

Problem: ModuleNotFoundError for Django apps
Solution: Make sure migrations ran. Check logs:
bash
docker-compose logs backend

If migrations didn't run, manually trigger:
bash
docker-compose exec backend python manage.py migrate

Problem: Database connection refused
Solution: PostgreSQL may not be healthy yet. Wait 30 seconds and refresh.
If still broken:
bash
docker-compose logs postgres
docker-compose restart postgres

Problem: React won't load / CORS error
Solution: Backend and frontend not communicating.
Check docker-compose logs:
bash
docker-compose logs frontend
docker-compose logs backend

Verify CORS_ALLOWED_ORIGINS in .env includes frontend URL.

Problem: psycopg2 or numpy compilation fails during build
Solution: This is handled by the Dockerfile. If it still fails:
bash
docker-compose build --no-cache backend

This rebuilds from scratch without cached layers.

STEP 8: PRODUCTION DEPLOYMENT (e.g., Railway)
----------------------------------------------

8.1 Push to GitHub
bash
git add .
git commit -m "Add Docker setup"
git push origin main

8.2 On Railway (railway.app):
- Create new project
- Connect GitHub repo
- Railway auto-detects docker-compose.yml
- Add PostgreSQL plugin (Railway will set DATABASE_URL automatically)
- Set environment variables:
  - SECRET_KEY (generate random: openssl rand -hex 32)
  - DEBUG=False
  - ALLOWED_HOSTS=yourdomain.railway.app
  - CORS_ALLOWED_ORIGINS=https://yourdomain.railway.app

8.3 Railway will automatically:
✓ Build images
✓ Run migrations
✓ Start all services
✓ Expose public URLs

STEP 9: FILE LOCATIONS IN CONTAINER
------------------------------------

Backend:
- /app/manage.py
- /app/config/settings.py
- /app/apps/

Frontend:
- /app/dist/  (built files)
- /app/src/   (source)

Database:
- /var/lib/postgresql/data  (persistent volume)

STEP 10: VERIFY EVERYTHING WORKS
---------------------------------

10.1 Check backend is running
bash
curl http://localhost:8000/api/auth/me/

Expected: 401 response (not authenticated)

10.2 Check frontend is running
bash
curl http://localhost:5173/

Expected: HTML response with React app

10.3 Check database
bash
docker-compose exec postgres psql -U postgres -d breathe_esg -c "SELECT COUNT(*) FROM ingestion_ingestionbatch;"

Expected: Tables exist (even if count is 0)

10.4 Test the full flow
- Open http://localhost:5173
- Login with admin / admin123
- Go to Upload
- Upload one of the sample CSV files
- Go to Review
- See the normalized data

COMMON COMMANDS REFERENCE
--------------------------

Start all services:
docker-compose up

Start in background (daemon mode):
docker-compose up -d

View logs:
docker-compose logs -f

Stop all services:
docker-compose down

Remove all data (including DB):
docker-compose down -v

Rebuild a specific service:
docker-compose build backend

Rebuild all without cache:
docker-compose build --no-cache

Run command in backend:
docker-compose exec backend python manage.py migrate

Get shell access to backend:
docker-compose exec backend bash

Connect to database:
docker-compose exec postgres psql -U postgres -d breathe_esg

DONE!
-----

Your entire project now runs with:
bash
docker-compose up --build

No more:
- "pip install failed"
- "postgres won't start"
- "migration didn't run"
- "CORS error"
- "port already in use"

Everything is containerized, isolated, and reproducible.
