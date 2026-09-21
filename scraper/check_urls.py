import requests

headers = {'User-Agent': 'Mozilla/5.0'}
urls = [
    'https://image.tmdb.org/t/p/w500/welad_rizk_3.jpg',
    'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg'
]
for u in urls:
    try:
        r = requests.get(u, headers=headers, stream=True, timeout=3)
        print(u, '=>', r.status_code)
    except Exception as e:
        print(u, 'error:', e)
