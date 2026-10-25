"""Stop local processes started by run_local.py."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "logs" / "local-processes.json"


def main() -> None:
    if not STATE_FILE.exists():
        return
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    supervisor = state.get("supervisor")
    if supervisor:
        subprocess.run(
            ["taskkill.exe", "/PID", str(supervisor), "/T", "/F"],
            check=False,
            creationflags=0x08000000,
        )
    STATE_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
