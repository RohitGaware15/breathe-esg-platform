PRODUCTION DEPLOYMENT GUIDE - RAILWAY.APP
==========================================

PREREQUISITES
-------------

1. GitHub account (to push your code)
2. Railway.app account (free tier available)
3. Docker and Docker Compose locally (for testing)

STEP 1: PREPARE FOR DEPLOYMENT
-------------------------------

1.1 Generate a secure SECRET_KEY
bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Copy this value.

1.2 Update .env for production
Edit .env:
  SECRET_KEY=<paste the generated key here>
  DEBUG=False
  DB_PASSWORD=<generate a strong password, min 20 chars>
  ALLOWED_HOSTS=yourdomain.railway.app,www.yourdomain.com
  CORS_ALLOWED_ORIGINS=https://yourdomain.railway.app,https://www.yourdomain.com
  VITE_API_URL=https://yourdomain.railway.app

1.3 Commit all changes
bash
git add docker-compose.yml Dockerfile* entrypoint.sh nginx.conf .env .gitignore
git commit -m "Add Docker and production configuration"

Create .gitignore:
bash
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

1.4 Push to GitHub
bash
git push origin main

STEP 2: RAILWAY DEPLOYMENT
----------------------------

2.1 Go to Railway.app
https://railway.app/

2.2 Create new project
- Click "New Project"
- Select "Deploy from GitHub"
- Select your repository
- Select the branch (usually main)

2.3 Railway will auto-detect docker-compose.yml
- You'll see 4 services: postgres, backend, frontend, nginx

2.4 Set environment variables
For each service, set:

POSTGRES SERVICE:
- (Railway handles this automatically)

BACKEND SERVICE:
  SECRET_KEY=<your secret key from step 1.1>
  DEBUG=False
  ALLOWED_HOSTS=yourdomain.railway.app
  CORS_ALLOWED_ORIGINS=https://yourdomain.railway.app
  VITE_API_URL=https://yourdomain.railway.app

FRONTEND SERVICE:
  VITE_API_URL=https://yourdomain.railway.app
  NODE_ENV=production

NGINX SERVICE:
  (No specific env vars needed)

2.5 Configure PostgreSQL plugin
- In Backend service settings, add PostgreSQL addon
- Railway will automatically set DATABASE_URL

2.6 Deploy
- Click "Deploy" button
- Wait for build (5-10 minutes on first deploy)
- Check logs for any errors

STEP 3: DOMAIN CONFIGURATION
-----------------------------

3.1 Get your Railway domain
In Railway dashboard:
- Backend service → Settings → Domains
- Click "Generate Domain" or add custom domain
- Note the domain: something.railway.app

3.2 Update environment variables with actual domain
In Railway:
- Go to each service → Variables
- Update ALLOWED_HOSTS with actual domain
- Update CORS_ALLOWED_ORIGINS with actual domain
- Click "Redeploy" for changes to take effect

3.3 (Optional) Custom domain
- Click "Add Custom Domain" in service settings
- Add yourdomain.com
- Update DNS CNAME record in your domain registrar:
  CNAME yourdomain.com → something.railway.app

STEP 4: VERIFY DEPLOYMENT
---------------------------

4.1 Check services are healthy
In Railway dashboard, verify all services show "Success" status.

4.2 Test the application
bash
curl https://yourdomain.railway.app/health/  # Should return 200

4.3 Access the app
Frontend:  https://yourdomain.railway.app/
Backend:   https://yourdomain.railway.app/api/
Admin:     https://yourdomain.railway.app/admin/

4.4 Login
Username: admin
Password: admin123

STEP 5: MONITORING AND MAINTENANCE
-----------------------------------

5.1 View logs
In Railway dashboard:
- Click any service → Deployments → View Logs
- Or use: docker-compose logs -f (locally)

5.2 Health checks
Railway automatically:
- Restarts failed services
- Scales based on demand (paid plans)
- Monitors database

5.3 Backup PostgreSQL
In Railway:
- Database → Backups → Auto backup enabled
- Manual backup: Backups → Create backup

5.4 Update environment secrets
Never commit real secrets. In Railway:
- Go to service → Variables
- Update values
- Click "Redeploy"

