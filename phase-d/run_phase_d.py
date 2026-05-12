"""Run Phase D blueprint generation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run([sys.executable, str(ROOT_DIR / "phase-d" / "generate_blueprint.py")], cwd=ROOT_DIR, check=True)


if __name__ == "__main__":
    main()
