"""Résolution des valeurs envoyées par l'agent.

Les URLs d'images sont téléchargées ici (avec limites de taille et de délai) ;
les moteurs de rendu reçoivent des valeurs déjà résolues et ne touchent
jamais au réseau.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging

import httpx
from PIL import Image, UnidentifiedImageError

from .config import Settings
from .models import ImageValue, Placeholder, RenderValue, ResolvedValue, TextValue, ValueSpec

logger = logging.getLogger(__name__)

Image.MAX_IMAGE_PIXELS = 120_000_000  # garde-fou contre les bombes de décompression


class ValueError_(ValueError):
    """Erreur de valeur utilisateur, renvoyée en 422 par l'API."""


def _decode_image(data: bytes, origin: str) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except UnidentifiedImageError:
        raise ValueError_(f"Le contenu de {origin!r} n'est pas une image reconnue")


def _download(url: str, settings: Settings) -> bytes:
    try:
        with httpx.Client(timeout=settings.download_timeout, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                length = resp.headers.get("content-length")
                if length and int(length) > settings.max_image_bytes:
                    raise ValueError_(f"Image trop lourde ({length} octets) : {url}")
                buf = io.BytesIO()
                for chunk in resp.iter_bytes():
                    buf.write(chunk)
                    if buf.tell() > settings.max_image_bytes:
                        raise ValueError_(f"Image trop lourde (> {settings.max_image_bytes} octets) : {url}")
                return buf.getvalue()
    except httpx.HTTPError as exc:
        raise ValueError_(f"Téléchargement impossible ({url}) : {exc}")


def _image_from_url(url: str, settings: Settings) -> Image.Image:
    if url.startswith("data:"):
        try:
            _, payload = url.split(",", 1)
            data = base64.b64decode(payload)
        except (ValueError, binascii.Error):
            raise ValueError_("data: URI invalide")
        return _decode_image(data, "data URI")
    if not url.startswith(("http://", "https://")):
        raise ValueError_(f"URL d'image non supportée : {url!r} (http/https/data: attendu)")
    return _decode_image(_download(url, settings), url)


def resolve_values(
    data: dict[str, RenderValue],
    placeholders: list[Placeholder],
    settings: Settings,
    allow_missing: bool = True,
) -> tuple[dict[str, ResolvedValue], list[str]]:
    """Convertit les valeurs brutes de la requête en valeurs prêtes au rendu.

    Retourne (valeurs résolues, avertissements).
    """
    by_name: dict[str, Placeholder] = {}
    for ph in placeholders:
        by_name.setdefault(ph.name, ph)

    warnings: list[str] = []
    resolved: dict[str, ResolvedValue] = {}

    for name, raw in data.items():
        ph = by_name.get(name)
        if ph is None:
            warnings.append(f"Placeholder inconnu ignoré : {name!r}")
            continue

        spec = raw if isinstance(raw, ValueSpec) else None
        if spec is None and isinstance(raw, dict):
            spec = ValueSpec(**raw)

        if ph.type == "text":
            if spec is not None:
                if spec.text is None:
                    raise ValueError_(f"{name!r} est un placeholder texte : champ 'text' requis")
                resolved[name] = TextValue(text=spec.text, color=spec.color,
                                           align=spec.align, size=spec.size)
            else:
                resolved[name] = TextValue(text=str(raw))
        else:  # image
            if spec is not None:
                if spec.b64:
                    try:
                        img = _decode_image(base64.b64decode(spec.b64), name)
                    except binascii.Error:
                        raise ValueError_(f"{name!r} : base64 invalide")
                elif spec.url:
                    img = _image_from_url(spec.url, settings)
                else:
                    raise ValueError_(f"{name!r} est un placeholder image : champ 'url' ou 'b64' requis")
                resolved[name] = ImageValue(image=img, fit=spec.fit)
            else:
                resolved[name] = ImageValue(image=_image_from_url(str(raw), settings))

    missing = [n for n in by_name if n not in resolved]
    if missing:
        msg = f"Placeholders sans valeur : {', '.join(sorted(missing))}"
        if allow_missing:
            warnings.append(msg + " (laissés tels quels dans le template)")
        else:
            raise ValueError_(msg)

    return resolved, warnings
