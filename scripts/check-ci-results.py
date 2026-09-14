"""Report every dependency result; only a nonempty all-success set passes."""

import json
import os
import sys


def main():
    try:
        results = json.loads(os.environ.get("CI_NEEDS", ""))
    except (TypeError, ValueError):
        print("CI result evidence is missing or invalid.", file=sys.stderr)
        return 1
    if not isinstance(results, dict) or not results:
        print("CI result evidence must contain dependency jobs.", file=sys.stderr)
        return 1
    failed = []
    for name, job in sorted(results.items()):
        result = job.get("result") if isinstance(job, dict) else None
        print(f"{name}: {result or 'missing'}")
        if result != "success":
            failed.append(name)
    if failed:
        print("CI did not pass: " + ", ".join(failed), file=sys.stderr)
        return 1
    print("All dependency jobs passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
