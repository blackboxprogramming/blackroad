# BlackRoad React Dashboard Guide

## Overview

Modern, responsive web dashboard for BlackRoad SaaS platform with real-time analytics, billing management, and customer insights. Built with React 18 + Vite + Tailwind CSS.

**Features:**
- 📊 Real-time analytics with ML predictions
- 💳 Billing & invoice management
- 🔐 API key management
- 📈 Customer segmentation & cohort analysis
- 🎨 Beautiful, responsive UI
- ⚡ Fast performance (Vite)

## Installation & Setup

### Prerequisites
- Node.js 16+ and npm
- API backend running on port 8000 (billing service)

### Quick Start

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Start development server (runs on port 3000)
npm run dev

# Build for production
npm run build
```

Access dashboard at: **http://localhost:3000**

## Project Structure

```
dashboard/
├── index.html                 # Main HTML entry
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind CSS config
├── package.json              # Dependencies
├── src/
│   ├── main.jsx             # React entry point
│   ├── App.jsx              # Main app component
│   ├── index.css            # Global styles
│   ├── components/          # Reusable components
│   │   ├── Navigation.jsx   # Sidebar navigation
│   │   ├── StatCard.jsx     # Stats display card
│   │   └── Chart.jsx        # Chart wrapper
│   ├── pages/               # Page components
│   │   ├── Dashboard.jsx    # Main dashboard (8 stats + 2 charts)
│   │   ├── Analytics.jsx    # Advanced analytics (ML insights)
│   │   ├── Billing.jsx      # Billing & invoices
│   │   └── Settings.jsx     # API keys & webhooks
│   ├── stores/              # Zustand state management
│   ├── api/                 # API client functions
│   ├── hooks/               # Custom React hooks
│   └── utils/               # Utility functions
```

## Pages & Features

### 1. Dashboard (Home)
**Path:** `/`
**Purpose:** Quick overview of key metrics

**Components:**
- 4 stat cards showing:
  - Monthly requests count
  - Revenue earned
  - Current subscription tier
  - Active concurrent users
- 2 charts:
  - Line chart: Usage trend (7-day)
  - Bar chart: Daily breakdown

**Data Sources:**
- `/api/billing/usage` - Monthly metrics
- `/api/analytics/dashboard` - Aggregated stats

### 2. Analytics
**Path:** `/analytics`
**Purpose:** Advanced ML-driven insights

**Displays:**
- Performance metrics (avg response time, error rate, P95 latency, throughput)
- 12-month LTV forecast chart
- Churn risk distribution (pie chart)
- Cohort retention analysis (bar chart)
- Customer segmentation breakdown (expandable)

**ML Models Integration:**
- Churn prediction: Shows risk distribution
- LTV forecasting: 12-month revenue projection
- Cohort analysis: Week-by-week retention tracking
- Segmentation: Customer buckets (Enterprise/Mid-Market/SMB/Starter)

**Data Sources:**
- `/api/ml/churn-prediction` - Churn risk scores
- `/api/ml/ltv-forecast` - 12-month LTV
- `/api/ml/cohort-analysis` - Cohort retention
- `/api/customer-analytics/segmentation` - Segments

### 3. Billing
**Path:** `/billing`
**Purpose:** Invoice & subscription management

**Tabs:**
1. **Current Month**
   - Active plan (Light, Power, Enterprise)
   - Monthly price
   - Next billing date
   - Usage forecast
   - Upgrade/Cancel buttons

2. **Invoice History**
   - Table of past invoices
   - Invoice ID, date, amount, status
   - Download PDF links
   - Filters (paid/pending/failed)

3. **Payment Methods**
   - Current credit cards
   - Add/remove payment methods
   - Card details (last 4 digits)

**Data Sources:**
- `/api/billing/subscription` - Current plan
- `/api/billing/invoices` - Invoice history
- `/api/billing/usage` - Usage metrics

### 4. Settings
**Path:** `/settings`
**Purpose:** Configuration & administration

**Sections:**
1. **Organization**
   - Company name
   - Admin email
   - Save changes button

2. **API Keys**
   - List of active keys (production & test)
   - Copy to clipboard
   - Last used timestamp
   - Generate new key button

3. **Webhooks**
   - List of webhook endpoints
   - Active/inactive status
   - Event subscriptions
   - Edit/delete/add endpoints

**Data Sources:**
- `/api/carkeys/api-keys` - API keys management
- `/api/carkeys/webhooks` - Webhook endpoints

## Component Library

### StatCard
Displays a single metric with label and subtext

```jsx
<StatCard 
  label="Monthly Revenue"
  value="$2,450"
  subtext="USD"
/>
```

### Navigation
Sidebar with 4 main navigation items (using Lucide icons)

**Items:**
- Dashboard (BarChart3)
- Analytics (TrendingUp)
- Billing (CreditCard)
- Settings (Settings)

## Authentication

### Token Management
Dashboard uses bearer token authentication (compatible with CarKeys system):

```javascript
// Token from URL param or localStorage
const token = new URLSearchParams(window.location.search).get('token') || 
              localStorage.getItem('token')

// Automatically stored in localStorage
localStorage.setItem('token', token)
```

### API Requests
All requests include authorization header:

```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

### Token Flow
1. User logs in via CarKeys
2. CarKeys redirects to dashboard with `?token=<token>`
3. Dashboard extracts token and stores in localStorage
4. Subsequent requests use stored token
5. Token persists across page reloads

## API Integration

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://api.blackroad.com`

### Endpoints Used

#### Billing Service (port 8000)
```
GET  /api/billing/usage           - Monthly usage metrics
GET  /api/billing/subscription    - Current plan details
GET  /api/billing/invoices        - Invoice history
GET  /api/billing/forecast        - Usage forecast
POST /api/billing/upgrade         - Change plan
```

