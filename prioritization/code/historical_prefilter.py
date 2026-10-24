#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT
    / "04_candidate_inventory"
    / "literature_new_candidates_vs_pubmed.csv"
)

CLEAN_DIR = PROJECT / "03_cleaned_tables"
INVENTORY_DIR = PROJECT / "04_candidate_inventory"
RESULTS_DIR = PROJECT / "08_results"
LOG_DIR = PROJECT / "07_logs"

OUTPUT_ALL = CLEAN_DIR / "literature_expansion_prefiltered.csv"
OUTPUT_XLSX = CLEAN_DIR / "literature_expansion_prefiltered.xlsx"
OUTPUT_A = INVENTORY_DIR / "expansion_A_high_priority.csv"
OUTPUT_B = INVENTORY_DIR / "expansion_B_possible_candidates.csv"
OUTPUT_C = INVENTORY_DIR / "expansion_C_manual_review.csv"
OUTPUT_D = INVENTORY_DIR / "expansion_D_probable_irrelevant.csv"
OUTPUT_SUMMARY = RESULTS_DIR / "literature_expansion_prefilter_summary.csv"

BRAZIL_TERMS = [
    "brazil", "brasil", "brazilian", "brasileiro", "brasileira",
    "amazonas", "amazon", "cerrado", "pantanal", "mata atlantica",
    "sao paulo", "rio de janeiro", "minas gerais", "bahia", "parana",
    "rio grande do sul", "pernambuco", "ceara", "goias",
    "distrito federal", "brasilia", "espirito santo", "para",
]

BRAZIL_AFFILIATION_TERMS = [
    "brazil", "brasil", "embrapa", "universidade de sao paulo",
    "universidade federal", "instituto biologico", "fiocruz",
    "unicamp", "unesp", "ufv", "ufla", "ucb",
]

VIRUS_TERMS = [
    "virus", "viruses", "viral", "viroid", "viroids", "virome",
    "phytovirus", "rhabdovirus", "geminivirus", "begomovirus",
    "potyvirus", "closterovirus", "tospovirus", "orthotospovirus",
    "tenuivirus", "dichorhavirus", "carlavirus", "polerovirus",
    "enamovirus", "secovirus", "partitivirus", "mitovirus",
    "alphasatellite", "betasatellite", "deltasatellite",
]

PLANT_STRONG = [
    "plant virus", "plant viruses", "plant virome", "plant-associated virus",
    "plant associated virus", "virus infecting plants", "plant viral disease",
    "phytovirus", "phytovirome", "crop virus", "crop viruses",
]

PLANT_GENERAL = [
    "plant", "plants", "crop", "crops", "leaf", "leaves", "fruit",
    "fruits", "seed", "seeds", "tree", "trees", "root", "roots",
    "tuber", "tubers", "cultivar", "cultivars", "orchard", "weed",
    "weeds", "horticultural", "agricultural", "ornamental",
    "germplasm", "phytopathology", "host plant",
]

CROP_TERMS = [
    "arracacha", "arracacia", "tomato", "solanum lycopersicum",
    "potato", "solanum tuberosum", "pepper", "capsicum", "tobacco",
    "nicotiana", "citrus", "orange", "lemon", "lime", "bean",
    "phaseolus", "soybean", "glycine max", "maize", "corn", "zea mays",
    "wheat", "triticum", "rice", "oryza", "cassava", "manihot",
    "sugarcane", "saccharum", "cotton", "gossypium", "coffee",
    "coffea", "cacao", "cocoa", "theobroma", "banana", "musa",
    "papaya", "carica papaya", "pineapple", "ananas", "passion fruit",
    "passiflora", "grapevine", "grape", "vitis", "apple", "malus",
    "pear", "pyrus", "peach", "prunus", "strawberry", "fragaria",
    "melon", "cucumis melo", "cucumber", "cucumis sativus", "squash",
    "pumpkin", "cucurbita", "watermelon", "citrullus", "lettuce",
    "lactuca", "garlic", "allium", "onion", "carrot", "daucus",
    "brassica", "peanut", "arachis", "sunflower", "helianthus",
    "sweet potato", "ipomoea batatas", "yam", "dioscorea",
    "rubber tree", "hevea", "hovenia", "eucalyptus", "orchid",
    "sorghum", "barley", "hordeum", "oat", "avena",
]

