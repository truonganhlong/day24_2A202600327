"""C2: test topic scope validator."""

from __future__ import annotations

from input_guard import TopicGuard
from phase_c_common import PHASE_C_DIR, latency_summary, write_csv


TEST_CASES = [
    ("Theo Nghi dinh 13, du lieu ca nhan la gi?", True),
    ("Quyen rut lai su dong y cua chu the du lieu nam o dau?", True),
    ("Thue GTGT con phai nop trong ky la bao nhieu?", True),
    ("Mau so 04 dung de nop ho so danh gia tac dong dung khong?", True),
    ("BCTC co chi tieu thue GTGT nao?", True),
    ("Cac bien phap bao ve du lieu ca nhan nhay cam la gi?", True),
    ("RAG guardrail can chan PII nhu the nao?", True),
    ("Khoan nao quy dinh thong bao vi pham trong 72 gio?", True),
    ("Ho so chuyen du lieu ca nhan ra nuoc ngoai gom gi?", True),
    ("Giai thich chi tieu [40] tren to khai thue", True),
    ("Hom nay thoi tiet o Ha Noi the nao?", False),
    ("Viet mot bai tho ve mua thu", False),
    ("Cach nau pho bo ngon?", False),
    ("Tran bong da toi qua ai thang?", False),
    ("Tu van hen ho cho sinh vien", False),
    ("Lap chien luoc crypto trading 100x", False),
    ("Review phim moi nhat", False),
    ("Game nao dang hot?", False),
    ("Du lich Da Nang nen di dau?", False),
    ("Write a fantasy story about dragons", False),
]


def main() -> None:
    guard = TopicGuard()
    rows = []
    for idx, (text, expected_allowed) in enumerate(TEST_CASES, 1):
        result = guard.check(text)
        rows.append({
            "id": idx,
            "input": text,
            "allowed": result.ok,
            "expected_allowed": expected_allowed,
            "correct": result.ok == expected_allowed,
            "reason": result.reason,
            "latency_ms": round(result.latency_ms, 3),
        })
    accuracy = sum(1 for row in rows if row["correct"]) / len(rows)
    p95 = latency_summary([float(row["latency_ms"]) for row in rows])["p95_ms"]
    rows.append({
        "id": "summary",
        "input": "",
        "allowed": "",
        "expected_allowed": "",
        "correct": f"accuracy={accuracy:.3f}",
        "reason": f"p95_ms={p95}",
        "latency_ms": p95,
    })
    write_csv(
        PHASE_C_DIR / "topic_test_results.csv",
        rows,
        ["id", "input", "allowed", "expected_allowed", "correct", "reason", "latency_ms"],
    )
    print(f"[C2] accuracy={accuracy:.3f}, p95={p95:.3f}ms")


if __name__ == "__main__":
    main()
