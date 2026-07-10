"""Bibliothèque d'images (assets).

Les images déposées ici sont réutilisables dans n'importe quel rendu via la
référence ``asset:<id>`` — pratique quand les visuels ne sont pas accessibles
par URL (fichiers locaux du graphiste, images produites par l'agent…).
"""

from __future__ import annotations

import datetime
import io
import re
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .config import Settings

_SAFE_RE = re.compile(r"[^A-Za-z0-9._\-]+")
_ID_RE = re.compile(r"^[a-f0-9]{12}$")

ALLOWED_FORMATS = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp",
                   "GIF": ".gif", "TIFF": ".tif", "BMP": ".bmp"}


class AssetNotFound(KeyError):
    pass


class InvalidAsset(ValueError):
    pass


def _dir(settings: Settings) -> Path:
    d = settings.data_dir / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_asset(filename: str, data: bytes, settings: Settings) -> dict:
    """Valide et stocke une image ; retourne sa fiche (id, ref, dimensions)."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except UnidentifiedImageError:
        raise InvalidAsset("Le fichier n'est pas une image reconnue "
                           "(formats acceptés : PNG, JPEG, WebP, GIF, TIFF, BMP)")
    ext = ALLOWED_FORMATS.get(img.format or "")
    if ext is None:
        raise InvalidAsset(f"Format d'image non supporté : {img.format}")

    asset_id = uuid.uuid4().hex[:12]
    stem = _SAFE_RE.sub("_", Path(filename).stem).strip("._")[:60] or "image"
    path = _dir(settings) / f"{asset_id}__{stem}{ext}"
    path.write_bytes(data)
    return _info(path, img.size)


def _info(path: Path, size: tuple | None = None) -> dict:
    asset_id, _, rest = path.name.partition("__")
    if size is None:
        try:
            with Image.open(path) as img:
                size = img.size
        except (UnidentifiedImageError, OSError):
            size = (0, 0)
    stat = path.stat()
    return {
        "id": asset_id,
        "ref": f"asset:{asset_id}",
        "filename": rest,
        "width": size[0],
        "height": size[1],
        "bytes": stat.st_size,
        "created_at": datetime.datetime.fromtimestamp(
            stat.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds"),
    }


def find_path(asset_id: str, settings: Settings) -> Path:
    if not _ID_RE.match(asset_id):
        raise AssetNotFound(asset_id)
    for path in _dir(settings).glob(f"{asset_id}__*"):
        return path
    raise AssetNotFound(asset_id)


def load_image(asset_id: str, settings: Settings) -> Image.Image:
    path = find_path(asset_id, settings)
    img = Image.open(path)
    img.load()
    return img


def list_assets(settings: Settings) -> list[dict]:
    return sorted((_info(p) for p in _dir(settings).glob("*__*")),
                  key=lambda a: a["created_at"], reverse=True)


def delete_asset(asset_id: str, settings: Settings) -> None:
    find_path(asset_id, settings).unlink()
