import asyncio
from sites.yts import YtsAdapter

async def test():
    ad = YtsAdapter()
    p1 = await ad.fetch_html("https://en.yts-official.biz/browse-movies?genre=action&page=1")
    m1 = [a.attrib.get("href") for a in p1.css("a[href*='/movies/']")] if p1 else []
    p2 = await ad.fetch_html("https://en.yts-official.biz/browse-movies?genre=action&page=2")
    m2 = [a.attrib.get("href") for a in p2.css("a[href*='/movies/']")] if p2 else []
    print("Page 1 movies count:", len(m1), "Sample:", m1[:2])
    print("Page 2 movies count:", len(m2), "Sample:", m2[:2])
    print("Overlap count:", len(set(m1).intersection(set(m2))))

if __name__ == "__main__":
    asyncio.run(test())
