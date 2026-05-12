"""Build bottom-question failure cluster analysis for Phase A."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from phase_a_common import PHASE_DIR, read_csv

METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def diagnose(row: dict[str, str]) -> tuple[str, str]:
    scores = {metric: float(row.get(metric, 0.0) or 0.0) for metric in METRICS}
    worst_metric = min(scores, key=scores.get)
    eval_type = row.get("evaluation_type", "")

    if worst_metric == "context_recall" or eval_type == "multi_context":
        return "Missing relevant chunks", "Increase retrieval top_k, use parent context, and add multi-hop query expansion."
    if worst_metric == "context_precision":
        return "Off-topic retrievals", "Tune hybrid weights and rerank more candidates before selecting final contexts."
    if worst_metric == "faithfulness":
        return "Answer not fully grounded", "Tighten system prompt, quote context spans, and return unknown when evidence is missing."
    return "Answer not aligned with question", "Use a stricter answer template and include the user question in final verification."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(PHASE_DIR / "ragas_results.csv"))
    parser.add_argument("--out", default=str(PHASE_DIR / "failure_analysis.md"))
    parser.add_argument("--bottom-n", type=int, default=10)
    args = parser.parse_args()

    rows = read_csv(Path(args.results))
    rows = sorted(rows, key=lambda row: float(row.get("avg_score", 0.0) or 0.0))
    bottom = rows[: args.bottom_n]

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    enriched = []
    for row in bottom:
        diagnosis, fix = diagnose(row)
        clusters[diagnosis].append(row)
        enriched.append((row, diagnosis, fix))

    lines = [
        "# Failure Cluster Analysis",
        "",
        "## Bottom 10 Questions",
        "",
        "| # | Question | Type | F | AR | CP | CR | Avg | Diagnosis |",
        "|---|----------|------|---|----|----|----|-----|-----------|",
    ]
    for i, (row, diagnosis, _) in enumerate(enriched, 1):
        q = row["question"].replace("|", "\\|")[:120]
        lines.append(
            f"| {i} | {q} | {row.get('evaluation_type', '')} | "
            f"{float(row.get('faithfulness', 0)):.2f} | {float(row.get('answer_relevancy', 0)):.2f} | "
            f"{float(row.get('context_precision', 0)):.2f} | {float(row.get('context_recall', 0)):.2f} | "
            f"{float(row.get('avg_score', 0)):.2f} | {diagnosis} |"
        )

    lines.extend(["", "## Clusters Identified", ""])
    for idx, (cluster, items) in enumerate(clusters.items(), 1):
        examples = "; ".join(item["question"][:80] for item in items[:2])
        _, fix = diagnose(items[0])
        lines.extend([
            f"### Cluster C{idx}: {cluster}",
            "",
            f"- Count: {len(items)}",
            f"- Pattern: {examples}",
            f"- Root cause: weakest observed metric and query type indicate `{cluster.lower()}`.",
            f"- Proposed technical fix: {fix}",
            "",
        ])

    lines.extend([
        "## Next Actions",
        "",
        "1. Re-run retrieval with larger candidate set before reranking.",
        "2. Preserve parent chunks as generation context for legal and financial sections.",
        "3. Add an answer verifier that checks whether the answer is supported by retrieved contexts.",
    ])
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[A3] wrote {args.out}")


if __name__ == "__main__":
    main()
