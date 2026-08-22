"""
WAQI vs Model Arbitration (Groq)
===================================
Be honest about what this does: an LLM cannot independently *measure* air
quality, so it can't "know" which of the two numbers is objectively
correct. What it CAN usefully do is a plausibility/sanity-check -- look at
both readings alongside context (recent trend, pollutant concentrations,
each source's known error characteristics, time of day/season) and judge
which one is more internally consistent, the way a human analyst
double-checking two instruments would. Its output is a reasoned judgment,
not verified ground truth -- treat it as a second opinion, not an oracle.

To keep this cheap and fast, arbitration only runs when the two sources
actually disagree by more than ARBITRATION_THRESHOLD. When they roughly
agree, there's nothing to arbitrate -- WAQI (real ground-station data) is
used directly, no API call needed.

Results are cached per city for CACHE_TTL_SECONDS -- the frontend polls
every ~60s and the underlying live data doesn't change nearly that fast,
so re-arbitrating every poll just burns rate limit for no new signal.

If GROQ_API_KEY isn't set, or the call fails for any reason, this fails
SAFE: it defaults to WAQI (ground-station reading) and reports that
arbitration didn't run, rather than blocking the request or guessing.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

ARBITRATION_THRESHOLD = 0.15  # only arbitrate if readings differ by >15%

_arbitration_cache = {}  # {city: (cached_at_timestamp, result_dict)}
CACHE_TTL_SECONDS = 300  # 5 minutes


def is_configured() -> bool:
    return bool(GROQ_API_KEY)


def needs_arbitration(waqi_aqi: float, model_aqi: float) -> bool:
    if waqi_aqi is None or model_aqi is None:
        return False
    baseline = max(waqi_aqi, 1.0)
    return abs(waqi_aqi - model_aqi) / baseline > ARBITRATION_THRESHOLD


def arbitrate(city: str, waqi_aqi: float, waqi_category: str, model_aqi: float,
              model_category: str, pollutants: dict, nowcast_mae: float,
              recent_trend: list) -> dict:
    """Returns:
        {
          "chosen": "waqi" | "model",
          "final_aqi": float,
          "final_category": str,
          "reasoning": str,
          "arbitrated": bool,   # False if Groq wasn't called/failed
        }
    """
    now = time.time()
    cached = _arbitration_cache.get(city)
    if cached and (now - cached[0]) < CACHE_TTL_SECONDS:
        return cached[1]

    fallback = {
        "chosen": "waqi", "final_aqi": waqi_aqi, "final_category": waqi_category,
        "reasoning": "Arbitration not run (Groq not configured or call failed) -- "
                     "defaulted to WAQI ground-station reading.",
        "arbitrated": False,
    }

    if not is_configured():
        _arbitration_cache[city] = (now, fallback)
        return fallback

    prompt = f"""You are sanity-checking two Air Quality Index readings for {city}, Delhi NCR, that disagree with each other. You cannot take a real measurement yourself -- judge plausibility only from the data given.

Reading A (WAQI ground-station, real CPCB monitor): AQI={waqi_aqi}, category={waqi_category}
Reading B (trained ML nowcast model from live pollutant concentrations): AQI={model_aqi}, category={model_category}
  - Model's historical validation MAE on held-out data: {nowcast_mae}

Live pollutant concentrations used by the model (from OpenWeatherMap): {json.dumps(pollutants)}

Recent AQI trend for this city (oldest to newest, may be empty if data is still being collected): {recent_trend}

Consider: does reading B's pollutant mix plausibly produce reading B's AQI value? Is either reading a big jump from the recent trend with no obvious explanation? Ground-station readings (A) are generally more trustworthy when available and not clearly anomalous, since they measure actual air rather than inferring it. Note known limitations honestly if relevant: e.g. OWM pollutant sensors can occasionally return implausible values.

Respond with ONLY valid JSON, no other text:
{{"chosen": "waqi" or "model", "reasoning": "one or two plain sentences explaining why"}}"""

    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_completion_tokens": 200,
            },
            timeout=8,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(content)
        chosen = parsed.get("chosen", "waqi")
        reasoning = parsed.get("reasoning", "")
    except Exception as e:
        fallback["reasoning"] = f"Arbitration not run (Groq call failed: {e}) -- defaulted to WAQI."
        _arbitration_cache[city] = (now, fallback)
        return fallback

    if chosen == "model":
        result = {
            "chosen": "model", "final_aqi": model_aqi, "final_category": model_category,
            "reasoning": reasoning, "arbitrated": True,
        }
    else:
        result = {
            "chosen": "waqi", "final_aqi": waqi_aqi, "final_category": waqi_category,
            "reasoning": reasoning, "arbitrated": True,
        }

    _arbitration_cache[city] = (now, result)
    return result