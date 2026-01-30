"""Synthesizer Agent: Merge bear and bull memos into a final recommendation."""

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from agents.schemas import (
    AnalystMemo,
    FinancialMetrics,
    FinalRecommendation,
    SynthesizerOutput,
)


SYNTHESIZER_SYSTEM_PROMPT = """You are a senior investment committee synthesizing two analyst reports.
Your job is to weigh both perspectives and produce a balanced final recommendation.

CRITICAL INSTRUCTIONS:
- Weight the stronger argument. If evidence strongly favors one side, commit to BUY/SELL.
- Do NOT default to "HOLD" without clear justification—this is lazy analysis.
- STRONG_BUY/STRONG_SELL require high confidence and clear evidence.
- Identify 3-5 specific caveats the investor must verify independently."""


def synthesize(
    bull: AnalystMemo,
    bear: AnalystMemo,
    metrics: FinancialMetrics,
) -> FinalRecommendation:
    """
    Synthesize bull and bear memos into a final recommendation.

    Args:
        bull: Bullish (Buffett-style) memo
        bear: Bearish (Munger-style) memo
        metrics: Current financial metrics

    Returns:
        FinalRecommendation with balanced analysis

    Raises:
        RuntimeError: If LLM call fails or returns invalid response
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    user_prompt = f"""Synthesize these two analyst reports and produce your final recommendation.

BULL MEMO (Buffett perspective):
{bull.model_dump_json(indent=2)}

BEAR MEMO (Munger perspective):
{bear.model_dump_json(indent=2)}

CURRENT METRICS:
{metrics.model_dump_json(indent=2)}

Respond with a JSON object containing:
- ticker: the stock ticker
- recommendation: one of "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
- confidence_score: float between 0.0 and 1.0 (NOT a simple average—reason about which thesis is stronger)
- synthesis_summary: balanced summary weighing both perspectives (max 600 chars)
- key_caveats: list of 3-5 specific things the investor must verify independently"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part(text=SYNTHESIZER_SYSTEM_PROMPT)]),
                types.Content(role="model", parts=[types.Part(text="I understand. I will carefully weigh both analyst perspectives and produce a balanced final recommendation with specific caveats.")]),
                types.Content(role="user", parts=[types.Part(text=user_prompt)]),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SynthesizerOutput,
                temperature=0.7,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed during synthesis: {e}") from e

    if response.parsed is None:
        raise RuntimeError("Gemini returned invalid response for synthesis")

    synth_output: SynthesizerOutput = response.parsed

    # Compose full FinalRecommendation with original memos attached
    return FinalRecommendation(
        ticker=synth_output.ticker,
        recommendation=synth_output.recommendation,
        confidence_score=synth_output.confidence_score,
        synthesis_summary=synth_output.synthesis_summary,
        key_caveats=synth_output.key_caveats,
        bull_memo=bull,
        bear_memo=bear,
    )
