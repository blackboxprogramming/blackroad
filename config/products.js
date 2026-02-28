'use strict';

/**
 * BlackRoad production product catalog.
 *
 * Each entry maps to a portal described in PORTALS.md and is ready to be
 * synced with Stripe Products via the API.
 */

const products = [
  {
    id: 'roadbook',
    name: 'Roadbook',
    description: 'Trip journals with photos, itineraries and map routes.',
    active: true,
    tier: 'free',
    stripe_price_id: null, // populated after Stripe sync
    metadata: { portal: 'roadbook', stack: 'node-prisma-postgres-s3' }
  },
  {
    id: 'roadview',
    name: 'Roadview',
    description: 'Stream user journeys on an interactive map with clustering and filters.',
    active: true,
    tier: 'pro',
    stripe_price_id: null,
    metadata: { portal: 'roadview', stack: 'websocket-postgis' }
  },
  {
    id: 'lucidia',
    name: 'Lucidia',
    description: 'Knowledge base of travel guides and user tips using MDX articles.',
    active: true,
    tier: 'free',
    stripe_price_id: null,
    metadata: { portal: 'lucidia', stack: 'nestjs-search' }
  },
  {
    id: 'roadcode',
    name: 'Roadcode',
    description: 'Collaborative coding playground for trip-related tools.',
    active: true,
    tier: 'pro',
    stripe_price_id: null,
    metadata: { portal: 'roadcode', stack: 'containers-git' }
  },
  {
    id: 'radius',
    name: 'Radius',
    description: 'Local meetup planner highlighting events near a user\'s current position.',
    active: true,
    tier: 'free',
    stripe_price_id: null,
    metadata: { portal: 'radius', stack: 'redis-geospatial' }
  },
  {
    id: 'roadworld',
    name: 'Roadworld',
    description: 'Social feed aggregating activity from all portals.',
    active: true,
    tier: 'pro',
    stripe_price_id: null,
    metadata: { portal: 'roadworld', stack: 'kafka-graphql' }
  },
  {
    id: 'roadcoin',
    name: 'Roadcoin',
    description: 'Wallet dashboard showing token balances and staking actions.',
    active: true,
    tier: 'enterprise',
    stripe_price_id: null,
    metadata: { portal: 'roadcoin', stack: 'rust-ledger' }
  },
  {
    id: 'roadchain',
    name: 'Roadchain',
    description: 'Explorer for on-chain travel proofs and smart-contract interactions.',
    active: true,
    tier: 'enterprise',
    stripe_price_id: null,
    metadata: { portal: 'roadchain', stack: 'indexer-chain' }
  },
  {
    id: 'roadie',
    name: 'Roadie',
    description: 'Mobile assistant guiding users through trips with voice commands.',
    active: true,
    tier: 'pro',
    stripe_price_id: null,
    metadata: { portal: 'roadie', stack: 'stt-pipeline' }
  },
  {
    id: 'prism',
    name: 'Prism Console',
    description: 'Master console unifying tools from all portals through customizable tiles and global search.',
    active: true,
    tier: 'enterprise',
    stripe_price_id: null,
    metadata: { portal: 'prism', stack: 'orchestrator-sso' }
  },
  {
    id: 'blackroad-drive',
    name: 'BlackRoad Drive',
    description: 'Cloud storage for trip documents, photos and itineraries backed by Google Drive and S3.',
    active: true,
    tier: 'pro',
    stripe_price_id: null,
    metadata: { portal: 'drive', stack: 'google-drive-s3' }
  }
];

function getAllProducts() {
  return products;
}

function getActiveProducts() {
  return products.filter(p => p.active);
}

function getProductById(id) {
  return products.find(p => p.id === id) || null;
}

function getProductsByTier(tier) {
  return products.filter(p => p.tier === tier);
}

module.exports = {
  products,
  getAllProducts,
  getActiveProducts,
  getProductById,
  getProductsByTier
};
