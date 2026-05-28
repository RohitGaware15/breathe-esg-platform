COMPLETE DOCKER SETUP - FILE PLACEMENT GUIDE
============================================

YOUR PROJECT STRUCTURE SHOULD BE:
---------------------------------

breathe-esg/
├── docker-compose.yml              ← Main orchestration file (USE docker-compose-final.yml content)
├── docker-compose-final.yml        ← Template (copy to docker-compose.yml)
├── entrypoint.sh                   ← Backend startup script
├── start.sh                        ← One-command startup script
├── nginx.conf                      ← Nginx configuration
├── .env.example                    ← Environment template (copy to .env)
├── .env                            ← Your actual secrets (created from .env.example) - DO NOT COMMIT
├── .gitignore                      ← Ignore sensitive files
├── DOCKER_SETUP_GUIDE.md           ← How to run locally
├── RAILWAY_DEPLOYMENT.md           ← How to deploy to production
├── README.md                       ← Project overview
│
├── backend/
│   ├── Dockerfile                  ← USE backend-dockerfile-final content
│   ├── backend-dockerfile-final    ← Template (copy to Dockerfile)
│   ├── entrypoint.sh               ← Copied from root
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── __init__.py
│   ├── apps/
│   │   ├── tenants/
│   │   ├── ingestion/
│   │   ├── normalization/
│   │   ├── review/
│   │   └── users/
│   └── [existing Django files...]
│
├── frontend/
│   ├── Dockerfile                  ← USE frontend-dockerfile-final content
│   ├── frontend-dockerfile-final   ← Template (copy to Dockerfile)
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── [existing React files...]
│
├── sample_data/
│   ├── sap_export.csv
│   ├── utility_export.csv
│   └── travel_concur.csv
│
└── docs/
    ├── MODEL.md
    ├── DECISIONS.md
    ├── TRADEOFFS.md
    └── SOURCES.md

SETUP INSTRUCTIONS (COPY-PASTE)
================================

1. COPY ALL FILES TO PROJECT ROOT:

Copy from /home/claude/ to your breathe-esg/ directory:

  docker-compose-final.yml    →  breathe-esg/docker-compose.yml
  entrypoint.sh               →  breathe-esg/entrypoint.sh
  start.sh                    →  breathe-esg/start.sh
  nginx.conf                  →  breathe-esg/nginx.conf
  .env.example                →  breathe-esg/.env.example
  DOCKER_SETUP_GUIDE.md       →  breathe-esg/DOCKER_SETUP_GUIDE.md
  RAILWAY_DEPLOYMENT.md       →  breathe-esg/RAILWAY_DEPLOYMENT.md

Bash command:
-----------
cd /home/claude
cp docker-compose-final.yml /path/to/breathe-esg/docker-compose.yml
cp entrypoint.sh /path/to/breathe-esg/
cp start.sh /path/to/breathe-esg/
cp nginx.conf /path/to/breathe-esg/
cp .env.example /path/to/breathe-esg/
cp DOCKER_SETUP_GUIDE.md /path/to/breathe-esg/
cp RAILWAY_DEPLOYMENT.md /path/to/breathe-esg/

2. COPY DOCKERFILES TO SUBDIRECTORIES:

Copy from /home/claude/ to backend and frontend:

  backend-dockerfile-final    →  breathe-esg/backend/Dockerfile
  frontend-dockerfile-final   →  breathe-esg/frontend/Dockerfile

Bash command:
-----------
cp /home/claude/backend-dockerfile-final /path/to/breathe-esg/backend/Dockerfile
cp /home/claude/frontend-dockerfile-final /path/to/breathe-esg/frontend/Dockerfile
cp /home/claude/entrypoint.sh /path/to/breathe-esg/backend/

3. CREATE .env FROM .env.example:

cd breathe-esg
cp .env.example .env

Edit .env to customize (passwords, domains, etc.)

4. (OPTIONAL) Create .gitignore:

cat > .gitignore << 'EOF'
*.pyc
__pycache__/
db.sqlite3
.env
.DS_Store
/backend/staticfiles/
/backend/media/
/frontend/dist/
/frontend/node_modules/
.venv/
venv/
*.egg-info/
dist/
build/
EOF

RUN THE PROJECT
===============

Option A: ONE-COMMAND STARTUP (Easiest)
---------------------------------------
cd breathe-esg
bash start.sh

Then open:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Nginx: http://localhost

Option B: MANUAL STARTUP
-----------------------
cd breathe-esg
docker-compose up --build

Same URLs as above.

WHAT EACH FILE DOES
====================

docker-compose.yml
- Orchestrates 4 services: postgres, backend, frontend, nginx
- Defines networks, volumes, dependencies
- Sets environment variables
- Configures health checks
- Manages restart policies

