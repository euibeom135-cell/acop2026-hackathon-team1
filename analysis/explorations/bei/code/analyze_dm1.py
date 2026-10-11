#!/usr/bin/env python3
"""Reproducible, training-only exploratory covariate analysis for DM1 hackathon."""
from pathlib import Path
import argparse, hashlib, itertools, json, platform, shutil
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import sklearn
from sklearn.model_selection import train_test_split

SEED = 20261011
ARMS = ['Mexiletine', 'Oligonucleotide', 'Tideglusib']
NUMERIC = ['ctg_repeats','somatic_mosaicism_index','age','age_at_onset',
           'disease_duration','myotonia_severity','muscle_strength','pr_interval',
           'cognitive_function','ck_level','insulin_resistance','albumin','bmi']
CATEGORICAL = ['phenotype','sex','family_history','cataracts','smoking_status']
ENDPOINTS = {'Mexiletine':'myotonia_change_12wk','Oligonucleotide':'qmt_change_26wk',
             'Tideglusib':'tideglusib_composite'}
RESPONDER = {'Mexiletine':'responder_phenotype_mex','Oligonucleotide':'responder_phenotype_oligo',
             'Tideglusib':'responder_phenotype_tidge'}
SIGN = {'Mexiletine':-1,'Oligonucleotide':1,'Tideglusib':1}
LABELS = {'ctg_repeats':'CTG repeats','somatic_mosaicism_index':'Somatic mosaicism',
 'age':'Age (years)','age_at_onset':'Age at onset (years)','disease_duration':'Disease duration (years)',
 'myotonia_severity':'Myotonia severity (0–10)','muscle_strength':'Muscle strength (20–100)',
 'pr_interval':'PR interval (ms)','cognitive_function':'Cognitive function (z-score)',
 'ck_level':'CK (U/L)','insulin_resistance':'Insulin resistance (HOMA-IR)',
 'albumin':'Albumin (g/dL)','bmi':'BMI (kg/m²)','phenotype':'Phenotype','sex':'Sex',
 'family_history':'Family history','cataracts':'Cataracts','smoking_status':'Smoking status'}
SHORT = ['CTG','Mosaicism','Age','Onset age','Duration','Myotonia','Strength','PR','Cognition','CK','HOMA-IR','Albumin','BMI']
LEVELS = {'phenotype':['juvenile_onset','adult_onset','late_onset'], 'sex':['Female','Male'],
 'family_history':['No','Unknown','Yes'], 'cataracts':['No','Yes'], 'smoking_status':['Never','Former','Current']}

def bh(p):
    p = np.asarray(p, dtype=float)
    valid=np.isfinite(p); vals=p[valid]
    order=np.argsort(vals); ans=np.empty(len(vals)); q=np.full(len(p),np.nan)
    ans[order] = np.minimum(1, np.minimum.accumulate((vals[order]*len(vals)/np.arange(1,len(vals)+1))[::-1])[::-1])
    q[valid]=ans
    return q

def corr(x,y):
    if len(np.unique(x))<2 or len(np.unique(y))<2:
        return np.nan,np.nan,np.nan,np.nan
    s,ps=stats.spearmanr(x,y); r,pp=stats.pearsonr(x,y)
    return s,ps,r,pp

