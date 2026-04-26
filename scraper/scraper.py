"""
Job Scraper — Imam Fikri's Remote Job Hunter
Scrapes Glints and Jobstreet for KOL / Community / PM / Partnerships roles.
Runs daily at 8PM via cron. Outputs scraped_jobs.json to the parent folder.

Usage:
  python3 scraper/scraper.py
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ── Configuration ─────────────────────────────────────────────────────────────

OUTPUT_FILE = Path(__file__).parent.parent / "scraped_jobs.json"

KEYWORDS = [
    "KOL Manager",
    "Influencer Marketing Manager",
    "Community Manager",
    "Community Engagement",
    "Digital Partnerships",
    "Partnership Manager",
    "Project Manager digital",
]

# Map keywords → role type for the Command Center
ROLE_MAP = {
    "kol":          ["kol manager", "influencer marketing", "kol specialist", "creator partnerships"],
    "community":    ["community manager", "community engagement", "community ops"],
    "partnerships": ["partnership manager", "digital partnerships", "business partnerships", "bd manager"],
    "pm":           ["project manager", "program manager", "digital project"],
}

LOCATIONS = ["Indonesia", "Remote"]

# Portals to scrape
PORTALS = ["glints", "jobstreet", "kalibrr"]

# ── Role classifier ────────────────────────────────────────────────────────────

def classify_role(title: str) -> str:
    title_lower = title.lower()
    for role, keywords in ROLE_MAP.items():
        if any(k in title_lower for k in keywords):
            return role
    return "pm"  # default fallback

# ── Deduplication ─────────────────────────────────────────────────────────────

def dedupe(jobs: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for job in jobs:
        key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
        if key not in seen:
            seen.add(key)
            result.append(job)
    return result

# ── Glints scraper ─────────────────────────────────────────────────────────────

async def scrape_glints(page, keyword: str) -> list[dict]:
    jobs = []
    url = f"https://glints.com/id/opportunities/jobs/explore?keyword={keyword.replace(' ', '%20')}&countryCode=ID"

    print(f"  [Glints] Searching: {keyword}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for job cards — Glints uses a data-cy attribute
        await page.wait_for_selector(
            '[data-cy="job-card"], .JobCardsc__JobcardContainer, [class*="JobCard"]',
            timeout=15000
        )
        await asyncio.sleep(2)  # let lazy-loaded content settle

        cards = await page.query_selector_all(
            '[data-cy="job-card"], .JobCardsc__JobcardContainer, [class*="JobCard"]'
        )

        for card in cards[:15]:  # cap at 15 per keyword
            try:
                # Title — try multiple selectors
                title_el = await card.query_selector(
                    '[data-cy="job-title"], [class*="JobTitle"], h3, h2'
                )
                title = (await title_el.inner_text()).strip() if title_el else ""

                # Company
                company_el = await card.query_selector(
                    '[data-cy="company-name"], [class*="CompanyName"], [class*="company"]'
                )
                company = (await company_el.inner_text()).strip() if company_el else ""

                # Location
                loc_el = await card.query_selector(
                    '[data-cy="job-location"], [class*="Location"], [class*="location"]'
                )
                location = (await loc_el.inner_text()).strip() if loc_el else "Indonesia"

                # Salary (often not shown)
                sal_el = await card.query_selector('[class*="Salary"], [class*="salary"]')
                salary = (await sal_el.inner_text()).strip() if sal_el else ""

                # Link
                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                link = f"https://glints.com{href}" if href and href.startswith("/") else href

                if title and company:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": salary,
                        "platform": "Glints",
                        "url": link,
                        "keyword": keyword,
                        "role_type": classify_role(title),
                        "posted": "",
                        "scraped_at": datetime.now().isoformat(),
                    })
            except Exception as e:
                continue

    except PWTimeout:
        print(f"  [Glints] Timeout on keyword: {keyword}")
    except Exception as e:
        print(f"  [Glints] Error on keyword '{keyword}': {e}")

    print(f"  [Glints] Found {len(jobs)} jobs for '{keyword}'")
    return jobs

# ── Jobstreet scraper ──────────────────────────────────────────────────────────

async def scrape_jobstreet(page, keyword: str) -> list[dict]:
    jobs = []
    url = f"https://www.jobstreet.co.id/jobs?q={keyword.replace(' ', '+')}&l=Indonesia"

    print(f"  [Jobstreet] Searching: {keyword}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector(
            '[data-testid="job-card"], [class*="job-card"], article[class*="Job"]',
            timeout=15000
        )
        await asyncio.sleep(2)

        cards = await page.query_selector_all(
            '[data-testid="job-card"], [class*="job-card"], article[class*="Job"]'
        )

        for card in cards[:15]:
            try:
                title_el = await card.query_selector(
                    'h1, h2, h3, [data-automation="job-list-item-link-title"], [class*="Title"]'
                )
                title = (await title_el.inner_text()).strip() if title_el else ""

                company_el = await card.query_selector(
                    '[class*="company"], [data-automation="job-card-company"], span[class*="Company"]'
                )
                company = (await company_el.inner_text()).strip() if company_el else ""

                loc_el = await card.query_selector(
                    '[data-automation="job-location"], [class*="Location"], [class*="location"]'
                )
                location = (await loc_el.inner_text()).strip() if loc_el else "Indonesia"

                sal_el = await card.query_selector(
                    '[data-automation="job-salary"], [class*="salary"], [class*="Salary"]'
                )
                salary = (await sal_el.inner_text()).strip() if sal_el else ""

                link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                link = f"https://www.jobstreet.co.id{href}" if href and href.startswith("/") else href

                if title and company:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": salary,
                        "platform": "Jobstreet",
                        "url": link,
                        "keyword": keyword,
                        "role_type": classify_role(title),
                        "posted": "",
                        "scraped_at": datetime.now().isoformat(),
                    })
            except Exception:
                continue

    except PWTimeout:
        print(f"  [Jobstreet] Timeout on keyword: {keyword}")
    except Exception as e:
        print(f"  [Jobstreet] Error on keyword '{keyword}': {e}")

    print(f"  [Jobstreet] Found {len(jobs)} jobs for '{keyword}'")
    return jobs

# ── Kalibrr scraper ────────────────────────────────────────────────────────────

async def scrape_kalibrr(page, keyword: str) -> list[dict]:
    jobs = []
    url = f"https://www.kalibrr.com/job-board/te/{keyword.replace(' ', '%20')}/in/indonesia"

    print(f"  [Kalibrr] Searching: {keyword}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector(
            '[class*="job-card"], [class*="JobCard"], [data-cy*="job"]',
            timeout=12000
        )
        await asyncio.sleep(2)

        cards = await page.query_selector_all(
            '[class*="job-card"], [class*="JobCard"]'
        )

        for card in cards[:15]:
            try:
                title_el = await card.query_selector('h2, h3, [class*="title"], [class*="Title"]')
                title = (await title_el.inner_text()).strip() if title_el else ""

                company_el = await card.query_selector('[class*="company"], [class*="Company"]')
                company = (await company_el.inner_text()).strip() if company_el else ""

                link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                link = f"https://www.kalibrr.com{href}" if href and href.startswith("/") else href

                if title and company:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": "Indonesia",
                        "salary": "",
                        "platform": "Kalibrr",
                        "url": link,
                        "keyword": keyword,
                        "role_type": classify_role(title),
                        "posted": "",
                        "scraped_at": datetime.now().isoformat(),
                    })
            except Exception:
                continue

    except PWTimeout:
        print(f"  [Kalibrr] Timeout on keyword: {keyword}")
    except Exception as e:
        print(f"  [Kalibrr] Error on keyword '{keyword}': {e}")

    print(f"  [Kalibrr] Found {len(jobs)} jobs for '{keyword}'")
    return jobs

# ── Load existing jobs (for dedup against yesterday's results) ─────────────────

def load_existing_ids() -> set[str]:
    if OUTPUT_FILE.exists():
        try:
            data = json.loads(OUTPUT_FILE.read_text())
            return {
                f"{j['title'].lower().strip()}|{j['company'].lower().strip()}"
                for j in data.get("jobs", [])
            }
        except Exception:
            return set()
    return set()

# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    print("\n" + "="*60)
    print(f"  Job Scraper — starting at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    all_jobs: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for keyword in KEYWORDS:
            print(f"\n── Keyword: {keyword} ──")
            all_jobs += await scrape_glints(page, keyword)
            await asyncio.sleep(1.5)
            all_jobs += await scrape_jobstreet(page, keyword)
            await asyncio.sleep(1.5)
            all_jobs += await scrape_kalibrr(page, keyword)
            await asyncio.sleep(1.5)

        await browser.close()

    # Deduplicate within this run
    unique_jobs = dedupe(all_jobs)

    # Mark which ones are new vs seen before
    existing_ids = load_existing_ids()
    for job in unique_jobs:
        key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
        job["is_new"] = key not in existing_ids

    new_count = sum(1 for j in unique_jobs if j["is_new"])

    # Write output
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(unique_jobs),
        "new_since_last_run": new_count,
        "jobs": unique_jobs,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print(f"  Done! {len(unique_jobs)} total jobs ({new_count} new)")
    print(f"  Saved to: {OUTPUT_FILE}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
