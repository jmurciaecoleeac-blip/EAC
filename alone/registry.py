"""Stockage des templates sur disque.

Chaque template vit dans ``<data>/templates/<id>/`` : le fichier d'origine
plus un ``meta.json`` (résultat d'inspection, réutilisé à chaque rendu).
"""

from __future__ import annotations

import datetime
import json
import re
import shutil
import uuid
from pathlib import Path

from .config import Settings
from .engines import engine_for
from .models import TemplateInfo

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\-]+")


class TemplateNotFound(KeyError):
    pass


def _safe_filename(name: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", Path(name).name).strip("._") or "template"
    return cleaned[:120]


class TemplateRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = settings.templates_dir

    def add(self, filename: str, data: bytes, display_name: str | None = None) -> TemplateInfo:
        template_id = uuid.uuid4().hex[:12]
        filename = _safe_filename(filename)
        folder = self.root / template_id
        folder.mkdir(parents=True)
        path = folder / filename
        path.write_bytes(data)

        try:
            engine = engine_for(path)
            result = engine.inspect(path)
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise

        info = TemplateInfo(
            id=template_id,
            name=display_name or Path(filename).stem,
            format=result.format,  # type: ignore[arg-type]
            filename=filename,
            pages=result.pages,
            placeholders=result.placeholders,
            warnings=result.warnings,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        )
        (folder / "meta.json").write_text(info.model_dump_json(indent=2), encoding="utf-8")
        return info

    def get(self, template_id: str) -> TemplateInfo:
        meta = self.root / template_id / "meta.json"
        if not meta.is_file():
            raise TemplateNotFound(template_id)
        return TemplateInfo.model_validate_json(meta.read_text(encoding="utf-8"))

    def file_path(self, template_id: str) -> Path:
        info = self.get(template_id)
        return self.root / template_id / info.filename

    def list(self) -> list[TemplateInfo]:
        infos = []
        if self.root.is_dir():
            for folder in sorted(self.root.iterdir()):
                if (folder / "meta.json").is_file():
                    try:
                        infos.append(self.get(folder.name))
                    except Exception:
                        continue
        return infos

    def delete(self, template_id: str) -> None:
        folder = self.root / template_id
        if not (folder / "meta.json").is_file():
            raise TemplateNotFound(template_id)
        shutil.rmtree(folder)
