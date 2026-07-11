"""Moteur IDML — templates InDesign.

Workflow designer : dans InDesign, nommer les blocs éditables via le panneau
Calques (double-clic sur l'objet) : ``{{titre}}``, ``{{photo_1}}``… puis
« Fichier > Exporter > IDML ».

IDML est le format d'échange officiel d'InDesign : une archive zip de XML
(designmap, spreads, stories, ressources). Alone en fait un rendu simplifié :

- blocs rectangles/ellipses avec fond et contour unis ;
- blocs texte : contenu des stories avec police, corps, couleur et alignement
  du premier style de chaque paragraphe, césure simple à la largeur du bloc ;
- blocs image : remplacés par les images fournies ; les images fixes liées
  (non incorporées au XML) sont affichées en gris neutre.

Les effets avancés (dégradés, transparences, habillage, styles imbriqués,
texte curviligne…) ne sont pas reproduits — voir le README pour les
recommandations de conception de templates.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw

from ..models import (
    BBox,
    ImageValue,
    Placeholder,
    PLACEHOLDER_RE,
    TextValue,
    find_placeholder_name,
    fit_image,
    parse_color,
)
from .base import Engine, InspectResult, RenderContext, TemplateParseError

logger = logging.getLogger(__name__)

IDPKG_NS = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"
PX_PER_PT = 96.0 / 72.0  # rendu de base : 96 px par pouce (comme le SVG)

_FRAME_TAGS = {"Rectangle", "Oval", "Polygon", "TextFrame"}
_GRAPHIC_CHILD_TAGS = {"Image", "PDF", "EPS", "PICT", "WMF", "ImportedPage"}


# ---------------------------------------------------------------------------
# Géométrie
# ---------------------------------------------------------------------------


@dataclass
class Matrix:
    a: float = 1
    b: float = 0
    c: float = 0
    d: float = 1
    tx: float = 0
    ty: float = 0

    @classmethod
    def parse(cls, raw: str | None) -> "Matrix":
        if not raw:
            return cls()
        parts = [float(p) for p in raw.split()]
        return cls(*parts) if len(parts) == 6 else cls()

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (self.a * x + self.c * y + self.tx,
                self.b * x + self.d * y + self.ty)

    def compose(self, inner: "Matrix") -> "Matrix":
        """self ∘ inner (inner appliqué d'abord)."""
        return Matrix(
            a=self.a * inner.a + self.c * inner.b,
            b=self.b * inner.a + self.d * inner.b,
            c=self.a * inner.c + self.c * inner.d,
            d=self.b * inner.c + self.d * inner.d,
            tx=self.a * inner.tx + self.c * inner.ty + self.tx,
            ty=self.b * inner.tx + self.d * inner.ty + self.ty,
        )


def _path_points(item) -> list[tuple[float, float]]:
    pts = []
    for pp in item.findall(".//PathPointType"):
        anchor = pp.get("Anchor")
        if anchor:
            x, y = (float(v) for v in anchor.split()[:2])
            pts.append((x, y))
    return pts


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


@dataclass
class _Frame:
    tag: str  # Rectangle / Oval / Polygon / TextFrame
    name: str | None  # nom de placeholder si présent
    auto: bool  # True : bloc nommé sans {{...}}, promu placeholder automatiquement
    bounds: tuple[float, float, float, float]  # en points, repère page (x0, y0, x1, y1)
    rotated: bool
    fill: tuple | None
    stroke: tuple | None
    stroke_weight: float
    story_id: str | None = None
    has_graphic: bool = False
    embedded_image: bytes | None = None
    graphic_href: str | None = None
    layer_id: str | None = None
    seq: int = 0  # ordre de rencontre dans le spread
    opacity: float = 1.0  # opacité InDesign (0-1)
    content_type: str | None = None  # ContentType InDesign (GraphicType/TextType…)


@dataclass
class _Page:
    number: int
    width: float  # points
    height: float
    frames: list[_Frame] = field(default_factory=list)


@dataclass
class _Run:
    text: str
    size: float = 12.0
    color: tuple = (0, 0, 0, 255)
    font: str | None = None
    font_style: str | None = None


@dataclass
class _Paragraph:
    runs: list[_Run] = field(default_factory=list)
    align: str = "left"
    leading: float | None = None

    @property
    def text(self) -> str:
        return "".join(r.text for r in self.runs)


class _IdmlDoc:
    def __init__(self, path: Path):
        try:
            self.zf = zipfile.ZipFile(path)
        except (zipfile.BadZipFile, OSError) as exc:
            raise TemplateParseError(f"IDML illisible : {exc}")
        self.warnings: list[str] = []
        self._names = set(self.zf.namelist())
        designmap = self._xml("designmap.xml")
        if designmap is None:
            raise TemplateParseError("IDML invalide : designmap.xml manquant")
        self.colors = self._load_colors()
        self.layers = self._load_layers(designmap)
        self.stories = self._load_stories(designmap)
        self.pages = self._load_pages(designmap)
        self._promote_named_layers()
        self._sort_by_layer_stack()

    # -- calques --------------------------------------------------------------

    def _load_layers(self, designmap) -> dict[str, dict]:
        """Calques du document : {id: {name, index, visible}}.

        Dans le designmap, les calques sont listés du premier plan vers
        l'arrière-plan (même ordre que le panneau Calques d'InDesign).
        """
        layers: dict[str, dict] = {}
        for idx, layer in enumerate(designmap.iter("Layer")):
            self_id = layer.get("Self")
            if self_id:
                layers[self_id] = {
                    "name": (layer.get("Name") or "").strip(),
                    "index": idx,
                    "visible": layer.get("Visible", "true") != "false",
                }
        return layers

    _DEFAULT_LAYER_RE = re.compile(
        r"^(calque|layer|ebene|capa|livello|camada|laag|lager)\s*\d*$", re.IGNORECASE)

    def _promote_named_layers(self) -> None:
        """Un calque nommé qui contient un seul bloc de contenu devient éditable.

        Les designers nomment souvent le calque (« image 1 », « texte sortie »)
        plutôt que l'objet lui-même : si le calque porte un nom personnalisé et
        n'abrite qu'un bloc de contenu, ce bloc hérite du nom.
        """
        by_layer: dict[str, list[_Frame]] = {}
        for page in self.pages:
            for frame in page.frames:
                if frame.layer_id:
                    by_layer.setdefault(frame.layer_id, []).append(frame)

        for layer_id, frames in by_layer.items():
            info = self.layers.get(layer_id)
            if not info or not info["name"]:
                continue
            raw = info["name"]
            name = find_placeholder_name(raw)
            if name is None:
                if self._DEFAULT_LAYER_RE.match(raw):
                    continue  # « Calque 1 », « Layer 2 »… : nom par défaut
                name = raw
            content = [f for f in frames
                       if f.name is None
                       and (f.tag == "TextFrame" or f.has_graphic
                            or f.content_type == "GraphicType")]
            kinds = {"text" if f.tag == "TextFrame" else "image" for f in content}
            if len(kinds) == 1:
                # Tous du même type : la même valeur alimente chaque bloc.
                # Cas typique : la photo d'une page posée deux fois (grand
                # arrière-plan sous un voile + premier plan encadré).
                for f in content:
                    f.name, f.auto = name, True
            elif len(kinds) > 1:
                self.warnings.append(
                    f"Calque « {raw} » : blocs texte et image mélangés, impossible de "
                    "savoir lesquels rendre éditables — nommez les objets {{" + name + "}} "
                    "dans le panneau Calques (flèche du calque > double-clic sur l'objet)."
                )

    def _sort_by_layer_stack(self) -> None:
        """Trie les blocs par empilement des calques (arrière-plan d'abord)."""
        if not self.layers:
            return
        top = len(self.layers)

        def rank(frame: _Frame) -> tuple:
            info = self.layers.get(frame.layer_id or "")
            # premier calque du designmap = premier plan → dessiné en dernier
            depth = (top - info["index"]) if info else 0
            return (depth, frame.seq)

        for page in self.pages:
            page.frames.sort(key=rank)

    def _xml(self, name: str):
        if name not in self._names:
            return None
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            return etree.fromstring(self.zf.read(name), parser=parser)
        except etree.XMLSyntaxError as exc:
            raise TemplateParseError(f"XML invalide dans l'IDML ({name}) : {exc}")

    # -- couleurs -----------------------------------------------------------

    def _load_colors(self) -> dict[str, tuple]:
        colors: dict[str, tuple] = {}
        root = self._xml("Resources/Graphic.xml")
        if root is None:
            return colors
        for color in root.iter("Color"):
            self_id = color.get("Self")
            space = color.get("Space", "")
            raw = color.get("ColorValue", "")
            if not self_id or not raw:
                continue
            try:
                vals = [float(v) for v in raw.split()]
            except ValueError:
                continue
            rgba = None
            if space == "RGB" and len(vals) >= 3:
                rgba = (round(vals[0]), round(vals[1]), round(vals[2]), 255)
            elif space == "CMYK" and len(vals) >= 4:
                c, m, y, k = (v / 100.0 for v in vals[:4])
                rgba = (round(255 * (1 - c) * (1 - k)),
                        round(255 * (1 - m) * (1 - k)),
                        round(255 * (1 - y) * (1 - k)), 255)
            elif space == "LAB" and len(vals) >= 3:
                # approximation grossière : la luminance seule
                lum = round(vals[0] / 100 * 255)
                rgba = (lum, lum, lum, 255)
            if rgba:
                colors[self_id] = rgba
        return colors

    def resolve_color(self, ref: str | None) -> tuple | None:
        if not ref or ref.endswith("/None"):
            return None
        if ref in self.colors:
            return self.colors[ref]
        if ref.endswith("Black"):
            return (0, 0, 0, 255)
        if ref.endswith("Paper") or ref.endswith("White"):
            return (255, 255, 255, 255)
        # "Color/C=75 M=5 Y=100 K=0" : les valeurs sont lisibles dans le nom
        m = re.search(r"C=([\d.]+)\s*M=([\d.]+)\s*Y=([\d.]+)\s*K=([\d.]+)", ref)
        if m:
            c, mm, y, k = (float(v) / 100 for v in m.groups())
            return (round(255 * (1 - c) * (1 - k)),
                    round(255 * (1 - mm) * (1 - k)),
                    round(255 * (1 - y) * (1 - k)), 255)
        return (128, 128, 128, 255)

    # -- stories ------------------------------------------------------------

    def _load_stories(self, designmap) -> dict[str, list[_Paragraph]]:
        stories: dict[str, list[_Paragraph]] = {}
        for ref in designmap.iter(f"{{{IDPKG_NS}}}Story"):
            src = ref.get("src")
            root = self._xml(src) if src else None
            if root is None:
                continue
            for story in root.iter("Story"):
                sid = story.get("Self")
                if sid:
                    stories[sid] = self._parse_story(story)
        return stories

    def _parse_story(self, story) -> list[_Paragraph]:
        paragraphs: list[_Paragraph] = []
        for psr in story.iter("ParagraphStyleRange"):
            align = {"CenterAlign": "center", "RightAlign": "right",
                     "CenterJustified": "center", "RightJustified": "right"}.get(
                psr.get("Justification", ""), "left")
            current = _Paragraph(align=align)
            for csr in psr.iter("CharacterStyleRange"):
                size = float(csr.get("PointSize", 12) or 12)
                color = self.resolve_color(csr.get("FillColor")) or (0, 0, 0, 255)
                font = csr.get("AppliedFont")
                if font is None:
                    prop = csr.find("Properties/AppliedFont")
                    font = prop.text if prop is not None else None
                font_style = csr.get("FontStyle")
                leading_raw = csr.get("Leading")
                leading = None
                if leading_raw:
                    try:
                        leading = float(leading_raw)
                    except ValueError:
                        leading = None
                if leading and current.leading is None:
                    current.leading = leading

                for node in csr:
                    tag = etree.QName(node).localname if isinstance(node.tag, str) else ""
                    if tag == "Content":
                        text = node.text or ""
                        # U+2028 : saut de ligne forcé dans InDesign
                        parts = text.split(" ")
                        for i, part in enumerate(parts):
                            if i > 0:
                                paragraphs.append(current)
                                current = _Paragraph(align=align, leading=current.leading)
                            if part:
                                current.runs.append(_Run(part, size, color, font, font_style))
                    elif tag == "Br":
                        paragraphs.append(current)
                        current = _Paragraph(align=align, leading=current.leading)
            paragraphs.append(current)
        return [p for p in paragraphs if True]  # garde les paragraphes vides (lignes blanches)

    # -- pages et blocs -------------------------------------------------------

    def _load_pages(self, designmap) -> list[_Page]:
        pages: list[_Page] = []
        page_infos = []  # (page, origin_in_spread, matrix_spread->page px)
        number = 0
        for ref in designmap.iter(f"{{{IDPKG_NS}}}Spread"):
            root = self._xml(ref.get("src")) if ref.get("src") else None
            if root is None:
                continue
            spread = root.find(".//Spread")
            if spread is None:
                continue

            spread_pages = []
            for page_el in spread.iter("Page"):
                number += 1
                bounds = [float(v) for v in page_el.get("GeometricBounds", "0 0 792 612").split()]
                top, left, bottom, right = bounds
                m = Matrix.parse(page_el.get("ItemTransform"))
                x0, y0 = m.apply(left, top)
                page = _Page(number=number, width=right - left, height=bottom - top)
                pages.append(page)
                spread_pages.append((page, x0, y0))

            if not spread_pages:
                continue

            def assign(cx: float, cy: float):
                best, best_d = None, None
                for page, x0, y0 in spread_pages:
                    if x0 <= cx <= x0 + page.width and y0 <= cy <= y0 + page.height:
                        return page, x0, y0
                    d = abs(cx - (x0 + page.width / 2)) + abs(cy - (y0 + page.height / 2))
                    if best_d is None or d < best_d:
                        best, best_d = (page, x0, y0), d
                return best

            self._seq = 0
            self._collect_frames(spread, Matrix(), assign, None)
        return pages

    def _collect_frames(self, parent, outer: Matrix, assign, layer_id: str | None) -> None:
        for item in parent:
            if not isinstance(item.tag, str):
                continue
            tag = etree.QName(item).localname
            item_layer = item.get("ItemLayer") or layer_id
            if item.get("Visible") == "false":
                continue
            layer_info = self.layers.get(item_layer or "")
            if layer_info and not layer_info["visible"]:
                continue
            if tag == "Group":
                m = outer.compose(Matrix.parse(item.get("ItemTransform")))
                self._collect_frames(item, m, assign, item_layer)
                continue
            if tag not in _FRAME_TAGS:
                continue

            m = outer.compose(Matrix.parse(item.get("ItemTransform")))
            pts = _path_points(item)
            if not pts:
                continue
            spread_pts = [m.apply(x, y) for x, y in pts]
            xs = [p[0] for p in spread_pts]
            ys = [p[1] for p in spread_pts]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            target = assign(cx, cy)
            if target is None:
                continue
            page, ox, oy = target
            rotated = abs(m.b) > 1e-6 or abs(m.c) > 1e-6

            # Un nom posé à la main dans le panneau Calques est toujours
            # intentionnel : {{nom}} explicite, ou nom libre promu placeholder
            # (InDesign écrit "$ID/…" pour les objets non nommés).
            raw_name = (item.get("Name") or "").strip()
            if raw_name.startswith("$ID"):
                raw_name = ""
            name = find_placeholder_name(raw_name)
            auto = False
            if name is None and raw_name:
                name, auto = raw_name, True
            fill = self._tinted(self.resolve_color(item.get("FillColor")),
                                item.get("FillTint"))
            stroke = self._tinted(self.resolve_color(item.get("StrokeColor")),
                                  item.get("StrokeTint"))
            weight = float(item.get("StrokeWeight", 0) or 0)

            # opacité InDesign : <TransparencySetting><BlendingSetting Opacity="50"/>
            opacity = 1.0
            blending = item.find("TransparencySetting/BlendingSetting")
            if blending is not None:
                try:
                    opacity = max(0.0, min(1.0, float(blending.get("Opacity", 100)) / 100))
                except ValueError:
                    opacity = 1.0

            embedded, href, has_graphic = None, None, False
            for child in item:
                ctag = etree.QName(child).localname if isinstance(child.tag, str) else ""
                if ctag in _GRAPHIC_CHILD_TAGS:
                    has_graphic = True
                    link = child.find(".//Link")
                    if link is not None:
                        href = link.get("LinkResourceURI")
                    contents = child.find("Properties/Contents")
                    if contents is not None and contents.text:
                        try:
                            embedded = base64.b64decode(contents.text)
                        except (ValueError, binascii.Error):
                            embedded = None

            page.frames.append(_Frame(
                tag=tag,
                name=name,
                auto=auto,
                bounds=(min(xs) - ox, min(ys) - oy, max(xs) - ox, max(ys) - oy),
                rotated=rotated,
                fill=fill,
                stroke=stroke,
                stroke_weight=weight,
                story_id=item.get("ParentStory") if tag == "TextFrame" else None,
                has_graphic=has_graphic,
                embedded_image=embedded,
                graphic_href=href,
                layer_id=item_layer,
                seq=self._seq,
                opacity=opacity,
                content_type=item.get("ContentType"),
            ))
            self._seq += 1
            if rotated:
                self.warnings.append(
                    f"Page {page.number} : bloc pivoté rendu sans rotation (approximation)"
                )

    @staticmethod
    def _tinted(color: tuple | None, tint_raw: str | None) -> tuple | None:
        """Applique la teinte InDesign (Tint 0-100 : mélange vers le blanc)."""
        if color is None or not tint_raw:
            return color
        try:
            tint = float(tint_raw)
        except ValueError:
            return color
        if not 0 <= tint < 100:
            return color
        t = tint / 100
        r, g, b, a = color
        return (round(r * t + 255 * (1 - t)),
                round(g * t + 255 * (1 - t)),
                round(b * t + 255 * (1 - t)), a)


# ---------------------------------------------------------------------------
# Moteur
# ---------------------------------------------------------------------------


class IdmlEngine(Engine):
    def inspect(self, path: Path) -> InspectResult:
        doc = _IdmlDoc(path)
        placeholders: list[Placeholder] = []
        warnings = list(doc.warnings)
        seen: set[str] = set()

        for page in doc.pages:
            for frame in page.frames:
                x0, y0, x1, y1 = frame.bounds
                bbox = BBox(x=x0, y=y0, width=x1 - x0, height=y1 - y0)
                if frame.name and frame.name not in seen:
                    seen.add(frame.name)
                    ph_type = "text" if frame.tag == "TextFrame" else "image"
                    hints = {}
                    if frame.auto:
                        hints["auto"] = True
                    if ph_type == "text" and frame.story_id:
                        paras = doc.stories.get(frame.story_id, [])
                        sample = " ".join(p.text for p in paras).strip()
                        if sample:
                            hints["sample"] = sample[:120]
                        if paras and paras[0].runs:
                            hints["size"] = paras[0].runs[0].size
                            if paras[0].runs[0].font:
                                hints["font"] = paras[0].runs[0].font
                    placeholders.append(Placeholder(name=frame.name, type=ph_type,
                                                    page=page.number, bbox=bbox, hints=hints))
                elif frame.tag == "TextFrame" and frame.story_id:
                    paras = doc.stories.get(frame.story_id, [])
                    for m in PLACEHOLDER_RE.finditer(" ".join(p.text for p in paras)):
                        n = m.group(1).strip()
                        if n not in seen:
                            seen.add(n)
                            placeholders.append(Placeholder(name=n, type="text",
                                                            page=page.number, bbox=bbox,
                                                            hints={"inline": True}))
                if (frame.has_graphic and not frame.name
                        and frame.embedded_image is None and frame.graphic_href):
                    warnings.append(
                        f"Page {page.number} : image fixe liée ({frame.graphic_href.split('/')[-1]}) "
                        "non incorporée à l'IDML — elle apparaîtra en gris. Préférez un fond "
                        "exporté en image ou nommez le bloc {{...}} pour le remplir via l'API."
                    )

        bracket_re = re.compile(r"\[([^\[\]\n]{2,60})\]")
        tokens = {m.group(1).strip() for paras in doc.stories.values()
                  for p in paras for m in bracket_re.finditer(p.text)}
        if tokens:
            sample = sorted(tokens)[0]
            warnings.append(
                "Texte à trous détecté avec des crochets simples : "
                + ", ".join(f"[{t}]" for t in sorted(tokens))
                + f". Écrivez plutôt {{{{{sample}}}}} (doubles accolades) pour rendre "
                "ce fragment éditable individuellement."
            )

        auto_names = sorted({ph.name for ph in placeholders if ph.hints.get("auto")})
        if auto_names:
            warnings.append(
                "Blocs nommés sans {{...}} rendus éditables automatiquement : "
                + ", ".join(f"« {n} »" for n in auto_names)
                + ". Pour un contrôle explicite, nommez-les {{" + auto_names[0] + "}}."
            )
        warnings.append(
            "Rendu IDML simplifié : aplats, textes et images. Les effets avancés "
            "(dégradés, ombres, habillage…) ne sont pas reproduits."
        )
        return InspectResult(format="idml", pages=len(doc.pages),
                             placeholders=placeholders, warnings=warnings)

    def render(self, path: Path, ctx: RenderContext) -> list[tuple[int, Image.Image]]:
        from ..config import settings

        doc = _IdmlDoc(path)
        ctx.warnings.extend(doc.warnings)
        s = PX_PER_PT * ctx.scale
        results: list[tuple[int, Image.Image]] = []

        for page in doc.pages:
            if not ctx.wants_page(page.number):
                continue
            w_px = max(1, round(page.width * s))
            h_px = max(1, round(page.height * s))
            if max(w_px, h_px) > settings.max_render_px:
                raise TemplateParseError(
                    f"Rendu trop grand ({w_px}x{h_px} px) : réduisez 'scale'"
                )
            canvas = Image.new("RGBA", (w_px, h_px), (255, 255, 255, 255))
            draw = ImageDraw.Draw(canvas)

            for frame in page.frames:
                self._draw_frame(canvas, draw, frame, doc, ctx, s)
            results.append((page.number, canvas))
        return results

    # -- dessin ---------------------------------------------------------------

    def _draw_frame(self, canvas: Image.Image, draw: ImageDraw.ImageDraw,
                    frame: _Frame, doc: _IdmlDoc, ctx: RenderContext, s: float) -> None:
        x0, y0, x1, y1 = (v * s for v in frame.bounds)
        box = (round(x0), round(y0), round(max(x1, x0 + 1)), round(max(y1, y0 + 1)))
        value = ctx.values.get(frame.name) if frame.name else None

        def with_opacity(color: tuple) -> tuple:
            r, g, b, a = color
            return (r, g, b, round(a * frame.opacity))

        def paint_shape(fill: tuple | None, outline: tuple | None, width: int = 0) -> None:
            """Dessine avec un vrai fondu alpha (ImageDraw écraserait les pixels)."""
            fill = with_opacity(fill) if fill else None
            outline = with_opacity(outline) if outline else None
            translucent = any(c and c[3] < 255 for c in (fill, outline))
            target_draw = draw
            layer = None
            if translucent:
                layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                target_draw = ImageDraw.Draw(layer)
            shape = target_draw.ellipse if frame.tag == "Oval" else target_draw.rectangle
            kwargs = {}
            if fill:
                kwargs["fill"] = fill
            if outline and width:
                kwargs["outline"] = outline
                kwargs["width"] = width
            if kwargs:
                shape(box, **kwargs)
            if layer is not None:
                canvas.alpha_composite(layer)

        def paint_image(img: Image.Image, fit: str) -> None:
            fitted = fit_image(img, box[2] - box[0], box[3] - box[1], fit)
            if frame.opacity < 1.0:
                alpha = fitted.getchannel("A").point(lambda a: round(a * frame.opacity))
                fitted.putalpha(alpha)
            canvas.alpha_composite(fitted, (box[0], box[1]))

        # fond et contour
        paint_shape(frame.fill,
                    frame.stroke if frame.stroke_weight > 0 else None,
                    max(1, round(frame.stroke_weight * s)) if frame.stroke_weight > 0 else 0)

        # contenu image
        if isinstance(value, ImageValue):
            paint_image(value.image, value.fit)
            return
        if frame.has_graphic or frame.content_type == "GraphicType":
            if frame.embedded_image:
                try:
                    paint_image(Image.open(io.BytesIO(frame.embedded_image)), "cover")
                    return
                except OSError:
                    pass
            if not frame.fill and frame.has_graphic:
                paint_shape((210, 210, 210, 255), None)
            return

        # contenu texte
        if frame.tag == "TextFrame":
            paras = list(doc.stories.get(frame.story_id or "", []))
            if isinstance(value, TextValue):
                paras = self._override_paragraphs(paras, value)
            else:
                paras = self._substitute_inline(paras, ctx)
            self._draw_paragraphs(draw, paras, box, ctx, s)

    def _override_paragraphs(self, paras: list[_Paragraph], value: TextValue) -> list[_Paragraph]:
        model = next((r for p in paras for r in p.runs), _Run(""))
        align = value.align or next((p.align for p in paras if p.runs), "left")
        size = value.size or model.size
        color = parse_color(value.color, default=model.color)
        out = []
        for line in value.text.split("\n"):
            out.append(_Paragraph(
                runs=[_Run(line, size, color, model.font, model.font_style)],
                align=align,
                leading=None,
            ))
        return out

    def _substitute_inline(self, paras: list[_Paragraph], ctx: RenderContext) -> list[_Paragraph]:
        def repl(m: re.Match) -> str:
            v = ctx.values.get(m.group(1).strip())
            return v.text if isinstance(v, TextValue) else m.group(0)

        out = []
        for p in paras:
            runs = [_Run(PLACEHOLDER_RE.sub(repl, r.text), r.size, r.color, r.font, r.font_style)
                    for r in p.runs]
            out.append(_Paragraph(runs=runs, align=p.align, leading=p.leading))
        return out

    def _draw_paragraphs(self, draw: ImageDraw.ImageDraw, paras: list[_Paragraph],
                         box: tuple[int, int, int, int], ctx: RenderContext, s: float) -> None:
        left, top, right, bottom = box
        width = right - left
        y = float(top)
        for para in paras:
            if not para.runs:
                y += 12 * s  # ligne vide
                continue
            run = para.runs[0]  # style du paragraphe = style du premier segment
            size_px = run.size * s
            font = ctx.fonts.load(run.font, size_px, run.font_style)
            leading = (para.leading * s) if para.leading else size_px * 1.2
            for line in self._wrap(draw, para.text, font, width):
                line_w = draw.textlength(line, font=font)
                if para.align == "center":
                    x = left + (width - line_w) / 2
                elif para.align == "right":
                    x = right - line_w
                else:
                    x = left
                draw.text((x, y), line, font=font, fill=run.color)
                y += leading
                if y > bottom:
                    return

    @staticmethod
    def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and draw.textlength(candidate, font=font) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current or not lines:
            lines.append(current)
        return lines
