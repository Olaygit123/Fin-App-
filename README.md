# 6-Pillar Investment Evaluator

A professional single-stock investment evaluator built with Python and Streamlit. It scores any stock across **82 indicators** organised into 6 pillars, fetches live data automatically, and delivers a clear BUY / HOLD / SELL decision — all in your browser.

Supports both **US stocks** (NYSE, NASDAQ) and **Thai SET stocks** (auto-detects `.BK` suffix).

---

## Features

- **6-Pillar Scoring System** — Portfolio Allocation, Asset Class, Geographic Macro, Industry, Security Selection, and Market Timing
- **82 Indicators** — 43 auto-fetched, 39 adjustable via sidebar sliders
- **Live Data** — Yahoo Finance, FRED (Federal Reserve), and World Bank APIs — no API keys required
- **Thai SET Stock Support** — enter `BBL` or `PTT`, the app auto-adds `.BK`
- **AI Investor Profile** — bilingual (English / Thai) questionnaire powered by Claude AI; auto-fills your P1 Asset Allocation sliders
- **3 Market Modes** — Base, Bull, Bear (different pillar weights)
- **Hourly Auto-Refresh** — data updates in the background every hour
- **Manual Refresh** — refresh on demand with one click

---

## Screenshots

| Investor Profile (EN/TH) | Stock Evaluator |
|---|---|
| Complete a 15-question risk questionnaire | Enter any ticker and get a scored decision |
| AI interprets your answers | See all 6 pillar scores with indicator breakdown |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Olaygit123/Fin-App-.git
cd Fin-App-
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Anthropic API key (optional — for AI investor profiling)

Copy the example secrets file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` and replace the placeholder with your real key:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-your-real-key-here"
```

Get a free API key at [console.anthropic.com](https://console.anthropic.com).

> If you skip this step, the app still works fully — it falls back to a rule-based investor profile instead of AI.

### 4. Run the app

```bash
python3 -m streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## How to Use

### Tab 1 — Investor Profile

1. Choose your language (English / Thai)
2. Answer 15 questions about your financial goals, risk tolerance, and investment experience
3. Click **Submit**
4. The AI (or rule-based fallback) assigns you a profile: Conservative / Moderate / Aggressive / Very Aggressive
5. Click **Apply Profile to P1** — your Asset Allocation sliders update automatically

### Tab 2 — Stock Evaluator

1. Enter a ticker in the search box (e.g. `AAPL`, `MSFT`, `BBL`, `PTT`)
2. Select a market mode: **Base**, **Bull**, or **Bear**
3. Adjust sidebar sliders for any manual inputs (optional)
4. Click **Analyze**
5. View the final decision, pillar breakdown, and full indicator table

---

## Scoring System

### Decision Thresholds

| Final Score | Decision |
|---|---|
| > +0.40 | **Strong Buy** |
| +0.10 to +0.40 | **Buy / Selective Add** |
| -0.10 to +0.10 | **Hold / Neutral** |
| < -0.10 | **Reduce / Sell** |

### The 6 Pillars

| Pillar | Name | Base Weight |
|---|---|---|
| P1 | Portfolio & Asset Allocation | 15% |
| P2 | Asset Class Attractiveness | 15% |
| P3 | Geographic & Macro | 15% |
| P4 | Industry Selection | 15% |
| P5 | Security Selection | 20% |
| P6 | Market Timing | 20% |

Weights shift in Bull and Bear modes to reflect changing market conditions.

### Data Sources

| Source | Data |
|---|---|
| Yahoo Finance (`yfinance`) | Price, fundamentals, analyst targets, short interest |
| FRED (Federal Reserve) | Credit spreads, CPI, yield curve, M2, PMI |
| World Bank API | GDP growth, government debt/GDP |
| Manual sliders | Portfolio metrics, industry data, macro overrides |

---

## Professional Indicators Included

Beyond the standard 74 indicators, the app includes 8 advanced metrics:

- **Economic Moat Score** — composite of ROIC, Gross Margin, and Revenue Consistency
- **Piotroski F-Score** — 9-point financial health test
- **Altman Z-Score** — bankruptcy risk model
- **EV / FCF** — enterprise value vs. free cash flow
- **Accruals Ratio** — earnings quality check
- **Total Shareholder Yield** — dividends + buybacks
- **Analyst Price Target Upside** — consensus vs. current price
- **Short Interest % Float** — market sentiment signal

---

## Project Structure

```
Fin-App-/
├── app.py                        # Main Streamlit application
├── indicators.py                 # All 82 indicators with BUY/HOLD/SELL thresholds
├── profile.py                    # Investor questionnaire (EN/TH) + Claude AI integration
├── requirements.txt              # Python dependencies
├── .gitignore                    # Excludes secrets.toml from version control
└── .streamlit/
    └── secrets.toml.example      # Template for your API key (copy → secrets.toml)
```

---

## Requirements

- Python 3.9+
- Internet connection (for live data fetching)
- Anthropic API key (optional — only needed for AI investor profiling)

---

## Dependencies

```
streamlit>=1.32.0
yfinance>=0.2.38
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
streamlit-autorefresh>=1.0.1
anthropic>=0.25.0
```

---

## Notes

- The app does **not store any data** — all fetched data is cached in memory for 1 hour only
- Thai SET stocks are supported — just enter the ticker without `.BK` and the app detects it automatically
- The app runs entirely locally on your machine — no data is sent anywhere except to the public APIs listed above
- The Anthropic API is only called when you submit the investor questionnaire

---

## License

This project is for personal and educational use.
