# HTS plant-virus literature review in Brazil

Data and code accompanying the R1 revision of JPDP-D-26-01558, submitted to the Journal of Plant Diseases and Protection. This version records the revision dataset as of 24 October 2026: 65 articles, 129 entities and 139 article–entity links. Main and Secondary cohorts contain 77 and 52 entities.

## Contents

- `analysis/data/`: article reporting scores, a reduced entity table and article–entity links. DOI and article identifiers connect the tables to the source studies.
- `analysis/code/`: the preserved statistical functions, a reproducibility driver and the five figure-generation routines.
- `analysis/reference/`: the checked results used for comparison.
- `prioritization/`: the original dictionary classifier, dictionaries, per-record dictionary-presence features and the historical classification reference.
- `data_dictionary.md`: definitions, encoding and source qualifications.
- `verification.json` and `SHA256SUMS.txt`: verification of this snapshot and file integrity.

The journal supplement remains the detailed evidence and source-adjudication workbook. This repository provides the inputs and code needed for the numerical results and figures, without duplicating the manuscript, correspondence, reviewer reports or full-text articles.

## Reproduce

Use Python 3.12. Install the pinned packages from this repository root:

```sh
python -m pip install -r requirements.txt
python prioritization/code/reproduce_prioritization.py
python analysis/code/reproduce_analysis.py
python analysis/code/reproduce_figures.py
```

The three commands run offline after dependency installation. Outputs are written under each module's `results/` directory. Each of the three composite-score tests uses 100,000 permutations with the original seeds 20260807, 20260808 and 20260809. Analysis results must equal the checked reference. Five figures are regenerated as PNG and SVG; timestamps and identifiers in SVG files may differ between runs.

The prioritization replay checks 8,968 records across 25 stored output fields. It supplies the historical classifier with dictionary-membership answers extracted from the original metadata. Scores, caps, branch order and labels run through the unchanged original classifier. The raw third-party abstracts and affiliations are omitted. Thus this replay does not independently repeat source-text extraction. To classify a lawfully obtained original-format export, use `python prioritization/code/reproduce_prioritization.py --input /path/to/export.csv`.

## Interpretation

Reproduction checks calculations, not literature-search sensitivity or the correctness of every source extraction. The historical classifier forwarded 85 records and did not forward 8,883. Revision checks examined a 141-record historical queue; they did not validate the other 8,742 non-forwarded records. The supplementary current-index retrieval included 365 previously unlinked records subjected to initial metadata screening and directed checks, not universal full-text review. It does not reconstruct the historical capped query.

This release is a versioned revision snapshot, not a claim of an exhaustive census or completed independent author review of all proposed adjudications. Four directed cases remain outside the count because Brazilian material was not demonstrated, rather than because foreign provenance was established. The source qualifications in `data_dictionary.md` remain part of the interpretation.

The adjusted ordered trend for total-read reporting has q = 0.03686415646724539; its adjusted exact association test has q = 0.07740974179490541. These are separate tests. Positive biological-evidence fractions describe documented evidence, not experimental success rates.

## Citation and reuse

See `CITATION.cff` for this snapshot. No article DOI or acceptance is implied by the manuscript identifier. Cite the archived version DOI when available, otherwise cite the specific GitHub version.

Code is licensed under MIT. Original curated tables and documentation are licensed under CC BY 4.0. Bibliographic identifiers refer to third-party sources; no rights to the cited articles or omitted abstracts are granted. See `LICENSE.md` and `LICENSE-MIT`.