backend/Dockerfile
- Uses Python 3.11 slim image
- Installs PostgreSQL dev files (fixes psycopg2 errors)
- Installs all Python dependencies
- Copies Django code
- Runs entrypoint.sh for automatic setup

backend/entrypoint.sh
- Waits for PostgreSQL to be ready
- Runs Django migrations
- Creates demo admin user (admin/admin123)
- Creates Acme Corp demo tenant
- Starts Gunicorn server

frontend/Dockerfile
- Uses Node 20 Alpine image
- Installs npm dependencies
- Copies React code
- Runs Vite dev server on port 5173

nginx.conf
- Reverse proxy for frontend + backend
- Routes /api/* to backend:8000
- Routes everything else to frontend:5173
- Enables gzip compression
- Sets security headers

.env
- Database credentials
- Django SECRET_KEY
- Allowed hosts and CORS origins
- API URLs
- Environment (DEBUG, etc.)

start.sh
- Checks Docker is installed
- Creates .env from .env.example if missing
- Copies files in correct places
- Starts docker-compose
- Shows status and URLs

DOCKER COMMAND QUICK REFERENCE
==============================

Start everything:
docker-compose up --build

Start in background:
docker-compose up -d --build

Stop everything:
docker-compose down

Remove all data (including database):
docker-compose down -v

View logs:
docker-compose logs -f

View specific service logs:
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

Execute Django command:
docker-compose exec backend python manage.py <command>

Shell access to backend:
docker-compose exec backend bash

Database shell:
docker-compose exec postgres psql -U postgres -d breathe_esg

Rebuild specific service:
docker-compose build backend
docker-compose build frontend

FIXING COMMON ERRORS
====================

Error: "port 5432 already in use"
Solution: Change DB_PORT in .env or docker-compose.yml
  DB_PORT=5433:5432

Error: "psycopg2 build failed"
Solution: Already handled by Dockerfile. If still fails:
  docker-compose build --no-cache backend

Error: "connection refused at 5432"
Solution: PostgreSQL not ready yet. Wait 30 seconds and retry.
  docker-compose restart postgres

Error: "CORS error in browser"
Solution: Backend port wrong or CORS_ALLOWED_ORIGINS incorrect
  Check docker-compose.yml backend port is 8000
  Check .env CORS_ALLOWED_ORIGINS includes your frontend URL

Error: "ModuleNotFoundError: No module named 'django'"
Solution: Docker build failed. Rebuild:
  docker-compose build --no-cache backend

Error: "relation does not exist"
Solution: Migrations didn't run. Manually trigger:
  docker-compose exec backend python manage.py migrate

PRODUCTION DEPLOYMENT
====================

For Railway.app:
1. Push to GitHub
2. Create Railway project connected to GitHub
3. Railway auto-detects docker-compose.yml
4. Set environment variables
5. Deploy

See RAILWAY_DEPLOYMENT.md for detailed steps.

WHAT'S AUTOMATED
================

✓ Database initialization
✓ Database migrations
✓ Admin user creation (admin/admin123)
✓ Demo tenant creation (Acme Corp)
✓ Service startup ordering
✓ Health checks
✓ Automatic restarts
✓ Logging
✓ Nginx routing
✓ Static file serving
✓ Frontend build

WHAT'S NOT AUTOMATED (DO MANUALLY)
===================================

- Change default passwords (see Django admin)
- Upload real data files
- Configure emission factors
- Change SECRET_KEY for production
- Set up custom domain
- Enable HTTPS (Railway does this automatically)
- Backup/restore database

IMPORTANT NOTES
===============

1. This setup is development-ready with production patterns
2. For real production:
   - Change SECRET_KEY (use strong random value)
   - Change all default passwords
   - Enable HTTPS (Railway does this)
   - Set DEBUG=False (already in .env)
   - Use strong database password
   - Enable database backups

3. Docker volumes persist data even when containers stop
4. Use `docker-compose down -v` ONLY to completely reset

4. All services have health checks for automatic failure recovery

5. Logs are kept for debugging (max 10MB per service)

NEXT STEPS
==========

1. Copy all files to your project directory ✓
2. Run: bash start.sh ✓
3. Open http://localhost:5173
4. Login with admin / admin123
5. Upload sample CSVs and test
6. When ready: Push to GitHub and deploy to Railway

HELP & DEBUGGING
================

Check if all services started:
docker-compose ps

View detailed logs:
docker-compose logs -f --all

Check backend health:
curl http://localhost:8000/health/

Check frontend health:
curl http://localhost:5173/

Test database connection:
docker-compose exec postgres psql -U postgres -d breathe_esg -c "SELECT 1"

Done! Your entire project is now containerized with zero manual steps. 🚀
