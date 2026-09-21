import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

urls = [
    ("Khaie VidSrc", "https://vidsrc.to/embed/tv/244673/1/1"),
    ("Khaie VidSrc.xyz", "https://vidsrc.xyz/embed/tv?tmdb=244673&season=1&episode=1"),
    ("Khaie MultiEmbed", "https://multiembed.mov/?video_id=244673&tmdb=1&s=1&e=1"),
    ("Breaking Bad VidSrc", "https://vidsrc.to/embed/tv/1396/1/1"),
    ("Breaking Bad VidSrc.xyz", "https://vidsrc.xyz/embed/tv?tmdb=1396&season=1&episode=1"),
]

for label, u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=5)
        print(f"[{label}] status={r.status_code} len={len(r.text)}")
        if "unavailable" in r.text.lower():
            print(f"  -> Contains 'unavailable'!")
        if "player" in r.text.lower() or "iframe" in r.text.lower():
            print(f"  -> Contains player/iframe")
    except Exception as e:
        print(f"[{label}] error: {e}")
