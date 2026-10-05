# ZEUS — Application & Website Builder Agent

> Agent autonome de conception, développement, test, optimisation et déploiement
> d'applications web et de sites internet.

**Version :** 1.0.0 · **Propriétaire :** LKG ENTREPRISES (Armand Loukou) · **Dépôt :** privé

---

## Qu'est-ce que ZEUS ?

ZEUS n'est pas un simple générateur de code : c'est un **agent de livraison
logicielle** qui raisonne comme une petite équipe de développement complète.

| Casquette | Rôle |
|---|---|
| Product Owner / Business Analyst | Comprend le besoin, lève les ambiguïtés |
| UX/UI Designer | Structure l'interface, le parcours utilisateur |
| Software Architect | Conçoit l'architecture, la stack, les modules |
| Front-End Developer | Développe les interfaces responsive |
| Back-End Developer | Développe la logique métier, les API |
| Database Engineer | Conçoit la base de données, les migrations, l'intégrité |
| QA / Test Engineer | Teste chaque workflow critique |
| SEO Specialist | Optimise le référencement et la performance |
| DevOps / Deployment Engineer | Build, déploie, vérifie après déploiement |

**Approche :**
`Understand → Architect → Build → Test → Fix → Optimize → Deploy → Verify`

**Principe directeur :**
`Correctness > Security > Maintainability > Performance > Speed`

---

## Structure du dépôt

```
zeus-agent/
├── SOUL.md                    # Définition de l'agent (prompt système ZEUS)
├── README.md                  # Ce fichier
├── CHANGELOG.md               # Historique des versions
├── LICENSE                    # Licence (propriétaire)
├── .gitignore                 # Exclusion des secrets et artefacts
├── config/
│   ├── config.example.yaml    # Configuration Hermes assainie (aucun secret)
│   └── env.example            # Noms des variables d'environnement (valeurs vides)
├── docs/
│   └── INSTALLATION.md        # Guide d'installation pas-à-pas
└── skills/                    # 64 compétences (4 Mo)
    ├── autonomous-ai-agents/  # claude-code, codex, hermes-agent, opencode…
    ├── creative/              # design, p5js, manim, infographies…
    ├── devops/                # sdlc-review
    ├── email/                 # himalaya, triage de boîte mail
    ├── media/                 # gif-search, songsee, youtube-content
    ├── note-taking/           # obsidian
    ├── productivity/          # docx, xlsx, pdf, powerpoint, notion, airtable…
    ├── research/              # arxiv, veille concurrentielle, citations
    ├── social-media/          # xurl (X/Twitter)
    ├── software-development/  # laravel-php-mysql, supabase, TDD, debugging…
    └── web/                   # récupération de pages bloquées
```

---

## Ce que ZEUS sait faire

### Applications
Comprendre → analyser → architecturer → concevoir la base de données → coder →
intégrer → tester → corriger → sécuriser → documenter → déployer → vérifier.

### Sites web
Comprendre → structurer → UX/UI → développer → responsive → SEO → performance →
tester → corriger → déployer → vérifier.

### Champs d'action
Nouvelle application · nouveau site · fonctionnalité · module · API · base de
données · correction de bug · refonte · optimisation · projet existant ·
déploiement.

---

## Compétences techniques (skills embarquées)

Les skills sont des procédures réutilisables que l'agent charge à la demande.
Elles couvrent notamment :

- **Laravel / PHP / MySQL** — construction d'apps web complètes
- **Supabase** — installation, auth, projets, `db push`
- **Next.js 14 + Server Actions + SQLite**
- **Test-Driven Development**, debugging systématique, revue de code
- **GitHub** via `gh` CLI — PR, issues, reviews, repos
- **Déploiement** Vercel, Docker, serveurs
- **SEO**, performance, accessibilité
- **Documents** : Word, Excel, PowerPoint, PDF

---

## Sécurité — ce qui n'est JAMAIS dans ce dépôt

| Fichier / dossier | Raison de l'exclusion |
|---|---|
| `.env` | Clés API, tokens, mots de passe |
| `auth.json` | Jetons OAuth (JWT) |
| `state.db`, `kanban.db`, `*.db` | Données de session et d'état |
| `sessions/`, `memories/`, `logs/` | Historique de conversations |
| `attachments/`, `images/` | Fichiers utilisateur |
| `cache/`, `installs/`, `tools/` | Artefacts reconstruisibles (Go) |

Le fichier `config/env.example` liste les **noms** des variables requises avec
des **valeurs vides** : aucun secret n'y figure.

> ⚠️ **Un dépôt GitHub n'est pas un coffre-fort.** Ne commitez jamais de secret,
> même dans un dépôt privé.

---

## Installation

Voir [`docs/INSTALLATION.md`](docs/INSTALLATION.md).

---

## Politique de risque

ZEUS agit **seul** pour coder, tester, modifier et exécuter des workflows.
Il demande une **validation humaine explicite** avant :

- tout déploiement en production ;
- toute publication en production ;
- la validation finale d'une release ;
- toute action irréversible (DROP, TRUNCATE, suppression massive).

Chaque approbation ne couvre que l'action présentée.

---

## Livrables

Chaque mission se termine par un **Build & Delivery Report** contenant :
architecture · base de données · développement · tests · sécurité · SEO ·
déploiement · **statut final** (`SUCCESS` | `SUCCESS WITH WARNINGS` | `BLOCKED` |
`FAILED`) — avec les preuves correspondantes.

> **Jamais de succès sans preuve. Jamais de test sauté. Jamais d'erreur masquée.**

---

## Licence

Propriétaire — © 2026 LKG ENTREPRISES. Tous droits réservés.
Voir [`LICENSE`](LICENSE).
