from __future__ import annotations

import math
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

from indicators import INDICATORS, PILLAR_NAMES, PILLAR_WEIGHTS
from profile import render_profile_tab

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTO_FETCH_IDS = {
    "P2-02", "P2-03", "P2-04", "P2-05", "P2-06", "P2-07",
    "P3-01", "P3-02", "P3-04", "P3-06",
    "P5-01", "P5-02", "P5-03", "P5-04", "P5-05", "P5-06",
    "P5-07", "P5-08", "P5-09", "P5-12", "P5-13", "P5-14",
    "P5-15", "P5-17", "P5-18", "P5-19",
    "P6-03", "P6-04", "P6-05", "P6-06", "P6-07", "P6-08",
    "P6-10", "P6-11", "P6-12",
    "P5-20",  # Economic Moat Score (composite)
    "P5-21", "P5-22", "P5-23", "P5-24", "P5-25",  # Professional Tier 1
    "P6-14", "P6-15",  # Professional Tier 2
}

MANUAL_DEFAULTS = {
    # P1
    "P1-01": 8.0, "P1-02": 15.0, "P1-03": 0.7, "P1-04": 20.0,
    "P1-05": 1.0, "P1-06": 0.4,  "P1-07": 4.0, "P1-08": 7.0,
    # P2
    "P2-01": 2.5, "P2-08": 50.0,
    # P3
    "P3-03": 0.0, "P3-05": -2.0, "P3-07": 100.0, "P3-08": 20.0,
    "P3-09": 2.0, "P3-10": 0.0,  "P3-11": 60.0,  "P3-12": 3.0,
    "P3-13": 80.0, "P3-14": 60.0,
    # P4
    "P4-01": 5.0, "P4-02": 7.0,  "P4-03": 0.0,  "P4-04": 10.0,
    "P4-05": 10.0, "P4-06": 70.0, "P4-07": 1200.0, "P4-08": 3.0,
    "P4-09": 0.0, "P4-10": 12.0, "P4-11": 1.5, "P4-12": 3.0,
    # P5
    "P5-10": 3.0, "P5-11": 0.0, "P5-16": 25.0,
    # P6
    "P6-01": 0.0, "P6-02": 0.0, "P6-09": 0.85, "P6-13": 0.0,
}

MANUAL_CONFIG = {
    # id: (label, min, max, step, format)
    "P1-01": ("Expected Return (%)", -5.0, 30.0, 0.5, "%.1f"),
    "P1-02": ("Portfolio Volatility (%)", 0.0, 50.0, 0.5, "%.1f"),
    "P1-03": ("Sharpe Ratio", -1.0, 3.0, 0.05, "%.2f"),
    "P1-04": ("Max Drawdown (%)", 0.0, 60.0, 0.5, "%.1f"),
    "P1-05": ("Beta to Market", 0.0, 2.5, 0.05, "%.2f"),
    "P1-06": ("Avg Pairwise Correlation", -0.5, 1.0, 0.05, "%.2f"),
    "P1-07": ("# Asset Classes", 1.0, 12.0, 1.0, "%.0f"),
    "P1-08": ("Portfolio Drift (%)", 0.0, 25.0, 0.5, "%.1f"),
    "P2-01": ("Equity Risk Premium (%)", -2.0, 8.0, 0.1, "%.1f"),
    "P2-08": ("Risk-On/Off Score (0-100)", 0.0, 100.0, 1.0, "%.0f"),
    "P3-03": ("Policy Rate Trend (% chg)", -3.0, 3.0, 0.1, "%.1f"),
    "P3-05": ("Current Account / GDP (%)", -10.0, 10.0, 0.5, "%.1f"),
    "P3-07": ("Market Cap / GDP (%)", 10.0, 250.0, 5.0, "%.0f"),
    "P3-08": ("Country CAPE Ratio", 5.0, 60.0, 1.0, "%.0f"),
    "P3-09": ("Country PBV", 0.3, 5.0, 0.1, "%.1f"),
    "P3-10": ("FX 1Y Trend (%)", -30.0, 30.0, 1.0, "%.0f"),
    "P3-11": ("WGI Governance Score (0-100)", 0.0, 100.0, 1.0, "%.0f"),
    "P3-12": ("Country Index 12M RS (%)", -40.0, 80.0, 1.0, "%.0f"),
    "P3-13": ("Country CDS 5Y (bps)", 0.0, 1000.0, 5.0, "%.0f"),
    "P3-14": ("Market Turnover Ratio (%)", 0.0, 250.0, 5.0, "%.0f"),
    "P4-01": ("Industry Revenue Growth (%)", -10.0, 40.0, 0.5, "%.1f"),
    "P4-02": ("TAM CAGR 5Y (%)", 0.0, 40.0, 0.5, "%.1f"),
    "P4-03": ("EPS Revision Net (%)", -30.0, 30.0, 1.0, "%.0f"),
    "P4-04": ("Industry EBIT Margin (%)", -10.0, 50.0, 0.5, "%.1f"),
    "P4-05": ("Industry ROIC (%)", -5.0, 50.0, 0.5, "%.1f"),
    "P4-06": ("FCF Conversion (%)", 0.0, 150.0, 5.0, "%.0f"),
    "P4-07": ("HHI Concentration", 0.0, 10000.0, 50.0, "%.0f"),
    "P4-08": ("Disruption Risk Score (1-5)", 1.0, 5.0, 1.0, "%.0f"),
    "P4-09": ("Industry PE vs 5Y Avg (%)", -40.0, 60.0, 1.0, "%.0f"),
    "P4-10": ("Industry EV/EBITDA", 2.0, 40.0, 0.5, "%.1f"),
    "P4-11": ("Industry PEG", 0.0, 5.0, 0.1, "%.1f"),
    "P4-12": ("Industry 12M RS (%)", -40.0, 80.0, 1.0, "%.0f"),
    "P5-10": ("Governance Score (1-5)", 1.0, 5.0, 1.0, "%.0f"),
    "P5-11": ("PE vs 5Y Avg (%)", -40.0, 60.0, 1.0, "%.0f"),
    "P5-16": ("Customer Concentration (%)", 0.0, 100.0, 1.0, "%.0f"),
    "P6-01": ("Discount to Fair Value (%)", -50.0, 50.0, 1.0, "%.0f"),
    "P6-02": ("Asset PE vs 5Y Avg (%)", -40.0, 60.0, 1.0, "%.0f"),
    "P6-09": ("Put/Call Ratio", 0.3, 2.5, 0.05, "%.2f"),
    "P6-13": ("Position Drift vs Target (%)", -30.0, 30.0, 1.0, "%.0f"),
}

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def _fred_df(series_id: str):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        df = pd.read_csv(url, parse_dates=["DATE"])
        df.columns = ["date", "value"]
        df = df[df["value"] != "."].copy()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().reset_index(drop=True)
    except Exception:
        return None


