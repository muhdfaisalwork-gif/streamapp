import httpx, re
UA = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'}
r = httpx.get('https://tpb.party/top/201', headers=UA, timeout=15)
html = r.text
# Find any href containing "torrent"
tlinks = re.findall(r'href="([^"]*torrent[^"]*)"', html)
print('All torrent-related hrefs:')
for t in tlinks[:8]:
    print(' ', t[:140])
print()
# Try finding /torrent/ID/slug pattern with different boundaries
for pat in [r'href="(/torrent/\d+/[A-Za-z0-9_.\-%]+)"',
            r'href="(/torrent/\d+/\S+?)"',
            r'/torrent/(\d+)/([A-Za-z0-9_.\-%]+)']:
    matches = re.findall(pat, html)
    print(f'  pattern {pat[:55]}: {len(matches)} matches')
    if matches:
        for m in matches[:3]:
            print(f'    {m}')