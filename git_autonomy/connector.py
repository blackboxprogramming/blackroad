"""Explicit, local Git commits with a reviewable plan and stale-state checks.

No explicit network calls, implicit staging, automatic pushes, or shell interpolation.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Tuple


class GitPlanError(RuntimeError):
    """A Git operation failed or the workspace no longer matches its plan."""


@dataclass(frozen=True)
class GitPlan:
    repository: str
    branch: str
    head: str
    paths: Tuple[str, ...]
    hashes: Tuple[str, ...]


class GitConnector:
    def __init__(self, repository):
        root = Path(repository).resolve()
        result = self._run_at(root, "rev-parse", "--show-toplevel")
        if root != Path(result.strip()).resolve():
            raise GitPlanError("Repository must be its Git worktree root")
        self.root = root

    @staticmethod
    def _run_at(root, *args):
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        if result.returncode:
            raise GitPlanError(result.stderr.strip() or "Git command failed")
        return result.stdout

    def _git(self, *args):
        return self._run_at(self.root, *args)

    def _state(self):
        branch = self._git("symbolic-ref", "--quiet", "--short", "HEAD").strip()
        if branch in ("main", "master"):
            raise GitPlanError("Create a feature branch before planning a commit")
        if self._git("diff", "--cached", "--name-only", "-z"):
            raise GitPlanError("Index contains staged changes; clear them before planning")
        return branch, self._git("rev-parse", "HEAD").strip()

    def _path(self, name):
        if not isinstance(name, str) or not name or "\x00" in name or "\n" in name:
            raise GitPlanError("Paths must be nonempty, single-line strings")
        relative = Path(name)
        if relative.is_absolute() or name.startswith("-") or any(p in (".", "..") for p in relative.parts):
            raise GitPlanError(f"Invalid relative path: {name!r}")
        resolved = (self.root / relative).resolve()
        if not resolved.is_relative_to(self.root) or not resolved.is_file() or (self.root / relative).is_symlink():
            raise GitPlanError(f"Path must be a regular file within the worktree: {name!r}")
        return relative.as_posix(), hashlib.sha256(resolved.read_bytes()).hexdigest()

    def plan(self, paths):
        branch, head = self._state()
        if not paths:
            raise GitPlanError("Select at least one changed file")
        pairs = tuple(sorted({self._path(path) for path in paths}))
        names = tuple(path for path, _ in pairs)
        if len(names) != len(set(names)):
            raise GitPlanError("A path was specified with conflicting content")
        changed = set(self._git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *names).split("\x00"))
        # Porcelain entries have two status characters and one space before each path.
        observed = {entry[3:] for entry in changed if entry}
        if set(names) != observed:
            raise GitPlanError(f"Selected paths must all have Git changes: {sorted(set(names) - observed)}")
        return GitPlan(str(self.root), branch, head, names, tuple(digest for _, digest in pairs))

    def apply(self, plan, message):
        if not isinstance(plan, GitPlan) or plan.repository != str(self.root):
            raise GitPlanError("Plan belongs to another repository")
        if not isinstance(message, str) or not re.search(r"\S", message) or "\x00" in message:
            raise GitPlanError("Commit message is required")
        branch, head = self._state()
        if (branch, head) != (plan.branch, plan.head):
            raise GitPlanError("Branch or HEAD changed since planning")
        current = self.plan(plan.paths)
        if current != plan:
            raise GitPlanError("Selected files changed since planning; create a new plan")
        self._git("add", "--", *plan.paths)
        staged = set(filter(None, self._git("diff", "--cached", "--name-only", "-z").split("\x00")))
        if staged != set(plan.paths):
            raise GitPlanError("Staged files differ from the plan; inspect the index")
        for path, digest in zip(plan.paths, plan.hashes):
            staged_bytes = subprocess.run(
                ["git", "-C", str(self.root), "show", f":{path}"],
                capture_output=True, check=True,
            ).stdout
            if hashlib.sha256(staged_bytes).hexdigest() != digest:
                raise GitPlanError("Index content changed since planning; inspect the index")
        self._git("-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                  "commit", "-m", message)
        return self._git("rev-parse", "HEAD").strip()
