"""Shared result plumbing: provenance (version, input hash, timestamp), the
``Alert`` type for data-quality notes, and small formatting helpers. Every
public computation returns a frozen dataclass that carries one of these meta
blocks, so a result can be reproduced and audited later.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from ._version import __version__

SCHEMA = 1


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def data_hash(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


def make_meta(inputs: dict) -> dict:
    """Build the provenance block stamped onto every result."""
    return {
        "library": "revmng",
        "version": __version__,
        "computed_at": utcnow(),
        "input_hash": data_hash(inputs),
    }


@dataclass(frozen=True)
class Alert:
    """A data-quality or modelling caveat attached to a result."""

    indicator: str
    message: str
    severity: str = "warning"  # info | warning | error

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.indicator}: {self.message}"


def money(value: float | None) -> str:
    return "-" if value is None else f"{value:,.2f}"


def num(value: float | None, places: int = 2) -> str:
    return "-" if value is None else f"{value:,.{places}f}"
