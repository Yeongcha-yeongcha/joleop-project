#!/usr/bin/env bash
set -euo pipefail

git fetch project backend
git subtree pull --prefix=backend project backend --squash
