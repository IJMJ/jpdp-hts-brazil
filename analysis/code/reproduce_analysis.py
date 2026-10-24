"""Reproduce the provisional 65-article and 129-entity revision calculations offline."""
from pathlib import Path
import json,math,hashlib,sys
import numpy as np
import pandas as pd
import statistical_functions as m
# Explicit interval-label override; statistical functions and period scores unchanged.
m.PERIODS=['2016-2019','2020-2022','2023-2026']
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'data'
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)
a=pd.read_csv(O/'article_reporting_scores_R1_working.csv')
e=pd.read_csv(O/'entity_master_R1_coverage_working.csv')

links=pd.read_csv(O/'article_entity_links_R1_working.csv')
assert len(a)==65 and not a.article_id.duplicated().any()
assert len(e)==129 and not e.master_entity_id.duplicated().any()
assert len(links)==139 and not links[['article_id','entity_id']].duplicated().any()
assert set(links.article_id)==set(a.article_id)
assert set(links.entity_id)==set(e.master_entity_id)
assert e.cohort.value_counts().to_dict()=={'Main':77,'Secondary':52}
for dim in m.DIMS:
    flag=dim+'_reported'
    assert a[flag].isin([0,1]).all()
    assert a[flag].eq(a[dim].eq('REPORTED').astype(int)).all()
assert a.sequencing_evidence_score.eq(a[[d+'_reported' for d in m.DIMS[:3]]].sum(axis=1)).all()
assert a.bioinformatics_reproducibility_score.eq(a[[d+'_reported' for d in m.DIMS[3:]]].sum(axis=1)).all()
assert a.overall_reporting_score.eq(a[m.SCORE_COLS[:2]].sum(axis=1)).all()
assert a.period.eq(a.year.map(lambda y:'2016-2019' if 2016<=y<=2019 else '2020-2022' if 2020<=y<=2022 else '2023-2026' if 2023<=y<=2026 else 'OUT_OF_SCOPE')).all()

totals=[int(a.period.eq(p).sum()) for p in m.PERIODS]
assert totals==[22,21,22]
assert len(a)==65 and a.article_id.nunique()==65
assert len(e)==129 and e.master_entity_id.nunique()==129
assert a.period.eq(a.year.map(lambda y:'2016-2019' if 2016<=y<=2019 else '2020-2022' if 2020<=y<=2022 else '2023-2026' if 2023<=y<=2026 else 'OUT_OF_SCOPE')).all()
rows=[]
for dim in m.DIMS:
    successes=[int(a.loc[a.period.eq(p),dim+'_reported'].sum()) for p in m.PERIODS]
    z,p=m.cochran_armitage(successes,totals,m.PERIOD_SCORES)
    rows.append({'dimension':dim,'reported_by_period':successes,'total_by_period':totals,'exact_p':m.ffh_exact_3x2(successes,totals),'trend_p':p,'trend_z':z})
for row,q1,q2 in zip(rows,m.bh_adjust([r['exact_p'] for r in rows]),m.bh_adjust([r['trend_p'] for r in rows])):row.update(exact_q=q1,trend_q=q2)
scores=[]
for i,col in enumerate(m.SCORE_COLS):
    stat,p=m.permutation_rank_test(a[col].to_numpy(dtype=float),a.period.to_numpy(),100000,m.RANDOM_SEED+i)
    scores.append({'score':col,'statistic':stat,'p':p,'permutations':100000,'seed':m.RANDOM_SEED+i})
    print(col,p,flush=True)
for row,q in zip(scores,m.bh_adjust([r['p'] for r in scores])):row['q']=q
def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-h,c+h]
metrics=[]
for cohort in ['All','Main','Secondary']:
    data=e if cohort=='All' else e[e.cohort.eq(cohort)]
    for field in ['molecular_validation_or_higher','replicated_association_or_higher','experimental_infection_or_higher','experimental_disease_reproduction','reconstructed_agent_direct','has_public_raw_reads','complete_or_coding_complete_genome','hts_platform_explicit','state_level_mappable','accepted_species']:
        k=int(data.species_status.eq('Accepted species').sum()) if field=='accepted_species' else int(data[field].sum())
        n=len(data);metrics.append({'cohort':cohort,'metric':field,'numerator':k,'denominator':n,'percent':100*k/n,'wilson95':wilson(k,n)})
result={'status':'Working corpus after authorized historical Pending reconciliation; qualified coding and remaining coverage unresolved, not final results','entities':len(e),'articles':len(a),
 'temporal':{'periods':m.PERIODS,'totals':totals,'dimensions':rows,'scores':scores},'entity_metrics':metrics,
 'strongest_evidence_counts':e.strongest_biological_evidence_class.value_counts().sort_index().to_dict(),
 'contribution_counts':e.novelty_primary_group.value_counts().to_dict(),
 'family_counts':e.family_display.value_counts().to_dict(),
 'genome_completeness_counts':e.genome_completeness_standardized.value_counts().to_dict(),
 'all_temporal_fdr_nonsignificant':all(r['exact_q']>=.05 and r['trend_q']>=.05 for r in rows) and all(r['q']>=.05 for r in scores)}
(OUT/'recalculated_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Saved recalculated results; all temporal FDR nonsignificant:',result['all_temporal_fdr_nonsignificant'],flush=True)

expected=json.loads((ROOT/'reference/expected_results.json').read_text())
# Exact equality is expected with the recorded dependency versions and seeds.
if result != expected:
    raise SystemExit('Reproduction differs from the checked reference. Inspect results before use.')
report={'status':'PASS','exact_match_to_checked_reference':True,'articles':len(a),'entities':len(e),'article_entity_links':len(links),'dimensions':len(rows),'composite_scores':len(scores),'permutations_per_score':100000,'seeds':[x['seed'] for x in scores],'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'working_snapshot_not_final_corpus':True}
(OUT/'reproduction_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
