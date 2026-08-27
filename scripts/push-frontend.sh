#!/usr/bin/env bash
set -euo pipefail

branch_name="split-frontend-$(date +%Y%m%d%H%M%S)"
git subtree split --prefix=frontend -b "$branch_name"
git push project "$branch_name:frontend"
git branch -D "$branch_name"
