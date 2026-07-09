"""Bibliothèque de polices.

Les fichiers .ttf/.otf déposés dans le dossier de polices sont indexés par
famille, nom complet et nom PostScript (celui que référencent les PSD et les
IDML). Pour le rendu SVG (cairosvg s'appuie sur fontconfig), le dossier est
également enregistré auprès de fontconfig.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from fontTools.ttLib import TTFont, TTLibError
from PIL import ImageFont

logger = logging.getLogger(__name__)

_NAME_FAMILY = 1
_NAME_SUBFAMILY = 2
_NAME_FULL = 4
_NAME_POSTSCRIPT = 6
_NAME_TYPO_FAMILY = 16
_NAME_TYPO_SUBFAMILY = 17

FONT_EXTENSIONS = {".ttf", ".otf", ".ttc"}


def _norm(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


class FontLibrary:
    """Index des polices disponibles pour le rendu."""

    def __init__(self, fonts_dir: Path, extra_dirs: Optional[list[Path]] = None):
        self.fonts_dir = fonts_dir
        self.extra_dirs = extra_dirs or [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
        # clef normalisée -> chemin du fichier
        self._index: dict[str, Path] = {}
        # (famille normalisée, style normalisé) -> chemin
        self._family_style: dict[tuple[str, str], Path] = {}
        self.families: dict[str, list[str]] = {}
        self.refresh()

    # -- indexation ---------------------------------------------------------

    def refresh(self) -> None:
        self._index.clear()
        self._family_style.clear()
        self.families.clear()
        dirs = [d for d in [self.fonts_dir, *self.extra_dirs] if d and d.is_dir()]
        for directory in dirs:
            for path in sorted(directory.rglob("*")):
                if path.suffix.lower() in FONT_EXTENSIONS and path.is_file():
                    self._register(path)

    def _register(self, path: Path) -> None:
        try:
            font = TTFont(str(path), fontNumber=0, lazy=True)
        except (TTLibError, Exception):  # fichier corrompu : on ignore
            logger.warning("Police illisible ignorée : %s", path)
            return
        try:
            names = {}
            for rec_id in (_NAME_FAMILY, _NAME_SUBFAMILY, _NAME_FULL,
                           _NAME_POSTSCRIPT, _NAME_TYPO_FAMILY, _NAME_TYPO_SUBFAMILY):
                rec = font["name"].getDebugName(rec_id)
                if rec:
                    names[rec_id] = rec
        except Exception:
            return
        finally:
            font.close()

        family = names.get(_NAME_TYPO_FAMILY) or names.get(_NAME_FAMILY)
        style = names.get(_NAME_TYPO_SUBFAMILY) or names.get(_NAME_SUBFAMILY) or "Regular"
        if not family:
            return

        for key in filter(None, [names.get(_NAME_POSTSCRIPT), names.get(_NAME_FULL),
                                 f"{family} {style}", family if _norm(style) == "regular" else None]):
            self._index.setdefault(_norm(key), path)
        self._family_style.setdefault((_norm(family), _norm(style)), path)
        self.families.setdefault(family, [])
        if style not in self.families[family]:
            self.families[family].append(style)

    # -- résolution ---------------------------------------------------------

    def find_path(self, name: Optional[str], style: Optional[str] = None) -> Optional[Path]:
        """Trouve le fichier d'une police par nom PostScript, nom complet ou famille."""
        if not name:
            return None
        if style:
            hit = self._family_style.get((_norm(name), _norm(style)))
            if hit:
                return hit
        hit = self._index.get(_norm(f"{name} {style}" if style else name))
        if hit:
            return hit
        return self._index.get(_norm(name))

    def load(self, name: Optional[str], size: float, style: Optional[str] = None) -> ImageFont.FreeTypeFont:
        """Charge une police Pillow, avec repli sur DejaVu Sans."""
        size_px = max(1, int(round(size)))
        path = self.find_path(name, style)
        if path is None and name:
            logger.info("Police introuvable : %r (style %r), repli sur la police par défaut", name, style)
        if path is None:
            path = self._default_font_path()
        if path is not None:
            try:
                return ImageFont.truetype(str(path), size_px)
            except OSError:
                pass
        return ImageFont.load_default(size=size_px)  # type: ignore[return-value]

    def _default_font_path(self) -> Optional[Path]:
        for candidate in ("DejaVu Sans", "Liberation Sans", "FreeSans", "Arial"):
            path = self.find_path(candidate)
            if path:
                return path
        return None

    # -- intégration fontconfig (rendu SVG) ---------------------------------

    def register_with_fontconfig(self) -> None:
        """Rend le dossier de polices visible de fontconfig (donc de cairosvg).

        On crée des liens symboliques dans ~/.local/share/fonts (répertoire
        utilisateur standard de fontconfig) puis on rafraîchit le cache.
        """
        if not self.fonts_dir.is_dir():
            return
        user_fonts = Path.home() / ".local" / "share" / "fonts" / "alone"
        try:
            user_fonts.mkdir(parents=True, exist_ok=True)
            for path in self.fonts_dir.rglob("*"):
                if path.suffix.lower() in FONT_EXTENSIONS and path.is_file():
                    link = user_fonts / path.name
                    if not link.exists():
                        try:
                            link.symlink_to(path.resolve())
                        except OSError:
                            link.write_bytes(path.read_bytes())
        except OSError as exc:
            logger.warning("Impossible d'exposer les polices à fontconfig : %s", exc)
            return
        try:
            subprocess.run(["fc-cache", "-f", str(user_fonts)],
                           check=False, capture_output=True, timeout=60,
                           env={**os.environ})
        except (OSError, subprocess.TimeoutExpired):
            logger.warning("fc-cache indisponible : le rendu SVG utilisera les polices système")
