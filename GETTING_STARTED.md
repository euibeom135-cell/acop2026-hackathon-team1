# Getting started (5 minutes)

Everyone on the team has **write access**: you can add, change and upload files directly. Nobody needs approval to share work.

## 1. Accept the invite

Open the invitation email from GitHub, or go to https://github.com/euibeom135-cell/acop2026-hackathon-team1 while signed in, and click **Accept**.

## 2. Get the files

Pick one.

**A. GitHub Desktop (easiest if you don't use git)**
1. Install [GitHub Desktop](https://desktop.github.com) and sign in.
2. File, then Clone repository, then choose `acop2026-hackathon-team1`.

**B. Command line**
```bash
git clone https://github.com/euibeom135-cell/acop2026-hackathon-team1.git
cd acop2026-hackathon-team1
```

**C. Just reading?** Browse on the website. PDFs in `slides/` open in the browser.

## 3. Add the dataset (on your machine only)

Download it from our SharePoint folder and save it into `analysis/data/`. Git ignores that folder, so it cannot be uploaded by accident.

## 4. Run the analysis

```bash
Rscript analysis/install_packages.R     # first time only
cd analysis && Rscript dm1_analysis.R   # about a minute
```

Your results appear in `analysis/dm1_outputs/`. That folder is personal and is not uploaded. The team's official results are in `results/`.

## 5. Try your own idea

Copy `analysis/explorations/_template.R` into your folder (`analysis/explorations/<your name>/`) and edit it. You get training patients only; the test set stays locked so our final numbers are honest.

If you use Codex or Claude Code, start it inside the repository folder. It reads the project rules from `AGENTS.md` / `CLAUDE.md` automatically.

## 6. Share your work

**GitHub Desktop:** write a short summary, click **Commit to main**, then **Push origin**. If it says there are new changes, click **Pull origin** first.

**Command line:** one command does pull, save and upload:
```bash
bash sync.sh "what I changed"
```

**Website:** open the folder, then **Add file**, then **Upload files**.

## Who edits what

| Files | Who |
|---|---|
| Your folder under `analysis/explorations/` | You, freely |
| `slides/` (deck drafts, figures) | Anyone; say in the chat when you're editing the deck so two people don't overwrite each other |
| `DECISIONS.md`, `AI_DISCLOSURE.md` | Anyone; add rows, don't delete others' |
| `analysis/dm1_analysis.R`, `analysis/R/common.R`, `results/` | Agree in the chat first. Everyone's numbers come from these |

Because each person works mainly in their own folder, changes rarely collide.

## If something goes wrong

| Problem | Fix |
|---|---|
| "Updates were rejected" or push fails | Someone uploaded before you. Pull first (`git pull --rebase`, or **Pull origin**), then push again. `sync.sh` does this for you |
| "Merge conflict" | Two people changed the same lines. Ask in the chat before resolving; or keep your version in your own folder and re-pull |
| Script cannot find the dataset | The file must be in `analysis/data/` and have `DM1` in its name |
| A package fails to install | Send the error to the chat; the rest of the team can still run it |
| Uploaded something by mistake | Tell the chat. It can be undone |
