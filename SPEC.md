# Munger-Buffett Analyst Swarm - SPEC.md

---

## 1. Project Overview

**Goal:** Given a stock ticker, produce a balanced investment thesis by synthesizing a "Bear Memo" (Munger-style skepticism) and a "Bull Memo" (Buffett-style optimism) into a final recommendation with a confidence score (0.0-1.0) and key caveats.

**Core Stack:**
- **Python 3.11+**
- **google-genai** (Gemini 3.0 Flash) — for LLM calls (new SDK, not `google-generativeai`)
- **yfinance** — for financial data
- **Streamlit** — for UI

---

## 2. Directory Structure

```
kwealth/
├── SPEC.md                 # This file
├── requirements.txt        # Dependencies
├── .env.example            # Template for API keys
├── app.py                  # [ENTRY POINT] Streamlit UI
├── config.py               # Centralized configuration
└── agents/
    ├── __init__.py
    ├── schemas.py          # Pydantic models (Data Contracts)
    ├── scout.py            # Scout Agent: fetches raw data
    ├── analyst.py          # Munger & Buffett agents
    └── synthesizer.py      # Final recommendation logic
```

---

## 3. Data Dictionary (Contracts)

All inter-agent data is typed with **Pydantic**. No raw dicts.

### `schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Literal

class FinancialMetrics(BaseModel):
    """Core financial data from yfinance."""
    ticker: str
    company_name: str
    current_price: float
    pe_ratio: float | None = Field(description="Trailing P/E")
    forward_pe: float | None
    price_to_book: float | None
    debt_to_equity: float | None
    free_cash_flow: float | None = Field(description="In USD")
    market_cap: float | None
    dividend_yield: float | None
    fifty_two_week_high: float
    fifty_two_week_low: float
    sector: str | None
    industry: str | None

class NewsHeadline(BaseModel):
    """Single news item from yfinance."""
    title: str
    publisher: str
    link: str | None = None

class ScoutReport(BaseModel):
    """Output of Scout Agent."""
    metrics: FinancialMetrics
    headlines: list[NewsHeadline]
    fetch_timestamp: str

class AnalystMemo(BaseModel):
    """Output of Munger/Buffett Agents."""
    perspective: Literal["bear", "bull"]
    ticker: str
    summary: str = Field(max_length=500, description="3-4 sentence summary")
    key_points: list[str] = Field(min_length=3, max_length=5)
    risk_reward_assessment: str = Field(max_length=300)
    confidence_in_thesis: float = Field(ge=0.0, le=1.0)

class FinalRecommendation(BaseModel):
    """Output of Synthesizer."""
    ticker: str
    recommendation: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    synthesis_summary: str = Field(max_length=600)
    key_caveats: list[str] = Field(min_length=1, max_length=5)
    bull_memo: AnalystMemo
    bear_memo: AnalystMemo
```

---

## 4. Component Specifications

### 4.1 `config.py` — Configuration

**Responsibility:** Centralize all configurable values.

```python
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-flash-preview"  # Fast, cheap, sufficient
REQUEST_TIMEOUT = 30  # seconds
MAX_HEADLINES = 5
```

**Constraints:**
- No hardcoded API keys.
- Single source of truth for model name.

---

### 4.2 `agents/scout.py` — Scout Agent

**Responsibility:** Fetch financial metrics and news headlines for a ticker.

**Inputs:**
```python
def fetch_scout_report(ticker: str) -> ScoutReport:
```

**Outputs:** `ScoutReport` (see schemas)

**Internal Logic:**
1. Use `yfinance.Ticker(ticker).info` for metrics.
2. Use `yfinance.Ticker(ticker).news` for headlines (up to `MAX_HEADLINES`).
3. Handle missing data gracefully (set to `None`).

**Constraints:**
- **No LLM calls.** Pure data fetching.
- If yfinance returns empty/invalid data, raise `ValueError` with clear message.

---

### 4.3 `agents/analyst.py` — Munger & Buffett Agents

**Responsibility:** Generate perspective-specific memos using an LLM.

**Inputs:**
```python
def generate_bear_memo(report: ScoutReport) -> AnalystMemo:
def generate_bull_memo(report: ScoutReport) -> AnalystMemo:
```

**Outputs:** `AnalystMemo`

**Internal Logic (shared):**
1. Build a system prompt defining the persona (Munger = skeptic, Buffett = optimist).
2. Inject `ScoutReport` as JSON into the user prompt.
3. Request **structured JSON output** from Gemini using `response_mime_type="application/json"` and `response_schema`.
4. Parse response directly into `AnalystMemo`.

**Prompt Templates:**

```
# MUNGER SYSTEM PROMPT
You are Charlie Munger, legendary investor known for inversion thinking.
Analyze the following stock data with EXTREME SKEPTICISM.
Focus on: hidden risks, excessive debt, accounting red flags, competitive threats, management incompetence, crypto/fad exposure.
Do NOT sugarcoat. Find what could go wrong.
```

```
# BUFFETT SYSTEM PROMPT
You are Warren Buffett, the Oracle of Omaha.
Analyze the following stock data with a focus on LONG-TERM VALUE.
Focus on: durable competitive advantages (moats), brand power, pricing power, compounding potential, management quality, margin of safety.
Be realistic but identify genuine strengths.
```

**Constraints:**
- Use `google.genai.Client().models.generate_content()` (new SDK). No LangChain.
- Use Gemini's native structured output via `response.parsed` (not manual JSON parsing).
- Temperature = 0.7 for creativity within structured bounds.

---

### 4.4 `agents/synthesizer.py` — Synthesizer Agent

**Responsibility:** Merge bear and bull memos into a final balanced recommendation.

**Inputs:**
```python
def synthesize(bull: AnalystMemo, bear: AnalystMemo, metrics: FinancialMetrics) -> FinalRecommendation:
```

**Outputs:** `FinalRecommendation`

**Internal Logic:**
1. Build a synthesis prompt that includes both memos as JSON.
2. Instruct LLM to weigh both perspectives and produce:
   - A `recommendation` enum value
   - A `confidence_score` (weighted average informed by both thesis confidences)
   - Key `caveats` the user must independently verify
3. Parse into `FinalRecommendation`.

**Prompt Template:**
```
You are a senior investment committee synthesizing two analyst reports.
BULL MEMO: {bull_json}
BEAR MEMO: {bear_json}
CURRENT METRICS: {metrics_json}

