# BlackRoad CI/CD Pipeline Guide

## Overview

Complete GitHub Actions CI/CD pipeline for automated testing, building, and deployment of all BlackRoad services (APIs, dashboards, mobile app).

**Pipelines:**
- ✅ **CI** - Test, lint, security scan on every push/PR
- ✅ **Build** - Docker images on every tag
- ✅ **Deploy Staging** - Auto-deploy on develop branch
- ✅ **Deploy Production** - Manual or release-triggered
- ✅ **Performance Tests** - Daily load testing

## Quick Setup

### 1. Add Secrets to GitHub

Go to repository **Settings → Secrets and variables → Actions** and add:

```
AWS_ACCOUNT_ID          # Your AWS account ID
GITHUB_TOKEN            # Auto-provided by GitHub
SONARCLOUD_TOKEN        # Optional: SonarCloud token
```

### 2. Create GitHub Environments

Go to **Settings → Environments** and create:

1. **staging**
   - Environment protection rules: None (auto-deploy)
   - Reviewers: None

2. **production**
   - Environment protection rules: Require approval
   - Reviewers: Add team members who should approve

### 3. Configure AWS IAM Role

Create IAM role for GitHub Actions:

```bash
aws iam create-role \
  --role-name github-actions-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:OWNER/REPO:ref:refs/heads/main"
        }
      }
    }]
  }'
```

Attach policies:
```bash
aws iam attach-role-policy \
  --role-name github-actions-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-role-policy \
  --role-name github-actions-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

## Workflows

### 1. CI Workflow (ci.yml)

**Triggers:** Push to main/develop, Pull requests

**Jobs:**

#### Python Lint & Type Check
- Format check with `black`
- Lint with `flake8`
- Type check with `mypy`

```bash
# Run locally
black --check *.py
flake8 *.py
mypy *.py --ignore-missing-imports
```

#### Python Tests
- Unit tests with pytest
- Coverage reporting to Codecov
- Database: PostgreSQL 14

```bash
# Run locally
pytest --cov=. --cov-report=xml
```

#### Dashboard Lint & Build
- ESLint checks
- Vite build

```bash
cd dashboard
npm ci
npm run lint
npm run build
```

#### Mobile App Lint
- ESLint checks
- React Native validation

```bash
cd mobile
npm ci
npm run lint
```

#### Security Scan
- Trivy vulnerability scanning
- Results uploaded to GitHub Security tab

#### Code Quality
- SonarCloud analysis (optional)

**Artifacts:**
- Dashboard build (`dist/` directory)

**Status Check:**
- All jobs must pass before merging PR

### 2. Build Workflow (build.yml)

**Triggers:** Tag push (e.g., `git tag v1.0.0 && git push --tags`)

**Jobs:**

#### Build API Services
Builds Docker images for:
- Billing API (main.py)
- Admin Dashboard (admin_dashboard.py)
- ML Analytics (ml_analytics_engine.py)

```bash
# Build locally
docker build -f Dockerfile -t blackroad-billing:v1.0.0 .
docker push ghcr.io/YOUR_REPO/blackroad-billing:v1.0.0
```

#### Build Dashboard
```bash
docker build -f dashboard/Dockerfile -t blackroad-dashboard:v1.0.0 .
docker push ghcr.io/YOUR_REPO/blackroad-dashboard:v1.0.0
```

**Registry:** GitHub Container Registry (ghcr.io)

**Tags:**
- Semantic version: `v1.0.0`
- SHA: `abc1234`
- Latest: `latest`

### 3. Deploy Staging (deploy-staging.yml)

**Triggers:** Push to develop branch, manual workflow dispatch

**Environment:** staging

**Process:**

1. **Checkout code**
2. **Configure AWS credentials** (OIDC)
3. **Build Docker images**
4. **Run pre-deployment checks**
   - Validate deployment configuration
   - Database migrations
   - Dependency checks

5. **Deploy to ECS**
   ```bash
   aws ecs update-service \
     --cluster blackroad-staging \
     --service blackroad-api \
     --force-new-deployment
   ```

6. **Verify deployment**
   - Health check: `curl http://staging-api.blackroad.com/health`
   - Wait 30 seconds
   - Retry up to 10 times

7. **Notify result**

**Duration:** ~5-10 minutes

**Rollback:** Manual via AWS console (or revert develop branch commit)

### 4. Deploy Production (deploy-production.yml)

**Triggers:**
- GitHub release published
- Manual workflow dispatch with version input

**Environment:** production

**Protection:** Requires manual approval

**Process:**

1. **Checkout with full history**
2. **Configure AWS credentials** (OIDC)
3. **Validate production config**
4. **Build production images** (optimized)
5. **Deploy with blue/green strategy**
   ```bash
   python deploy.py \
     --env production \
     --strategy blue-green \
     --version v1.0.0
   ```

6. **Run smoke tests**
   ```bash
   bash test_dashboard_integration.sh
   ```

7. **Monitor health**
   - Poll health endpoint 10 times
   - Automatic rollback on failure

8. **Record deployment**
   - Upload logs to S3
   - Create deployment record

**Rollback (automatic):**
```bash
python deploy.py --rollback --env production
```

**Duration:** ~15-20 minutes

### 5. Performance Tests (performance-tests.yml)

**Triggers:** Daily at 2 AM UTC, manual dispatch

**Services:** PostgreSQL, Redis

**Tests:**

1. **Load Tests** (Locust)
   - 1000 concurrent users
   - Ramp up 50 users/second
   - Run for 5 minutes
   - Metrics: Response time, throughput, errors

2. **Performance Benchmarks** (pytest-benchmark)
   - Database queries
   - API endpoints
   - Caching performance

3. **Database Optimization**
   - Create indexes
   - Analyze statistics
   - Generate reports

