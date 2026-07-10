"""Exemple : un agent IA (ou n'importe quel script) pilote Alone.

    ALONE_URL=http://vps:8000 ALONE_API_KEY=xxx python examples/agent_alone.py brochure.idml
"""

import json
import os
import pathlib
import sys

import httpx

BASE = os.environ.get("ALONE_URL", "http://127.0.0.1:8000")
HEADERS = {"X-API-Key": os.environ.get("ALONE_API_KEY", "")}


def main(template_file: str) -> None:
    client = httpx.Client(base_url=BASE, headers=HEADERS, timeout=120)

    # 1. Déposer le template
    with open(template_file, "rb") as fh:
        info = client.post("/v1/templates", files={"file": (pathlib.Path(template_file).name, fh)})
    info.raise_for_status()
    template = info.json()
    print(f"Template {template['id']} — {template['pages']} page(s)")

    # 2. Découvrir les zones à remplir
    for ph in template["placeholders"]:
        print(f"  {{{{{ph['name']}}}}} : {ph['type']} (page {ph['page']})")

    # 3. Construire les valeurs (ici, un exemple statique ; un agent IA
    #    générerait textes et choix d'images selon sa mission)
    data = {}
    for ph in template["placeholders"]:
        if ph["type"] == "text":
            data[ph["name"]] = f"Texte généré pour {ph['name']}"
        else:
            data[ph["name"]] = "https://picsum.photos/1200/800"

    # 4. Rendre
    result = client.post(f"/v1/templates/{template['id']}/render",
                         json={"data": data, "format": "png", "scale": 2.0})
    result.raise_for_status()
    rendered = result.json()
    for warning in rendered["warnings"]:
        print(f"⚠ {warning}")

    # 5. Télécharger les pages
    out_dir = pathlib.Path("rendus")
    out_dir.mkdir(exist_ok=True)
    for page in rendered["pages"]:
        img = client.get(page["url"])
        img.raise_for_status()
        target = out_dir / page["filename"]
        target.write_bytes(img.content)
        print(f"→ {target} ({page['width']}x{page['height']})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"usage": "python agent_alone.py <template.(svg|zip|psd|idml)>"}))
        sys.exit(1)
    main(sys.argv[1])