def _fred_latest(series_id: str):
    df = _fred_df(series_id)
    return float(df["value"].iloc[-1]) if df is not None and len(df) else None


def _fred_yoy(series_id: str):
    df = _fred_df(series_id)
    if df is None or len(df) < 13:
        return None
    return float((df["value"].iloc[-1] - df["value"].iloc[-13]) / abs(df["value"].iloc[-13]) * 100)


@st.cache_data(ttl=86400, show_spinner=False)
def _worldbank(indicator: str, country: str = "US"):
    url = (
        f"https://api.worldbank.org/v2/country/{country}/indicator/"
        f"{indicator}?format=json&mrv=5"
    )
    try:
        data = requests.get(url, timeout=10).json()[1]
        for d in data:
            if d["value"] is not None:
                return float(d["value"])
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_stock(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info
    hist = t.history(period="2y")
    try:
        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow
    except Exception:
        fin = bs = cf = None
    return info, hist, fin, bs, cf


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_market():
    results = {}
    try:
        vix = yf.Ticker("^VIX").history(period="5d")
        results["vix"] = float(vix["Close"].iloc[-1]) if len(vix) else None
    except Exception:
        results["vix"] = None
    for sym, key in [("GLD", "gld"), ("SPY", "spy")]:
        try:
            h = yf.download(sym, period="14mo", progress=False, auto_adjust=True)
            results[key] = h["Close"]
        except Exception:
            results[key] = None
    return results


def _rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1]) if not rsi.empty else None


