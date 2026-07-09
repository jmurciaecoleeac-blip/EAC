"""Moteurs de rendu par format de template."""

from __future__ import annotations

from pathlib import Path

from .base import Engine, UnsupportedTemplateError


def engine_for(path: Path) -> Engine:
    """Choisit le moteur adapté à un fichier template."""
    from .idml_engine import IdmlEngine
    from .psd_engine import PsdEngine
    from .svg_engine import SvgEngine

    suffix = path.suffix.lower()
    if suffix == ".svg":
        return SvgEngine()
    if suffix == ".zip":
        return SvgEngine()  # archive de SVG = pages multiples (plans de travail)
    if suffix in (".psd", ".psb"):
        return PsdEngine()
    if suffix == ".idml":
        return IdmlEngine()
    raise UnsupportedTemplateError(
        f"Format non supporté : {suffix!r}. Formats acceptés : .svg, .zip (SVG multi-pages), "
        ".psd, .idml. Pour Illustrator, exportez en SVG ; pour InDesign, exportez en IDML."
    )
