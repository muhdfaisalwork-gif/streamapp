import requests

r = requests.get('http://localhost:3000/api/v1/tv/244673/episodes?season=1')
print("Status:", r.status_code)
data = r.json()
print("Count:", data.get('count'))
episodes = data.get('episodes', [])
if episodes:
    print("Episode 1 sources:")
    for s in episodes[0].get('sources', []):
        print(" ", s)
