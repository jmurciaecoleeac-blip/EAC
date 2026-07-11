from PIL import Image

from alone.engines.base import RenderContext
from alone.engines.idml_engine import IdmlEngine
from alone.models import ImageValue, TextValue


def test_inspect(idml_path):
    result = IdmlEngine().inspect(idml_path)
    assert result.format == "idml"
    assert result.pages == 2
    by_name = {ph.name: ph for ph in result.placeholders}
    assert by_name["titre"].type == "text"
    assert by_name["titre"].page == 1
    assert by_name["titre"].hints["size"] == 24.0
    assert by_name["photo"].type == "image"
    assert by_name["photo"].bbox.width == 180
    assert by_name["prenom"].type == "text"
    assert by_name["prenom"].page == 2
    # bloc nommé sans {{...}} : promu placeholder automatiquement
    auto = by_name["Texte nom Sortie"]
    assert auto.type == "text" and auto.page == 2
    assert auto.hints["auto"] is True
    assert any("Texte nom Sortie" in w for w in result.warnings)


def test_render_auto_named_frame(idml_path, fonts):
    ctx = RenderContext(values={"Texte nom Sortie": TextValue(text="Nouveau contenu")},
                        fonts=fonts, pages=[2])
    [(_, img)] = IdmlEngine().render(idml_path, ctx)
    assert img.size == (533, 400)


def test_render_pages_and_colors(idml_path, fonts):
    ctx = RenderContext(values={
        "titre": TextValue(text="Édition Spéciale"),
        "photo": ImageValue(image=Image.new("RGB", (500, 500), (180, 40, 40))),
        "prenom": TextValue(text="Camille"),
    }, fonts=fonts)
    rendered = dict(IdmlEngine().render(idml_path, ctx))
    assert set(rendered) == {1, 2}
    page1 = rendered[1]
    # 400x300 pt à 96 px/pouce -> 533x400 px
    assert page1.size == (533, 400)
    # bandeau jaune CMJN (0 10 90 0) en haut (à gauche du titre centré)
    r, g, b, a = page1.getpixel((40, 30))
    assert r > 220 and g > 180 and b < 90
    # photo remplacée par du rouge
    r, g, b, a = page1.getpixel((150, 190))
    assert r > 140 and g < 80


def test_render_single_page(idml_path, fonts):
    ctx = RenderContext(values={}, fonts=fonts, pages=[2])
    rendered = IdmlEngine().render(idml_path, ctx)
    assert [p for p, _ in rendered] == [2]


def test_inline_substitution_keeps_unknown(idml_path, fonts):
    ctx = RenderContext(values={"prenom": TextValue(text="Alex")}, fonts=fonts, pages=[2])
    [(_, img)] = IdmlEngine().render(idml_path, ctx)
    assert img.size == (533, 400)


def test_scale(idml_path, fonts):
    ctx = RenderContext(values={}, fonts=fonts, scale=2.0, pages=[1])
    [(_, img)] = IdmlEngine().render(idml_path, ctx)
    assert img.size == (1067, 800)
