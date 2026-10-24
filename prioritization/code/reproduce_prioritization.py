"""Replay historical dictionary-presence features, or classify a supplied raw CSV."""
import argparse, importlib.util, json, platform
from pathlib import Path
from functools import lru_cache
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('historical',ROOT/'code/historical_prefilter.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.normalize=lru_cache(maxsize=65536)(m.normalize)
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,help='Optional original-format CSV including title/abstract metadata. Not distributed.')
args=parser.parse_args()
expected=pd.read_csv(ROOT/'data/expected_classification.csv',dtype=str,keep_default_na=False).set_index('master_identity')
rows=[]
if args.input:
    records=pd.read_csv(args.input,dtype=str,keep_default_na=False)
    for _,r in records.iterrows():
        result=m.classify(r).to_dict();result['master_identity']=r['master_identity'];rows.append(result)
    mode='raw_text_reclassification'
else:
    with (ROOT/'data/term_presence.jsonl').open() as h:
        for line in h:
            feature=json.loads(line)
            # Adapt term membership only. All weights, caps, ordered branches,
            # labels and output formatting still run in the unchanged classifier.
            lookup={'titlefeature':set(feature['title']),
                    'abstractfeature':set(feature['abstract']),
                    'affiliationfeature':set(feature['affiliation']),
                    'titlefeature publicationfeature':set(feature['publication_context']),
                    '':set()}
            m.contains=lambda text,term: m.normalize(term) in lookup[text.strip()]
            r=pd.Series({'title':'titlefeature','abstract':'abstractfeature' if feature['has_abstract'] else '',
                         'affiliations':'affiliationfeature','publication_types':'publicationfeature'})
            result=m.classify(r).to_dict();result['master_identity']=feature['master_identity'];rows.append(result)
    mode='dictionary_presence_replay'
actual=pd.DataFrame(rows).set_index('master_identity')
assert actual.index.is_unique and expected.index.is_unique
assert len(actual)==len(expected)==8968 and set(actual.index)==set(expected.index)
actual=actual.loc[expected.index]
different=actual[list(expected.columns)].astype(str).ne(expected)
advanced=actual.expansion_class.isin(['A','B']) | ((actual.expansion_class=='C') & actual.expansion_label.eq('Manual review'))
report={'status':'PASS' if not different.any().any() else 'FAIL','mode':mode,'records':len(actual),
        'compared_fields':len(expected.columns),'different_cells':int(different.sum().sum()),
        'advanced_to_human_screening':int(advanced.sum()),'not_advanced':int((~advanced).sum()),
        'class_label_counts':[{'class':c,'label':l,'records':int(n)} for (c,l),n in actual.groupby(['expansion_class','expansion_label']).size().items()],
        'python':platform.python_version(),'pandas':pd.__version__,
        'scope':'Feature replay checks scoring and classification; omitted source-text extraction and screening sensitivity are not independently validated.'}
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'results/reproduction_report.json').write_text(json.dumps(report,indent=2)+'\n')
actual.loc[advanced].reset_index()[['master_identity','expansion_class','expansion_label']].to_csv(ROOT/'results/advanced_records.csv',index=False)
assert not different.any().any(),report
assert int(advanced.sum())==85
print(json.dumps(report,indent=2))
