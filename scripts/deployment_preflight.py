"""Check resolved Compose JSON before image pulls, builds, or container starts.

Usage: docker compose -f docker-compose.prod.yml config --format json |
       python3 scripts/deployment_preflight.py --root .
This checks local source prerequisites, not runtime or production readiness.
"""

import argparse
import json
from pathlib import Path
import sys


def check_sources(config, root):
    root = Path(root).resolve()
    if not isinstance(config, dict) or not isinstance(config.get('services'), dict):
        return ['Compose configuration must contain a services mapping']
    if not config['services']:
        return ['Compose configuration has no services']
    errors = []
    published = []
    for name, service in config['services'].items():
        if not isinstance(service, dict):
            errors.append(f'{name}: invalid service configuration')
            continue
        build = service.get('build')
        if build is not None:
            if isinstance(build, str):
                build = {'context': build}
            if not isinstance(build, dict) or not isinstance(build.get('context', '.'), str):
                errors.append(f'{name}: invalid build configuration')
                continue
            context_name = build.get('context', '.')
            if '://' in context_name or context_name.startswith('git@'):
                errors.append(f'{name}: remote build context cannot be verified locally')
                continue
            context = (root / context_name).resolve()
            if not context.is_dir():
                errors.append(f'{name}: missing build context {context_name}')
            elif 'dockerfile_inline' not in build:
                dockerfile_name = build.get('dockerfile', 'Dockerfile')
                if not isinstance(dockerfile_name, str):
                    errors.append(f'{name}: invalid Dockerfile path')
                    continue
                dockerfile = context / dockerfile_name
                if not dockerfile.is_file():
                    errors.append(f'{name}: missing Dockerfile {dockerfile_name}')
                elif 'app.main:app' in dockerfile.read_text() and not (context / 'app/main.py').is_file():
                    errors.append(f'{name}: Dockerfile references missing app/main.py')
        for volume in service.get('volumes', []):
            if not isinstance(volume, dict):
                errors.append(f'{name}: volumes must be resolved by Compose config --format json')
                continue
            if volume.get('type') == 'bind':
                source = volume.get('source')
                if not isinstance(source, str) or not source or not (root / source).exists():
                    errors.append(f'{name}: missing bind source {source}')
        for port in service.get('ports', []):
            if not isinstance(port, dict):
                errors.append(f'{name}: ports must be resolved by Compose config --format json')
                continue
            value = port.get('published')
            if value is None:
                continue
            # Dynamic port 0 is allocated by the runtime and does not conflict.
            if str(value) == '0':
                continue
            try:
                endpoints = str(value).split('-')
                first, last = int(endpoints[0]), int(endpoints[-1])
                if len(endpoints) > 2 or not 1 <= first <= last <= 65535:
                    raise ValueError
            except ValueError:
                errors.append(f'{name}: invalid published port')
                continue
            protocol = port.get('protocol', 'tcp')
            host = port.get('host_ip', '0.0.0.0')
            for other_name, other_first, other_last, other_protocol, other_host in published:
                overlap = max(first, other_first) <= min(last, other_last)
                same_host = host == other_host or host in ('0.0.0.0', '::') or other_host in ('0.0.0.0', '::')
                if overlap and protocol == other_protocol and same_host:
                    errors.append(f'{name}: published port {value}/{protocol} conflicts with {other_name}')
            published.append((name, first, last, protocol, host))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        errors = check_sources(json.load(sys.stdin), args.root)
    except (ValueError, OSError, TypeError) as exc:
        # Do not echo resolved configuration, which may contain credentials.
        print(f'Deployment source check could not complete: {type(exc).__name__}', file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print('Deployment blocked by source/configuration errors.', file=sys.stderr)
        return 1
    print('Local source prerequisites found. Runtime health and deployment remain unverified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
