#!/bin/bash

##############################################################################
# BlackRoad Disaster Recovery & Backup Management
# 
# Complete automation for backup, restore, and disaster recovery operations
# Usage: ./disaster-recovery.sh <command> [options]
##############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:=/backups}"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
DOCKER_NETWORK="blackroad-network"
POSTGRES_CONTAINER="postgres"
REDIS_CONTAINER="redis"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-changeme123}"
BACKUP_RETENTION_DAYS=30

# Timestamps
NOW=$(date +%Y%m%d_%H%M%S)
TODAY=$(date +%Y_%m_%d)

##############################################################################
# UTILITY FUNCTIONS
##############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    log_success "Docker found"
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    log_success "Docker Compose found"
}

check_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        mkdir -p "$BACKUP_DIR/postgres/full"
        mkdir -p "$BACKUP_DIR/postgres/incremental"
        mkdir -p "$BACKUP_DIR/postgres/wal"
        mkdir -p "$BACKUP_DIR/redis/snapshots"
        mkdir -p "$BACKUP_DIR/config"
        mkdir -p "$BACKUP_DIR/volumes"
        mkdir -p "$BACKUP_DIR/metadata"
    fi
}

verify_containers_running() {
    log_info "Verifying containers are running..."
    
    if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_error "PostgreSQL container not running"
        return 1
    fi
    
    if ! docker ps | grep -q "$REDIS_CONTAINER"; then
        log_error "Redis container not running"
        return 1
    fi
    
    log_success "All containers running"
    return 0
}

