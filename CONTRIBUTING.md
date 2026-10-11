# How to share changes

## Never upload

- **The dataset.** It was shared with participants through SharePoint. Keep it in `analysis/data/` on your own machine; the repository ignores everything in that folder.
- Licensed third-party material. (The organizers' kickoff deck is in `slides/` only while this repository is private.)

## Sharing changes

Everyone has write access. See [`GETTING_STARTED.md`](GETTING_STARTED.md) for the three ways to share (GitHub Desktop, `bash sync.sh "message"`, or uploading on the website) and what to do if a push fails.

## Conventions

- Try ideas in your own folder under `analysis/explorations/`. They see training patients only.
- One main script: `analysis/dm1_analysis.R`, and one shared foundation: `analysis/R/common.R`. Change them only after the team agrees; don't fork copies.
- If you work with Codex or Claude Code, start it inside this repository so it reads `AGENTS.md`.
- Any change to the split, methods, thresholds or cleaning rules gets a row in `DECISIONS.md`.
- Do not change the random seed or re-split after looking at test-set results.
- If you use an AI tool, add it to `AI_DISCLOSURE.md`.
- Slides and drafts go in `slides/`.
