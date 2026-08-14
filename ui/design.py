from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QAbstractButton, QApplication, QLayout, QWidget


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
    _BASE_FONT_ATTR = "_provoware_unscaled_base_font"

    def __init__(self, app: QApplication, tokens: DesignTokens) -> None:
        self.app = app
        self.tokens = tokens
        stored = getattr(app, self._BASE_FONT_ATTR, None)
        if isinstance(stored, QFont):
            self._base_font = QFont(stored)
        else:
            self._base_font = QFont(app.font())
            setattr(app, self._BASE_FONT_ATTR, QFont(self._base_font))
        base_size = self._base_font.pointSizeF()
        self._base_point_size = base_size if base_size > 0 else 10.0

    def spacing(self, name: str = "M") -> int:
        return self.tokens.spacing[name]

    def configure_layout(self, layout: QLayout, *, spacing: str = "M", margins: str = "M") -> None:
        gap = self.spacing(spacing)
        margin = self.spacing(margins)
        layout.setSpacing(gap)
        layout.setContentsMargins(margin, margin, margin, margin)

    def fit_text_controls(self, root: QWidget) -> None:
        """Passt texttragende Bedienelemente nach einer globalen Schriftänderung neu an."""
        horizontal_padding = 2 * self.spacing("S")
        vertical_padding = 2 * self.spacing("XS")
        font = QFont(self.app.font())
        for button in root.findChildren(QAbstractButton):
            button.setFont(font)
            metrics = button.fontMetrics()
            button.setMinimumWidth(metrics.horizontalAdvance(button.text()) + horizontal_padding + 2)
            button.setMinimumHeight(metrics.height() + vertical_padding)
            button.updateGeometry()
        layout = root.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
        root.updateGeometry()

    def apply_font_scale(self, percent: int) -> None:
        if percent not in self.tokens.font_scales:
            raise ValueError(f"Nicht freigegebene Schriftgröße: {percent}%")
        font = QFont(self._base_font)
        font.setPointSizeF(self._base_point_size * percent / 100.0)
        self.app.setFont(font)
        for window in self.app.topLevelWidgets():
            self.fit_text_controls(window)

    @staticmethod
    def accessible(widget: QWidget, name: str, description: str = "") -> None:
        widget.setAccessibleName(name)
        if description:
            widget.setAccessibleDescription(description)
