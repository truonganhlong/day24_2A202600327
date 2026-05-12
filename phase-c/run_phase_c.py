"""Run all Phase C guardrails tasks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PHASE_C_DIR = ROOT_DIR / "phase-c"


def run(cmd: list[str]) -> None:
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, cwd=PHASE_C_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--use-output-api", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    run([py, "test_input_guard.py"])
    run([py, "test_topic_guard.py"])
    run([py, "test_adversarial.py"])
    output_cmd = [py, "test_output_guard.py"]
    if args.use_output_api:
        output_cmd.append("--use-api")
    run(output_cmd)
    full_cmd = [py, "full_pipeline.py", "--n", str(args.n)]
    if args.use_llm:
        full_cmd.append("--use-llm")
    if args.use_output_api:
        full_cmd.append("--use-output-api")
    run(full_cmd)


if __name__ == "__main__":
    main()
