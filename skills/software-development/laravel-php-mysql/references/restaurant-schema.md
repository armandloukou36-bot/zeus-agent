# Restaurant platform — multi-tenant schema (Lots 1–4)

Table layout used for the restaurant management platform. All business tables carry `establishment_id` for multi-tenant isolation (RLS-equivalent via scoping every query by the user's establishment).

## Core tables
- **establishments** — name, legal_name, ncc (DGI tax number), address, phone, currency (FCFA), timezone, logo_path, is_active.
- **users** — extends Laravel's users with: establishment_id, role (owner/manager/cashier/server/kitchen/bar/stock), first_name, last_name, phone, pin (6-digit for sensitive actions), is_active.
- **zones** — salle zones (Terrasse, Salle, VIP): establishment_id, name, sort_order.
- **tables** — establishment_id, zone_id, name, qr_token (unique, per-table QR), capacity, status (free/occupied/order_sent/ready/bill_requested/to_clean).
- **stations** — production posts (Grill, Friture, Froid, Pâtisserie, Bar, Passe): establishment_id, name, type (kitchen/bar/pass), sort_order. KDS routes each item to its station.

## Menu
- **categories** — establishment_id, name, sort_order, is_active.
- **products** — establishment_id, category_id, station_id, name, description, photo_path, price, allergens (json array), spice_level (0-3), prep_time_min, barcode, is_active, is_available, sort_order.
- **product_options** — establishment_id, product_id (null = global option), name, type (single/multiple), required, sort_order.
- **product_option_choices** — option_id, name, price_delta, is_default, sort_order.

## Orders & payments
- **orders** — establishment_id, table_id, user_id (server), order_number (#2925), channel (dine_in/takeaway/delivery/counter), status (open/sent/in_progress/ready/served/paid/cancelled), guest_count, customer_name/phone, note, subtotal, discount, total, sent_at, paid_at.
- **order_items** — order_id, product_id, station_id, product_name (snapshot), unit_price, quantity, notes ("bien cuit", allergy — shown red in kitchen), status (new/in_progress/ready/served/cancelled), wave (starter/main/dessert for deferred sending), sort_order.
- **order_item_options** — order_item_id, option_name, choice_name, price_delta.
- **payments** — order_id, user_id, method (cash/card/orange_money/mtn_momo/moov/wave/voucher/account), amount, change_due, reference.
- **cash_sessions** — establishment_id, user_id, opening_amount, closing_amount, counted_amount, difference, status (open/closed), opened_at, closed_at. (POS open/close + Z report.)

## Real-time & audit
- **events** — establishment_id, type (order.sent, item.ready, table.status, payment.made...), payload (json), created_at. Indexed by (establishment_id, created_at). SSE endpoint polls this table.
- **audit_logs** — establishment_id, user_id, action, entity_type, entity_id, details (json), ip, created_at. For sensitive actions (cancellation, discount, cash-drawer open).

## Stock (Lot 2)
- **depots** — establishment_id, name, type (storage/kitchen/bar). Multi-depot (réserve, cuisine, bar).
- **ingredients** — establishment_id, depot_id, name, unit (g/kg/l/cl/unité), stock_qty, min_stock, cost (purchase unit cost), barcode. `isLowStock()` = min_stock>0 && stock_qty<=min_stock.
- **recipe_items** — establishment_id, product_id, ingredient_id, quantity. Unique (product_id, ingredient_id). The fiche technique: each sale destocks `quantity × item.quantity` of each ingredient.
- **stock_movements** — establishment_id, ingredient_id, depot_id, type (in/out/sale/loss/transfer_in/transfer_out), quantity (negative for out/sale/loss), unit_cost, reference (order # or invoice), reason (casse/périmé/repas_personnel), user_id, created_at. Indexed by (ingredient_id, created_at).
- **suppliers** — establishment_id, name, contact, phone, email, address.

## Loyalty & customers (Lot 2)
- **customers** — establishment_id, name, phone, email, loyalty_points, loyalty_tier (0=standard/1=argent/2=or), total_spent. Indexed by (establishment_id, phone).
- **loyalty_transactions** — establishment_id, customer_id, order_id, type (earn/redeem), points, reason, created_at.

## Reservations (Lot 3, INN-02)
- **reservations** — establishment_id, table_id (nullable), customer_name, customer_phone, guests, reserved_at, status (pending/confirmed/cancelled/completed/no_show), deposit (Mobile Money acompte), deposit_method, note. Indexed by (establishment_id, reserved_at).

## Delivery (Lot 4, INN-04)
- **couriers** — establishment_id, user_id (nullable), name, phone, vehicle (moto/vélo/voiture/pied), is_available, is_active.
- **deliveries** — establishment_id, order_id, courier_id (nullable), status (pending/assigned/picked_up/in_transit/delivered/returned/cancelled), contact_name/phone, address, city, landmark, delivery_fee, collected_amount (encaissé à la livraison), payment_method, assigned_at/picked_up_at/delivered_at. Indexed by (establishment_id, status).
- **Delivery lifecycle**: creating a delivery with a courier sets status `assigned` + `assigned_at`; marking `delivered` pays the order (creates a Payment for `collected_amount`, sets order `paid`, destocks) — encaissement à la livraison. Order needs a `delivery()` hasOne relation for `whereDoesntHave('delivery')` to find undelivered orders.

## Dynamic pricing & events (Lot 4)
- **price_rules** (IA-10) — establishment_id, product_id (null = global), name, day_of_week (monday...sunday or 'all'), start_time/end_time (TIME columns — compare as strings via substr), discount_percent (0-90), is_active. `PricingService::effectivePrice()` returns base/effective/discount_percent/is_discounted/rule_name.
- **event_models** (INN-06) — establishment_id, name, starts_at/ends_at, entry_fee (billetterie), is_active. Only one active at a time (toggle deactivates others).
- **event_model_products** — event_model_id, product_id, price (fixed event price, nullable), is_included (consommations prépayées incluses).

## Key model relations
- Establishment hasMany: users, zones, tables, stations, categories, products, orders.
- Order belongsTo table/user; hasMany items, payments. OrderItem belongsTo order/product/station; hasMany options.
- `Order::isOpen()` = status not in [paid, cancelled]. `Table::activeOrder()` = latest non-paid order.
- Product hasMany recipe_items (via RecipeItem). Ingredient hasMany stock_movements. Customer hasMany loyalty_transactions.

## Business rules wired into payment (Lot 2)
- On `pay()`: destock via `StockService::destockOrder($order)` (reads recipe_items, decrements ingredient stock, writes sale movements) and, if `customer_phone` provided, credit loyalty via `LoyaltyService::earnPoints($order, $phone)` (1 point per 1000 FCFA, tier by total_spent). Both run inside the payment DB transaction.
- **Destocking and loyalty fire on PAYMENT, not on order creation** — a client/QR order sits at `sent` with stock untouched until the cashier settles it. Verify stock after paying, not after ordering.

## Seeding note
Seed data must reference parent rows by the EXACT string keys used to create them (e.g. category `'Plats'` not `'Plat'`) or FK lookups return null and the seeder crashes. See SKILL.md seeding pitfalls.
