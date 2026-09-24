#!/usr/bin/env bash
# Read-only scan of one repo's change for signs that tests were weakened.
# Heuristic: every hit needs a human look; a clean run is not proof.
#
# Usage: scan-test-weakening.sh <repo-dir> [base-ref]
#   base-ref defaults to origin/main. The diff covers commits after base-ref plus
#   uncommitted edits; untracked test files are listed and scanned too.
# Exit: 0 = no hits, 1 = hits to review, 2 = usage error.
set -uo pipefail

repo="${1:?usage: scan-test-weakening.sh <repo-dir> [base-ref]}"
base="${2:-origin/main}"
cd "$repo" || exit 2
git rev-parse --verify -q "$base" >/dev/null || { echo "base ref '$base' not found in $repo" >&2; exit 2; }

tests=(':(glob)**/*.test.ts' ':(glob)**/*.test.tsx' ':(glob)**/*.spec.ts' ':(glob)**/e2e/**'
  ':(glob)**/tests/**' ':(glob)**/test_*.py' ':(glob)**/*.snap' ':(glob)**/__snapshots__/**'
  ':(glob)**/*-snapshots/**' ':(glob)**/src/test/**')
configs=(':(glob)**/vitest.config.ts' ':(glob)**/playwright.config.ts' ':(glob)**/biome.json'
  ':(glob)**/tsconfig*.json' ':(glob)**/pyproject.toml' ':(glob)**/.github/workflows/*.yml'
  ':(glob)**/package.json')

hits=0
section() { printf '\n== %s\n' "$1"; }
report() { if [ -n "$1" ]; then printf '%s\n' "$1"; hits=1; else echo "none"; fi; }

section "Deleted or renamed test files"
report "$(git diff --name-status -M --diff-filter=DR "$base" -- "${tests[@]}")"

section "Skips, focus, mocks, sleeps and ignores added in tests"
weak='\.(skip|only|todo|fixme|fails|fail)\(|\bx(it|describe|test)\(|pytest\.mark\.(skip|xfail)|vi\.mock\(|vi\.spyOn\(|mockImplementation|mockResolvedValue|waitForTimeout|test\.slow\(|@ts-(ignore|expect-error|nocheck)|biome-ignore|noqa|expect\.anything\(|expect\.any\(|\.toBeTruthy\(\)|\.toBeDefined\(\)|expect\.soft\(|toMatchSnapshot|toHaveScreenshot|retries'
report "$(git diff -U0 "$base" -- "${tests[@]}" | grep -E '^\+[^+]' | grep -En "$weak")"

section "Assertion lines removed vs added in tests"
removed=$(git diff -U0 "$base" -- "${tests[@]}" | grep -E '^-[^-]' | grep -cE 'expect\(|assert |toThrow|toEqual|toBe\(|rejects\.')
added=$(git diff -U0 "$base" -- "${tests[@]}" | grep -E '^\+[^+]' | grep -cE 'expect\(|assert |toThrow|toEqual|toBe\(|rejects\.')
echo "removed=$removed added=$added"
if [ "$removed" -gt 0 ]; then
  echo "Read every removed assertion below and say where its behavior is still checked:"
  git diff -U0 "$base" -- "${tests[@]}" | grep -E '^(\+\+\+|-[^-])' | grep -E '^\+\+\+|expect\(|assert |toThrow|toEqual|toBe\(|rejects\.'
  hits=1
fi

section "Snapshot and screenshot baselines changed"
report "$(git diff --name-only "$base" -- ':(glob)**/*.snap' ':(glob)**/__snapshots__/**' ':(glob)**/*-snapshots/**')"

section "Test, lint or CI config loosened"
cfg='exclude|testIgnore|include|retries|passWithNoTests|continue-on-error|if-present|--no-verify|"off"|"warn"|strict|skipLibCheck|testTimeout|coverage'
report "$(git diff -U0 "$base" -- "${configs[@]}" | grep -E '^(\+\+\+|[-+][^-+])' | grep -E "^\+\+\+|$cfg" | grep -B1 -E '^[-+][^-+]')"

section "Test-only branches added to production code"
special='NODE_ENV[^\n]*test|isTest|VITEST|PLAYWRIGHT|E2E_|process\.env\.CI|__TEST__|pytest|if .*mock'
report "$(git diff -U0 "$base" -- . ':(exclude,glob)**/*.test.ts' ':(exclude,glob)**/*.spec.ts' ':(exclude,glob)**/e2e/**' ':(exclude,glob)**/tests/**' ':(exclude,glob)**/src/test/**' | grep -E '^(\+\+\+|\+[^+])' | grep -E "^\+\+\+|$special" | grep -B1 -E '^\+[^+]')"

section "Untracked test files (not in git diff; scanned in full)"
untracked=$(git ls-files --others --exclude-standard -- "${tests[@]}")
if [ -n "$untracked" ]; then
  echo "$untracked"
  while IFS= read -r f; do grep -EnH "$weak" "$f"; done <<<"$untracked"
  hits=1
else
  echo "none"
fi

printf '\nResult: %s\n' "$([ "$hits" = 1 ] && echo 'hits to review (not automatically blocking)' || echo 'no hits')"
exit "$hits"
