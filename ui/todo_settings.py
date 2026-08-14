from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from viewmodel.todo_query import TodoListMode


TODO_SETTINGS_SCHEMA_VERSION = 1
MODE_TEXT = {
    TodoListMode.TODAY: "Heute",
    TodoListMode.THIS_WEEK: "Diese Woche",
    TodoListMode.OVERDUE: "Überfällig",
    TodoListMode.WITHOUT_DATE: "Ohne Datum",
    TodoListMode.DONE: "Erledigt",
}


@dataclass(frozen=True)
class TodoGuiSettings:
    schema_version: int
    font_scale_percent: int
    todo_view_mode: str

    @classmethod
    def load(cls, path: Path, *, valid_font_scales: tuple[int, ...]) -> TodoGuiSettings | None:
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None
            if type(data.get("schema_version")) is not int:
                return None
            if type(data.get("font_scale_percent")) is not int:
                return None
            if not isinstance(data.get("todo_view_mode"), str):
                return None
            settings = cls(
                schema_version=data["schema_version"],
                font_scale_percent=data["font_scale_percent"],
                todo_view_mode=data["todo_view_mode"],
            )
            if settings.schema_version != TODO_SETTINGS_SCHEMA_VERSION:
                return None
            if settings.font_scale_percent not in valid_font_scales:
                return None
            TodoListMode(settings.todo_view_mode)
            return settings
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        candidate = path.with_suffix(".tmp")
        candidate.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        candidate.replace(path)
