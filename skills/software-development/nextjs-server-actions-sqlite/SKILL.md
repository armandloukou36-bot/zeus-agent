---
name: nextjs-server-actions-sqlite
description: Use for Next.js 14 Server Actions + node:sqlite apps.
---

# Next.js 14 App Router + node:sqlite : pièges vérifiés

Application testée : app de gestion immobilière (CRUD complet, auth, Server Actions).

## Pièges bloquants (rencontrés en production)

### 1. `node:sqlite` renvoie des objets à prototype nul
React refuse de sérialiser ces lignes d'un Server Component vers un Client Component :

```
Error: Only plain objects, and a few built-ins, can be passed to Client
Components from Server Components. Classes or null prototypes are not supported.
```

**Correctif** : envelopper `db.prepare` pour normaliser chaque ligne **une seule fois**, au lieu de patcher chaque requête :

```ts
function normalizeRows(db: DatabaseSync): DatabaseSync {
  const originalPrepare = db.prepare.bind(db);
  (db as any).prepare = (sql: string) => {
    const st = originalPrepare(sql);
    const all = (st as any).all.bind(st);
    const get = (st as any).get.bind(st);
    (st as any).all = (...p: any[]) => all(...p).map((r: any) => ({ ...r }));
    (st as any).get = (...p: any[]) => { const r = get(...p); return r === undefined ? undefined : { ...r }; };
    return st;
  };
  return db;
}
const db = normalizeRows(new DatabaseSync(DB_PATH));
```

### 2. React 18.3 n'a pas `useActionState`
`useFormState` / `useActionState` n'existent pas avant React 19. Vérifier **avant** de concevoir les formulaires :
`grep -r "useFormState" node_modules/react-dom/`.

Solution : composant `ActionForm` maison (contexte de pending + `onSubmit` qui appelle l'action).

### 3. `redirect()` ne renvoie AUCUNE valeur
Une Server Action terminant par `redirect()` retourne `undefined`. Lire `result.ok` lève :
`TypeError: Cannot read properties of undefined (reading 'ok')`

**Correctif** : `const result = await action(fd); if (!result) return;`

### 4. Les dossiers préfixés `_` sont privés dans `app/`
`app/api/_selftest/route.ts` → 404. Nommer sans underscore : `app/api/selftest/route.ts`.

### 5. Ne PAS mettre `action={...}` sur un form client avec `onSubmit`
Un `<form>` client avec `action` + `onSubmit` : le POST natif recharge la page **sans exécuter** l'action (car `e.preventDefault()` bloque la soumission RSC). Résultat : formulaire silencieusement inopérant. Garder uniquement `onSubmit`.

### 6. Page statique = POST servi depuis le cache
`x-nextjs-cache: HIT` sur un POST signifie que la page est prérendue : le POST ne déclenche rien. Les pages avec formulaire doivent être dynamiques (`cookies()`/`headers()`).

## Tester réellement (indispensable)

Un POST `curl` brut ne suffit pas : les Server Actions exigent le champ `$ACTION_ID_<hash>` **et** un payload RSC. Le navigateur bloqué sur `localhost` (adresse privée) impose Playwright.

```bash
npm i playwright-core && npx playwright install chromium --with-deps
# binaire : /root/.cache/ms-playwright/chromium-*/chrome-linux64/chrome
```

Parcours à couvrir : accueil → redirection anonyme → connexion → navigation → créer/modifier/supprimer → validation champ vide → recherche/filtre → paiement → onglets → déconnexion → inscription → **collecter `pageerror`**.

## Pièges de test (faux négatifs)

- `textContent('body')` inclut le **JSON des scripts Next.js** : une chaîne absente de l'écran peut apparaître. Vérifier le **DOM visible** (`table tbody tr`), pas le corps brut.
- Plusieurs `<form>` par page (déconnexion dans l'en-tête !) : `page.click('form button')` peut cliquer Déconnexion. Cibler par libellé.
- Une session en base peut être invalidée par un `login()` ultérieur dans le même test : restaurer la session admin après avoir testé un autre compte.

## Vérifier un Server Action côté serveur sans navigateur

Exposer une route temporaire appelant directement les actions, avec un cookie de session créé via un script `node:sqlite`, puis la supprimer avant livraison. Utile pour tester les cas limites (validation, doublons, effets métier).
