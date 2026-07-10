"""Moteur PSD — templates Photoshop.

Workflow designer : dans Photoshop, nommer les calques éditables ``{{titre}}``,
``{{photo_1}}``… et enregistrer le .psd tel quel (pas d'export nécessaire).

Rendu : les calques fixes sont composités par psd-tools ; les calques
placeholders sont masqués puis remplacés par le texte ou l'image fournis,
dessinés dans l'emprise (bbox) du calque d'origine. Pour les calques texte,
la police, la taille et la couleur d'origine sont réutilisées si possible.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw
from psd_tools import PSDImage

from ..models import (
    BBox,
    ImageValue,
    Placeholder,
    TextValue,
    find_placeholder_name,
    fit_image,
    parse_color,
)
from .base import Engine, InspectResult, RenderContext, TemplateParseError

logger = logging.getLogger(__name__)


def iter_layers(node):
    """Parcourt récursivement tous les calques (les groupes sont traversés)."""
    for layer in node:
        if layer.is_group():
            yield from iter_layers(layer)
        else:
            yield layer


def _layer_type(layer) -> str:
    return "text" if getattr(layer, "kind", "") == "type" else "image"


def extract_text_style(layer) -> dict:
    """Extrait police / taille / couleur d'un calque texte, best-effort."""
    style: dict = {}
    try:
        engine = layer.engine_dict
        runs = engine[b"StyleRun"][b"RunArray"]
        sheet = runs[0][b"StyleSheet"][b"StyleSheetData"]
        if b"FontSize" in sheet:
            size = float(sheet[b"FontSize"])
            # La matrice du calque texte porte l'échelle réelle du texte.
            transform = getattr(layer, "transform", None)
            if transform and len(transform) == 6:
                size *= abs(float(transform[3])) or 1.0
            style["size"] = size
        if b"FillColor" in sheet:
            values = sheet[b"FillColor"][b"Values"]
            a, r, g, b = (float(v) for v in values)
            style["color"] = (round(r * 255), round(g * 255), round(b * 255),
                              round(a * 255))
        if b"Font" in sheet:
            idx = int(sheet[b"Font"])
            fontset = layer.resource_dict[b"FontSet"]
            style["font"] = str(fontset[idx][b"Name"]).strip("'\"")
    except Exception:  # structures Adobe très variables : on reste tolérant
        logger.debug("Style de texte non extractible pour %r", getattr(layer, "name", "?"),
                     exc_info=True)
    return style


class PsdEngine(Engine):
    def _open(self, path: Path) -> PSDImage:
        try:
            return PSDImage.open(path)
        except Exception as exc:
            raise TemplateParseError(f"PSD illisible : {exc}")

    def inspect(self, path: Path) -> InspectResult:
        psd = self._open(path)
        placeholders: list[Placeholder] = []
        warnings: list[str] = []
        seen: set[str] = set()

        for layer in iter_layers(psd):
            name = find_placeholder_name(layer.name or "")
            if not name:
                continue
            if name in seen:
                warnings.append(f"Calque {{{{{name}}}}} en double : seul le premier est utilisé")
                continue
            seen.add(name)
            left, top, right, bottom = layer.bbox
            ph_type = _layer_type(layer)
            hints = {}
            if ph_type == "text":
                hints = {k: v for k, v in extract_text_style(layer).items() if k != "color"}
                text = getattr(layer, "text", None)
                if text:
                    hints["sample"] = str(text)[:120]
            placeholders.append(Placeholder(
                name=name, type=ph_type, page=1,
                bbox=BBox(x=left, y=top, width=right - left, height=bottom - top),
                hints=hints,
            ))

        if psd.color_mode.name not in ("RGB", "GRAYSCALE"):
            warnings.append(
                f"Mode colorimétrique {psd.color_mode.name} : le rendu est converti en RGB, "
                "les couleurs peuvent légèrement différer de Photoshop."
            )
        return InspectResult(format="psd", pages=1, placeholders=placeholders,
                             warnings=warnings)

    def render(self, path: Path, ctx: RenderContext) -> list[tuple[int, Image.Image]]:
        if not ctx.wants_page(1):
            return []
        psd = self._open(path)

        replaced_layers = []  # (layer, valeur) dans l'ordre du document (z bas -> haut)
        replaced_ids = set()
        for layer in iter_layers(psd):
            name = find_placeholder_name(layer.name or "")
            if name and name in ctx.values and id(layer) not in replaced_ids:
                replaced_layers.append((layer, ctx.values[name], name))
                replaced_ids.add(id(layer))

        hidden = {id(layer) for layer, _, _ in replaced_layers}
        base = psd.composite(
            force=bool(hidden),
            layer_filter=lambda l: l.is_visible() and id(l) not in hidden,
        )
        if base is None:
            raise TemplateParseError("PSD sans données composites exploitables")
        base = base.convert("RGBA")
        if base.size != (psd.width, psd.height):
            canvas = Image.new("RGBA", (psd.width, psd.height), (255, 255, 255, 0))
            canvas.paste(base, (0, 0))
            base = canvas

        for layer, value, name in replaced_layers:
            left, top, right, bottom = layer.bbox
            w, h = right - left, bottom - top
            if w <= 0 or h <= 0:
                ctx.warnings.append(f"Calque {{{{{name}}}}} vide (bbox nulle) : ignoré")
                continue
            if isinstance(value, ImageValue):
                fitted = fit_image(value.image, w, h, value.fit)
                base.alpha_composite(fitted, (left, top))
            elif isinstance(value, TextValue):
                self._draw_text(base, layer, value, (left, top, w, h), ctx)

        if ctx.scale != 1.0:
            new_size = (max(1, round(base.width * ctx.scale)),
                        max(1, round(base.height * ctx.scale)))
            from ..config import settings
            if max(new_size) > settings.max_render_px:
                raise TemplateParseError(
                    f"Rendu trop grand ({new_size[0]}x{new_size[1]} px) : réduisez 'scale'"
                )
            base = base.resize(new_size, Image.LANCZOS)
        return [(1, base)]

    def _draw_text(self, canvas: Image.Image, layer, value: TextValue,
                   frame: tuple[int, int, int, int], ctx: RenderContext) -> None:
        left, top, w, h = frame
        style = extract_text_style(layer)
        size = value.size or style.get("size") or max(12.0, h * 0.8)
        color = parse_color(value.color, default=style.get("color", (0, 0, 0, 255)))
        font = ctx.fonts.load(style.get("font"), size)

        draw = ImageDraw.Draw(canvas)
        align = value.align or "left"
        lines = value.text.split("\n")
        line_height = size * 1.2
        # Ancrage vertical : le bloc de texte démarre en haut de l'emprise du
        # calque d'origine, légèrement compensé pour approcher la ligne de base.
        y = top
        for line in lines:
            line_w = draw.textlength(line, font=font)
            if align == "center":
                x = left + (w - line_w) / 2
            elif align == "right":
                x = left + w - line_w
            else:
                x = left
            draw.text((x, y), line, font=font, fill=color)
            y += line_height