calculate_checksum() {
    if command -v sha256sum &> /dev/null; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

encrypt_file() {
    local input_file=$1
    local output_file=$2
    
    if command -v openssl &> /dev/null; then
        openssl enc -aes-256-cbc -salt -in "$input_file" -out "$output_file" -k "$ENCRYPTION_KEY" -pbkdf2
        log_success "Encrypted: $output_file"
    else
        cp "$input_file" "$output_file"
        log_warning "OpenSSL not found, backup stored unencrypted"
    fi
}

decrypt_file() {
    local input_file=$1
    local output_file=$2
    
    if command -v openssl &> /dev/null; then
        openssl enc -aes-256-cbc -d -in "$input_file" -out "$output_file" -k "$ENCRYPTION_KEY" -pbkdf2
        log_success "Decrypted: $output_file"
    else
        cp "$input_file" "$output_file"
        log_warning "OpenSSL not found"
    fi
}

##############################################################################
# BACKUP FUNCTIONS
##############################################################################

backup_postgres() {
    log_info "Starting PostgreSQL backup..."
    
    check_backup_dir
    
    local backup_file="$BACKUP_DIR/postgres/full/full_$TODAY.sql"
    local compressed_file="$backup_file.gz"
    local encrypted_file="$compressed_file.enc"
    
    if [ -f "$encrypted_file" ]; then
        log_warning "Backup already exists for today, using existing: $encrypted_file"
        return 0
    fi
    
    # Dump database
    docker exec -t $POSTGRES_CONTAINER pg_dump -U postgres -d roaddb \
        --verbose --no-acl --no-owner > "$backup_file"
    
    if [ ! -f "$backup_file" ]; then
        log_error "PostgreSQL dump failed"
        return 1
    fi
    
    log_success "PostgreSQL dump created: $(du -h $backup_file | cut -f1)"
    
    # Compress
    gzip -f "$backup_file"
    log_success "Compressed: $(du -h $compressed_file | cut -f1)"
    
    # Encrypt
    encrypt_file "$compressed_file" "$encrypted_file"
    rm "$compressed_file"
    
    # Calculate checksum
    local checksum=$(calculate_checksum "$encrypted_file")
    echo "$checksum $encrypted_file" >> "$BACKUP_DIR/metadata/checksums_$TODAY.sha256"
    
    log_success "PostgreSQL backup complete: $encrypted_file"
    echo "$encrypted_file"
}

backup_redis() {
    log_info "Starting Redis backup..."
    
    check_backup_dir
    
    local backup_file="$BACKUP_DIR/redis/snapshots/redis_$TODAY.rdb"
    local compressed_file="$backup_file.gz"
    local encrypted_file="$compressed_file.enc"
    
    if [ -f "$encrypted_file" ]; then
        log_warning "Redis backup already exists for today"
        return 0
    fi
    
    # Trigger Redis save
    docker exec $REDIS_CONTAINER redis-cli BGSAVE
    sleep 2
    
    # Copy dump.rdb from container
    docker cp $REDIS_CONTAINER:/data/dump.rdb "$backup_file"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Redis dump failed"
        return 1
    fi
    
    log_success "Redis dump created: $(du -h $backup_file | cut -f1)"
    
    # Compress
    gzip -f "$backup_file"
    log_success "Compressed: $(du -h $compressed_file | cut -f1)"
    
    # Encrypt
    encrypt_file "$compressed_file" "$encrypted_file"
    rm "$compressed_file"
    
    # Calculate checksum
    local checksum=$(calculate_checksum "$encrypted_file")
    echo "$checksum $encrypted_file" >> "$BACKUP_DIR/metadata/checksums_$TODAY.sha256"
    
    log_success "Redis backup complete: $encrypted_file"
    echo "$encrypted_file"
}

backup_config() {
    log_info "Starting configuration backup..."
    
    check_backup_dir
    
    local config_tar="$BACKUP_DIR/config/config_$TODAY.tar.gz"
    
    if [ -f "$config_tar" ]; then
        log_warning "Config backup already exists for today"
        return 0
    fi
    
    # Backup docker-compose and config files
    tar -czf "$config_tar" \
        docker-compose.prod.yml \
        .env \
        monitoring/prometheus.yml \
        monitoring/alert-rules.yml \
        monitoring/grafana/provisioning/ \
        2>/dev/null || true
    
    if [ ! -f "$config_tar" ]; then
        log_error "Configuration backup failed"
        return 1
    fi
    
    log_success "Configuration backup complete: $(du -h $config_tar | cut -f1)"
    echo "$config_tar"
}

backup_volumes() {
    log_info "Starting volumes backup..."
    
    check_backup_dir
    
    local volumes_tar="$BACKUP_DIR/volumes/volumes_$TODAY.tar.gz"
    
    if [ -f "$volumes_tar" ]; then
        log_warning "Volumes backup already exists for today"
        return 0
    fi
    
    # Backup Docker volumes (if any app-specific data)
    tar -czf "$volumes_tar" \
        data/ \
        logs/ \
        2>/dev/null || true
    
    if [ -f "$volumes_tar" ]; then
        log_success "Volumes backup complete: $(du -h $volumes_tar | cut -f1)"
        echo "$volumes_tar"
    else
        log_warning "No volumes to backup"
    fi
}

backup_all() {
    log_info "=== FULL BACKUP STARTING ==="
    
    check_docker
    check_docker_compose
    check_backup_dir
    
    local start_time=$(date +%s)
    
    # Run backups
    backup_postgres
    backup_redis
    backup_config
    backup_volumes
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Create manifest
    create_manifest
    
    log_success "=== FULL BACKUP COMPLETE (${duration}s) ==="
    
    # Display summary
    du -sh "$BACKUP_DIR" 2>/dev/null | awk '{print "Total backup size: " $1}'
}

create_manifest() {
    log_info "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/metadata/manifest_$TODAY.json"
    
    cat > "$manifest_file" << EOF
{
  "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_id": "$NOW",
  "retention_days": $BACKUP_RETENTION_DAYS,
  "files": {
    "postgres": "$(ls -la $BACKUP_DIR/postgres/full/full_$TODAY* 2>/dev/null | wc -l) file(s)",
    "redis": "$(ls -la $BACKUP_DIR/redis/snapshots/redis_$TODAY* 2>/dev/null | wc -l) file(s)",
    "config": "$(ls -la $BACKUP_DIR/config/config_$TODAY* 2>/dev/null | wc -l) file(s)",
    "volumes": "$(ls -la $BACKUP_DIR/volumes/volumes_$TODAY* 2>/dev/null | wc -l) file(s)"
  },
  "checksums_file": "$BACKUP_DIR/metadata/checksums_$TODAY.sha256",
  "recovery_procedure": "See DISASTER_RECOVERY_PLAN.md",
  "contact": "infrastructure-team@example.com"
}
EOF
    
    log_success "Manifest created: $manifest_file"
}

##############################################################################
# RESTORE FUNCTIONS
##############################################################################

restore_database() {
    log_info "Starting PostgreSQL restore..."
    
    local restore_file=$1
    
    if [ -z "$restore_file" ]; then
        log_error "No restore file specified"
        return 1
    fi
    
    if [ ! -f "$restore_file" ]; then
        log_error "Restore file not found: $restore_file"
        return 1
    fi
    
    # Decrypt if needed
    local temp_file="/tmp/restore_$NOW.sql.gz"
    if [[ "$restore_file" == *.enc ]]; then
        decrypt_file "$restore_file" "$temp_file.enc"
        restore_file="$temp_file.enc"
    fi
    
    # Decompress
    if [[ "$restore_file" == *.gz ]]; then
        gunzip -c "$restore_file" > "$temp_file.sql"
        restore_file="$temp_file.sql"
    fi
    
    # Stop services to avoid write conflicts
    log_info "Stopping services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop
    
    # Drop existing database
    log_warning "Dropping existing database..."
    docker exec $POSTGRES_CONTAINER psql -U postgres -c "DROP DATABASE IF EXISTS roaddb;"
    docker exec $POSTGRES_CONTAINER psql -U postgres -c "CREATE DATABASE roaddb;"
    
    # Restore from backup
    log_info "Restoring database..."
    docker exec -i $POSTGRES_CONTAINER psql -U postgres -d roaddb < "$restore_file"
    
    # Cleanup
    rm -f "$temp_file" "$temp_file.sql" "$temp_file.enc" 2>/dev/null || true
    
    log_success "PostgreSQL restore complete"
}

restore_cache() {
    log_info "Starting Redis restore..."
    
    local restore_file=$1
    
    if [ -z "$restore_file" ]; then
        log_error "No restore file specified"
        return 1
    fi
    
    if [ ! -f "$restore_file" ]; then
        log_error "Restore file not found: $restore_file"
        return 1
    fi
    
    # Decrypt if needed
    local temp_file="/tmp/restore_redis_$NOW.rdb"
    if [[ "$restore_file" == *.enc ]]; then
        decrypt_file "$restore_file" "$temp_file.enc"
        restore_file="$temp_file.enc"
    fi
    
    # Decompress
    if [[ "$restore_file" == *.gz ]]; then
        gunzip -c "$restore_file" > "$temp_file"
        restore_file="$temp_file"
    fi
    
    # Stop Redis
    log_info "Stopping Redis..."
    docker exec $REDIS_CONTAINER redis-cli SHUTDOWN
    sleep 2
    
    # Restore dump.rdb
    docker cp "$restore_file" $REDIS_CONTAINER:/data/dump.rdb
    
    # Restart Redis
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d $REDIS_CONTAINER
    sleep 3
    
    # Cleanup
    rm -f "$temp_file" "$temp_file.enc" 2>/dev/null || true
    
    log_success "Redis restore complete"
}

##############################################################################
# RECOVERY COMMANDS
##############################################################################

recover_database() {
    local pitr_timestamp=$1
    
    log_info "Recovering PostgreSQL to: $pitr_timestamp"
    
    # For now, restore from latest full backup
    local latest_backup=$(ls -t "$BACKUP_DIR/postgres/full/"*.enc 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backups found"
        return 1
    fi
    
    log_info "Using backup: $latest_backup"
    restore_database "$latest_backup"
}

recover_cache() {
    log_info "Recovering Redis cache..."
    
    local latest_backup=$(ls -t "$BACKUP_DIR/redis/snapshots/"*.enc 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No Redis backups found"
        return 1
    fi
    
    log_info "Using backup: $latest_backup"
    restore_cache "$latest_backup"
}

full_recovery() {
    log_info "=== FULL SYSTEM RECOVERY STARTING ==="
    
    local start_time=$(date +%s)
    
    check_docker
    check_docker_compose
    
    # Recover database
    recover_database
    
    # Recover cache
    recover_cache
    
    # Restart all services
    log_info "Restarting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    sleep 10
    
    # Verify health
    verify_system_health
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "=== FULL RECOVERY COMPLETE (${duration}s) ==="
}

##############################################################################
# VERIFICATION & HEALTH
##############################################################################

verify_backup_integrity() {
    log_info "Verifying backup integrity..."
    
    if [ ! -f "$BACKUP_DIR/metadata/checksums_$TODAY.sha256" ]; then
        log_warning "No checksums file found for today"
        return 0
    fi
    
    cd "$BACKUP_DIR"
    if sha256sum -c "metadata/checksums_$TODAY.sha256"; then
        log_success "All backups verified ✓"
        return 0
    else
        log_error "Backup verification failed!"
        return 1
    fi
}

verify_system_health() {
    log_info "Verifying system health..."
    
    local errors=0
    
    # Check PostgreSQL
    if docker exec $POSTGRES_CONTAINER psql -U postgres -c "SELECT 1;" &>/dev/null; then
        log_success "PostgreSQL: OK"
    else
        log_error "PostgreSQL: FAILED"
        ((errors++))
    fi
    
    # Check Redis
    if docker exec $REDIS_CONTAINER redis-cli ping &>/dev/null; then
        log_success "Redis: OK"
    else
        log_error "Redis: FAILED"
        ((errors++))
    fi
    
    # Check services
    local services=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --services)
    for service in $services; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log_success "$service: UP"
        else
            log_warning "$service: NOT UP"
            ((errors++))
        fi
    done
    
    if [ $errors -eq 0 ]; then
        log_success "System health check passed ✓"
        return 0
    else
        log_warning "System health check found $errors issue(s)"
        return 1
    fi
}

list_restore_points() {
    log_info "Available restore points:"
    
    echo ""
    echo "PostgreSQL Backups:"
    ls -lh "$BACKUP_DIR/postgres/full/" 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
    
    echo ""
    echo "Redis Backups:"
    ls -lh "$BACKUP_DIR/redis/snapshots/" 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
    
    echo ""
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."
    
    find "$BACKUP_DIR/postgres/full" -name "*.enc" -mtime +$BACKUP_RETENTION_DAYS -delete
    find "$BACKUP_DIR/redis/snapshots" -name "*.enc" -mtime +$BACKUP_RETENTION_DAYS -delete
    find "$BACKUP_DIR/config" -name "*.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
    
    log_success "Cleanup complete"
}

##############################################################################
# TEST FUNCTIONS
##############################################################################

test_restore() {
    log_info "=== TESTING RESTORE (non-destructive) ==="
    
    log_info "This would restore from latest backup to isolated environment"
    log_info "Not implemented in this demo version"
    log_info "In production: Create clone environment and test restore"
    
    log_success "Test restore procedure ready"
}

##############################################################################
# STATUS & REPORTING
##############################################################################

show_backup_status() {
    log_info "=== BACKUP STATUS REPORT ==="
    
    echo ""
    echo "Backup Directory: $BACKUP_DIR"
    echo "Total Size: $(du -sh $BACKUP_DIR 2>/dev/null | cut -f1)"
    
    echo ""
    echo "PostgreSQL:"
    echo "  Latest backup: $(ls -t $BACKUP_DIR/postgres/full/*.enc 2>/dev/null | head -1 | xargs basename)"
    echo "  Backup count: $(ls $BACKUP_DIR/postgres/full/*.enc 2>/dev/null | wc -l)"
    
    echo ""
    echo "Redis:"
    echo "  Latest backup: $(ls -t $BACKUP_DIR/redis/snapshots/*.enc 2>/dev/null | head -1 | xargs basename)"
    echo "  Backup count: $(ls $BACKUP_DIR/redis/snapshots/*.enc 2>/dev/null | wc -l)"
    
    echo ""
    echo "Configuration:"
    echo "  Config backups: $(ls $BACKUP_DIR/config/*.gz 2>/dev/null | wc -l)"
    
    echo ""
}

##############################################################################
# MAIN COMMAND HANDLER
##############################################################################

usage() {
    cat << EOF
BlackRoad Disaster Recovery Management

USAGE:
  ./disaster-recovery.sh <command> [options]

BACKUP COMMANDS:
  backup-all              Create full backup (postgres, redis, config)
  backup-postgres         Backup PostgreSQL database only
  backup-redis            Backup Redis cache only
  backup-config           Backup configuration files only

RECOVERY COMMANDS:
  recover-database        Restore PostgreSQL from latest backup
  recover-cache           Restore Redis from latest backup
  full-recovery           Complete system recovery
  test-restore            Test restore procedure (non-destructive)

MANAGEMENT COMMANDS:
  status                  Show backup status
  verify                  Verify backup integrity
  list-restore-points     List available backups
  cleanup                 Remove backups older than $BACKUP_RETENTION_DAYS days
  health                  Verify system health

EXAMPLES:
  # Create full backup
  ./disaster-recovery.sh backup-all

  # Recover database from latest backup
  ./disaster-recovery.sh recover-database

  # Full system recovery
  ./disaster-recovery.sh full-recovery

  # Check backup status
  ./disaster-recovery.sh status

  # Verify all backups
  ./disaster-recovery.sh verify

EOF
}

##############################################################################
# MAIN ENTRY POINT
##############################################################################

main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    
    case "$1" in
        backup-all)
            backup_all
            ;;
        backup-postgres)
            backup_postgres
            ;;
        backup-redis)
            backup_redis
            ;;
        backup-config)
            backup_config
            ;;
        backup-volumes)
            backup_volumes
            ;;
        recover-database)
            recover_database "${2:-}"
            ;;
        recover-cache)
            recover_cache
            ;;
        full-recovery)
            full_recovery
            ;;
        test-restore)
            test_restore
            ;;
        status)
            show_backup_status
            verify_backup_integrity
            ;;
        verify)
            verify_backup_integrity
            ;;
        health)
            verify_system_health
            ;;
        list-restore-points)
            list_restore_points
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        *)
            log_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
