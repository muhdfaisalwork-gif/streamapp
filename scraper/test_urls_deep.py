import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

test_urls = [
    # Jawan (Movie 939335)
    ("Jawan vidsrc.me", "https://vidsrc.me/embed/movie?tmdb=939335"),
    ("Jawan vidsrc.to", "https://vidsrc.to/embed/movie/939335"),
    ("Jawan multiembed", "https://multiembed.mov/?video_id=939335&tmdb=1"),
    ("Jawan 2embed", "https://www.2embed.cc/embed/939335"),

    # Doctor Who (TV 57243 S1E1)
    ("Doctor Who vidsrc.me", "https://vidsrc.me/embed/tv?tmdb=57243&season=1&episode=1"),
    ("Doctor Who vidsrc.to", "https://vidsrc.to/embed/tv/57243/1/1"),
    ("Doctor Who multiembed", "https://multiembed.mov/?video_id=57243&tmdb=1&s=1&e=1"),

    # Khaie (TV 244673 / tt30894528 S1E1)
    ("Khaie vidsrc.me (tmdb)", "https://vidsrc.me/embed/tv?tmdb=244673&season=1&episode=1"),
    ("Khaie vidsrc.me (imdb)", "https://vidsrc.me/embed/tv?imdb=tt30894528&season=1&episode=1"),
    ("Khaie vidsrc.to", "https://vidsrc.to/embed/tv/244673/1/1"),
    ("Khaie multiembed (tmdb)", "https://multiembed.mov/?video_id=244673&tmdb=1&s=1&e=1"),
    ("Khaie multiembed (imdb)", "https://multiembed.mov/?video_id=tt30894528&s=1&e=1"),
]

for label, u in test_urls:
    try:
        r = requests.get(u, headers=headers, timeout=5)
        print(f"[{label:<25}] status={r.status_code} len={len(r.text)}")
    except Exception as e:
        print(f"[{label:<25}] error: {e}")
