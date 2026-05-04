# 🔐 GitHub Secrets Setup - BlackRoad SaaS Platform

**Status:** ✅ Repository live at https://github.com/blackboxprogramming/blackroad  
**Workflows:** ✅ All 5+ workflows configured and running  
**Next Step:** Configure secrets for CI/CD automation

---

## 🔑 Required Secrets for CI/CD

The deployment workflows require these secrets to be configured in GitHub:

### 1. AWS Deployment Secrets
```
AWS_ACCOUNT_ID          (Your AWS account ID)
AWS_ACCESS_KEY_ID       (IAM user access key)
AWS_SECRET_ACCESS_KEY   (IAM user secret key)
AWS_REGION              (e.g., us-east-1)
AWS_ECR_REGISTRY        (Your ECR registry URL)
```

### 2. Stripe Secrets
```
STRIPE_API_KEY          (Stripe live API key)
STRIPE_WEBHOOK_SECRET   (Webhook signing secret)
STRIPE_PUBLISHABLE_KEY  (Publishable key)
```

### 3. Email Secrets
```
SENDGRID_API_KEY        (SendGrid API key)
SENDER_EMAIL            (Sender email address)
```

### 4. Database Secrets
```
DATABASE_URL            (PostgreSQL connection string)
REDIS_URL               (Redis connection URL)
```

### 5. Application Secrets
```
FLASK_SECRET_KEY        (Generate: openssl rand -hex 32)
JWT_SECRET_KEY          (Generate: openssl rand -hex 32)
API_RATE_LIMIT          (e.g., 1000 per hour)
```

### 6. Optional Secrets
```
SLACK_WEBHOOK_URL       (For notifications)
SENTRY_DSN              (Error tracking)
DATADOG_API_KEY         (Monitoring)
```

---

## 📝 How to Add Secrets to GitHub

### Via GitHub CLI (Recommended)
```bash
# Log in to GitHub
gh auth login

# Add a secret
gh secret set AWS_ACCESS_KEY_ID -R blackboxprogramming/blackroad

# You'll be prompted to enter the value

# View all secrets
gh secret list -R blackboxprogramming/blackroad
```

### Via GitHub Web UI
1. Go to https://github.com/blackboxprogramming/blackroad/settings/secrets/actions
2. Click "New repository secret"
3. Enter the secret name and value
4. Click "Add secret"

---

## 🚀 Quick Setup Commands

```bash
# Set up AWS secrets
gh secret set AWS_ACCOUNT_ID -R blackboxprogramming/blackroad
gh secret set AWS_ACCESS_KEY_ID -R blackboxprogramming/blackroad
gh secret set AWS_SECRET_ACCESS_KEY -R blackboxprogramming/blackroad
gh secret set AWS_REGION -R blackboxprogramming/blackroad

# Set up Stripe secrets
gh secret set STRIPE_API_KEY -R blackboxprogramming/blackroad
gh secret set STRIPE_WEBHOOK_SECRET -R blackboxprogramming/blackroad

# Set up application secrets
gh secret set FLASK_SECRET_KEY -R blackboxprogramming/blackroad
gh secret set JWT_SECRET_KEY -R blackboxprogramming/blackroad

# Verify
gh secret list -R blackboxprogramming/blackroad
```

---

## ⚠️ Security Best Practices

1. **Never commit secrets** to the repository
2. **Use environment variables** for all credentials
3. **Rotate secrets regularly** (every 90 days)
4. **Use IAM roles** instead of access keys when possible
5. **Set secret expiration** on API keys
6. **Use least privilege** for IAM permissions
7. **Monitor secret access** logs
8. **Enable MFA** on your GitHub account

---

## 🔍 Workflow Secrets Usage

### CI Workflow (.github/workflows/ci.yml)
- Uses: Python linting, testing, code coverage

### Build Workflow (.github/workflows/build.yml)
- Uses: AWS_ACCOUNT_ID, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- Creates Docker images and pushes to ECR

### Deploy Staging (.github/workflows/deploy-staging.yml)
- Uses: All AWS secrets
- Deploys to staging environment
- Runs integration tests

### Deploy Production (.github/workflows/deploy-production.yml)
- Uses: All AWS secrets, Stripe secrets
- Requires manual approval
- Blue/Green deployment strategy

### Performance Tests (.github/workflows/performance-tests.yml)
- Uses: DATABASE_URL, REDIS_URL
- Runs load tests on 1B user scale

---

## 📊 Workflow Status

Check workflow status at: https://github.com/blackboxprogramming/blackroad/actions

### Currently Running:
- ✅ CI - Test & Lint
- ✅ CI/CD Pipeline
- ✅ Dependabot Updates

### Configure Before Production:
- ⚠️ Deploy - Staging (needs AWS secrets)
- ⚠️ Deploy - Production (needs all secrets + approval)
- ⚠️ Performance Tests (needs database secrets)

---

## 🎯 Deployment Pipeline

### Step 1: Add Secrets (This step)
- [ ] AWS secrets configured
- [ ] Stripe secrets configured
- [ ] Database secrets configured
- [ ] Application secrets configured

### Step 2: Run Staging Deployment
- Push to develop branch → Staging deploys automatically
- Run integration tests
- Verify in staging environment

### Step 3: Run Production Deployment
- Create pull request main branch
- Get code review
- Merge to main → Manual approval required
- Production deployment starts

### Step 4: Monitor & Alert
- Watch CloudWatch dashboards
- Monitor Prometheus metrics
- Check Slack notifications

---

## 🚨 Troubleshooting

### "Secret not found" error
- Ensure secret name matches exactly in workflow file
- Check GitHub CLI is authenticated: `gh auth status`

### Workflow fails on deployment
- Verify AWS credentials have correct permissions
- Check AWS ECR registry exists
- Ensure RDS database is accessible

### Build fails with "Access Denied"
- Verify AWS IAM policy includes:
  - `ecr:GetDownloadUrlForLayer`
  - `ecr:BatchGetImage`
  - `ec2:*`
  - `ecs:*`
  - `iam:PassRole`

### Stripe webhook fails
- Verify webhook secret matches GitHub secret
- Check Stripe event types are enabled
- Ensure webhook endpoint is publicly accessible

---

## 📞 Support

For help setting up secrets:
1. Check GitHub docs: https://docs.github.com/en/actions/security-guides/encrypted-secrets
2. Check AWS IAM docs: https://docs.aws.amazon.com/IAM/
3. Check Stripe docs: https://stripe.com/docs/webhooks

---

## ✅ Verification Checklist

After adding all secrets:
- [ ] `gh secret list` shows all required secrets
- [ ] CI workflow passes (no secret errors)
- [ ] Build workflow passes
- [ ] Can view secrets in GitHub UI (Settings → Secrets)
- [ ] No secrets in workflow logs
- [ ] Ready to deploy to staging

---

**Next Step:** Add all secrets, then trigger staging deployment! 🚀

