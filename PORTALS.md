# BlackRoad Portal Designs

This document outlines interface concepts and backend logic for a suite of community portals.

## Roadbook
- **Interface**: Trip journals with photos, itineraries and map routes.
- **Backend Logic**: Node.js service with Prisma + PostgreSQL; uploads stored on S3.

## Roadview
- **Interface**: Stream user journeys on an interactive map with clustering and filters.
- **Backend Logic**: WebSocket gateway for live updates; GIS queries served by PostGIS.

## Lucidia
- **Interface**: Knowledge base of travel guides and user tips using MDX articles.
- **Backend Logic**: Content API built with NestJS exposing search and tagging endpoints.

## Roadcode
- **Interface**: Collaborative coding playground for trip-related tools.
- **Backend Logic**: Runs containerized sandboxes; maintains revision history in Git.

## Radius
- **Interface**: Local meetup planner highlighting events near a user's current position.
- **Backend Logic**: Geospatial lookups on a Redis-backed cache with scheduled jobs for event reminders.

## Roadcode + Lucidia Co‑Coding Portal
- **Interface**: Dual-pane editor where coding snippets link directly to Lucidia docs.
- **Backend Logic**: Shares Roadcode's sandbox infrastructure and Lucidia's content APIs.

## Roadview (extended)
- **Interface**: 3D globe rendering of trips with WebGL and immersive flyovers.
- **Backend Logic**: Tile server that aggregates route data and streams binary geometry.

## Roadworld
- **Interface**: Social feed aggregating activity from all portals.
- **Backend Logic**: Event bus (Kafka) fan-out to services; GraphQL gateway composes feeds.

## Roadcoin
- **Interface**: Wallet dashboard showing token balances and staking actions.
- **Backend Logic**: Rust microservice handling ledger state and transaction signing.

## Roadchain
- **Interface**: Explorer for on-chain travel proofs and smart-contract interactions.
- **Backend Logic**: Indexer service that syncs chain events into a searchable database.

## Roadie
- **Interface**: Mobile assistant guiding users through trips with voice commands.
- **Backend Logic**: Uses a speech-to-text pipeline and connects to portal APIs for context.

