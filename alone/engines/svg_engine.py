"""Moteur SVG — templates Illustrator.

Workflow designer : dans Illustrator, nommer les calques/objets éditables
``{{titre}}``, ``{{photo_1}}``… puis « Exporter sous… > SVG » (un fichier par
plan de travail). Un template multi-pages est un zip contenant les SVG, dont
l'ordre alphabétique naturel donne l'ordre des pages.

Détection des zones : attribut ``data-name`` (posé par Illustrator), ``id``
(en décodant l'échappement ``_xHH_`` d'Illustrator), label Inkscape, ou motif
``{{nom}}`` directement dans le contenu d'un bloc de texte.
"""

from __future__ import annotations

import base64
import io
import re
import zipfile
from pathlib import Path

import cairosvg
from lxml import etree
from PIL import Image

from ..models import (
    BBox,
    ImageValue,
    Placeholder,
    PLACEHOLDER_RE,
    TextValue,
    find_placeholder_name,
    parse_color,
)
from .base import Engine, InspectResult, RenderContext, TemplateParseError

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INKSCAPE_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"

_AI_ESCAPE_RE = re.compile(r"_x([0-9A-Fa-f]{2})_")
_IMAGE_TAGS = {"rect", "image", "circle", "ellipse", "polygon", "path", "use"}
_NATSORT_RE = re.compile(r"(\d+)")


def _decode_ai_id(value: str) -> str:
    """Décode l'échappement d'Illustrator dans les id SVG (``_x7B_`` → ``{``)."""
    decoded = _AI_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), value or "")
    # Illustrator suffixe les noms dupliqués : "{{photo}}_2_" — le motif
    # {{nom}} reste détectable tel quel.
    return decoded


def _natural_key(name: str):
    return [int(part) if part.isdigit() else part.lower() for part in _NATSORT_RE.split(name)]


def _localname(el) -> str:
    try:
        return etree.QName(el).localname
    except ValueError:
        return ""


def _element_placeholder_name(el) -> str | None:
    for raw in (el.get("data-name"), el.get(INKSCAPE_LABEL), _decode_ai_id(el.get("id") or "")):
        name = find_placeholder_name(raw or "")
        if name:
            return name
    return None


def _parse_length(value: str | None) -> float | None:
    if not value:
        return None
    m = re.match(r"^\s*(-?[\d.]+)", value)
    return float(m.group(1)) if m else None


def _element_bbox(el) -> BBox | None:
    tag = _localname(el)
    if tag in ("rect", "image"):
        x, y = _parse_length(el.get("x")) or 0.0, _parse_length(el.get("y")) or 0.0
        w, h = _parse_length(el.get("width")), _parse_length(el.get("height"))
        if w and h:
            return BBox(x=x, y=y, width=w, height=h)
    elif tag == "circle":
        cx, cy = _parse_length(el.get("cx")) or 0.0, _parse_length(el.get("cy")) or 0.0
        r = _parse_length(el.get("r"))
        if r:
            return BBox(x=cx - r, y=cy - r, width=2 * r, height=2 * r)
    elif tag == "ellipse":
        cx, cy = _parse_length(el.get("cx")) or 0.0, _parse_length(el.get("cy")) or 0.0
        rx, ry = _parse_length(el.get("rx")), _parse_length(el.get("ry"))
        if rx and ry:
            return BBox(x=cx - rx, y=cy - ry, width=2 * rx, height=2 * ry)
    elif tag == "text":
        x, y = _parse_length(el.get("x")), _parse_length(el.get("y"))
        if x is not None and y is not None:
            return BBox(x=x, y=y, width=0, height=0)
    return None


def _iter_text_nodes(text_el):
    """Itère (élément, attribut 'text'|'tail') pour chaque nœud texte d'un <text>."""
    if text_el.text:
        yield text_el, "text"
    for child in text_el.iter():
        if child is text_el:
            continue
        if child.text:
            yield child, "text"
        if child.tail and child is not text_el:
            yield child, "tail"


def _full_text(text_el) -> str:
    return "".join(text_el.itertext())


