from pathlib import Path

from PIL import Image
from psd_tools import PSDImage

from alone.engines.base import RenderContext
from alone.engines.psd_engine import PsdEngine
from alone.models import ImageValue, TextValue


class FakeColorMode:
    name = "RGB"


class FakeLayer:
    def __init__(self, name, kind="pixel", bbox=(0, 0, 10, 10), visible=True):
        self.name, self.kind, self.bbox = name, kind, bbox
        self._visible = visible

    def is_group(self):
        return False

    def is_visible(self):
        return self._visible


class FakeGroup:
    def __init__(self, layers):
        self._layers = layers

    def is_group(self):
        return True

    def __iter__(self):
        return iter(self._layers)


class FakePSD:
    width, height = 300, 200
    color_mode = FakeColorMode()

    def __init__(self, layers, base_color=(240, 240, 220)):
        self._layers = layers
        self.base_color = base_color
        self.composite_calls = []

    def __iter__(self):
        return iter(self._layers)

    def composite(self, force=False, layer_filter=None):
        self.composite_calls.append((force, layer_filter))
        return Image.new("RGB", (self.width, self.height), self.base_color)


def _engine_with(psd):
    engine = PsdEngine()
    engine._open = lambda path: psd
    return engine


def test_inspect_placeholders_including_groups():
    psd = FakePSD([
        FakeLayer("fond"),
        FakeGroup([FakeLayer("{{photo}}", bbox=(10, 10, 160, 110))]),
        FakeLayer("{{titre}}", kind="type", bbox=(10, 130, 290, 170)),
    ])
    result = _engine_with(psd).inspect(Path("x.psd"))
    by_name = {ph.name: ph for ph in result.placeholders}
    assert set(by_name) == {"photo", "titre"}
    assert by_name["photo"].type == "image"
    assert by_name["photo"].bbox.x == 10
    assert by_name["titre"].type == "text"


def test_render_replaces_layers(fonts):
    psd = FakePSD([
        FakeLayer("fond"),
        FakeLayer("{{photo}}", bbox=(10, 10, 160, 110)),
        FakeLayer("{{titre}}", kind="type", bbox=(10, 130, 290, 170)),
    ])
    ctx = RenderContext(values={
        "photo": ImageValue(image=Image.new("RGB", (50, 50), (0, 150, 0))),
        "titre": TextValue(text="Salut", color="#000080"),
    }, fonts=fonts)
    [(page, img)] = _engine_with(psd).render(Path("x.psd"), ctx)
    assert page == 1 and img.size == (300, 200)
    r, g, b, a = img.getpixel((80, 60))  # dans le cadre photo
    assert g > 100 and r < 80
    # les calques placeholders ont bien été exclus du composite
    _, layer_filter = psd.composite_calls[0]
    assert layer_filter(psd._layers[0]) is True
    assert layer_filter(psd._layers[1]) is False


def test_render_scale(fonts):
    psd = FakePSD([FakeLayer("fond")])
    ctx = RenderContext(values={}, fonts=fonts, scale=0.5)
    [(_, img)] = _engine_with(psd).render(Path("x.psd"), ctx)
    assert img.size == (150, 100)


def test_real_flat_psd_roundtrip(tmp_path, fonts):
    """Intégration avec psd-tools réel : PSD plat sans placeholder."""
    path = tmp_path / "flat.psd"
    PSDImage.frompil(Image.new("RGB", (60, 40), (10, 20, 30))).save(path)

    engine = PsdEngine()
    result = engine.inspect(path)
    assert result.format == "psd" and result.pages == 1
    [(_, img)] = engine.render(path, RenderContext(values={}, fonts=fonts))
    assert img.size == (60, 40)
    assert img.getpixel((30, 20))[:3] == (10, 20, 30)
