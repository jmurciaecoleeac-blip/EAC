# Architecture — Aréopage V0.2

## Vue d'ensemble

V0.2 pose la **fondation de données** du conseil. Trois modules :

| Module | Rôle |
|---|---|
| `areopage.enums` | vocabulaire fermé du domaine (StrEnum) |
| `areopage.models` | modèles Pydantic 2 stricts |
| `areopage.storage` | persistance SQLite minimale (stdlib) |

Aucune orchestration, aucun client d'agent, aucun moteur de consolidation :
ces éléments arriveront en V0.3+ et s'appuieront sur ces modèles.

## Cycle de vie d'une session

```
CREATED → FIRST_ROUND → REVIEW → SECOND_ROUND → COMPLETED
                                       └────────→ FAILED (à tout moment)
```

1. **Ingestion** : un `SourceDocument` immuable est construit ; son SHA-256
   est calculé et vérifié à la construction.
2. **Premier tour** : chaque agent produit une `FirstRoundAnalysis`
   indépendante (constats `Finding` + `ConfidenceAssessment`).
3. **Revue croisée** : chaque agent prend position sur les constats adverses
   via des `ReviewDecision` (CONFIRMED / CORRECTED / REJECTED, justification
   obligatoire pour les deux derniers).
4. **Second tour** : `SecondRoundAnalysis` = décisions de revue + nouveaux
   constats.
5. **Verdict** : `CouncilVerdict` agrège constats retenus, recommandations,
   données manquantes et confiance globale. En V0.2 c'est un simple
   conteneur : sa production est manuelle ou déléguée aux versions futures.

## Modèles

- **SourceDocumentMetadata** *(immuable)* — nom de fichier, type MIME,
  taille, langue, origine, date d'ingestion.
- **SourceDocument** *(immuable)* — id, métadonnées, contenu, SHA-256
  vérifié contre le contenu. Toute correction = nouveau document.
- **Finding** — constat d'agent ; `author` obligatoire, catégorie, gravité,
  titre, description, preuve optionnelle.
- **ConfidenceAssessment** — score borné [0, 100] + justification.
- **FirstRoundAnalysis** — agent, référence au document, constats, résumé,
  confiance.
- **ReviewDecision** — position d'un agent sur un constat ; justification
  imposée par validateur pour CORRECTED et REJECTED.
- **SecondRoundAnalysis** — décisions de revue + nouveaux constats.
- **MissingData** — donnée absente nécessaire, avec impact et auteur.
- **Recommendation** — action proposée, priorisée par gravité.
- **CouncilVerdict** — synthèse finale (conteneur de données en V0.2).
- **CouncilSession** — agrégat racine : document, statut, analyses des deux
  tours, verdict optionnel.

## Invariants transverses

- `extra="forbid"` sur tous les modèles : un champ inconnu est une erreur.
- Identifiants : `uuid.UUID` (v4 par défaut).
- Dates : `pydantic.AwareDatetime` — une date naïve est rejetée ; l'usine
  par défaut est `utcnow()` (UTC).
- Sérialisation stable : `to_stable_json()` produit un JSON déterministe
  (clés triées, séparateurs compacts, UTF-8 préservé) ; `from_json()`
  restaure le modèle. Propriété testée : round-trip sans perte.

## Persistance

`SessionRepository` stocke chaque `CouncilSession` sous sa forme JSON stable
dans une table SQLite unique (`council_sessions`), avec upsert par id.
SQLite joue le rôle de journal durable ; aucun ORM, aucun chemin codé en
dur — le chemin de la base est fourni par l'appelant.

## Ce que V0.2 ne fait volontairement pas

- pas d'appels à Claude Code ni Codex CLI ;
- pas de clés API ni configuration réseau ;
- pas d'interface graphique ;
- pas de moteur de consolidation du verdict ;
- pas de migration de schéma SQLite (table unique, créée si absente).
