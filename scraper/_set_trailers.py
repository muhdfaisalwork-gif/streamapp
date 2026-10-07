import sqlite3

# Curated YouTube trailer IDs for popular well-known films.
# Format: (slug, youtube_url)
TRAILERS = [
    ('the-lord-of-the-rings-the-return-of-the-king-2003', 'https://www.youtube.com/watch?v=r5X-hFf6Bwo'),
    ('parasite-2019', 'https://www.youtube.com/watch?v=5xH0HfJHsaY'),
    ('one-piece-1999', 'https://www.youtube.com/watch?v=S8_YwFLCh4U'),
    ('attack-on-titan-2013', 'https://www.youtube.com/watch?v=MGRm4IzK1SQ'),
    ('fullmetal-alchemist-brotherhood-2009', 'https://www.youtube.com/watch?v=--IcmZkvL0Q'),
    ('squid-game-2021', 'https://www.youtube.com/watch?v=oqxAJKy0IU4'),
    ('spirited-away-2001', 'https://www.youtube.com/watch?v=ByXuk9QqQkk'),
    ('your-name-2016', 'https://www.youtube.com/watch?v=xU47nhruN-Q'),
    ('sherlock', 'https://www.youtube.com/watch?v=qlcWFoGOneE'),
    ('breaking-bad', 'https://www.youtube.com/watch?v=HhesaQXLuRY'),
    ('star-wars-episode-iv-a-new-hope-1977', 'https://www.youtube.com/watch?v=vZ734NWnAHA'),
    ('the-lord-of-the-rings-the-fellowship-of-the-ring-2001', 'https://www.youtube.com/watch?v=V75dMMIW2B4'),
    ('the-lord-of-the-rings-the-two-towers-2002', 'https://www.youtube.com/watch?v=LbfMDwc4MGY'),
    ('harry-potter-and-the-deathly-hallows-part-2-2011', 'https://www.youtube.com/watch?v=mObK5XD8eok'),
    ('one-piece-film-red-2022', 'https://www.youtube.com/watch?v=4SCNxhTDb9g'),
    ('jujutsu-kaisen-2020', 'https://www.youtube.com/watch?v=4A_X-Dvl0ws'),
    ('demon-slayer-kimetsu-no-yaiba-2019', 'https://www.youtube.com/watch?v=ATJYr5Z6CCc'),
    ('death-note-2006', 'https://www.youtube.com/watch?v=NlJZ-YgAt-c'),
    ('rrr-2022', 'https://www.youtube.com/watch?v=Ng_LkCOmmzM'),
    ('chernobyl-2019', 'https://www.youtube.com/watch?v=s9APLXM9Ei8'),
    ('the-blue-elephant-2014', 'https://www.youtube.com/watch?v=8r5L3tB8Y1Y'),
    ('baahubali-2-the-conclusion-2017', 'https://www.youtube.com/watch?v=G62Hr81YbYo'),
    ('vikram-2022', 'https://www.youtube.com/watch?v=OKBMCL-frPU'),
    ('the-boys-2019', 'https://www.youtube.com/watch?v=06-K2nGgFnY'),
    ('mirzapur-2018', 'https://www.youtube.com/watch?v=lYBR0U2jCYo'),
    ('sardar-udham-2021', 'https://www.youtube.com/watch?v=LwGBrY_ijC0'),
    ('shershaah-2021', 'https://www.youtube.com/watch?v=QqOH4VkIvJU'),
    ('capernaum-2018', 'https://www.youtube.com/watch?v=ULXhyROVEkY'),
    ('a-separation-2011', 'https://www.youtube.com/watch?v=WP__GJzNcS0'),
    ('die-hard-1988', 'https://www.youtube.com/watch?v=2HU_m9h0Gyw'),
    ('scarface-1983', 'https://www.youtube.com/watch?v=VMaKwQ1WCXM'),
    ('raiders-of-the-lost-ark-1981', 'https://www.youtube.com/watch?v=Rh_BJXG1-44'),
    ('pirates-of-the-caribbean-the-curse-of-the-black-pearl-2003', 'https://www.youtube.com/watch?v=naQr0AvTrHk'),
    ('the-terminator-1984', 'https://www.youtube.com/watch?v=k64P4l2Wmeg'),
    ('the-sixth-sense-1999', 'https://www.youtube.com/watch?v=VG9AGf66tRY'),
    ('for-sama-2019', 'https://www.youtube.com/watch?v=8ssYAU7w8mA'),
    ('planet-earth-2006', 'https://www.youtube.com/watch?v=c8aFcHFu8QM'),
    ('wednesday-2022', 'https://www.youtube.com/watch?v=Di310WS8zLk'),
    ('solo-leveling-2024', 'https://www.youtube.com/watch?v=4gR0gRrVUf8'),
    ('frieren-beyond-journeys-end-2023', 'https://www.youtube.com/watch?v=ZAkJtMIKsWk'),
    ('spy-x-family-2022', 'https://www.youtube.com/watch?v=ofXigq9aIpo'),
]

db = sqlite3.connect('catalog.db')
cur = db.cursor()

updated = 0
not_found = []
for slug, url in TRAILERS:
    cur.execute("UPDATE titles SET trailer_url = ? WHERE slug = ?", (url, slug))
    if cur.rowcount > 0:
        updated += 1
    else:
        not_found.append(slug)

db.commit()
db.close()
print(f'Updated: {updated}/{len(TRAILERS)}')
if not_found:
    print(f'Slugs not found in DB: {not_found}')
