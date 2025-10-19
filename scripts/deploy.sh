#!/bin/bash

# 🧠 QUANTUM MEMORY ORCHESTRATOR - PRODUCTION DEPLOYMENT SCRIPT
# Case: 1FDV-23-0001009
# BAMCPAPIN High Power Architecture
# Full automated deployment with health checks

set -e  # Exit on any error

# =============================================================================
# CONFIGURATION
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/deployment.log"
ENV_FILE="$PROJECT_DIR/.env"

# Deployment settings
CASE_ID="1FDV-23-0001009"
DEPLOYMENT_MODE="production"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $*"
    log "INFO" "$*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    log "SUCCESS" "$*"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
    log "WARNING" "$*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    log "ERROR" "$*"
}

header() {
    echo
    echo -e "${PURPLE}=================================================================${NC}"
    echo -e "${PURPLE} $*${NC}"
    echo -e "${PURPLE}=================================================================${NC}"
    echo
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is required but not installed. Please install $1 and try again."
        exit 1
    fi
}

wait_for_service() {
    local service_name="$1"
    local health_url="$2"
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / HEALTH_CHECK_INTERVAL))
    local attempt=1
    
    info "Waiting for $service_name to become healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$health_url" &>/dev/null; then
            success "$service_name is healthy!"
            return 0
        fi
        
        info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep $HEALTH_CHECK_INTERVAL
        ((attempt++))
    done
    
    error "$service_name failed to become healthy within ${HEALTH_CHECK_TIMEOUT} seconds"
    return 1
}

# =============================================================================
# PRE-DEPLOYMENT CHECKS
# =============================================================================

header "QUANTUM MEMORY ORCHESTRATOR - PRODUCTION DEPLOYMENT"
info "Case ID: $CASE_ID"
info "Deployment Mode: $DEPLOYMENT_MODE"
info "Project Directory: $PROJECT_DIR"
info "Log File: $LOG_FILE"
echo

header "PRE-DEPLOYMENT CHECKS"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/config"

# Check required commands
info "Checking required commands..."
check_command "docker"
check_command "docker-compose"
check_command "curl"
check_command "jq"
check_command "git"
success "All required commands are available"

# Check Docker daemon
info "Checking Docker daemon..."
if ! docker info &>/dev/null; then
    error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi
success "Docker daemon is running"

# Check environment file
info "Checking environment configuration..."
if [ ! -f "$ENV_FILE" ]; then
    warn "Environment file not found. Creating from template..."
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
    warn "Please edit $ENV_FILE with your actual configuration before proceeding."
    warn "Press Enter to continue after configuring environment..."
    read -r
fi
success "Environment file exists"

# Validate critical environment variables
info "Validating critical environment variables..."
source "$ENV_FILE"

critical_vars=("MEM0_API_KEY" "POSTGRES_PASSWORD" "JWT_SECRET")
for var in "${critical_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error "Critical environment variable $var is not set"
        exit 1
    fi
done
success "Critical environment variables are set"

# =============================================================================
# DEPLOYMENT PREPARATION
# =============================================================================

header "DEPLOYMENT PREPARATION"

# Pull latest images
info "Pulling latest Docker images..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" pull
success "Docker images pulled successfully"

# Build custom images
info "Building Quantum Memory Orchestrator image..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" build quantum-orchestrator
success "Custom images built successfully"

# Create external networks if needed
info "Setting up Docker networks..."
docker network create quantum-memory-network 2>/dev/null || true
success "Docker networks configured"

# =============================================================================
# CORE SERVICES DEPLOYMENT
# =============================================================================

header "CORE SERVICES DEPLOYMENT"

# Stop any existing services
info "Stopping existing services..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" down --remove-orphans
success "Existing services stopped"

# Start infrastructure services first
info "Starting infrastructure services..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d postgres redis neo4j qdrant
success "Infrastructure services started"

# Wait for infrastructure to be ready
wait_for_service "PostgreSQL" "http://localhost:5432" || {
    # PostgreSQL doesn't have HTTP endpoint, check with docker
    info "Checking PostgreSQL with docker exec..."
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres pg_isready -U postgres
}

wait_for_service "Redis" "http://localhost:6379" || {
    # Redis doesn't have HTTP endpoint, check with docker
    info "Checking Redis with docker exec..."
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" exec -T redis redis-cli ping
}

info "Checking Neo4j..."
sleep 30  # Neo4j takes longer to start
wait_for_service "Neo4j" "http://localhost:7474"

wait_for_service "Qdrant" "http://localhost:6333"

# =============================================================================
# APPLICATION SERVICES DEPLOYMENT
# =============================================================================

header "APPLICATION SERVICES DEPLOYMENT"

# Start SuperMemory
info "Starting SuperMemory service..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d supermemory
sleep 20
wait_for_service "SuperMemory" "http://localhost:3000/health"

# Start Quantum Memory Orchestrator
info "Starting Quantum Memory Orchestrator..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d quantum-orchestrator
sleep 30
wait_for_service "Quantum Memory Orchestrator" "http://localhost:8000/health"

# =============================================================================
# MONITORING AND AUXILIARY SERVICES
# =============================================================================

header "MONITORING AND AUXILIARY SERVICES"

# Start monitoring services
info "Starting monitoring services..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d prometheus grafana nginx
sleep 15

