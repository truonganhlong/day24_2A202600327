"""Generate synthetic test set for Phase A."""

from __future__ import annotations

import argparse
from pathlib import Path

from phase_a_common import (
    PHASE_DIR,
    chat_json,
    dump_contexts,
    fallback_question,
    load_corpus_chunks,
    sample_context_sets,
    write_csv,
)


SYSTEM_PROMPT = """You generate Vietnamese RAG evaluation examples.
Return JSON only with keys: question, ground_truth.
The answer must be grounded strictly in the provided context.
Do not mention that you are using a context."""


def build_prompt(contexts: list[str], evaluation_type: str) -> str:
    if evaluation_type == "simple":
        instruction = "Create a direct factual question answerable from one context chunk."
    elif evaluation_type == "reasoning":
        instruction = "Create a question that requires light inference from the context, not outside knowledge."
    else:
        instruction = "Create a question that requires combining at least two context chunks."
    joined = "\n\n--- CONTEXT ---\n\n".join(contexts)
    return f"""Evaluation type: {evaluation_type}
Instruction: {instruction}

Context:
{joined}

Return:
{{"question": "...", "ground_truth": "..."}}"""


def generate_one(contexts: list[str], evaluation_type: str, index: int, use_llm: bool = True) -> dict[str, str]:
    if not use_llm:
        return fallback_question("\n\n".join(contexts), evaluation_type, index)
    payload = chat_json(SYSTEM_PROMPT, build_prompt(contexts, evaluation_type))
    if payload and payload.get("question") and payload.get("ground_truth"):
        return {
            "question": str(payload["question"]).strip(),
            "ground_truth": str(payload["ground_truth"]).strip(),
        }
    return fallback_question("\n\n".join(contexts), evaluation_type, index)


def write_review_notes(rows: list[dict[str, str]], path: Path) -> None:
    lines = [
        "# Test Set Review Notes",
        "",
        "Manual review sample: first 10 generated questions.",
        "",
        "| # | Type | Question | Review |",
        "|---|------|----------|--------|",
    ]
    for i, row in enumerate(rows[:10], 1):
        q = row["question"].replace("|", "\\|")
        lines.append(f"| {i} | {row['evaluation_type']} | {q} | pending manual review |")
    lines.extend([
        "",
        "Checks used before RAGAS:",
        "- Questions are answerable from the saved contexts.",
        "- Ground truths do not require outside knowledge.",
        "- Evaluation types cover simple, reasoning, and multi_context cases.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--out", default=str(PHASE_DIR / "test_set_v1.csv"))
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    chunks = load_corpus_chunks()
    context_sets = sample_context_sets(chunks, total=args.n)
    rows: list[dict[str, str]] = []

    for i, labeled_contexts in enumerate(context_sets, 1):
        evaluation_type = labeled_contexts[0]["evaluation_type"]
        contexts = [item["text"] for item in labeled_contexts]
        generated = generate_one(contexts, evaluation_type, i, use_llm=not args.no_llm)
        rows.append({
            "question": generated["question"],
            "ground_truth": generated["ground_truth"],
            "contexts": dump_contexts(contexts),
            "evaluation_type": evaluation_type,
        })
        print(f"[A1] {i}/{args.n} {evaluation_type}")

    out_path = Path(args.out)
    write_csv(out_path, rows, ["question", "ground_truth", "contexts", "evaluation_type"])
    write_review_notes(rows, PHASE_DIR / "test_set_review_notes.md")
    print(f"[A1] wrote {out_path}")


if __name__ == "__main__":
    main()
