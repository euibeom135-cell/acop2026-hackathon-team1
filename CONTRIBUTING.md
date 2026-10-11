# How to share changes

## Never upload

- **The dataset.** It was shared with participants through SharePoint. Keep it in `3_analysis/data/` on your own machine; the repository ignores everything in that folder.
- The organizers' kickoff deck, or any licensed third-party material.

## If you use git

```bash
git clone https://github.com/euibeom135-cell/acop2026-hackathon-team1.git
cd acop2026-hackathon-team1
# ...make your change...
git pull                      # get others' changes first
git add -A
git commit -m "Short description of what changed and why"
git push
```

For anything larger than a small fix to `dm1_analysis.R`, say so in the team chat first, since everyone's results come from that one script.

## If you don't use git

- **To get the files:** green **Code** button, then **Download ZIP**.
- **To add or replace a file:** open the folder on GitHub, then **Add file**, then **Upload files**.

## Conventions

- One analysis script: `3_analysis/dm1_analysis.R`. Change it; don't fork copies.
- Any change to the split, methods, thresholds or cleaning rules gets a row in `DECISIONS.md`.
- Do not change the random seed or re-split after looking at test-set results.
- If you use an AI tool, add it to `AI_DISCLOSURE.md`.
- Slides and drafts go in `4_slides/`.
