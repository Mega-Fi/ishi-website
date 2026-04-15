#!/usr/bin/env bash
# Demo walkthrough for the Hacker News scraper test task.
# Run from the project root with the virtual environment activated:
#   source .venv/bin/activate && ./demo.sh

set -u

GREEN='\033[1;32m'
DIM='\033[2m'
RESET='\033[0m'

trap 'printf "\n\n%bdemo ended%b\n" "$GREEN" "$RESET"; exit 0' INT

step() {
    local title="$1"
    local blurb="$2"
    local cmd="$3"

    printf "\n\n"
    printf "%b────────────────────────────────────────────────────────%b\n" "$GREEN" "$RESET"
    printf "%b  %s%b\n" "$GREEN" "$title" "$RESET"
    printf "%b────────────────────────────────────────────────────────%b\n" "$GREEN" "$RESET"
    printf "  %s\n" "$blurb"
    printf "  %b\$ %s%b\n" "$DIM" "$cmd" "$RESET"
    read -r -p "  » press Enter to run "
    printf "\n"
    eval "$cmd"
}

clear

printf "%bHacker News Scraper — Demo%b\n" "$GREEN" "$RESET"
printf "Each step pauses for Enter. Ctrl+C to exit cleanly.\n"

# Shot 0: clean slate
rm -f test_automation.db

step "1. Clean slate" \
     "No database yet. First run should save ten fresh articles." \
     "ls test_automation.db 2>/dev/null || echo 'no DB — clean slate'"

step "2. First run — scrape and persist" \
     "Headless Chromium, extract top 10, insert into SQLite." \
     "python -m src.main"

step "3. Second run — deduplication" \
     "UNIQUE(url) + INSERT OR IGNORE. All ten should be skipped." \
     "python -m src.main"

step "3b. Schema — UNIQUE constraint and index" \
     "Dedup is enforced at the schema level, not in application code." \
     "sqlite3 test_automation.db '.schema articles'"

step "4. Stored rows — full titles and URLs" \
     "Ten articles, each with its absolute URL persisted for dedup." \
     "sqlite3 test_automation.db \"SELECT printf('%2d. %s' || char(10) || '    %s', id, title, url) FROM articles ORDER BY id;\""

step "4b. Timestamps" \
     "created_at populated by the schema default on insert." \
     "sqlite3 -header -column test_automation.db \"SELECT id, created_at FROM articles ORDER BY id;\""

step "5. Parameterized queries — SQL safety" \
     "Injection payload stored as data, articles table intact." \
     "pytest tests/test_db.py::TestSaveArticle::test_resists_sql_injection_via_parameterized_queries -v"

step "6. Full test suite" \
     "28 tests across models, db, and URL normalization." \
     "pytest -v"

step "7. Module layout" \
     "models / scraper / db / main. Clean separation of concerns." \
     "ls src/"

step "8. Resource management — no orphan Chromium" \
     "Run and interrupt mid-scrape; AsyncExitStack still tears down." \
     "(python -m src.main & sleep 1; kill -INT \$!; wait) 2>/dev/null; sleep 1; (pgrep -fl -i chromium || echo 'no orphan Chromium processes')"

printf "\n\n%bDemo complete%b\n\n" "$GREEN" "$RESET"