class _SvgDoc:
    """Un fichier SVG chargé (une page)."""

    def __init__(self, data: bytes, page: int, source_name: str):
        parser = etree.XMLParser(resolve_entities=False, no_network=True,
                                 remove_comments=False, huge_tree=False)
        try:
            self.tree = etree.fromstring(data, parser=parser)
        except etree.XMLSyntaxError as exc:
            raise TemplateParseError(f"SVG invalide ({source_name}) : {exc}")
        if _localname(self.tree) != "svg":
            raise TemplateParseError(f"{source_name} n'est pas un fichier SVG")
        self.page = page
        self.source_name = source_name

    # -- inspection ---------------------------------------------------------

    def placeholders(self) -> tuple[list[Placeholder], list[str]]:
        found: list[Placeholder] = []
        warnings: list[str] = []
        seen: set[str] = set()

        for el in self.tree.iter():
            if not isinstance(el.tag, str):
                continue
            tag = _localname(el)
            name = _element_placeholder_name(el)
            if name:
                if tag == "text":
                    ph_type = "text"
                elif tag in _IMAGE_TAGS or tag == "g":
                    ph_type = "image"
                    if tag == "g":
                        warnings.append(
                            f"Page {self.page} : {{{{{name}}}}} est un groupe ; utilisez plutôt "
                            "un rectangle comme cadre d'image (le cadre sera approximé)."
                        )
                else:
                    continue
                if name not in seen:
                    seen.add(name)
                    hints = {}
                    if tag == "text":
                        hints["sample"] = _full_text(el).strip()[:120]
                    found.append(Placeholder(name=name, type=ph_type, page=self.page,
                                             bbox=_element_bbox(el), hints=hints))
                continue

            # placeholders {{nom}} directement dans le texte
            if tag == "text":
                for m in PLACEHOLDER_RE.finditer(_full_text(el)):
                    n = m.group(1).strip()
                    if n not in seen:
                        seen.add(n)
                        found.append(Placeholder(name=n, type="text", page=self.page,
                                                 bbox=_element_bbox(el),
                                                 hints={"inline": True}))

        # images liées (non incorporées) : le rendu serveur ne les trouvera pas
        for el in self.tree.iter(f"{{{SVG_NS}}}image"):
            href = el.get(f"{{{XLINK_NS}}}href") or el.get("href") or ""
            if href and not href.startswith("data:"):
                warnings.append(
                    f"Page {self.page} : image liée non incorporée ({href!r}). Dans Illustrator, "
                    "choisissez « Incorporer » les images fixes avant l'export SVG."
                )
        return found, warnings

    # -- application des valeurs --------------------------------------------

    def apply(self, ctx: RenderContext) -> None:
        for el in list(self.tree.iter()):
            if not isinstance(el.tag, str):
                continue
            tag = _localname(el)
            name = _element_placeholder_name(el)
            value = ctx.values.get(name) if name else None

            if value is not None:
                if tag == "text" and isinstance(value, TextValue):
                    self._set_text(el, value)
                    continue
                if isinstance(value, ImageValue):
                    self._place_image(el, value, ctx)
                    continue
                ctx.warnings.append(
                    f"Page {self.page} : type de valeur incompatible pour {{{{{name}}}}} ignoré"
                )

            if tag == "text":
                self._substitute_inline(el, ctx)

    def _substitute_inline(self, text_el, ctx: RenderContext) -> None:
        def repl(m: re.Match) -> str:
            v = ctx.values.get(m.group(1).strip())
            return v.text if isinstance(v, TextValue) else m.group(0)

        for node, attr in list(_iter_text_nodes(text_el)):
            new = PLACEHOLDER_RE.sub(repl, getattr(node, attr))
            setattr(node, attr, new)

    def _set_text(self, text_el, value: TextValue) -> None:
        """Remplace tout le contenu d'un <text> nommé, en gardant le style."""
        tspans = [c for c in text_el if _localname(c) == "tspan"]
        lines = value.text.split("\n")

        if value.color:
            r, g, b, _ = parse_color(value.color)
            self._set_style(text_el, "fill", f"#{r:02x}{g:02x}{b:02x}")
        if value.size:
            self._set_style(text_el, "font-size", f"{value.size}px")
        if value.align:
            anchor = {"left": "start", "center": "middle", "right": "end"}[value.align]
            self._set_style(text_el, "text-anchor", anchor)

        font_size = self._font_size_of(text_el) or 16.0
        line_height = font_size * 1.2

        if not tspans:
            text_el.text = lines[0]
            base_x = text_el.get("x")
            base_y = _parse_length(text_el.get("y"))
            for i, line in enumerate(lines[1:], start=1):
                extra = etree.SubElement(text_el, f"{{{SVG_NS}}}tspan")
                if base_x is not None:
                    extra.set("x", base_x)
                if base_y is not None:
                    extra.set("y", str(base_y + i * line_height))
                else:
                    extra.set("dy", str(line_height))
                extra.text = line
            return

        model = tspans[0]
        for extra_tspan in tspans[1:]:
            text_el.remove(extra_tspan)
        text_el.text = None
        model.text = lines[0]
        for c in list(model):
            model.remove(c)
        base_y = _parse_length(model.get("y"))
        model_size = self._font_size_of(model) or font_size
        for i, line in enumerate(lines[1:], start=1):
            clone = etree.SubElement(text_el, f"{{{SVG_NS}}}tspan")
            for k, v in model.attrib.items():
                clone.set(k, v)
            if base_y is not None:
                clone.set("y", str(base_y + i * model_size * 1.2))
            else:
                clone.set("x", model.get("x", "0"))
                clone.set("dy", str(model_size * 1.2))
            clone.text = line

    def _font_size_of(self, el) -> float | None:
        for node in (el, el.getparent()):
            if node is None:
                continue
            direct = node.get("font-size")
            if direct:
                return _parse_length(direct)
            style = node.get("style") or ""
            m = re.search(r"font-size\s*:\s*([\d.]+)", style)
            if m:
                return float(m.group(1))
        return None

    @staticmethod
    def _set_style(el, prop: str, value: str) -> None:
        style = el.get("style") or ""
        if re.search(rf"{prop}\s*:", style):
            style = re.sub(rf"{prop}\s*:[^;]*", f"{prop}:{value}", style)
            el.set("style", style)
        else:
            el.set(prop, value)

    def _place_image(self, el, value: ImageValue, ctx: RenderContext) -> None:
        tag = _localname(el)
        bbox = _element_bbox(el)
        if bbox is None or not bbox.width or not bbox.height:
            ctx.warnings.append(
                f"Page {self.page} : cadre d'image sans dimensions exploitables "
                f"(<{tag}>) — utilisez un rectangle. Zone ignorée."
            )
            return

        img = _prepare_for_frame(value.image, bbox.width, bbox.height, value.fit)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        href = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

        if tag == "image":
            el.set(f"{{{XLINK_NS}}}href", href)
            if el.get("href"):
                el.set("href", href)
            el.set("preserveAspectRatio", "none")
            return

        image_el = etree.Element(f"{{{SVG_NS}}}image")
        image_el.set("x", str(bbox.x))
        image_el.set("y", str(bbox.y))
        image_el.set("width", str(bbox.width))
        image_el.set("height", str(bbox.height))
        image_el.set("preserveAspectRatio", "none")
        image_el.set(f"{{{XLINK_NS}}}href", href)
        if el.get("transform"):
            image_el.set("transform", el.get("transform"))
        parent = el.getparent()
        parent.insert(parent.index(el) + 1, image_el)

    # -- rendu ---------------------------------------------------------------

    def to_png(self, scale: float, max_px: int) -> Image.Image:
        data = etree.tostring(self.tree, xml_declaration=True, encoding="utf-8")
        png = cairosvg.svg2png(bytestring=data, scale=scale)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        if max(img.size) > max_px:
            raise TemplateParseError(
                f"Rendu trop grand ({img.size[0]}x{img.size[1]} px) : réduisez 'scale'"
            )
        return img