def rho_ci(x,y,rng,rep=2000):
    ix=rng.integers(0,len(x),(rep,len(x)))
    a=stats.rankdata(np.asarray(x)[ix],axis=1); b=stats.rankdata(np.asarray(y)[ix],axis=1)
    a-=a.mean(axis=1,keepdims=True); b-=b.mean(axis=1,keepdims=True)
    r=np.sum(a*b,axis=1)/np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
    return np.quantile(r[np.isfinite(r)],[.025,.975])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,default=Path('inputs/dm1_clinical_trial_dataset.csv'))
    ap.add_argument('--out',type=Path,default=Path('outputs/dm1_covariates_20261011'))
    args=ap.parse_args(); out=args.out; (out/'tables').mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(args.input)
    assert df.shape==(500,26) and df.patient_id.is_unique
    assert not df[NUMERIC+CATEGORICAL].isna().any().any()
    assert (df.age-df.age_at_onset==df.disease_duration).all()
    split=[]; summaries=[]; train_parts=[]
    for arm in ARMS:
        g=df[df.treatment_arm==arm].copy()
        assert g[ENDPOINTS[arm]].notna().all() and g[RESPONDER[arm]].notna().all()
        for other in ARMS:
            if other!=arm:
                assert g[ENDPOINTS[other]].isna().all() and g[RESPONDER[other]].isna().all()
        tr,te=train_test_split(g.index,test_size=.2,random_state=SEED,stratify=g[RESPONDER[arm]])
        for index in g.index:
            split.append({'patient_id':df.loc[index,'patient_id'],'treatment_arm':arm,
                          'partition':'Training' if index in tr else 'Test'})
        t=g.loc[tr].sort_values('patient_id').copy()
        t['improvement_score']=SIGN[arm]*t[ENDPOINTS[arm]]
        t['assigned_endpoint']=ENDPOINTS[arm]
        t['assigned_response']=t[RESPONDER[arm]]
        train_parts.append(t)
        summaries.append({'Arm':arm,'All_n':len(g),'Training_n':len(t),'Test_n':len(te),
                          'Training_responders':int(t.assigned_response.eq('Responder').sum()),
                          'Training_responder_rate':float(t.assigned_response.eq('Responder').mean()),
                          'Endpoint':ENDPOINTS[arm], 'Improvement_multiplier':SIGN[arm],
                          'Improvement_mean':float(t.improvement_score.mean()),
                          'Improvement_SD':float(t.improvement_score.std()),
                          'Improvement_median':float(t.improvement_score.median())})
    train=pd.concat(train_parts).reset_index(drop=True)
    partition=pd.DataFrame(split).sort_values('patient_id')
    assert len(train)==399 and len(partition)==500
    partition.to_csv(out/'tables/patient_partitions.csv',index=False)
    train.to_csv(out/'tables/training_data.csv',index=False)
    summary=pd.DataFrame(summaries)
    rng=np.random.default_rng(SEED)
    outcome=[]
    for arm in ARMS:
        g=train[train.treatment_arm==arm]; y=g.improvement_score
        for v in NUMERIC:
            rho,ps,r,pp=corr(g[v],y)
            lo,hi=rho_ci(g[v].values,y.values,rng) if np.isfinite(rho) else (np.nan,np.nan)
            outcome.append({'Arm':arm,'Covariate':v,'Type':'Numeric','N':len(g),
                            'Status':'Testable' if np.isfinite(rho) else 'Constant within arm',
                            'Effect_type':'Spearman rho','Spearman_rho_improvement':rho,
                            'Spearman_rho_original':SIGN[arm]*rho, 'CI95_low':lo,'CI95_high':hi,
                            'Pearson_r_improvement':r,'Pearson_p':pp,'Kruskal_H':None,
                            'Eta_squared_H':None,'P_primary':ps,'Groups':None})
        for v in CATEGORICAL:
            groups=[s.improvement_score.values for _,s in g.groupby(v,sort=True)]
            h,p=stats.kruskal(*groups); k=len(groups)
            eps=max(0,(h-k+1)/(len(g)-k))
            outcome.append({'Arm':arm,'Covariate':v,'Type':'Categorical','N':len(g),
                            'Status':'Testable',
                            'Effect_type':'Kruskal-Wallis eta squared (H)', 'Spearman_rho_improvement':None,
                            'Spearman_rho_original':None,'CI95_low':None,'CI95_high':None,
                            'Pearson_r_improvement':None,'Pearson_p':None,'Kruskal_H':h,
                            'Eta_squared_H':eps,'P_primary':p,'Groups':k})
    outcomes=pd.DataFrame(outcome)
    outcomes['Q_within_arm']=outcomes.groupby('Arm',sort=False).P_primary.transform(lambda x:bh(x))
    outcomes['Q_all_evaluable']=bh(outcomes.P_primary)
    outcomes['FDR_0_05']=outcomes.Q_within_arm<.05
    # Numeric baseline correlations: pooled training and three arm subsets.
    correlations=[]; matrices=[]; cohorts=[('Pooled training',train)]+[(a,train[train.treatment_arm==a]) for a in ARMS]
    for cohort,g in cohorts:
        sm=g[NUMERIC].corr(method='spearman'); pm=g[NUMERIC].corr(method='pearson')
        matrices.append({'cohort':cohort,'n':len(g),'spearman':json.loads(sm.to_json(orient='values')),
                         'pearson':json.loads(pm.to_json(orient='values'))})
        for x,y in itertools.combinations(NUMERIC,2):
            s,ps,r,pp=corr(g[x],g[y])
            correlations.append({'Cohort':cohort,'N':len(g),'Covariate_1':x,'Covariate_2':y,
                                 'Status':'Testable' if np.isfinite(s) else 'Constant within cohort',
                                 'Spearman_rho':s,'P_spearman':ps,'Pearson_r':r,'P_pearson':pp,
                                 'Abs_rho_ge_0_70':abs(s)>=.7})
    pairs=pd.DataFrame(correlations)
    pairs['Q_spearman_within_cohort']=pairs.groupby('Cohort',sort=False).P_spearman.transform(lambda x:bh(x))
    # Preserve nominal categorical variables without imposing arbitrary numeric order.
    mixed=[]
    for cohort,g in cohorts:
        for x,y in itertools.combinations(CATEGORICAL,2):
            tab=pd.crosstab(g[x],g[y]); chi,p,dof,expected=stats.chi2_contingency(tab,correction=False)
            v=np.sqrt(chi/(len(g)*min(tab.shape[0]-1,tab.shape[1]-1)))
            mixed.append({'Cohort':cohort,'N':len(g),'Covariate_1':x,'Covariate_2':y,
                          'Status':'Testable',
                          'Effect_type':"Cramer's V",'Effect':v,'P':p,'Groups':None,
                          'Minimum_expected_count':float(expected.min())})
        for x in CATEGORICAL:
            for y in NUMERIC:
                groups=[s[y].values for _,s in g.groupby(x,sort=True)]
                constant=g[y].nunique()<2
                h,p=stats.kruskal(*groups) if not constant else (np.nan,np.nan)
                k=len(groups)
                mixed.append({'Cohort':cohort,'N':len(g),'Covariate_1':x,'Covariate_2':y,
                              'Status':'Constant within cohort' if constant else 'Testable',
                              'Effect_type':'Kruskal-Wallis eta squared (H)','Effect':max(0,(h-k+1)/(len(g)-k)) if not constant else np.nan,
                              'P':p,'Groups':k,'Minimum_expected_count':None})
    mixed=pd.DataFrame(mixed)
    mixed['Q_within_cohort_type']=mixed.groupby(['Cohort','Effect_type'],sort=False).P.transform(lambda x:bh(x))
    descriptive=[]
    for arm in ARMS:
        g=train[train.treatment_arm==arm]
        for v in NUMERIC:
            descriptive.append({'Arm':arm,'Covariate':v,'Type':'Numeric','Level':None,'N':len(g),'Count':None,
                                'Proportion':None,'Mean':g[v].mean(),'SD':g[v].std(),'Median':g[v].median(),
                                'Q1':g[v].quantile(.25),'Q3':g[v].quantile(.75),'Min':g[v].min(),'Max':g[v].max(),
                                'Improvement_mean':None,'Improvement_median':None})
        for v in CATEGORICAL:
            for level in LEVELS[v]:
                q=g[g[v]==level]
                descriptive.append({'Arm':arm,'Covariate':v,'Type':'Categorical','Level':level,'N':len(g),
                                    'Count':len(q),'Proportion':len(q)/len(g),'Mean':None,'SD':None,'Median':None,
                                    'Q1':None,'Q3':None,'Min':None,'Max':None,
                                    'Improvement_mean':q.improvement_score.mean(),
                                    'Improvement_median':q.improvement_score.median()})
    desc=pd.DataFrame(descriptive)
    for name,data in [('arm_summary',summary),('outcome_associations',outcomes),('numeric_correlations',pairs),
                      ('categorical_covariate_associations',mixed),('covariate_summaries',desc)]:
        data.to_csv(out/'tables'/f'{name}.csv',index=False)
    # Metadata documents exactly what was screened; no holdout outcome analysis.
    meta={'seed':SEED,'test_fraction':.2,'stratify_by':'assigned-arm responder label',
          'source_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
          'numeric':NUMERIC,'categorical':CATEGORICAL,'labels':LABELS,'short_labels':SHORT,
          'arms':ARMS,'endpoints':ENDPOINTS,'sign':SIGN,'levels':LEVELS,
          'bootstrap_replicates':2000,'missing_predictor_cells':0,
          'constant_predictor':'albumin in Mexiletine; do not replace undefined correlations with zero',
          'FDR_families':'17 evaluable outcome tests in Mexiletine, 18 each in other arms; 53 across arms',
          'age_duration_identity':'disease_duration = age - age_at_onset, all 500 rows',
          'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
          'scipy':scipy.__version__,'sklearn':sklearn.__version__}
    (out/'analysis_metadata.json').write_text(json.dumps(meta,indent=2))
    def records(d): return json.loads(d.to_json(orient='records'))
    report={'metadata':meta,'arm_summary':records(summary),'outcomes':records(outcomes),
            'pairs':records(pairs),'mixed':records(mixed),'descriptive':records(desc),
            'matrices':matrices,'partition':records(partition),'training':records(train)}
    (out/'analysis_results.json').write_text(json.dumps(report,allow_nan=False))
    print(summary.to_string(index=False))
    for arm in ARMS:
        print('\n',arm,'primary FDR < 0.05')
        z=outcomes[(outcomes.Arm==arm)&outcomes.FDR_0_05]
        print(z[['Covariate','Type','Spearman_rho_improvement','Eta_squared_H','P_primary','Q_within_arm']].to_string(index=False))
    print('\nStrong numeric pairs:')
    print(pairs[pairs.Abs_rho_ge_0_70][['Cohort','Covariate_1','Covariate_2','Spearman_rho','Pearson_r']].to_string(index=False))
    print('\nDONE',out.resolve())

if __name__=='__main__': main()
