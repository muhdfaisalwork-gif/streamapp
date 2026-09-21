import re

content = open('backend/src/scrapers/MovieBoxScraper.js', encoding='utf-8').read()
v = re.findall(r"v\(\s*'([^']+)'", content)
print('Total v(...) in MovieBox:', len(v))
print('Sample:', v[:10])
