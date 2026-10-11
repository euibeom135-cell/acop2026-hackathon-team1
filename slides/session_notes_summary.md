# Kickoff session notes: what was said beyond the slides

Summary of the organizers' spoken remarks at the kickoff, 11 October 2026, taken from a live speech-to-text transcript. The transcript had errors (drug names, numbers), which are corrected here against the slide deck. Team side-conversations are not included. Where a remark is a hint about the dataset, it is marked **Hint**.

## Logistics and rules

- The dataset is an Excel spreadsheet, released through the team SharePoint folder at the end of the kickoff session, with a data dictionary.
- **The dataset has no missing values but does need cleaning.**
- Any platform, language or software. AI tools, including chatbots and agents, are welcome. Requirements: note in the **code annotations** which AI tool or agent was used and for what; state it in the final presentation; understand every step; the team remains accountable.
- Slides are due by the end of Tuesday because the organizers merge all teams' decks into one presentation. Teams do not present from their own laptops.
- Judges want the code files submitted as well, because it is hard to judge on the presentation alone. They may not run them.
- Each team should nominate one representative to communicate with the organizers and to email them when the final slides are uploaded.
- Final presentation: five minutes per team, then three minutes of Q&A. The session is 1.5 hours for ten teams, so time is tight: "try to create a really good message". At least one team member must present; more may join.
- Office hours are in Magnolia 1, on the far side of the hotel. The slides list Tuesday 8:00 to 9:00 AM; the speaker mentioned morning times on the next two days, so check with the organizers whether there is also a Monday slot.
- Winners and any honourable mentions are announced at the closing session, Wednesday 4:30 to 5:00 PM.

## What judges look for

- **Clinical:** did you find meaningful covariates, or did you select noise? Do you propose some kind of stratification based on the findings? "Not only the model with some results, but how you're going to use it for clinical interpretation."
- **Technical:** the workflow and the metrics. Analyse the data first, decide which methods suit it, and justify the assessment.
- **Communication:** "it's difficult to do in five minutes, so it's also a challenge"; a full story with visuals.
- Repeated emphasis: meaningful covariate identification matters more than fancy models. Although the data is simulated, it is "based on current knowledge about the disease", and the organizers hope for real insight.

## Disease background

- DM1 was chosen because it is "clinically a very difficult disease to work with": a rare, multi-organ, genetic disease with very different manifestations between patients.
- Prevalence is 16.7 per 100,000, about 1 in 6,000. Some regions are hotspots through a founder effect, notably the Saguenay area of Quebec.
- Autosomal dominant: one copy from one parent is enough. Severity can differ between affected siblings.
- More CTG repeats generally means earlier onset and more severe disease, "but it's not always happening this way".
- **Hint:** the dataset includes the onset category (`phenotype`) as a column to analyse.
- **Hint:** dataset features map to the organ systems shown on the slides, for example cataracts as yes/no, insulin resistance, and separate measures of muscle weakness and myotonia.
- "When we treat the muscle function itself, it doesn't mean we will improve other problems for this particular patient."
- Closing remark on this section: the team should "understand the nature of the disease and interpret the different categories", naming disease severity, CTG repeats and age.

## The three treatments

| Arm | What was said | Outcome and direction |
|---|---|---|
| **Mexiletine** | Sodium channel blocker. "Turning down the volume of an over-excited muscle." Treats the symptom, not the genetic mechanism | Change in myotonia severity at 12 weeks. **Negative is improvement. "Please remember this direction because the other two arms are on the opposite side."** |
| **Oligonucleotide** | Antisense strand that sticks to the *DMPK* RNA, lowers the toxic RNA and frees the trapped MBNL1 protein, restoring splicing. "Works at the root of the disease, theoretically" | Change in QMT (a muscle strength score) at 26 weeks. Positive is improvement. vHOT is the common trial endpoint but was not used because of its high variability |
| **Tideglusib** | Blocks GSK3-beta, which is overactive in DM1, affecting Wnt/beta-catenin signalling and the control of protein synthesis and RNA-binding proteins. Fits the multisystem nature of the disease | Combined cognitive and motor improvement score, 0 to 20, at 26 weeks. Higher is better |

