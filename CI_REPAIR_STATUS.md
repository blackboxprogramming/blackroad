# BlackRoad CI repair

This repair makes selected Python components usable and makes CI failures visible. It does not certify the complete platform or a production deployment.

## Repaired

- Customer analytics imports SQLAlchemy `distinct` before using it.
- Cohort lookup uses the matching profile's user ID.
- Search analytics imports the `Tuple` type used by its public annotation.
- Eight offline regressions cover cohorts, trending-query retention, and CI result handling.
- Test collection dependencies are declared in `requirements-test.txt` and installed in both test workflows.
- The CI/CD test command targets the existing `tests/` directory; failed tests are no longer ignored.
- Artifact uploads use v4, and SARIF upload uses CodeQL Action v4.
- The Trivy report is retained as a workflow artifact independently of the Security-tab upload result.
- The final CI gate fails for any failed, cancelled, skipped, missing, or malformed required job result.
- Load-test and report-analysis failures are no longer ignored. The pipeline uses Docker Compose v2 syntax.

## Verify the offline behavior

From the repository root:

```bash
python -m unittest discover -s tests/unit -v
```

This suite does not contact APIs, databases, or external providers. The separate Python Regression Checks workflow runs it on pull requests and default-branch updates.

## Integration prerequisites remain incomplete

`tests/integration/test_complete_platform.py` expects eight services, PostgreSQL, and Redis. Its service endpoints do not match the current default Compose setup. Both test jobs now provision disposable PostgreSQL and Redis, pass their URLs to the suite, and apply the committed Alembic migration. The production Compose service directories and the root Dockerfile entry point `app.main:app` are absent from this checkout; those application services are not provisioned.

## Frontend repair

Both frontends now include npm lockfiles and ESLint configurations. CI runs on Node 22 and fails if frontend lint fails. The dashboard builds through Vite with Tailwind/PostCSS processing; the unused import of the nonexistent Chart component is removed.

The mobile manifest removes the unpublished, unused chart-wrapper and legacy navigation dependencies. React Native packages match Expo 49's published compatibility map. The stack navigator uses its actual `createStackNavigator` export, native gesture setup loads first, and the status bar uses Expo's `style` prop. The Expo entry point and Babel preset are explicit.

From `dashboard/`:

```bash
npm ci
npm run lint
npm run build
```

From `mobile/`:

```bash
npm ci
npm run lint
CI=1 npm run check:dependencies
CI=1 npm run export:check
```

CI retains the dashboard build and Android/iOS JavaScript bundles as artifacts. Mobile export checks module resolution and Hermes compilation; it does not build or run a native application.

Remaining frontend limitations:

- Dashboard and mobile screens still contain sample data and unfinished actions.
- Mobile authentication state, logout, and device API routing remain incomplete. Successful bundling does not establish a working sign-in flow.
- `mobile/app.json` references icon/splash assets absent from the repository. Native configuration, notification setup, device builds, and store submission still need verification.
- Expo 49 and the existing frontend toolchains retain older dependencies. This repair establishes reproducible installation, not a completed SDK/security upgrade.
- Browser interaction and native-device behavior have not been validated. The dashboard build reports a bundle-size warning.

## Other CI limitations

The Security-tab upload previously returned `Resource not accessible by integration`. This patch does not change token permissions or repository access controls. The report artifact is additional evidence, not a successful Security-tab upload.

The load-test job still needs its k6 installation and application startup verified. Build, performance, staging, and production deployment behavior are not established by the offline regression suite.

Existing advisory formatter and type-check steps still use `continue-on-error`; the strict regression job is a separate check. Passing an advisory step does not certify its underlying tool result. Frontend lint is now enforced.

## Upstream action references

- [Upload-artifact migration guidance](https://github.com/actions/upload-artifact)
- [Supported CodeQL Action versions](https://github.com/github/codeql-action#supported-versions-of-the-codeql-action)
- [React Navigation 6 stack setup](https://reactnavigation.org/docs/6.x/stack-navigator/)
- Expo compatibility versions were read from `expo@49.0.23/bundledNativeModules.json` and checked with `expo install --check`.

## Database and cache repair

The Alembic environment no longer imports the absent `app.models`. Explicit migrations work without ORM metadata; autogeneration remains unavailable until real model metadata exists. Logging configuration includes the required root logger. Percent-encoded database URLs survive Alembic configuration interpolation.

Integration tests read `DATABASE_URL` and `REDIS_URL`, with local development defaults. CI uses disposable service credentials. Redis write checks use a unique, expiring key and clean up in a finally block. No shared `test_key` is overwritten.

Two additional integration checks verify the committed revision, all six monetization tables, and the customer-ID uniqueness constraint using a rolled-back transaction. The existing platform-table assertion (`users`, `customers`, `subscriptions`, `transactions`) remains: those tables have no committed migration, so that contract still fails. No dummy tables or health-only application services were added.

Local migration SQL generation is available without a database:

```bash
pip install -r requirements-test.txt
alembic upgrade head --sql
```

The service-backed checks run in the existing GitHub jobs against PostgreSQL and Redis. A passing migration does not establish that the missing application stack works.

## Deployment reporting repair

A source-readiness CI job resolves production Compose and checks local build paths, Dockerfiles, bind sources and published-port conflicts before any deployment action. Missing sources cause a failing check. The local deployment script uses the same validation, supports `--check`, propagates container-start failures, and fails on HTTP health errors.

The Python deployment interface's simulated deployment/traffic/telemetry helpers now report unimplemented operations. It checks backend availability before invoking Git, Docker or AWS, records failed deployment attempts, and does not automatically stash changes. HTTP smoke checks reject error responses.

Twelve offline regression tests cover these failure paths, including execution of the shell script with controlled command fixtures. Those fixtures test command ordering and failure propagation; they do not prove real container deployment. The production-ready, platform-complete and checklist documents now describe verified results and outstanding work.
