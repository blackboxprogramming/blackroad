# BlackRoad deployment readiness

**Status: blocked by missing source and unfinished deployment backends.** This supersedes the previous production-ready claim.

**We access it all at RoadOS.**  
**We collaborate with Roadies.**  
**We code in Road.**

*Integration is Innovation.*

Evidence from commit `cd3b42e3b33bbdda0e175eff4e679ae345be4465` on the repair branch:

| Area | Verified result |
| --- | --- |
| Dashboard | Clean install, lint and production bundle pass |
| Mobile | Clean install, lint, Expo compatibility and Android/iOS JavaScript exports pass |
| Python | Eight offline regressions pass |
| PostgreSQL and Redis | Five integration checks pass, including the committed migration and uniqueness constraint |
| Complete integration suite | 17 of 22 tests fail; application services and platform tables remain incomplete |
| Production deployment | Not established |

[CI evidence](https://github.com/blackboxprogramming/blackroad/actions/runs/34803253867) · [Integration receipt](https://github.com/blackboxprogramming/0/blob/main/BLACKROAD_INTEGRATION_REPAIR_2026-09-14.md)

## Check the local source prerequisites

From the repository root, with Docker Compose v2, Python 3 and curl installed:

```bash
bash deploy-local.sh --check
```

This resolves the production Compose configuration and checks build directories, Dockerfiles, bind-mount sources and conflicting published ports. It performs no image pulls, builds or container starts. It currently fails because referenced source is absent. Creating empty directories does not satisfy the check.

To inspect the same check directly:

```bash
docker compose -f docker-compose.prod.yml config --format json | python3 scripts/deployment_preflight.py --root .
```

Passing this check proves only that these local prerequisites were found. It does not validate every Dockerfile instruction, runtime dependency, secret, network, image or application behavior.

## Deployment command behavior

`deploy-local.sh` validates before it builds or starts containers. Startup must satisfy Compose's bounded wait. Every one of the eight HTTP health requests must succeed; HTTP errors and timeouts fail verification. It no longer creates empty source directories or announces success after incomplete health checks.

`deploy.py` has no implemented deployment, traffic-switching, rollback or telemetry backend. Those operations now fail explicitly. It no longer simulates successful deployment, load testing or monitoring, and its Git check does not stash the working tree. Its normal deploy command records the failed attempt; it cannot launch a production deployment.

## Work needed

Restore or implement the missing application code and reconcile Compose with actual entry points. The existing dashboard now builds through the react-web service and binds to localhost:3002; Grafana retains port 3000. The separate admin frontend source is still missing. Replace example deployment credentials and validate runtime configuration. Implement deployment and rollback operations against an explicit target, then verify application workflows, migrations, integration tests and operational behavior in that target.

See [the checklist](PRODUCTION_CHECKLIST.md). The repaired commands do not establish production readiness.

Docker references: [Compose config](https://docs.docker.com/reference/cli/docker/compose/config/) and [Compose up](https://docs.docker.com/reference/cli/docker/compose/up/).

## Run the existing dashboard alone

```bash
docker compose -f docker-compose.prod.yml build react-web
docker compose -f docker-compose.prod.yml up -d --no-deps --wait --wait-timeout 60 react-web
python3 scripts/check-dashboard-http.py http://127.0.0.1:3002
```

This starts the static dashboard independently of the incomplete backend stack. Its pages contain sample data. Requests under `/api/` return HTTP 503 with an explicit integration-not-configured message; there is no working API proxy. The HTTP checks verify served HTML, built JavaScript/CSS, SPA routing, health and that API boundary. They do not execute browser JavaScript or verify sign-in.
