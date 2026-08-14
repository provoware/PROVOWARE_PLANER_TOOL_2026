from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLayout, QWidget


@dataclass(frozen=True, slots=True)
class DesignTokens:
    spacing: dict[str, int]
    font_scales: tuple[int, ...]
    status_text: dict[str, str]

    @classmethod
    def from_repository(cls, root: Path) -> "DesignTokens":
        data = json.loads((Path(root) / "standards" / "UI_STANDARD.json").read_text(encoding="utf-8"))
        return cls(
            spacing={key: int(value) for key, value in data["spacing_tokens_px"].items()},
            font_scales=tuple(int(value) for value in data["font_scale_percent"]),
            status_text={
                "GREEN": data["status_lights"]["GREEN"]["text"],
                "YELLOW": data["status_lights"]["YELLOW"]["text"],
                "RED": data["status_lights"]["RED"]["text"],
            },
        )


class DesignSystem:
    def __init__(self, app: QApplication, tokens: DesignTokens) -> None:
        self.app = app
        self.tokens = tokens
        self._base_font = QFont(app.font())
        base_size = self._base_font.pointSizeF()
        self._base_point_size = base_size if base_size > 0 else 10.0

    def spacing(self, name: str = "M") -> int:
        return self.tokens.spacing[name]

    def configure_layout(self, layout: QLayout, *, spacing: str = "M", margins: str = "M") -> None:
        gap = self.spacing(spacing)
        margin = self.spacing(margins)
        layout.setSpacing(gap)
        layout.setContentsMargins(margin, margin, margin, margin)

    def apply_font_scale(self, percent: int) -> None:
        if percent not in self.tokens.font_scales:
            raise ValueError(f"Nicht freigegebene Schriftgröße: {percent}%")
        font = QFont(self._base_font)
        font.setPointSizeF(self._base_point_size * percent / 100.0)
        self.app.setFont(font)

    @staticmethod
    def accessible(widget: QWidget, name: str, description: str = "") -> None:
        widget.setAccessibleName(name)
        if description:
            widget.setAccessibleDescription(description)
