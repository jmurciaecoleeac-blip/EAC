# Alone — moteur de templates Adobe pilotable par un agent IA

**Alone** est un service Python auto-hébergé (VPS Linux) qui ouvre des templates
créés dans **Illustrator**, **Photoshop** ou **InDesign**, remplace les zones
prévues par des textes et des images, et produit des rendus **PNG/JPEG** —
le tout via une **API REST** conçue pour être pilotée par un agent IA.

```
Designer (Adobe) ──export──▶ template ──upload──▶ Alone (VPS) ◀──JSON── Agent IA
                                                      │
                                                      ▼
                                               PNG / JPEG rendus
```

100 % open-source : aucune application Adobe ni API payante n'est nécessaire
sur le serveur.

## Formats supportés

Les formats natifs `.ai` et `.indd` sont propriétaires et fermés : aucun
logiciel ne peut les rééditer fidèlement sans Adobe. Alone travaille donc sur
les **formats d'échange** que chaque application exporte nativement en un clic :

| Application | Format template | Export côté designer | Fidélité de rendu |
|---|---|---|---|
| Illustrator | `.svg` (1 page) ou `.zip` de SVG (multi-pages) | Fichier > Exporter > Exporter sous… > SVG | ★★★★★ |
| Photoshop | `.psd` **natif** | aucun export : le .psd est lu directement | ★★★★☆ |
| InDesign | `.idml` | Fichier > Exporter > IDML | ★★★☆☆ (rendu simplifié, voir [Limites](#limites)) |

## La convention `{{nom}}`

Dans le fichier source, le designer **nomme** les calques/objets éditables
entre doubles accolades :

- `{{titre}}`, `{{sous_titre}}` sur un **bloc de texte** → zone texte ;
- `{{photo_1}}`, `{{logo}}` sur un **rectangle ou un cadre image** → zone image.

Tout le reste (calques non nommés `{{…}}`) est rendu tel quel. Un placeholder
peut aussi être écrit **directement dans un texte** : « Contact : {{email}} ».

### Côté Illustrator (cas typique : 7 plans de travail)

1. Nommer les calques/objets éditables `{{…}}` dans le panneau Calques.
2. **Incorporer** les images fixes (Fenêtre > Liens > Incorporer les images).
3. Fichier > Exporter > Exporter sous… > **SVG**, cocher **« Utiliser les plans
   de travail »** (un SVG par page) avec les options :
   - Polices : **SVG** (surtout pas « Vectoriser » pour les textes à modifier) ;
   - Images : **Incorporer** ;
   - IDs d'objet : **Noms de calque**.
4. Zipper les SVG obtenus (l'ordre des pages suit le tri naturel des noms de
   fichiers) et envoyer le zip à Alone.

### Côté Photoshop

Nommer les calques `{{…}}` et envoyer le `.psd` tel quel. Les calques texte
remplacés réutilisent la police, le corps et la couleur d'origine (si la
police est installée sur le serveur, voir [Polices](#polices)).

### Côté InDesign

Nommer les blocs via le panneau Calques (double-clic sur le nom de l'objet),
puis Fichier > Exporter > **IDML**.

## Installation sur le VPS

### Avec Docker (recommandé)

```bash
git clone <ce dépôt> && cd EAC
echo "ALONE_API_KEY=$(openssl rand -hex 24)" > .env
docker compose up -d --build
curl http://localhost:8000/health
```

### Sans Docker

```bash
apt-get install libcairo2 fontconfig fonts-dejavu-core   # dépendances système
pip install .
export ALONE_API_KEY="votre-clé-secrète"
export ALONE_DATA_DIR=/var/lib/alone                     # templates, polices, rendus
alone serve --host 0.0.0.0 --port 8000
```

En production, placez l'API derrière un reverse-proxy HTTPS (Caddy, Nginx…).
Variables d'environnement : `ALONE_API_KEY` (clé d'accès, obligatoire hors
réseau privé), `ALONE_DATA_DIR` (stockage), `ALONE_MAX_IMAGE_BYTES`,
`ALONE_DOWNLOAD_TIMEOUT`, `ALONE_MAX_RENDER_PX`.

## Polices

Pour un rendu fidèle, déposez les `.ttf`/`.otf` utilisés par vos templates
(licences serveur en règle) :

```bash
curl -X POST http://vps:8000/v1/fonts -H "X-API-Key: $KEY" -F "file=@Montserrat.zip"
curl http://vps:8000/v1/fonts -H "X-API-Key: $KEY"   # familles disponibles
```

Les polices manquantes sont remplacées par DejaVu Sans (avec avertissement
dans les logs).

## Interface web de gestion

Une interface d'administration légère est servie par Alone lui-même sur
**`http://vps:8000/ui`** (aucune dépendance externe) : saisie de la clé API,
dépôt de templates par glisser-déposer, tableau des zones détectées,
formulaire de test de rendu avec aperçu et téléchargement, gestion des
polices. Idéale pour valider un template avant de le confier à l'agent IA.

## API REST

Toutes les routes `/v1/*` exigent l'en-tête `X-API-Key`. La documentation
interactive OpenAPI est sur **`/docs`** ; `GET /` renvoie un manifeste JSON
décrivant le service (pratique pour amorcer un agent IA).

### 1. Déposer un template

```bash
curl -X POST http://vps:8000/v1/templates \
  -H "X-API-Key: $KEY" \
  -F "file=@brochure.idml" -F "name=Brochure 7 pages"
```

Réponse : l'inspection complète du template — pages, zones détectées, position
et type de chaque zone, avertissements de conception :

```json
{
  "id": "abb8190c3fd0",
  "format": "idml",
  "pages": 7,
  "placeholders": [
    {"name": "titre",   "type": "text",  "page": 1, "bbox": {...}, "hints": {"font": "Montserrat", "size": 24.0}},
    {"name": "photo_1", "type": "image", "page": 1, "bbox": {...}}
  ],
  "warnings": []
}
```

### 2. Rendre le template

```bash
curl -X POST http://vps:8000/v1/templates/abb8190c3fd0/render \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "data": {
      "titre":   "Collection Automne",
      "accroche": {"text": "Jusqu'\''à -50%", "color": "#C41E2F", "align": "center"},
      "photo_1": "https://exemple.fr/visuel.jpg",
      "logo":    {"url": "https://exemple.fr/logo.png", "fit": "contain"}
    },
    "pages": [1, 2],
    "format": "png",
    "scale": 2.0
  }'
```

Valeurs acceptées pour chaque zone :

- **texte** : chaîne, ou objet `{"text": "...", "color": "#RRGGBB", "align": "left|center|right", "size": 18}` ;
- **image** : URL `http(s)`/`data:`, référence `asset:<id>` (voir ci-dessous), ou
  objet `{"url"|"b64": "...", "fit": "cover|contain|stretch"}` (défaut `cover`).

### Déposer des images (bibliothèque d'assets)

Quand les visuels ne sont pas accessibles par URL (fichiers locaux, images
produites par l'agent), déposez-les d'abord dans la bibliothèque :

```bash
curl -X POST http://vps:8000/v1/assets -H "X-API-Key: $KEY" -F "file=@photo.jpg"
# → {"id": "9c2e41ab07d3", "ref": "asset:9c2e41ab07d3", "width": 4000, ...}
```

…puis utilisez la référence retournée comme valeur : `"photo_1": "asset:9c2e41ab07d3"`.
Dans l'interface `/ui`, chaque zone image a un bouton « Téléverser… » qui fait
tout cela en un clic, et la section « Images » liste la bibliothèque.
Routes : `GET /v1/assets` · `GET/DELETE /v1/assets/{id}`.

Réponse : les URLs des pages rendues (`GET /v1/outputs/...`, même clé API),
plus d'éventuels avertissements (placeholders sans valeur, approximations…).

### Autres routes

`GET /v1/templates` · `GET /v1/templates/{id}` · `DELETE /v1/templates/{id}` ·
`GET/POST /v1/fonts` · `GET /health`

## Utilisation par un agent IA

Le déroulé type pour un agent (voir `examples/agent_alone.py`) :

1. `GET /` puis `GET /v1/templates` pour découvrir le service et les templates ;
2. `GET /v1/templates/{id}` pour connaître les zones à remplir (noms, types,
   pages, tailles des cadres — utile pour choisir des images au bon ratio) ;
3. `POST /v1/templates/{id}/render` avec son JSON ;
4. téléchargement des PNG via les URLs retournées.

L'API étant OpenAPI-standard (`/docs`, `/openapi.json`), elle se branche
directement comme *tool* dans la plupart des frameworks d'agents.

## CLI (tests en local)

```bash
alone inspect brochure.idml
alone render brochure.idml donnees.json -o rendus/ --pages 1,2 --scale 2
```

## Limites

- **SVG (Illustrator)** : fidélité excellente via cairosvg. Points d'attention :
  incorporer les images fixes à l'export ; certains effets raster complexes
  (grain, flous artistiques) peuvent différer légèrement.
- **PSD (Photoshop)** : les calques fixes sont composités par psd-tools
  (fidèle, y compris la plupart des modes de fusion). Le texte de remplacement
  est redessiné : police/corps/couleur repris du calque d'origine, mais sans
  crénage avancé ni styles de calque (ombres, contours) sur le nouveau texte.
- **IDML (InDesign)** : rendu **simplifié** — aplats, contours, textes
  (police/corps/couleur/alignement du premier style de chaque paragraphe,
  césure simple) et images. Non reproduits : dégradés, transparences, ombres,
  habillage, tableaux, blocs pivotés (approximés), images fixes liées non
  incorporées (affichées en gris). **Conseil** : pour des maquettes InDesign
  très travaillées, exporter chaque page en arrière-plan image (placé dans un
  bloc plein-page) et ne garder en IDML « vivant » que les blocs à remplir —
  ou préférer le circuit Illustrator/SVG.
- Fichiers `.ai`/`.indd` natifs : non lisibles sans Adobe (format fermé) ;
  l'API renvoie un message expliquant quel export utiliser.

## Feuille de route possible

- File d'attente asynchrone pour les gros volumes (job_id + webhook) ;
- export PDF multi-pages ;
- backend Scribus optionnel pour un rendu IDML haute-fidélité ;
- écriture de fichiers natifs via les API cloud Adobe (payantes) pour les
  clients qui en ont besoin.

## Développement

```bash
pip install -e .[dev]
pytest            # 31 tests : moteurs SVG/PSD/IDML, polices, valeurs, API
```

Arborescence : `alone/engines/` (un moteur par format), `alone/api.py`
(FastAPI), `alone/fonts.py`, `alone/images.py`, `alone/registry.py`,
`tests/` (fixtures SVG/IDML générées, doublures PSD).
