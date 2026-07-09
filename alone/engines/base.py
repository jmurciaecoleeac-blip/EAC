"""Interface commune des moteurs de rendu."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from ..fonts import FontLibrary
from ..models import Placeholder, ResolvedValue


class UnsupportedTemplateError(ValueError):
    pass


class TemplateParseError(ValueError):
    pass


@dataclass
class InspectResult:
    format: str  # "svg" | "svg-bundle" | "psd" | "idml"
    pages: int
    placeholders: list[Placeholder]
    warnings: list[str] = field(default_factory=list)


@dataclass
class RenderContext:
    values: dict[str, ResolvedValue]
    fonts: FontLibrary
    scale: float = 1.0
    pages: list[int] | None = None  # 1-indexé ; None = toutes
    warnings: list[str] = field(default_factory=list)

    def wants_page(self, page: int) -> bool:
        return self.pages is None or page in self.pages


class Engine(ABC):
    """Un moteur sait inspecter un template (zones éditables) et le rendre."""

    @abstractmethod
    def inspect(self, path: Path) -> InspectResult: ...

    @abstractmethod
    def render(self, path: Path, ctx: RenderContext) -> list[tuple[int, Image.Image]]:
        """Rend les pages demandées. Retourne des paires (numéro de page, image RGBA)."""
