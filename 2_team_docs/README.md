# Team documents

Two summaries of the kickoff, written for the team. Both open in the browser when clicked.

| Document | Length | Read it when |
|---|---|---|
| [`Team1_hackathon_brief.pdf`](Team1_hackathon_brief.pdf) | 3 pages | You want the whole picture in five minutes: clinical background, approach, logistics |
| [`Team1_hackathon_detailed_guide.pdf`](Team1_hackathon_detailed_guide.pdf) | 10 pages | You want the reasoning: disease mechanism step by step, each drug, every dataset column, each analysis step and method in plain words, how to read the metrics, pitfalls and likely judge questions, glossary |

The original 90-slide deck is in [`../1_kickoff/`](../1_kickoff/), with an index of which slides cover what.

---

## The brief, in short

**The question.** Can machine learning identify additional predictors and improve patient stratification beyond traditional covariate modelling?

**The task.** For each of three DM1 treatment arms, find which baseline characteristics drive response, separate real predictors from planted noise, compare covariate models with ML models, and explain the findings clinically.

### Clinical background

DM1 as one chain:

1. **A stutter in one gene.** The *DMPK* gene has the letters CTG repeated. Normal is up to about 37 repeats; DM1 is 50 to several thousand.
2. **Sticky RNA.** The RNA copy of the long repeat clumps in the cell nucleus.
3. **A trapped editor.** The clump traps a protein (MBNL) that edits other RNA messages (splicing).
4. **Faulty proteins.** Many proteins are made in the wrong version.
5. **Many organs affected:** muscle (stiffness and weakness, which are separate problems), heart, brain, metabolism, eye, breathing and gut.

Why patients differ: more repeats generally means earlier and worse disease, but the count is a rough guide because repeats keep growing at different rates in different tissues (somatic mosaicism), and the mix of affected organs varies.

| Arm | Where it acts | Outcome | Better is | Organizers' hint |
|---|---|---|---|---|
| **Mexiletine** | The symptom: calms over-excitable muscle | Change in myotonia severity, week 12 | Lower | Clinical presentation may matter |
| **Oligonucleotide** | The root: destroys the toxic RNA | Change in muscle strength (QMT), week 26 | Higher | Molecular and clinical burden may both matter |
| **Tideglusib** | Mid-chain: blocks an overactive enzyme in several tissues | Combined cognitive + motor score, 0 to 20, week 26 | Higher | Features from more than one domain may contribute |

### The data

- 500 simulated patients, one row each, about 167 per arm. No doses, concentrations or repeat visits.
- 18 baseline covariates (13 numeric, 5 categorical). **Some are deliberate noise.**
- Each arm has a continuous outcome and a responder label derived from it.
- No missing values, but the data needs cleaning.

### Approach

1. Explore and clean (rules decided from baseline columns only, never from the outcome).
2. Split per arm, stratified, fixed seed. Lock the test set.
3. Preprocess using the training set only.
4. Covariate models: stepwise, LASSO, elastic net.
5. ML models: random forest, XGBoost (untuned and tuned on a small grid).
6. Evaluate once on the test set. Continuous: RMSE, MAE, R². Label: ROC-AUC, recall, precision.
7. Compare which covariates each method picked; agreement builds confidence.
8. Separate signal from noise; interpret against each drug's mechanism; propose how to stratify patients.

Limit to state: there is no placebo arm, so predictors show who does well on a drug, not that the drug caused it.

### Logistics

| When | What |
|---|---|
| Tue 13 Oct, 8:00 to 9:00 AM | Office hour, Magnolia 1 |
| **Tue 13 Oct, 11:59 PM ET** | **Slides and all code in the Team 1 SharePoint folder**; one representative emails the chairs |
| Wed 14 Oct, 9:00 to 10:30 AM | 5-minute talk + 3-minute Q&A (one judge question) |
| Wed 14 Oct, 4:30 PM | Winners announced |

Scoring: Clinical 10, Technical 10, Communication 10. "Meaningful covariate identification matters more than fancy models." AI tools are allowed with disclosure of which tools and for what.

*Prepared with Claude (Anthropic) from the kickoff deck and session notes. The approach section is a suggestion for the team to agree.*
