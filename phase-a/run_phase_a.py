"""Run all Phase A tasks end to end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from phase_a_common import PHASE_DIR, ROOT_DIR


def run(cmd: list[str]) -> None:
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--rag-mode", choices=["auto", "full", "light"], default="auto")
    parser.add_argument("--allow-fallback-metrics", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    generate_cmd = [py, str(PHASE_DIR / "generate_test_set.py"), "--n", str(args.n)]
    rag_cmd = [py, str(PHASE_DIR / "run_rag_on_testset.py"), "--mode", args.rag_mode]
    if args.no_llm:
        generate_cmd.append("--no-llm")
        rag_cmd.append("--no-llm")
    run(generate_cmd)
    run(rag_cmd)
    ragas_cmd = [py, str(PHASE_DIR / "run_ragas.py")]
    if args.allow_fallback_metrics:
        ragas_cmd.append("--allow-fallback")
    if args.no_llm:
        ragas_cmd.extend(["--allow-fallback", "--force-fallback"])
    run(ragas_cmd)
    run([py, str(PHASE_DIR / "analyze_failures.py")])


if __name__ == "__main__":
    main()