HTS_TERMS = [
    "high-throughput sequencing", "high throughput sequencing",
    "next-generation sequencing", "next generation sequencing",
    "deep sequencing", "massively parallel sequencing", "rna-seq",
    "rna seq", "small rna sequencing", "small rna deep sequencing",
    "srna sequencing", "dsrna sequencing",
    "double-stranded rna sequencing", "metatranscriptomic",
    "metatranscriptomics", "viral metagenomics", "metagenomic sequencing",
    "virome analysis", "virome sequencing", "illumina", "nanopore",
    "oxford nanopore", "minion", "ion torrent", "454 sequencing",
    "transcriptome sequencing", "public rna-seq", "transcriptome mining",
]

NOVELTY_TERMS = [
    "novel virus", "novel viruses", "new virus", "new viruses",
    "novel viroid", "new viroid", "new species", "novel species",
    "tentative species", "putative novel", "previously undescribed",
    "previously unreported", "newly identified", "newly discovered",
    "virus discovery", "viral discovery", "potential new virus",
    "potentially new virus", "complete genome", "complete genomic sequence",
    "near-complete genome", "near complete genome", "first report",
    "first detection", "first identification", "characterization of a novel",
]

NONPLANT_TERMS = [
    "human", "patient", "hospital", "clinical sample", "bat", "rodent",
    "mouse", "mice", "rat", "mosquito", "aedes", "culex", "anopheles",
    "tick", "bird", "avian", "duck", "chicken", "pig", "swine",
    "cattle", "bovine", "sheep", "goat", "dog", "canine", "cat",
    "feline", "fish", "seal", "mammal", "animal virome",
    "insect-specific virus", "insect specific virus", "bacteriophage",
    "mycobacterium", "parasite", "nematode",
]

INDIRECT_TERMS = [
    "stool", "feces", "faeces", "fecal", "faecal", "gut virome",
    "sewage", "wastewater", "rainwater", "drinking water", "serum",
    "sera", "blood", "lung", "spleen", "brain", "saliva",
]

REVIEW_TYPES = [
    "review", "systematic review", "scoping review", "meta-analysis",
    "editorial", "comment", "perspective", "opinion",
]

CORRECTION_TYPES = [
    "correction", "corrigendum", "erratum", "retraction",
]


