import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=process.argv[2] || '/workspace/scratch/420c8302a6b5';
const out=process.argv[3] || root+'/outputs/dm1_covariates_20261011';
const d=JSON.parse(await fs.readFile(out+'/analysis_results.json','utf8'));
const dictionary=JSON.parse(await fs.readFile(root+'/work/dictionary.json','utf8'));
const wb=Workbook.create();
const names=['Overview','Outcome associations','Spearman matrices','Numeric pairs','Mixed pairs','Covariate summaries','Training data','Split','Dictionary'];
const sh=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const ink='#20344A', muted='#66727F', header='#304B69';
const col=(n)=>{let s=''; for(;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
function base(s,rows,cols){
  s.showGridLines=false;
  const r=s.getRange(`A1:${col(cols)}${rows}`);
  r.format.font={name:'Arial',size:10,color:ink};
  r.format.rowHeight=21;r.format.columnWidth=17;r.format.verticalAlignment='center';
}
function title(s,text,note,cols){
  s.getRange('A2').values=[[text]];s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:ink};
  s.getRange('A3').values=[[note]];s.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:muted};
  s.getRange(`A4:${col(cols)}4`).format.borders={bottom:{style:'thin',color:'#B8C2CC'}};
}
function value(v){return v===null||v===undefined?'NA':v;}
function table(s,rows,fields,labels,name,{raw=false,widths=[]}={}){
  const start=raw?1:5;
  base(s,rows.length+start,fields.length);
  s.getRange(`A${start}:${col(fields.length)}${start+rows.length}`).values=[labels,...rows.map(r=>fields.map(f=>value(r[f])))];
  const hdr=s.getRange(`A${start}:${col(fields.length)}${start}`);
  hdr.format.fill=header;hdr.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  hdr.format.wrapText=true;hdr.format.rowHeight=42;hdr.format.horizontalAlignment='center';
  const t=s.tables.add(`A${start}:${col(fields.length)}${start+rows.length}`,true,name);
  t.style='TableStyleMedium2';t.showBandedRows=true;
  s.freezePanes.freezeRows(start);
  for(let i=0;i<fields.length;i++)s.getRange(`${col(i+1)}${start}:${col(i+1)}${start+rows.length}`).format.columnWidth=widths[i]??17;
  return start;
}
const ss=sh['Split'];table(ss,d.partition,['patient_id','treatment_arm','partition'],['patient_id','treatment_arm','partition'],'PartitionTable',{raw:true,widths:[19,24,18]});
const train=sh['Training data'];const fields=Object.keys(d.training[0]);
table(train,d.training,fields,fields,'TrainingTable',{raw:true,widths:fields.map(f=>f.length>18?27:f.length>12?23:18)});
// Source blanks are structural nonassigned-arm outcomes. Keep them blank in the raw training table.
train.getRange(`A2:${col(fields.length)}${d.training.length+1}`).values=d.training.map(r=>fields.map(f=>r[f]??null));
train.getRange('AE1').values=[['Source: dm1_clinical_trial_dataset.csv. Training subset, seed 20261011.']];
train.getRange('AE2').values=[['Endpoint and units: participant data dictionary. Nonassigned-arm endpoints remain blank.']];
train.getRange('AE3').values=[['improvement_score = negative mexiletine change, otherwise assigned continuous endpoint.']];
train.getRange('AE1:AE3').format.columnWidth=95;train.getRange('AE1:AE3').format.font={name:'Arial',size:10,color:muted};
// Overview: formulas make sample counts traceable to the delivered patient lists.
const s=sh.Overview;base(s,36,8);s.getRange('A1:H36').format.columnWidth=18;s.getRange('A1:A36').format.columnWidth=24;
title(s,'DM1 covariate correlations by treatment arm','Simulated data. Training-only exploratory screening. Outcome associations are saved analysis results.',8);
s.getRange('A6:F6').values=[['Treatment arm','All patients','Training','Test reserved','Training responders','Responder rate']];
s.getRange('A6:F6').format.fill=header;s.getRange('A6:F6').format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
s.getRange('A6:F6').format.wrapText=true;s.getRange('A6:F6').format.rowHeight=34;
for(let i=0;i<d.metadata.arms.length;i++){
 const r=7+i, a=d.metadata.arms[i];s.getRange(`A${r}`).values=[[a]];
 s.getRange(`B${r}:F${r}`).formulas=[[
  `=COUNTIFS('Split'!$B$2:$B$501,A${r})`,
  `=COUNTIFS('Split'!$B$2:$B$501,A${r},'Split'!$C$2:$C$501,"Training")`,
  `=COUNTIFS('Split'!$B$2:$B$501,A${r},'Split'!$C$2:$C$501,"Test")`,
  `=COUNTIFS('Training data'!$B$2:$B$400,A${r},'Training data'!$AC$2:$AC$400,"Responder")`,
  `=E${r}/C${r}`]];
}
s.getRange('B7:E9').setNumberFormat('0');s.getRange('F7:F9').setNumberFormat('0.0%');
s.getRange('A10').values=[['Total']];s.getRange('B10:E10').formulas=[['=SUM(B7:B9)','=SUM(C7:C9)','=SUM(D7:D9)','=SUM(E7:E9)']];
s.getRange('F10').formulas=[['=E10/C10']];s.getRange('F10').setNumberFormat('0.0%');s.getRange('A10:F10').format.font.bold=true;
s.getRange('A13').values=[['Leading marginal associations']];s.getRange('A13').format.font={name:'Arial',size:14,bold:true,color:ink};
s.getRange('A15:E15').values=[['Treatment arm','Covariate','Effect','Estimate','Within-arm FDR q']];
s.getRange('A15:E15').format.fill=header;s.getRange('A15:E15').format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
s.getRange('A15:E15').format.rowHeight=32;s.getRange('A15:E15').format.wrapText=true;
let rr=16;
for(const arm of d.metadata.arms){
 const lead=d.outcomes.filter(x=>x.Arm===arm&&x.Type==='Numeric'&&x.Status==='Testable').sort((a,b)=>Math.abs(b.Spearman_rho_improvement)-Math.abs(a.Spearman_rho_improvement)).slice(0,2);
 lead.push(d.outcomes.find(x=>x.Arm===arm&&x.Covariate==='phenotype'));
 for(const r of lead){s.getRange(`A${rr}:E${rr}`).values=[[arm,d.metadata.labels[r.Covariate].split(' (')[0],r.Type==='Numeric'?'Spearman rho':'Eta squared (H)',r.Type==='Numeric'?r.Spearman_rho_improvement:r.Eta_squared_H,r.Q_within_arm]];rr++;}
}
s.getRange('B15:B24').format.columnWidth=27;s.getRange('C15:C24').format.columnWidth=20;s.getRange('D16:D24').setNumberFormat('0.000');s.getRange('E16:E24').setNumberFormat('0.00E+00');
const notes=[
 'Split: 80/20 within each arm, stratified by responder label. Seed 20261011.',
 'Positive rho means greater improvement. Mexiletine change was multiplied by -1.',
 'BH FDR: 17 evaluable predictors in mexiletine, 18 in each other arm. q across all 53 tests is also supplied.',
 'Albumin is constant at 4.18 g/dL in mexiletine. NA indicates an undefined association, not a zero effect.',
 'Disease duration = age - age at onset. Avoid fitting all three as unrestricted linear terms.',
 'Correlations are marginal. Correlated covariates may share signal. Nonlinear effects can be missed.',
 'Arm assignment was weighted by baseline fit. Different endpoints prevent direct efficacy ranking.',
 'Result tables are snapshots from the included Python analysis. Rerun the analysis to update statistical results.'
];
notes.forEach((x,i)=>{s.getRange(`A${27+i}`).values=[[x]];s.getRange(`A${27+i}`).format.font={name:'Arial',size:10,color:muted};});
s.tabColor=header;
const assoc=sh['Outcome associations'];
const af=['Arm','Covariate','Type','N','Spearman_rho_improvement','Spearman_rho_original','CI95_low','CI95_high','Pearson_r_improvement','Eta_squared_H','P_primary','Q_within_arm','Q_all_evaluable','FDR_0_05','Status'];
table(assoc,d.outcomes,af,['Arm','Covariate','Type','N','rho improvement','rho original endpoint','95% CI lower','95% CI upper','Pearson r improvement','Eta squared (H)','Primary p','FDR q within arm','FDR q all 53 tests','FDR <0.05','Status'],'OutcomeTable',{widths:[24,32,16,10,17,19,16,16,21,17,17,18,18,16,27]});
title(assoc,'Covariate associations with arm-specific improvement','Numeric: Spearman. Categorical: Kruskal-Wallis. CI = 2,000 percentile bootstrap resamples. Eta squared (H) is unsigned.',15);
assoc.getRange('E6:J59').setNumberFormat('0.000');assoc.getRange('K6:M59').setNumberFormat('0.00E+00');
assoc.getRange('L6:L59').conditionalFormats.add('cellIs',{operator:'lessThan',formula:.05,format:{fill:'#DCEEE9',font:{bold:true,color:'#126E82'}}});
const mat=sh['Spearman matrices'];base(mat,90,14);title(mat,'Baseline numeric covariate correlations','Spearman rho. Pooled training and each treatment arm. NA = constant within cohort. Pearson results are in Numeric pairs.',14);
mat.getRange('A1:A90').format.columnWidth=34;mat.getRange('B1:N90').format.columnWidth=10;
for(let k=0;k<d.matrices.length;k++){
 const m=d.matrices[k],r=6+k*21;
 mat.getRange(`A${r}`).values=[[`${m.cohort}, n=${m.n}`]];mat.getRange(`A${r}`).format.font={name:'Arial',size:14,bold:true,color:ink};
 mat.getRange(`B${r+2}:N${r+2}`).values=[d.metadata.short_labels];mat.getRange(`B${r+2}:N${r+2}`).format.fill=header;
 mat.getRange(`B${r+2}:N${r+2}`).format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};mat.getRange(`B${r+2}:N${r+2}`).format.wrapText=true;mat.getRange(`B${r+2}:N${r+2}`).format.rowHeight=34;
 mat.getRange(`A${r+3}:A${r+15}`).values=d.metadata.numeric.map(v=>[d.metadata.labels[v]]);
 const grid=mat.getRange(`B${r+3}:N${r+15}`);grid.values=m.spearman.map(row=>row.map(value));grid.setNumberFormat('0.00');
 grid.conditionalFormats.add('colorScale',{colors:['#B87746','#FFFFFF','#19768A'],thresholds:[{type:'num',value:-1},{type:'num',value:0},{type:'num',value:1}]});
}
const np=sh['Numeric pairs'];const nf=['Cohort','N','Covariate_1','Covariate_2','Spearman_rho','Pearson_r','P_spearman','P_pearson','Q_spearman_within_cohort','Abs_rho_ge_0_70','Status'];
table(np,d.pairs,nf,['Cohort','N','Covariate 1','Covariate 2','Spearman rho','Pearson r','Spearman p','Pearson p','Spearman FDR q','Abs rho >=0.70','Status'],'NumericPairTable',{widths:[24,10,32,32,18,18,18,18,21,18,27]});
title(np,'Pairwise numeric covariate correlations','78 pairs per cohort. FDR correction covers evaluable Spearman tests within each cohort. Constant predictors are NA.',11);
np.getRange(`E6:F${d.pairs.length+5}`).setNumberFormat('0.000');np.getRange(`G6:I${d.pairs.length+5}`).setNumberFormat('0.00E+00');
const mix=sh['Mixed pairs'];const mf=['Cohort','N','Covariate_1','Covariate_2','Effect_type','Effect','P','Q_within_cohort_type','Minimum_expected_count','Status'];
table(mix,d.mixed,mf,['Cohort','N','Covariate 1','Covariate 2','Association measure','Effect','p','FDR q','Minimum expected count','Status'],'MixedPairTable',{widths:[24,10,31,31,39,17,17,18,24,27]});
title(mix,'Categorical covariate relationships','Categorical-categorical: Cramer V (uncorrected). Categorical-numeric: Kruskal-Wallis eta squared (H). Unsigned, different scales.',10);
mix.getRange(`F6:F${d.mixed.length+5}`).setNumberFormat('0.000');mix.getRange(`G6:H${d.mixed.length+5}`).setNumberFormat('0.00E+00');mix.getRange(`I6:I${d.mixed.length+5}`).setNumberFormat('0.0');
const des=sh['Covariate summaries'];const df=['Arm','Covariate','Type','Level','N','Count','Proportion','Mean','SD','Median','Q1','Q3','Min','Max','Improvement_mean','Improvement_median'];
table(des,d.descriptive,df,['Arm','Covariate','Type','Level','Arm N','Level count','Level fraction','Mean','SD','Median','Q1','Q3','Min','Max','Level improvement mean','Level improvement median'],'DescriptiveTable',{widths:[24,32,16,23,10,13,17,16,16,16,16,16,16,16,25,25]});
title(des,'Covariate summaries by arm','Training patients only. Numeric covariates retain source units. For categorical rows, level counts and level-specific improvement are shown.',16);
des.getRange(`G6:G${d.descriptive.length+5}`).setNumberFormat('0.0%');des.getRange(`H6:P${d.descriptive.length+5}`).setNumberFormat('0.00');
table(sh.Dictionary,dictionary,['Column','Type','Description'],['Column','Type and units','Description'],'DictionaryTable',{raw:true,widths:[35,50,110]});
sh.Dictionary.getRange(`C2:C${dictionary.length+1}`).format.wrapText=true;sh.Dictionary.getRange(`C2:C${dictionary.length+1}`).format.rowHeight=44;
sh.Dictionary.getRange('E1').values=[['Source: DM1_Data_Dictionary_Participant.xlsx, Column Dictionary.']];sh.Dictionary.getRange('E1').format.columnWidth=90;
wb.recalculate();
await fs.mkdir(root+'/work/xlsx_qa',{recursive:true});
for(const [name,range] of [['Overview','A1:H35'],['Outcome associations','A1:F15'],['Spearman matrices','A6:N21'],['Numeric pairs','A1:F14'],['Mixed pairs','A1:F14'],['Covariate summaries','A1:G14'],['Training data','A1:G12'],['Split','A1:C12'],['Dictionary','A1:C8']]){
 const b=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
 await fs.writeFile(root+'/work/xlsx_qa/'+name.replaceAll(' ','_')+'.png',new Uint8Array(await b.arrayBuffer()));
}
console.log((await wb.inspect({kind:'table',range:'Overview!A6:F10',include:'values,formulas',tableMaxRows:5,tableMaxCols:6,maxChars:2000})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1200})).ndjson);
const f=await SpreadsheetFile.exportXlsx(wb);await f.save(out+'/DM1_Covariate_Correlation_Results.xlsx');
console.log('Exported workbook with',names.length,'sheets.');
