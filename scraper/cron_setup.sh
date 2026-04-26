#!/bin/bash
# Sets up a daily cron job to run the scraper at 8PM.
# Usage: bash scraper/cron_setup.sh

# Get the absolute path of the project folder
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The cron line: 8PM every day
CRON_LINE="0 20 * * * cd \"$PROJECT_DIR\" && python3 scraper/scraper.py >> scraper/scraper.log 2>&1"

echo ""
echo "  Project folder detected: $PROJECT_DIR"
echo ""
echo "  Adding cron job: run scraper daily at 8:00 PM"

# Add to crontab (safe — only adds if not already there)
( crontab -l 2>/dev/null | grep -v "scraper/scraper.py" ; echo "$CRON_LINE" ) | crontab -

echo ""
echo "  ✓ Cron job added!"
echo ""
echo "  ── Verify it's set ──────────────────────────────────"
echo "  Run: crontab -l"
echo ""
echo "  ── To remove it later ───────────────────────────────"
echo "  Run: crontab -e  (then delete the scraper line)"
echo ""
echo "  ── To test the scraper manually right now ───────────"
echo "  Run: python3 scraper/scraper.py"
echo ""
echo "  ── Scraper log (after first run) ────────────────────"
echo "  Run: tail -f scraper/scraper.log"
echo ""
