#!/usr/bin/env bash
#
# Release eurocodepy: tag the version in pyproject.toml, push, create the GitHub
# release and upload the build to PyPI. Bump the version in pyproject.toml and
# commit it before running this.
#
# Usage:
#   tools/publish_release.sh [--skip-tests] [--dry-run]
#
#   --skip-tests  do not run pytest before releasing.
#   --dry-run     build and check everything, but push/release/upload nothing.
#
# Requirements: git, gh (authenticated), uv, and a PyPI token in
# UV_PUBLISH_TOKEN (create one at https://pypi.org/manage/account/token/).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # this script lives in tools/
cd "$ROOT"

RUN_TESTS=1
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --skip-tests) RUN_TESTS=0 ;;
    --dry-run)    DRY_RUN=1 ;;
    -h|--help)    sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)           echo "ERROR: unknown option $arg" >&2; exit 1 ;;
    *)            echo "ERROR: unexpected argument $arg" >&2; exit 1 ;;
  esac
done

die() { echo "ERROR: $*" >&2; exit 1; }
read_version() { grep -m1 -E '^version[[:space:]]*=' pyproject.toml | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/'; }

for tool in git gh uv; do
  command -v "$tool" >/dev/null || die "$tool not found in PATH"
done
gh auth status >/dev/null 2>&1 || die "gh is not authenticated (run: gh auth login)"
if [[ $DRY_RUN -eq 0 && -z "${UV_PUBLISH_TOKEN:-}" ]]; then
  die "UV_PUBLISH_TOKEN is not set (PyPI API token)"
fi

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || die "detached HEAD; check out a branch first"
[[ -z "$(git status --porcelain)" ]] || die "working tree is not clean; commit or stash first"
git fetch -q origin
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse "origin/${BRANCH}" 2>/dev/null || echo none)" ]]; then
  git merge-base --is-ancestor "origin/${BRANCH}" HEAD \
    || die "origin/${BRANCH} has commits you do not have; pull first"
fi

CURRENT="$(read_version)"
[[ -n "$CURRENT" ]] || die "could not read the version from pyproject.toml"
VERSION="$CURRENT"
[[ "$VERSION" =~ ^[0-9]+(\.[0-9]+)*([abc]|rc|\.post|\.dev)?[0-9]*$ ]] || die "invalid version: $VERSION"
TAG="v${VERSION}"

git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null && die "tag ${TAG} already exists locally"
git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1 && die "tag ${TAG} already exists on origin"

if [[ $RUN_TESTS -eq 1 ]]; then
  echo "Running tests…"
  uv run --extra test pytest -q
fi

# Build from a scratch dir so stale artifacts in dist/ are never uploaded.
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

echo "Building ${VERSION}…"
uv build --out-dir "$BUILD_DIR" >/dev/null
ls "$BUILD_DIR"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Dry run: build OK, nothing pushed or uploaded."
  exit 0
fi

git tag -a "$TAG" -m "eurocodepy ${VERSION}"
git push origin "$BRANCH"
git push origin "$TAG"

gh release create "$TAG" "$BUILD_DIR"/* --title "eurocodepy ${VERSION}" --generate-notes

echo "Uploading to PyPI…"
if ! uv publish "$BUILD_DIR"/*; then
  echo "ERROR: the GitHub release ${TAG} exists but the PyPI upload failed." >&2
  echo "Retry with: uv build && uv publish   " >&2
  exit 1
fi

echo "Done: ${TAG} released on GitHub and PyPI."
