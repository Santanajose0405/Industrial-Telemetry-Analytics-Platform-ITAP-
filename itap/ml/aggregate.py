from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class AggregateSummary:
    group_key: str
    n_flagged: int
    avg_score: float
    p95_score: float
    top_families: List[Tuple[str, float]]  # [(family, pct), ...]


def _normalize_family_totals(family_totals: Dict[str, float]) -> Dict[str, float]:
    total = float(sum(family_totals.values()))
    if total <= 0.0:
        return {k: 0.0 for k in family_totals}
    return {k: (v / total) * 100.0 for k, v in family_totals.items()}


def aggregate_explanations(
    *,
    rows: pd.DataFrame,
    family_totals_col: str = "family_totals",
    group_by: str = "device_id",
    score_col: str = "score",
    top_k_families: int = 5,
) -> List[AggregateSummary]:
    if rows.empty:
        return []

    if family_totals_col not in rows.columns:
        raise ValueError(f"Expected '{family_totals_col}' column on rows.")

    summaries: List[AggregateSummary] = []

    for key, g in rows.groupby(group_by, dropna=False):
        merged: Dict[str, float] = {}

        for d in g[family_totals_col]:
            if not isinstance(d, dict):
                continue
            for fam, pct in d.items():
                merged[fam] = merged.get(fam, 0.0) + float(pct)

        merged = _normalize_family_totals(merged)
        top = sorted(merged.items(), key=lambda kv: kv[1], reverse=True)[:top_k_families]

        scores = pd.to_numeric(g[score_col], errors="coerce").fillna(0.0).to_numpy()
        avg_score = float(np.mean(scores)) if len(scores) else 0.0
        p95_score = float(np.percentile(scores, 95)) if len(scores) else 0.0

        summaries.append(
            AggregateSummary(
                group_key=str(key),
                n_flagged=int(len(g)),
                avg_score=avg_score,
                p95_score=p95_score,
                top_families=[(k, float(v)) for k, v in top],
            )
        )

    summaries.sort(key=lambda s: (s.n_flagged, s.p95_score), reverse=True)
    return summaries


def print_aggregate_summaries(
    title: str,
    summaries: List[AggregateSummary],
    top_n: int = 10,
) -> None:
    print(f"\n{title}")
    if not summaries:
        print("(no results)")
        return

    for s in summaries[:top_n]:
        fam_str = ", ".join([f"{k}={v:.1f}%" for k, v in s.top_families])
        print(
            f"- {s.group_key} | n={s.n_flagged} | avg_score={s.avg_score:.4f} | p95={s.p95_score:.4f} | {fam_str}"
        )


def summaries_to_json(summaries: List[AggregateSummary]) -> List[dict]:
    return [asdict(s) for s in summaries]
