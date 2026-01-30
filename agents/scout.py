"""Scout Agent: fetches raw financial data and news headlines."""

from datetime import datetime

import yfinance as yf

from config import MAX_HEADLINES
from agents.schemas import FinancialMetrics, NewsHeadline, ScoutReport


def fetch_scout_report(ticker: str) -> ScoutReport:
    """
    Fetch financial metrics and news headlines for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")

    Returns:
        ScoutReport with metrics and headlines

    Raises:
        ValueError: If ticker is invalid or essential data is missing
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    # Validate we got real data (yfinance returns empty dict for invalid tickers)
    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        raise ValueError(f"Invalid ticker or no data available for: {ticker}")

    # Price fallback chain: currentPrice -> regularMarketPrice
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    if current_price is None:
        raise ValueError(f"Could not determine current price for: {ticker}")

    # Build FinancialMetrics with graceful None handling
    # Note: yfinance returns debt_to_equity as a percentage (e.g., 152.411 = 152.411%)
    # Convert to actual ratio by dividing by 100
    debt_to_equity_raw = info.get("debtToEquity")
    debt_to_equity = debt_to_equity_raw / 100 if debt_to_equity_raw is not None else None
    
    metrics = FinancialMetrics(
        ticker=ticker.upper(),
        company_name=info.get("longName") or info.get("shortName") or ticker.upper(),
        current_price=current_price,
        pe_ratio=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        price_to_book=info.get("priceToBook"),
        debt_to_equity=debt_to_equity,
        free_cash_flow=info.get("freeCashflow"),  # Note: lowercase 'f' in yfinance
        market_cap=info.get("marketCap"),
        dividend_yield=info.get("dividendYield"),
        fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
        fifty_two_week_low=info.get("fiftyTwoWeekLow"),
        sector=info.get("sector"),
        industry=info.get("industry"),
    )

    # Fetch news headlines (may be empty list)
    raw_news = stock.news or []
    headlines = [
        NewsHeadline(
            title=item.get("title", ""),
            publisher=item.get("publisher", ""),
            link=item.get("link"),
        )
        for item in raw_news[:MAX_HEADLINES]
        if item.get("title")  # Skip items without titles
    ]

    return ScoutReport(
        metrics=metrics,
        headlines=headlines,
        fetch_timestamp=datetime.now().isoformat(),
    )
