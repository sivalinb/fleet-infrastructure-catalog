"""Run the catalog API and interface; stop owned processes on exit."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ui", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    logs = ROOT / ".runtime/logs"
    logs.mkdir(parents=True, exist_ok=True)
    commands = [
        (
            "api",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "fleet_catalog.api:app_factory",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8002",
            ],
        )
    ]
    if not args.no_ui:
        commands.append(("gradio", [sys.executable, "gradio_app.py"]))
    processes = []
    handles = []
    try:
        for name, command in commands:
            handle = (logs / (name + ".log")).open("a")
            handles.append(handle)
            processes.append(
                (
                    name,
                    subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT),
                )
            )
        (ROOT / ".runtime/processes.json").write_text(
            json.dumps({name: p.pid for name, p in processes})
        )
        print("Catalog API: http://127.0.0.1:8002/docs", flush=True)
        if not args.no_ui:
            print("Catalog application: http://127.0.0.1:7861", flush=True)
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    raise RuntimeError(f"{name} exited; inspect .runtime/logs")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for _, p in reversed(processes):
            if p.poll() is None:
                p.terminate()
        for _, p in reversed(processes):
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        for handle in handles:
            handle.close()


if __name__ == "__main__":
    main()