def _safe(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            return v
    return None


def _pct(v):
    return v * 100 if v is not None else None


def compute_auto_values(ticker: str) -> dict[str, float | None]:
    vals: dict[str, float | None] = {}
    fetch_errors: list[str] = []

    # ---- Stock data ----
    try:
        info, hist, fin, bs, cf = _fetch_stock(ticker)
    except Exception as e:
        fetch_errors.append(f"yfinance stock: {e}")
        info, hist, fin, bs, cf = {}, pd.DataFrame(), None, None, None

    close = hist["Close"] if hist is not None and "Close" in hist.columns and len(hist) > 0 else None

    if close is not None and len(close) >= 20:
        cur = float(close.iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        ma50  = float(close.rolling(50).mean().iloc[-1])  if len(close) >= 50  else None
        high52 = float(close.rolling(min(252, len(close))).max().iloc[-1])
        drawdown = (cur - high52) / high52 * 100

        ret12m = None
        if len(close) >= 252:
            ret12m = (cur - float(close.iloc[-252])) / float(close.iloc[-252]) * 100

        vals["P5-17"] = ret12m
        vals["P5-18"] = drawdown
        vals["P5-19"] = cur / ma200 if ma200 else None
        vals["P6-03"] = cur / ma200 if ma200 else None
        vals["P6-04"] = ma50 / ma200 if (ma50 and ma200) else None
        vals["P6-05"] = ret12m
        vals["P6-06"] = drawdown
        vals["P6-07"] = _rsi(close)

    # Margins / ratios from info
    vals["P5-02"] = _pct(_safe(info, "operatingMargins"))
    vals["P5-04"] = _pct(_safe(info, "grossMargins"))
    vals["P5-08"] = _safe(info, "currentRatio")
    vals["P5-09"] = _pct(_safe(info, "heldPercentInsiders"))
    vals["P5-12"] = _safe(info, "priceToBook")
    vals["P5-13"] = _safe(info, "trailingPegRatio", "pegRatio")
    vals["P5-15"] = _pct(_safe(info, "dividendYield"))

    # Revenue growth
    if fin is not None and not fin.empty and fin.shape[1] >= 2:
        try:
            for lbl in ("Total Revenue", "Revenue"):
                if lbl in fin.index:
                    r = fin.loc[lbl]
                    r0, r1 = float(r.iloc[0]), float(r.iloc[1])
                    if r1 != 0:
                        vals["P5-01"] = (r0 - r1) / abs(r1) * 100
                    break
        except Exception:
            pass

    # EBIT, Interest, EBITDA, ROIC, Net Debt/EBITDA, Interest Coverage
    if fin is not None and bs is not None and not fin.empty and not bs.empty:
        try:
            ebit = next((float(fin.loc[l].iloc[0]) for l in ("EBIT", "Operating Income") if l in fin.index), None)
            da   = next((float(fin.loc[l].iloc[0]) for l in ("Depreciation And Amortization", "Reconciled Depreciation") if l in fin.index), None)
            ni   = next((float(fin.loc[l].iloc[0]) for l in ("Net Income", "Net Income Common Stockholders") if l in fin.index), None)
            interest = next((abs(float(fin.loc[l].iloc[0])) for l in ("Interest Expense", "Interest Expense Non Operating") if l in fin.index), None)
            debt = next((float(bs.loc[l].iloc[0]) for l in ("Total Debt", "Long Term Debt") if l in bs.index), None)
            cash = next((float(bs.loc[l].iloc[0]) for l in ("Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments") if l in bs.index), None)
            equity = next((float(bs.loc[l].iloc[0]) for l in ("Stockholders Equity", "Common Stock Equity") if l in bs.index), None)

            if ebit and interest and interest > 0:
                vals["P5-06"] = ebit / interest
            ebitda = (ebit or 0) + (da or 0) if ebit else None
            if debt is not None and ebitda and ebitda > 0:
                vals["P5-05"] = (debt - (cash or 0)) / ebitda
            if ebit and debt is not None and equity is not None:
                ic = debt + equity - (cash or 0)
                if ic > 0:
                    vals["P5-03"] = ebit * 0.79 / ic * 100  # assumes 21% tax
        except Exception:
            pass

    # FCF, FCF Yield, FCF Conversion
    if cf is not None and fin is not None and not cf.empty and not fin.empty:
        try:
            ocf  = next((float(cf.loc[l].iloc[0]) for l in ("Operating Cash Flow", "Cash Flow From Continuing Operating Activities") if l in cf.index), None)
            capex = next((float(cf.loc[l].iloc[0]) for l in ("Capital Expenditure", "Capital Expenditures") if l in cf.index), None)
            if ocf is not None and capex is not None:
                fcf = ocf + capex  # capex stored as negative
                mktcap = info.get("marketCap")
                if mktcap and mktcap > 0:
                    vals["P5-14"] = fcf / mktcap * 100
                ni = next((float(fin.loc[l].iloc[0]) for l in ("Net Income", "Net Income Common Stockholders") if l in fin.index), None)
                if ni and ni > 0:
                    vals["P5-07"] = fcf / ni * 100
        except Exception:
            pass

    # ---- Economic Moat Score (P5-20) ----
    # Composite of 3 sub-scores: ROIC, Gross Margin, Revenue Consistency
    try:
        sub_scores = []

        roic = vals.get("P5-03")
        if roic is not None:
            sub_scores.append(1 if roic >= 15 else (0 if roic >= 8 else -1))

        gm = vals.get("P5-04")
        if gm is not None:
            sub_scores.append(1 if gm >= 40 else (0 if gm >= 20 else -1))

        if fin is not None and not fin.empty and fin.shape[1] >= 4:
            for lbl in ("Total Revenue", "Revenue"):
                if lbl in fin.index:
                    rev = fin.loc[lbl].dropna()
                    if len(rev) >= 4:
                        growths = [
                            (float(rev.iloc[i]) - float(rev.iloc[i + 1])) / abs(float(rev.iloc[i + 1])) * 100
                            for i in range(min(3, len(rev) - 1))
                            if float(rev.iloc[i + 1]) != 0
                        ]
                        if growths:
                            stdev = float(pd.Series(growths).std())
                            sub_scores.append(1 if stdev < 10 else (0 if stdev < 20 else -1))
                    break

        if sub_scores:
            vals["P5-20"] = round(sum(sub_scores) / len(sub_scores), 4)
    except Exception:
        pass

    # ---- Professional indicators ----
    # Helper: pull a value from a DataFrame by trying multiple row labels
    def _row(df, labels, col=0):
        if df is None or df.empty: return None
        for lbl in (labels if isinstance(labels, list) else [labels]):
            if lbl in df.index:
                try:
                    v = df.loc[lbl].iloc[col]
                    return float(v) if pd.notna(v) else None
                except Exception:
                    pass
        return None

    # --- P5-21: Piotroski F-Score (0–9) ---
    try:
        f, n = 0, 0
        NI   = ["Net Income", "Net Income Common Stockholders"]
        REV  = ["Total Revenue", "Revenue"]
        GP   = ["Gross Profit"]
        OCF  = ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]
        TA   = ["Total Assets"]
        CA   = ["Current Assets"]
        CL   = ["Current Liabilities", "Total Current Liabilities"]
        LTD  = ["Long Term Debt"]
        SH   = ["Ordinary Shares Number", "Share Issued"]
        RE   = ["Retained Earnings"]

        ta0 = _row(bs, TA, 0);  ta1 = _row(bs, TA, 1)
        ni0 = _row(fin, NI, 0); ni1 = _row(fin, NI, 1)
        ocf0 = _row(cf, OCF, 0)
        rev0 = _row(fin, REV, 0); rev1 = _row(fin, REV, 1)
        gp0  = _row(fin, GP, 0);  gp1  = _row(fin, GP, 1)
        ca0  = _row(bs, CA, 0);   ca1  = _row(bs, CA, 1)
        cl0  = _row(bs, CL, 0);   cl1  = _row(bs, CL, 1)
        ltd0 = _row(bs, LTD, 0);  ltd1 = _row(bs, LTD, 1)
        sh0  = _row(bs, SH, 0);   sh1  = _row(bs, SH, 1)

        def _inc(cond):
            nonlocal f, n
            if cond is not None: f += int(bool(cond)); n += 1

        # Profitability
        _inc(ta0 and ni0 is not None and ni0 / ta0 > 0)
        _inc(ocf0 is not None and ocf0 > 0)
        if ta0 and ta1 and ni0 is not None and ni1 is not None:
            _inc(ni0 / ta0 > ni1 / ta1)
        if ta0 and ni0 is not None and ocf0 is not None:
            _inc(ocf0 / ta0 > ni0 / ta0)
        # Leverage / Liquidity
        if ta0 and ta1 and ltd0 is not None and ltd1 is not None:
            _inc(ltd0 / ta0 < ltd1 / ta1)
        if ca0 and cl0 and ca1 and cl1 and cl0 != 0 and cl1 != 0:
            _inc(ca0 / cl0 > ca1 / cl1)
        if sh0 and sh1:
            _inc(sh0 <= sh1 * 1.02)
        # Operating efficiency
        if rev0 and rev1 and gp0 and gp1 and rev0 != 0 and rev1 != 0:
            _inc(gp0 / rev0 > gp1 / rev1)
        if rev0 and rev1 and ta0 and ta1 and ta0 != 0 and ta1 != 0:
            _inc(rev0 / ta0 > rev1 / ta1)

        if n >= 6:
            vals["P5-21"] = float(f)
    except Exception:
        pass

    # --- P5-22: Altman Z-Score ---
    try:
        ta   = _row(bs, ["Total Assets"])
        ca   = _row(bs, ["Current Assets"])
        cl   = _row(bs, ["Current Liabilities", "Total Current Liabilities"])
        re   = _row(bs, ["Retained Earnings"])
        tl   = _row(bs, ["Total Liabilities Net Minority Interest", "Total Liabilities"])
        ebit = _row(fin, ["EBIT", "Operating Income"])
        rev  = _row(fin, ["Total Revenue", "Revenue"])
        mc   = info.get("marketCap")

        if all(v is not None for v in [ta, ca, cl, re, tl, ebit, rev, mc]) and ta > 0 and tl > 0:
            x1 = (ca - cl) / ta
            x2 = re / ta
            x3 = ebit / ta
            x4 = mc / tl
            x5 = rev / ta
            vals["P5-22"] = round(1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5, 3)
    except Exception:
        pass

    # --- P5-23: EV / FCF ---
    try:
        mc    = info.get("marketCap")
        debt  = _row(bs, ["Total Debt", "Long Term Debt"])
        cash_ = _row(bs, ["Cash And Cash Equivalents",
                           "Cash Cash Equivalents And Short Term Investments"])
        ocf_  = _row(cf, ["Operating Cash Flow",
                           "Cash Flow From Continuing Operating Activities"])
        capex = _row(cf, ["Capital Expenditure", "Capital Expenditures"])

        if all(v is not None for v in [mc, ocf_, capex]):
            ev  = (mc or 0) + (debt or 0) - (cash_ or 0)
            fcf = ocf_ + capex  # capex is stored negative
            if fcf > 0:
                vals["P5-23"] = round(ev / fcf, 2)
    except Exception:
        pass

    # --- P5-24: Accruals Ratio (%) ---
    try:
        ni_  = _row(fin, ["Net Income", "Net Income Common Stockholders"])
        ocf_ = _row(cf,  ["Operating Cash Flow",
                           "Cash Flow From Continuing Operating Activities"])
        ta_  = _row(bs,  ["Total Assets"])
        if ni_ is not None and ocf_ is not None and ta_ and ta_ > 0:
            vals["P5-24"] = round((ni_ - ocf_) / ta_ * 100, 2)
    except Exception:
        pass

    # --- P5-25: Total Shareholder Yield (%) ---
    try:
        mc_ = info.get("marketCap")
        div_paid  = _row(cf, ["Cash Dividends Paid", "Payment Of Dividends",
                               "Common Stock Dividend Paid"])
        buybacks  = _row(cf, ["Repurchase Of Capital Stock",
                               "Common Stock Repurchased",
                               "Purchase Of Business"])
        if mc_ and mc_ > 0:
            div_amt  = abs(div_paid)  if div_paid  is not None else 0
            buyb_amt = abs(buybacks)  if buybacks  is not None else 0
            vals["P5-25"] = round((div_amt + buyb_amt) / mc_ * 100, 2)
    except Exception:
        pass

    # --- P6-14: Analyst Price Target Upside (%) ---
    try:
        target = info.get("targetMeanPrice") or info.get("targetMedianPrice")
        price_ = (info.get("currentPrice") or info.get("regularMarketPrice"))
        if not price_ and hist is not None and len(hist):
            price_ = float(hist["Close"].iloc[-1])
        if target and price_ and price_ > 0:
            vals["P6-14"] = round((target - price_) / price_ * 100, 2)
    except Exception:
        pass

    # --- P6-15: Short Interest % Float ---
    try:
        si = info.get("shortPercentOfFloat")
        if si is not None:
            vals["P6-15"] = round(si * 100, 2)
    except Exception:
        pass

    # ---- Market data ----
    try:
        mkt = _fetch_market()
        vals["P6-08"] = mkt.get("vix")

        gld_s = mkt.get("gld")
        spy_s = mkt.get("spy")
        if gld_s is not None and spy_s is not None and len(gld_s) and len(spy_s):
            vals["P2-05"] = float(gld_s.iloc[-1]) / float(spy_s.iloc[-1])
            if len(spy_s) >= 252:
                vals["P2-07"] = (float(spy_s.iloc[-1]) - float(spy_s.iloc[-252])) / float(spy_s.iloc[-252]) * 100
    except Exception as e:
        fetch_errors.append(f"market data: {e}")

    # ---- FRED ----
    fred_map = {
        "P2-03": ("BAMLC0A0CM",   "latest"),
        "P2-04": ("BAMLH0A0HYM2", "latest"),
        "P2-06": ("DTWEXBGS",     "latest"),
        "P3-02": ("CPIAUCSL",     "yoy"),
        "P3-04": ("NAPM",         "latest"),
        "P6-10": ("T10Y2Y",       "latest"),
        "P6-12": ("M2SL",         "yoy"),
    }
    for iid, (series, mode) in fred_map.items():
        try:
            vals[iid] = _fred_latest(series) if mode == "latest" else _fred_yoy(series)
        except Exception as e:
            fetch_errors.append(f"FRED {series}: {e}")

    # Real 10Y yield = DGS10 − CPI YoY
    try:
        dgs10 = _fred_latest("DGS10")
        cpi   = _fred_yoy("CPIAUCSL")
        if dgs10 is not None and cpi is not None:
            vals["P2-02"] = dgs10 - cpi
    except Exception as e:
        fetch_errors.append(f"Real 10Y: {e}")

    # Credit spread 3M change (P6-11)
    try:
        df_ig = _fred_df("BAMLC0A0CM")
        if df_ig is not None and len(df_ig) > 63:
            vals["P6-11"] = float(df_ig["value"].iloc[-1]) - float(df_ig["value"].iloc[-63])
    except Exception as e:
        fetch_errors.append(f"P6-11: {e}")

    # World Bank
    try:
        vals["P3-01"] = _worldbank("NY.GDP.MKTP.KD.ZG")
    except Exception as e:
        fetch_errors.append(f"WB GDP: {e}")
    try:
        vals["P3-06"] = _worldbank("GC.DOD.TOTL.GD.ZS")
    except Exception as e:
        fetch_errors.append(f"WB debt: {e}")

    return vals, fetch_errors


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_indicator(value, ind: dict) -> int | None:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    v = float(value)
    if ind["buy_min"] <= v <= ind["buy_max"]:
        return 1
    if ind["hold_min"] <= v <= ind["hold_max"]:
        return 0
    if ind["sell_min"] <= v <= ind["sell_max"]:
        return -1
    return None


def compute_scores(all_vals: dict, mode: str = "Base"):
    pillar_results = {}
    for p in range(1, 7):
        inds = [i for i in INDICATORS if i["pillar"] == p]
        rows = []
        for ind in inds:
            val = all_vals.get(ind["id"])
            s = score_indicator(val, ind)
            rows.append({
                "id": ind["id"],
                "name": ind["name"],
                "unit": ind["unit"],
                "source": ind["source"],
                "value": val,
                "signal": {1: "BUY", 0: "HOLD", -1: "SELL"}.get(s, "N/A"),
                "score": s,
                "weight": ind["weight"],
                "auto": ind["id"] in AUTO_FETCH_IDS,
            })
        valid = [r for r in rows if r["score"] is not None]
        total_w = sum(r["weight"] for r in valid)
        pscore = sum(r["weight"] * r["score"] for r in valid) / total_w if total_w > 0 else 0.0
        pillar_results[p] = {
            "score": pscore,
            "rows": rows,
            "coverage": len(valid) / len(inds) if inds else 0,
        }

    pw = PILLAR_WEIGHTS[mode]
    final = sum(pw[p] * pillar_results[p]["score"] for p in range(1, 7))
    return pillar_results, final


def decision(score: float) -> tuple[str, str]:
    if score > 0.40:
        return "STRONG BUY", "#1a7a1a"
    if score > 0.10:
        return "BUY / Selective Add", "#2ecc71"
    if score >= -0.10:
        return "HOLD / Neutral", "#e67e22"
    return "REDUCE / SELL", "#c0392b"


def signal_color(sig: str) -> str:
    return {"BUY": "#2ecc71", "HOLD": "#e67e22", "SELL": "#c0392b"}.get(sig, "#888888")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def pillar_card(p: int, data: dict, pillar_weight: float):
    score = data["score"]
    label, color = decision(score)
    cov = data["coverage"]

    st.markdown(
        f"""
        <div style="border:1px solid #ddd;border-radius:8px;padding:14px 16px;height:100%">
          <div style="font-size:0.75rem;color:#888;font-weight:600;text-transform:uppercase;
                      letter-spacing:.05em">P{p} · wt {pillar_weight:.0%}</div>
          <div style="font-size:1.05rem;font-weight:700;margin:2px 0 4px">
            {PILLAR_NAMES[p]}</div>
          <div style="font-size:2rem;font-weight:800;color:{color};line-height:1">
            {score:+.2f}</div>
          <div style="font-size:0.8rem;color:{color};font-weight:600;margin-top:2px">
            {label}</div>
          <div style="font-size:0.72rem;color:#aaa;margin-top:6px">
            {cov:.0%} indicators scored ({sum(1 for r in data['rows'] if r['score'] is not None)}/{len(data['rows'])})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Indicators  ({len(data['rows'])})"):
        table_rows = []
        for r in data["rows"]:
            val_str = f"{r['value']:.3g}" if r["value"] is not None else "—"
            src_tag = "auto" if r["auto"] else "manual"
            table_rows.append({
                "ID": r["id"],
                "Indicator": r["name"],
                "Value": val_str,
                "Unit": r["unit"],
                "Signal": r["signal"],
                "Wt": f"{r['weight']:.0%}",
                "Source": src_tag,
            })
        df = pd.DataFrame(table_rows)

        def _style(row):
            c = signal_color(row["Signal"])
            return [""] * 4 + [f"color:{c};font-weight:600"] + [""] * 2

        st.dataframe(
            df.style.apply(_style, axis=1),
            hide_index=True,
            use_container_width=True,
        )


def render_sidebar() -> dict[str, float]:
    st.sidebar.header("Manual Inputs")
    st.sidebar.caption(
        "Auto-fetched indicators (yfinance / FRED / World Bank) are filled automatically. "
        "Adjust these to reflect your portfolio, industry, and macro views."
    )

    manual_vals: dict[str, float] = {}

    groups = [
        ("P1: Asset Allocation (Portfolio)", ["P1-01","P1-02","P1-03","P1-04","P1-05","P1-06","P1-07","P1-08"]),
        ("P2: Asset Class – Manual Overrides", ["P2-01","P2-08"]),
        ("P3: Geographic Macro", ["P3-03","P3-05","P3-07","P3-08","P3-09","P3-10","P3-11","P3-12","P3-13","P3-14"]),
        ("P4: Industry Selection", ["P4-01","P4-02","P4-03","P4-04","P4-05","P4-06","P4-07","P4-08","P4-09","P4-10","P4-11","P4-12"]),
        ("P5: Security – Extra Inputs", ["P5-10","P5-11","P5-16"]),
        ("P6: Timing – Extra Inputs",  ["P6-01","P6-02","P6-09","P6-13"]),
    ]

    for group_label, ids in groups:
        with st.sidebar.expander(group_label, expanded=False):
            for iid in ids:
                cfg = MANUAL_CONFIG.get(iid)
                if cfg is None:
                    continue
                label, lo, hi, step, fmt = cfg
                default = float(MANUAL_DEFAULTS.get(iid, (lo + hi) / 2))
                default = max(lo, min(hi, default))
                val = st.slider(
                    label,
                    min_value=lo,
                    max_value=hi,
                    value=default,
                    step=step,
                    key=f"slider_{iid}",
                    format=fmt,
                )
                manual_vals[iid] = val

    return manual_vals


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="6-Pillar Stock Evaluator",
        page_icon=None,
        layout="wide",
    )

    # ---- Auto-refresh every hour (3 600 000 ms) ----
    refresh_count = st_autorefresh(interval=1_800_000, key="hourly_refresh")

    # ---- Session state init ----
    for key, default in [
        ("last_refresh", None),
        ("last_ticker", "AAPL"),
        ("last_mode", "Base"),
        ("prev_refresh_count", 0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Detect hourly auto-refresh firing
    auto_fired = (refresh_count != st.session_state.prev_refresh_count
                  and refresh_count > 0)
    if auto_fired:
        st.session_state.prev_refresh_count = refresh_count
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()

    st.title("6-Pillar Investment Evaluator")

    # ---- Tabs ----
    tab_profile, tab_analysis = st.tabs(["Investor Profile", "Stock Evaluator"])

    with tab_profile:
        render_profile_tab()

    with tab_analysis:
        st.caption(
            "Scores a single stock across 82 indicators. "
            "Auto-fetches from Yahoo Finance, FRED, and World Bank. "
            "Fill sidebar P1 sliders via the Investor Profile tab."
        )

        # ---- Top controls ----
        col_ticker, col_mode, col_analyze, col_refresh = st.columns([2, 2, 1, 1])
        with col_ticker:
            ticker = st.text_input(
                "Ticker", value=st.session_state.last_ticker,
                label_visibility="collapsed",
                placeholder="Enter ticker (e.g. AAPL)",
            ).upper().strip()
        with col_mode:
            mode = st.radio(
                "Market mode", ["Base", "Bull", "Bear"], horizontal=True,
                index=["Base", "Bull", "Bear"].index(st.session_state.last_mode),
            )
        with col_analyze:
            run = st.button("Analyze", type="primary", use_container_width=True)
        with col_refresh:
            manual_refresh = st.button("Refresh Data", use_container_width=True)

        # Manual refresh: clear cache and rerun immediately
        if manual_refresh:
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()

        # ---- Refresh status line ----
        _, status_col = st.columns([3, 1])
        with status_col:
            if st.session_state.last_refresh:
                elapsed  = int((datetime.now() - st.session_state.last_refresh).total_seconds())
                next_min = max(0, 30 - elapsed // 60)
                st.caption(
                    f"Last refreshed: {st.session_state.last_refresh.strftime('%H:%M:%S')}  \n"
                    f"Next auto-refresh in: ~{next_min} min"
                )
            else:
                st.caption("Auto-refresh: every 30 minutes")

        manual_vals = render_sidebar()

        # Run if Analyze clicked OR auto-refresh fired with a previous ticker
        should_run = run or (auto_fired and bool(st.session_state.last_ticker))

        if not should_run:
            st.info("Enter a ticker and click **Analyze** to run the evaluation.")
        else:
            if not ticker:
                st.warning("Please enter a ticker symbol.")
            else:
                # Persist ticker + mode for auto-refresh reruns
                st.session_state.last_ticker = ticker
                st.session_state.last_mode   = mode

                # Auto-resolve Thai SET stocks: if no dot suffix, try .BK
                if "." not in ticker:
                    probe = yf.Ticker(f"{ticker}.BK").info
                    if probe.get("regularMarketPrice") or probe.get("currentPrice"):
                        ticker = f"{ticker}.BK"
                        st.session_state.last_ticker = ticker
                        st.info(f"Thai SET stock detected — using ticker **{ticker}**")

                # Fetch & score
                with st.spinner(f"Fetching data for {ticker}…"):
                    auto_vals, errors = compute_auto_values(ticker)

                # ---- Stock info header ----
                try:
                    info, hist, _, _, _ = _fetch_stock(ticker)
                    name     = info.get("longName") or info.get("shortName") or ticker
                    currency = info.get("currency") or ""
                    exchange = info.get("exchange") or ""
                    mktcap   = info.get("marketCap")
                    sector   = info.get("sector") or ""
                    industry = info.get("industry") or ""

                    price = (
                        info.get("currentPrice")
                        or info.get("regularMarketPrice")
                        or info.get("ask")
                        or info.get("bid")
                    )
                    if not price and hist is not None and len(hist):
                        price = float(hist["Close"].iloc[-1])

                    prev = (
                        info.get("previousClose")
                        or info.get("regularMarketPreviousClose")
                    )
                    if not prev and hist is not None and len(hist) >= 2:
                        prev = float(hist["Close"].iloc[-2])

                    day_chg     = (price - prev) if (price and prev) else None
                    day_chg_pct = (day_chg / prev * 100) if (day_chg is not None and prev) else None
                    chg_color   = "#2ecc71" if (day_chg_pct or 0) >= 0 else "#c0392b"
                    chg_sign    = "+" if (day_chg_pct or 0) >= 0 else ""

                    def fmt_mktcap(v):
                        if not v: return "—"
                        if v >= 1e12: return f"{v/1e12:.2f}T"
                        if v >= 1e9:  return f"{v/1e9:.2f}B"
                        if v >= 1e6:  return f"{v/1e6:.2f}M"
                        return f"{v:,.0f}"

                    price_str = f"{price:,.2f} {currency}".strip() if price else "—"
                    chg_str   = (f"{chg_sign}{day_chg:.2f} ({chg_sign}{day_chg_pct:.2f}%)"
                                 if day_chg is not None else "")

                    st.markdown(
                        f"""
                        <div style="background:#f8f9fa;border:1px solid #e0e0e0;border-radius:10px;
                                    padding:16px 24px;margin:12px 0 4px;display:flex;
                                    align-items:center;gap:32px;flex-wrap:wrap">
                          <div>
                            <div style="font-size:1.1rem;font-weight:700">{name}</div>
                            <div style="font-size:0.78rem;color:#888">{ticker} · {exchange}</div>
                          </div>
                          <div>
                            <div style="font-size:2rem;font-weight:900;line-height:1">{price_str}</div>
                            <div style="font-size:0.9rem;color:{chg_color};font-weight:600">{chg_str}</div>
                          </div>
                          <div style="color:#666;font-size:0.82rem">
                            <div><b>Market Cap</b>&nbsp; {fmt_mktcap(mktcap)}</div>
                            <div><b>Sector</b>&nbsp; {sector or '—'}</div>
                            <div><b>Industry</b>&nbsp; {industry or '—'}</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.caption(f"Could not load stock header: {e}")

                # Merge: manual provides fallback, auto overrides where successful
                all_vals = dict(manual_vals)
                for k, v in auto_vals.items():
                    if v is not None:
                        all_vals[k] = v

                if errors:
                    with st.expander(f"Fetch warnings ({len(errors)}) — non-critical, manual values used as fallback"):
                        for e in errors:
                            st.caption(f"- {e}")

                pillar_results, final_score = compute_scores(all_vals, mode)
                label, color = decision(final_score)
                pw = PILLAR_WEIGHTS[mode]

                # Final decision banner
                st.markdown(
                    f"""
                    <div style="background:{color}18;border:2px solid {color};border-radius:10px;
                                padding:20px 28px;margin:16px 0;display:flex;align-items:center;gap:32px">
                      <div>
                        <div style="font-size:0.8rem;color:#888;font-weight:600;text-transform:uppercase">
                          Final Score  ·  {mode} mode</div>
                        <div style="font-size:3rem;font-weight:900;color:{color};line-height:1">
                          {final_score:+.3f}</div>
                      </div>
                      <div>
                        <div style="font-size:0.8rem;color:#888;font-weight:600;text-transform:uppercase">
                          Decision</div>
                        <div style="font-size:1.8rem;font-weight:800;color:{color}">{label}</div>
                        <div style="font-size:0.75rem;color:#888;margin-top:4px">
                          &gt;+0.40 Strong Buy · +0.10→+0.40 Buy · −0.10→+0.10 Hold · &lt;−0.10 Reduce/Sell
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Pillar score bar
                st.subheader("Pillar Breakdown")
                bar_cols = st.columns(6)
                for idx, p in enumerate(range(1, 7)):
                    s = pillar_results[p]["score"]
                    _, c = decision(s)
                    bar_cols[idx].metric(
                        label=f"P{p}",
                        value=f"{s:+.2f}",
                        delta=PILLAR_NAMES[p],
                        delta_color="off",
                    )

                # Pillar cards (2 rows × 3)
                st.markdown("---")
                row1 = st.columns(3)
                row2 = st.columns(3)
                for idx, p in enumerate(range(1, 7)):
                    col = row1[idx] if idx < 3 else row2[idx - 3]
                    with col:
                        pillar_card(p, pillar_results[p], pw[p])

                # Auto-fetch summary
                n_auto   = sum(1 for k in AUTO_FETCH_IDS if all_vals.get(k) is not None)
                n_manual = sum(1 for k in MANUAL_CONFIG if all_vals.get(k) is not None and k not in AUTO_FETCH_IDS)
                st.markdown("---")
                st.caption(
                    f"Data coverage: {n_auto} auto-fetched + {n_manual} manual = "
                    f"{n_auto + n_manual} / 74 indicators with values."
                )


if __name__ == "__main__":
    main()
