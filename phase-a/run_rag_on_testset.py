"""Run the Day 18 RAG pipeline on Phase A test questions."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from phase_a_common import PHASE_DIR, dump_contexts, load_corpus_chunks, openai_client, read_csv, write_csv


class LightRAG:
    """BM25-backed fallback that reuses Day 18 chunking/search primitives."""

    def __init__(self, use_llm: bool = True) -> None:
        from src.m2_search import BM25Search

        chunks = load_corpus_chunks(max_chars=1600)
        self.searcher = BM25Search()
        self.searcher.index(chunks)
        self.client = openai_client() if use_llm else None

    def run_query(self, query: str) -> tuple[str, list[str]]:
        results = self.searcher.search(query, top_k=3)
        contexts = [r.text for r in results]
        if not contexts:
            return "Khong tim thay.", []
        if self.client is None:
            return contexts[0][:700], contexts

        prompt = (
            "Tra loi ngan gon bang tieng Viet, chi dua tren context. "
            "Neu context khong co thong tin thi noi 'Khong tim thay.'"
        )
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Context:\n{chr(10).join(contexts)}\n\nCau hoi: {query}"},
            ],
            temperature=0,
            max_completion_tokens=300,
        )
        return response.choices[0].message.content.strip(), contexts


def build_runner(mode: str, use_llm: bool = True):
    if mode == "light":
        return LightRAG(use_llm=use_llm).run_query

    if mode in {"auto", "full"}:
        try:
            from src.pipeline import build_pipeline, run_query

            search, reranker = build_pipeline()
            return lambda question: run_query(question, search, reranker)
        except Exception as exc:
            if mode == "full":
                raise
            print(f"[warn] full pipeline unavailable, using light runner: {exc}")
            return LightRAG(use_llm=use_llm).run_query

    raise ValueError(f"Unknown mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-set", default=str(PHASE_DIR / "test_set_v1.csv"))
    parser.add_argument("--out", default=str(PHASE_DIR / "rag_answers.csv"))
    parser.add_argument("--mode", choices=["auto", "full", "light"], default="auto")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    rows = read_csv(Path(args.test_set))
    if args.limit:
        rows = rows[: args.limit]

    run_query = build_runner(args.mode, use_llm=not args.no_llm)
    out_rows: list[dict[str, str | float]] = []
    for i, row in enumerate(rows, 1):
        start = time.perf_counter()
        answer, retrieved_contexts = run_query(row["question"])
        latency_ms = (time.perf_counter() - start) * 1000
        contexts = retrieved_contexts or []
        out_rows.append({
            "question": row["question"],
            "answer": answer,
            "ground_truth": row["ground_truth"],
            "contexts": dump_contexts(contexts),
            "evaluation_type": row.get("evaluation_type", ""),
            "latency_ms": round(latency_ms, 2),
        })
        print(f"[RAG] {i}/{len(rows)} {latency_ms:.0f}ms")

    write_csv(
        Path(args.out),
        out_rows,
        ["question", "answer", "ground_truth", "contexts", "evaluation_type", "latency_ms"],
    )
    print(f"[RAG] wrote {args.out}")


if __name__ == "__main__":
    main()
