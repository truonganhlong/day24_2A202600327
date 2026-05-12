"""Run all Phase B judge and calibration tasks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PHASE_B_DIR = ROOT_DIR / "phase-b"


def run(cmd: list[str]) -> None:
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    no_llm = ["--no-llm"] if args.no_llm else []
    run([py, str(PHASE_B_DIR / "build_answer_variants.py")])
    run([py, str(PHASE_B_DIR / "pairwise_judge.py"), "--limit", str(args.limit), *no_llm])
    run([py, str(PHASE_B_DIR / "absolute_scoring.py"), "--limit", str(args.limit), *no_llm])
    run([py, str(PHASE_B_DIR / "calibrate_kappa.py"), "--sample-size", str(args.sample_size)])
    run([py, str(PHASE_B_DIR / "bias_report.py")])


if __name__ == "__main__":
    main()
