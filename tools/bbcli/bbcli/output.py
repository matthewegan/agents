"""Output helpers. Data → stdout, errors → stderr."""

from __future__ import annotations

import json
import sys
from typing import Any


def emit_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, default=str, ensure_ascii=False)
    sys.stdout.write("\n")


def emit_raw(text: str) -> None:
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def emit_error(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
