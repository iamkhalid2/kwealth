"""Munger & Buffett Analyst Agents: Generate perspective-specific memos using LLM."""

from typing import Literal

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from agents.schemas import AnalystMemo, ScoutReport


# System prompts for each persona
MUNGER_SYSTEM_PROMPT = """You are Charlie Munger, legendary investor known for inversion thinking.
Analyze the following stock data with EXTREME SKEPTICISM.
Focus on: hidden risks, excessive debt, accounting red flags, competitive threats, management incompetence, crypto/fad exposure.
Do NOT sugarcoat. Find what could go wrong."""

BUFFETT_SYSTEM_PROMPT = """You are Warren Buffett, the Oracle of Omaha.
Analyze the following stock data with a focus on LONG-TERM VALUE.
Focus on: durable competitive advantages (moats), brand power, pricing power, compounding potential, management quality, margin of safety.
Be realistic but identify genuine strengths."""


def _generate_memo(
    report: ScoutReport,
    perspective: Literal["bear", "bull"],
    system_prompt: str,
) -> AnalystMemo:
    """
    Internal helper to generate an analyst memo using Gemini.

    Args:
        report: ScoutReport with financial metrics and news
        perspective: "bear" or "bull"
        system_prompt: Persona-specific system prompt

    Returns:
        AnalystMemo with the LLM's analysis

    Raises:
        RuntimeError: If LLM call fails or returns invalid response
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    user_prompt = f"""Analyze this stock and produce your investment memo.

STOCK DATA:
{report.model_dump_json(indent=2)}

Respond with a JSON object containing:
- summary: 3-4 sentence summary (max 500 chars)
- key_points: list of 3-5 bullet points
- risk_reward_assessment: your risk/reward analysis (max 300 chars)
- confidence_in_thesis: float between 0.0 and 1.0"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part(text=system_prompt)]),
                types.Content(role="model", parts=[types.Part(text="I understand. I will analyze the stock data you provide with my perspective and return a structured JSON memo.")]),
                types.Content(role="user", parts=[types.Part(text=user_prompt)]),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalystMemo,
                temperature=0.7,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    if response.parsed is None:
        raise RuntimeError(f"Gemini returned invalid response for {perspective} memo")

    memo: AnalystMemo = response.parsed

    # Override perspective and ticker to ensure correctness (don't trust LLM)
    memo.perspective = perspective
    memo.ticker = report.metrics.ticker

    return memo


def generate_bear_memo(report: ScoutReport) -> AnalystMemo:
    """
    Generate a bearish (Munger-style) investment memo.

    Args:
        report: ScoutReport with financial metrics and news

    Returns:
        AnalystMemo with perspective="bear"
    """
    return _generate_memo(report, "bear", MUNGER_SYSTEM_PROMPT)


def generate_bull_memo(report: ScoutReport) -> AnalystMemo:
    """
    Generate a bullish (Buffett-style) investment memo.

    Args:
        report: ScoutReport with financial metrics and news

    Returns:
        AnalystMemo with perspective="bull"
    """
    return _generate_memo(report, "bull", BUFFETT_SYSTEM_PROMPT)
