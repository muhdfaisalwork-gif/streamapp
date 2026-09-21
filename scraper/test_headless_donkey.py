import asyncio
from scrapling.fetchers import StealthyFetcher

async def test():
    print("Launching StealthyFetcher with network_idle...")
    resp = await StealthyFetcher.async_fetch("https://donkey.to/media/movie", headless=True, network_idle=True)
    all_a = resp.css("a")
    print("Total anchors rendered on Donkey:", len(all_a))
    for a in all_a[:15]:
        print("  a:", a.attrib.get("href"), "|", a.get_all_text().strip())

if __name__ == "__main__":
    asyncio.run(test())
