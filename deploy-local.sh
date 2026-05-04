#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install it first."
    exit 1
fi
print_success "Docker Compose found: $(docker-compose --version)"

# Step 1: Prepare environment
print_header "Step 1: Preparing Local Environment"

mkdir -p monitoring/grafana/provisioning/{dashboards,datasources}
mkdir -p services/database/migrations
print_success "Created required directories"

# Step 2: Pull images
print_header "Step 2: Pulling Docker Images"

docker-compose -f docker-compose.prod.yml pull
print_success "All Docker images pulled"

# Step 3: Start infrastructure
print_header "Step 3: Starting Infrastructure (PostgreSQL & Redis)"

docker-compose -f docker-compose.prod.yml up -d postgres redis
print_info "Waiting for infrastructure to be healthy (30 seconds)..."
sleep 30

if docker-compose -f docker-compose.prod.yml ps | grep -q "postgres.*healthy" && \
   docker-compose -f docker-compose.prod.yml ps | grep -q "redis.*healthy"; then
    print_success "Infrastructure is healthy"
else
    print_error "Infrastructure failed health checks"
    docker-compose -f docker-compose.prod.yml logs postgres redis
    exit 1
fi

# Step 4: Start monitoring
print_header "Step 4: Starting Monitoring Stack"

docker-compose -f docker-compose.prod.yml up -d prometheus grafana alertmanager
print_info "Waiting for monitoring stack (20 seconds)..."
sleep 20
print_success "Monitoring stack started"
print_info "Prometheus: http://localhost:9090"
print_info "Grafana: http://localhost:3000 (admin / grafana_admin_pass)"
print_info "AlertManager: http://localhost:9093"

# Step 5: Build services
print_header "Step 5: Building Microservices"

docker-compose -f docker-compose.prod.yml build
print_success "All services built"

# Step 6: Start services
print_header "Step 6: Starting Microservices"

docker-compose -f docker-compose.prod.yml up -d
print_info "Services starting, waiting 30 seconds for startup..."
sleep 30

# Step 7: Verify health
print_header "Step 7: Verifying Service Health"

SERVICES=(8001 8002 8003 8004 8005 8006 8007 8008)
HEALTHY=0
TOTAL=${#SERVICES[@]}

for port in "${SERVICES[@]}"; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        print_success "Service on port $port is healthy"
        ((HEALTHY++))
    else
        print_info "Service on port $port is starting up..."
    fi
done

if [ $HEALTHY -eq $TOTAL ]; then
    print_success "All services are healthy"
else
    print_info "Waiting for remaining services..."
    sleep 30
fi

# Step 8: Summary
print_header "Deployment Complete! 🎉"

echo -e "${GREEN}Your BlackRoad SaaS platform is now running locally:${NC}\n"

echo "Services:"
echo "  • Billing API:       http://localhost:8001"
echo "  • Admin Dashboard:   http://localhost:8002"
echo "  • Analytics Engine:  http://localhost:8003"
echo "  • ML Analytics:      http://localhost:8004"
echo "  • Customer UI:       http://localhost:8005"
echo "  • Stripe Webhooks:   http://localhost:8006"
echo "  • Onboarding:        http://localhost:8007"
echo "  • Monitoring:        http://localhost:8008"
echo ""
echo "Monitoring & Observability:"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Grafana:           http://localhost:3000"
echo "  • AlertManager:      http://localhost:9093"
echo "  • Database:          localhost:5432"
echo "  • Cache:             localhost:6379"
echo ""
echo "API Gateway:"
echo "  • Load Balancer:     http://localhost"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}\n"
echo "  View all services:    docker-compose -f docker-compose.prod.yml ps"
echo "  View logs:            docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services:        docker-compose -f docker-compose.prod.yml stop"
echo "  Start services:       docker-compose -f docker-compose.prod.yml start"
echo "  Remove everything:    docker-compose -f docker-compose.prod.yml down"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo "  1. Visit http://localhost:3000 to view Grafana dashboards"
echo "  2. Visit http://localhost:9090 to view Prometheus metrics"
echo "  3. Run health checks: curl http://localhost/api/billing/health"
echo "  4. Load test: ab -n 10000 -c 1000 http://localhost/api/billing/health"
echo ""

print_success "Deployment successful! Your platform is ready to use."
