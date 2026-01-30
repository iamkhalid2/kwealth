from pydantic import BaseModel, Field
from typing import Literal


class FinancialMetrics(BaseModel):
    """Core financial data from yfinance."""

    ticker: str
    company_name: str
    current_price: float
    pe_ratio: float | None = Field(default=None, description="Trailing P/E")
    forward_pe: float | None = None
    price_to_book: float | None = None
    debt_to_equity: float | None = None
    free_cash_flow: float | None = Field(default=None, description="In USD")
    market_cap: float | None = None
    dividend_yield: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    sector: str | None = None
    industry: str | None = None


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


class SynthesizerOutput(BaseModel):
    """LLM output for Synthesizer (without nested memos)."""

    ticker: str
    recommendation: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    synthesis_summary: str = Field(max_length=600)
    key_caveats: list[str] = Field(min_length=1, max_length=5)


class FinalRecommendation(BaseModel):
    """Output of Synthesizer."""

    ticker: str
    recommendation: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    synthesis_summary: str = Field(max_length=600)
    key_caveats: list[str] = Field(min_length=1, max_length=5)
    bull_memo: AnalystMemo
    bear_memo: AnalystMemo
