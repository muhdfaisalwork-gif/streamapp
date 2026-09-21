import json, sys

REAL_HOLLYWOOD = ['The Dark Knight','The Matrix','Inception','Mad Max','Fight Club','Gladiator','Terminator','John Wick','Black Panther','Pulp Fiction','Forrest Gump','Goodfellas','Interstellar','Joker']
REAL_BOLLYWOOD = ['Jawan','Pathaan','Dangal','3 Idiots','Lagaan','PK','Sultan','Bajrangi Bhaijaan','Andhadhun','Sholay','Gangs of Wasseypur','Drishyam','Padmaavat','RRR','Kantara','Brahmastra','Stree']

def has_sherlock(items):
    for it in items:
        t = (it.get('title') or '').lower(); i = (it.get('id') or '').lower()
        if 'sherlock' in t or 'sherlock' in i: return True
    return False

def show(label, path):
    print('='*60); print(label); print('='*60)
    with open(path,'r',encoding='utf-8') as f: return json.load(f)

d = show("TEST 1: /api/v1/categories -> Action & Adventure", r"G:\streaming app\reports\test1_categories.json")
cats = d.get('categories', [])
print('Total categories:', len(cats))
action = next((c for c in cats if c.get('id') == 'action'), None)
items = action.get('items', []) if action else []
print('Action count:', len(items))
titles = [it.get('title','') for it in items]
ids = [it.get('id','') for it in items]
print('First 20 titles:', titles[:20])
print('First 20 ids:', ids[:20])
found_real = []
for rt in REAL_HOLLYWOOD:
    for tt in titles:
        if rt.lower() in (tt or '').lower(): found_real.append(rt); break
print('Real movie titles found:', found_real)
sp = has_sherlock(items)
print('Contains Sherlock:', sp)
print('VERDICT:', 'PASS' if (len(items) >= 50 and len(found_real) > 0 and not sp) else 'FAIL')
print()

d = show("TEST 2: /api/v1/search?country=hollywood", r"G:\streaming app\reports\test2_search_hollywood.json")
results = d.get('results', [])
count = d.get('count', len(results))
print('count field:', count, 'array len:', len(results))
titles = [it.get('title','') for it in results]
ids = [it.get('id','') for it in results]
print('First 15 titles:', titles[:15])
print('First 15 ids:', ids[:15])
found_real = []
for rt in REAL_HOLLYWOOD:
    for tt in titles:
        if rt.lower() in (tt or '').lower(): found_real.append(rt); break
print('Real movie titles found:', found_real)
print('VERDICT:', 'PASS' if (count >= 50 and len(found_real) > 0) else 'FAIL')
print()

d = show("TEST 3: /api/v1/search?country=bollywood", r"G:\streaming app\reports\test3_search_bollywood.json")
results = d.get('results', [])
count = d.get('count', len(results))
print('count field:', count, 'array len:', len(results))
titles = [it.get('title','') for it in results]
ids = [it.get('id','') for it in results]
print('First 15 titles:', titles[:15])
print('First 15 ids:', ids[:15])
found_bolly = []
for rt in REAL_BOLLYWOOD:
    for tt in titles:
        if rt.lower() in (tt or '').lower(): found_bolly.append(rt); break
print('Bollywood titles found:', found_bolly)
first5_t = titles[:5]; first5_i = ids[:5]
sherlock_first5 = any('sherlock' in (t or '').lower() for t in first5_t) or any('sherlock' in (i or '').lower() for i in first5_i)
print('Sherlock in first 5?:', sherlock_first5)
print('VERDICT:', 'PASS' if (count >= 50 and len(found_bolly) > 0 and not sherlock_first5) else 'FAIL')
print()

d = show("TEST 4: /api/v1/search?genre=Animation", r"G:\streaming app\reports\test4_search_animation.json")
results = d.get('results', [])
count = d.get('count', len(results))
print('count field:', count, 'array len:', len(results))
titles = [it.get('title','') for it in results]
ids = [it.get('id','') for it in results]
print('First 20 titles:', titles[:20])
print('First 20 ids:', ids[:20])
sp = has_sherlock(results)
print('Contains Sherlock:', sp)
print('VERDICT:', 'PASS' if (count >= 30 and not sp) else 'FAIL')
print()

d = show("TEST 5: /api/v1/search?q=demon%20slayer", r"G:\streaming app\reports\test5_search_demon.json")
results = d.get('results', [])
count = d.get('count', len(results))
print('count field:', count, 'array len:', len(results))
titles = [it.get('title','') for it in results]
ids = [it.get('id','') for it in results]
types = [(it.get('type') or it.get('media_type') or '') for it in results]
print('First 20 titles:', titles[:20])
print('First 20 ids:', ids[:20])
print('Types first 20:', types[:20])
tv_count = sum(1 for t in types if t == 'tv')
has_ds = any('demon slayer' in (t or '').lower() for t in titles) or any('demon-slayer' in (i or '').lower() for i in ids)
print('TV type count:', tv_count, '/', len(types))
print('Contains Demon Slayer:', has_ds)
print('VERDICT:', 'PASS' if (tv_count > 0 and has_ds) else 'FAIL')
print()
