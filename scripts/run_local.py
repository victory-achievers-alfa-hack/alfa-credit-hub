"""Run the local backend and frontend without opening console windows."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
STATE_FILE = LOG_DIR / "local-processes.json"
CREATE_NO_WINDOW = 0x08000000


def open_log(name: str):
    LOG_DIR.mkdir(exist_ok=True)
    return (LOG_DIR / name).open("a", encoding="utf-8")


def main() -> None:
    backend_out = open_log("backend-local.log")
    backend_err = open_log("backend-local-error.log")
    frontend_out = open_log("frontend-local.log")
    frontend_err = open_log("frontend-local-error.log")

    backend = subprocess.Popen(
        [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=ROOT,
        stdout=backend_out,
        stderr=backend_err,
        creationflags=CREATE_NO_WINDOW,
    )
    frontend = subprocess.Popen(
        [
            r"C:\Program Files\nodejs\node.exe",
            "node_modules/vite/bin/vite.js",
            "--host",
            "127.0.0.1",
            "--port",
            "5173",
        ],
        cwd=ROOT / "frontend",
        stdout=frontend_out,
        stderr=frontend_err,
        creationflags=CREATE_NO_WINDOW,
    )
    processes = [backend, frontend]
    STATE_FILE.write_text(
        json.dumps({"supervisor": os.getpid(), "backend": backend.pid, "frontend": frontend.pid}),
        encoding="utf-8",
    )

    stopping = False

    def stop_processes(*_args) -> None:
        nonlocal stopping
        if stopping:
            return
        stopping = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop_processes)
    signal.signal(signal.SIGINT, stop_processes)

    try:
        while not stopping and all(process.poll() is None for process in processes):
            time.sleep(1)
    finally:
        stop_processes()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        STATE_FILE.unlink(missing_ok=True)
        for stream in (backend_out, backend_err, frontend_out, frontend_err):
            stream.close()


if __name__ == "__main__":
    main()
