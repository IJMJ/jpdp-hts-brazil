"""Functions and constants copied unchanged from the original temporal analysis.
Legacy absolute paths and the original 50-article entry point are omitted.
"""
from math import comb, erf, sqrt
import numpy as np
import pandas as pd

DIMS = [
    "total_read_count",
    "virus_supporting_read_count",
    "coverage_depth",
    "preprocessing_parameters",
    "assembly_parameters",
    "mapping_identification_parameters",
]

PERIODS = ["2017-2019", "2020-2022", "2023-2026"]

PERIOD_SCORES = [0.0, 1.0, 2.0]

SCORE_COLS = [
    "sequencing_evidence_score",
    "bioinformatics_reproducibility_score",
    "overall_reporting_score",
]

N_PERMUTATIONS = 100_000

RANDOM_SEED = 20260807

def normal_two_sided_p(z: float) -> float:
    """Two-sided p-value from standard normal without scipy."""
    cdf = 0.5 * (1.0 + erf(abs(z) / sqrt(2.0)))
    return max(0.0, min(1.0, 2.0 * (1.0 - cdf)))

def bh_adjust(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg FDR adjusted p-values."""
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adjusted = np.empty(n, dtype=float)

    running = 1.0
    for i in range(n - 1, -1, -1):
        idx = order[i]
        rank = i + 1
        value = p[idx] * n / rank
        running = min(running, value)
        adjusted[idx] = min(1.0, running)

    return adjusted.tolist()

def ffh_exact_3x2(successes: list[int], totals: list[int]) -> float:
    """
    Fisher-Freeman-Halton exact two-sided p-value for a 3x2 table,
    conditioning on all row totals and the total number of successes.

    Two-sided definition:
        sum probabilities of all tables with probability <= observed table.
    """
    if len(successes) != 3 or len(totals) != 3:
        raise ValueError("This implementation expects exactly three rows.")

    S = int(sum(successes))
    N = int(sum(totals))

    denominator = comb(N, S)
    observed_num = 1
    for n, x in zip(totals, successes):
        observed_num *= comb(int(n), int(x))
    observed_prob = observed_num / denominator

    p = 0.0

    n1, n2, n3 = [int(x) for x in totals]

    x1_min = max(0, S - n2 - n3)
    x1_max = min(n1, S)

    for x1 in range(x1_min, x1_max + 1):
        x2_min = max(0, S - x1 - n3)
        x2_max = min(n2, S - x1)

        for x2 in range(x2_min, x2_max + 1):
            x3 = S - x1 - x2

            if x3 < 0 or x3 > n3:
                continue

            numerator = (
                comb(n1, x1)
                * comb(n2, x2)
                * comb(n3, x3)
            )
            prob = numerator / denominator

            if prob <= observed_prob + 1e-15:
                p += prob

    return min(1.0, p)

def cochran_armitage(
    successes: list[int],
    totals: list[int],
    scores: list[float],
) -> tuple[float, float]:
    """
    Cochran-Armitage trend test using ordered group scores.
    Returns z statistic and two-sided p-value.
    """
    N = float(sum(totals))
    S = float(sum(successes))

    if S == 0 or S == N:
        return 0.0, 1.0

    p_hat = S / N

    weighted_score_mean = sum(
        n * w for n, w in zip(totals, scores)
    ) / N

    numerator = sum(
        w * (x - n * p_hat)
        for x, n, w in zip(successes, totals, scores)
    )

    variance_term = sum(
        n * (w - weighted_score_mean) ** 2
        for n, w in zip(totals, scores)
    )

    denominator = sqrt(
        p_hat * (1.0 - p_hat) * variance_term
    )

    if denominator == 0:
        return 0.0, 1.0

    z = numerator / denominator
    p_value = normal_two_sided_p(z)

    return float(z), float(p_value)

def rank_statistic(values: np.ndarray, groups: np.ndarray) -> float:
    """
    Kruskal-Wallis-style rank statistic.
    The tie-correction factor is constant across permutations and therefore
    not required for the empirical permutation p-value.
    """
    ranks = (
        pd.Series(values)
        .rank(method="average")
        .to_numpy(dtype=float)
    )

    N = len(values)
    H = 0.0

    for g in np.unique(groups):
        mask = groups == g
        n_g = int(mask.sum())
        mean_rank = float(ranks[mask].mean())
        H += n_g * (mean_rank - (N + 1.0) / 2.0) ** 2

    H *= 12.0 / (N * (N + 1.0))
    return float(H)

def permutation_rank_test(
    values: np.ndarray,
    groups: np.ndarray,
    n_permutations: int,
    seed: int,
) -> tuple[float, float]:
    observed = rank_statistic(values, groups)

    rng = np.random.default_rng(seed)
    extreme = 0

    for _ in range(n_permutations):
        perm_groups = rng.permutation(groups)
        stat = rank_statistic(values, perm_groups)

        if stat >= observed - 1e-12:
            extreme += 1

    p_value = (extreme + 1.0) / (n_permutations + 1.0)

    return observed, p_value
