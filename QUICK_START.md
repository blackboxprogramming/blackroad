# 🚀 QUICK START - BlackRoad SaaS Platform

## One-Liner Deployment

```bash
cd /Users/alexa/blackroad && ./deploy-local.sh
```

That's it! Your entire SaaS platform will deploy in ~30 minutes.

---

## After Deployment

### View Dashboards (Real-Time)

```bash
# Grafana (metrics & dashboards)
open http://localhost:3000
# Username: admin
# Password: grafana_admin_pass

# Prometheus (raw metrics)
open http://localhost:9090

# Your app
open http://localhost
```

### Manage Platform

```bash
# Check status
./blackroad-cli.sh status

# View logs
./blackroad-cli.sh logs

# Health check
./blackroad-cli.sh health

# Stop services
./blackroad-cli.sh stop

# Start services
./blackroad-cli.sh start

# Scale a service
./blackroad-cli.sh scale billing-api 3

# Connect to database
./blackroad-cli.sh db

# Connect to cache
./blackroad-cli.sh cache

# Full help
./blackroad-cli.sh help
```

---

## Services Running

| Service | URL | Purpose |
|---------|-----|---------|
| **Billing API** | http://localhost:8001 | Payment processing |
| **Admin Dashboard** | http://localhost:8002 | Revenue tracking |
| **Analytics Engine** | http://localhost:8003 | Customer analytics |
| **ML Analytics** | http://localhost:8004 | Predictions |
| **Customer UI** | http://localhost:8005 | User dashboard |
| **Stripe Webhooks** | http://localhost:8006 | Payment events |
| **Onboarding** | http://localhost:8007 | User signup |
| **Monitoring** | http://localhost:8008 | Health checks |
| **Grafana** | http://localhost:3000 | Dashboards |
| **Prometheus** | http://localhost:9090 | Metrics |

---

## What's Included

✅ 10 microservices (all working)
✅ 3 frontends (web, mobile, admin)
✅ 5 ML models (trained & ready)
✅ PostgreSQL database
✅ Redis cache
✅ Real-time monitoring
✅ Automated alerts
✅ Load balancer
✅ Comprehensive documentation

---

## Stop When Done

```bash
./blackroad-cli.sh stop
```

---

## More Information

- **Architecture:** See `COMPLETE_SAAS_PLATFORM_README.md`
- **Deployment Details:** See `LOCAL_DEPLOYMENT_GUIDE.md`
- **Platform Status:** See `FINAL_PLATFORM_STATUS.md`

---

**Ready? Deploy now:**

```bash
./deploy-local.sh
```

🎉 Your SaaS is launching!
