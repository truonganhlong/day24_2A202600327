"""C1: test PII redaction guard."""

from __future__ import annotations

from pathlib import Path

from input_guard import InputGuard
from phase_c_common import PHASE_C_DIR, latency_summary, write_csv


TEST_INPUTS = [
    ("My name is John Smith from Microsoft. Email john@ms.com, phone 555-1234", True),
    ("Call me at 0987654321 or visit 12 Rain Street HCM", True),
    ("VN CCCD cua toi la 012345678901", True),
    ("Lien he qua 0912345678 hoac mst 0106769437", True),
    ("Customer Nguyen Van A, CCCD 079876543211, phone 0912345678", True),
    ("Bridge over legal text has no personal data", False),
    ("Just a normal question about Nghi dinh 13", False),
    ("My VISA number is 4111111111111111", True),
    ("Tax code:0102345678 and email:a@b.com", True),
    ("", False),
    ("Long text " * 900 + " email hidden@example.com", True),
]


def main() -> None:
    guard = InputGuard()
    rows = []
    for idx, (text, expected_pii) in enumerate(TEST_INPUTS, 1):
        result = guard.scrub_pii(text)
        pii_found = bool(result.findings)
        rows.append({
            "id": idx,
            "input": text[:500],
            "sanitized": result.text[:800],
            "pii_found": pii_found,
            "expected_pii": expected_pii,
            "correct": pii_found == expected_pii,
            "findings": ";".join(result.findings),
            "latency_ms": round(result.latency_ms, 3),
        })

    recall_den = sum(1 for _, expected in TEST_INPUTS if expected)
    recall_num = sum(1 for row in rows if row["expected_pii"] and row["pii_found"])
    p95 = latency_summary([float(row["latency_ms"]) for row in rows])["p95_ms"]
    rows.append({
        "id": "summary",
        "input": "",
        "sanitized": "",
        "pii_found": "",
        "expected_pii": "",
        "correct": "",
        "findings": f"recall={recall_num / recall_den:.3f};p95_ms={p95}",
        "latency_ms": p95,
    })
    write_csv(
        PHASE_C_DIR / "pii_test_results.csv",
        rows,
        ["id", "input", "sanitized", "pii_found", "expected_pii", "correct", "findings", "latency_ms"],
    )
    print(f"[C1] recall={recall_num / recall_den:.3f}, p95={p95:.3f}ms")


if __name__ == "__main__":
    main()
