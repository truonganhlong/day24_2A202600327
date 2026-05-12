"""Check Phase A aggregate RAGAS thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase_a_common import PHASE_DIR


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(PHASE_DIR / "ragas_summary.json"))
    parser.add_argument("--metric", default="faithfulness")
    parser.add_argument("--threshold", type=float, default=0.75)
    args = parser.parse_args()

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    score = float(summary.get("aggregate", {}).get(args.metric, 0.0))
    print(f"{args.metric}={score:.4f}, threshold={args.threshold:.4f}")
    if score < args.threshold:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
