# ECOS Daily Watch

A small, zero-dependency automation that checks three Korean economic
indicators every day and posts a summary to Discord — so I don't have
to manually check a website and copy numbers into a spreadsheet.

**Tracked daily:**
- USD/KRW exchange rate (원/달러 환율)
- KOSPI index (코스피지수)
- 3-year Korean treasury bond yield (국고채수익률 3년)

## Why I built this

I do a version of this check by hand at work every day, for production
monitoring on a computer-vision analytics platform: pull the day's
numbers, compare them to what "normal" looks like, and flag anything
that needs a closer look. This project is a public, self-contained
version of that same pattern — same shape, public data, so I can share
the actual code and keep iterating on it in the open.

## How it works

```
GitHub Actions (daily cron)
        │
        ▼
   main.py
        │
        ├──► src/fetch.py   → calls the Bank of Korea's ECOS Open API
        │                      (KeyStatisticList endpoint)
        │
        └──► src/notify.py  → posts a formatted summary to a
                               Discord webhook
```

No server, no database, no always-on process. GitHub Actions wakes up
once a day, runs the script, and shuts down. The only external
dependency is the Python standard library — no `pip install` step.

## Data source

[Bank of Korea ECOS Open API](https://ecos.bok.or.kr) — the central
bank's official, free, public statistics API. Using an official API
instead of scraping a page avoids any question about redistribution
rights, and it's simply more reliable than parsing HTML.

## Setup (if you want to run your own copy)

1. Get a free ECOS API key at ecos.bok.or.kr (OpenAPI menu → 인증키 신청).
2. Create a Discord server and add a webhook to a channel
   (channel settings → Integrations → Webhooks).
3. In your fork's repo settings, add two secrets:
   - `ECOS_API_KEY`
   - `DISCORD_WEBHOOK_URL`
4. The workflow in `.github/workflows/daily_check.yml` runs
   automatically once a day. You can also trigger it manually from
   the Actions tab (`workflow_dispatch`).

## Roadmap

- [x] Fetch + notify pipeline (this version)
- [ ] Store daily history in-repo for trend comparison
- [ ] Flag values that deviate meaningfully from recent norms,
      instead of just reporting raw numbers