**Artifacts:** `results*.csv` (performance metrics)

**Reporting:** Compare against baseline, alert on regressions

## Workflow Status & Monitoring

### GitHub Actions Dashboard
Navigate to **Actions** tab to see:
- Workflow runs
- Job status
- Logs
- Artifacts
- Deployment history

### Status Badges

Add to README.md:

```markdown
[![CI](https://github.com/YOUR_REPO/workflows/CI/badge.svg)](https://github.com/YOUR_REPO/actions?query=workflow:CI)
[![Build](https://github.com/YOUR_REPO/workflows/Build/badge.svg)](https://github.com/YOUR_REPO/actions?query=workflow:Build)
[![Deploy Staging](https://github.com/YOUR_REPO/workflows/Deploy%20Staging/badge.svg)](https://github.com/YOUR_REPO/actions?query=workflow:Deploy%20Staging)
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/my-feature develop

# Make changes, test locally
npm run lint
npm run test

# Push branch
git push origin feature/my-feature

# Create pull request to develop
```

**Automated checks run:**
- Linting
- Tests
- Security scan
- Code quality
- Build (dashboard)

### 2. Merge to Develop

PR merges to `develop` after approval + checks pass

**Auto-triggered:**
- Deploy Staging workflow
- Staging environment updated within 5-10 minutes

### 3. Release to Production

```bash
# Create release tag
git tag v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

**Auto-triggered:**
- Build workflow (creates Docker images)
- Manual approval required
- Deploy Production workflow

**Or manual dispatch:**
- Go to Actions → Deploy Production
- Click "Run workflow"
- Enter version (e.g., v1.0.0)

## Dependency Management

### Dependabot

GitHub automatically updates dependencies:

- **Python (pip)**: Weekly checks
- **Node.js (npm)**: Weekly checks
- **GitHub Actions**: Weekly checks

**Auto-merged PRs:**
- Minor/patch versions only
- All checks pass
- Assigned to owner for review

### Manual Updates

```bash
# Python
pip install --upgrade pip
pip list --outdated
pip install -U package-name

# Node.js (Dashboard)
cd dashboard
npm outdated
npm update

# Node.js (Mobile)
cd mobile
npm outdated
npm update
```

## Security & Quality

### Trivy Scan
Vulnerability scanning on every CI run

Results appear in **Security → Code scanning**

### SonarCloud (Optional)
Code quality metrics:
- Code coverage
- Code smell detection
- Security hotspots
- Duplicate code

Setup:
1. Create SonarCloud account
2. Add `SONARCLOUD_TOKEN` secret
3. Uncomment SonarCloud job

### Branch Protection Rules

Go to **Settings → Branches** and set up:

**For main branch:**
- Require branches to be up to date before merging
- Require status checks to pass:
  - python-lint
  - python-test
  - dashboard-lint
  - mobile-lint
  - security-scan
- Require code reviews: 1 approval
- Dismiss stale PRs: Yes
- Require status checks from up-to-date branches

## Troubleshooting

### CI Failures

**Python tests fail:**
```bash
# Run locally
pytest -v

# Check database connection
psql -h localhost -U postgres -d blackroad_test

# Run with verbose logging
pytest -vv --tb=long
```

**Linting fails:**
```bash
# Auto-fix with black
black *.py

# Fix eslint issues
npm run lint -- --fix
```

### Build Failures

**Docker build fails:**
```bash
# Build locally to debug
docker build -f Dockerfile -t test .

# Check dependencies
pip install -r requirements.txt
```

**Dashboard build fails:**
```bash
cd dashboard
rm -rf node_modules dist
npm ci
npm run build
```

### Deployment Issues

**Deployment timeout:**
- Check AWS ECS cluster status
- Verify security group allows traffic
- Check CloudWatch logs

**Health check fails:**
```bash
# Test endpoint locally
curl -v http://staging-api.blackroad.com/health

# Check logs
aws logs tail /ecs/blackroad-staging --follow
```

### Rollback

**Manual rollback:**
```bash
# Rollback to previous deployment
git revert <commit-hash>
git push origin main

# Or manually via AWS
aws ecs update-service \
  --cluster blackroad-production \
  --service blackroad-api \
  --task-definition blackroad-api:5  # Previous version
```

## Monitoring

### CloudWatch Alarms

Create alarms for:
- Failed deployments
- Unhealthy tasks
- High error rates
- Performance degradation

### Notifications

Configure in GitHub:
- Slack integration
- Email notifications
- Custom webhooks

## Best Practices

1. **Small, focused PRs** - Easier to review & test
2. **Descriptive commit messages** - "fix: handle null user" vs "fix stuff"
3. **Test locally before pushing** - `npm test`, `pytest`, etc.
4. **Wait for checks to pass** - Don't force merge
5. **Review code changes** - At least one approval
6. **Use semantic versioning** - v1.2.3 for releases
7. **Monitor deployments** - Check logs after deploy
8. **Keep secrets safe** - Use GitHub Secrets, never commit

## CI/CD Checklist

Before production:
- [ ] All tests passing
- [ ] Code coverage >80%
- [ ] Security scan clear
- [ ] Performance within baseline
- [ ] Deployment plan documented
- [ ] Rollback procedure ready
- [ ] Team notified

## Next Steps

1. **Enable branch protection** - Prevent accidental pushes
2. **Configure notifications** - Slack/email alerts
3. **Set up monitoring** - CloudWatch alarms
4. **Document runbooks** - Incident response
5. **Schedule on-call** - Team rotation

---

**CI/CD Status:** ✅ **COMPLETE & READY**

**Workflows:** 5  
**Jobs:** 15+  
**Coverage:** All services (APIs, Dashboard, Mobile)  
**Deploy:** Staging (auto), Production (gated)

