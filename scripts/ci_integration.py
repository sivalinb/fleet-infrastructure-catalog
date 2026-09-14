"""Own and clean up an independent catalog stack during integration checks."""

import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    process = subprocess.Popen([sys.executable, "scripts/run_stack.py"], cwd=ROOT)
    try:
        subprocess.run(
            [sys.executable, "scripts/verify_catalog.py"], cwd=ROOT, check=True
        )
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
