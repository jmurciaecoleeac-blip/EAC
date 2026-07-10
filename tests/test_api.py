import pytest
from fastapi.testclient import TestClient

from alone.api import create_app
from alone.config import Settings

API_KEY = "cle-de-test"


@pytest.fixture
def client(tmp_path):
    settings = Settings(api_key=API_KEY, data_dir=tmp_path / "data")
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def _upload_svg(client, svg_bytes) -> dict:
    resp = client.post(
        "/v1/templates",
        files={"file": ("affiche.svg", svg_bytes, "image/svg+xml")},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_root_manifest_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    manifest = client.get("/").json()
    assert manifest["service"] == "alone"


def test_ui_served(client):
    resp = client.get("/ui")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Alone" in resp.text
    assert "X-API-Key" in resp.text


def test_auth_required(client, svg_bytes):
    assert client.get("/v1/templates").status_code == 401
    resp = client.post("/v1/templates",
                       files={"file": ("a.svg", svg_bytes, "image/svg+xml")})
    assert resp.status_code == 401


def test_upload_inspect_render_flow(client, svg_bytes, red_png_data_uri):
    info = _upload_svg(client, svg_bytes)
    assert info["format"] == "svg"
    assert info["pages"] == 1
    names = {ph["name"]: ph["type"] for ph in info["placeholders"]}
    assert names == {"photo": "image", "titre": "text", "email": "text"}

    listed = client.get("/v1/templates", headers={"X-API-Key": API_KEY}).json()
    assert [t["id"] for t in listed] == [info["id"]]

    resp = client.post(
        f"/v1/templates/{info['id']}/render",
        json={"data": {"titre": "Bonjour",
                       "email": {"text": "x@y.fr"},
                       "photo": {"url": red_png_data_uri, "fit": "contain"}},
              "format": "png", "scale": 1.0},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert len(result["pages"]) == 1
    page = result["pages"][0]
    assert page["width"] == 400 and page["height"] == 300

    out = client.get(f"/v1/outputs/{result['render_id']}/{page['filename']}",
                     headers={"X-API-Key": API_KEY})
    assert out.status_code == 200
    assert out.headers["content-type"] == "image/png"
    assert out.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_jpg_and_bad_pages(client, svg_bytes):
    info = _upload_svg(client, svg_bytes)
    resp = client.post(f"/v1/templates/{info['id']}/render",
                       json={"data": {}, "format": "jpg"},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200
    assert resp.json()["pages"][0]["filename"].endswith(".jpg")

    resp = client.post(f"/v1/templates/{info['id']}/render",
                       json={"data": {}, "pages": [4]},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 422


def test_upload_rejects_unknown_format(client):
    resp = client.post("/v1/templates",
                       files={"file": ("doc.indd", b"xxxx", "application/octet-stream")},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 422
    assert "IDML" in resp.json()["detail"]


def test_delete_template(client, svg_bytes):
    info = _upload_svg(client, svg_bytes)
    headers = {"X-API-Key": API_KEY}
    assert client.delete(f"/v1/templates/{info['id']}", headers=headers).status_code == 204
    assert client.get(f"/v1/templates/{info['id']}", headers=headers).status_code == 404


def test_font_upload(client, tmp_path):
    from pathlib import Path

    src = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
    if not src.is_file():
        pytest.skip("DejaVu absent de l'environnement")
    resp = client.post("/v1/fonts",
                       files={"file": ("Custom.ttf", src.read_bytes(), "font/ttf")},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 201
    assert "DejaVu Serif" in resp.json()["families"]


def test_assets_flow(client, svg_bytes, red_image):
    import io

    headers = {"X-API-Key": API_KEY}
    buf = io.BytesIO()
    red_image.save(buf, format="PNG")

    resp = client.post("/v1/assets",
                       files={"file": ("Visuel Automne.png", buf.getvalue(), "image/png")},
                       headers=headers)
    assert resp.status_code == 201, resp.text
    asset = resp.json()
    assert asset["ref"] == f"asset:{asset['id']}"
    assert asset["width"] == 300 and asset["height"] == 100

    listed = client.get("/v1/assets", headers=headers).json()
    assert [a["id"] for a in listed] == [asset["id"]]

    raw = client.get(f"/v1/assets/{asset['id']}", headers=headers)
    assert raw.status_code == 200
    assert raw.content[:8] == b"\x89PNG\r\n\x1a\n"

    # rendu utilisant la référence asset:
    info = _upload_svg(client, svg_bytes)
    resp = client.post(f"/v1/templates/{info['id']}/render",
                       json={"data": {"photo": asset["ref"]}},
                       headers=headers)
    assert resp.status_code == 200, resp.text

    # référence inconnue -> 422
    resp = client.post(f"/v1/templates/{info['id']}/render",
                       json={"data": {"photo": "asset:000000000000"}},
                       headers=headers)
    assert resp.status_code == 422

    assert client.delete(f"/v1/assets/{asset['id']}", headers=headers).status_code == 204
    assert client.get(f"/v1/assets/{asset['id']}", headers=headers).status_code == 404

    resp = client.post("/v1/assets",
                       files={"file": ("pas_une_image.txt", b"bonjour", "text/plain")},
                       headers=headers)
    assert resp.status_code == 422


def test_idml_via_api(client, idml_path):
    resp = client.post("/v1/templates",
                       files={"file": ("mag.idml", idml_path.read_bytes(),
                                       "application/octet-stream")},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 201
    info = resp.json()
    assert info["format"] == "idml" and info["pages"] == 2

    resp = client.post(f"/v1/templates/{info['id']}/render",
                       json={"data": {"titre": "Via API", "prenom": "Léa"}},
                       headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200
    assert len(resp.json()["pages"]) == 2
