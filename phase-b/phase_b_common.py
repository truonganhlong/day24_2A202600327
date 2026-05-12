"""Shared helpers for Day 24 Phase B judge calibration artifacts."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
PHASE_A_DIR = ROOT_DIR / "phase-a"
PHASE_B_DIR = ROOT_DIR / "phase-b"

sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")


def ensure_phase_dir() -> None:
    PHASE_B_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_phase_dir()
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


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


def compact_text(text: str, max_chars: int = 1800) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def tokenize(text: str) -> set[str]:
    return {tok.lower() for tok in re.findall(r"[\w]+", text or "", flags=re.UNICODE) if len(tok) > 2}


def lexical_overlap(candidate: str, reference: str) -> float:
    cand = tokenize(candidate)
    ref = tokenize(reference)
    if not cand or not ref:
        return 0.0
    return len(cand & ref) / len(ref)


def length_penalty(answer: str) -> float:
    words = len(re.findall(r"[\w]+", answer or "", flags=re.UNICODE))
    if words <= 0:
        return 0.0
    if 25 <= words <= 120:
        return 1.0
    if words < 25:
        return max(0.35, words / 25)
    return max(0.35, 1.0 - (words - 120) / 300)


def heuristic_quality(question: str, answer: str, ground_truth: str, contexts: str) -> float:
    relevance = lexical_overlap(answer, question)
    accuracy = lexical_overlap(answer, ground_truth)
    grounded = lexical_overlap(answer, contexts)
    concise = length_penalty(answer)
    return 0.40 * accuracy + 0.25 * grounded + 0.20 * relevance + 0.15 * concise


def score_to_1_5(value: float) -> int:
    return max(1, min(5, int(round(1 + value * 4))))


def openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=api_key)
    except Exception:
        return None


def chat_json(system: str, user: str, use_llm: bool = True) -> dict[str, Any] | None:
    if not use_llm:
        return None
    client = openai_client()
    if client is None:
        return None
    model = os.getenv("OPENAI_JUDGE_MODEL", os.getenv("OPENAI_EVAL_MODEL", "gpt-4o-mini"))
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:
        print(f"[warn] judge call failed: {exc}")
        return None


def normalize_winner(value: str) -> str:
    value = (value or "").strip().upper()
    if value in {"A", "ANSWER_A", "FIRST"}:
        return "A"
    if value in {"B", "ANSWER_B", "SECOND"}:
        return "B"
    return "tie"


def cohen_interpretation(kappa: float) -> str:
    if kappa < 0:
        return "worse than chance"
    if kappa < 0.2:
        return "slight agreement"
    if kappa < 0.4:
        return "fair agreement"
    if kappa < 0.6:
        return "moderate agreement"
    if kappa < 0.8:
        return "substantial agreement"
    return "almost perfect agreement"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return default if math.isnan(out) else out
    except Exception:
        return default
