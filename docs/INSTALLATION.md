# Guide d'installation — Agent ZEUS

Ce guide explique comment installer et activer l'agent ZEUS sur une machine.

ZEUS tourne sur **[Hermes Agent](https://hermes-agent.nousresearch.com/docs)**.
Il suffit donc d'installer Hermes, puis d'y déposer la définition (`SOUL.md`),
la configuration et les compétences (`skills/`).

---

## Prérequis

| Élément | Requis |
|---|---|
| Système | Linux, macOS ou Windows (WSL recommandé) |
| Hermes Agent | Version à jour |
| Git | Pour cloner ce dépôt |
| Compte fournisseur LLM | Clé API (Nous, OpenRouter, Anthropic, Gemini…) |

---

## Étape 1 — Installer Hermes Agent

```bash
# Installation de Hermes (voir la documentation officielle pour la commande à jour)
# https://hermes-agent.nousresearch.com/docs
```

Puis vérifie que Hermes fonctionne :

```bash
hermes --version
```

---

## Étape 2 — Cloner ce dépôt

```bash
git clone https://github.com/armandloukou36-bot/zeus-agent.git
cd zeus-agent
```

> Le dépôt est **privé** : il faut être connecté au compte
> `armandloukou36-bot` (`gh auth login` ou un jeton d'accès personnel).

---

## Étape 3 — Installer la définition de l'agent (SOUL.md)

Le fichier `SOUL.md` contient le prompt système qui fait de l'agent un
**Application & Website Builder**.

```bash
# Sauvegarde de l'ancien fichier s'il existe
[ -f ~/.hermes/SOUL.md ] && cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak

# Installation de la définition ZEUS
cp SOUL.md ~/.hermes/SOUL.md
chmod 600 ~/.hermes/SOUL.md
```

---

## Étape 4 — Installer les compétences (skills)

```bash
# Copier les 64 compétences dans le dossier des skills de Hermes
cp -r skills/. ~/.hermes/skills/
```

Vérification :

```bash
find ~/.hermes/skills -name "SKILL.md" | wc -l
# Doit afficher un nombre >= 64
```

---

## Étape 5 — Configurer les variables d'environnement

Le fichier `config/env.example` liste les **noms** des variables nécessaires
(valeurs vides pour la sécurité).

```bash
# Créer le fichier de configuration réel
cp config/env.example ~/.hermes/.env
chmod 600 ~/.hermes/.env

# Puis éditer et remplir les clés API
nano ~/.hermes/.env
```

> ⚠️ **Ne commitez jamais** `~/.hermes/.env` : il contient tes clés API.

### Variables principales

| Variable | Rôle |
|---|---|
| `NOUS_API_KEY` | Fournisseur Nous (ou autre selon ta configuration) |
| `OPENROUTER_API_KEY` | Fournisseur OpenRouter |
| `ANTHROPIC_API_KEY` | Fournisseur Anthropic (Claude) |
| `GOOGLE_API_KEY` | Fournisseur Google Gemini |
| `GITHUB_TOKEN` | Accès GitHub (via `gh auth login`) |
| `SUPABASE_ACCESS_TOKEN` | Accès Supabase (si utilisé) |

Il est aussi possible d'utiliser l'assistant intégré :

```bash
hermes setup
```

---

## Étape 6 — (Optionnel) Appliquer la configuration

Le fichier `config/config.example.yaml` est une configuration Hermes de
référence **assainie**. Pour l'utiliser :

```bash
# ATTENTION : remplace la configuration existante — fais une sauvegarde d'abord
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
cp config/config.example.yaml ~/.hermes/config.yaml
```

> La plupart du temps, il est préférable de **conserver sa propre
> configuration** et de n'y copier que les réglages souhaités (modèle,
> fournisseur, préférences).

---

## Étape 7 — Vérifier l'installation

```bash
# Lancer Hermes
hermes
```

L'agent doit s'identifier comme **ZEUS — Application & Website Builder Agent**.

Test rapide :

```
Donne-moi ton rôle et ta mission.
```

La réponse doit mentionner l'architecture, le développement full-stack, les
tests, la sécurité, le SEO et le déploiement.

---

## Étape 8 — Authentifier GitHub (recommandé)

Pour que ZEUS puisse gérer des dépôts, des PR et des déploiements :

```bash
gh auth login
gh auth status
```

Scopes recommandés : `repo`, `workflow`, `read:org`, `gist`.

---

## Dépannage

| Problème | Solution |
|---|---|
| L'agent ne répond pas en ZEUS | Vérifier que `~/.hermes/SOUL.md` a bien été copié |
| `skills` non reconnues | Vérifier le chemin `~/.hermes/skills/` et relancer Hermes |
| Erreur d'authentification | Vérifier les clés dans `~/.hermes/.env` puis `hermes auth status` |
| GitHub refuse l'accès | `gh auth login` avec les bons scopes |

---

## Mise à jour de l'agent

```bash
cd zeus-agent
git pull
cp SOUL.md ~/.hermes/SOUL.md
cp -r skills/. ~/.hermes/skills/
```

---

## Désinstallation

```bash
rm ~/.hermes/SOUL.md
# puis restaurer la sauvegarde éventuelle :
# cp ~/.hermes/SOUL.md.bak ~/.hermes/SOUL.md
```

---

© 2026 LKG ENTREPRISES — Document interne.