- **Hint (mexiletine):** the drug acts on muscle excitability, "so the clinical presentation might matter". Relief of myotonia did not improve six-minute walk distance in a six-month placebo-controlled trial.
- **Hint (oligonucleotide):** "both the molecular-level evidence and the clinical evidence might matter", but "not every disease marker" is informative.
- **Hint (tideglusib):** features from more than one domain may contribute.

## Workflow

- The training set is "practice problems"; the test set is "the final exam".
- Preprocessing means any cleaning or transformation the chosen method needs, such as scaling or encoding categories.
- **Leakage** is test-set information sneaking into training. Three moves: split first, fit on the training set only, then apply to the test set.
- **Hint:** each arm has roughly 160 to 170 patients. "This is not a really big dataset, so discuss how you want to deal with that."
- Ask whether covariates are correlated or interact, and choose methods that can handle it.
- Continuous or binary outcome is the team's choice; both is also fine. Metrics must match the outcome.
- Example of a biased split: a training set that is all adult onset with juvenile-onset patients only in the test set "wouldn't work".
- The workflow is a recommendation; the slides highlight "popular places for mistakes".
- Submission checklist as spoken: slides tell one story (workflow, key covariates, interpretation, conclusion); code is complete and reproduces results; the split, the handling of noise covariates and the metrics are explained and justified; key covariates are identified per arm, and each arm may have a different set; AI use is reported.

## Covariate methods

- Methods trade interpretability against flexibility. Simple ones may oversimplify but are easy to interpret clinically, "which is our task: we want to inform patient stratification". Others may fit everything but be hard to interpret in the clinic.
- **Hint:** linear regression, "despite being a pretty simple model, in many cases actually outperforms the more fancy methods. We still recommend you try this."
- Stepwise selection is unstable: with correlated covariates, the order of adding and removing decides which one stays, and the dropped one may be the more meaningful. "Do not see the result of stepwise selection as the truth."
- Best subset: R² is a poor criterion because it never penalises adding covariates. Use one that does, such as BIC. "The parsimony principle is always there."
- LASSO, ridge and elastic net work for continuous and binary outcomes by changing the family setting. They need cross-validation; choosing the penalty is tricky.
- Polynomials can swing wildly at the edges of the data. Splines and GAMs are flexible but overfit easily if given too many knots.
- PCA reduces correlated covariates to components, but a component is hard to explain or to use for stratifying patients: "always trade-offs". For categorical or mixed data there are MCA and FAMD.
- Free textbook recommended: *An Introduction to Statistical Learning*, with R and Python examples.

## Machine-learning methods

- K-nearest neighbours: intuitive for clinicians ("patients like you"), but noise covariates dilute similarity and it is "really sensitive" to this.
- XGBoost: small trees built in sequence, each correcting the last; often strong on tabular clinical data and handles interactions. Many settings, and it overfits quickly on a small dataset.
- Neural network: use a deliberately tiny one if at all. It can learn interactions without being told, but it is the least transparent and hard to interpret with a small sample.
- Tuning: every model has settings; grid search tries combinations and keeps the best.
- Covariate-method examples in the deck are in R; ML examples are in Python (scikit-learn).

## Takeaways for our approach

1. Keep models simple; expect plain regression to be competitive.
2. Treat noise handling as a headline item, not a footnote.
3. Report results per arm, and expect each arm to have a different set of key covariates.
4. State the outcome direction on every result: mexiletine lower, the other two higher.
5. Tie each selected covariate to its organ system and to the drug's mechanism.
6. End with a stratification proposal.
7. Disclose AI use in code comments and aloud in the talk.

*Compiled with Claude (Anthropic) from a live transcript. The session's later parts (permutation importance, SHAP, assessment metrics, Q&A) were not captured in the transcript; see slides 72 to 83 of the kickoff deck.*
