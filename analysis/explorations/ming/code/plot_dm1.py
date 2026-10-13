#!/usr/bin/env python3
"""Create scientific correlation figures and a PDF report from the saved DM1 analysis."""
from pathlib import Path
import argparse, json, textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import font_manager
from pypdf import PdfReader, PdfWriter

COLORS={'Mexiletine':'#126E82','Oligonucleotide':'#6F4B96','Tideglusib':'#D87920'}
INK='#20344A'; GREY='#66727F'
DIV=LinearSegmentedColormap.from_list('association',['#A75C24','#FFFFFF','#126E82'])
DIV.set_bad('#E3E6EA')
POS=LinearSegmentedColormap.from_list('positive',['#FFFFFF','#B4D3DD','#126E82'])
POS.set_bad('#E3E6EA')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.titlesize':15,
 'axes.labelsize':12,'xtick.labelsize':10,'ytick.labelsize':11,'axes.spines.top':False,
 'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.labelcolor':INK,
 'text.color':INK,'axes.titlecolor':INK,'figure.facecolor':'white'})

def qfmt(q):
    if not np.isfinite(q): return 'NA'
    return '<0.001' if q<.001 else f'{q:.3f}'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,default=Path('outputs/dm1_covariates_20261011'))
    args=ap.parse_args(); out=args.out; figs=out/'figures'; figs.mkdir(exist_ok=True)
    js=json.loads((out/'analysis_results.json').read_text()); meta=js['metadata']
    arms=meta['arms']; num=meta['numeric']; cat=meta['categorical']; labels=meta['labels']; short=meta['short_labels']
    outcomes=pd.DataFrame(js['outcomes']); train=pd.DataFrame(js['training']); mixed=pd.DataFrame(js['mixed'])
    pages=[]; index=[]
    def save(fig,name,title,note):
        fig.suptitle(title,x=.045,y=.967,ha='left',fontsize=24,fontweight='bold')
        fig.text(.045,.025,note,ha='left',va='bottom',fontsize=10,color=GREY)
        fig.savefig(figs/f'{name}.png',dpi=170)
        fig.savefig(figs/f'{name}.svg')
        fig.savefig(figs/f'{name}.pdf')
        pages.append(figs/f'{name}.pdf'); index.append({'file':name,'title':title,'note':note}); plt.close(fig)
    def heat(ax,values,rows,cols,cmap=DIV,vmin=-1,vmax=1,stars=None,fs=12):
        arr=np.array(values,dtype=float)
        im=ax.imshow(np.ma.masked_invalid(arr),cmap=cmap,vmin=vmin,vmax=vmax,aspect='auto')
        ax.set_xticks(np.arange(len(cols)),cols); ax.set_yticks(np.arange(len(rows)),rows)
        ax.tick_params(length=0)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                val=arr[i,j]; mark='*' if stars is not None and stars[i,j] else ''
                text='NA' if np.isnan(val) else f'{val:+.2f}{mark}' if vmin<0 else f'{val:.2f}{mark}'
                color='white' if np.isfinite(val) and (abs(val)>.68 if vmin<0 else val>.70*vmax) else INK
                ax.text(j,i,text,ha='center',va='center',fontsize=fs,color=color)
        for spine in ax.spines.values(): spine.set_visible(False)
        return im
    # All 13 numeric associations, arm-specific outcomes oriented toward improvement.
    values=np.array([[outcomes[(outcomes.Arm==a)&(outcomes.Covariate==v)].Spearman_rho_improvement.iloc[0] for a in arms] for v in num])
    stars=np.array([[outcomes[(outcomes.Arm==a)&(outcomes.Covariate==v)].Q_within_arm.iloc[0]<.05 for a in arms] for v in num])
    fig,ax=plt.subplots(figsize=(16,9)); fig.subplots_adjust(left=.31,right=.88,top=.87,bottom=.12)
    im=heat(ax,values,[labels[v] for v in num],[f'{a}\nn={len(train[train.treatment_arm==a])}' for a in arms],stars=stars,fs=16)
    fig.colorbar(im,ax=ax,fraction=.05,pad=.06,label='Spearman rho with improvement')
    save(fig,'01_numeric_outcome_associations','Numeric covariates and improvement by treatment arm',
         '* Within-arm BH FDR < 0.05. Mexiletine improvement = −myotonia_change_12wk. Other endpoints retain their original sign. NA = constant albumin.')
    vals=np.array([[outcomes[(outcomes.Arm==a)&(outcomes.Covariate==v)].Eta_squared_H.iloc[0] for a in arms] for v in cat])
    stars=np.array([[outcomes[(outcomes.Arm==a)&(outcomes.Covariate==v)].Q_within_arm.iloc[0]<.05 for a in arms] for v in cat])
    fig,ax=plt.subplots(figsize=(16,9)); fig.subplots_adjust(left=.23,right=.86,top=.86,bottom=.15)
    im=heat(ax,vals,[labels[v] for v in cat],arms,cmap=POS,vmin=0,vmax=.3,stars=stars,fs=20)
    fig.colorbar(im,ax=ax,fraction=.05,pad=.07,label='Kruskal–Wallis eta squared (H)')
    save(fig,'02_categorical_outcome_associations','Categorical covariates and improvement by treatment arm',
         '* Within-arm BH FDR < 0.05. Eta²(H) = max(0, (H−k+1)/(n−k)). This rank effect size is unsigned and has a different scale from rho.')
    # Correlations among baseline numeric predictors in the pooled training sample and each arm.
    for idx,m in enumerate(js['matrices']):
        fig,ax=plt.subplots(figsize=(16,9)); fig.subplots_adjust(left=.21,right=.83,top=.87,bottom=.19)
        im=heat(ax,m['spearman'],[labels[v] for v in num],short,fs=10)
        ax.set_xticklabels(short,rotation=45,ha='right',fontsize=10)
        fig.colorbar(im,ax=ax,fraction=.04,pad=.035,label='Spearman rho')
        save(fig,f'03_{idx}_baseline_numeric_correlations',f"Baseline numeric covariate correlations: {m['cohort']} (n={m['n']})",
             'Training patients only. Full Spearman and Pearson results are in the workbook. NA = no within-cohort variation. Onset age = age_at_onset.')
    # Confidence intervals for all numeric outcome relationships.
    fig,axs=plt.subplots(1,3,figsize=(16,9),sharey=True); fig.subplots_adjust(left=.25,right=.965,top=.85,bottom=.13,wspace=.16)
    for ax,a in zip(axs,arms):
        ax.axvline(0,color='#8B959E',lw=1); g=outcomes[(outcomes.Arm==a)&(outcomes.Type=='Numeric')].set_index('Covariate').loc[num]
        for k,(v,row) in enumerate(g.iterrows()):
            if pd.isna(row.Spearman_rho_improvement):
                ax.text(0,k,'NA (constant)',ha='center',va='center',fontsize=10,color=GREY); continue
            color=COLORS[a] if row.Q_within_arm<.05 else '#909AA4'
            ax.plot([row.CI95_low,row.CI95_high],[k,k],color=color,lw=2)
            ax.scatter(row.Spearman_rho_improvement,k,color=color,s=44,zorder=3)
        ax.set_xlim(-1,1); ax.set_xticks([-1,-.5,0,.5,1]); ax.set_title(f'{a}\nn={len(train[train.treatment_arm==a])}',color=COLORS[a])
        ax.set_xlabel('Spearman rho'); ax.grid(axis='x',alpha=.16)
    axs[0].set_yticks(range(len(num)),[labels[v] for v in num]); axs[0].invert_yaxis()
    save(fig,'04_numeric_outcome_confidence_intervals','Uncertainty in numeric covariate associations',
         'Points and 95% percentile bootstrap intervals (2,000 resamples). Colored points have within-arm FDR < 0.05. Intervals are not multiplicity adjusted.')
    for a in arms:
        g=train[train.treatment_arm==a]; z=outcomes[(outcomes.Arm==a)&(outcomes.Type=='Numeric')].copy()
        z['abs_rho']=z.Spearman_rho_improvement.abs(); z=z.dropna(subset=['abs_rho']).sort_values('abs_rho',ascending=False).head(4)
        fig,axs=plt.subplots(2,2,figsize=(16,9)); fig.subplots_adjust(left=.075,right=.965,top=.83,bottom=.14,hspace=.54,wspace=.18)
        for ax,(_,r) in zip(axs.flat,z.iterrows()):
            x=g[r.Covariate].values; y=g.improvement_score.values
            ax.scatter(x,y,s=27,alpha=.7,color=COLORS[a],edgecolor='white',linewidth=.35)
            fit=stats.linregress(x,y); xx=np.linspace(x.min(),x.max(),100); ax.plot(xx,fit.intercept+fit.slope*xx,color=INK,lw=1.8)
            ax.set_xlabel(labels[r.Covariate]); ax.set_ylabel('Improvement score'); ax.grid(alpha=.15)
            ax.set_title(f"rho = {r.Spearman_rho_improvement:+.3f}, FDR q {qfmt(r.Q_within_arm)}",fontsize=14)
        save(fig,f'05_{a.lower()}_leading_scatterplots',f'Leading numeric associations: {a} (n={len(g)})',
             'Four largest absolute Spearman correlations. Line shows unadjusted OLS as a visual guide. Correlated predictors can represent the same underlying signal.')
    # All five nominal covariates: no arbitrary integer coding.
    jitter=np.random.default_rng(meta['seed']+1)
    catsets=[['phenotype'],['sex','family_history'],['cataracts','smoking_status']]
    for k,vs in enumerate(catsets):
        fig,axs=plt.subplots(len(vs),3,figsize=(16,9),squeeze=False)
        fig.subplots_adjust(left=.06,right=.965,top=.82,bottom=.14,wspace=.23,hspace=.75 if len(vs)>1 else .25)
        for i,v in enumerate(vs):
            for j,a in enumerate(arms):
                ax=axs[i,j]; g=train[train.treatment_arm==a]; levels=meta['levels'][v]
                vals=[g[g[v]==lev].improvement_score.values for lev in levels]
                bp=ax.boxplot(vals,positions=np.arange(len(levels)),widths=.52,patch_artist=True,showfliers=False,
                              medianprops={'color':INK,'linewidth':2},boxprops={'linewidth':1,'edgecolor':COLORS[a]},
                              whiskerprops={'color':GREY},capprops={'color':GREY})
                for b in bp['boxes']: b.set_facecolor(COLORS[a]); b.set_alpha(.2)
                for h,y in enumerate(vals): ax.scatter(h+jitter.uniform(-.15,.15,len(y)),y,s=12,alpha=.6,color=COLORS[a])
                r=outcomes[(outcomes.Arm==a)&(outcomes.Covariate==v)].iloc[0]
                ax.set_title(f"{a}\n{labels[v]}: eta²(H)={r.Eta_squared_H:.3f}, q {qfmt(r.Q_within_arm)}",fontsize=13)
                pretty=[lev.replace('_onset',' onset').capitalize()+f'\n(n={len(val)})' for lev,val in zip(levels,vals)]
                ax.set_xticks(np.arange(len(levels)),pretty,fontsize=10)
                ax.grid(axis='y',alpha=.15)
                if j==0: ax.set_ylabel('Improvement score')
        save(fig,f'06_{k}_categorical_outcome_distributions','Improvement distributions by '+('phenotype' if k==0 else 'categorical covariates'),
             'Training patients only. Boxes show median and IQR. Whiskers extend to 1.5 IQR. Points are individual patients. q = within-arm BH FDR.')
    # Numeric-categorical covariate relationships across all four cohorts.
    fig,axs=plt.subplots(2,2,figsize=(16,9)); fig.subplots_adjust(left=.11,right=.91,top=.85,bottom=.17,wspace=.28,hspace=.5)
    for ax,m in zip(axs.flat,js['matrices']):
        cohort=m['cohort']; vals=[]
        for v in cat:
            vals.append([mixed[(mixed.Cohort==cohort)&(mixed.Covariate_1==v)&(mixed.Covariate_2==u)].Effect.iloc[0] for u in num])
        im=heat(ax,vals,[labels[v] for v in cat],short,cmap=POS,vmin=0,vmax=1,fs=7)
        ax.set_title(f"{cohort} (n={m['n']})",fontsize=14); ax.set_xticklabels(short,rotation=45,ha='right',fontsize=8)
        ax.tick_params(axis='y',labelsize=9)
    cax=fig.add_axes([.94,.25,.015,.48]); fig.colorbar(im,cax=cax,label='Kruskal–Wallis eta squared (H)')
    save(fig,'07_mixed_baseline_covariate_associations','Categorical and numeric baseline covariate relationships',
         'Unsigned rank effect size, not a correlation coefficient. Full results and categorical–categorical Cramer’s V are in the workbook. NA = constant albumin.')
    # Summary and methods pages via ReportLab, then append vector figure pages.
    pdfmetrics.registerFont(TTFont('ReportSans',font_manager.findfont('DejaVu Sans')))
    pdfmetrics.registerFont(TTFont('ReportSansBold',font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans',weight='bold'))))
    intro=out/'report_intro.pdf'; c=canvas.Canvas(str(intro),pagesize=(1152,648))
    def txt(x,y,s,size=18,bold=False,col=INK):
        c.setFillColor(HexColor(col)); c.setFont('ReportSansBold' if bold else 'ReportSans',size); c.drawString(x,y,s)
    def wrap_width(s,width,size=15):
        lines=[]; cur=''
        for w in s.split():
            new=cur+' '+w if cur else w
            if pdfmetrics.stringWidth(new,'ReportSans',size)>width and cur:
                lines.append(cur); cur=w
            else: cur=new
        if cur: lines.append(cur)
        return lines
    txt(48,596,'DM1 covariate correlations by treatment arm',32,True)
    txt(48,564,'Simulated ACoP 2026 hackathon data. Exploratory associations from training patients.',18,col=GREY)
    columns=[48,360,500,635,780]; headers=['Treatment arm','All patients','Training','Test reserved','Training responders']
    for x,h in zip(columns,headers): txt(x,508,h,16,True)
    for k,r in enumerate(js['arm_summary']):
        y=470-40*k; vals=[r['Arm'],str(r['All_n']),str(r['Training_n']),str(r['Test_n']),f"{r['Training_responders']} ({r['Training_responder_rate']:.1%})"]
        for x,v in zip(columns,vals): txt(x,y,v,19)
    txt(48,330,'Leading unadjusted associations with improvement',23,True)
    for i,a in enumerate(arms):
        z=outcomes[(outcomes.Arm==a)&(outcomes.Type=='Numeric')].copy(); z['abs_rho']=z.Spearman_rho_improvement.abs()
        z=z.sort_values('abs_rho',ascending=False).head(2)
        desc='; '.join(f"{labels[r.Covariate].split(' (')[0]} (rho {r.Spearman_rho_improvement:+.2f})" for _,r in z.iterrows())
        txt(48,288-38*i,f'{a}: {desc}',19,col=COLORS[a])
    txt(48,146,'Modeling issues',22,True)
    txt(48,116,'Albumin is constant at 4.18 g/dL in mexiletine. Its within-arm correlation is undefined.',17)
    txt(48,90,'Disease duration = age - age at onset. Include at most two of these three linear terms.',17)
    txt(48,52,'Strong covariate correlations can produce several marginal associations from one underlying signal.',16,col=GREY)
    c.showPage()
    txt(48,596,'Analysis definitions and interpretation',32,True)
    lines=[
      ('Analysis population','80/20 split within each arm, stratified by the assigned responder label. Seed 20261011.'),
      ('Holdout protection','399 training patients screened. The 101 test patients were reserved for future model evaluation.'),
      ('Endpoint direction','Mexiletine: -myotonia_change_12wk. Oligonucleotide: qmt_change_26wk. Tideglusib: tideglusib_composite.'),
      ('Numeric covariates','Spearman rank correlations are primary. Pearson correlations provide a linear-association sensitivity analysis.'),
      ('Categorical covariates','Kruskal-Wallis tests and eta-squared (H) effect sizes. Nominal levels are never assigned arbitrary numeric codes.'),
      ('Multiplicity','BH FDR across 17 evaluable predictors in mexiletine and 18 in each other arm. q across all 53 tests is also supplied.'),
      ('Uncertainty','95% percentile bootstrap intervals use 2,000 resamples. They are exploratory and not multiplicity adjusted.'),
      ('Missing values','Blank nonassigned-arm endpoints are structural. No imputation. Constant predictors receive NA, not zero.'),
      ('Interpretation','These marginal associations do not establish independent predictors. Nonlinear and interacting effects may be missed.'),
      ('Arm comparisons','Assignment used weighted probabilities informed by baseline fit. Different endpoints prevent direct efficacy ranking.'),
      ('Next modeling step','Assess correlated predictors jointly with regularization or prespecified alternatives using training-only cross-validation.'),
    ]
    y=535
    for title,body in lines:
        txt(48,y,title,15.5,True)
        for line in wrap_width(body,785,14):
            txt(320,y,line,14); y-=17
        y-=13
    txt(48,26,'Sources: supplied dataset and dictionary. Kickoff deck pp. 39, 41, 44-46. Effect-size definition: rstatix kruskal_effsize.',10,col=GREY)
    c.linkURL('https://rpkgs.datanovia.com/rstatix/reference/kruskal_effsize.html',(730,20,1100,35),relative=0)
    c.save()
    final=PdfWriter(); final.append(str(intro))
    for p in pages: final.append(str(p))
    final.write(str(out/'DM1_Covariate_Correlations_by_Arm.pdf')); intro.unlink()
    (out/'figure_index.json').write_text(json.dumps(index,indent=2))
    print('Figures:',len(pages),'Report pages:',len(PdfReader(out/'DM1_Covariate_Correlations_by_Arm.pdf').pages))

if __name__=='__main__': main()
