# Changelog

Toutes les modifications notables de l'agent ZEUS sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet adhère au [versionnage sémantique](https://semver.org/lang/fr/).

## [1.0.0] — 2026-10-05

### Ajouté
- Définition initiale de l'agent ZEUS (`SOUL.md`) : rôle, mission, workflow
  en 5 phases, matrice agent/risque, politique de risque, human gate,
  critères de succès et comportement en cas d'échec.
- 64 compétences (`skills/`) couvrant le développement full-stack, la base de
  données, les tests, le SEO, le déploiement et la productivité.
- Configuration Hermes assainie (`config/config.example.yaml`).
- Liste des variables d'environnement (`config/env.example`) — valeurs vides.
- Guide d'installation pas-à-pas (`docs/INSTALLATION.md`).
- Licence propriétaire LKG ENTREPRISES.

### Sécurité
- Exclusion stricte des secrets (`.env`, `auth.json`), bases de données de
  session, journaux, caches et artefacts reconstruisibles via `.gitignore`.