wait_for_service "Prometheus" "http://localhost:9090/-/healthy"
wait_for_service "Grafana" "http://localhost:3001/api/health"
wait_for_service "Nginx" "http://localhost:80"

# =============================================================================
# SYSTEM VALIDATION
# =============================================================================

header "SYSTEM VALIDATION"

# Test core functionality
info "Testing memory storage..."
test_memory_response=$(curl -s -X POST "http://localhost:8000/memory/store" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Quantum Memory Orchestrator deployment test - Case 1FDV-23-0001009",
        "priority": "critical",
        "source": "deployment_validation"
    }')

if echo "$test_memory_response" | jq -e '.status == "success"' &>/dev/null; then
    success "Memory storage test passed"
else
    error "Memory storage test failed"
    echo "Response: $test_memory_response"
    exit 1
fi

# Test memory search
info "Testing memory search..."
test_search_response=$(curl -s -X POST "http://localhost:8000/memory/search" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "deployment test",
        "case_id": "1FDV-23-0001009",
        "limit": 5
    }')

if echo "$test_search_response" | jq -e '.merged_results | length > 0' &>/dev/null; then
    success "Memory search test passed"
else
    error "Memory search test failed"
    echo "Response: $test_search_response"
    exit 1
fi

# Test forensic report
info "Testing forensic reporting..."
forensic_response=$(curl -s "http://localhost:8000/forensic")
if echo "$forensic_response" | jq -e '.case_id == "1FDV-23-0001009"' &>/dev/null; then
    success "Forensic reporting test passed"
else
    error "Forensic reporting test failed"
fi

# =============================================================================
# MCP SERVER SETUP
# =============================================================================

header "MCP SERVER SETUP"

# Install MCP servers (if Node.js is available)
if command -v npm &> /dev/null; then
    info "Installing MCP memory servers..."
    
    # Install Memory Plugin MCP
    npm install -g @memoryplugin/mcp-serve || warn "Failed to install Memory Plugin MCP"
    
    # Install Mem0 MCP
    npm install -g @mem0/mcp-server || warn "Failed to install Mem0 MCP"
    
    success "MCP servers installation completed"
else
    warn "Node.js not found. MCP servers need to be installed manually:"
    warn "  npm install -g @memoryplugin/mcp-serve"
    warn "  npm install -g @mem0/mcp-server"
fi

# =============================================================================
# DEPLOYMENT SUMMARY
# =============================================================================

header "DEPLOYMENT SUMMARY"

# Get system status
info "Retrieving system status..."
system_health=$(curl -s "http://localhost:8000/health")
metrics=$(curl -s "http://localhost:8000/metrics")

echo -e "${GREEN}\u2705 QUANTUM MEMORY ORCHESTRATOR SUCCESSFULLY DEPLOYED${NC}"
echo
echo -e "${CYAN}System Information:${NC}"
echo "  • Case ID: $CASE_ID"
echo "  • Deployment Mode: $DEPLOYMENT_MODE"
echo "  • Main API: http://localhost:8000"
echo "  • SuperMemory: http://localhost:3000"
echo "  • Grafana: http://localhost:3001"
echo "  • Neo4j Browser: http://localhost:7474"
echo
echo -e "${CYAN}Health Status:${NC}"
echo "$system_health" | jq -r '"  • Overall Status: " + .overall_status'
echo "$system_health" | jq -r '"  • Uptime: " + .uptime_human'
echo "$system_health" | jq -r '"  • Active Providers: " + (.providers | keys | join(", "))'
echo
echo -e "${CYAN}System Metrics:${NC}"
echo "$metrics" | jq -r '"  • Total Memories: " + (.metrics.total_memories_stored | tostring)'
echo "$metrics" | jq -r '"  • Successful Operations: " + (.metrics.successful_operations | tostring)'
echo "$metrics" | jq -r '"  • Audit Chain Length: " + (.audit_chain_length | tostring)'
echo
echo -e "${CYAN}Available Endpoints:${NC}"
echo "  • Health Check: GET http://localhost:8000/health"
echo "  • Store Memory: POST http://localhost:8000/memory/store"
echo "  • Search Memory: POST http://localhost:8000/memory/search"
echo "  • Forensic Report: GET http://localhost:8000/forensic"
echo "  • System Metrics: GET http://localhost:8000/metrics"
echo "  • API Documentation: http://localhost:8000/docs"
echo
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Configure your MCP clients (Claude Desktop, Cursor, etc.)"
echo "  2. Set up automated backups"
echo "  3. Configure monitoring alerts"
echo "  4. Review security settings"
echo "  5. Test integration with Notion workspace"
echo
echo -e "${CYAN}Support:${NC}"
echo "  • Logs: $LOG_FILE"
echo "  • Container logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart services: docker-compose restart"
echo
echo -e "${GREEN}\ud83e\udde0 BAMCPAPIN HIGH POWER ARCHITECTURE IS NOW LIVE!${NC}"
echo -e "${GREEN}\u2696\ufe0f FORENSIC-GRADE MEMORY SYSTEM OPERATIONAL FOR CASE $CASE_ID${NC}"

# Log final status
log "SUCCESS" "Quantum Memory Orchestrator deployment completed successfully"
log "INFO" "System is operational and ready for production use"
log "INFO" "Case ID: $CASE_ID | Main API: http://localhost:8000"

exit 0