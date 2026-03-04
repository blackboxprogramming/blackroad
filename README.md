# BlackRoad

Backend API for BlackRoad.io — Stripe payments, Lucidia LLM, and portal services.

Runs on Raspberry Pi with nginx + systemd.

## Quick Start

```bash
cp .env.example .env
# Fill in your Stripe keys (from https://dashboard.stripe.com/apikeys)
npm install
npm start
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/health` | API health (includes Stripe status) |
| GET | `/api/stripe/config` | Publishable key for frontend |
| GET | `/api/stripe/prices` | List active products/prices |
| POST | `/api/stripe/create-checkout-session` | Start checkout flow |
| POST | `/api/stripe/create-payment-intent` | One-time payment |
| POST | `/api/stripe/customer-portal` | Manage subscriptions |
| POST | `/api/stripe/webhook` | Stripe webhook receiver |
| POST | `/api/llm/chat` | Lucidia LLM chat bridge |

## Testing

```bash
npm test                           # All tests (Stripe mocked)
STRIPE_SECRET_KEY=sk_test_... npm run test:e2e  # Live Stripe e2e
```

## Pi Deployment

The API runs on Raspberry Pi behind nginx:

- **systemd service**: `systemd/blackroad-api.service`
- **nginx config**: `nginx/blackroad.io.conf`
- **auto-update**: `scripts/auto-update.sh` (pulls main, restarts services)

### Setup on Pi

```bash
# Clone to /srv/blackroad
git clone https://github.com/blackboxprogramming/blackroad.git /srv/blackroad
cd /srv/blackroad && npm install --production

# Copy .env and fill in Stripe keys
cp .env.example .env && nano .env

# Install services
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo cp nginx/blackroad.io.conf /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable --now blackroad-api blackroad-update.timer
sudo systemctl reload nginx
```

### Stripe Webhook Setup

1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://blackroad.io/api/stripe/webhook`
3. Select events: `checkout.session.completed`, `payment_intent.succeeded`, `customer.subscription.*`, `invoice.payment_failed`
4. Copy the signing secret to `.env` as `STRIPE_WEBHOOK_SECRET`

## Environment Variables

See `.env.example` for all required variables.
