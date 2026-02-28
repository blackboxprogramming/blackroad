'use strict';

/**
 * Centralised configuration loader.
 *
 * Reads from process.env (populate via .env in development).
 * All Stripe and Drive keys are required in production; missing keys are
 * surfaced through the /api/config/status health endpoint.
 */

const REQUIRED_KEYS = [
  'STRIPE_SECRET_KEY',
  'STRIPE_PUBLISHABLE_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'GOOGLE_DRIVE_CLIENT_ID',
  'GOOGLE_DRIVE_CLIENT_SECRET',
  'GOOGLE_DRIVE_FOLDER_ID',
  'DATABASE_URL',
  'JWT_SECRET'
];

function loadConfig() {
  return {
    port: process.env.PORT || 4000,
    nodeEnv: process.env.NODE_ENV || 'development',

    stripe: {
      secretKey: process.env.STRIPE_SECRET_KEY || '',
      publishableKey: process.env.STRIPE_PUBLISHABLE_KEY || '',
      webhookSecret: process.env.STRIPE_WEBHOOK_SECRET || ''
    },

    drive: {
      clientId: process.env.GOOGLE_DRIVE_CLIENT_ID || '',
      clientSecret: process.env.GOOGLE_DRIVE_CLIENT_SECRET || '',
      redirectUri: process.env.GOOGLE_DRIVE_REDIRECT_URI || 'https://blackroad.io/api/drive/callback',
      folderId: process.env.GOOGLE_DRIVE_FOLDER_ID || ''
    },

    database: {
      url: process.env.DATABASE_URL || ''
    },

    llm: {
      baseUrl: process.env.LLM_BASE_URL || 'http://127.0.0.1:8083'
    },

    s3: {
      bucket: process.env.S3_BUCKET || 'blackroad-uploads',
      region: process.env.S3_REGION || 'us-east-1',
      accessKey: process.env.S3_ACCESS_KEY || '',
      secretKey: process.env.S3_SECRET_KEY || ''
    },

    auth: {
      jwtSecret: process.env.JWT_SECRET || '',
      sessionSecret: process.env.SESSION_SECRET || ''
    }
  };
}

/**
 * Returns a list of required environment variables that are missing or empty.
 */
function getMissingKeys() {
  return REQUIRED_KEYS.filter(k => !process.env[k]);
}

module.exports = { loadConfig, getMissingKeys, REQUIRED_KEYS };
