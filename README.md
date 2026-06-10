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

A DCA calculator for the **108-1009 movement** — buying 108 THB of Bitcoin every day. Enter an amount, frequency, and start date to see total invested, portfolio value, P&L, BTC accumulated, and average buy price. Compare against S&P 500 or Gold side-by-side.

**Live → [crnds.github.io/108thbdaily](https://crnds.github.io/108thbdaily/)**

---

Daily · Weekly · Monthly · 1–10 year lookback · THB/USD toggle · % Return chart · Dark/Light · EN/ไทย

---

## Data

| Asset | Source | From |
|---|---|---|
| BTC | Binance klines | 2017-08-17 |
| S&P 500 | Yahoo Finance | 2014-01-01 |
| Gold | Yahoo Finance (GLD ETF) | 2014-01-01 |

Pre-fetched daily via GitHub Actions → `data/prices.js`. Kraken tops up any days since the last update.

## Running locally

```bash
open index.html                 # no build step needed
python3 -m http.server 8080    # needed for S&P/Gold compare (CORS)
```

```bash
pip install yfinance
python3 fetch_data.py           # skip if up to date
python3 fetch_data.py --force   # re-download everything
```
