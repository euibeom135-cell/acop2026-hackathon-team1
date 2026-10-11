# Literature to back the clinical claims

Nine papers, chosen to support one claim each. Found by web search on 11 October 2026 and checked against the publisher or PubMed page; details marked "check" were not visible in the abstract and should be confirmed in the full text before they go on a slide.

## Disease and covariates

| # | Reference | What it backs on our slides |
|---|---|---|
| 1 | Morales F, et al. Somatic instability of the expanded CTG triplet repeat in myotonic dystrophy type 1 is a heritable quantitative trait and modifier of disease severity. *Hum Mol Genet* 2012;21:3558–67. [doi:10.1093/hmg/dds185](https://doi.org/10.1093/hmg/dds185) | CTG repeat length is the main driver of age at onset and severity; somatic expansion rate modifies it. Supports `ctg_repeats` and `somatic_mosaicism_index` as the "cause" layer, and their correlation |
| 2 | Cumming SA, et al. Genetic determinants of disease severity in the myotonic dystrophy type 1 OPTIMISTIC cohort. *Neurology* 2019;93:e995–e1009. [PubMed](https://pubmed.ncbi.nlm.nih.gov/31395669/) | Severity driven by progenitor allele length, modified by age and sex. Supports the CTG, age and onset cluster we see |
| 3 | De Antonio M, et al. Unravelling the myotonic dystrophy type 1 clinical spectrum: a systematic registry-based study with implications for disease classification. *Rev Neurol (Paris)* 2016;172:572–80. [doi:10.1016/j.neurol.2016.08.003](https://doi.org/10.1016/j.neurol.2016.08.003) | The onset-form classification (congenital, infantile, juvenile, adult, late) is a continuum tied to repeat size; justifies `phenotype` as a population-group variable and stratified splitting on it |
| 4 | Okkersen K, et al. Brain imaging in myotonic dystrophy type 1: a systematic review. *Neurology* 2017;89:960–9. [doi:10.1212/WNL.0000000000004300](https://doi.org/10.1212/WNL.0000000000004300) | DM1 is a brain disease as well as a muscle disease; cognitive involvement is a real, measurable domain. Supports treating `cognitive_function` as organ damage rather than noise |

## The three drugs

| # | Reference | What it backs |
|---|---|---|
| 5 | Heatwole C, et al. Mexiletine in myotonic dystrophy type 1: a randomized, double-blind, placebo-controlled trial. *Neurology* 2021;96:e228–e240 (online 2020). [NCT01406873](https://clinicaltrials.gov/study/NCT01406873) | Mexiletine improved measured grip myotonia but not 6-minute walk at 6 months. Supports "symptomatic drug: the effect is on the symptom it targets", and the organizers' own hint |
| 6 | Logigian EL, et al. Mexiletine is an effective antimyotonia treatment in myotonic dystrophy type 1. *Neurology* 2010;74:1441–8. [PMC2871004](https://pmc.ncbi.nlm.nih.gov/articles/PMC2871004) | Two crossover trials: mexiletine shortens grip relaxation time. Supports a baseline-myotonia-dependent effect (patients were enrolled for having myotonia) |
| 7 | Thornton CA, et al. Antisense oligonucleotide targeting DMPK in patients with myotonic dystrophy type 1: a multicentre, randomised, dose-escalation, placebo-controlled, phase 1/2a trial. *Lancet Neurol* 2023;22:218–28. [PubMed 36804094](https://pubmed.ncbi.nlm.nih.gov/36804094/) | The antisense mechanism (degrade DMPK RNA) and the clinical reality: safe, but target knockdown in muscle was limited and efficacy modest. Supports "direction knowable, individual response weak" for the oligonucleotide arm |
| 8 | Jones K, et al. GSK3β mediates muscle pathology in myotonic dystrophy. *J Clin Invest* 2012;122:4461–72. [doi:10.1172/JCI64081](https://doi.org/10.1172/JCI64081) | CUG repeats raise GSK3β, which suppresses CELF1/CUGBP1 signalling; GSK3 inhibition restores muscle function in the mouse. Supports the tideglusib mechanism slide |
| 9 | Horrigan J, et al. A phase 2 study of AMO-02 (tideglusib) in congenital and childhood-onset myotonic dystrophy type 1. *Pediatr Neurol* 2020;112:84–93. [doi:10.1016/j.pediatrneurol.2020.08.001](https://doi.org/10.1016/j.pediatrneurol.2020.08.001) | 16 patients, 12 weeks, 400 vs 1000 mg; improvements reported in cognition, fatigue and daily function, more at the higher dose. Supports a cognitive component to tideglusib response (check: no placebo arm; small) |

## Method (one reference, for the Q&A)

| # | Reference | What it backs |
|---|---|---|
| 10 | Hutmacher MM, Kowalski KG. Covariate selection in pharmacometric analyses: a review of methods. *Br J Clin Pharmacol* 2015;79:132–47. [doi:10.1111/bcp.12451](https://doi.org/10.1111/bcp.12451) | Stepwise selection is familiar but unstable with correlated covariates; penalised and full-model approaches are preferred for predictive performance. Supports running several selection methods and reporting their agreement, and the forest-plot presentation of covariate effects against a reference patient |

## How the literature is used

- One citation per claim, on the slide where the claim is made, in small type.
- The mechanism chain (repeat, toxic RNA, GSK3β/CELF1 and MBNL1 mis-splicing, organ damage, symptom) is drawn from 1, 2, 7 and 8.
- The "measure the organ the drug acts on" conclusion is ours; the literature backs the mechanism of each drug, not the stratification rule, which comes from the simulated data.
