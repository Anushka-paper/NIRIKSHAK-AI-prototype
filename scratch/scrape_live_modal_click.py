import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_esakshi():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("1. Opening https://mplads.mospi.gov.in/digigov/dashboard.html...")
        await page.goto("https://mplads.mospi.gov.in/digigov/dashboard.html", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)
        
        # Close privacy modal if open
        try:
            print("2. Closing privacy policy modal...")
            await page.click(".privacy-close", timeout=5000)
            await page.wait_for_timeout(1000)
        except Exception as e:
            print("Modal close skipped:", e)
            
        async def parse_cards_dom():
            # Scrape text of legend cards / tiles
            text = await page.inner_text("body")
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return lines

        print("3. Clicking Lok Sabha (#lok)...")
        await page.click("#lok")
        await page.wait_for_timeout(4000)
        ls_lines = await parse_cards_dom()
        
        print("4. Clicking Rajya Sabha (#rajya)...")
        await page.click("#rajya")
        await page.wait_for_timeout(4000)
        rs_lines = await parse_cards_dom()

        print("\n--- LOK SABHA SCRAPED LINES ---")
        for line in ls_lines[:35]:
            print("  •", line)

        print("\n--- RAJYA SABHA SCRAPED LINES ---")
        for line in rs_lines[:35]:
            print("  •", line)

        with open("scratch/live_modal_dump.json", "w") as f:
            json.dump({"ls": ls_lines, "rs": rs_lines}, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_esakshi())

