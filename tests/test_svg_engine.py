from PIL import Image

from alone.engines.base import RenderContext
from alone.engines.svg_engine import SvgEngine, _decode_ai_id
from alone.models import ImageValue, TextValue


def test_decode_illustrator_id():
    assert _decode_ai_id("_x7B__x7B_titre_x7D__x7D_") == "{{titre}}"
    assert _decode_ai_id("simple") == "simple"


def test_placeholder_names_with_spaces_and_accents():
    from alone.models import find_placeholder_name

    assert find_placeholder_name("{{Texte nom Sortie}}") == "Texte nom Sortie"
    assert find_placeholder_name("{{ prénom }}") == "prénom"
    assert find_placeholder_name("{{image 1}}") == "image 1"
    assert find_placeholder_name("sans accolades") is None


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


def test_set_text_reuses_styled_tspans(fonts, tmp_path):
    """Chaque ligne du nouveau texte reprend le tspan (donc le style) d'origine."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
      <text id="_x7B__x7B_bloc_x7D__x7D_" text-anchor="middle">
        <tspan x="100" y="30" font-family="Arial" font-weight="bold" font-size="20">GRAS</tspan>
        <tspan x="100" y="60" font-family="Georgia" font-size="14">LEGER</tspan>
      </text>
    </svg>"""
    path = tmp_path / "t.svg"
    path.write_text(svg)

    from alone.engines.svg_engine import _SvgDoc
    from alone.engines.base import RenderContext as RC

    doc = _SvgDoc(path.read_bytes(), 1, "t.svg")
    ctx = RC(values={"bloc": TextValue(text="TITRE\nSous-titre")}, fonts=fonts)
    doc.apply(ctx)
    tspans = [c for c in doc.tree.iter("{http://www.w3.org/2000/svg}tspan")]
    assert [t.text for t in tspans] == ["TITRE", "Sous-titre"]
    assert tspans[0].get("font-family") == "Arial"
    assert tspans[1].get("font-family") == "Georgia"

    # option font explicite : les font-family des tspans sont neutralisées
    doc2 = _SvgDoc(path.read_bytes(), 1, "t.svg")
    ctx2 = RC(values={"bloc": TextValue(text="A\nB", font="DejaVu Sans")}, fonts=fonts)
    doc2.apply(ctx2)
    text_el = next(doc2.tree.iter("{http://www.w3.org/2000/svg}text"))
    assert "DejaVu Sans" in (text_el.get("font-family") or "")
    for t in text_el:
        assert t.get("font-family") is None
