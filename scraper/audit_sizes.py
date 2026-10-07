import urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36'

def size(url):
    # Range GET so we read bytes instead of downloading 100MB
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Range': 'bytes=0-0'})
    try:
        r = urllib.request.urlopen(req, timeout=25)
        cr = r.headers.get('content-range')
        if cr and '/' in cr:
            return int(cr.split('/')[-1]), r.status
        # fallback: content-length on full response
        req2 = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
        r2 = urllib.request.urlopen(req2, timeout=25)
        n = r2.headers.get('content-length')
        return (int(n) if n else None), r2.status
    except Exception as e:
        return str(e), None

for k in ['latest.yml', 'ShadowStream-Setup-x64.exe', 'ShadowStream-win-x64.zip',
          'StreamApp-Browser-Shortcut.exe', 'ShadowStream-Setup-x64.exe.blockmap']:
    n, s = size(f'https://ssmoviestvs.site/downloads/{k}')
    if isinstance(n, int):
        print(f"   {k:<40} {s}  {n/1048576:>8.1f} MB")
    else:
        print(f"   {k:<40} {s}  {n}")