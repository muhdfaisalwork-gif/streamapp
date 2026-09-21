import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

test_providers = [
    ("vidsrc.to", "https://vidsrc.to/embed/movie/939335"),
    ("vidsrc.me", "https://vidsrc.me/embed/939335"),
    ("vidsrc.cc", "https://vidsrc.cc/v2/embed/movie/939335"),
    ("vidsrc.in", "https://vidsrc.in/embed/movie/939335"),
    ("vidsrc.pm", "https://vidsrc.pm/embed/movie/939335"),
    ("vidsrc.net", "https://vidsrc.net/embed/movie/939335"),
    ("vidsrc.xyz", "https://vidsrc.xyz/embed/movie?tmdb=939335"),
    ("multiembed.mov", "https://multiembed.mov/?video_id=939335&tmdb=1"),
    ("player.autoembed.cc", "https://player.autoembed.cc/embed/movie/939335"),
    ("embed.su", "https://embed.su/embed/movie/939335"),
    ("2embed.cc", "https://www.2embed.cc/embed/939335"),
    ("smashy.stream", "https://player.smashy.stream/movie/939335"),
    ("superembed", "https://multiembed.mov/directstream.php?video_id=939335&tmdb=1"),
]

for name, u in test_providers:
    try:
        r = requests.get(u, headers=headers, timeout=4)
        print(f"[{name:<18}] status={r.status_code} len={len(r.text)}")
    except Exception as e:
        print(f"[{name:<18}] error: {type(e).__name__} - {e}")
