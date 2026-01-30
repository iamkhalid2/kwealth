# 📊 Munger-Buffett Analyst Swarm

A multi-agent stock analysis system that synthesizes opposing investment perspectives into balanced recommendations. The system channels **Charlie Munger's** skeptical "inversion thinking" and **Warren Buffett's** value-focused optimism through separate AI agents, then merges their insights into actionable investment theses.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 What It Does

Given a stock ticker (e.g., `AAPL`, `MSTR`, `TSLA`), the system:

1. **Fetches** real-time financial metrics and news via `yfinance`
2. **Generates** a **Bear Memo** using Munger-style skepticism (focuses on risks, red flags, overvaluation)
3. **Generates** a **Bull Memo** using Buffett-style value analysis (focuses on moats, pricing power, durability)
4. **Synthesizes** both perspectives into a final recommendation with confidence scoring and caveats

**Output:** A structured report with:
- Final recommendation: `STRONG_BUY` | `BUY` | `HOLD` | `SELL` | `STRONG_SELL`
- Confidence score (0.0–1.0)
- Balanced synthesis summary
- Key caveats for independent verification
- Full bear and bull analyst memos

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
│  (Ticker)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│               Scout Agent (scout.py)                  │
│  • Fetches financial metrics from yfinance           │
│  • Pulls recent news headlines                       │
│  → Outputs: ScoutReport                              │
└───────────────────┬──────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Bear Analyst    │    │  Bull Analyst    │
│  (Munger AI)     │    │  (Buffett AI)    │
│                  │    │                  │
│  Gemini LLM      │    │  Gemini LLM      │
│  + System Prompt │    │  + System Prompt │
│                  │    │                  │
│  → AnalystMemo   │    │  → AnalystMemo   │
│    (Bear)        │    │    (Bull)        │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌────────────────────────┐
         │  Synthesizer Agent     │
         │  (synthesizer.py)      │
         │                        │
         │  Gemini LLM            │
         │  Weighs both theses    │
         │                        │
         │  → FinalRecommendation │
         └────────────────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  Rich UI Report        │
         │  • Colored badge       │
         │  • Confidence score    │
         │  • Synthesis summary   │
         │  • Caveats list        │
         │  • Expandable memos    │
         └────────────────────────┘
```

---

## 🚀 Setup

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/iamkhalid2/kwealth.git
   cd kwealth
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**
   
   Create a `.env` file (use `.env.example` as template):
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

---

## 💻 Usage

### Run the Streamlit UI

```bash
streamlit run app.py
# or
python -m streamlit run app.py
```

Then open your browser to `http://localhost:8501`

### Example Workflow

1. Enter a ticker: `AAPL`
2. Click **🔍 Analyze**
3. Watch the multi-step progress:
   - ✅ Fetching data...
   - ✅ Generating Bear memo (Munger)...
   - ✅ Generating Bull memo (Buffett)...
   - ✅ Synthesizing recommendations...
4. Review the final report with metrics, memos, and caveats

### Programmatic Usage

```python
from agents.scout import fetch_scout_report
from agents.analyst import generate_bear_memo, generate_bull_memo
from agents.synthesizer import synthesize

# Fetch data
report = fetch_scout_report("AAPL")

# Generate opposing perspectives
bear = generate_bear_memo(report)
bull = generate_bull_memo(report)

# Synthesize final recommendation
final = synthesize(bull, bear, report.metrics)

print(f"Recommendation: {final.recommendation}")
print(f"Confidence: {final.confidence_score}")
print(f"Summary: {final.synthesis_summary}")
```

---

## 🔧 Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Gemini model to use |
| `REQUEST_TIMEOUT` | `30` | API timeout in seconds |
| `MAX_HEADLINES` | `5` | Number of news headlines to fetch |

---

## 📂 Project Structure

```
kwealth/
├── SPEC.md                 # Full technical specification
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── config.py               # Centralized configuration
├── app.py                  # Streamlit UI (entry point)
└── agents/
    ├── __init__.py         # Package exports
    ├── schemas.py          # Pydantic data models
    ├── scout.py            # Financial data fetcher
    ├── analyst.py          # Bear/Bull memo generators
    └── synthesizer.py      # Final recommendation logic
```

---

## 🧠 How It Works

### 1. Scout Agent (Data Gathering)
- Calls `yfinance` to fetch:
  - Financial metrics (P/E, P/B, D/E, FCF, market cap, etc.)
  - Recent news headlines
- Normalizes data (e.g., converts yfinance's D/E percentage to ratio)
- Returns structured `ScoutReport`

### 2. Analyst Agents (Perspective Generation)

**Bear Agent (Munger)** focuses on:
- Hidden risks and overvaluation
- Debt concerns and accounting red flags
- Competitive threats and market saturation
- Crypto/fad exposure warnings

**Bull Agent (Buffett)** focuses on:
- Durable competitive moats
- Brand power and pricing power
- Free cash flow generation
- Management quality and capital allocation

Both use **Gemini's structured output** to produce typed `AnalystMemo` objects with:
- Summary (3-4 sentences)
- Key points (3-5 bullets)
- Risk/reward assessment
- Confidence score

### 3. Synthesizer Agent (Final Judgment)

- Receives both bear and bull memos + current metrics
- Uses Gemini to weigh arguments intelligently (not simple averaging)
- Produces:
  - Final recommendation enum
  - Confidence score (0.0–1.0)
  - Synthesis summary balancing both views
  - 3-5 specific caveats for user to verify independently

---

## 📊 Example Output

### AAPL Analysis (January 2026)

**Recommendation:** `SELL` (Confidence: 70%)

**Synthesis:**
> While Apple remains a premier cash-flow engine with an unrivaled ecosystem, the valuation has reached levels that ignore structural risks. A P/B ratio over 51 and 32x P/E for a maturing hardware business suggest the stock is priced for perfection. The bear argument regarding financial engineering is compelling; using debt to fund buybacks at these valuations suggests management is prioritizing EPS support over fundamental reinvestment...

**Key Caveats:**
- ⚠️ Verify net cash position to determine if 152% D/E is mitigated by offshore liquidity
- ⚠️ Monitor US/EU antitrust cases targeting App Store commission structures
- ⚠️ Evaluate upcoming iPhone refresh cycle for genuine AI-driven super-cycle
- ⚠️ Analyze Services growth sustainability if third-party payments are mandated
- ⚠️ Check for shifts in capital allocation strategy at current price levels

---

## 🛡️ Error Handling

The system gracefully handles:
- **Invalid tickers:** Shows user-friendly error message
- **API failures:** Catches Gemini 503/timeout errors with clear messages
- **Missing data:** Displays "N/A" for unavailable metrics (e.g., no dividend yield for growth stocks)

---

## 🔒 Security Notes

- Never commit `.env` with real API keys
- API key is loaded via `python-dotenv` from `.env`
- Use `.env.example` as a template for sharing

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] Add support for portfolio-level analysis
- [ ] Integrate additional data sources (SEC filings, earnings transcripts)
- [ ] Implement caching for repeated ticker lookups
- [ ] Add charting/visualization for historical performance
- [ ] Support non-US stocks

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **yfinance** for financial data
- **Google Gemini** for LLM-powered analysis
- **Streamlit** for rapid UI prototyping
- Inspired by the investment philosophies of Charlie Munger and Warren Buffett

---

## ⚠️ Disclaimer

**This tool is for educational and research purposes only.** It does not constitute financial advice. Always conduct your own due diligence and consult with a qualified financial advisor before making investment decisions. The system's recommendations are generated by AI and may contain errors or biases.
