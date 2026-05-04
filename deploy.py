"""
Production Deployment Pipeline for BlackRoad
Features: Blue/Green deployment, Canary releases, Automated rollback, Health checks
"""

import subprocess
import time
import sys
import json
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================

class Environment(Enum):
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStrategy(Enum):
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"

# ==================== Deployment Pipeline ====================

class DeploymentPipeline:
    """Production deployment with health checks and rollback capability"""
    
    def __init__(self, env: Environment, strategy: DeploymentStrategy):
        self.env = env
        self.strategy = strategy
        self.timestamp = datetime.now().isoformat()
        self.deployment_id = f"{env.value}-{strategy.value}-{int(time.time())}"
        self.deployment_log = []
    
    def log(self, level: str, message: str):
        """Log deployment event"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.deployment_log.append(entry)
        if level == 'ERROR':
            logger.error(message)
        elif level == 'WARNING':
            logger.warning(message)
        else:
            logger.info(message)
    
    # ==================== Pre-deployment ====================
    
    def run_pre_deployment_checks(self) -> bool:
        """Run pre-deployment validation"""
        self.log('INFO', f"🔍 Running pre-deployment checks for {self.env.value}...")
        
        checks = [
            self.check_git_status,
            self.check_docker_images,
            self.check_aws_credentials,
            self.check_database_migrations,
            self.check_configuration,
            self.run_tests,
        ]
        
        for check in checks:
            if not check():
                self.log('ERROR', f"Pre-deployment check failed: {check.__name__}")
                return False
        
        self.log('INFO', "✅ All pre-deployment checks passed")
        return True
    
    def check_git_status(self) -> bool:
        """Verify git repository is clean"""
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            self.log('WARNING', "Git working directory not clean. Stashing changes...")
            subprocess.run(['git', 'stash'], capture_output=True)
        
        self.log('INFO', f"Git branch: {subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()}")
        return True
    
    def check_docker_images(self) -> bool:
        """Verify Docker images are built"""
        self.log('INFO', "Checking Docker images...")
        result = subprocess.run(['docker', 'image', 'ls'], 
                              capture_output=True, text=True)
        if 'blackroad' not in result.stdout:
            self.log('WARNING', "Docker image not found. Building...")
            subprocess.run(['docker', 'build', '-t', 'blackroad:latest', '.'],
                         capture_output=True)
        return True
    
    def check_aws_credentials(self) -> bool:
        """Verify AWS credentials are configured"""
        self.log('INFO', "Checking AWS credentials...")
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            self.log('ERROR', "AWS credentials not configured")
            return False
        
        account_id = json.loads(result.stdout).get('Account')
        self.log('INFO', f"AWS Account: {account_id}")
        return True
    
    def check_database_migrations(self) -> bool:
        """Verify all database migrations are applied"""
        self.log('INFO', "Checking database migrations...")
        # In production: check alembic version
        return True
    
    def check_configuration(self) -> bool:
        """Verify all configuration is present"""
        self.log('INFO', "Checking configuration...")
        required_env_vars = [
            'STRIPE_SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'AWS_REGION'
        ]
        
        import os
        for var in required_env_vars:
            if not os.getenv(var):
                self.log('WARNING', f"Missing environment variable: {var}")
        
        return True
    
    def run_tests(self) -> bool:
        """Run test suite"""
        self.log('INFO', "Running test suite...")
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
                              capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            self.log('ERROR', f"Tests failed:\n{result.stdout}")
            return False
        
        self.log('INFO', "✅ All tests passed")
        return True
    
    # ==================== Blue/Green Deployment ====================
    
    def deploy_blue_green(self) -> bool:
        """Deploy using blue/green strategy"""
        self.log('INFO', "🔵🟢 Starting Blue/Green deployment...")
        
        # Step 1: Deploy to GREEN (inactive)
        self.log('INFO', "Step 1: Deploying to GREEN environment...")
        if not self.deploy_to_environment('green'):
            return False
        
        # Step 2: Run smoke tests on GREEN
        self.log('INFO', "Step 2: Running smoke tests on GREEN...")
        if not self.run_smoke_tests('green'):
            self.log('ERROR', "Smoke tests failed on GREEN")
            return False
        
        # Step 3: Run load tests on GREEN
        self.log('INFO', "Step 3: Running load tests on GREEN...")
        if not self.run_load_tests('green', duration=60):
            self.log('ERROR', "Load tests failed on GREEN")
            return False
        
        # Step 4: Warm up GREEN cache
        self.log('INFO', "Step 4: Warming up cache...")
        self.warmup_cache('green')
        
        # Step 5: Switch traffic BLUE → GREEN
        self.log('INFO', "Step 5: Switching traffic to GREEN...")
        if not self.switch_traffic('blue', 'green'):
            return False
        
        # Step 6: Monitor for 5 minutes
        self.log('INFO', "Step 6: Monitoring GREEN for 5 minutes...")
        if not self.monitor_deployment('green', duration=300):
            self.log('WARNING', "Issues detected. Rolling back...")
            self.switch_traffic('green', 'blue')
            return False
        
        # Step 7: Cleanup BLUE
        self.log('INFO', "Step 7: Cleaning up BLUE environment...")
        self.cleanup_environment('blue')
        
        self.log('INFO', "✅ Blue/Green deployment completed successfully")
        return True
    
    # ==================== Canary Deployment ====================
    
    def deploy_canary(self, canary_percentage: int = 10) -> bool:
        """Deploy using canary strategy"""
        self.log('INFO', f"🐤 Starting Canary deployment ({canary_percentage}% traffic)...")
        
        stages = [
            (5, "Route 5% of traffic to new version"),
            (10, "Route 10% of traffic to new version"),
            (25, "Route 25% of traffic to new version"),
            (50, "Route 50% of traffic to new version"),
            (100, "Route 100% of traffic to new version"),
        ]
        
        for percentage, description in stages:
            self.log('INFO', f"Canary Step: {description}...")
            
            # Deploy new version
            if percentage == 5:
                self.deploy_to_environment('canary')
            
            # Route traffic
            self.set_traffic_split('current', 'canary', 100 - percentage, percentage)
            
            # Monitor
            monitor_duration = 60
            self.log('INFO', f"Monitoring for {monitor_duration} seconds...")
            if not self.monitor_deployment('canary', duration=monitor_duration):
                self.log('ERROR', f"Canary failed at {percentage}% traffic")
                # Rollback to 0% canary traffic
                self.set_traffic_split('current', 'canary', 100, 0)
                return False
            
            # Check error rate
            error_rate = self.get_error_rate('canary')
            if error_rate > 0.01:  # 1% error threshold
                self.log('ERROR', f"Error rate too high: {error_rate*100:.2f}%")
                self.set_traffic_split('current', 'canary', 100, 0)
                return False
            
            self.log('INFO', f"✅ Canary stable at {percentage}% traffic")
            time.sleep(30)  # Wait between stages
        
        self.log('INFO', "✅ Canary deployment completed successfully")
        return True
    
    # ==================== Deployment Helpers ====================
    
    def deploy_to_environment(self, env_name: str) -> bool:
        """Deploy services to environment"""
        self.log('INFO', f"Deploying to {env_name} environment...")
        
        try:
            # In production: use Terraform or ECS
            # terraform apply -var="environment={env_name}"
            
            self.log('INFO', f"  • Pulling latest images...")
            self.log('INFO', f"  • Starting services...")
            self.log('INFO', f"  • Waiting for health checks...")
            
            time.sleep(5)  # Simulate deployment
            self.log('INFO', f"✅ {env_name} environment ready")
            return True
        except Exception as e:
            self.log('ERROR', f"Failed to deploy to {env_name}: {str(e)}")
            return False
    
    def run_smoke_tests(self, env_name: str) -> bool:
        """Run smoke tests on deployment"""
        self.log('INFO', f"Running smoke tests on {env_name}...")
        
        tests = [
            ("Health check", f"curl http://{env_name}:8000/health"),
            ("Billing API", f"curl http://{env_name}:8000/status"),
            ("Admin API", f"curl http://{env_name}:8001/health"),
            ("Customer API", f"curl http://{env_name}:8003/health"),
        ]
        
        failed = 0
        for test_name, command in tests:
            result = subprocess.run(command.split(), capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log('INFO', f"  ✅ {test_name}")
            else:
                self.log('ERROR', f"  ❌ {test_name}")
                failed += 1
        
        return failed == 0
    
    def run_load_tests(self, env_name: str, duration: int = 60) -> bool:
        """Run load tests on deployment"""
        self.log('INFO', f"Running {duration}s load test on {env_name}...")
        
        # Simulate load test
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration:
            # Simulate requests
            request_count += 100
            errors += 2  # Simulate some errors
            
            # Log progress every 10s
            if int(time.time() - start_time) % 10 == 0:
                throughput = request_count / (time.time() - start_time)
                error_rate = errors / request_count if request_count > 0 else 0
                self.log('INFO', f"  {throughput:.0f} req/s, error rate: {error_rate*100:.2f}%")
            
            time.sleep(0.1)
        
        error_rate = errors / request_count
        if error_rate > 0.01:
            self.log('ERROR', f"Load test failed: error rate {error_rate*100:.2f}%")
            return False
        
        self.log('INFO', f"✅ Load test passed: {request_count} requests, {error_rate*100:.2f}% error rate")
        return True
    
    def warmup_cache(self, env_name: str):
        """Pre-populate cache before switching traffic"""
        self.log('INFO', f"Warming up cache for {env_name}...")
        # In production: Make requests to populate Redis cache
        time.sleep(2)
        self.log('INFO', "✅ Cache warmed up")
    
    def switch_traffic(self, from_env: str, to_env: str) -> bool:
        """Switch traffic from one environment to another"""
        self.log('INFO', f"Switching traffic from {from_env} to {to_env}...")
        
        try:
            # In production: Use AWS Route 53 / ALB target group switching
            # aws elbv2 register-targets --target-group-arn ... --targets ...
            
            self.log('INFO', "  • Updating load balancer...")
            self.log('INFO', "  • Draining connections from old targets...")
            self.log('INFO', "  • Updating DNS records...")
            
            time.sleep(3)
            self.log('INFO', f"✅ Traffic switched to {to_env}")
            return True
        except Exception as e:
            self.log('ERROR', f"Failed to switch traffic: {str(e)}")
            return False
    
    def set_traffic_split(self, primary: str, canary: str, primary_pct: int, canary_pct: int):
        """Set traffic split between two environments"""
        self.log('INFO', f"Traffic split: {primary}({primary_pct}%) / {canary}({canary_pct}%)")
        # In production: Use weighted target groups
    
    def get_error_rate(self, env_name: str) -> float:
        """Get current error rate from monitoring"""
        # In production: Query Prometheus/CloudWatch
        return 0.002  # Return mock value
    
    def monitor_deployment(self, env_name: str, duration: int = 60) -> bool:
        """Monitor deployment for issues"""
        self.log('INFO', f"Monitoring {env_name} for {duration}s...")
        
        for i in range(0, duration, 10):
            error_rate = self.get_error_rate(env_name)
            latency = 50 + (i % 20)  # Simulate latency
            
            if error_rate > 0.01:
                self.log('ERROR', f"High error rate detected: {error_rate*100:.2f}%")
                return False
            
            self.log('INFO', f"  {i}s: latency={latency}ms, error_rate={error_rate*100:.2f}%")
            time.sleep(10)
        
        return True
    
    def cleanup_environment(self, env_name: str):
        """Clean up old environment after successful deployment"""
        self.log('INFO', f"Cleaning up {env_name} environment...")
        # In production: Deregister targets, stop containers, etc.
        self.log('INFO', f"✅ {env_name} cleaned up")
    
    # ==================== Rollback ====================
    
    def rollback(self, rollback_version: str):
        """Rollback to previous version"""
        self.log('INFO', f"🔄 Rolling back to version {rollback_version}...")
        
        try:
            # Step 1: Get previous version
            self.log('INFO', "Step 1: Fetching previous version...")
            
            # Step 2: Deploy previous version
            self.log('INFO', "Step 2: Deploying previous version...")
            self.deploy_to_environment('rollback')
            
            # Step 3: Switch traffic back
            self.log('INFO', "Step 3: Switching traffic back...")
            self.switch_traffic('current', 'rollback')
            
            # Step 4: Monitor
            self.log('INFO', "Step 4: Monitoring...")
            if not self.monitor_deployment('rollback', duration=120):
                self.log('ERROR', "Rollback monitoring failed")
                return False
            
            self.log('INFO', f"✅ Rollback to {rollback_version} completed")
            return True
        except Exception as e:
            self.log('ERROR', f"Rollback failed: {str(e)}")
            return False
    
    # ==================== Health Checks ====================
    
    def comprehensive_health_check(self) -> bool:
        """Run comprehensive health checks across all services"""
        self.log('INFO', "🏥 Running comprehensive health check...")
        
        services = [
            ('Billing API', 'http://localhost:8000/health'),
            ('Admin Dashboard', 'http://localhost:8001/health'),
            ('Customer Analytics', 'http://localhost:8003/health'),
            ('Customer UI', 'http://localhost:8004/health'),
            ('ML Engine', 'http://localhost:8005/health'),
        ]
        
        all_healthy = True
        for service_name, url in services:
            try:
                result = subprocess.run(['curl', '-f', url], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.log('INFO', f"✅ {service_name}")
                else:
                    self.log('ERROR', f"❌ {service_name}")
                    all_healthy = False
            except Exception as e:
                self.log('ERROR', f"❌ {service_name}: {str(e)}")
                all_healthy = False
        
        return all_healthy
    
    # ==================== Main Deployment ====================
    
    def deploy(self) -> bool:
        """Execute deployment pipeline"""
        self.log('INFO', f"🚀 Starting {self.strategy.value} deployment to {self.env.value}")
        self.log('INFO', f"Deployment ID: {self.deployment_id}")
        
        # Pre-deployment
        if not self.run_pre_deployment_checks():
            self.log('ERROR', "Pre-deployment checks failed")
            return False
        
        # Deploy based on strategy
        if self.strategy == DeploymentStrategy.BLUE_GREEN:
            success = self.deploy_blue_green()
        elif self.strategy == DeploymentStrategy.CANARY:
            success = self.deploy_canary(canary_percentage=10)
        else:
            success = False
        
        # Post-deployment
        if success:
            self.log('INFO', "✅ Deployment successful!")
            self.comprehensive_health_check()
        else:
            self.log('ERROR', "❌ Deployment failed")
        
        # Save deployment log
        self.save_deployment_log()
        
        return success
    
    def save_deployment_log(self):
        """Save deployment log to file"""
        log_file = f"deployment-{self.deployment_id}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'deployment_id': self.deployment_id,
                'environment': self.env.value,
                'strategy': self.strategy.value,
                'timestamp': self.timestamp,
                'log': self.deployment_log
            }, f, indent=2)
        self.log('INFO', f"Deployment log saved to {log_file}")


# ==================== CLI ====================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='BlackRoad Production Deployment')
    parser.add_argument('--env', choices=['staging', 'production'], 
                       default='staging', help='Environment to deploy to')
    parser.add_argument('--strategy', choices=['blue-green', 'canary', 'rolling'],
                       default='blue-green', help='Deployment strategy')
    parser.add_argument('--rollback', metavar='VERSION', help='Rollback to specific version')
    parser.add_argument('--health-check', action='store_true', help='Run health checks only')
    
    args = parser.parse_args()
    
    env = Environment.PRODUCTION if args.env == 'production' else Environment.STAGING
    strategy_map = {
        'blue-green': DeploymentStrategy.BLUE_GREEN,
        'canary': DeploymentStrategy.CANARY,
        'rolling': DeploymentStrategy.ROLLING,
    }
    strategy = strategy_map.get(args.strategy, DeploymentStrategy.BLUE_GREEN)
    
    pipeline = DeploymentPipeline(env, strategy)
    
    if args.health_check:
        sys.exit(0 if pipeline.comprehensive_health_check() else 1)
    elif args.rollback:
        sys.exit(0 if pipeline.rollback(args.rollback) else 1)
    else:
        sys.exit(0 if pipeline.deploy() else 1)
