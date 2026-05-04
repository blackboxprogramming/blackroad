BlackRoad Billing — README

Overview

This folder contains a source-of-truth pricing catalog (blackroad_pricing_catalog.json) and an idempotent script (scripts/stripe_create_catalog.py) to create Products and Prices in Stripe.

Important notes
- Do NOT hardcode Stripe secret keys. The script reads STRIPE_SECRET_KEY from the environment.
- By default the script runs in dry-run mode and will not create resources unless --apply is passed.
- The script refuses to make live-mode changes if STRIPE_SECRET_KEY appears to be a live key unless you pass --live.

Setup

1) Create a Python virtualenv and install the Stripe SDK:

   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install stripe

2) Set your Stripe test secret key (example):

   export STRIPE_SECRET_KEY="sk_test_..."

Dry-run (recommended first)

This checks your Stripe account for existing Products/Prices and prints the actions the script would take:

   python3 scripts/stripe_create_catalog.py --catalog billing/blackroad_pricing_catalog.json --dry-run

Apply changes in test mode

After reviewing the dry-run output, create the products/prices in the Stripe account referenced by STRIPE_SECRET_KEY:

   python3 scripts/stripe_create_catalog.py --catalog billing/blackroad_pricing_catalog.json --apply

Allow live-mode (explicit)

To allow the script to modify a live Stripe account, set STRIPE_SECRET_KEY to a live key and pass --live:

   export STRIPE_SECRET_KEY="sk_live_..."  # DANGEROUS
   python3 scripts/stripe_create_catalog.py --catalog billing/blackroad_pricing_catalog.json --apply --live

What the script creates
- Product objects for each entry in products and usage_products
- Recurring monthly Prices for base tiers (lookup_key present for every Price)
- Metered usage Prices for atomic usage products (lookup_key present)
- All Products and Prices include metadata copied from the catalog plus a catalog_product_key or price_key
- A mapping file billing/stripe_price_map.json is written with created or found price IDs

Lookup keys
- Every Price in the catalog includes lookup_key (e.g., "blackroad_base_consumer_monthly"). Use that lookup_key in the application to retrieve price IDs or to drive billing logic.

Atomic pricing considerations
- Very small per-event rates are aggregated (routed events and memory records) into per-1k units to avoid sub-cent rounding issues.
- infra_cost_markup expects quantities reported in integer cents (see catalog metadata) — report raw cents as quantity (e.g., quantity=12345 for $123.45).
- volatility_premium is created as a placeholder and flagged as manual: it should be applied via a manual invoice item until policy for automation is finalized.

Safety
- The script checks for existing Prices by lookup_key and reuses them to avoid duplicates.
- Always run the dry-run first.

If anything in your environment is missing (STRIPE_SECRET_KEY, stripe package), the script will fail fast and explain what is required.
