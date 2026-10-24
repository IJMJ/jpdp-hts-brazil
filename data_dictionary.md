# Data definitions and source qualifications

## Analysis tables

Each CSV has one header row and UTF-8 encoding. Empty fields mean unavailable or not applicable, not zero. Identifiers are strings. Binary analytical flags use 0 and 1. Published counts use the supplied flags; absence of documented evidence is not proof that an experiment was never attempted.

`article_reporting_scores_R1_working.csv` has one row per article. `article_id` joins to the link table; `DOI` and `citation` identify the publication. `year` is the publication year and `period` is 2016–2019, 2020–2022 or 2023–2026. Six reporting dimensions cover total reads, virus-supporting reads, coverage depth, preprocessing parameters, assembly parameters and mapping/identification parameters. A `_reported` flag equals 1 exactly when the corresponding categorical field equals `REPORTED`. The first three flags sum to `sequencing_evidence_score`, the last three to `bioinformatics_reproducibility_score`, and all six to `overall_reporting_score`. Zero flags include all other categorical statuses.

`article_entity_links_R1_working.csv` has one row per article–entity link, with `article_id`, `entity_id`, contribution `role` and source `doi`. Articles can contribute multiple entities; an entity can link to multiple articles. Do not sum links as distinct entities.

`entity_master_R1_coverage_working.csv` has one row per distinct inventory entity. `master_entity_id` joins to link-table `entity_id`. `master_article_id` names the primary characterization source. Reported and final entity names are retained separately; neither guarantees an accepted ICTV species. `cohort` is Main or Secondary under the manuscript criteria. Source identifiers and accepted primary sequence accession identifiers are bibliographic references only; no sequence data are distributed.

Host and geography fields preserve the curated categories and resolution; no country or state is inferred from author affiliation. `publication_year_numeric` is the primary characterization year. `species_status`, `family_display` and `order_display` preserve formal taxonomy and unresolved categories. `novelty_primary_group` is the curated primary contribution. `genome_completeness_standardized` separates complete/coding-complete, near-complete and partial/contig evidence. The complete/coding-complete binary flag excludes near-complete records.

`strongest_biological_evidence_class` records B0, HTS evidence; B1, molecular validation; B2, replicated association; B3, experimental infection; B4, disease reproduction; or B5, reconstructed-agent evidence. Cumulative analytical flags are `molecular_validation_or_higher`, `replicated_association_or_higher` and `experimental_infection_or_higher`. Direct milestone flags are `experimental_disease_reproduction` and `reconstructed_agent_direct`; they are retained separately from the strongest class. `has_public_raw_reads`, `hts_platform_explicit` and `state_level_mappable` indicate confirmed public reads, explicit platform reporting and usable state-level geography. Read-availability flags reflect the audit snapshot, not permanent repository status.

## Source qualifications

- The 2016 H086 article remains eligible under the submitted scope, which had no lower publication-year cutoff. Its early-online date was 2015. The first analytical interval explicitly includes 2016; statistical tests and seeds are preserved.
- H124 reference genomes are not new complete genomes from that study. Its focal contribution remains conservatively coded as partial/contig evidence.
- H127 retains the source's differing sequence-length statements without inventing an explanation. Inventory units are identifiable study virus/isolate groups, not each assembled contig.
- H012 contributes contextual discussion without an added inventory unit; isolate identity across publications is not established merely by a shared name.
- Unresolved identity labels in the Oliveira source are not treated as additional distinct entities.
- Four directed cases, H034, H036, H133 and L02-007, are outside the counted set because Brazilian provenance was not demonstrated. Missing origin metadata are not proof of foreign origin.
- The detailed source evidence, taxonomic decisions and qualifications are documented in the journal supplement. The reduced entity table omits internal work queues, sign-off fields, copied quotations and operational notes; retained analytical cells are unchanged.

## Prioritization inputs

`term_presence.jsonl` has one JSON record per historical candidate. `master_identity` joins to `expected_classification.csv`; DOI, PMID and source identifiers identify the bibliographic record where available. `title`, `abstract`, `affiliation` and `publication_context` are lists of normalized dictionary terms matched in the original field, not source text. `publication_context` matches normalized title followed by publication types. `affiliation` matches affiliations followed by country-code metadata; country codes were absent from this historical input. `has_abstract` records whether the normalized original abstract was nonempty. Dictionary lists retain the original spellings and overlaps. There are 309 stored entries plus the literal runtime affiliation token `br`; this is not a count of 310 distinct normalized words.

The 25 reference fields contain the classification, label, reason, component and total scores, flags and formatted matches. Formatted matches omit abstract hits already present in the title, whereas component scoring counts both fields. The presence input therefore retains title and abstract matches separately. Branches use the first satisfied condition. A, B and C labelled exactly `Manual review` advance; C labelled `Supporting/manual review` does not. No summed-score advancement cutoff is applied. The original classifier contains the precise weights, caps and ordered conditions.
