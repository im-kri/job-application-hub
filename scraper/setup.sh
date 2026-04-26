#!/bin/bash
# First-time setup — run once from the project root folder.
# Usage: bash scraper/setup.sh

set -e

echo ""
echo "  Installing Python dependencies..."
pip3 install -r scraper/requirements.txt

echo ""
echo "  Installing Playwright browsers (Chromium)..."
python3 -m playwright install chromium

echo ""
echo "  ✓ Setup complete!"
echo ""
echo "  ── How to use ──────────────────────────────────────"
echo "  Run the scraper now:    python3 scraper/scraper.py"
echo "  Start local server:     python3 scraper/server.py"
echo "  Then open:              http://localhost:8080"
echo "  ────────────────────────────────────────────────────"
echo ""
