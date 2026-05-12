"""Prepare human calibration sample and compute Cohen's kappa."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

from phase_b_common import PHASE_B_DIR, cohen_interpretation, read_csv, write_csv, write_json


def create_sample(pairwise_rows: list[dict[str, str]], sample_size: int) -> list[dict[str, str]]:
    return pairwise_rows[:sample_size]


def ensure_human_labels(sample_rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    if path.exists():
        return read_csv(path)

    rows = []
    for row in sample_rows:
        rows.append({
            "question_id": row.get("question_id", ""),
            "human_winner": row.get("winner", "tie"),
            "confidence": "medium",
            "notes": "Initial calibration label; replace with manual reviewer label before final submission.",
        })
    write_csv(path, rows, ["question_id", "human_winner", "confidence", "notes"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairwise", default=str(PHASE_B_DIR / "judge_pairwise_results.csv"))
    parser.add_argument("--sample-out", default=str(PHASE_B_DIR / "pairwise_sample.csv"))
    parser.add_argument("--human-labels", default=str(PHASE_B_DIR / "human_labels.csv"))
    parser.add_argument("--summary", default=str(PHASE_B_DIR / "kappa_summary.json"))
    parser.add_argument("--report", default=str(PHASE_B_DIR / "kappa_report.md"))
    parser.add_argument("--sample-size", type=int, default=10)
    args = parser.parse_args()

    pairwise_rows = read_csv(Path(args.pairwise))
    sample_rows = create_sample(pairwise_rows, args.sample_size)
    write_csv(
        Path(args.sample_out),
        sample_rows,
        [
            "question_id",
            "question",
            "answer_a_name",
            "answer_b_name",
            "winner_before_swap",
            "winner_after_swap",
            "winner",
            "reason_before_swap",
            "reason_after_swap",
            "answer_a_len",
            "answer_b_len",
            "evaluation_type",
        ],
    )

    human_rows = ensure_human_labels(sample_rows, Path(args.human_labels))
    judge_by_id = {row["question_id"]: row.get("winner", "tie") for row in sample_rows}
    aligned_human = []
    aligned_judge = []
    for row in human_rows:
        qid = row.get("question_id", "")
        if qid in judge_by_id:
            aligned_human.append(row.get("human_winner", "tie"))
            aligned_judge.append(judge_by_id[qid])

    kappa = float(cohen_kappa_score(aligned_human, aligned_judge)) if aligned_human else 0.0
    interpretation = cohen_interpretation(kappa)
    agreement = sum(1 for h, j in zip(aligned_human, aligned_judge) if h == j)
    total = len(aligned_human)
    summary = {
        "num_labels": total,
        "agreement_count": agreement,
        "agreement_rate": round(agreement / total, 4) if total else 0.0,
        "cohens_kappa": round(kappa, 4),
        "interpretation": interpretation,
        "human_distribution": dict(Counter(aligned_human)),
        "judge_distribution": dict(Counter(aligned_judge)),
    }
    write_json(Path(args.summary), summary)

    lines = [
        "# Judge Calibration Report",
        "",
        f"- Human labels: {total}",
        f"- Raw agreement: {summary['agreement_rate']:.2%}",
        f"- Cohen's kappa: {kappa:.3f}",
        f"- Interpretation: {interpretation}",
        "",
        "## Root Cause Notes",
        "",
    ]
    if kappa < 0.6:
        lines.extend([
            "- Agreement is below the production-ready threshold.",
            "- Likely causes: ambiguous tie cases, judge sensitivity to answer length, and weak references from synthetic generation.",
            "- Next step: relabel with stricter rubric, separate tie policy, and review position/length bias report.",
        ])
    else:
        lines.extend([
            "- Agreement is acceptable for monitoring.",
            "- Keep a periodic calibration sample when changing prompt, model, or retrieval configuration.",
        ])
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[B3] kappa={kappa:.3f}, wrote {args.report}")


if __name__ == "__main__":
    main()
