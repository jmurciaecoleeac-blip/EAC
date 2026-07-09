import base64
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from alone.fonts import FontLibrary

SVG_PAGE = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#eeeecc"/>
  <rect id="_x7B__x7B_photo_x7D__x7D_" x="20" y="20" width="200" height="150" fill="#cccccc"/>
  <text id="_x7B__x7B_titre_x7D__x7D_" x="20" y="220" font-size="24" fill="#003366">Titre exemple</text>
  <text x="20" y="260" font-size="14">Contact : {{email}}</text>
</svg>"""

SVG_PAGE2 = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
  <rect width="400" height="300" fill="#ffffff"/>
  <text data-name="{{slogan}}" x="30" y="150" font-size="20">Slogan</text>
</svg>"""


@pytest.fixture
def svg_bytes() -> bytes:
    return SVG_PAGE.encode()


@pytest.fixture
def svg_path(tmp_path, svg_bytes) -> Path:
    p = tmp_path / "template.svg"
    p.write_bytes(svg_bytes)
    return p


@pytest.fixture
def svg_zip_path(tmp_path) -> Path:
    p = tmp_path / "template.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("page-10.svg", SVG_PAGE2)  # tri naturel : page-2 avant page-10
        zf.writestr("page-2.svg", SVG_PAGE)
    return p


@pytest.fixture
def idml_path(tmp_path) -> Path:
    from .idml_fixture import build

    return Path(build(str(tmp_path / "template.idml")))


@pytest.fixture
def red_image() -> Image.Image:
    return Image.new("RGB", (300, 100), (200, 30, 30))


@pytest.fixture
def red_png_data_uri(red_image) -> str:
    buf = io.BytesIO()
    red_image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def fonts(tmp_path) -> FontLibrary:
    return FontLibrary(tmp_path / "fonts")
