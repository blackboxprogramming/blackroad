#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/srv/blackroad"
BRANCH="main"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Repository missing at $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"

git fetch origin "$BRANCH"

LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/"$BRANCH")

if [[ "$LOCAL_HASH" != "$REMOTE_HASH" ]]; then
  echo "Updating: $LOCAL_HASH -> $REMOTE_HASH"
  git reset --hard "origin/$BRANCH"
  npm install --production
  systemctl restart blackroad-api.service
  systemctl reload nginx
  echo "Deploy complete: $(git rev-parse --short HEAD)"
fi
