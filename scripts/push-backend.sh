#!/usr/bin/env bash
set -euo pipefail

branch_name="split-backend-$(date +%Y%m%d%H%M%S)"
git subtree split --prefix=backend -b "$branch_name"
git push project "$branch_name:backend"
git branch -D "$branch_name"
