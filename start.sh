
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          BREATHE ESG - Docker Automation Setup            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Get the directory where script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}→ Creating .env file from .env.example${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created. Edit it to change passwords/secrets.${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Parse command line arguments
BUILD_FLAG=""
CLEAN_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --clean)
            CLEAN_FLAG="1"
            shift
            ;;
        --help)
            echo "Usage: bash start.sh [--build] [--clean]"
            echo ""
            echo "Options:"
            echo "  --build    Rebuild Docker images before starting"
            echo "  --clean    Remove all containers and volumes before starting"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Clean up if requested
if [ "$CLEAN_FLAG" == "1" ]; then
    echo -e "${YELLOW}→ Cleaning up existing containers and volumes${NC}"
    docker-compose down -v 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
fi

# Copy backend entrypoint if it exists
if [ -f "entrypoint.sh" ] && [ ! -f "backend/entrypoint.sh" ]; then
    echo -e "${YELLOW}→ Copying entrypoint script to backend${NC}"
    mkdir -p backend
    cp entrypoint.sh backend/entrypoint.sh
    chmod +x backend/entrypoint.sh
fi

# Copy Dockerfiles
echo -e "${YELLOW}→ Setting up Dockerfiles${NC}"
if [ -f "backend-dockerfile-final" ]; then
    cp backend-dockerfile-final backend/Dockerfile
fi
if [ -f "frontend-dockerfile-final" ]; then
    cp frontend-dockerfile-final frontend/Dockerfile
fi
if [ -f "docker-compose-final.yml" ]; then
    cp docker-compose-final.yml docker-compose.yml
fi
echo -e "${GREEN}✓ Dockerfiles configured${NC}"

# Start services
echo -e "${BLUE}→ Starting Docker services...${NC}"
echo -e "${YELLOW}This may take 30-40 seconds on first run.${NC}"
echo ""

docker-compose up $BUILD_FLAG &

# Wait for backend to be healthy
echo -e "${YELLOW}→ Waiting for services to be healthy...${NC}"
sleep 10

# Show status
echo ""
echo -e "${BLUE}Checking service status...${NC}"
sleep 20

docker-compose ps

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 SETUP COMPLETE!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📱 Frontend:     http://localhost:5173"
echo "🔧 Backend API:  http://localhost:8000"
echo "🌐 Nginx:        http://localhost"
echo "🗄️  Database:     localhost:5432"
echo ""

echo "📝 Default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""

echo "📚 Useful commands:"
echo "   View logs:           docker-compose logs -f"
echo "   Stop services:       docker-compose down"
echo "   Remove all data:     docker-compose down -v"
echo "   Shell access:        docker-compose exec backend bash"
echo "   Database shell:      docker-compose exec postgres psql -U postgres -d breathe_esg"
echo ""

echo -e "${YELLOW}→ To stop services, press Ctrl+C${NC}"
echo ""

# Keep docker-compose running in foreground
wait
