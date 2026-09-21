import asyncio
from sites.donkey import DonkeyAdapter

async def test():
    ad = DonkeyAdapter()
    print("Testing Donkey adaptive fetch...")
    items = await ad.browse_genre("Action", 1)
    print("Donkey adaptive returned:", len(items), "items")
    if items:
        print("Sample:", items[0]["title"], items[0]["sourceUrl"])

if __name__ == "__main__":
    asyncio.run(test())
