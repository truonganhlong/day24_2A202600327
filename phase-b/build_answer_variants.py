"""Build two answer variants for LLM-as-judge comparison."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from phase_b_common import PHASE_A_DIR, PHASE_B_DIR, compact_text, parse_contexts, read_csv, write_csv


def extractive_baseline(contexts: list[str], ground_truth: str) -> str:
    if not contexts:
        return ""
    sentences: list[str] = []
    for context in contexts:
        sentences.extend([s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", context) if s.strip()])
    if not sentences:
        return compact_text(contexts[0], 700)

    gt_terms = {tok.lower() for tok in re.findall(r"[\w]+", ground_truth, flags=re.UNICODE) if len(tok) > 2}
    if not gt_terms:
        return compact_text(sentences[0], 700)

    ranked = sorted(
        sentences,
        key=lambda sent: len(gt_terms & {tok.lower() for tok in re.findall(r"[\w]+", sent, flags=re.UNICODE)}),
        reverse=True,
    )
    selected = [sent for sent in ranked[:3] if sent]
    return compact_text(" ".join(selected), 900)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", default=str(PHASE_A_DIR / "rag_answers.csv"))
    parser.add_argument("--out", default=str(PHASE_B_DIR / "answer_variants.csv"))
    args = parser.parse_args()

    rows = read_csv(Path(args.answers))
    out_rows = []
    for idx, row in enumerate(rows, 1):
        contexts = parse_contexts(row.get("contexts", ""))
        out_rows.append({
            "question_id": idx,
            "question": row.get("question", ""),
            "ground_truth": row.get("ground_truth", ""),
            "contexts": row.get("contexts", ""),
            "answer_a_name": "production_rag",
            "answer_a": row.get("answer", ""),
            "answer_b_name": "extractive_context_baseline",
            "answer_b": extractive_baseline(contexts, row.get("ground_truth", "")),
            "evaluation_type": row.get("evaluation_type", ""),
        })

    write_csv(
        Path(args.out),
        out_rows,
        [
            "question_id",
            "question",
            "ground_truth",
            "contexts",
            "answer_a_name",
            "answer_a",
            "answer_b_name",
            "answer_b",
            "evaluation_type",
        ],
    )
    print(f"[B0] wrote {args.out}")


if __name__ == "__main__":
    main()
