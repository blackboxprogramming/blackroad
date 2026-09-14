"""Offline regressions; no API server, database, or provider is contacted."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PersonalizationRegressionTests(unittest.TestCase):
    def setUp(self):
        module = load_source("tested_personalizer", "personalization/personalizer.py")
        self.engine = module.PersonalizationEngine()

    def test_cohort_returns_matching_profiles_only(self):
        for name in ("alice", "cecilia", "lucidia"):
            profile = self.engine.get_or_create_profile(name)
            if name != "cecilia":
                profile.segments.add("builders")
        summaries = self.engine.get_cohort_profiles("builders")
        self.assertEqual({p["user_id"] for p in summaries}, {"alice", "lucidia"})
        self.assertEqual(len(summaries), 2)
        self.assertEqual(set(self.engine.profiles), {"alice", "cecilia", "lucidia"})

    def test_unknown_cohort_does_not_create_profiles(self):
        self.engine.get_or_create_profile("alice")
        self.assertEqual(self.engine.get_cohort_profiles("unknown"), [])
        self.assertEqual(set(self.engine.profiles), {"alice"})


class SearchRegressionTests(unittest.TestCase):
    def setUp(self):
        module = load_source("tested_search_analytics", "search_engine/analytics.py")
        self.analytics = module.SearchAnalytics(max_queries=3)

    def test_trending_queries_count_repeated_queries_and_limit(self):
        for query in ("RoadOS", "Road", "RoadOS"):
            self.analytics.record_search(query, 1, 2.0)
        self.assertEqual(self.analytics.get_trending_queries(1), [("RoadOS", 2)])

    def test_expired_query_leaves_the_trending_window(self):
        for query in ("old", "Road", "Road", "Roadies"):
            self.analytics.record_search(query, 1, 2.0)
        self.assertEqual(self.analytics.get_trending_queries(), [("Road", 2), ("Roadies", 1)])


class CIResultRegressionTests(unittest.TestCase):
    def run_gate(self, value):
        env = {**os.environ, "CI_NEEDS": value}
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/check-ci-results.py")],
            env=env, capture_output=True, text=True, check=False,
        )

    def test_all_success_passes(self):
        result = self.run_gate(json.dumps({"python": {"result": "success"}, "web": {"result": "success"}}))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_python_failure_cannot_pass(self):
        result = self.run_gate(json.dumps({"python": {"result": "success"}, "security": {"result": "failure"}}))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("security", result.stderr)

    def test_cancelled_skipped_and_unknown_results_fail(self):
        for status in ("cancelled", "skipped", "queued", "", None):
            with self.subTest(status=status):
                self.assertNotEqual(self.run_gate(json.dumps({"job": {"result": status}})).returncode, 0)

    def test_missing_and_malformed_evidence_fails(self):
        for evidence in ("", "{}", "[]", "null", "bad json", '{"job": null}', '{"job": {}}'):
            with self.subTest(evidence=evidence):
                self.assertNotEqual(self.run_gate(evidence).returncode, 0)


if __name__ == "__main__":
    unittest.main()
