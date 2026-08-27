#!/usr/bin/env bash
set -euo pipefail

git fetch project frontend
git subtree pull --prefix=frontend project frontend --squash
