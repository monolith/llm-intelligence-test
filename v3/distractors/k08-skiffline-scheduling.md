# SKIFFLINE Municipal Ferry Scheduling Service, Interface Specification v2.4 — Kelmond Harbor Transit Authority, Engineering Standards Group (2023)

## 1. Purpose

SKIFFLINE is the authoritative scheduling and dispatch service for the Kelmond municipal ferry
network. It owns the published timetable, the live sailing board, the reservation ledger for
vehicle decks, and the tide-window constraints that govern the two shallow berths at Lowgate and
Ferrn Point. All consumer applications — the public web board, the terminal display units, the
deckhand handhelds, and the Authority's own operations console — read from SKIFFLINE and write
nothing except through the endpoints below.

SKIFFLINE does **not** own vessel maintenance records, fare collection, or crew rostering. Those
live in MOORING (maintenance) and PAYWELL (fares) respectively and are joined by
`vessel_id` and `sailing_id`.

Non-goals for v2.4: multi-operator federation, foot-passenger reservations, and any form of
dynamic pricing.

## 2. Data model

### 2.1 Route

| field | type | notes |
|---|---|---|
| `route_id` | string, `RT-` + 3 digits | e.g. `RT-104` |
| `name` | string, ≤ 48 chars | e.g. "Lowgate – Ferrn Point" |
| `origin_berth` | berth_id | |
| `dest_berth` | berth_id | |
| `nominal_crossing_min` | integer, 4–180 | scheduled water time |
| `vehicle_capable` | boolean | false for the two passenger-only routes |
| `seasonal` | boolean | if true, `active_window` is required |

The network currently defines nine routes, of which six are vehicle-capable.

### 2.2 Berth

| field | type | notes |
|---|---|---|
| `berth_id` | string, `BR-` + 2 digits | `BR-01` … `BR-14` |
| `name` | string | |
| `min_draft_m` | decimal(3,2) | 1.10 at Lowgate, 2.45 at Kelmond Main |
| `tide_gated` | boolean | true for `BR-03` and `BR-11` only |
| `ramp_class` | enum `A`\|`B`\|`C` | class C accepts no vehicle above 7.5 t |

### 2.3 Sailing

A **sailing** is one scheduled departure of one vessel on one route.

| field | type | notes |
|---|---|---|
| `sailing_id` | string, `SL-` + 8 digits | monotonic, not sequential |
| `route_id` | route_id | |
| `vessel_id` | string, `VS-` + 3 digits | |
| `scheduled_depart` | RFC 3339, always with offset | |
| `state` | enum | see 2.4 |
| `deck_slots_total` | integer, 0–86 | |
| `deck_slots_held` | integer | ≤ `deck_slots_total` |
| `tide_window` | object or null | `{opens, closes}`, null if berths not gated |
| `etag` | opaque string | required for all mutations |

### 2.4 Sailing state machine

```
PLANNED ──publish──> PUBLISHED ──board──> BOARDING ──depart──> UNDERWAY ──arrive──> ARRIVED
   │                     │                    │
   └──cancel──> CANCELLED┴────cancel──────────┘
```

`UNDERWAY` may not transition to `CANCELLED`. A sailing in `ARRIVED` is immutable except for the
`actual_arrive` field, which may be corrected once within 90 minutes by an operator holding the
`sched.correct` scope.

### 2.5 Deck reservation

| field | type | notes |
|---|---|---|
| `res_id` | string, `RS-` + 10 chars, base32 | |
| `sailing_id` | sailing_id | |
| `plate` | string, ≤ 10 chars, upper | normalized: strip spaces and hyphens |
| `length_class` | enum `S`\|`M`\|`L`\|`XL` | consumes 1, 1, 2, 3 deck slots |
| `hold_expires` | RFC 3339 | default now + 20 min |
| `confirmed` | boolean | |

## 3. Endpoints

Base path `/v2`. All requests carry `X-Skiffline-Key`. All responses are `application/json`
with `Content-Language: en`.

### 3.1 `GET /v2/routes`

Returns all routes. Query params: `vehicle_capable` (bool), `active_on` (date).
Cacheable for 3600 s.

### 3.2 `GET /v2/sailings`

Required: `route_id`, `from` (RFC 3339), `to` (RFC 3339). The span `to − from` may not exceed
14 days; a longer span returns `SKF-2201`.

Optional: `state` (repeatable), `min_free_slots` (integer), `page_size` (default 50, max 200),
`cursor`.

Response envelope:

