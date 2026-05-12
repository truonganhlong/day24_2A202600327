"""Run RAGAS metrics for Phase A answers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from phase_a_common import PHASE_DIR, parse_contexts, read_csv, write_csv, write_json

METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def lexical_score(answer: str, reference: str) -> float:
    a = {tok.lower() for tok in answer.split() if len(tok) > 2}
    r = {tok.lower() for tok in reference.split() if len(tok) > 2}
    if not a or not r:
        return 0.0
    return len(a & r) / max(len(r), 1)


def fallback_eval(rows: list[dict[str, str]]) -> list[dict[str, float]]:
    scored = []
    for row in rows:
        overlap = lexical_score(row.get("answer", ""), row.get("ground_truth", ""))
        context_text = " ".join(parse_contexts(row.get("contexts", "")))
        support = lexical_score(row.get("answer", ""), context_text)
        scored.append({
            "faithfulness": min(1.0, support * 1.5),
            "answer_relevancy": min(1.0, overlap * 1.8),
            "context_precision": min(1.0, support * 1.2),
            "context_recall": min(1.0, lexical_score(row.get("ground_truth", ""), context_text) * 1.2),
        })
    return scored


def ragas_eval(rows: list[dict[str, str]]) -> list[dict[str, float]]:
    from src.m4_eval import evaluate_ragas

    results = evaluate_ragas(
        [row["question"] for row in rows],
        [row["answer"] for row in rows],
        [parse_contexts(row["contexts"]) for row in rows],
        [row["ground_truth"] for row in rows],
    )
    per_question = results.get("per_question", [])
    out: list[dict[str, float]] = []
    for item in per_question:
        out.append({metric: float(getattr(item, metric, 0.0) or 0.0) for metric in METRICS})
    return out


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    summary = {
        "num_questions": len(rows),
        "aggregate": {},
        "by_evaluation_type": {},
        "targets": {
            "faithfulness": 0.75,
            "answer_relevancy": 0.70,
            "context_precision": 0.60,
            "context_recall": 0.65,
        },
    }
    for metric in METRICS:
        values = [float(row[metric]) for row in rows]
        summary["aggregate"][metric] = round(sum(values) / len(values), 4) if values else 0.0

    types = sorted({row.get("evaluation_type", "") for row in rows})
    for eval_type in types:
        subset = [row for row in rows if row.get("evaluation_type") == eval_type]
        summary["by_evaluation_type"][eval_type] = {
            metric: round(sum(float(row[metric]) for row in subset) / len(subset), 4)
            for metric in METRICS
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", default=str(PHASE_DIR / "rag_answers.csv"))
    parser.add_argument("--out", default=str(PHASE_DIR / "ragas_results.csv"))
    parser.add_argument("--summary", default=str(PHASE_DIR / "ragas_summary.json"))
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--force-fallback", action="store_true")
    args = parser.parse_args()

    rows = read_csv(Path(args.answers))
    try:
        if args.force_fallback:
            raise RuntimeError("forced fallback")
        scores = ragas_eval(rows)
        source = "ragas"
        if args.allow_fallback and scores and all(
            all(float(score.get(metric, 0.0) or 0.0) == 0.0 for metric in METRICS)
            for score in scores
        ):
            raise RuntimeError("RAGAS returned all-zero scores")
    except Exception as exc:
        if not args.allow_fallback:
            raise
        print(f"[warn] RAGAS failed, using lexical fallback: {exc}")
        scores = fallback_eval(rows)
        source = "fallback"

    out_rows: list[dict[str, str | float]] = []
    for row, score in zip(rows, scores):
        clean_score = {
            metric: round(0.0 if math.isnan(score.get(metric, 0.0)) else float(score.get(metric, 0.0)), 4)
            for metric in METRICS
        }
        avg = round(sum(clean_score.values()) / len(METRICS), 4)
        out_rows.append({**row, **clean_score, "avg_score": avg, "metric_source": source})

    write_csv(
        Path(args.out),
        out_rows,
        [
            "question",
            "answer",
            "ground_truth",
            "contexts",
            "evaluation_type",
            "latency_ms",
            *METRICS,
            "avg_score",
            "metric_source",
        ],
    )
    summary = summarize(out_rows)
    summary["metric_source"] = source
    write_json(Path(args.summary), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
