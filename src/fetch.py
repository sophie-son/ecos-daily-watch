"""
fetch.py

Pulls the day's USD/KRW rate, KOSPI index, and 3-year treasury yield
from the Bank of Korea ECOS "KeyStatisticList" (100 key indicators)
endpoint.

No table/item codes needed -- this single endpoint returns ~100 major
economic indicators by name, and our 3 target metrics are always in
it, updated daily. Confirmed by manual test call against the live API.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error

TARGET_METRICS = {
    "원/달러 환율(종가)": {"label": "USD/KRW", "unit": "원"},
    "코스피지수": {"label": "KOSPI", "unit": "pt"},
    "국고채수익률(3년)": {"label": "3Y Treasury Yield", "unit": "%"},
}


def fetch_key_stats(api_key: str, max_retries: int = 3, timeout: int = 30) -> list[dict]:
    url = f"http://ecos.bok.or.kr/api/KeyStatisticList/{api_key}/json/kr/1/100"

    raw = None
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            last_error = None
            break
        except urllib.error.URLError as e:
            last_error = e
            print(f"ECOS request attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(5)

    if raw is None:
        raise RuntimeError(
            f"ECOS request failed after {max_retries} attempts: {last_error}"
        ) from last_error

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"ECOS returned non-JSON response: {raw[:200]}") from e

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
                value = raw_value

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