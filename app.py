"""Streamlit UI for Munger-Buffett Analyst Swarm."""

import streamlit as st

from agents.scout import fetch_scout_report
from agents.analyst import generate_bear_memo, generate_bull_memo
from agents.synthesizer import synthesize
from agents.schemas import FinancialMetrics, AnalystMemo, FinalRecommendation


# --- Helper Functions ---

def format_large_number(n: float | None) -> str:
    """Format large numbers to human-readable (e.g., $3.8T, $78.9B)."""
    if n is None:
        return "N/A"
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1e12:
        return f"{sign}${abs_n / 1e12:.2f}T"
    elif abs_n >= 1e9:
        return f"{sign}${abs_n / 1e9:.2f}B"
    elif abs_n >= 1e6:
        return f"{sign}${abs_n / 1e6:.2f}M"
    else:
        return f"{sign}${abs_n:,.2f}"


def format_percent(n: float | None, is_ratio: bool = False) -> str:
    """Format as percentage or ratio."""
    if n is None:
        return "N/A"
    if is_ratio:
        return f"{n:.2f}"
    return f"{n * 100:.2f}%" if n < 1 else f"{n:.2f}%"


def get_recommendation_color(rec: str) -> str:
    """Map recommendation to hex color."""
    colors = {
        "STRONG_BUY": "#00C853",
        "BUY": "#69F0AE",
        "HOLD": "#FFD600",
        "SELL": "#FF5252",
        "STRONG_SELL": "#D50000",
    }
    return colors.get(rec, "#9E9E9E")


def display_metrics_sidebar(metrics: FinancialMetrics, headlines: list) -> None:
    """Render financial metrics and headlines in sidebar."""
    st.sidebar.header("📊 Financial Metrics")
    
    st.sidebar.metric("Company", metrics.company_name)
    st.sidebar.metric("Current Price", f"${metrics.current_price:,.2f}")
    st.sidebar.metric("Market Cap", format_large_number(metrics.market_cap))
    
    st.sidebar.divider()
    st.sidebar.subheader("Valuation")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("P/E (TTM)", format_percent(metrics.pe_ratio, is_ratio=True))
    col2.metric("Forward P/E", format_percent(metrics.forward_pe, is_ratio=True))
    col1.metric("P/B Ratio", format_percent(metrics.price_to_book, is_ratio=True))
    col2.metric("D/E Ratio", format_percent(metrics.debt_to_equity, is_ratio=True))
    
    st.sidebar.divider()
    st.sidebar.subheader("Cash & Yield")
    st.sidebar.metric("Free Cash Flow", format_large_number(metrics.free_cash_flow))
    st.sidebar.metric("Dividend Yield", format_percent(metrics.dividend_yield))
    
    st.sidebar.divider()
    st.sidebar.subheader("52-Week Range")
    low = metrics.fifty_two_week_low
    high = metrics.fifty_two_week_high
    if low and high:
        st.sidebar.write(f"${low:,.2f} — ${high:,.2f}")
        # Position indicator
        if high > low:
            position = (metrics.current_price - low) / (high - low)
            st.sidebar.progress(min(max(position, 0), 1))
    else:
        st.sidebar.write("N/A")
    
    st.sidebar.divider()
    st.sidebar.subheader("Classification")
    st.sidebar.write(f"**Sector:** {metrics.sector or 'N/A'}")
    st.sidebar.write(f"**Industry:** {metrics.industry or 'N/A'}")
    
    # Headlines section
    st.sidebar.divider()
    st.sidebar.header("📰 Recent Headlines")
    if headlines:
        for h in headlines:
            if h.link:
                st.sidebar.markdown(f"- [{h.title}]({h.link}) *({h.publisher})*")
            else:
                st.sidebar.markdown(f"- {h.title} *({h.publisher})*")
    else:
        st.sidebar.write("No headlines available")


def display_memo(memo: AnalystMemo, emoji: str, label: str) -> None:
    """Render an analyst memo in an expander."""
    with st.expander(f"{emoji} {label} (Confidence: {memo.confidence_in_thesis:.0%})"):
        st.markdown(f"**Summary:** {memo.summary}")
        
        st.markdown("**Key Points:**")
        for point in memo.key_points:
            st.markdown(f"- {point}")
        
        st.markdown(f"**Risk/Reward Assessment:** {memo.risk_reward_assessment}")


def display_results(result: FinalRecommendation) -> None:
    """Render the final recommendation and all details."""
    # Large colored recommendation badge
    color = get_recommendation_color(result.recommendation)
    st.markdown(
        f"""
        <div style="
            background-color: {color};
            color: {'white' if result.recommendation in ('STRONG_SELL', 'SELL', 'STRONG_BUY') else 'black'};
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            text-align: center;
            font-size: 2rem;
            font-weight: bold;
            margin: 1rem 0;
        ">
            {result.recommendation.replace('_', ' ')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Confidence score
    st.subheader("Confidence Score")
    st.progress(result.confidence_score, text=f"{result.confidence_score:.0%}")
    
    # Synthesis summary
    st.subheader("Synthesis Summary")
    st.write(result.synthesis_summary)
    
    # Key caveats
    st.subheader("⚠️ Key Caveats")
    st.markdown("*Items you must verify independently:*")
    for caveat in result.key_caveats:
        st.markdown(f"- ⚠️ {caveat}")
    
    st.divider()
    
    # Analyst memos
    st.subheader("Analyst Memos")
    display_memo(result.bear_memo, "🐻", "Bear Case (Munger)")
    display_memo(result.bull_memo, "🐂", "Bull Case (Buffett)")


# --- Main App ---

st.set_page_config(
    page_title="Munger-Buffett Analyst",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Munger-Buffett Analyst Swarm")
st.markdown("*Synthesizing bear (Munger) and bull (Buffett) perspectives into a balanced investment thesis.*")

st.divider()

# Input section
ticker = st.text_input(
    "Enter Stock Ticker",
    placeholder="e.g., AAPL, MSFT, MSTR",
    max_chars=10,
).strip().upper()

analyze_clicked = st.button("🔍 Analyze", type="primary", disabled=not ticker)

if analyze_clicked and ticker:
    try:
        with st.status(f"Analyzing {ticker}...", expanded=True) as status:
            # Step 1: Scout
            status.update(label=f"Fetching data for {ticker}...")
            report = fetch_scout_report(ticker)
            st.write(f"✅ Retrieved data for **{report.metrics.company_name}**")
            
            # Step 2: Bear memo
            status.update(label="Generating Bear memo (Munger)...")
            bear_memo = generate_bear_memo(report)
            st.write(f"✅ Bear analysis complete (confidence: {bear_memo.confidence_in_thesis:.0%})")
            
            # Step 3: Bull memo
            status.update(label="Generating Bull memo (Buffett)...")
            bull_memo = generate_bull_memo(report)
            st.write(f"✅ Bull analysis complete (confidence: {bull_memo.confidence_in_thesis:.0%})")
            
            # Step 4: Synthesize
            status.update(label="Synthesizing recommendations...")
            final = synthesize(bull_memo, bear_memo, report.metrics)
            st.write(f"✅ Synthesis complete: **{final.recommendation}**")
            
            status.update(label="Analysis complete!", state="complete", expanded=False)
        
        # Display sidebar with metrics
        display_metrics_sidebar(report.metrics, report.headlines)
        
        # Display main results
        display_results(final)
        
    except ValueError as e:
        st.error(f"❌ Invalid ticker or data unavailable: {e}")
    except RuntimeError as e:
        st.error(f"❌ Analysis failed: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