```json
{
  "items": [ ... ],
  "next_cursor": "c2FpbGluZzo0NDcx",
  "server_time": "2023-09-14T06:12:03-04:00"
}
```

### 3.3 `POST /v2/sailings/{sailing_id}/hold`

Places a soft hold on deck slots. Body:

```json
{
  "plate": "KLM4482",
  "length_class": "M",
  "hold_minutes": 20
}
```

`hold_minutes` is clamped to `[5, 45]`. Returns `201` with the reservation object and a
`Location` header. Idempotency: repeat the call with the same `Idempotency-Key` header within
600 s to receive the identical `res_id`.

### 3.4 `POST /v2/reservations/{res_id}/confirm`

Requires header `If-Match` bearing the reservation `etag`. Converts a hold into a confirmed
booking and decrements nothing — slot accounting happens at hold time, not confirm time. This
is deliberate and has surprised three separate integrators; see §6.

### 3.5 `DELETE /v2/reservations/{res_id}`

Releases slots immediately. Returns `204`. Deleting an already-deleted reservation returns `204`
as well, not `404`.

### 3.6 `PATCH /v2/sailings/{sailing_id}`

Operator-only. Permitted field set depends on state:

| state | patchable |
|---|---|
| `PLANNED` | all except `sailing_id` |
| `PUBLISHED` | `vessel_id`, `deck_slots_total`, `scheduled_depart` (≤ 25 min shift) |
| `BOARDING` | `deck_slots_total` (decrease only) |
| `UNDERWAY` | none |

A `scheduled_depart` shift greater than 25 minutes must be expressed as a cancellation plus a new
sailing, so that downstream displays do not silently move a departure a rider has already
planned around.

### 3.7 `GET /v2/tide-windows`

Params: `berth_id`, `date`. Returns up to four windows per berth per day, each with `opens`,
`closes`, and `predicted_min_depth_m`. Windows narrower than 35 minutes are suppressed and
reported in the `suppressed_count` field.

## 4. Error codes

All errors use HTTP status plus a stable code in `error.code`.

| code | HTTP | meaning |
|---|---|---|
| `SKF-1001` | 401 | missing or unknown API key |
| `SKF-1004` | 403 | key lacks required scope |
| `SKF-2201` | 400 | query span exceeds 14 days |
| `SKF-2207` | 400 | `plate` fails normalization |
| `SKF-2212` | 400 | `length_class` not one of S, M, L, XL |
| `SKF-3301` | 409 | insufficient free deck slots |
| `SKF-3304` | 409 | `etag` mismatch on `If-Match` |
| `SKF-3309` | 409 | illegal state transition |
| `SKF-3311` | 409 | vessel `min_draft_m` exceeds berth depth in the requested tide window |
| `SKF-4402` | 422 | `scheduled_depart` shift exceeds 25 minutes in `PUBLISHED` |
| `SKF-4408` | 422 | sailing has no tide window on the requested date |
| `SKF-5502` | 503 | tide predictor unavailable; retry after `Retry-After` |

Clients must treat any unrecognized `SKF-5xxx` as retryable and any `SKF-2xxx` or `SKF-4xxx` as
permanent for the given payload.

## 5. Worked example

Book one medium vehicle on the 07:40 Lowgate departure.

```
GET /v2/sailings?route_id=RT-104&from=2023-09-14T00:00:00-04:00&to=2023-09-15T00:00:00-04:00
→ 200, items[3].sailing_id = "SL-40917266", deck_slots_total 62, deck_slots_held 58

POST /v2/sailings/SL-40917266/hold
    Idempotency-Key: 9f2c-0041
    {"plate":"KLM4482","length_class":"M","hold_minutes":20}
→ 201, res_id "RS-7QK2MJ4A0B", hold_expires 2023-09-14T06:32:03-04:00

POST /v2/reservations/RS-7QK2MJ4A0B/confirm
    If-Match: "w/8812-3"
→ 200, confirmed true
```

Had `deck_slots_held` been 62, the hold would have returned `SKF-3301` with a `retry_sailings`
array naming the next two departures on the same route with free capacity.

## 6. Known sharp edges

1. Slot accounting occurs at hold, not confirm (§3.4). An abandoned hold ties up capacity for up
   to 45 minutes.
2. `XL` consumes three slots but is refused outright at ramp class C berths, which produces
   `SKF-3311`, not `SKF-2212`. The code is arguably wrong and is retained for compatibility.
3. `next_cursor` is not stable across a `PATCH` to any sailing in the page. Re-issue from `from`.
