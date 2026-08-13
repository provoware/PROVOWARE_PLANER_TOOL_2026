from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "errors" / "FEHLERKATALOG.json"


@dataclass(frozen=True)
class ErrorEvent:
    code: str
    severity: str
    title: str
    effect: str
    user_action: str
    trace_id: str


def load_catalog() -> dict[str, dict]:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {entry["code"]: entry for entry in data["errors"]}


def make_event(code: str) -> ErrorEvent:
    entry = load_catalog()[code]
    return ErrorEvent(
        code=code,
        severity=entry["severity"],
        title=entry["title"],
        effect=entry["effect"],
        user_action=entry["user_action"],
        trace_id=f"TRC-{uuid.uuid4().hex[:12].upper()}",
    )


def user_message(event: ErrorEvent) -> str:
    return (
        f"[{event.severity}] {event.title}\n"
        f"Auswirkung: {event.effect}\n"
        f"Was ist zu tun: {event.user_action}\n"
        f"Fehler-ID: {event.code}\n"
        f"Vorgang: {event.trace_id}"
    )