def normalize(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[-_/]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains(text: str, term: str) -> bool:
    target = normalize(term)
    if not target:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(target) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def matches(text: str, terms: Iterable[str]) -> list[str]:
    return sorted({term for term in terms if contains(text, term)})


def score_terms(
    title_text: str,
    abstract_text: str,
    terms: Iterable[str],
    title_weight: int,
    abstract_weight: int,
    cap: int,
) -> tuple[int, list[str], list[str]]:
    title_matches = matches(title_text, terms)
    abstract_matches = matches(abstract_text, terms)
    score = (
        len(title_matches) * title_weight
        + len(abstract_matches) * abstract_weight
    )
    return min(score, cap), title_matches, abstract_matches


def format_matches(title_hits: list[str], abstract_hits: list[str]) -> str:
    title_set = set(title_hits)
    abstract_only = [x for x in abstract_hits if x not in title_set]
    pieces = []
    if title_hits:
        pieces.append("TITLE: " + "; ".join(title_hits))
    if abstract_only:
        pieces.append("ABSTRACT: " + "; ".join(abstract_only))
    return " | ".join(pieces)


def classify(row: pd.Series) -> pd.Series:
    title = normalize(row.get("title", ""))
    abstract = normalize(row.get("abstract", ""))
    affiliations = normalize(row.get("affiliations", ""))
    country_codes = normalize(row.get("institution_country_codes", ""))
    publication_types = normalize(row.get("publication_types", ""))

    # Brazil in title/abstract is treated as evidence about study/sample context.
    brazil_score, br_t, br_a = score_terms(
        title, abstract, BRAZIL_TERMS, 4, 2, 16
    )
    brazil_affiliation_hits = matches(
        affiliations + " " + country_codes,
        BRAZIL_AFFILIATION_TERMS + ["br"],
    )
    brazil_affiliation_flag = bool(brazil_affiliation_hits)

    virus_score, vi_t, vi_a = score_terms(
        title, abstract, VIRUS_TERMS, 3, 1, 15
    )
    plant_strong_score, ps_t, ps_a = score_terms(
        title, abstract, PLANT_STRONG, 5, 3, 20
    )
    plant_general_score, pg_t, pg_a = score_terms(
        title, abstract, PLANT_GENERAL, 2, 1, 12
    )
    crop_score, cr_t, cr_a = score_terms(
        title, abstract, CROP_TERMS, 4, 2, 20
    )
    plant_score = plant_strong_score + plant_general_score + crop_score

    hts_score, ht_t, ht_a = score_terms(
        title, abstract, HTS_TERMS, 4, 2, 20
    )
    novelty_score, no_t, no_a = score_terms(
        title, abstract, NOVELTY_TERMS, 4, 2, 20
    )
    nonplant_score, np_t, np_a = score_terms(
        title, abstract, NONPLANT_TERMS, 4, 2, 24
    )
    indirect_score, in_t, in_a = score_terms(
        title, abstract, INDIRECT_TERMS, 5, 3, 20
    )

    review_hits = matches(
        title + " " + publication_types,
        REVIEW_TYPES,
    )
    correction_hits = matches(
        title + " " + publication_types,
        CORRECTION_TYPES,
    )

    is_review = bool(review_hits)
    is_correction = bool(correction_hits)
    has_abstract = bool(abstract)

    relevance = (
        brazil_score
        + virus_score
        + plant_score
        + hts_score
        + novelty_score
        - nonplant_score
        - indirect_score
    )

    # Strict, conservative expansion prefilter.
    if is_correction:
        cls = "D"
        label = "Probable irrelevant"
        reason = "Correction, erratum, corrigendum or retraction."

    elif is_review:
        cls = "C"
        label = "Supporting/manual review"
        reason = "Review/editorial-like record; useful mainly for citation chasing."

    elif (
        brazil_score >= 2
        and virus_score >= 2
        and plant_score >= 7
        and hts_score >= 4
        and novelty_score >= 4
        and nonplant_score <= 6
        and indirect_score <= 4
    ):
        cls = "A"
        label = "High priority"
        reason = (
            "Brazilian study/sample context plus strong plant, virus, HTS "
            "and novelty evidence."
        )

    elif (
        brazil_score >= 2
        and virus_score >= 2
        and plant_score >= 5
        and hts_score >= 2
        and novelty_score >= 2
        and nonplant_score <= 10
    ):
        cls = "B"
        label = "Possible candidate"
        reason = (
            "Relevant Brazilian plant-virus and sequencing signals, but "
            "manual confirmation is required."
        )

    elif (
        brazil_score >= 1
        and virus_score >= 2
        and plant_score >= 4
        and (hts_score >= 2 or novelty_score >= 2)
    ):
        cls = "C"
        label = "Manual review"
        reason = (
            "Partial eligibility evidence; sample origin, HTS role or "
            "novelty remains unclear."
        )

    elif (
        brazil_affiliation_flag
        and virus_score >= 2
        and plant_score >= 5
        and hts_score >= 2
        and novelty_score >= 2
    ):
        cls = "C"
        label = "Manual review"
        reason = (
            "Brazilian affiliation and relevant content, but Brazilian "
            "sample provenance is not evident from title/abstract."
        )

    else:
        cls = "D"
        label = "Probable irrelevant"
        reason = (
            "Insufficient combined evidence of Brazilian plant material, "
            "HTS-based discovery and viral novelty."
        )

    return pd.Series(
        {
            "expansion_class": cls,
            "expansion_label": label,
            "expansion_reason": reason,
            "expansion_relevance_score": relevance,
            "brazil_context_score": brazil_score,
            "brazil_affiliation_flag": "Yes" if brazil_affiliation_flag else "No",
            "virus_score": virus_score,
            "plant_score": plant_score,
            "hts_score": hts_score,
            "novelty_score": novelty_score,
            "nonplant_score": nonplant_score,
            "indirect_source_score": indirect_score,
            "abstract_available": "Yes" if has_abstract else "No",
            "review_flag": "Yes" if is_review else "No",
            "correction_flag": "Yes" if is_correction else "No",
            "matched_brazil_context": format_matches(br_t, br_a),
            "matched_brazil_affiliation": "; ".join(brazil_affiliation_hits),
            "matched_virus": format_matches(vi_t, vi_a),
            "matched_plant_strong": format_matches(ps_t, ps_a),
            "matched_plant_general": format_matches(pg_t, pg_a),
            "matched_crop_taxa": format_matches(cr_t, cr_a),
            "matched_hts": format_matches(ht_t, ht_a),
            "matched_novelty": format_matches(no_t, no_a),
            "matched_nonplant": format_matches(np_t, np_a),
            "matched_indirect_source": format_matches(in_t, in_a),
            "manual_decision": "",
            "manual_exclusion_reason": "",
            "manual_notes": "",
        }
    )


def excel_safe(frame: pd.DataFrame) -> pd.DataFrame:
    safe = frame.copy()
    for column in safe.columns:
        if safe[column].dtype == "object":
            safe[column] = safe[column].map(
                lambda x: x[:32767] if isinstance(x, str) else x
            )
    return safe


def main() -> None:
    for directory in [CLEAN_DIR, INVENTORY_DIR, RESULTS_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(
        INPUT_FILE,
        dtype={"pmid": str},
        keep_default_na=False,
        low_memory=False,
    )

    required = {"title"}
    missing = required.difference(df.columns)
    if missing:
        raise SystemExit(
            f"Required columns missing from input: {sorted(missing)}"
        )

    if "abstract" not in df.columns:
        df["abstract"] = ""

    classification = df.apply(classify, axis=1)
    result = pd.concat([df.reset_index(drop=True), classification], axis=1)

    order = pd.CategoricalDtype(
        categories=["A", "B", "C", "D"],
        ordered=True,
    )
    result["_class_order"] = result["expansion_class"].astype(order)
    result = result.sort_values(
        [
            "_class_order",
            "expansion_relevance_score",
            "publication_year",
            "title",
        ],
        ascending=[True, False, False, True],
        na_position="last",
    ).drop(columns="_class_order")

    subsets = {
        "A": result[result["expansion_class"] == "A"].copy(),
        "B": result[result["expansion_class"] == "B"].copy(),
        "C": result[result["expansion_class"] == "C"].copy(),
        "D": result[result["expansion_class"] == "D"].copy(),
    }

    result.to_csv(OUTPUT_ALL, index=False)
    subsets["A"].to_csv(OUTPUT_A, index=False)
    subsets["B"].to_csv(OUTPUT_B, index=False)
    subsets["C"].to_csv(OUTPUT_C, index=False)
    subsets["D"].to_csv(OUTPUT_D, index=False)

    summary = (
        result.groupby(["expansion_class", "expansion_label"], dropna=False)
        .size()
        .reset_index(name="records")
        .sort_values("expansion_class")
    )
    summary["percent"] = summary["records"] / len(result) * 100
    summary.to_csv(OUTPUT_SUMMARY, index=False)

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        excel_safe(result).to_excel(
            writer, sheet_name="All_records", index=False
        )
        excel_safe(subsets["A"]).to_excel(
            writer, sheet_name="A_high_priority", index=False
        )
        excel_safe(subsets["B"]).to_excel(
            writer, sheet_name="B_possible", index=False
        )
        excel_safe(subsets["C"]).to_excel(
            writer, sheet_name="C_manual_review", index=False
        )
        excel_safe(summary).to_excel(
            writer, sheet_name="Summary", index=False
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = {
        "run_utc": timestamp,
        "input_file": str(INPUT_FILE),
        "records_input": int(len(df)),
        "records_output": int(len(result)),
        "class_counts": {
            row["expansion_class"]: int(row["records"])
            for _, row in summary.iterrows()
        },
        "outputs": [
            str(OUTPUT_ALL), str(OUTPUT_XLSX), str(OUTPUT_A),
            str(OUTPUT_B), str(OUTPUT_C), str(OUTPUT_D),
            str(OUTPUT_SUMMARY),
        ],
        "warning": (
            "This is a conservative prioritization filter, not a final "
            "eligibility decision."
        ),
    }

    log_file = LOG_DIR / f"literature_expansion_prefilter_{timestamp}.json"
    log_file.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nEurope PMC expansion prefilter completed.")
    print(f"Input records: {len(df)}")
    print("\nClass summary:")
    print(
        summary.to_string(
            index=False,
            formatters={"percent": "{:.1f}".format},
        )
    )

    print("\nPriority records for manual inspection:")
    print(f"  A: {len(subsets['A'])}")
    print(f"  B: {len(subsets['B'])}")
    print(f"  C: {len(subsets['C'])}")
    print(f"  A+B+C: {len(subsets['A']) + len(subsets['B']) + len(subsets['C'])}")

    print("\nOutputs:")
    for path in log["outputs"] + [str(log_file)]:
        print(f"  - {path}")

    print(
        "\nIMPORTANT: D records remain stored and are not final exclusions."
    )


if __name__ == "__main__":
    main()
