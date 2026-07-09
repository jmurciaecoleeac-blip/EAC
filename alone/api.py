"""API REST d'Alone.

Conçue pour être pilotée par un agent IA : la racine ``GET /`` décrit le
service et ses conventions, la doc OpenAPI interactive est sur ``/docs``.
Authentification : en-tête ``X-API-Key`` (variable d'env ``ALONE_API_KEY``).
"""

from __future__ import annotations

import logging
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .config import Settings, settings as default_settings
from .engines import engine_for
from .engines.base import RenderContext, TemplateParseError, UnsupportedTemplateError
from .fonts import FONT_EXTENSIONS, FontLibrary
from .images import ValueError_, resolve_values
from .models import RenderedPage, RenderRequest, RenderResult, TemplateInfo
from .registry import TemplateNotFound, TemplateRegistry

logger = logging.getLogger(__name__)

_ID_RE = re.compile(r"^[a-f0-9]{12}$")
_OUTPUT_FILE_RE = re.compile(r"^page_\d{3}\.(png|jpg)$")

MAX_UPLOAD_BYTES = 200 * 1024 * 1024

SERVICE_MANIFEST = {
    "service": "alone",
    "description": (
        "Moteur de rendu de templates graphiques créés dans Adobe Illustrator "
        "(export SVG), Photoshop (PSD natif) et InDesign (export IDML). "
        "Les zones éditables sont des calques/objets nommés {{nom}} dans le "
        "fichier source. Envoyez un JSON {nom: texte ou URL d'image} pour "
        "obtenir des rendus PNG/JPEG."
    ),
    "auth": "En-tête 'X-API-Key' sur toutes les routes /v1/*",
    "workflow": [
        "1. POST /v1/templates (multipart, champ 'file') pour déposer un template (.svg, .zip de SVG, .psd, .idml)",
        "2. GET /v1/templates/{id} pour lire les placeholders détectés (nom, type texte/image, page, position)",
        "3. POST /v1/templates/{id}/render avec {data: {placeholder: valeur}} — valeur = texte, URL http(s)/data:, ou objet {text|url|b64, fit, color, align, size}",
        "4. Télécharger les pages rendues via les URLs retournées",
    ],
    "docs": "/docs (OpenAPI)",
    "version": __version__,
}


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or default_settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cfg.ensure_dirs()
        fonts = FontLibrary(cfg.fonts_dir)
        fonts.register_with_fontconfig()
        app.state.fonts = fonts
        app.state.registry = TemplateRegistry(cfg)
        if not cfg.api_key:
            logger.warning(
                "ALONE_API_KEY non défini : l'API est OUVERTE. "
                "À réserver aux réseaux privés."
            )
        yield

    app = FastAPI(
        title="Alone",
        version=__version__,
        description=SERVICE_MANIFEST["description"],
        lifespan=lifespan,
    )

    def require_key(request: Request) -> None:
        if cfg.api_key and request.headers.get("x-api-key") != cfg.api_key:
            raise HTTPException(401, "Clé API absente ou invalide (en-tête X-API-Key)")

    auth = Depends(require_key)

    # -- découverte ----------------------------------------------------------

    @app.get("/", tags=["service"])
    def root() -> dict:
        return SERVICE_MANIFEST

    @app.get("/health", tags=["service"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    # -- templates -----------------------------------------------------------

    @app.post("/v1/templates", response_model=TemplateInfo, status_code=201,
              tags=["templates"], dependencies=[auth])
    async def upload_template(file: UploadFile = File(...),
                              name: str | None = Form(default=None)) -> TemplateInfo:
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Fichier trop volumineux")
        if not data:
            raise HTTPException(422, "Fichier vide")
        try:
            return app.state.registry.add(file.filename or "template", data, name)
        except (UnsupportedTemplateError, TemplateParseError) as exc:
            raise HTTPException(422, str(exc))

    @app.get("/v1/templates", response_model=list[TemplateInfo],
             tags=["templates"], dependencies=[auth])
    def list_templates() -> list[TemplateInfo]:
        return app.state.registry.list()

    @app.get("/v1/templates/{template_id}", response_model=TemplateInfo,
             tags=["templates"], dependencies=[auth])
    def get_template(template_id: str) -> TemplateInfo:
        try:
            return app.state.registry.get(template_id)
        except TemplateNotFound:
            raise HTTPException(404, f"Template inconnu : {template_id}")

    @app.delete("/v1/templates/{template_id}", status_code=204,
                tags=["templates"], dependencies=[auth])
    def delete_template(template_id: str) -> None:
        try:
            app.state.registry.delete(template_id)
        except TemplateNotFound:
            raise HTTPException(404, f"Template inconnu : {template_id}")

    # -- rendu ----------------------------------------------------------------

    @app.post("/v1/templates/{template_id}/render", response_model=RenderResult,
              tags=["rendu"], dependencies=[auth])
    def render_template(template_id: str, req: RenderRequest, request: Request) -> RenderResult:
        registry: TemplateRegistry = app.state.registry
        try:
            info = registry.get(template_id)
        except TemplateNotFound:
            raise HTTPException(404, f"Template inconnu : {template_id}")

        if req.pages:
            bad = [p for p in req.pages if p < 1 or p > info.pages]
            if bad:
                raise HTTPException(422, f"Pages hors limites {bad} (template : {info.pages} page(s))")

        try:
            values, warnings = resolve_values(req.data, info.placeholders,
                                              cfg, req.allow_missing)
        except ValueError_ as exc:
            raise HTTPException(422, str(exc))

        path = registry.file_path(template_id)
        ctx = RenderContext(values=values, fonts=app.state.fonts,
                            scale=req.scale, pages=req.pages, warnings=warnings)
        try:
            rendered = engine_for(path).render(path, ctx)
        except (TemplateParseError, UnsupportedTemplateError) as exc:
            raise HTTPException(422, str(exc))
        if not rendered:
            raise HTTPException(422, "Aucune page à rendre")

        fmt = "jpg" if req.format in ("jpg", "jpeg") else "png"
        render_id = uuid.uuid4().hex[:12]
        out_dir = cfg.outputs_dir / render_id
        out_dir.mkdir(parents=True)

        pages: list[RenderedPage] = []
        for page_no, img in rendered:
            filename = f"page_{page_no:03d}.{fmt}"
            out_path = out_dir / filename
            if fmt == "jpg":
                from PIL import Image
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                background.save(out_path, quality=req.jpeg_quality)
            else:
                img.save(out_path)
            pages.append(RenderedPage(
                page=page_no, filename=filename,
                url=str(request.url_for("get_output", render_id=render_id, filename=filename)),
                width=img.width, height=img.height,
            ))

        return RenderResult(render_id=render_id, template_id=template_id,
                            format=fmt, pages=pages, warnings=ctx.warnings)

    @app.get("/v1/outputs/{render_id}/{filename}", tags=["rendu"],
             dependencies=[auth], name="get_output")
    def get_output(render_id: str, filename: str) -> FileResponse:
        if not _ID_RE.match(render_id) or not _OUTPUT_FILE_RE.match(filename):
            raise HTTPException(404, "Rendu inconnu")
        path = cfg.outputs_dir / render_id / filename
        if not path.is_file():
            raise HTTPException(404, "Rendu inconnu")
        media = "image/jpeg" if filename.endswith(".jpg") else "image/png"
        return FileResponse(path, media_type=media)

    # -- polices ---------------------------------------------------------------

    @app.get("/v1/fonts", tags=["polices"], dependencies=[auth])
    def list_fonts() -> dict:
        fonts: FontLibrary = app.state.fonts
        return {"families": fonts.families}

    @app.post("/v1/fonts", status_code=201, tags=["polices"], dependencies=[auth])
    async def upload_font(file: UploadFile = File(...)) -> JSONResponse:
        filename = Path(file.filename or "").name
        suffix = Path(filename).suffix.lower()
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Fichier trop volumineux")

        saved: list[str] = []
        if suffix == ".zip":
            import io
            import zipfile
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for entry in zf.namelist():
                        name = Path(entry).name
                        if Path(name).suffix.lower() in FONT_EXTENSIONS and not entry.endswith("/"):
                            (cfg.fonts_dir / name).write_bytes(zf.read(entry))
                            saved.append(name)
            except zipfile.BadZipFile:
                raise HTTPException(422, "Archive zip invalide")
            if not saved:
                raise HTTPException(422, "Aucune police (.ttf/.otf) dans l'archive")
        elif suffix in FONT_EXTENSIONS:
            (cfg.fonts_dir / filename).write_bytes(data)
            saved.append(filename)
        else:
            raise HTTPException(422, "Formats acceptés : .ttf, .otf, .ttc ou .zip de polices")

        fonts: FontLibrary = app.state.fonts
        fonts.refresh()
        fonts.register_with_fontconfig()
        return JSONResponse({"saved": saved, "families": fonts.families}, status_code=201)

    return app


app = create_app()
