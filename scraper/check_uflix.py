import asyncio
from sites.uflix import UflixAdapter

async def test():
    ad = UflixAdapter()
    for u in ["https://uflix.cc/movies?page=2", "https://uflix.cc/movies/2", "https://uflix.cc/browse/page/2", "https://uflix.cc/movies?p=2"]:
        doc = await ad.fetch_html(u)
        cards = doc.css("a[href*='/movie/']") if doc else []
        print(u, "-> cards:", len(cards))

if __name__ == "__main__":
    asyncio.run(test())
