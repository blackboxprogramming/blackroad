#!/bin/bash

# BlackRoad Platform Management CLI
# Simple tool for managing the local deployment

set -e

COMPOSE_FILE="docker-compose.prod.yml"
COMPOSE_CMD="docker-compose -f $COMPOSE_FILE"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help
show_help() {
    cat << 'HELP'
BlackRoad Platform Management CLI

Usage: ./blackroad-cli.sh [COMMAND] [OPTIONS]

Commands:
  deploy          Deploy entire platform (./deploy-local.sh)
  status          Show status of all services
  logs [SERVICE]  View logs (all services or specific)
  restart [SVC]   Restart service (all or specific)
  stop            Stop all services
  start           Start all services
  health          Health check all services
  scale SVC NUM   Scale service to N instances
  db              Connect to database
  cache           Connect to Redis cache
  metrics         Show current metrics
  clean           Clean up everything (⚠️  removes data)
  help            Show this help message

Examples:
  ./blackroad-cli.sh status
  ./blackroad-cli.sh logs billing-api
  ./blackroad-cli.sh restart admin-dashboard
  ./blackroad-cli.sh health
  ./blackroad-cli.sh scale billing-api 3
  ./blackroad-cli.sh metrics

For help on specific command:
  ./blackroad-cli.sh [COMMAND] help

HELP
}

# Status
cmd_status() {
    echo -e "${BLUE}Service Status:${NC}\n"
    $COMPOSE_CMD ps
}

# Logs
cmd_logs() {
    if [ -z "$1" ] || [ "$1" = "help" ]; then
        echo "Usage: ./blackroad-cli.sh logs [SERVICE]"
        echo "Examples:"
        echo "  ./blackroad-cli.sh logs              # All services"
        echo "  ./blackroad-cli.sh logs billing-api  # Specific service"
        return
    fi
    
    if [ "$1" = "all" ]; then
        $COMPOSE_CMD logs -f
    else
        $COMPOSE_CMD logs -f "$1"
    fi
}

# Restart
cmd_restart() {
    if [ -z "$1" ] || [ "$1" = "help" ]; then
        echo "Usage: ./blackroad-cli.sh restart [SERVICE]"
        echo "Examples:"
        echo "  ./blackroad-cli.sh restart              # Restart all"
        echo "  ./blackroad-cli.sh restart billing-api  # Restart specific"
        return
    fi
    
    if [ "$1" = "all" ]; then
        echo "Restarting all services..."
        $COMPOSE_CMD restart
    else
        echo "Restarting $1..."
        $COMPOSE_CMD restart "$1"
    fi
}

# Stop
cmd_stop() {
    echo "Stopping all services..."
    $COMPOSE_CMD stop
}

# Start
cmd_start() {
    echo "Starting all services..."
    $COMPOSE_CMD start
}

# Health check
cmd_health() {
    echo -e "${BLUE}Health Check:${NC}\n"
    
    SERVICES=(8001 8002 8003 8004 8005 8006 8007 8008)
    HEALTHY=0
    
    for port in "${SERVICES[@]}"; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Service :$port is healthy"
            ((HEALTHY++))
        else
            echo -e "${RED}✗${NC} Service :$port is down"
        fi
    done
    
    TOTAL=${#SERVICES[@]}
    echo -e "\nResult: $HEALTHY/$TOTAL services healthy"
}

# Scale service
cmd_scale() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "Usage: ./blackroad-cli.sh scale [SERVICE] [NUM]"
        echo "Example: ./blackroad-cli.sh scale billing-api 3"
        return
    fi
    
    echo "Scaling $1 to $2 instances..."
    $COMPOSE_CMD up -d --scale "$1=$2"
}

# Database
cmd_db() {
    echo "Connecting to PostgreSQL..."
    $COMPOSE_CMD exec postgres psql -U blackroad -d blackroad_prod
}

# Cache
cmd_cache() {
    echo "Connecting to Redis..."
    $COMPOSE_CMD exec redis redis-cli -a cache_secure_pass_12345
}

# Metrics
cmd_metrics() {
    echo -e "${BLUE}Prometheus Metrics:${NC}"
    echo "http://localhost:9090"
    echo ""
    echo -e "${BLUE}Grafana Dashboards:${NC}"
    echo "http://localhost:3000"
    echo ""
    echo "Username: admin"
    echo "Password: grafana_admin_pass"
}

# Clean
cmd_clean() {
    read -p "Remove everything including data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning up..."
        $COMPOSE_CMD down -v
        echo -e "${GREEN}Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
}

# Main
case "$1" in
    deploy) ./deploy-local.sh ;;
    status) cmd_status ;;
    logs) cmd_logs "$2" ;;
    restart) cmd_restart "$2" ;;
    stop) cmd_stop ;;
    start) cmd_start ;;
    health) cmd_health ;;
    scale) cmd_scale "$2" "$3" ;;
    db) cmd_db ;;
    cache) cmd_cache ;;
    metrics) cmd_metrics ;;
    clean) cmd_clean ;;
    help|"") show_help ;;
    *) 
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
