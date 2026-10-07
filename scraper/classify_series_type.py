#!/usr/bin/env python3
"""
Phase 4: Series Type Classification
Classifies TV titles into: fictional, true_story, historical, biographical, historical_fiction
Based on TMDB genres, keywords, and overview text.
"""
import sqlite3
import re
from pathlib import Path

CATALOG_DB = Path(__file__).parent / "catalog.db"

# Keywords that indicate each series type
TRUE_STORY_KEYWORDS = [
    'based on a true story', 'based on true events', 'true story', 'real events',
    'inspired by true', 'inspired by real', 'actual events', 'real life',
    'true crime', 'documentary', 'docudrama', 'reenactment'
]

HISTORICAL_KEYWORDS = [
    'historical', 'period drama', 'period piece', 'history', 'historical fiction',
    'set in', 'century', 'war', 'revolution', 'empire', 'dynasty', 'medieval',
    'ancient', 'victorian', 'edwardian', 'renaissance', 'colonial', 'wwii',
    'world war', 'civil war', 'cold war', 'historical figure'
]

BIOGRAPHICAL_KEYWORDS = [
    'biographical', 'biopic', 'biography', 'life of', 'story of',
    'based on the life', 'autobiographical', 'memoir', 'autobiography',
    'real person', 'famous', 'legend', 'icon', 'celebrity'
]

FICTIONAL_INDICATORS = [
    'fictional', 'fantasy', 'sci-fi', 'supernatural', 'magic', 'vampire',
    'zombie', 'alien', 'superhero', 'mutant', 'dystopian', 'post-apocalyptic',
    'alternate reality', 'parallel universe', 'time travel', 'space opera'
]

def normalize_text(text):
    """Normalize text for keyword matching."""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()

def classify_series_type(genres, keywords, overview, title):
    """
    Classify a series into one of:
    - fictional
    - true_story
    - historical
    - biographical
    - historical_fiction
    """
    # Combine all text for analysis
    all_text = " ".join([
        " ".join(genres) if genres else "",
        " ".join(keywords) if keywords else "",
        overview or "",
        title or ""
    ])
    normalized = normalize_text(all_text)
    
    # Score each category
    scores = {
        'true_story': 0,
        'historical': 0,
        'biographical': 0,
        'historical_fiction': 0,
        'fictional': 0
    }
    
    # Check true story keywords
    for kw in TRUE_STORY_KEYWORDS:
        if kw in normalized:
            scores['true_story'] += 2
    
    # Check historical keywords
    for kw in HISTORICAL_KEYWORDS:
        if kw in normalized:
            scores['historical'] += 2
    
    # Check biographical keywords
    for kw in BIOGRAPHICAL_KEYWORDS:
        if kw in normalized:
            scores['biographical'] += 2
    
    # Check fictional indicators
    for kw in FICTIONAL_INDICATORS:
        if kw in normalized:
            scores['fictional'] += 1
    
    # Genre-based scoring
    genre_text = " ".join(genres).lower() if genres else ""
    if 'documentary' in genre_text:
        scores['true_story'] += 3
    if 'history' in genre_text:
        scores['historical'] += 3
    if 'biography' in genre_text:
        scores['biographical'] += 3
    if 'war' in genre_text or 'war & politics' in genre_text:
        scores['historical'] += 2
    if 'fantasy' in genre_text or 'science fiction' in genre_text:
        scores['fictional'] += 3
    if 'crime' in genre_text and 'true crime' in normalized:
        scores['true_story'] += 2
    if 'drama' in genre_text:
        scores['historical_fiction'] += 1
    
    # Determine best match
    # If true_story is highest and significantly above others
    if scores['true_story'] >= max(scores.values()):
        if scores['true_story'] >= 3:
            return 'true_story'
    
    # If biographical is highest
    if scores['biographical'] >= max(scores.values()):
        if scores['biographical'] >= 3:
            return 'biographical'
    
    # If historical is highest
    if scores['historical'] >= max(scores.values()):
        # Check if it's historical_fiction (historical + fictional elements)
        if scores['fictional'] > 0 and scores['historical'] > scores['fictional']:
            return 'historical_fiction'
        if scores['historical'] >= 3:
            return 'historical'
    
    # Default to fictional for most TV content
    return 'fictional'

def main():
    conn = sqlite3.connect(str(CATALOG_DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all TV titles that don't have series_type set
    cur.execute("""
        SELECT t.id, t.title, t.original_title, t.year, t.overview, t.type
        FROM titles t
        WHERE t.type = 'tv' 
        AND (t.series_type IS NULL OR t.series_type = '')
    """)
    
    rows = cur.fetchall()
    print(f"Found {len(rows)} TV titles to classify")
    
    # We need genre and keyword data - check if we have it in title_genres
    # For now, use what we have in the database
    classified = 0
    for row in rows:
        title_id = row['id']
        title = row['title'] or ''
        original_title = row['original_title'] or ''
        year = row['year']
        overview = row['overview'] or ''
        
        # Get genres
        cur.execute("""
            SELECT g.name FROM genres g
            JOIN title_genres tg ON g.id = tg.genre_id
            WHERE tg.title_id = ?
        """, (title_id,))
        genres = [r['name'] for r in cur.fetchall()]
        
        # Get keywords from title_aka or overview
        keywords = []
        
        # Classify
        series_type = classify_series_type(genres, keywords, overview, title)
        
        # Update database
        cur.execute("""
            UPDATE titles SET series_type = ? WHERE id = ?
        """, (series_type, title_id))
        
        classified += 1
        if classified % 1000 == 0:
            conn.commit()
            print(f"  Classified {classified} titles...")
    
    conn.commit()
    print(f"Classification complete: {classified} titles classified")
    
    # Show distribution
    cur.execute("""
        SELECT series_type, COUNT(*) as count FROM titles 
        WHERE type = 'tv' AND series_type IS NOT NULL
        GROUP BY series_type
        ORDER BY count DESC
    """)
    print("\nSeries type distribution:")
    for row in cur.fetchall():
        print(f"  {row['series_type']}: {row['count']}")
    
    conn.close()

if __name__ == "__main__":
    main()