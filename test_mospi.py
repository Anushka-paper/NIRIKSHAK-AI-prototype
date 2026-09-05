import asyncio
import aiohttp
import json

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        url = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesData"
        payload = json.dumps({"uname": "34,2,7,2"})
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            async with session.post(url, data=payload, headers=headers) as resp:
                print(f"Status: {resp.status}")
                print("Response:")
                print(await resp.json(content_type=None))
        except Exception as e:
            print(e)

asyncio.run(main())
