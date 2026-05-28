#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          BREATHE ESG - Podman Quick Start                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

if ! command -v podman &> /dev/null; then
    echo -e "${RED}Podman is not installed. Install it with: sudo dnf install podman${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Podman $(podman --version)${NC}"

COMPOSE_CMD=""
if command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
    echo -e "${GREEN}✓ podman-compose available${NC}"
elif podman compose &> /dev/null 2>&1; then
    COMPOSE_CMD="podman compose"
    echo -e "${GREEN}✓ podman compose plugin available${NC}"
else
    echo -e "${RED}No podman-compose or podman compose plugin found."
    echo -e "Install with: sudo dnf install podman-compose${NC}"
    exit 1
fi

cd "$(dirname "$0")"

echo -e "${YELLOW}→ Building and starting containers...${NC}"
echo -e "${YELLOW}  First build may take 3-5 minutes.${NC}"
echo ""

$COMPOSE_CMD -f docker-compose-podman.yml up --build -d

echo ""
echo -e "${YELLOW}→ Waiting for services to be healthy...${NC}"
sleep 15

echo ""
echo -e "${BLUE}Checking service status...${NC}"
$COMPOSE_CMD -f docker-compose-podman.yml ps

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 BREATHE ESG IS RUNNING!                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Frontend:${NC}  http://localhost"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "  ${BLUE}Admin:${NC}     http://localhost:8000/admin/"
echo ""
echo -e "  ${YELLOW}Login:${NC}    admin / admin123"
echo ""
echo -e "  ${BLUE}Useful commands:${NC}"
echo "  View logs:     $COMPOSE_CMD -f docker-compose-podman.yml logs -f"
echo "  Stop:          $COMPOSE_CMD -f docker-compose-podman.yml down"
echo "  Stop + clean:  $COMPOSE_CMD -f docker-compose-podman.yml down -v"
echo "  Shell backend: $COMPOSE_CMD -f docker-compose-podman.yml exec backend bash"
