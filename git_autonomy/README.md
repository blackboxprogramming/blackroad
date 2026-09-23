# Local Git autonomy connector

`GitConnector` lets an agent prepare a specific list of changed files on a feature
branch and commit them only if the branch, HEAD and file contents still match its
plan. It never pushes, merges, changes remotes, or stages unrelated files. It
requires an empty Git index before planning. `apply` returns the new commit SHA.

```python
from git_autonomy import GitConnector

connector = GitConnector('/path/to/worktree')
plan = connector.plan(['src/example.py'])
print(plan)  # inspect the exact branch, base commit, path and SHA-256
commit = connector.apply(plan, 'Implement example')
```

The worktree can have unrelated unstaged edits. A file must exist as a regular
file and have a Git change; deletion and rename commits are outside this
connector's current scope. A stale plan raises `GitPlanError`. Failed Git
operations can leave selected files staged: inspect `git status` before retrying.
Git hooks and commit signing are disabled for its commit so a local hook cannot
perform an unplanned side effect. Git filters configured for `git add` remain
subject to the repository's own Git configuration.

Run `python -m unittest git_autonomy.test_connector -v` from the repository root.
For BlackRoad, perform canonical review and publication on Forgejo; GitHub is a
public mirror where available.
