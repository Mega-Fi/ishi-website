# Hacker News Scraper

A Python script that extracts the top 10 Hacker News articles with headless Playwright, persists them to a local SQLite database, and skips articles already saved in prior runs.

## Requirements

- Python 3.11+
- macOS, Linux, or Windows

## Setup

Confirm the Python version first:

```bash
python3 --version   # must be 3.11 or newer
```

Then create the virtual environment, install dependencies, and fetch the headless browser (Playwright downloads roughly 140 MB of Chromium on the first run):

macOS and Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Run

Activate the virtual environment first if the shell is new (`source .venv/bin/activate` on macOS or Linux, `.venv\Scripts\activate` on Windows), then:

```bash
python -m src.main
```

Expected output on first run:

```
10 items saved, 0 items skipped due to existing state.
```

Re-running without clearing the database:

```
0 items saved, 10 items skipped due to existing state.
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Covers the `Article` domain model, the SQLite connection context manager (commit, rollback, close), schema creation, dedup semantics at both the `UNIQUE` constraint and `INSERT OR IGNORE` layers, parameterized-query safety against injection payloads, and URL normalization.

## Artifacts

- `test_automation.db` — SQLite database, created in the working directory on first run. Delete it to reset state.

Inspect the stored rows:

```bash
sqlite3 test_automation.db "SELECT id, title, url, created_at FROM articles ORDER BY id;"
sqlite3 test_automation.db ".schema articles"
```

## Layout

```
src/
  models.py     Article dataclass (frozen, immutable domain model)
  scraper.py    Async Playwright extraction, AsyncExitStack teardown
  db.py         SQLite connection context manager, schema, parameterized insert
  main.py       Orchestration and CLI entrypoint
```

## Design Notes

- **Resource management**: `AsyncExitStack` in the scraper and `@contextmanager` in the db module guarantee page, context, browser, Playwright runtime, and SQLite connection are released in reverse order on any exit path (success, exception, or SIGINT).
- **Deduplication**: `UNIQUE(url)` constraint with `INSERT OR IGNORE` handles dedup atomically at the schema level, avoiding the race window of a separate `SELECT` then `INSERT`.
- **SQL safety**: All queries use `?` parameter placeholders. No string formatting into SQL.
- **URL normalization**: Relative HN links (for example `item?id=...`) are resolved against the base URL before storage so dedup works across runs.
