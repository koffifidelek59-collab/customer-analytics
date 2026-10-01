#!/usr/bin/env python3
"""Run quality analysis then dispatch notifications."""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main():
    qa = subprocess.call([sys.executable, str(ROOT / "api" / "run_quality_alerts.py")])
    # always attempt notify (respects min_status inside)
    subprocess.call([sys.executable, str(ROOT / "api" / "notify_alerts.py")])
    return qa
if __name__ == "__main__":
    sys.exit(main())
