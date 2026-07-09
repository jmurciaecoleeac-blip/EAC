from PIL import Image

from alone.engines.base import RenderContext
from alone.engines.svg_engine import SvgEngine, _decode_ai_id
from alone.models import ImageValue, TextValue


def test_decode_illustrator_id():
    assert _decode_ai_id("_x7B__x7B_titre_x7D__x7D_") == "{{titre}}"
    assert _decode_ai_id("simple") == "simple"


def test_inspect_finds_placeholders(svg_path):
    result = SvgEngine().inspect(svg_path)
    assert result.format == "svg"
    assert result.pages == 1
    by_name = {ph.name: ph for ph in result.placeholders}
    assert by_name["photo"].type == "image"
    assert by_name["photo"].bbox.width == 200
    assert by_name["titre"].type == "text"
    assert by_name["email"].type == "text"
    assert by_name["email"].hints.get("inline") is True


def test_render_replaces_text_and_image(svg_path, fonts, red_image):
    ctx = RenderContext(values={
        "titre": TextValue(text="Bonjour", color="#ff0000"),
        "email": TextValue(text="a@b.fr"),
        "photo": ImageValue(image=red_image, fit="cover"),
    }, fonts=fonts)
    [(page, img)] = SvgEngine().render(svg_path, ctx)
    assert page == 1
    assert img.size == (400, 300)
    # le cadre photo (20,20)-(220,170) doit être rempli du rouge de l'image
    r, g, b, a = img.getpixel((120, 95))
    assert r > 150 and g < 90 and b < 90


def test_render_scale(svg_path, fonts):
    ctx = RenderContext(values={}, fonts=fonts, scale=2.0)
    [(_, img)] = SvgEngine().render(svg_path, ctx)
    assert img.size == (800, 600)


def test_zip_bundle_pages_natural_order(svg_zip_path, fonts):
    engine = SvgEngine()
    result = engine.inspect(svg_zip_path)
    assert result.format == "svg-bundle"
    assert result.pages == 2
    # page-2.svg (titre/photo/email) avant page-10.svg (slogan)
    pages = {ph.name: ph.page for ph in result.placeholders}
    assert pages["titre"] == 1
    assert pages["slogan"] == 2

    ctx = RenderContext(values={"slogan": TextValue(text="Nouveau slogan")},
                        fonts=fonts, pages=[2])
    rendered = engine.render(svg_zip_path, ctx)
    assert [p for p, _ in rendered] == [2]


def test_multiline_text(svg_path, fonts):
    ctx = RenderContext(values={"titre": TextValue(text="Ligne 1\nLigne 2")}, fonts=fonts)
    [(_, img)] = SvgEngine().render(svg_path, ctx)
    assert img.size == (400, 300)
