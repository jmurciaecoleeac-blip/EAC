"""Interface en ligne de commande d'Alone.

    alone serve  [--host 0.0.0.0] [--port 8000]
    alone inspect template.(svg|zip|psd|idml)
    alone render  template.idml data.json -o sortie/ [--pages 1,3] [--scale 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("alone.api:app", host=args.host, port=args.port, workers=args.workers)
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    from .engines import engine_for

    path = Path(args.template)
    result = engine_for(path).inspect(path)
    print(json.dumps({
        "format": result.format,
        "pages": result.pages,
        "placeholders": [ph.model_dump() for ph in result.placeholders],
        "warnings": result.warnings,
    }, ensure_ascii=False, indent=2))
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    from .config import settings
    from .engines import engine_for
    from .engines.base import RenderContext
    from .fonts import FontLibrary
    from .images import resolve_values

    path = Path(args.template)
    engine = engine_for(path)
    info = engine.inspect(path)

    data = json.loads(Path(args.data).read_text(encoding="utf-8")) if args.data else {}
    values, warnings = resolve_values(data, info.placeholders, settings)

    fonts = FontLibrary(Path(args.fonts) if args.fonts else settings.fonts_dir)
    fonts.register_with_fontconfig()
    pages = [int(p) for p in args.pages.split(",")] if args.pages else None
    ctx = RenderContext(values=values, fonts=fonts, scale=args.scale,
                        pages=pages, warnings=warnings)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for page_no, img in engine.render(path, ctx):
        out = out_dir / f"page_{page_no:03d}.{args.format}"
        if args.format == "jpg":
            from PIL import Image
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            bg.save(out, quality=90)
        else:
            img.save(out)
        print(out)
    for w in ctx.warnings:
        print(f"⚠ {w}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alone", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="démarre l'API REST")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--workers", type=int, default=1)
    p_serve.set_defaults(func=_cmd_serve)

    p_inspect = sub.add_parser("inspect", help="liste les zones éditables d'un template")
    p_inspect.add_argument("template")
    p_inspect.set_defaults(func=_cmd_inspect)

    p_render = sub.add_parser("render", help="rend un template avec des valeurs")
    p_render.add_argument("template")
    p_render.add_argument("data", nargs="?", help="fichier JSON {placeholder: valeur}")
    p_render.add_argument("-o", "--output", default="./rendus")
    p_render.add_argument("--pages", help="pages à rendre, ex. 1,3")
    p_render.add_argument("--scale", type=float, default=1.0)
    p_render.add_argument("--format", choices=["png", "jpg"], default="png")
    p_render.add_argument("--fonts", help="dossier de polices")
    p_render.set_defaults(func=_cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
