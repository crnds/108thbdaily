#!/usr/bin/env python3
"""
fetch_data.py — Download BTC, S&P 500, and Gold price history → data/prices.js

Sources (all free, no API key required):
  BTC      — Binance klines API  (data from 2017-08-17 onward)
  S&P 500  — yfinance  ^GSPC     (data from 2014 onward)
  Gold     — yfinance  GLD       (SPDR Gold Shares ETF; clean spot proxy, no futures-roll artifacts)

Requirements:
  pip install yfinance            (one-time install)

Usage:
  python3 fetch_data.py           # Skip if today's data already saved
  python3 fetch_data.py --force   # Re-download everything

Run once to initialise, then re-run whenever you want fresh data.
The browser page loads data/prices.js instantly and only calls Kraken
for a quick top-up of the most recent BTC candles.
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import yfinance as yf
    import warnings
    warnings.filterwarnings('ignore')
except ImportError:
    print('ERROR: yfinance is not installed.')
    print('Run:  pip install yfinance')
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
START_DATE   = '2014-01-01'
BINANCE_FROM = datetime(2017, 8, 17, tzinfo=timezone.utc)   # Binance launch date
OUTPUT_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE     = os.path.join(OUTPUT_DIR, 'prices.js')
COMPARE_FILE    = os.path.join(OUTPUT_DIR, 'prices-compare.js')


def log(msg='', end='\n'):
    print(msg, end=end, flush=True)


# ── BTC — Binance klines (with yfinance fallback for geo-blocked regions) ────
def fetch_btc_binance():
    """
    Fetch BTC/USDT daily closing prices from Binance klines (free, no key).
    Returns {YYYY-MM-DD: close_price}.  Data available from 2017-08-17.
    Raises urllib.error.HTTPError on geo-block (HTTP 451) or other errors.
    """
    log('Fetching BTC from Binance...')

    def get_url(url):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    prices   = {}
    start_ms = int(BINANCE_FROM.timestamp() * 1000)
    now_ms   = int(time.time() * 1000)
    page     = 1

    while start_ms < now_ms:
        url = (
            'https://api.binance.com/api/v3/klines'
            f'?symbol=BTCUSDT&interval=1d&startTime={start_ms}&limit=1000'
        )
        log(f'  page {page}... ', end='')
        klines = get_url(url)
        if not klines:
            break

        for k in klines:
            dt = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
            prices[dt] = round(float(k[4]), 2)   # k[4] = close price

        log(f'{len(klines)} candles  ({len(prices)} total)')

        if len(klines) < 1000:
            break                       # Last (partial) batch — we're done
        start_ms = klines[-1][6] + 1    # close_time of last candle + 1 ms
        page += 1
        time.sleep(0.08)

    log(f'  => {len(prices)} days  (from {min(prices)})\n')
    return prices


def fetch_btc():
    """
    Try Binance first; fall back to yfinance BTC-USD if Binance is unreachable
    (e.g., HTTP 451 geo-block on GitHub Actions US runners).
    """
    try:
        return fetch_btc_binance()
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        log(f'  Binance unavailable ({e}); falling back to yfinance BTC-USD.\n')
        return fetch_yf('BTC-USD', 'BTC')


# ── S&P 500 + Gold — yfinance ─────────────────────────────────────────────────
def fetch_yf(symbol, label):
    """
    Fetch daily closing prices via yfinance (Yahoo Finance wrapper).
    Returns {YYYY-MM-DD: close_price}.
    """
    log(f'Fetching {label} ({symbol}) via yfinance... ', end='')
    today  = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    df     = yf.download(symbol, start=START_DATE, end=today, progress=False, auto_adjust=True)

    if df.empty:
        raise RuntimeError(f'yfinance returned no data for {symbol}')

    # Flatten multi-level columns if present (handles both real MultiIndex and
    # the stringified-tuple columns that some yfinance + auto_adjust downloads produce).
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    else:
        # Repair columns like "('Close', 'GLD')" -> "Close"
        new_cols = []
        for c in df.columns:
            cs = str(c)
            if cs.startswith("('") and cs.endswith("')"):
                # extract first element of the apparent tuple repr
                inner = cs[2:-2]
                first = inner.split("', '")[0].strip("'")
                new_cols.append(first)
            else:
                new_cols.append(cs)
        df.columns = new_cols

    # Find a usable close column (some downloads use 'Close', others 'Adj Close' etc.)
    close_col = None
    for c in df.columns:
        cl = str(c).lower()
        if cl in ('close', 'adj close', 'adjclose'):
            close_col = c
            break
    if close_col is None:
        # Fallback to first numeric column
        for c in df.columns:
            if df[c].dtype.kind in 'fi':  # float or int
                close_col = c
                break
    if close_col is None:
        raise RuntimeError(f'Could not locate close price column for {symbol}')

    prices = {}
    for dt, val in df[close_col].items():
        if val == val:  # skip NaN
            prices[dt.strftime('%Y-%m-%d')] = round(float(val), 2)

    # Light outlier repair for traditional assets (S&P, Gold) in the *recent* window only.
    # We target bad ticks from the data provider that have appeared in the last ~4 months.
    # Legitimate historical crashes (e.g. 2020 COVID -10% days) are left untouched so that
    # long-term DCA simulations remain accurate. Recent >7% single-trading-day moves are
    # treated as glitches and replaced by linear interpolation between the nearest good
    # neighboring closes (or prev close if no future neighbor yet).
    if label != 'BTC':
        from datetime import datetime as dtmod, timedelta as tdelta
        # Gold is more prone to bad recent prints from yfinance (futures/ETF roll issues)
        # so we watch a longer window and use a slightly tighter threshold for it.
        CLEAN_WINDOW_DAYS = 200 if label == 'Gold' else 120
        THRESHOLD = 0.05 if label == 'Gold' else 0.07  # 5% gold, 7% equities

        sorted_ds = sorted(prices)
        if sorted_ds:
            today_d = dtmod.strptime(sorted_ds[-1], '%Y-%m-%d').date()
            cutoff = today_d - tdelta(days=CLEAN_WINDOW_DAYS)

            # First pass: identify recent candidates vs their immediate prior good close
            prev_p = None
            prev_ds = None
            candidates = []  # list of (ds, original_p, prev_good_p)
            for ds in sorted_ds:
                p = prices[ds]
                d = dtmod.strptime(ds, '%Y-%m-%d').date()
                is_recent = d >= cutoff
                if prev_p is not None and p is not None and prev_p > 0 and is_recent:
                    chg = abs((p - prev_p) / prev_p)
                    if chg > THRESHOLD:
                        candidates.append((ds, p, prev_p))
                if p is not None:
                    prev_p = p
                    prev_ds = ds

            # Second pass: for each bad recent day, try to interpolate with next good close
            cleaned = 0
            for ds, bad_p, prev_good in candidates:
                # find next good close after this ds
                next_good = None
                for later in sorted_ds:
                    if later > ds and prices[later] is not None:
                        next_good = prices[later]
                        break
                if next_good is not None and prev_good > 0:
                    interp = (prev_good + next_good) / 2.0
                else:
                    interp = prev_good
                prices[ds] = round(interp, 2)
                cleaned += 1

            if cleaned:
                log(f'  (repaired {cleaned} suspicious recent >{int(THRESHOLD*100)}% moves)')

    log(f'{len(prices)} days  (from {min(prices)})')
    return prices


# ── Compact serialization ─────────────────────────────────────────────────────
def to_compact(prices):
    """
    Convert {YYYY-MM-DD: price} to {'start': 'YYYY-MM-DD', 'close': [price | None, ...]}.
    The array is contiguous by day starting at the earliest date; missing days
    (weekends/holidays) are stored as None. This avoids repeating date-string
    keys and roughly halves the JSON payload.
    """
    if not prices:
        return {'start': None, 'close': []}
    sorted_dates = sorted(prices)
    start = datetime.strptime(sorted_dates[0], '%Y-%m-%d').date()
    end   = datetime.strptime(sorted_dates[-1], '%Y-%m-%d').date()
    span  = (end - start).days + 1
    close = [None] * span
    for ds, p in prices.items():
        i = (datetime.strptime(ds, '%Y-%m-%d').date() - start).days
        close[i] = p
    return {'start': start.isoformat(), 'close': close}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    force = '--force' in sys.argv
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Skip if already up to date today
    if not force and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            head = f.read(120)
        if f'"updated":"{today}"' in head:
            log(f'Already up to date ({today}). Use --force to re-download.')
            return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    log('=' * 52)
    log('  DCA Bitcoin — Data Fetcher')
    log(f'  Date  : {today}')
    log(f'  BTC   : 2017-08-17 → today  (Binance)')
    log(f'  S&P   : 2014-01-01 → today  (Yahoo Finance)')
    log(f'  Gold  : 2014-01-01 → today  (Yahoo Finance via GLD ETF)')
    log('=' * 52)
    log()

    btc   = fetch_btc()
    sp500 = fetch_yf('^GSPC', 'S&P 500')
    gold  = fetch_yf('GLD',   'Gold')

    # Main file — BTC only (loaded on every page view)
    main_payload = {
        'updated': today,
        'btc':     to_compact(btc),
    }
    main_js = 'window.LOCAL_PRICES=' + json.dumps(main_payload, separators=(',', ':')) + ';'
    with open(OUTPUT_FILE, 'w') as f:
        f.write(main_js)

    # Compare file — loaded lazily when the user toggles S&P/Gold comparison
    compare_payload = {
        'updated': today,
        'sp500':   to_compact(sp500),
        'gold':    to_compact(gold),
    }
    compare_js = 'window.LOCAL_PRICES_COMPARE=' + json.dumps(compare_payload, separators=(',', ':')) + ';'
    with open(COMPARE_FILE, 'w') as f:
        f.write(compare_js)

    main_kb    = os.path.getsize(OUTPUT_FILE)  / 1024
    compare_kb = os.path.getsize(COMPARE_FILE) / 1024

    log()
    log('=' * 52)
    log(f'  {OUTPUT_FILE}')
    log(f'    Size  : {main_kb:.0f} KB')
    log(f'    BTC   : {len(btc):,} days')
    log(f'  {COMPARE_FILE}')
    log(f'    Size  : {compare_kb:.0f} KB')
    log(f'    S&P   : {len(sp500):,} days')
    log(f'    Gold  : {len(gold):,} days')
    log('=' * 52)
    log()
    log('Done. Open index.html in your browser.')


if __name__ == '__main__':
    main()
