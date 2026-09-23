"""Tests run entirely in temporary Git repositories with no remote."""
import subprocess
import tempfile
from pathlib import Path
import unittest

from git_autonomy.connector import GitConnector, GitPlanError


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class GitConnectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test Agent")
        git(self.root, "config", "user.email", "agent@example.invalid")
        (self.root / "kept.txt").write_text("old\n")
        git(self.root, "add", "kept.txt")
        git(self.root, "commit", "-qm", "Initial")
        git(self.root, "switch", "-qc", "agent/connector")
        self.connector = GitConnector(self.root)

    def test_commits_only_selected_files_and_never_pushes(self):
        (self.root / "kept.txt").write_text("new\n")
        (self.root / "other.txt").write_text("unrelated\n")
        plan = self.connector.plan(["kept.txt"])
        head = self.connector.apply(plan, "Update kept file")
        self.assertEqual(head, git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(git(self.root, "show", "--pretty=format:", "--name-only", "HEAD"), "kept.txt")
        self.assertTrue((self.root / "other.txt").exists())
        self.assertEqual(git(self.root, "status", "--porcelain"), "?? other.txt")

    def test_rejects_stale_plan(self):
        (self.root / "kept.txt").write_text("new\n")
        plan = self.connector.plan(["kept.txt"])
        (self.root / "kept.txt").write_text("changed again\n")
        with self.assertRaisesRegex(GitPlanError, "changed since planning"):
            self.connector.apply(plan, "Should not commit")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s"), "Initial")

    def test_rejects_main_staged_changes_and_escape(self):
        (self.root / "kept.txt").write_text("new\n")
        with self.assertRaises(GitPlanError):
            self.connector.plan(["../outside.txt"])
        git(self.root, "add", "kept.txt")
        with self.assertRaisesRegex(GitPlanError, "staged changes"):
            self.connector.plan(["kept.txt"])
        git(self.root, "reset", "-q", "HEAD")
        git(self.root, "switch", "-qc", "main")
        with self.assertRaisesRegex(GitPlanError, "feature branch"):
            self.connector.plan(["kept.txt"])

    def test_rejects_symlink_and_unmodified_file(self):
        (self.root / "alias.txt").symlink_to("kept.txt")
        with self.assertRaises(GitPlanError):
            self.connector.plan(["alias.txt"])
        with self.assertRaises(GitPlanError):
            self.connector.plan(["kept.txt"])


if __name__ == "__main__":
    unittest.main()
