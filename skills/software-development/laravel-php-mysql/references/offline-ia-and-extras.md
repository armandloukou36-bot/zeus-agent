# Offline IA, WhatsApp, and multi-pays extras (no external API key)

This user repeatedly asks for features (IA copilote, WhatsApp receipts, multi-pays) that the
cahier des charges marks as needing an external API key (LLM, WhatsApp Business, payment
aggregator). When no key is available, deliver a working OFFLINE equivalent rather than
blocking. These patterns are proven on the restaurant platform.

## Rule-based copilot (IA-04) without an LLM key

Build a `CopilotService` that answers French questions by keyword-matching against the
question and returning real data from the DB. No LLM call, works offline, fast.

- Normalize the question: `mb_strtolower`, strip `? ! .`, fold accented chars
  (`é/è/ê → e`, `’ → '`) so keyword matching is robust.
- Route by keyword groups, each returning a computed answer:
  - `meilleur marge / plus rentable / benef` → menu-engineering matrix, sort by margin, top item.
  - `ca du jour / chiffre affaire` → sum of today's payments + order count.
  - `top produit / plus vendu` → top-N order_items by qty over 30 days.
  - `stock bas / rupture / manque` → ingredients where `stock_qty <= min_stock`.
  - `commande en cours` → open orders count.
  - `prevision / demain` → ForecastService result.
- Fallback: list the capabilities the copilot understands, so the user learns what to ask.
- Expose `POST /copilot/ask` returning `{answer}`; the view is a chat box with a
  Web Speech API mic button (`webkitSpeechRecognition`, `lang='fr-FR'`) that fills the input
  and submits. Voice works in Chrome; guard with a fallback alert otherwise.
- Empty-data answers should be instructive, not dead ends: "Pas encore assez de ventes pour
  calculer les marges. Encaisssez quelques commandes d'abord."

## WhatsApp receipt without the Business API

Use a `wa.me` deep link — free, no API key, opens the client's WhatsApp with a prefilled
message. On the receipt view, if the order has a customer phone:

```blade
<a href="https://wa.me/{{ preg_replace('/[^0-9]/', '', $order->customer_phone) }}?text={{ urlencode('Votre reçu ' . $order->order_number) }}" target="_blank">💬 Reçu WhatsApp</a>
```

If no phone, render the button disabled with a tooltip explaining why. This is the
"receipt by WhatsApp" requirement satisfied without any integration.

## Thermal printing (58/80mm) from a browser

- Keep the printable ticket in a `#ticket` div sized `width: 80mm`; put action buttons
  (print, WhatsApp) in a `.toolbar` that is `display:none` under `@media print`.
- Auto-print on load: `window.onload = () => setTimeout(() => window.print(), 300);` and
  close after: `window.onafterprint = () => setTimeout(() => window.close(), 200);`.
- Use the establishment's `currency_symbol` on the total, not a hardcoded `FCFA`.

## Multi-pays / multi-devises

- Add `country` (default 'Côte d\'Ivoire') and `currency_symbol` (default 'FCFA') columns to
  `establishments`; keep `currency` as the ISO code. Use `currency_symbol` in all money
  display (receipts, dashboards) so a GNF/NGN site renders its own symbol.
- A **consolidation view** (direction/owner only, `abort(403)` otherwise) maps over all
  active establishments and aggregates today's revenue, order count, and open orders per
  site, plus totals. This satisfies the multi-établissement comparison requirement.
- Add the consolidation link to the sidebar only for `auth()->user()->isManager()`.

## General rule

When a feature needs an external key the user does not have, deliver the offline
equivalent that satisfies the observable requirement (answers questions, sends a receipt,
prints a ticket) and note explicitly what the paid/API version would add. Do not block the
whole feature on the missing credential.
