"""Shared helpers for Day 24 Phase A evaluation artifacts."""

from __future__ import annotations

import csv
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT_DIR / "phase-a"
DATA_DIR = ROOT_DIR / "data"

sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")


def ensure_phase_dir() -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_phase_dir()
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    ensure_phase_dir()
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def parse_contexts(value: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [value]


def dump_contexts(contexts: list[str]) -> str:
    return json.dumps(contexts, ensure_ascii=False)


def load_corpus_chunks(max_chars: int = 2200) -> list[dict[str, Any]]:
    """Load markdown corpus and return section-like chunks with metadata."""
    from src.m1_chunking import chunk_structure_aware, load_documents

    chunks: list[dict[str, Any]] = []
    for doc in load_documents(str(DATA_DIR)):
        source = doc.get("metadata", {}).get("source", "document")
        for chunk in chunk_structure_aware(doc.get("text", ""), metadata=doc.get("metadata", {})):
            text = re.sub(r"\n{3,}", "\n\n", chunk.text.strip())
            if not text:
                continue
            if len(text) <= max_chars:
                chunks.append({"text": text, "metadata": {**chunk.metadata, "source": source}})
                continue
            for idx, part in enumerate(split_long_text(text, max_chars=max_chars)):
                chunks.append({
                    "text": part,
                    "metadata": {**chunk.metadata, "source": source, "part": idx},
                })
    return chunks


def split_long_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    out: list[str] = []
    current: list[str] = []
    current_len = 0
    for para in paragraphs:
        if current and current_len + len(para) + 2 > max_chars:
            out.append("\n\n".join(current))
            current = []
            current_len = 0
        if len(para) > max_chars:
            for start in range(0, len(para), max_chars):
                out.append(para[start:start + max_chars].strip())
        else:
            current.append(para)
            current_len += len(para) + 2
    if current:
        out.append("\n\n".join(current))
    return [item for item in out if item]


def sample_context_sets(chunks: list[dict[str, Any]], total: int, seed: int = 24) -> list[list[dict[str, Any]]]:
    rng = random.Random(seed)
    if not chunks:
        raise RuntimeError("No corpus chunks found in data/*.md")

    simple_count = total // 2
    reasoning_count = total // 4
    multi_count = total - simple_count - reasoning_count
    labeled: list[tuple[str, list[dict[str, Any]]]] = []

    pool = chunks[:]
    rng.shuffle(pool)
    for i in range(simple_count):
        labeled.append(("simple", [pool[i % len(pool)]]))
    for i in range(reasoning_count):
        labeled.append(("reasoning", [pool[(i + simple_count) % len(pool)]]))
    for i in range(multi_count):
        first = pool[(i + simple_count + reasoning_count) % len(pool)]
        second = pool[(i * 3 + 7) % len(pool)]
        if second is first and len(pool) > 1:
            second = pool[(i * 3 + 8) % len(pool)]
        labeled.append(("multi_context", [first, second]))

    return [[{"evaluation_type": label, **item} for item in items] for label, items in labeled]


def openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=api_key)
    except Exception:
        return None


def chat_json(system: str, user: str, model_env: str = "OPENAI_EVAL_MODEL") -> dict[str, Any] | None:
    client = openai_client()
    if client is None:
        return None
    model = os.getenv(model_env, os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini"))
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:
        print(f"[warn] OpenAI JSON call failed: {exc}")
        return None


def fallback_question(context: str, evaluation_type: str, index: int) -> dict[str, str]:
    heading = ""
    for line in context.splitlines():
        line = line.strip("# -*\t ")
        if line:
            heading = line[:90]
            break
    sentence = re.split(r"(?<=[.!?])\s+|\n", context.strip())[0][:450]
    if evaluation_type == "multi_context":
        question = f"Cac thong tin lien quan trong cac doan tai lieu noi gi ve {heading.lower()}?"
    elif evaluation_type == "reasoning":
        question = f"Tu noi dung tai lieu, co the ket luan diem chinh nao ve {heading.lower()}?"
    else:
        question = f"{heading} la gi theo tai lieu?"
    return {
        "question": question,
        "ground_truth": sentence or context[:450],
    }
