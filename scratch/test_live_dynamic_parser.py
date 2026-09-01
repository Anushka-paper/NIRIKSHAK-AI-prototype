import asyncio
import re
import json
from playwright.async_api import async_playwright

LIVE_URL = "https://mplads.mospi.gov.in/digigov/dashboard.html"

async def live_parse():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Connecting to live eSAKSHI portal:", LIVE_URL)
        await page.goto(LIVE_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)
        
        try:
            await page.click(".privacy-close", timeout=4000)
            await page.wait_for_timeout(1000)
        except Exception:
            pass

        async def parse_dom(house_name):
            text = await page.inner_text("body")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            
            data = {
                "house": house_name,
                "allocated_limit_cr": 0.0,
                "calamity_consent_cr": 0.0,
                "recommended_count": 0,
                "recommended_cr": 0.0,
                "sanctioned_count": 0,
                "sanctioned_cr": 0.0,
                "completed_count": 0,
                "completed_cr": 0.0,
                "expenditure_cr": 0.0
            }
            
            for i, line in enumerate(lines):
                if "Allocated Limit for" in line and i+1 < len(lines):
                    # Next line contains e.g. "8,318.06 Crore" or "3,363.85 Crore"
                    m = re.search(r'([\d,]+\.?\d*)', lines[i+1])
                    if m:
                        data["allocated_limit_cr"] = float(m.group(1).replace(",", ""))
                elif "Amount consented for Calamity" in line and i+1 < len(lines):
                    m = re.search(r'([\d,]+\.?\d*)', lines[i+1])
                    if m:
                        data["calamity_consent_cr"] = float(m.group(1).replace(",", ""))
                elif "Works Recommended" in line:
                    # Look ahead 4 lines for No. and Crore
                    for k in range(i+1, min(i+5, len(lines))):
                        if "No." in lines[k]:
                            m_no = re.search(r'No\.\s*([\d,]+)', lines[k])
                            if m_no:
                                data["recommended_count"] = int(m_no.group(1).replace(",", ""))
                        elif "Crore" in lines[k]:
                            m_cr = re.search(r'([\d,]+\.?\d*)', lines[k])
                            if m_cr:
                                data["recommended_cr"] = float(m_cr.group(1).replace(",", ""))
                elif "Works Sanctioned" in line:
                    for k in range(i+1, min(i+5, len(lines))):
                        if "No." in lines[k]:
                            m_no = re.search(r'No\.\s*([\d,]+)', lines[k])
                            if m_no:
                                data["sanctioned_count"] = int(m_no.group(1).replace(",", ""))
                        elif "Crore" in lines[k]:
                            m_cr = re.search(r'([\d,]+\.?\d*)', lines[k])
                            if m_cr:
                                data["sanctioned_cr"] = float(m_cr.group(1).replace(",", ""))
                elif "Works Completed" in line:
                    for k in range(i+1, min(i+5, len(lines))):
                        if "No." in lines[k]:
                            m_no = re.search(r'No\.\s*([\d,]+)', lines[k])
                            if m_no:
                                data["completed_count"] = int(m_no.group(1).replace(",", ""))
                        elif "Crore" in lines[k]:
                            m_cr = re.search(r'([\d,]+\.?\d*)', lines[k])
                            if m_cr:
                                data["completed_cr"] = float(m_cr.group(1).replace(",", ""))
                elif "Expenditure on Completed" in line and i+1 < len(lines):
                    m = re.search(r'([\d,]+\.?\d*)', lines[i+1])
                    if m:
                        data["expenditure_cr"] = float(m.group(1).replace(",", ""))

            return data

        # Scrape Lok Sabha
        await page.click("#lok")
        await page.wait_for_timeout(3000)
        ls_res = await parse_dom("Lok Sabha")

        # Scrape Rajya Sabha
        await page.click("#rajya")
        await page.wait_for_timeout(3000)
        rs_res = await parse_dom("Rajya Sabha")

        await browser.close()
        
        print("\n--- LIVE PARSED LOK SABHA ---")
        print(json.dumps(ls_res, indent=2))
        
        print("\n--- LIVE PARSED RAJYA SABHA ---")
        print(json.dumps(rs_res, indent=2))

if __name__ == "__main__":
    asyncio.run(live_parse())

