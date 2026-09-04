"""
live_scraper.py
----------------
Real Playwright-based scraper for mplads.mospi.gov.in
This script automates a headless Chromium browser to navigate the government
portal, find the internal data endpoints, and download the raw CSV data.

PREREQUISITES (run once):
    pip install playwright beautifulsoup4
    playwright install chromium
"""

import asyncio
import os
import csv
import json
import re
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
BASE_URL    = "https://mplads.mospi.gov.in/digigov/dashboard.html"
OUTPUT_DIR  = Path(__file__).parent / "LS_DATASET"
TIMESTAMP_FILE = Path(__file__).parent / ".last_scraped"

# All Indian States + UTs (abbreviations used by the portal)
ALL_STATES = [
    "AN", "AP", "AR", "AS", "BR", "CH", "CT", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OR", "PB", "PY", "RJ",
    "SK", "TG", "TN", "TR", "UP", "UT", "WB"
]

PARLIAMENT_TYPES = ["LS", "RS"]  # Lok Sabha, Rajya Sabha


# ------------------------------------------------------------------
# STEP 1: Find the real hidden data endpoint
# ------------------------------------------------------------------
async def discover_api_endpoint():
    """
    Opens the MoSPI portal in a headless browser, watches all network
    requests, and identifies the internal JSON/CSV data endpoint.
    Run this ONCE to discover the URL — then hardcode it below.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
        return

    async with async_playwright() as p:
        # Launch with stealth args to bypass bot detection
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = await browser.new_context(
            # Mimic a real Windows Chrome browser
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = await context.new_page()

        # Remove the "webdriver" property that sites use to detect bots
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        discovered_endpoints = []

        # Intercept ALL network requests to find the data API
        def on_request(request):
            url = request.url
            # Look for requests that look like data endpoints
            if any(x in url for x in [".do", "getWork", "report", "export", "json", "csv", "servlet", "ajax"]):
                print(f"[DISCOVERED] {request.method} {url}")
                discovered_endpoints.append({
                    "method": request.method,
                    "url": url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data
                })

        page.on("request", on_request)

        print(f"Navigating to {BASE_URL} ...")
        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            print("Page loaded. Waiting for JS to settle...")
            await asyncio.sleep(6)  # Give jQuery + Select2 time to initialize
        except Exception as e:
            print(f"[WARN] Page load warning (non-fatal): {e}")
            print("Continuing with partial page load...")

        # The portal uses Select2 — we must trigger it via JavaScript, not native clicks
        print("Triggering Select2 dropdowns via JavaScript...")
        try:
            # Get all select2 select element IDs
            select_ids = await page.evaluate("""
                () => Array.from(document.querySelectorAll('select')).map(s => s.id)
            """)
            print(f"Found select IDs: {select_ids}")

            # Try selecting the first option in each dropdown via jQuery
            for sel_id in select_ids[:3]:  # Try first 3 dropdowns
                try:
                    await page.evaluate(f"""
                        () => {{
                            var el = document.getElementById('{sel_id}');
                            if (el && el.options.length > 1) {{
                                el.selectedIndex = 1;
                                $(el).trigger('change');  // Trigger jQuery change event
                            }}
                        }}
                    """)
                    await asyncio.sleep(2)  # Wait for AJAX response
                    print(f"  Triggered change on #{sel_id}")
                except Exception as ex:
                    print(f"  Could not trigger #{sel_id}: {ex}")

        except Exception as e:
            print(f"[WARN] Could not interact with Select2 dropdowns: {e}")

        # Final wait to catch any late AJAX calls
        await asyncio.sleep(3)

        # Capture current page URL and HTML source for manual analysis
        html_source = await page.content()
        source_file = Path(__file__).parent / "portal_source.html"
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(html_source)
        print(f"Saved page HTML -> {source_file} (inspect for JS API calls)")

        print(f"\nCapture complete. Found {len(discovered_endpoints)} potential endpoint(s).")
        await browser.close()

        # Save discovered endpoints to a file for inspection
        output_file = Path(__file__).parent / "discovered_endpoints.json"
        with open(output_file, "w") as f:
            json.dump(discovered_endpoints, f, indent=2)

        print(f"Saved to: {output_file}")
        if not discovered_endpoints:
            print("\n[INFO] No data endpoints found. The portal may:")
            print("  1. Require a login before showing data")
            print("  2. Load data only on user interaction (click a state first)")
            print("  3. Be blocking headless browser access")
            print("\n[TIP] Try opening the portal manually in Chrome, go to:")
            print("  DevTools (F12) → Network tab → Filter: XHR")
            print("  Then change any filter on the page and look for POST requests.")
        return discovered_endpoints


# ------------------------------------------------------------------
# STEP 2: Once endpoint is found, use direct HTTP requests (faster)
# ------------------------------------------------------------------
async def get_tenure_list(session):
    """Fetch available tenures (parliament sessions) from the real API."""
    import aiohttp
    url = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTenureData"
    payload = json.dumps({"uname": "0,0,0,2"})
    headers = {"Content-Type": "application/json; charset=utf-8"}
    try:
        async with session.post(url, data=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                print(f"  Tenures found: {[t.get('CAPTION', t) for t in data]}")
                return data
    except Exception as e:
        print(f"  Error fetching tenures: {e}")
    return []

async def get_state_list(session):
    """Fetch all states from the real API."""
    import aiohttp
    url = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getStateData"
    payload = json.dumps({})
    headers = {"Content-Type": "application/json; charset=utf-8"}
    try:
        async with session.post(url, data=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                print(f"  States found: {len(data)}")
                return data
    except Exception as e:
        print(f"  Error fetching states: {e}")
    return []

async def get_tiles_data(session, combo_str: str):
    """Fetch summary tile data for a given combo string."""
    import aiohttp
    url = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesData"
    payload = json.dumps({"uname": combo_str})
    headers = {"Content-Type": "application/json; charset=utf-8"}
    try:
        async with session.post(url, data=payload, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json(content_type=None)
    except Exception as e:
        print(f"  Error fetching tiles for {combo_str}: {e}")
    return {}

async def scrape_state_data(session, state_id: str, parliament_type: str, tenure_id: str):
    """
    Fetch MP-level data for a given state using the discovered API.
    combo format: "state_id,house_type,tenure_id,2"
    house_type: LOK = 2, RAJYA = 1
    """
    house = "2" if parliament_type == "LS" else "1"
    combo_str = f"{state_id},{house},{tenure_id},2"
    return await get_tiles_data(session, combo_str)



# ------------------------------------------------------------------
# STEP 3: Full scrape orchestration
# ------------------------------------------------------------------
async def run_full_scrape():
    """
    Main scrape runner using the REAL discovered MPLADS REST API.
    Fetches state list + tiles data for each state/tenure combination.
    Works without login — pulls publicly accessible aggregate data.
    """
    import aiohttp, random

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    print("Starting REAL MPLADS scrape via REST API")
    print("=" * 60)

    headers = {"Content-Type": "application/json; charset=utf-8"}
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:

        # Step 1: Get all states
        print("[1/4] Fetching state list from MPLADS API...")
        states = await get_state_list(session)
        if not states:
            print("  ERROR: Could not get state list. Check internet connection.")
            return
        print(f"  Found {len(states)} states/UTs")

        # Step 2: Get tenure list
        print("[2/4] Fetching tenure list...")
        tenures = await get_tenure_list(session)
        if not tenures:
            tenures = [{"ID": 5, "CAPTION": "17th Lok Sabha"}, {"ID": 7, "CAPTION": "18th Lok Sabha"}]
        print(f"  Found tenures: {[t['CAPTION'] for t in tenures]}")

        # Step 3: For each state + tenure, fetch tile stats
        print("[3/4] Fetching tiles data per state per tenure...")
        for parliament_type, house_code in [("LS", "2"), ("RS", "1")]:
            for tenure in tenures:
                tenure_id = str(tenure["ID"])
                for state_info in states:
                    state_id = str(state_info["STATE_ID"])
                    state_name = state_info["STATE_NAME"]
                    combo = f"{state_id},{house_code},{tenure_id},2"

                    tiles = await get_tiles_data(session, combo)
                    if not tiles:
                        continue

                    def parse_val(arr, idx=0, default=0):
                        try:
                            v = str(arr[idx]).replace("\u00a0", "").replace(",", "").strip()
                            return float(v) if v else default
                        except Exception:
                            return default

                    alloc_arr = tiles.get("Allocated Limit for Hon'ble MPs", [])
                    exp_arr = tiles.get("Expenditure on Completed and On-going Works as on Date", [])
                    wc_arr = tiles.get("Works Completed", [])
                    ws_arr = tiles.get("Works Sanctioned", [])
                    wr_arr = tiles.get("Works Recommended", [])

                    allocated_crore = parse_val(alloc_arr, 0)
                    exp_crore = parse_val(exp_arr, 0)
                    works_completed = int(parse_val(wc_arr, 0))
                    works_sanctioned = int(parse_val(ws_arr, 0))
                    works_recommended = int(parse_val(wr_arr, 0))

                    row = {
                        "state_id": state_id,
                        "state": state_name,
                        "parliament_type": parliament_type,
                        "tenure_id": tenure_id,
                        "tenure_caption": tenure["CAPTION"],
                        "allocated_crore": allocated_crore,
                        "expenditure_crore": exp_crore,
                        "works_recommended": works_recommended,
                        "works_sanctioned": works_sanctioned,
                        "works_completed": works_completed,
                        "scraped_at": datetime.now().isoformat(),
                    }
                    all_rows.append(row)
                    print(f"  {state_name[:20]:20s} | {parliament_type} | T:{tenure_id} | Alloc:{allocated_crore}")
                    await asyncio.sleep(0.3)

    # Step 4: Write output
    print("[4/4] Saving results...")
    if all_rows:
        output_file = OUTPUT_DIR / "loksabha_state_tiles.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nSaved {len(all_rows):,} rows -> {output_file}")

        with open(TIMESTAMP_FILE, "w") as f:
            f.write(datetime.now().isoformat())
        print(f"Timestamp written -> {TIMESTAMP_FILE}")
    else:
        print("\nNo data collected. The API may have changed.")




# ------------------------------------------------------------------
# ENTRYPOINTS
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "discover":
        # Run: python live_scraper.py discover
        # Opens browser, watches network, dumps endpoint list
        print("=== DISCOVERY MODE ===")
        print("Opening portal in headless browser to find data endpoints...\n")
        asyncio.run(discover_api_endpoint())
    else:
        # Run: python live_scraper.py
        # Full production scrape
        print("=== FULL SCRAPE MODE ===")
        asyncio.run(run_full_scrape())
