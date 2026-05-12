"""Pairwise LLM-as-judge with swap-and-average mitigation."""

from __future__ import annotations

import argparse
from pathlib import Path

from phase_b_common import (
    PHASE_B_DIR,
    chat_json,
    compact_text,
    heuristic_quality,
    normalize_winner,
    read_csv,
    write_csv,
)

PAIRWISE_SYSTEM = """You are a strict RAG answer evaluator.
Compare Answer A and Answer B for the same question.
Judge only on factual accuracy against the reference, relevance to the question, and conciseness.
Return JSON only: {"winner": "A"|"B"|"tie", "reason": "..."}."""


def judge_once(row: dict[str, str], answer_a: str, answer_b: str, use_llm: bool) -> tuple[str, str]:
    prompt = f"""Question:
{row['question']}

Reference answer:
{compact_text(row['ground_truth'], 1200)}

Answer A:
{compact_text(answer_a, 1400)}

Answer B:
{compact_text(answer_b, 1400)}"""
    payload = chat_json(PAIRWISE_SYSTEM, prompt, use_llm=use_llm)
    if payload:
        return normalize_winner(str(payload.get("winner", "tie"))), str(payload.get("reason", "")).strip()

    contexts = row.get("contexts", "")
    score_a = heuristic_quality(row["question"], answer_a, row["ground_truth"], contexts)
    score_b = heuristic_quality(row["question"], answer_b, row["ground_truth"], contexts)
    if abs(score_a - score_b) < 0.03:
        return "tie", f"heuristic tie: A={score_a:.3f}, B={score_b:.3f}"
    if score_a > score_b:
        return "A", f"heuristic A better: A={score_a:.3f}, B={score_b:.3f}"
    return "B", f"heuristic B better: A={score_a:.3f}, B={score_b:.3f}"


def reconcile(before: str, after_swapped_position: str) -> str:
    after_original = {"A": "B", "B": "A", "tie": "tie"}[after_swapped_position]
    if before == after_original:
        return before
    if before == "tie":
        return after_original
    if after_original == "tie":
        return before
    return "tie"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", default=str(PHASE_B_DIR / "answer_variants.csv"))
    parser.add_argument("--out", default=str(PHASE_B_DIR / "judge_pairwise_results.csv"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    rows = read_csv(Path(args.variants))[: args.limit]
    out_rows = []
    for i, row in enumerate(rows, 1):
        answer_a = row.get("answer_a", "")
        answer_b = row.get("answer_b", "")
        before, reason_before = judge_once(row, answer_a, answer_b, use_llm=not args.no_llm)
        after_swapped, reason_after = judge_once(row, answer_b, answer_a, use_llm=not args.no_llm)
        final = reconcile(before, after_swapped)
        out_rows.append({
            "question_id": row.get("question_id", i),
            "question": row.get("question", ""),
            "answer_a_name": row.get("answer_a_name", "A"),
            "answer_b_name": row.get("answer_b_name", "B"),
            "winner_before_swap": before,
            "winner_after_swap": after_swapped,
            "winner": final,
            "reason_before_swap": reason_before,
            "reason_after_swap": reason_after,
            "answer_a_len": len(answer_a.split()),
            "answer_b_len": len(answer_b.split()),
            "evaluation_type": row.get("evaluation_type", ""),
        })
        print(f"[B1] {i}/{len(rows)} winner={final}")

    write_csv(
        Path(args.out),
        out_rows,
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
    print(f"[B1] wrote {args.out}")


if __name__ == "__main__":
    main()
