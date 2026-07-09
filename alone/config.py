"""Configuration du service, entièrement pilotée par variables d'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser().resolve()


@dataclass
class Settings:
    # Clé API attendue dans l'en-tête X-API-Key. Si vide, l'auth est désactivée
    # (à réserver aux réseaux privés).
    api_key: str = field(default_factory=lambda: os.environ.get("ALONE_API_KEY", ""))

    data_dir: Path = field(default_factory=lambda: _env_path("ALONE_DATA_DIR", "./data"))

    max_image_bytes: int = field(
        default_factory=lambda: int(os.environ.get("ALONE_MAX_IMAGE_BYTES", 25 * 1024 * 1024))
    )
    download_timeout: float = field(
        default_factory=lambda: float(os.environ.get("ALONE_DOWNLOAD_TIMEOUT", 30))
    )
    # Garde-fou sur la taille des rendus (pixels du plus grand côté).
    max_render_px: int = field(
        default_factory=lambda: int(os.environ.get("ALONE_MAX_RENDER_PX", 10000))
    )

    @property
    def templates_dir(self) -> Path:
        return self.data_dir / "templates"

    @property
    def fonts_dir(self) -> Path:
        return self.data_dir / "fonts"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    def ensure_dirs(self) -> None:
        for d in (self.templates_dir, self.fonts_dir, self.outputs_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
