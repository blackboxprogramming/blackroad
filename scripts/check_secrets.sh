#!/usr/bin/env bash
set -euo pipefail

# Lightweight repository secret scanner (read-only). Prints filenames/lines with redacted values.
# Does not modify files or upload anything.

PATTERNS=(
  "sk_live_" "sk_test_" "rk_live_" "rk_test_" "whsec_" "github_pat_" "ghp_" "CLOUDFLARE_API_TOKEN" "OPENAI_API_KEY" "STRIPE_SECRET_KEY=" "-----BEGIN PRIVATE KEY-----" "-----BEGIN RSA PRIVATE KEY-----"
)

GREP_ARGS=()
for p in "${PATTERNS[@]}"; do
  GREP_ARGS+=( -e "$p" )
done

redact_stream() {
  sed -E \
    -e 's/(sk_(live|test)_[^[:space:]]+)/<REDACTED_SK_KEY>/gI' \
    -e 's/(rk_(live|test)_[^[:space:]]+)/<REDACTED_RK_KEY>/gI' \
    -e 's/(whsec_[^[:space:]]+)/<REDACTED_WEBHOOK_SECRET>/gI' \
    -e 's/(github_pat_[^[:space:]]+)/<REDACTED_GITHUB_PAT>/gI' \
    -e 's/(ghp_[^[:space:]]+)/<REDACTED_GHP>/gI' \
    -e 's/(CLOUDFLARE_API_TOKEN=[^[:space:]]+)/CLOUDFLARE_API_TOKEN=<REDACTED>/gI' \
    -e 's/(OPENAI_API_KEY=[^[:space:]]+)/OPENAI_API_KEY=<REDACTED>/gI' \
    -e 's/(STRIPE_SECRET_KEY=[^[:space:]]+)/STRIPE_SECRET_KEY=<REDACTED>/gI' \
    -e 's/(-----BEGIN PRIVATE KEY-----)/-----BEGIN PRIVATE KEY----- <REDACTED>/gI' \
    
}

# Search tracked files (git grep) and untracked files (grep over git ls-files --others)
set +e
tracked_matches=$(git --no-pager grep -nI --no-color "${GREP_ARGS[@]}" 2>/dev/null || true)
untracked_matches=$(git ls-files --others --exclude-standard -z | xargs -0 grep -nI --no-color "${GREP_ARGS[@]}" 2>/dev/null || true)
set -e

all_matches=$(printf "%s\n%s\n" "$tracked_matches" "$untracked_matches" | sed '/^$/d' | sort -u)

if [ -z "$all_matches" ]; then
  echo "No likely secrets found in repository (tracked or untracked files)."
  exit 0
fi

echo "Potential secret-like matches (values redacted):"
printf "%s\n" "$all_matches" | while IFS= read -r line; do
  # line format: path:lineno:content
  path="$(printf "%s" "$line" | cut -d: -f1)"
  lineno="$(printf "%s" "$line" | cut -d: -f2)"
  content="$(printf "%s" "$line" | cut -d: -f3-)"

  # Ignore obvious examples/placeholders
  if printf "%s" "$path" | grep -qiE '\.example$'; then
    continue
  fi
  if printf "%s" "$content" | grep -qiE 'REPLACE_ME|<REDACTED>|EXAMPLE'; then
    continue
  fi

  redacted=$(printf "%s" "$content" | redact_stream)
  printf "%s:%s:%s\n" "$path" "$lineno" "$redacted"
done

# Exit with success (0) so this tool is safe to run in CI; human must inspect output.
exit 0
