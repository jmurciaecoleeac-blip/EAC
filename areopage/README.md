# Aréopage — Fondation technique V0.2

Aréopage est un conseil d'agents d'analyse documentaire : plusieurs agents
(Claude Code, Codex CLI) analysent indépendamment un même document, se
relisent mutuellement, puis un verdict consolidé est produit.

**Périmètre V0.2 : uniquement la fondation.** Modèles de domaine stricts,
énumérations, persistance SQLite minimale et tests. Aucune orchestration
d'agents, aucun appel réseau, aucune clé API, aucune interface graphique,
aucun moteur de consolidation.

## Pile technique

- Python 3.13
- Pydantic 2 (validation stricte)
- pytest
- SQLite via la bibliothèque standard (`sqlite3`)

## Installation

```bash
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Tests

```bash
.venv/bin/pytest
```

## Structure

```
areopage/
├── pyproject.toml
├── src/areopage/
│   ├── enums.py      # AgentName, Severity, FindingCategory, ReviewPosition, SessionStatus
│   ├── models.py     # modèles de domaine (SourceDocument … CouncilSession)
│   └── storage.py    # SessionRepository (SQLite, stdlib)
├── tests/
└── docs/
    ├── ARCHITECTURE.md
    ├── SECURITY_MODEL.md
    └── ENVIRONMENT_AUDIT.md
```

## Garanties de domaine

- identifiants UUID, dates toujours horodatées avec fuseau ;
- SHA-256 du document vérifié contre son contenu à la construction ;
- document source immuable ;
- score de confiance borné à [0, 100] ;
- auteur obligatoire pour chaque constat ;
- justification obligatoire pour les positions `CORRECTED` et `REJECTED` ;
- sérialisation JSON stable (clés triées, déterministe).

Voir `docs/ARCHITECTURE.md` pour le détail des modèles et
`docs/SECURITY_MODEL.md` pour les hypothèses de sécurité.
