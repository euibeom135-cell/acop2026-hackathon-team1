#!/bin/bash
# Save your changes, get everyone else's, and upload. Usage: bash sync.sh "what I changed"
set -e
cd "$(dirname "$0")"
if git ls-files --error-unmatch analysis/data/ 2>/dev/null | grep -qvE 'README\.md$'; then
  echo "A data file is being tracked in analysis/data/. Stop and tell the team before uploading."; exit 1
fi
git add -A
if git diff --cached --quiet; then echo "Nothing new to save."; else git commit -q -m "${1:-Update}"; echo "Saved: ${1:-Update}"; fi
git pull --rebase -q && echo "Got the team's latest changes."
git push -q && echo "Uploaded. Everyone can now see your work."
