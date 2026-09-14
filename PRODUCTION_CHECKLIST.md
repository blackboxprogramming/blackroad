# BlackRoad deployment repair checklist

**Deployment is not ready.** Check items only when linked evidence establishes them for the intended target. The earlier checklist contained commands referencing absent files; use this list with [current deployment status](PRODUCTION_DEPLOYMENT_READY.md).

**We access it all at RoadOS.**  
**We collaborate with Roadies.**  
**We code in Road.**

*Integration is Innovation.*

## Source and configuration

- [ ] Restore or implement all eight service build contexts referenced by production Compose.
- [ ] Restore or replace the referenced frontend build contexts.
- [ ] Supply the real API entry point; the root Dockerfile currently points to absent `app/main.py`.
- [ ] Reconcile migration locations and platform table requirements with the committed schema.
- [ ] Resolve conflicting published ports and missing bind sources.
- [ ] Replace example credentials and verify target-specific configuration without committing secrets.
- [ ] Make `bash deploy-local.sh --check` pass against the complete checkout.

## Application behavior

- [ ] Make all 22 integration tests pass against real services.
- [ ] Replace sample dashboard/mobile data with verified application behavior.
- [ ] Verify sign-in, session restoration, logout and device API routing.
- [ ] Restore native assets and verify native builds on the intended devices.
- [ ] Verify subscription/payment and webhook behavior with an explicitly configured test provider.
- [ ] Measure performance with recorded workload, environment and results.

## Deployment operations

- [ ] Implement real deployment, traffic-switching, rollback and telemetry backends.
- [ ] Verify readiness and post-deployment checks propagate failures.
- [ ] Exercise rollback and database recovery in the intended test environment.
- [ ] Record the exact source commit, built artifacts, target and outcome.

Previously verified component checks are listed in [CI_REPAIR_STATUS.md](CI_REPAIR_STATUS.md). They are not evidence that this checklist is complete.
