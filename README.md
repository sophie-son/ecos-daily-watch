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

## Debugging notes

Real problems hit while building this — kept here because "handled a production
integration issue" is a better portfolio line than "followed a tutorial."

### Duplicate daily messages

**Symptom:** Two Discord messages arrived on the same day with identical data
(Aug 5, 2026).

**Cause:** Two independent triggers were live on the workflow at once —
GitHub's native `schedule:` cron in the workflow file, and an external
cron-job.org job calling the same workflow's `workflow_dispatch` endpoint.
Each fired once a day, with no awareness of the other.

**Diagnosis:** GitHub's Actions run history showed the two runs with
different trigger types — one `workflow_dispatch` (cron-job.org, on time at
8:00 AM), one `schedule` (GitHub's own cron, 53 minutes late) — confirming
two separate trigger paths rather than one trigger misfiring twice.

**Fix:** Removed the `schedule:` block from `daily_check.yml`, leaving
`workflow_dispatch` as the only trigger. cron-job.org is now the sole
scheduler, chosen over GitHub's native cron because GitHub's schedule
trigger is documented to run late under platform load (confirmed here
directly) and silently disables itself after 60 days without a repo commit.

### TabError: mixed tabs and spaces in indentation

**Symptom:** A run failed immediately (no output produced) with
`TabError: inconsistent use of tabs and spaces in indentation`. No Discord
alert was sent -- this is a syntax-level failure, meaning the file never
even finishes parsing, so none of the script's own error-handling code
gets a chance to run.

**Cause:** A manual edit to `main.py` (adding the history-logging call) was
made in a plain text editor, which inserted a tab character where the rest
of the file used spaces.

**Fix:** Rewrote `main.py` with fully consistent, space-only indentation.

**Separately:** noticed the error handling only caught `RuntimeError`
specifically, which would miss other exception types. Broadened it to catch
any exception, so future *runtime* failures (distinct from parse-time ones
like this) are more reliably reported to Discord.

### ECOS request timing out on GitHub's runner

**Symptom:** A run failed with `urlopen error timed out` after a 15-second
wait on the ECOS API call.

**Cause:** ECOS is occasionally slow to respond, especially from GitHub's
hosted runners. An existing open-source ECOS API client corroborates this --
it defaults to a 60-second timeout with 5 retries, suggesting this is a
known characteristic of the API rather than a one-off.

**Fix:** Increased the timeout to 30 seconds and added automatic retries
(up to 3 attempts, 5 seconds apart) before giving up.

**Verified:** Confirmed via `gh run list` that a subsequent run succeeded,
and confirmed `data/history.csv` still had only one row for the day despite
three runs happening that same day -- evidence that the existing
duplicate-date check in `history.py` correctly prevented bad data even
while debugging live.


## Roadmap

- [x] Fetch + notify pipeline (this version)
- [x] Store daily history in-repo for trend comparison
- [ ] Flag values that deviate meaningfully from recent norms,
      instead of just reporting raw numbers
