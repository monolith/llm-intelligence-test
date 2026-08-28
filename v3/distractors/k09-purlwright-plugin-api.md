# Purlwright Pattern Editor — Plugin API Reference, v3.1 — Purlwright Maintainers Group (2022)

## 1. Purpose

Purlwright is a desktop editor for knitting and crochet charts. The plugin API exists so that
third parties can add stitch dictionaries, chart transformations, gauge calculators, exporters,
and live validators without forking the editor.

A plugin is a directory containing a `plugin.toml` manifest and one or more JavaScript modules.
Plugins run in a worker isolate with no filesystem or network access; all effects are requested
through the host bridge described in §5.

This document covers API level **31**. Level 31 is source-compatible with level 29 and drops the
level-27 `chart.rawCells()` accessor.

## 2. Manifest

```toml
[plugin]
id            = "org.tinsel.cablewright"
name          = "Cablewright"
version       = "1.4.2"
api_level     = 31
entry         = "main.js"

[capabilities]
stitch_dictionary = true
transforms        = ["mirror", "reflow"]
exporters         = ["pdf", "svg"]
validators        = ["gauge", "cable_span"]

[limits]
max_cells_per_pass = 250000
max_wall_ms        = 4000
```

`id` must be a reverse-DNS string of 6 to 96 characters. Duplicate `id` values cause the later
plugin to be skipped with diagnostic `PW-0102`.

If `api_level` is below 29 the plugin is refused outright (`PW-0104`). If it is above the host's
level the plugin loads in **degraded mode**: only `stitch_dictionary` capabilities are honored.

## 3. Data model

### 3.1 Chart

A chart is a rectangular grid of cells addressed `(row, col)` with row 1 at the **bottom** and
column 1 at the **right**, matching the direction of work. Charts carry:

| field | type | notes |
|---|---|---|
| `id` | uuid v4 | |
| `rows` | int, 1–4096 | |
| `cols` | int, 1–1024 | |
| `gauge` | `{stitches_per_10cm, rows_per_10cm}` | decimals, 2 dp |
| `flat` | bool | false means worked in the round |
| `repeat` | `{row_from, row_to, col_from, col_to}` or null | |
| `revision` | int | increments on every committed mutation |

### 3.2 Cell

```ts
interface Cell {
  readonly row: number;
  readonly col: number;
  symbol: SymbolRef;      // e.g. "k", "p", "c4f", "yo", "ssk"
  colorIndex: number;     // 0-based into chart palette, max 24 entries
  noSpan?: boolean;       // set on the trailing cells of a multi-cell symbol
}
```

A symbol whose `width` exceeds 1 occupies its anchor cell plus `width − 1` trailing cells with
`noSpan: true`. Writing a symbol over a trailing cell without first clearing its anchor raises
`PW-2210`.

### 3.3 SymbolRef and dictionaries

```ts
interface StitchSymbol {
  ref: string;            // 1–12 chars, [a-z0-9_]
  label: string;          // shown in the legend
  width: number;          // 1–8
  consumes: number;       // stitches consumed from the row below
  produces: number;       // stitches produced
  glyph: string;          // inline SVG path data, ≤ 2048 chars
}
```

The editor enforces the row-balance rule: for every row *r*, the sum of `consumes` over row *r*
must equal the sum of `produces` over row *r − 1*, with row 0 taken as the cast-on count. A
violation is a **soft** error and is surfaced as `PW-3302` on the affected row rather than
blocking the edit.

## 4. Plugin interfaces

### 4.1 Lifecycle

```ts
export function activate(ctx: HostContext): void | Promise<void>;
export function deactivate(): void;
```

`activate` is called once, on the worker's first idle tick after load. It must return within 500
ms or the plugin is unloaded with `PW-0111`. Long work belongs in a transform, not in activation.

### 4.2 Transform

```ts
export interface Transform {
  readonly name: string;
  readonly reversible: boolean;
  apply(chart: ChartView, sel: Selection, opts: Record<string, unknown>): Patch;
  invert?(patch: Patch): Patch;
}
```

`apply` receives a **read-only** view. It must not mutate; it returns a `Patch`, which is an
array of cell writes plus optional metadata writes. Patches are applied atomically and bump
`revision` by exactly 1 regardless of how many cells changed.

