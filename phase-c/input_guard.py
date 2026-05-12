"""Input guardrails: PII redaction, topic validation, and injection defense."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from phase_c_common import Timer, contains_any, normalize


@dataclass
class GuardResult:
    ok: bool
    text: str
    reason: str = ""
    findings: list[str] = field(default_factory=list)
    latency_ms: float = 0.0


VN_REGEX_PATTERNS: dict[str, re.Pattern[str]] = {
    "VN_PHONE": re.compile(r"(?<!\d)(?:\+?84|0)(?:\s|\.)?(?:3|5|7|8|9)(?:[\s.-]?\d){8}(?!\d)"),
    "VN_CCCD": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "VN_CMND": re.compile(r"(?<!\d)\d{9}(?!\d)"),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "CREDIT_CARD": re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"),
    "TAX_CODE": re.compile(r"(?<!\d)\d{10}(?:-\d{3})?(?!\d)"),
}


class InputGuard:
    def __init__(self) -> None:
        self.presidio_analyzer = None
        self.presidio_anonymizer = None
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self.presidio_analyzer = AnalyzerEngine()
            self.presidio_anonymizer = AnonymizerEngine()
        except Exception:
            self.presidio_analyzer = None
            self.presidio_anonymizer = None

    def scrub_pii(self, text: str) -> GuardResult:
        with Timer() as timer:
            if text is None:
                text = ""
            sanitized = str(text)
            findings: list[str] = []

            if self.presidio_analyzer and self.presidio_anonymizer and sanitized:
                try:
                    results = self.presidio_analyzer.analyze(text=sanitized, language="en")
                    if results:
                        anonymized = self.presidio_anonymizer.anonymize(text=sanitized, analyzer_results=results)
                        sanitized = anonymized.text
                        findings.extend(sorted({result.entity_type for result in results}))
                except Exception:
                    pass

            for label, pattern in VN_REGEX_PATTERNS.items():
                if pattern.search(sanitized):
                    findings.append(label)
                    sanitized = pattern.sub(f"[REDACTED_{label}]", sanitized)

            findings = sorted(set(findings))
        return GuardResult(ok=True, text=sanitized, findings=findings, latency_ms=timer.ms)


class TopicGuard:
    def __init__(self, allowed_topics: list[str] | None = None) -> None:
        self.allowed_topics = allowed_topics or [
            "du lieu ca nhan",
            "bao ve du lieu",
            "nghi dinh 13",
            "thue",
            "gtgt",
            "bctc",
            "tai chinh",
            "ke khai",
            "rag",
            "guardrail",
        ]
        self.block_keywords = [
            "bong da",
            "nau an",
            "du lich",
            "game",
            "crypto trading",
            "viet tho",
            "phim",
            "weather",
            "football",
            "recipe",
            "dating",
        ]

    def check(self, text: str) -> GuardResult:
        with Timer() as timer:
            norm = normalize(text).lower()
            if not norm:
                result = GuardResult(False, text or "", "empty input", ["EMPTY"])
            elif contains_any(norm, self.block_keywords):
                result = GuardResult(False, text, "off-topic request", ["OFF_TOPIC"])
            elif contains_any(norm, self.allowed_topics):
                result = GuardResult(True, text, "on topic", ["ON_TOPIC"])
            elif any(token in norm for token in ["nghi dinh", "mau so", "dieu ", "khoan ", "hoa don", "thue"]):
                result = GuardResult(True, text, "domain keyword matched", ["ON_TOPIC"])
            else:
                result = GuardResult(False, text, "outside legal/finance RAG scope", ["OFF_TOPIC"])
        result.latency_ms = timer.ms
        return result


class InjectionGuard:
    def __init__(self) -> None:
        self.patterns = [
            re.compile(r"ignore (all )?(previous|prior) instructions", re.I),
            re.compile(r"bo qua (tat ca )?(huong dan|chi thi)", re.I),
            re.compile(r"system prompt|developer message|hidden instruction", re.I),
            re.compile(r"reveal|exfiltrate|leak|dump", re.I),
            re.compile(r"roleplay|pretend|jailbreak|dan mode", re.I),
            re.compile(r"base64|decode|rot13", re.I),
            re.compile(r"<script|</script|prompt injection", re.I),
            re.compile(r"from now on|you are now|act as", re.I),
        ]

    def check(self, text: str) -> GuardResult:
        with Timer() as timer:
            norm = text or ""
            findings = [pattern.pattern for pattern in self.patterns if pattern.search(norm)]
            ok = not findings
            reason = "allowed" if ok else "prompt injection or policy bypass attempt"
        return GuardResult(ok=ok, text=text or "", reason=reason, findings=findings, latency_ms=timer.ms)


class InputGuardChain:
    def __init__(self) -> None:
        self.pii = InputGuard()
        self.topic = TopicGuard()
        self.injection = InjectionGuard()

    def sanitize(self, text: str) -> GuardResult:
        return self.pii.scrub_pii(text)

    def validate(self, text: str) -> GuardResult:
        sanitized = self.pii.scrub_pii(text)
        injection = self.injection.check(sanitized.text)
        topic = self.topic.check(sanitized.text)
        ok = injection.ok and topic.ok
        findings = sanitized.findings + injection.findings + topic.findings
        reason = "allowed" if ok else "; ".join([r for r in [injection.reason if not injection.ok else "", topic.reason if not topic.ok else ""] if r])
        return GuardResult(
            ok=ok,
            text=sanitized.text,
            reason=reason,
            findings=findings,
            latency_ms=sanitized.latency_ms + injection.latency_ms + topic.latency_ms,
        )
