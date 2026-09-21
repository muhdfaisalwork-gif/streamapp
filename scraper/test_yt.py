import requests

headers = {'User-Agent': 'Mozilla/5.0'}
u = "https://www.youtube-nocookie.com/embed?listType=search&list=Khaie+Episode+1"
r = requests.get(u, headers=headers)
print("YouTube embed status:", r.status_code, "len:", len(r.text))
