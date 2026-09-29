#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "${script_dir}/.." rev-parse --show-toplevel)"
if [[ -n "$(git -C "$repo_root" status --porcelain)" ]]; then
  echo "Refusing to deploy: commit or discard the working tree changes first." >&2
  exit 1
fi
release_sha="$(git -C "$repo_root" rev-parse HEAD)"
args=(--config "$script_dir/wrangler.toml" --keep-vars --var "RELEASE_SHA:${release_sha}")
if [[ "${1:-}" == "--dry-run" ]]; then
  args+=(--dry-run)
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi
npx wrangler deploy "${args[@]}"
