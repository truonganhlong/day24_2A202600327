"""Check Day 24 submission artifacts."""

from __future__ import annotations

from pathlib import Path


REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "prompts.md",
    ".env.example",
    ".github/workflows/eval-ragas.yml",
    "phase-a/test_set_v1.csv",
    "phase-a/ragas_results.csv",
    "phase-a/ragas_summary.json",
    "phase-a/failure_analysis.md",
    "phase-b/judge_pairwise_results.csv",
    "phase-b/absolute_scores.csv",
    "phase-b/human_labels.csv",
    "phase-b/kappa_report.md",
    "phase-b/judge_bias_report.md",
    "phase-c/input_guard.py",
    "phase-c/output_guard.py",
    "phase-c/full_pipeline.py",
    "phase-c/pii_test_results.csv",
    "phase-c/adversarial_test_results.csv",
    "phase-c/output_guard_results.csv",
    "phase-c/latency_benchmark.csv",
    "phase-c/audit_log.jsonl",
    "phase-d/blueprint.md",
    "phase-d/cost_model.csv",
    "demo/demo_notes.md",
    "submission_checklist.md",
]


def main() -> None:
    root = Path(__file__).resolve().parent
    missing = []
    empty = []
    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            missing.append(rel)
        elif path.is_file() and path.stat().st_size == 0:
            empty.append(rel)

    if missing or empty:
        if missing:
            print("Missing files:")
            for item in missing:
                print(f"  - {item}")
        if empty:
            print("Empty files:")
            for item in empty:
                print(f"  - {item}")
        raise SystemExit(1)

    print(f"Submission check passed: {len(REQUIRED_FILES)} files present.")


if __name__ == "__main__":
    main()
