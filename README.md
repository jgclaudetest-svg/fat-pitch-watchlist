# Fat pitch watchlist

A small site that tracks a list of public companies on two questions: is the price inside a range that would make it a bargain, and is the business still healthy.

General research, not investment advice. Ranges, thresholds and return assumptions are judgment calls and are not backtested.

- `docs/` is the published site. `docs/data.json` is refreshed by a scheduled job.
- `model/build_data.py` pulls prices and quarterly financials from Yahoo Finance and merges the per-company settings. `--prices` refreshes prices only.
- `notes/research/` holds dated research notes and red-flag checks that the page displays.
- `src/template.html` is the page source; `python3 src/site.py` builds `docs/index.html`.