Produce a balanced final recommendation.
Weight the stronger argument. Do not default to "HOLD" without justification.
Identify 3-5 caveats the investor must verify independently.
```

**Constraints:**
- Confidence score is NOT a simple average. LLM must reason about which thesis is stronger.
- Must return structured output.

---

### 4.5 `app.py` — Streamlit Entry Point

**Responsibility:** Provide a simple UI for input/output.

**UI Flow:**
1. Text input for ticker symbol.
2. "Analyze" button triggers the pipeline.
3. Use `st.status()` container to show multi-step progress (Scout → Bear → Bull → Synthesize).
4. Display:
   - **Final Recommendation** (large, colored badge)
   - **Confidence Score** (progress bar)
   - **Synthesis Summary**
   - **Key Caveats** (bulleted list)
   - **Expandable sections** for full Bull/Bear memos.

**Constraints:**
- No session state complexity. Single-page, stateless.
- Handle errors gracefully (invalid ticker, API failures) with `st.error()`.
- Display raw metrics in a sidebar for transparency.

---

## 5. Implementation Plan

### Phase 1: Foundation (Schemas + Scout)

| Task | File | Details |
|------|------|---------|
| 1.1 | `requirements.txt` | `yfinance`, `google-genai`, `streamlit`, `pydantic`, `python-dotenv` |
| 1.2 | `.env.example` | `GEMINI_API_KEY=your_key_here` |
| 1.3 | `config.py` | Load env vars, define constants |
| 1.4 | `agents/schemas.py` | All Pydantic models |
| 1.5 | `agents/scout.py` | `fetch_scout_report()` |

**Verification:**
```bash
# In Python REPL or test script:
from agents.scout import fetch_scout_report
report = fetch_scout_report("AAPL")
print(report.model_dump_json(indent=2))
```
Expected: Valid JSON with metrics and headlines.

---

### Phase 2: Core Analysts (Munger + Buffett + Synthesizer)

| Task | File | Details |
|------|------|---------|
| 2.1 | `agents/analyst.py` | `generate_bear_memo()`, `generate_bull_memo()` |
| 2.2 | `agents/synthesizer.py` | `synthesize()` |

**Verification:**
```bash
# Test with mock ScoutReport or real data:
from agents.scout import fetch_scout_report
from agents.analyst import generate_bear_memo, generate_bull_memo
from agents.synthesizer import synthesize

report = fetch_scout_report("MSTR")
bear = generate_bear_memo(report)
bull = generate_bull_memo(report)
final = synthesize(bull, bear, report.metrics)
print(final.model_dump_json(indent=2))
```
Expected: Structured `FinalRecommendation` with valid enum, score, and caveats.

---

### Phase 3: UI Integration (Streamlit)

| Task | File | Details |
|------|------|---------|
| 3.1 | `app.py` | Full Streamlit app |

**Verification:**
```bash
streamlit run app.py
```
- Enter `AAPL` → Should display full report.
- Enter `INVALIDTICKER123` → Should show error message.
- Enter `MSTR` → Should highlight crypto/volatility caveats.

---

## 6. Progress Tracker

- [x] Phase 1 Complete (Foundation) - Tested Scout Agent 
- [x] Phase 2 Complete (Core Agents) - Tested Munger, Buffett, Synthesizer
- [ ] Phase 3 Complete (UI)

---

## Appendix: Key Implementation Notes

### Gemini Structured Output Pattern (New SDK)
```python
from google import genai
from google.genai import types
from agents.schemas import AnalystMemo
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AnalystMemo,  # Pydantic model
        temperature=0.7,
    ),
)

# Use .parsed for direct Pydantic object (no manual JSON parsing)
memo: AnalystMemo = response.parsed
```

### yfinance Quick Reference
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info  # dict with 100+ keys
news = ticker.news  # list of news dicts

# Key fields for FinancialMetrics:
# info["trailingPE"], info["forwardPE"], info["priceToBook"]
# info["debtToEquity"], info["freeCashflow"], info["marketCap"]
# info["dividendYield"], info["fiftyTwoWeekHigh"], info["fiftyTwoWeekLow"]
# info["currentPrice"], info["longName"], info["sector"], info["industry"]

# News structure:
# news[0] = {"title": "...", "publisher": "...", "link": "...", ...}
```

---

*Last Updated: 2026-01-30*
