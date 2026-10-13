"""Pre-data expectations transcribed from the hypothesis sheet (data/DM1 Hackathon_ Pre-Data Mechanistic Hypothesis Sheet.html, sections 2-5), fixed BEFORE looking at any result.
PRIOR[arm][feature] = (strength, expected sign on IMPROVEMENT of a higher covariate value / presence of the dummy level: +1 better, -1 worse, 0 = open / not specified).
strength: strong / moderate / weak / expected_noise / unspecified. PLAUSIBLE_NOISE = the sheet's 'plausible-looking noise the organizers may have planted' per arm."""
PRIOR = {
 "Mexiletine": {"myotonia_severity": ("strong", +1), "smoking_status_Current": ("moderate", -1), "smoking_status_Former": ("weak", 0), "phenotype_adult_onset": ("moderate", +1), "phenotype_juvenile_onset": ("weak", 0),
                "bmi": ("weak", -1), "muscle_strength": ("weak", +1), "pr_interval": ("weak", -1), "cognitive_function": ("weak", +1), "sex_Male": ("weak", 0), "albumin": ("weak", 0),
                "log_ctg": ("expected_noise", 0), "somatic_mosaicism_index": ("expected_noise", 0), "age_at_onset": ("expected_noise", 0), "disease_duration": ("expected_noise", 0), "insulin_resistance": ("expected_noise", 0),
                "ck_level": ("expected_noise", 0), "cataracts_Yes": ("expected_noise", 0), "family_history_Yes": ("expected_noise", 0), "family_history_Unknown": ("expected_noise", 0)},
 "Oligonucleotide": {"log_ctg": ("strong", 0), "somatic_mosaicism_index": ("strong", 0), "muscle_strength": ("strong", 0), "disease_duration": ("moderate", -1), "age_at_onset": ("moderate", 0),
                     "phenotype_adult_onset": ("moderate", 0), "phenotype_juvenile_onset": ("moderate", 0), "ck_level": ("weak", 0), "albumin": ("weak", +1), "bmi": ("weak", -1), "insulin_resistance": ("weak", 0),
                     "myotonia_severity": ("unspecified", 0), "pr_interval": ("expected_noise", 0), "cognitive_function": ("expected_noise", 0), "cataracts_Yes": ("expected_noise", 0), "family_history_Yes": ("expected_noise", 0),
                     "family_history_Unknown": ("expected_noise", 0), "smoking_status_Former": ("expected_noise", 0), "smoking_status_Current": ("expected_noise", 0), "sex_Male": ("expected_noise", 0)},
 "Tideglusib": {"cognitive_function": ("strong", -1), "muscle_strength": ("strong", -1), "insulin_resistance": ("moderate", +1), "phenotype_juvenile_onset": ("moderate", +1), "phenotype_adult_onset": ("moderate", 0),
                "log_ctg": ("moderate", +1), "somatic_mosaicism_index": ("moderate", +1), "bmi": ("weak", 0), "albumin": ("weak", 0), "pr_interval": ("weak", 0), "smoking_status_Former": ("weak", 0), "smoking_status_Current": ("weak", 0),
                "age_at_onset": ("unspecified", 0), "disease_duration": ("unspecified", 0), "myotonia_severity": ("unspecified", 0), "ck_level": ("expected_noise", 0), "cataracts_Yes": ("expected_noise", 0),
                "family_history_Yes": ("expected_noise", 0), "family_history_Unknown": ("expected_noise", 0), "sex_Male": ("expected_noise", 0)}}
PLAUSIBLE_NOISE = {"Mexiletine": ["log_ctg", "insulin_resistance", "pr_interval", "cataracts_Yes"], "Oligonucleotide": ["pr_interval", "cognitive_function", "cataracts_Yes", "insulin_resistance"],
                   "Tideglusib": ["pr_interval", "ck_level", "smoking_status_Current", "smoking_status_Former"]}
WHY_PLAUSIBLE = {"log_ctg": "CTG expansion size sets toxic-RNA burden and onset age", "somatic_mosaicism_index": "somatic repeat instability is a proxy of muscle repeat burden", "age_at_onset": "earlier onset marks more severe disease",
 "disease_duration": "longer disease means more irreversible tissue damage", "myotonia_severity": "CLCN1 mis-splicing readout and baseline of the myotonia endpoint", "muscle_strength": "baseline of the motor endpoint (reversible reserve vs atrophy)",
 "pr_interval": "SCN5A cardiac-conduction readout (a safety covariate, not an efficacy path)", "cognitive_function": "CNS MBNL-loss readout and adherence proxy for oral regimens", "ck_level": "marker of ongoing myofiber turnover",
 "insulin_resistance": "INSR exon-11 mis-splicing readout and GSK3b-Akt axis", "albumin": "protein binding / PK modifier", "bmi": "adiposity changes mg/kg exposure and couples to insulin resistance",
 "sex_Male": "sex-specific weakness and cardiac norms", "family_history_Yes": "autosomal dominant inheritance makes a positive history near universal", "family_history_Unknown": "autosomal dominant inheritance",
 "cataracts_Yes": "posterior subcapsular cataract is a classic DM1 marker", "smoking_status_Current": "CYP1A2 induction (mexiletine PK)", "smoking_status_Former": "CYP1A2 induction (mexiletine PK)",
 "phenotype_adult_onset": "phenotype bins repeat size and onset", "phenotype_juvenile_onset": "juvenile onset carries larger repeats and more CNS involvement"}
STRENGTH_SCORE = {"strong": 3, "moderate": 2, "weak": 1, "unspecified": 0, "expected_noise": 0}
