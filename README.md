```
 ██╗ ██████╗  █████╗ ████████╗██╗  ██╗██████╗ ██████╗  █████╗ ██╗██╗     ██╗   ██╗
███║██╔═══██╗██╔══██╗╚══██╔══╝██║  ██║██╔══██╗██╔══██╗██╔══██╗██║██║     ╚██╗ ██╔╝
╚██║██║   ██║╚█████╔╝   ██║   ███████║██████╔╝██║  ██║███████║██║██║      ╚████╔╝ 
 ██║██║   ██║██╔══██╗   ██║   ██╔══██║██╔══██╗██║  ██║██╔══██║██║██║       ╚██╔╝  
 ██║╚██████╔╝╚█████╔╝   ██║   ██║  ██║██████╔╝██████╔╝██║  ██║██║███████╗   ██║   
 ╚═╝ ╚═════╝  ╚════╝    ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝   ╚═╝  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                BTC DCA Calculator                                
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

A DCA calculator for the **108-1009 movement** — buying 108 THB of Bitcoin every day. Enter an amount, frequency, and start date to see total invested, portfolio value, P&L, BTC accumulated, and average buy price. S&P 500 and Gold comparison lines are shown by default.

**Live → [crnds.github.io/108thbdaily](https://crnds.github.io/108thbdaily/)**

---

Daily · Weekly · Monthly · 1–10 year lookback · THB/USD toggle · % Return chart · Dark/Light · EN/ไทย

---

## Data

| Asset   | Source                        | From       |
|---------|-------------------------------|------------|
| BTC     | Binance klines                | 2017-08-17 |
| S&P 500 | Yahoo Finance (^GSPC)         | 2014-01-01 |
| Gold    | Yahoo Finance (GLD ETF)       | 2014-01-01 |

- BTC is pre-fetched daily into `data/prices.js` (with live top-up from Kraken for the most recent days).
- S&P 500 + Gold live in `data/prices-compare.js` (loaded when the compare view is active).
- Both files are kept up to date by a GitHub Action that runs `fetch_data.py --force` every day.
- Gold uses the GLD ETF series (cleaner than raw futures) plus automatic repair for occasional bad recent prints from the data provider.

## On GitHub Pages (recommended)

The site is designed to work great directly on GitHub Pages using the daily pre-fetched data (no local server needed). S&P 500 and Gold comparisons are enabled by default. A small "pre-fetched • as of ..." note appears when using compare data.

The GitHub Action automatically updates both price files every day.

## Running locally (optional, for freshest compare data)

```bash
open index.html                 # no build step needed
# python3 -m http.server 8080  # only needed if you want to test live Yahoo fallbacks
```

```bash
pip install yfinance
python3 fetch_data.py           # skip if up to date
python3 fetch_data.py --force   # re-download everything (recommended after pulling the repo)
```
