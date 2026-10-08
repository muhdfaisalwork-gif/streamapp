import re, sys
sys.path.insert(0, '.')
from ingest_references import http_get
import httpx
import asyncio

async def go():
    async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
        url = 'https://tpb.party/top/201'
        html = await http_get(client, url)
        # Find the torrent link
        idx = html.find('81513377')
        if idx > 0:
            print('Bytes around 81513377:')
            print(repr(html[max(0,idx-100):idx+200]))
        print()
        # Look for href with /torrent/ pattern more loosely
        for m in re.finditer(r'torrent/', html):
            pos = m.start()
            chunk = html[max(0,pos-50):pos+80]
            print(f'At pos {pos}: {chunk!r}')
            if pos > 1500:
                break

asyncio.run(go())