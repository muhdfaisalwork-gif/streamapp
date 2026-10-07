import httpx, re
UA = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'}
r = httpx.get('https://tpb.party/top/201', headers=UA, timeout=15)
# Find any torrent rows
print('Looking for torrent link patterns...')
for pat in [
    r'<a[^>]+class="detLink"[^>]+href="(/torrent/\d+/[^"]+)"',
    r'<a[^>]+href="(/torrent/\d+/[^"]+)"',
    r'/torrent/(\d+)/',
]:
    matches = re.findall(pat, r.text)
    print(f'  pattern "{pat[:60]}": {len(matches)} matches')
    if matches:
        for m in matches[:3]:
            print(f'    {m}')

# Check what HTML structure we got
print()
print('HTML title:', re.search(r'<title>([^<]+)</title>', r.text).group(1))
# Look for any "detName" or similar
for tag in ['detName', 'detLink', 'searchResult', 'list-entry', 'row']:
    if tag in r.text:
        print(f'  found {tag} in HTML')

# Print first 1000 chars of body content
body = re.search(r'<body.*?</body>', r.text, flags=re.S)
if body:
    print('Body length:', len(body.group(0)))
    # Find any links that contain "torrent"
    torrent_links = re.findall(r'href="([^"]*torrent[^"]*)"', r.text)
    print(f'Torrent-related hrefs: {len(torrent_links)}')
    for tl in torrent_links[:5]:
        print(f'  {tl}')