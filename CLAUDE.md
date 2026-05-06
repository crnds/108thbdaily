# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static Bitcoin DCA (Dollar-Cost Averaging) calculator for the Thai **108-1009 movement** (108 THB/day). No build step — open `index.html` directly in a browser. Hosted on GitHub Pages.

## Development

```bash
open index.html                 # open directly (no server needed)
python3 -m http.server 8080    # required for compare mode (S&P/Gold) due to CORS
```

## Refreshing price data

```bash
pip install yfinance
python3 fetch_data.py           # skip if already up to date today
python3 fetch_data.py --force   # re-download everything
```

The GitHub Actions workflow (`.github/workflows/update-prices.yml`) runs this daily at 01:00 UTC and commits the result automatically.

## Architecture

**Data pipeline:** `fetch_data.py` pulls BTC from Binance klines, S&P 500 and Gold from yfinance, then writes two JS files that set globals:
- `data/prices.js` → `window.LOCAL_PRICES` (BTC only, loaded on every page view)
- `data/prices-compare.js` → `window.LOCAL_PRICES_COMPARE` (S&P + Gold, loaded lazily when compare mode is toggled)

Both use a compact `{start, close[]}` array format (contiguous by day, `null` for missing days) instead of a date-keyed object — this roughly halves payload size.

**Price loading in `index.html`:** On startup, the app reads `window.LOCAL_PRICES` for the pre-fetched BTC history, then calls Kraken's API to top up any days since the last file update. If `window.LOCAL_PRICES` is missing (file not yet generated), it falls back to live API fetching entirely.

**DCA calculation:** All logic lives inside the `<script>` block in `index.html`. The `state` object holds all runtime state (prices, chart instance, currency, chart mode). `recalc()` is the main entry point — it reads the sidebar inputs, walks the price series day by day, computes portfolio snapshots, updates the stat cards, and re-renders the Chart.js chart.

**Compare mode:** When the user selects S&P 500 or Gold, `data/prices-compare.js` is injected as a `<script>` tag on demand (one-time load). The chart then overlays the alternative asset's DCA curve alongside BTC.

**i18n:** All UI strings are in the `T` object (English + Thai). The `applyLang()` function sets `data-i18n` attributes to swap text; currency labels update separately via `updateCurrencyDisplay()`.

**Vendor libs:** Chart.js and the date-fns adapter are vendored locally in `vendor/` — no CDN dependency.

**`pages/dashboard.html`:** A secondary page (linked from the footer) — currently a UI prototype with no live data.
