import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preflight = load_module('deployment_preflight', ROOT / 'scripts/deployment_preflight.py')
deploy = load_module('deployment', ROOT / 'deploy.py')


class SourceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_missing_context_and_empty_placeholder_are_rejected(self):
        config = {'services': {'api': {'build': {'context': 'api'}}}}
        self.assertIn('missing build context', preflight.check_sources(config, self.root)[0])
        (self.root / 'api').mkdir()
        self.assertIn('missing Dockerfile', preflight.check_sources(config, self.root)[0])

    def test_entry_point_and_bind_sources_must_exist(self):
        (self.root / 'Dockerfile').write_text('CMD ["uvicorn", "app.main:app"]')
        config = {'services': {'api': {'build': '.', 'volumes': [
            {'type': 'bind', 'source': 'absent.conf'},
            {'type': 'volume', 'source': 'database_data'},
        ]}}}
        errors = preflight.check_sources(config, self.root)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any('app/main.py' in e for e in errors))
        self.assertTrue(any('absent.conf' in e for e in errors))

    def test_overlapping_host_ports_are_rejected(self):
        config = {'services': {
            'one': {'ports': [{'published': '3000-3002'}]},
            'two': {'ports': [{'published': '3001', 'host_ip': '127.0.0.1'}]},
        }}
        self.assertIn('conflicts with one', preflight.check_sources(config, self.root)[0])
        config['services']['two']['ports'][0]['protocol'] = 'udp'
        self.assertEqual(preflight.check_sources(config, self.root), [])

    def test_present_sources_pass_without_runtime_claim(self):
        (self.root / 'Dockerfile').write_text('FROM scratch\n')
        (self.root / 'config').write_text('test')
        config = {'services': {'api': {'build': '.', 'volumes': [
            {'type': 'bind', 'source': str(self.root / 'config')},
        ]}}}
        self.assertEqual(preflight.check_sources(config, self.root), [])

    def test_malformed_input_fails_without_echoing_secrets(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/deployment_preflight.py')],
            input='{"secret": "PRIVATE_TEST_VALUE"', text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('PRIVATE_TEST_VALUE', result.stderr)


class DeploymentInterface(unittest.TestCase):
    def setUp(self):
        self.pipeline = deploy.DeploymentPipeline(deploy.Environment.STAGING, deploy.DeploymentStrategy.BLUE_GREEN)

    def test_deploy_and_rollback_fail_before_external_operations(self):
        with patch.object(deploy.subprocess, 'run') as run, patch.object(deploy.time, 'sleep') as sleep, \
                patch.object(self.pipeline, 'save_deployment_log') as save:
            self.assertFalse(self.pipeline.deploy())
            self.assertFalse(self.pipeline.rollback('test-version'))
            run.assert_not_called()
            sleep.assert_not_called()
            self.assertEqual(save.call_count, 2)

    def test_unimplemented_operations_do_not_simulate_success(self):
        with patch.object(deploy.subprocess, 'run') as run, patch.object(deploy.time, 'sleep') as sleep:
            for name, args in [
                ('deploy_blue_green', ()), ('deploy_canary', ()),
                ('deploy_to_environment', ('green',)), ('run_load_tests', ('green',)),
                ('warmup_cache', ('green',)), ('switch_traffic', ('blue', 'green')),
                ('set_traffic_split', ('blue', 'green', 90, 10)),
                ('monitor_deployment', ('green',)), ('cleanup_environment', ('blue',)),
                ('check_database_migrations', ()),
            ]:
                with self.subTest(operation=name):
                    self.assertFalse(getattr(self.pipeline, name)(*args))
            with self.assertRaises(NotImplementedError):
                self.pipeline.get_error_rate('green')
            run.assert_not_called()
            sleep.assert_not_called()

    def test_dirty_git_is_not_stashed_and_failed_image_check_is_not_built(self):
        with patch.object(deploy.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, ' M file')) as run:
            self.assertFalse(self.pipeline.check_git_status())
            run.assert_called_once_with(['git', 'status', '--porcelain'], capture_output=True, text=True)
        with patch.object(deploy.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '')) as run:
            self.assertFalse(self.pipeline.check_docker_images())
            run.assert_called_once_with(['docker', 'image', 'inspect', 'blackroad:latest'], capture_output=True, text=True)

    def test_missing_configuration_and_http_failures_fail_checks(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.pipeline.check_configuration())
        with patch.object(deploy.subprocess, 'run', return_value=subprocess.CompletedProcess([], 22)) as run:
            self.assertFalse(self.pipeline.run_smoke_tests('green'))
            self.assertTrue(all('--fail' in call.args[0] for call in run.call_args_list))


class LocalDeploymentScript(unittest.TestCase):
    def run_script(self, config, curl_status=0, up_status=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'bin').mkdir()
            shutil.copy(ROOT / 'deploy-local.sh', root / 'deploy-local.sh')
            shutil.copy(ROOT / 'scripts/deployment_preflight.py', root / 'scripts/deployment_preflight.py')
            (root / 'bin/python3').symlink_to(sys.executable)
            (root / 'compose.json').write_text(json.dumps(config))
            fake = '''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
with (root / 'calls.jsonl').open('a') as f:
    f.write(json.dumps([pathlib.Path(sys.argv[0]).name] + sys.argv[1:]) + '\\n')
if pathlib.Path(sys.argv[0]).name == 'curl':
    sys.exit(int(os.environ['CURL_STATUS']))
if 'config' in sys.argv:
    print((root / 'compose.json').read_text())
if 'up' in sys.argv:
    sys.exit(int(os.environ['UP_STATUS']))
'''
            for tool in ('docker', 'curl'):
                path = root / 'bin' / tool
                path.write_text(fake)
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'],
                       FIXTURE_ROOT=str(root), CURL_STATUS=str(curl_status), UP_STATUS=str(up_status))
            result = subprocess.run(['bash', str(root / 'deploy-local.sh')], cwd='/', env=env,
                                    text=True, capture_output=True, timeout=15)
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            return result, calls

    def test_missing_sources_stop_before_mutations(self):
        result, calls = self.run_script({'services': {'api': {'build': './missing'}}})
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(all('build' not in c and 'up' not in c and 'pull' not in c for c in calls))

    def test_http_errors_cannot_report_success(self):
        result, calls = self.run_script({'services': {'api': {'image': 'fixture'}}}, curl_status=22)
        self.assertNotEqual(result.returncode, 0)
        health_calls = [c for c in calls if c[0] == 'curl']
        self.assertEqual(len(health_calls), 8)
        self.assertTrue(all('--fail' in c for c in health_calls))
        self.assertNotIn('HTTP health checks passed', result.stdout)

    def test_failed_container_start_stops_health_checks(self):
        result, calls = self.run_script({'services': {'api': {'image': 'fixture'}}}, up_status=17)
        self.assertEqual(result.returncode, 17)
        self.assertFalse(any(c[0] == 'curl' for c in calls))


if __name__ == '__main__':
    unittest.main()
