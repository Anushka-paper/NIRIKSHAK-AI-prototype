import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_esakshi():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("1. Navigating to https://mplads.mospi.gov.in/digigov/dashboard.html...")
        await page.goto("https://mplads.mospi.gov.in/digigov/dashboard.html", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)
        
        async def get_all_cards():
            # Get text from cards-container or all tile divs
            elem = await page.query_selector(".cards-container, .rep-card-container, body")
            if elem:
                text = await elem.inner_text()
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                return lines
            return []

        print("2. Clicking Lok Sabha (#lok)...")
        await page.click("#lok")
        await page.wait_for_timeout(5000)
        ls_text = await get_all_cards()
        
        print("3. Clicking Rajya Sabha (#rajya)...")
        await page.click("#rajya")
        await page.wait_for_timeout(5000)
        rs_text = await get_all_cards()

        print("\n--- LOK SABHA SCRAPED LINES ---")
        print(json.dumps(ls_text[:30], indent=2))

        print("\n--- RAJYA SABHA SCRAPED LINES ---")
        print(json.dumps(rs_text[:30], indent=2))

        with open("scratch/scraped_live.json", "w") as f:
            json.dump({"ls": ls_text, "rs": rs_text}, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_esakshi())