#### Admin Dashboard (port 8001)
```
GET  /api/admin/dashboard         - Dashboard metrics
GET  /api/admin/revenue           - Revenue analytics
GET  /api/admin/customers         - Customer metrics
```

#### Customer Analytics (port 8003)
```
GET  /api/customer-analytics/insights  - Per-customer insights
GET  /api/customer-analytics/ltv       - LTV calculations
GET  /api/customer-analytics/churn     - Churn probability
GET  /api/customer-analytics/segmentation - Customer segments
```

#### ML Analytics (port 8005)
```
GET  /api/ml/churn-prediction          - Churn risk scores
GET  /api/ml/ltv-forecast              - LTV forecasting
GET  /api/ml/cohort-analysis           - Cohort retention
GET  /api/ml/anomaly-detection         - Anomaly alerts
GET  /api/ml/segmentation              - Customer segmentation
```

#### CarKeys (API Key Management)
```
GET  /api/carkeys/api-keys             - List API keys
POST /api/carkeys/api-keys             - Create new key
GET  /api/carkeys/webhooks             - List webhooks
POST /api/carkeys/webhooks             - Create webhook
```

## Styling & Customization

### Tailwind CSS Configuration
Located in `tailwind.config.js`

**Custom Colors:**
```javascript
colors: {
  primary: '#667eea',      // Blue
  secondary: '#764ba2'     // Purple
}
```

**Responsive Breakpoints:**
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px

### Theme Customization

To change colors globally:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#your-color',
        secondary: '#your-color'
      }
    }
  }
}
```

## Real-Time Updates

### Polling Strategy
Dashboard uses polling for real-time updates (can upgrade to WebSockets):

```javascript
// Poll every 30 seconds for new data
setInterval(() => {
  fetchDashboardData()
}, 30000)
```

### WebSocket Upgrade Path
To add WebSockets for real-time updates:

```javascript
const socket = io('http://localhost:8000', {
  auth: { token: localStorage.getItem('token') }
})

socket.on('dashboard:update', (data) => {
  setStats(data)
})
```

## Development Features

### Hot Module Reload (HMR)
Vite provides instant code updates during development:

```bash
npm run dev
# Make changes to src/*.jsx files
# Changes appear instantly in browser
```

### ESLint Configuration
Included ESLint setup for code quality:

```bash
npm run lint
```

### Performance Monitoring
Dashboard includes performance tracking:
- Interaction to Next Paint (INP)
- Cumulative Layout Shift (CLS)
- Time to First Byte (TTFB)

## Deployment

### Build for Production
```bash
npm run build
# Creates optimized bundle in dist/
```

### Serve Production Build Locally
```bash
npm run preview
```

### Deploy to AWS S3 + CloudFront
```bash
# Build
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket/dashboard/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

### Docker Deployment
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Integration with Existing Backend

### Connecting to Main API (port 8000)

Update `vite.config.js`:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
```

### Using with AWS ALB

When deploying behind Application Load Balancer:

```javascript
// src/api/client.js
const API_BASE = process.env.REACT_APP_API_URL || 'https://api.blackroad.com'

export const client = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
```

## Testing

### Add Jest + React Testing Library

```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

### Example Test

```javascript
// src/components/StatCard.test.jsx
import { render } from '@testing-library/react'
import StatCard from './StatCard'

describe('StatCard', () => {
  it('displays label and value', () => {
    const { getByText } = render(
      <StatCard label="Revenue" value="$100" subtext="USD" />
    )
    expect(getByText('Revenue')).toBeInTheDocument()
    expect(getByText('$100')).toBeInTheDocument()
  })
})
```

## Performance Optimization

### Bundle Analysis
```bash
npm install --save-dev vite-plugin-visualizer
```

### Image Optimization
Use modern formats (WebP) for charts:
```jsx
<img src="chart.webp" alt="chart" loading="lazy" />
```

### Code Splitting
Vite automatically splits at route boundaries:

```javascript
// pages are loaded on-demand
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))
```

## Troubleshooting

### Dashboard won't load
1. Check backend services are running on ports 8000-8005
2. Verify token is present (check localStorage)
3. Check browser console for CORS errors
4. Verify proxy settings in `vite.config.js`

### Charts not displaying
1. Ensure Recharts data is properly formatted
2. Check ResponsiveContainer parent has height
3. Verify API is returning correct data structure

### API requests failing
1. Verify API server is running: `curl http://localhost:8000/api/health`
2. Check Authorization header is sent
3. Check token has not expired
4. Review CORS headers in API response

## Next Steps

### Feature Enhancements
1. **Add Real-time Notifications** - WebSocket integration for alerts
2. **Export Reports** - PDF/CSV export of metrics
3. **Custom Dashboards** - User-defined widget layouts
4. **Dark Mode** - Toggle dark/light theme
5. **Mobile App** - React Native version

### Integration Opportunities
1. **Slack Integration** - Send alerts to Slack
2. **Email Reports** - Scheduled email digests
3. **Data Export** - BigQuery/Redshift connections
4. **Custom Integrations** - API for external tools

### Performance Improvements
1. **WebSocket** - Real-time data updates
2. **Service Worker** - Offline mode
3. **GraphQL** - Reduce payload size
4. **Edge Caching** - CDN integration

## Support & Documentation

**Repository:** https://github.com/yourusername/blackroad
**API Docs:** See API_DOCUMENTATION.md
**Deployment:** See AWS_DEPLOYMENT_QUICK_START.md
**ML Models:** See ML_ANALYTICS_GUIDE.md

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-04
**Built with:** React 18, Vite, Tailwind CSS, Recharts
