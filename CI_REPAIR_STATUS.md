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

`tests/integration/test_complete_platform.py` expects eight services, PostgreSQL, and Redis. Its endpoint and database configuration does not match the current default Compose setup. Installing test dependencies makes the suite collectable; it does not provision that platform.

The dashboard and mobile manifests lack committed lockfiles expected by `npm ci` and setup-node caching. The mobile manifest also lacks the lint script requested by CI. These frontend prerequisites still require repair.

The Security-tab upload previously returned `Resource not accessible by integration`. This patch does not change token permissions or repository access controls. The report artifact is additional evidence, not a successful Security-tab upload.

The load-test job still needs its k6 installation and application startup verified. Build, performance, staging, and production deployment behavior are not established by the offline regression suite.

Existing advisory formatter, type-check, and frontend-lint steps still use `continue-on-error`; the strict regression job is a separate check. Passing an advisory step does not certify its underlying tool result.

## Upstream action references

- [Upload-artifact migration guidance](https://github.com/actions/upload-artifact)
- [Supported CodeQL Action versions](https://github.com/github/codeql-action#supported-versions-of-the-codeql-action)