5.5 Deploy updates
After code changes:
bash
git add .
git commit -m "Update feature X"
git push origin main

Railway automatically redeploys from latest push.

STEP 6: TROUBLESHOOTING
-----------------------

Problem: Database connection failed
Solution: 
- Check DATABASE_URL is set in Backend variables
- Verify PostgreSQL service is healthy
- Check logs: docker-compose logs postgres

Problem: "Internal Server Error" on frontend
Solution:
- Check backend logs for errors
- Verify CORS_ALLOWED_ORIGINS is correct
- Check VITE_API_URL matches backend domain
- Trigger frontend rebuild: git push

Problem: Static files not loading (CSS/JS broken)
Solution:
- Frontend service status must be "Success"
- Check VITE_API_URL is correct
- Rebuild: docker-compose build frontend
- Push to GitHub to redeploy

Problem: Admin panel shows 404
Solution:
- Backend service must be healthy
- Check DATABASE_URL is set
- Run migrations: docker-compose exec backend python manage.py migrate

Problem: Cannot login with admin/admin123
Solution:
- Check setup_demo ran (logs should show it)
- Reset: docker-compose exec backend python manage.py setup_demo
- Or create new user: docker-compose exec backend python manage.py createsuperuser

STEP 7: SCALING (PAID RAILWAY PLANS)
-------------------------------------

For higher traffic:

7.1 Increase CPU/RAM
In Railway service → Resources → CPU/Memory slider

7.2 Increase database
Database service → Resources → Increase

7.3 Add more workers (backend)
Edit docker-compose.yml:
  backend:
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 8

Push to GitHub to redeploy.

STEP 8: SECURITY CHECKLIST
---------------------------

Before production:

☐ SECRET_KEY is random and 50+ characters
☐ DEBUG=False
☐ ALLOWED_HOSTS set to your domain only
☐ CORS_ALLOWED_ORIGINS set to your domain only
☐ Database password is strong (20+ chars)
☐ HTTPS is enabled (Railway does this automatically)
☐ Admin user password changed from default
☐ PostgreSQL backups enabled
☐ Logs are being monitored

STEP 9: COST ESTIMATION
-----------------------

Railway free tier includes:
- 100 hours/month per service
- Shared PostgreSQL
- 1 domain per project

For this project (all 4 services):
- ~400 hours/month (all services running)
- Exceeds free tier after ~5-10 days of continuous operation

Paid tier: $5/month + resource usage

To reduce costs:
- Stop services when not in use
- Use smaller database
- Combine frontend + nginx

STEP 10: ROLLBACK PROCEDURE
---------------------------

If deployment breaks:

10.1 Via GitHub
- Revert last commit locally
- Push to GitHub
- Railway auto-redeploys

10.2 Via Railway Dashboard
- Deployments tab
- Click previous successful deployment
- Click "Redeploy"

Database will not be affected.

TESTING LOCALLY BEFORE DEPLOYING
---------------------------------

Test with production settings locally:

bash
# Update .env
DEBUG=False
SECRET_KEY=<real secret key>

# Build and run
docker-compose down -v
docker-compose up --build

# Test at http://localhost:5173

# Check logs
docker-compose logs -f backend

Once working locally, push to Railway.

COMPLETE DEPLOYMENT CHECKLIST
------------------------------

☐ .env file created and configured
☐ .gitignore created
☐ docker-compose.yml in root
☐ All Dockerfiles in place
☐ Code pushed to GitHub
☐ Railway project created
☐ Environment variables set
☐ PostgreSQL addon configured
☐ Services deployed and healthy
☐ Domain working (yourdomain.railway.app)
☐ Login works (admin/admin123)
☐ File upload/review workflow tested
☐ Monitoring/logs accessible
☐ Backups enabled
☐ Security checklist passed

FINAL NOTES
-----------

1. First deploy takes 10-15 minutes
2. Subsequent deploys take 2-5 minutes
3. Railway has 99.9% uptime SLA
4. Database is always encrypted in transit
5. Logs are retained for 7 days
6. You can fork this for free tier testing

For detailed Railway docs: https://docs.railway.app/
