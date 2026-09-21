import httpx
import asyncio

async def test():
    keys = [
        "8414344423348331a733797588e19d7f",
        "4f3264550d792f3fc274e61b0469b22e",
        "f9349842a425333f20857a26f63ac872",
        "3e8a4a589415494d1b846ff9b6d8b3c6",
        "b4cd4da55d6eb090a2a16d511eaee4f4",
        "29b0151125272a8c3e800938f654b035",
        "13b836488d5e02e0c1975e53e414c1d4",
        "d330c6a51240c5f72671ebfb91c0ff6a"
    ]
    async with httpx.AsyncClient(timeout=5.0) as client:
        for k in keys:
            try:
                r = await client.get(f"https://api.themoviedb.org/3/discover/movie?api_key={k}&page=1")
                if r.status_code == 200:
                    d = r.json()
                    tot = d.get("total_results")
                    print(f"KEY {k} WORKS! Total results: {tot}")
                    return k
                else:
                    print(f"Key {k[:8]}... returned {r.status_code}")
            except Exception as e:
                print(f"Key {k[:8]}... error: {e}")
    print("No test keys worked")
    return None

if __name__ == "__main__":
    asyncio.run(test())
