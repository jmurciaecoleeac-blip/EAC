from pathlib import Path

import pytest

from alone.config import Settings
from alone.fonts import FontLibrary
from alone.images import ValueError_, resolve_values
from alone.models import ImageValue, Placeholder, TextValue, ValueSpec, fit_image
from PIL import Image


def _settings(tmp_path) -> Settings:
    return Settings(api_key="", data_dir=tmp_path)


PLACEHOLDERS = [
    Placeholder(name="titre", type="text"),
    Placeholder(name="photo", type="image"),
]


def test_resolve_text_and_data_uri(tmp_path, red_png_data_uri):
    values, warnings = resolve_values(
        {"titre": "Bonjour", "photo": red_png_data_uri},
        PLACEHOLDERS, _settings(tmp_path))
    assert isinstance(values["titre"], TextValue)
    assert values["titre"].text == "Bonjour"
    assert isinstance(values["photo"], ImageValue)
    assert values["photo"].image.size == (300, 100)
    assert warnings == []


def test_resolve_spec_and_unknown(tmp_path):
    values, warnings = resolve_values(
        {"titre": ValueSpec(text="X", color="#ff0000", align="center"),
         "mystere": "?"},
        PLACEHOLDERS, _settings(tmp_path))
    assert values["titre"].color == "#ff0000"
    assert any("mystere" in w for w in warnings)
    assert any("photo" in w for w in warnings)  # manquant signalé


def test_missing_strict(tmp_path):
    with pytest.raises(ValueError_):
        resolve_values({"titre": "X"}, PLACEHOLDERS, _settings(tmp_path),
                       allow_missing=False)


def test_image_requires_url(tmp_path):
    with pytest.raises(ValueError_):
        resolve_values({"photo": ValueSpec(text="pas une image")},
                       PLACEHOLDERS, _settings(tmp_path))


def test_bad_url_scheme(tmp_path):
    with pytest.raises(ValueError_):
        resolve_values({"photo": "ftp://exemple.fr/x.png"},
                       PLACEHOLDERS, _settings(tmp_path))


def test_fit_image_modes():
    src = Image.new("RGB", (200, 100), (255, 0, 0))
    assert fit_image(src, 100, 100, "cover").size == (100, 100)
    contained = fit_image(src, 100, 100, "contain")
    assert contained.size == (100, 100)
    assert contained.getpixel((50, 10))[3] == 0  # matte transparent
    assert fit_image(src, 50, 80, "stretch").size == (50, 80)


def test_font_library_system_fonts(tmp_path):
    lib = FontLibrary(tmp_path / "none")
    # DejaVu est présent sur l'image Docker et l'environnement de test
    assert lib.find_path("DejaVu Sans") is not None
    font = lib.load("DejaVu Sans", 20, style="Bold")
    assert font is not None
    # police inconnue : repli sans exception
    assert lib.load("Police Imaginaire", 14) is not None


def test_font_library_custom_dir(tmp_path):
    custom = tmp_path / "fonts"
    custom.mkdir()
    src = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
    if src.is_file():
        (custom / "MaPolice.ttf").write_bytes(src.read_bytes())
    lib = FontLibrary(custom, extra_dirs=[])
    if src.is_file():
        assert "DejaVu Serif" in lib.families