`reversible: true` requires `invert`. If `invert` is absent, registration fails with `PW-0121`.

### 4.3 Validator

```ts
export interface Validator {
  readonly name: string;
  readonly severity: "info" | "warn" | "error";
  check(chart: ChartView): Diagnostic[];
}

interface Diagnostic {
  code: string;           // must begin with the plugin's id hash, 6 hex chars
  row: number;
  col?: number;
  message: string;        // ≤ 140 chars
  quickFix?: Patch;
}
```

Validators run on a debounce of 350 ms after the last keystroke, and are hard-capped at
`max_wall_ms`. A validator that exceeds its cap twice in one session is disabled until restart.

### 4.4 Exporter

```ts
export interface Exporter {
  readonly format: "pdf" | "svg" | "png" | "csv";
  render(chart: ChartView, opts: ExportOptions): Uint8Array;
}
```

`ExportOptions` carries `dpi` (72–1200, default 300), `include_legend` (default true),
`page_mm` (`[width, height]`, default `[210, 297]`), and `repeat_shading` (default `0.12`).

## 5. Host bridge

The bridge is the only route to the outside.

| call | returns | notes |
|---|---|---|
| `ctx.log(level, msg)` | void | levels `debug`\|`info`\|`warn`\|`error` |
| `ctx.readSetting(key)` | string \| null | namespaced to the plugin |
| `ctx.writeSetting(key, val)` | void | 8 KB total per plugin |
| `ctx.requestFile(filter)` | Promise&lt;Uint8Array&gt; | opens a host file picker; user-gated |
| `ctx.offerFile(name, bytes)` | Promise&lt;boolean&gt; | opens a host save dialog |
| `ctx.registerTransform(t)` | void | must be called during `activate` |
| `ctx.registerValidator(v)` | void | idem |
| `ctx.registerExporter(e)` | void | idem |
| `ctx.palette()` | Color[] | current chart palette, ≤ 24 entries |

There is no timer API. Plugins that need periodic work should attach to the `chart.committed`
event, which fires at most once per 100 ms.

## 6. Error codes

| code | class | meaning |
|---|---|---|
| `PW-0102` | load | duplicate plugin id |
| `PW-0104` | load | `api_level` below 29 |
| `PW-0111` | load | `activate` exceeded 500 ms |
| `PW-0121` | load | `reversible` transform without `invert` |
| `PW-1201` | bridge | setting store over 8 KB |
| `PW-1204` | bridge | registration outside `activate` |
| `PW-2210` | edit | write over a `noSpan` trailing cell |
| `PW-2214` | edit | symbol `width` exceeds remaining columns |
| `PW-2219` | edit | `colorIndex` outside palette |
| `PW-3302` | validate | row balance violated (soft) |
| `PW-3307` | validate | diagnostic `code` prefix does not match plugin hash |
| `PW-4401` | export | `dpi` outside 72–1200 |
| `PW-4405` | export | render exceeded `max_wall_ms` |

## 7. Example: a two-stitch mirror transform

```js
export function activate(ctx) {
  ctx.registerTransform({
    name: "mirror-cables",
    reversible: true,
    apply(chart, sel) {
      const writes = [];
      for (let r = sel.rowFrom; r <= sel.rowTo; r++) {
        for (let c = sel.colFrom; c <= sel.colTo; c++) {
          const cell = chart.at(r, c);
          if (cell.symbol === "c4f") writes.push({ row: r, col: c, symbol: "c4b" });
          else if (cell.symbol === "c4b") writes.push({ row: r, col: c, symbol: "c4f" });
        }
      }
      ctx.log("info", `mirrored ${writes.length} cells`);
      return { writes };
    },
    invert(patch) { return patch; }
  });
}
export function deactivate() {}
```

Because `c4f` and `c4b` both have `width` 4 and identical `consumes`/`produces`, the transform is
its own inverse and row balance is preserved. A transform that swaps symbols of differing width
must clear anchors first or it will produce `PW-2210` on the second write.

## 8. Deprecations

`chart.rawCells()` (level 27) is removed. Use `chart.at(row, col)` or `chart.slice(sel)`.
`Exporter.render` returning a string is deprecated at level 31 and will be refused at level 33;
return `Uint8Array`.
