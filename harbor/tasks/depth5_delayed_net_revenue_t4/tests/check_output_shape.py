#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path


def write_reward(passed_smoke: bool, diagnostic: str) -> None:
    log_dir = Path(os.environ.get("LOG_DIR", "/logs/verifier"))
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "reward.txt").write_text("0\n")
    (log_dir / "reward.json").write_text(
        json.dumps(
            {
                "reward": 0.0,
                "passed_smoke": passed_smoke,
                "official_score": False,
                "smoke_only": True,
            },
            indent=2,
        ) + "\n"
    )
    (log_dir / "diagnostic.txt").write_text(diagnostic + "\n")


def main() -> int:
    app_dir = Path(os.environ.get("APP_DIR", "/app"))
    task = json.loads((app_dir / "task.json").read_text())
    answer_path = app_dir / "answer.txt"
    if not answer_path.exists():
        write_reward(False, "missing /app/answer.txt")
        return 1

    got = answer_path.read_text().strip()
    if task["answer_format"] == "exact integer":
        ok = bool(re.fullmatch(r"-?\d+", got))
        diagnostic = "valid integer smoke output" if ok else f"not an exact integer: {got!r}"
    else:
        ok = bool(re.fullmatch(r"[A-Za-z]+", got))
        diagnostic = "valid code smoke output" if ok else f"not an exact code: {got!r}"

    # This is intentionally not official scoring; it only verifies I/O shape.
    write_reward(ok, diagnostic)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