def _prepare_for_frame(img: Image.Image, frame_w: float, frame_h: float, fit: str) -> Image.Image:
    """Adapte le ratio de l'image au cadre sans perdre de résolution.

    L'image finale est insérée avec preserveAspectRatio="none" : on recadre
    (cover) ou on matte (contain) à ratio exact, la mise à l'échelle étant
    faite par le moteur SVG au rendu.
    """
    img = img.convert("RGBA")
    if fit == "stretch":
        return img
    src_ratio = img.width / img.height
    dst_ratio = frame_w / frame_h
    if abs(src_ratio - dst_ratio) < 1e-3:
        return img
    if fit == "contain":
        if src_ratio > dst_ratio:  # plus large : matte haut/bas
            new_h = round(img.width / dst_ratio)
            canvas = Image.new("RGBA", (img.width, new_h), (0, 0, 0, 0))
            canvas.paste(img, (0, (new_h - img.height) // 2))
        else:
            new_w = round(img.height * dst_ratio)
            canvas = Image.new("RGBA", (new_w, img.height), (0, 0, 0, 0))
            canvas.paste(img, ((new_w - img.width) // 2, 0))
        return canvas
    # cover : recadrage centré au ratio du cadre
    if src_ratio > dst_ratio:
        new_w = round(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        return img.crop((left, 0, left + new_w, img.height))
    new_h = round(img.width / dst_ratio)
    top = (img.height - new_h) // 2
    return img.crop((0, top, img.width, top + new_h))


class SvgEngine(Engine):
    """Moteur pour .svg (une page) et .zip de SVG (multi-pages)."""

    def _load_docs(self, path: Path) -> list[_SvgDoc]:
        if path.suffix.lower() == ".zip":
            docs = []
            try:
                with zipfile.ZipFile(path) as zf:
                    names = [n for n in zf.namelist()
                             if n.lower().endswith(".svg") and not n.startswith("__MACOSX")]
                    if not names:
                        raise TemplateParseError("Le zip ne contient aucun fichier .svg")
                    for page, name in enumerate(sorted(names, key=_natural_key), start=1):
                        docs.append(_SvgDoc(zf.read(name), page, name))
            except zipfile.BadZipFile:
                raise TemplateParseError("Archive zip invalide")
            return docs
        return [_SvgDoc(path.read_bytes(), 1, path.name)]

    def inspect(self, path: Path) -> InspectResult:
        docs = self._load_docs(path)
        placeholders: list[Placeholder] = []
        warnings: list[str] = []
        for doc in docs:
            found, warns = doc.placeholders()
            placeholders.extend(found)
            warnings.extend(warns)
        fmt = "svg-bundle" if path.suffix.lower() == ".zip" else "svg"
        return InspectResult(format=fmt, pages=len(docs),
                             placeholders=placeholders, warnings=warnings)

    def render(self, path: Path, ctx: RenderContext) -> list[tuple[int, Image.Image]]:
        from ..config import settings

        results: list[tuple[int, Image.Image]] = []
        for doc in self._load_docs(path):
            if not ctx.wants_page(doc.page):
                continue
            doc.apply(ctx)
            results.append((doc.page, doc.to_png(ctx.scale, settings.max_render_px)))
        return results
