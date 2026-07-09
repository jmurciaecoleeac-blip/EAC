"""Modèles Pydantic de l'API et types internes partagés par les moteurs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Union

from PIL import Image
from pydantic import BaseModel, Field

# Convention de nommage des zones éditables dans Adobe : {{nom}}
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")


def find_placeholder_name(raw: str) -> Optional[str]:
    """Extrait le nom d'un placeholder depuis un nom de calque/objet."""
    m = PLACEHOLDER_RE.search(raw or "")
    return m.group(1) if m else None


PlaceholderType = Literal["text", "image"]
FitMode = Literal["cover", "contain", "stretch"]


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Placeholder(BaseModel):
    """Zone éditable détectée dans un template."""

    name: str
    type: PlaceholderType
    page: int = 1
    bbox: Optional[BBox] = None
    # Infos de style détectées (police, taille…), à titre indicatif pour l'agent.
    hints: dict = Field(default_factory=dict)


class TemplateInfo(BaseModel):
    id: str
    name: str
    format: Literal["svg", "svg-bundle", "psd", "idml"]
    filename: str
    pages: int
    placeholders: list[Placeholder]
    created_at: str
    warnings: list[str] = Field(default_factory=list)


class ValueSpec(BaseModel):
    """Forme détaillée d'une valeur de placeholder envoyée par l'agent.

    Une valeur peut aussi être une simple chaîne : texte pour un placeholder
    texte, URL (http/https/data:) pour un placeholder image.
    """

    text: Optional[str] = None
    url: Optional[str] = None
    b64: Optional[str] = None  # image encodée en base64 (sans préfixe data:)
    fit: FitMode = "cover"
    color: Optional[str] = None  # texte : couleur CSS hex, ex. "#FF0000"
    align: Optional[Literal["left", "center", "right"]] = None
    size: Optional[float] = None  # texte : force la taille de police (pt/px)


RenderValue = Union[str, ValueSpec]


class RenderRequest(BaseModel):
    data: dict[str, RenderValue] = Field(default_factory=dict)
    pages: Optional[list[int]] = None  # 1-indexé ; None = toutes les pages
    format: Literal["png", "jpg", "jpeg"] = "png"
    scale: float = Field(default=1.0, gt=0, le=8)
    jpeg_quality: int = Field(default=90, ge=1, le=100)
    # Ignore les placeholders non fournis (sinon erreur 422).
    allow_missing: bool = True


class RenderedPage(BaseModel):
    page: int
    filename: str
    url: str
    width: int
    height: int


class RenderResult(BaseModel):
    render_id: str
    template_id: str
    format: str
    pages: list[RenderedPage]
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Types internes : valeurs résolues (images déjà téléchargées) passées aux
# moteurs de rendu, qui ne font jamais d'accès réseau eux-mêmes.
# ---------------------------------------------------------------------------


@dataclass
class TextValue:
    text: str
    color: Optional[str] = None
    align: Optional[str] = None
    size: Optional[float] = None


@dataclass
class ImageValue:
    image: Image.Image
    fit: str = "cover"


ResolvedValue = Union[TextValue, ImageValue]


def fit_image(img: Image.Image, width: int, height: int, fit: str = "cover") -> Image.Image:
    """Adapte une image aux dimensions d'un cadre.

    cover   : remplit le cadre, recadre l'excédent (défaut)
    contain : entre entièrement dans le cadre, centrée sur fond transparent
    stretch : déformée aux dimensions exactes
    """
    width, height = max(1, int(round(width))), max(1, int(round(height)))
    img = img.convert("RGBA")
    if fit == "stretch":
        return img.resize((width, height), Image.LANCZOS)

    src_ratio = img.width / img.height
    dst_ratio = width / height
    if fit == "contain":
        if src_ratio > dst_ratio:
            new_w, new_h = width, max(1, round(width / src_ratio))
        else:
            new_h, new_w = height, max(1, round(height * src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas.paste(resized, ((width - new_w) // 2, (height - new_h) // 2))
        return canvas

    # cover
    if src_ratio > dst_ratio:
        new_h, new_w = height, max(1, round(height * src_ratio))
    else:
        new_w, new_h = width, max(1, round(width / src_ratio))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def parse_color(value: Optional[str], default: tuple = (0, 0, 0, 255)) -> tuple:
    """Convertit une couleur CSS hex (#RGB, #RRGGBB, #RRGGBBAA) en tuple RGBA."""
    if not value:
        return default
    v = value.strip().lstrip("#")
    try:
        if len(v) == 3:
            r, g, b = (int(c * 2, 16) for c in v)
            return (r, g, b, 255)
        if len(v) == 6:
            return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255)
        if len(v) == 8:
            return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), int(v[6:8], 16))
    except ValueError:
        pass
    return default
