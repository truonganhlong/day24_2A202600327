"""Output guardrail with optional Llama Guard API and deterministic fallback."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import requests

from phase_c_common import Timer, contains_any


@dataclass
class OutputGuardResult:
    safe: bool
    text: str
    reason: str = ""
    categories: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    provider: str = "heuristic"


class OutputGuard:
    def __init__(self, use_api: bool = True) -> None:
        self.use_api = use_api
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("LLAMA_GUARD_MODEL", "llama-guard-3-8b")
        self.endpoint = os.getenv("GROQ_CHAT_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions")
        self.unsafe_keywords = [
            "kill yourself",
            "tu tu",
            "tu sat",
            "che tao bom",
            "make a bomb",
            "hack password",
            "steal credit card",
            "malware",
            "phishing",
            "medical advice",
            "ignore legal requirements",
            "sell personal data",
            "mua ban du lieu ca nhan",
        ]

    def check(self, user_input: str, response: str) -> OutputGuardResult:
        with Timer() as timer:
            if self.use_api and self.groq_api_key:
                api_result = self._check_groq(user_input, response)
                if api_result is not None:
                    api_result.latency_ms = timer.ms
                    return api_result
            fallback = self._heuristic_check(user_input, response)
        fallback.latency_ms = timer.ms
        return fallback

    def _check_groq(self, user_input: str, response: str) -> OutputGuardResult | None:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"User: {user_input}\nAssistant: {response}",
                }
            ],
            "temperature": 0,
            "max_tokens": 80,
        }
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].lower()
            safe = content.startswith("safe") or "unsafe" not in content
            cats = re.findall(r"s\d+", content)
            return OutputGuardResult(safe=safe, text=response, reason=content[:300], categories=cats, provider="llama_guard_api")
        except Exception as exc:
            print(f"[warn] Llama Guard API failed: {exc}")
            return None

    def _heuristic_check(self, user_input: str, response: str) -> OutputGuardResult:
        joined = f"{user_input}\n{response}".lower()
        categories: list[str] = []
        if contains_any(joined, self.unsafe_keywords):
            categories.append("unsafe_keyword")
        if re.search(r"\b(?:sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,})\b", joined):
            categories.append("credential_leak")
        if re.search(r"(?:\d[ -]*?){13,19}", joined):
            categories.append("payment_or_identifier")
        if "khong tim thay" in response.lower() or "không tìm thấy" in response.lower():
            pass

        safe = not categories
        reason = "safe" if safe else "unsafe: " + ", ".join(categories)
        return OutputGuardResult(safe=safe, text=response, reason=reason, categories=categories, provider="heuristic")
