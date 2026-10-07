import urllib.request, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36'

def head(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, int(r.headers.get('content-length', 0))
    except Exception as e:
        return str(e), 0

print("=== RELEASES at ssmoviestvs.site/downloads (GET for real length) ===")
for k in ['latest.yml', 'ShadowStream-Setup-x64.exe', 'ShadowStream-win-x64.zip',
          'StreamApp-Browser-Shortcut.exe', 'ShadowStream-Setup-x64.exe.blockmap']:
    s, n = head(f'https://ssmoviestvs.site/downloads/{k}')
    print(f"   {k:<40} {s}  {n/1048576:>8.1f} MB")

print()
print("=== audio_language on /titles (paged) ===")
W = 'https://streamapp-catalog.muhd-faisal-work.workers.dev'
for path in ['/api/v1/titles?audio_language=hi&page=1&page_size=3',
             '/api/v1/titles?audio_language=ur&page=1&page_size=3',
             '/api/v1/title/bleach-2004-2']:
    req = urllib.request.Request(W + path, headers={'User-Agent': UA})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        d = json.loads(r.read())
        if isinstance(d, list):
            it = d[0] if d else {}
            print(f"   list len={len(d)} first={it.get('title')} audioLanguages={it.get('audioLanguages')}")
        else:
            items = d.get('items') or []
            it = items[0] if items else d
            print(f"   {r.status} total={d.get('total')} first={it.get('title')} audioLanguages={it.get('audioLanguages')} dubs={it.get('dubs')}")
    except Exception as e:
        print(f"   ERR {path}: {e}")