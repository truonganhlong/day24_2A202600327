"""Analyze judge position and length bias observations."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from phase_b_common import PHASE_B_DIR, read_csv, safe_float, write_csv


def winner_length_delta(row: dict[str, str]) -> float:
    a_len = safe_float(row.get("answer_a_len"))
    b_len = safe_float(row.get("answer_b_len"))
    if row.get("winner") == "A":
        return a_len - b_len
    if row.get("winner") == "B":
        return b_len - a_len
    return 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairwise", default=str(PHASE_B_DIR / "judge_pairwise_results.csv"))
    parser.add_argument("--out", default=str(PHASE_B_DIR / "judge_bias_report.md"))
    parser.add_argument("--csv", default=str(PHASE_B_DIR / "judge_bias_observations.csv"))
    args = parser.parse_args()

    rows = read_csv(Path(args.pairwise))
    before = Counter(row.get("winner_before_swap", "tie") for row in rows)
    after = Counter(row.get("winner_after_swap", "tie") for row in rows)
    final = Counter(row.get("winner", "tie") for row in rows)
    inconsistent = [
        row for row in rows
        if row.get("winner_before_swap") != "tie"
        and row.get("winner_after_swap") != "tie"
        and row.get("winner_before_swap") == row.get("winner_after_swap")
    ]

    deltas = [winner_length_delta(row) for row in rows if row.get("winner") in {"A", "B"}]
    avg_winner_longer = sum(deltas) / len(deltas) if deltas else 0.0
    longer_wins = sum(1 for delta in deltas if delta > 0)
    length_bias_rate = longer_wins / len(deltas) if deltas else 0.0

    observation_rows = []
    for row in rows:
        observation_rows.append({
            "question_id": row.get("question_id", ""),
            "winner": row.get("winner", ""),
            "winner_before_swap": row.get("winner_before_swap", ""),
            "winner_after_swap": row.get("winner_after_swap", ""),
            "answer_a_len": row.get("answer_a_len", ""),
            "answer_b_len": row.get("answer_b_len", ""),
            "winner_length_delta": round(winner_length_delta(row), 2),
        })
    write_csv(
        Path(args.csv),
        observation_rows,
        [
            "question_id",
            "winner",
            "winner_before_swap",
            "winner_after_swap",
            "answer_a_len",
            "answer_b_len",
            "winner_length_delta",
        ],
    )

    lines = [
        "# Judge Bias Report",
        "",
        "## Bias 1: Position Bias",
        "",
        f"- First-pass winner counts: A={before.get('A', 0)}, B={before.get('B', 0)}, tie={before.get('tie', 0)}",
        f"- Swapped-pass positional winner counts: A={after.get('A', 0)}, B={after.get('B', 0)}, tie={after.get('tie', 0)}",
        f"- Final winner counts after swap reconciliation: A={final.get('A', 0)}, B={final.get('B', 0)}, tie={final.get('tie', 0)}",
        f"- Same-position winner after swap conflicts: {len(inconsistent)} / {len(rows)}",
        "",
        "Mitigation: use swap-and-average for every pairwise comparison and convert the swapped result back to original answer identity before deciding.",
        "",
        "## Bias 2: Length Bias",
        "",
        f"- Average winner length advantage: {avg_winner_longer:.2f} words",
        f"- Longer answer win rate among non-ties: {length_bias_rate:.2%}",
        "",
        "Mitigation: keep conciseness as an explicit rubric dimension and penalize unsupported extra detail.",
        "",
        "## Monitoring Decision",
        "",
        "- Keep both position and length checks as required diagnostics for each judge prompt/model update.",
        "- Re-run calibration when pairwise tie rate or swap conflicts change materially.",
    ]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[B4] wrote {args.out}")


if __name__ == "__main__":
    main()
