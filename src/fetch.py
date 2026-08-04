"""
fetch.py

Pulls the day's USD/KRW rate, KOSPI index, and 3-year treasury yield
from the Bank of Korea ECOS "KeyStatisticList" (100 key indicators)
endpoint.

No table/item codes needed -- this single endpoint returns ~100 major
economic indicators by name, and our 3 target metrics are always in
it, updated daily. Confirmed by manual test call against the live API.
"""

import json
import urllib.request
import urllib.error

# Exact KEYSTAT_NAME strings as returned by ECOS -- confirmed by test call.
# "unit" here is what we display -- NOT always the same as ECOS's raw
# UNIT_NAME field. For index-type metrics like KOSPI, ECOS's UNIT_NAME
# is actually the index's base-year definition (e.g. "1980.01.04=100"),
# not a real display unit, so we override it with something sensible.
TARGET_METRICS = {
    "원/달러 환율(종가)": {"label": "USD/KRW", "unit": "원"},
    "코스피지수": {"label": "KOSPI", "unit": "pt"},
    "국고채수익률(3년)": {"label": "3Y Treasury Yield", "unit": "%"},
}


def fetch_key_stats(api_key: str) -> list[dict]:
    """
    Calls ECOS and returns a list of dicts, one per target metric:
        {"name_kr": ..., "label": ..., "value": ..., "unit": ..., "date": ...}

    Raises RuntimeError on API errors, network failures, or if a
    target metric is missing from the response (e.g. ECOS renamed
    a field -- fail loudly rather than silently posting incomplete data).
    """
    url = f"http://ecos.bok.or.kr/api/KeyStatisticList/{api_key}/json/kr/1/100"

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise RuntimeError(f"ECOS request failed: {e}") from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"ECOS returned non-JSON response: {raw[:200]}") from e

    # ECOS reports errors inside a "RESULT" key instead of an HTTP error code
    if "RESULT" in data:
        raise RuntimeError(f"ECOS API error: {data['RESULT']}")

    if "KeyStatisticList" not in data:
        raise RuntimeError(f"Unexpected ECOS response shape: {list(data.keys())}")

    rows = data["KeyStatisticList"]["row"]

    results = []
    found_names = set()
    for row in rows:
        name = row.get("KEYSTAT_NAME")
        if name in TARGET_METRICS:
            meta = TARGET_METRICS[name]
            raw_value = row.get("DATA_VALUE")
            try:
                value = round(float(raw_value), 2)
            except (TypeError, ValueError):
                value = raw_value  # fall back to the raw string if it's ever non-numeric

            results.append({
                "name_kr": name,
                "label": meta["label"],
                "value": value,
                "unit": meta["unit"],
                "date": row.get("CYCLE"),
            })
            found_names.add(name)

    missing = set(TARGET_METRICS) - found_names
    if missing:
        raise RuntimeError(f"Expected metrics not found in ECOS response: {missing}")

    return results
