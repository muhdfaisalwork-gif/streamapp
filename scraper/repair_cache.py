import sqlite3

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()

# 1. Check before counts
c.execute("SELECT COUNT(*) FROM titles")
before_total = c.fetchone()[0]

# 2. Delete junk titles with no tmdb_id and no imdb_id
c.execute("""
    DELETE FROM titles 
    WHERE (imdb_id IS NULL OR imdb_id = '') 
      AND (tmdb_id IS NULL OR tmdb_id = '')
""")
deleted_no_ids = c.rowcount

# 3. Delete any remaining synthetic Volume titles or fake /poster_ paths
c.execute("""
    DELETE FROM titles 
    WHERE title LIKE '%Volume %' 
       OR poster LIKE '%/poster_%'
""")
deleted_synthetic = c.rowcount

# 4. Fix all broken/fake/relative poster paths
FALLBACK_POSTER = 'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg'

c.execute("""
    UPDATE titles
    SET poster = ?, backdrop = ?
    WHERE poster IS NULL 
       OR poster = '' 
       OR poster LIKE '/%'
       OR poster LIKE '%_pk.jpg%'
       OR poster LIKE '%_tr.jpg%'
       OR poster LIKE '%_eg.jpg%'
       OR poster LIKE '%welad%'
       OR poster LIKE '%hashashin%'
       OR poster LIKE '%sang_e_mah%'
       OR poster LIKE '%khaie%'
       OR poster LIKE '%gentleman%'
       OR poster LIKE '%lnj_pk%'
       OR poster LIKE '%qaz_pk%'
       OR poster LIKE '%/movies/poster/%'
""", (FALLBACK_POSTER, FALLBACK_POSTER))
fixed_posters = c.rowcount

conn.commit()

# 5. Check after counts
c.execute("SELECT COUNT(*) FROM titles")
after_total = c.fetchone()[0]

c.execute("""
    SELECT COUNT(*) FROM titles 
    WHERE (imdb_id IS NULL OR imdb_id = '') AND (tmdb_id IS NULL OR tmdb_id = '')
""")
remaining_no_ids = c.fetchone()[0]

c.execute("""
    SELECT COUNT(*) FROM titles 
    WHERE poster IS NULL OR poster = '' OR poster LIKE '/%' OR poster LIKE '%_pk.jpg%'
""")
remaining_bad_posters = c.fetchone()[0]

print(f"Before total: {before_total}")
print(f"Deleted unplayable titles (no IDs): {deleted_no_ids}")
print(f"Deleted synthetic Volume/poster titles: {deleted_synthetic}")
print(f"Fixed bad/missing poster URLs: {fixed_posters}")
print(f"After total: {after_total}")
print(f"Remaining titles with no IDs: {remaining_no_ids} (should be 0)")
print(f"Remaining bad posters: {remaining_bad_posters} (should be 0)")

conn.close()
