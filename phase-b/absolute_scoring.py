"""Absolute LLM-as-judge scoring with a 4-dimension rubric."""

from __future__ import annotations

import argparse
from pathlib import Path

from phase_b_common import (
    PHASE_B_DIR,
    chat_json,
    compact_text,
    heuristic_quality,
    lexical_overlap,
    length_penalty,
    read_csv,
    score_to_1_5,
    write_csv,
)

ABSOLUTE_SYSTEM = """You are a strict RAG answer evaluator.
Score the answer on 4 dimensions, each from 1 to 5:
accuracy: factually correct against the reference
relevance: answers the user's question
conciseness: appropriately brief without useless text
helpfulness: clear and useful to the user
Return JSON only:
{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "rationale": "..."}."""


def score_answer(row: dict[str, str], system_name: str, answer: str, use_llm: bool) -> dict[str, str | int | float]:
    prompt = f"""Question:
{row['question']}

Reference answer:
{compact_text(row['ground_truth'], 1200)}

System answer:
{compact_text(answer, 1600)}"""
    payload = chat_json(ABSOLUTE_SYSTEM, prompt, use_llm=use_llm)
    if payload:
        scores = {
            "accuracy": max(1, min(5, int(payload.get("accuracy", 1)))),
            "relevance": max(1, min(5, int(payload.get("relevance", 1)))),
            "conciseness": max(1, min(5, int(payload.get("conciseness", 1)))),
            "helpfulness": max(1, min(5, int(payload.get("helpfulness", 1)))),
            "rationale": str(payload.get("rationale", "")),
        }
    else:
        contexts = row.get("contexts", "")
        scores = {
            "accuracy": score_to_1_5(lexical_overlap(answer, row.get("ground_truth", ""))),
            "relevance": score_to_1_5(lexical_overlap(answer, row.get("question", ""))),
            "conciseness": score_to_1_5(length_penalty(answer)),
            "helpfulness": score_to_1_5(heuristic_quality(row.get("question", ""), answer, row.get("ground_truth", ""), contexts)),
            "rationale": "heuristic rubric fallback",
        }

    overall = round(
        (scores["accuracy"] + scores["relevance"] + scores["conciseness"] + scores["helpfulness"]) / 4,
        3,
    )
    return {
        "question_id": row.get("question_id", ""),
        "question": row.get("question", ""),
        "system": system_name,
        "answer": answer,
        "accuracy": scores["accuracy"],
        "relevance": scores["relevance"],
        "conciseness": scores["conciseness"],
        "helpfulness": scores["helpfulness"],
        "overall": overall,
        "rationale": scores["rationale"],
        "evaluation_type": row.get("evaluation_type", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", default=str(PHASE_B_DIR / "answer_variants.csv"))
    parser.add_argument("--out", default=str(PHASE_B_DIR / "absolute_scores.csv"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    rows = read_csv(Path(args.variants))[: args.limit]
    out_rows = []
    for i, row in enumerate(rows, 1):
        out_rows.append(score_answer(row, row.get("answer_a_name", "A"), row.get("answer_a", ""), use_llm=not args.no_llm))
        out_rows.append(score_answer(row, row.get("answer_b_name", "B"), row.get("answer_b", ""), use_llm=not args.no_llm))
        print(f"[B2] {i}/{len(rows)}")

    write_csv(
        Path(args.out),
        out_rows,
        [
            "question_id",
            "question",
            "system",
            "answer",
            "accuracy",
            "relevance",
            "conciseness",
            "helpfulness",
            "overall",
            "rationale",
            "evaluation_type",
        ],
    )
    print(f"[B2] wrote {args.out}")


if __name__ == "__main__":
    main()
