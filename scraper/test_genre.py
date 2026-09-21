import requests

r = requests.get('http://localhost:3000/api/v1/live/genre/Action?page=1&limit=50')
print('Status:', r.status_code)
data = r.json()
print('Count:', data.get('count'))
print('Results length:', len(data.get('results', [])))
for i, item in enumerate(data.get('results', [])[:15]):
    print(f"{i+1}. {item.get('title')} | poster: {item.get('poster')} | tmdb: {item.get('tmdbId')} | imdb: {item.get('imdbId')}")
