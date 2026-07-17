# Modèle de sécurité — Aréopage V0.2

## Périmètre

V0.2 est une bibliothèque locale sans réseau : la surface d'attaque se
limite aux données fournies par l'appelant (contenu des documents, JSON à
désérialiser, chemin de base SQLite).

## Garanties apportées par la fondation

### Intégrité du document source
- Le SHA-256 est **recalculé et vérifié** à la construction de
  `SourceDocument` : une empreinte incohérente ou mal formée est rejetée.
- Le document et ses métadonnées sont **immuables** (`frozen=True`) : toute
  tentative de modification lève une erreur de validation. La falsification
  a posteriori d'un document déjà ingéré est donc impossible par cette API.

### Traçabilité et imputabilité
- Chaque constat (`Finding`), recommandation, donnée manquante et décision
  de revue porte un **auteur obligatoire** (`AgentName`, vocabulaire fermé).
- Les positions `CORRECTED` et `REJECTED` exigent une **justification** :
  aucun rejet silencieux d'un constat adverse.
- Toutes les dates portent un fuseau horaire — pas d'ambiguïté temporelle
  dans le journal.

### Validation stricte des entrées
- `extra="forbid"` partout : l'injection de champs inattendus dans un JSON
  est rejetée à la désérialisation.
- Scores de confiance bornés [0, 100], chaînes obligatoires non vides,
  énumérations fermées.

### Persistance
- Requêtes SQLite exclusivement **paramétrées** — pas de concaténation SQL.
- Le chemin de la base est fourni par l'appelant : aucun chemin absolu codé
  en dur, aucune écriture hors du répertoire choisi par l'utilisateur.
- Une session relue depuis SQLite repasse par la validation Pydantic
  complète (y compris la vérification SHA-256 du document embarqué).

## Engagements de non-fonctionnalité (V0.2)

- **Aucun appel réseau** : ni Claude, ni Codex, ni aucun autre service.
- **Aucune clé API** manipulée, stockée ou lue depuis l'environnement.
- **Aucune exécution de code** dérivée du contenu des documents.
- `.gitignore` exclut `.env` et les fichiers de clés par défaut.

## Menaces hors périmètre V0.2 (à traiter en V0.3+)

- chiffrement au repos de la base SQLite ;
- contrôle d'accès multi-utilisateurs ;
- signature/horodatage cryptographique des verdicts ;
- sandboxing des futurs appels d'agents et validation de leurs sorties
  (les réponses d'agents devront être traitées comme non fiables) ;
- limites de taille sur le contenu des documents (risque mémoire).
