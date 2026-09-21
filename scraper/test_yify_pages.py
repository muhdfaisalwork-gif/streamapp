import asyncio
from sites.yify import YifyAdapter

async def test():
    yf = YifyAdapter()
    for p in [1, 5, 10, 20]:
        doc = await yf.fetch_html(f"https://yify.pro/browse-movies/{p}/")
        items = yf._extract_items(doc)
        sample = items[0]["title"] if items else "None"
        print(f"Yify browse page {p}: {len(items)} items. Sample: {sample}")

if __name__ == "__main__":
    asyncio.run(test())
