import asyncio
import json
from playwright.async_api import async_playwright

LIVE_URL = "https://mplads.mospi.gov.in/digigov/dashboard.html"

async def test_id_scraping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("1. Opening live portal...")
        await page.goto(LIVE_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)
        
        try:
            await page.click(".privacy-close", timeout=4000)
            await page.wait_for_timeout(1000)
        except Exception:
            pass

        async def get_tile_values():
            tile_ids = ["fra", "tcc", "tra", "tsw", "tca", "tea"]
            res = {}
            for tid in tile_ids:
                elem = await page.query_selector(f"#{tid}")
                if elem:
                    txt = await elem.inner_text()
                    res[tid] = txt.strip().replace("\n", " | ")
                else:
                    res[tid] = "Not found"
            return res

        print("2. Scraping Lok Sabha tiles (#lok)...")
        await page.click("#lok")
        await page.wait_for_timeout(4000)
        ls_tiles = await get_tile_values()
        
        print("3. Scraping Rajya Sabha tiles (#rajya)...")
        await page.click("#rajya")
        await page.wait_for_timeout(4000)
        rs_tiles = await get_tile_values()

        await browser.close()
        
        print("\n--- LOK SABHA TILES ---")
        print(json.dumps(ls_tiles, indent=2))
        
        print("\n--- RAJYA SABHA TILES ---")
        print(json.dumps(rs_tiles, indent=2))

if __name__ == "__main__":
    asyncio.run(test_id_scraping())

