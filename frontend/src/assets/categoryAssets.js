/**
 * categoryAssets.js — Centralized manifest for CATEGORY artwork (providers,
 * genres, collections, studios, animation studios, decades, actors, directors).
 *
 * This is deliberately separate from TITLE artwork (poster/backdrop), which
 * always comes from TMDB per the exact TMDB record — never from this file.
 * Never use an entry here as a movie/TV poster, and never pick a title's
 * poster by matching a filename or label against these keys.
 *
 * Swapping an asset only means editing the value here — no component should
 * hardcode one of these URLs directly.
 */

export const PROVIDER_ASSETS = {
    netflix: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/netflix.jpg',
    primeVideo: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/prime_video.jpg',
    disneyPlus: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/disney_plus.jpg',
    hulu: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/hulu.jpg',
    max: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/max.jpg',
    appleTvPlus: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/apple_tv.jpg',
    paramountPlus: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/paramount_plus.jpg',
    peacock: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/peacock.jpg',
    discoveryPlus: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/streaming_services/discovery_plus.jpg',
};

// Maps our streaming_providers.slug (DB) to a PROVIDER_ASSETS key, since the
// DB uses kebab-case slugs (e.g. "prime-video") and this manifest uses
// camelCase keys (e.g. "primeVideo"). Crunchyroll has no supplied image yet.
export const PROVIDER_SLUG_TO_ASSET_KEY = {
    netflix: 'netflix',
    'prime-video': 'primeVideo',
    'disney-plus': 'disneyPlus',
    hulu: 'hulu',
    max: 'max',
    'apple-tv-plus': 'appleTvPlus',
    'paramount-plus': 'paramountPlus',
    peacock: 'peacock',
    'discovery-plus': 'discoveryPlus',
};

export const GENRE_ASSETS = {
    trending: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/trending.png',
    action: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/action.png',
    adventure: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/adventure.png',
    animation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/animation.png',
    comedy: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/comedy.png',
    crime: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/crime.png',
    documentary: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/documentary.png',
    drama: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/drama.png',
    fantasy: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/fantasy.png',
    historical: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/historical.png',
    horror: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/horror.png',
    musical: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/musical.png',
    mystery: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/mystery.png',
    romance: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/romance.png',
    sciFi: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/sci-fi.png',
    thriller: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/thriller.png',
    war: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/genres/war.png',
};

// Maps our genres.slug (DB, from CANONICAL_GENRES in catalog_schema.py) to a
// GENRE_ASSETS key. Genres without a supplied asset simply have no entry here.
export const GENRE_SLUG_TO_ASSET_KEY = {
    action: 'action',
    adventure: 'adventure',
    animation: 'animation',
    comedy: 'comedy',
    crime: 'crime',
    documentary: 'documentary',
    drama: 'drama',
    fantasy: 'fantasy',
    history: 'historical',
    horror: 'horror',
    music: 'musical',
    mystery: 'mystery',
    romance: 'romance',
    'science-fiction': 'sciFi',
    thriller: 'thriller',
    war: 'war',
};

export const COLLECTION_ASSETS = {
    avatar: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/avatar.png',
    backToTheFuture: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/back_to_the_future.png',
    dune: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/dune.png',
    fastAndFurious: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/fast_and_furious.png',
    harryPotter: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/harry_potter.png',
    hungerGames: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/hunger_games.png',
    indianaJones: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/indiana_jones.png',
    jamesBond: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/james_bond.png',
    johnWick: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/john_wick.png',
    jurassicPark: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/jurassic_park.png',
    lordOfTheRings: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/lord_of_the_rings.png',
    marvel: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/marvel.png',
    matrix: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/matrix.png',
    missionImpossible: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/mission_impossible.png',
    monsterverse: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/monsterverse.png',
    piratesOfTheCaribbean: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/pirates_of_the_caribbean.png',
    rambo: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/rambo.png',
    rocky: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/rocky.png',
    starTrek: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/star_trek.png',
    starWars: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/star_wars.png',
    transformers: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/transformers.png',
    xMen: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/collections/x_men.png',
};

// Maps a collection to its TMDB collection ID, the authority for which titles
// belong to it — the image above is display-only and never determines membership.
export const COLLECTION_TMDB_IDS = {
    avatar: 87096,
    backToTheFuture: 264,
    dune: 726871,
    fastAndFurious: 9485,
    harryPotter: 1241,
    hungerGames: 131635,
    indianaJones: 84,
    jamesBond: 645,
    johnWick: 404609,
    jurassicPark: 328,
    lordOfTheRings: 119,
    // TMDB has no single "Marvel Cinematic Universe" collection (confirmed via
    // /search/collection) — 86311 is only "The Avengers Collection", a narrower
    // sub-franchise. The Marvel page must be driven by STUDIO_TMDB_IDS.marvelStudios
    // (company id 420) via /discover/movie?with_companies=420 instead.
    matrix: 2344,
    missionImpossible: 87359,
    monsterverse: 1767969,
    piratesOfTheCaribbean: 295,
    rambo: 5039,
    rocky: 1575,
    starTrek: 115575,
    starWars: 10,
    transformers: 8650,
    xMen: 748,
};

export const STUDIO_ASSETS = {
    dcStudios: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/dc_studios.png',
    dreamworksPictures: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/dreamworks_pictures.png',
    lionsgate: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/lionsgate.png',
    marvelStudios: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/marvel_studios.png',
    universalPictures: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/universal_pictures.png',
    waltDisneyPictures: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/walt_disney_pictures.png',
    warnerBros: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/studios/warner_bros_pictures.png',
};

// TMDB company IDs — the authority for studio filmography membership.
export const STUDIO_TMDB_IDS = {
    dcStudios: 184898,
    dreamworksPictures: 7,
    lionsgate: 1632,
    marvelStudios: 420,
    universalPictures: 33,
    waltDisneyPictures: 2,
    warnerBros: 174,
};

export const ANIMATION_STUDIO_ASSETS = {
    blueSkyAnimation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/blue_sky_animation.png',
    dreamworksAnimation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/dreamworks_animation.png',
    illumination: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/illumination.png',
    pixar: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/pixar.png',
    sonyPicturesAnimation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/sony_pictures_animation.png',
    waltDisneyAnimation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/walt_disney_animation.png',
    warnerBrosAnimation: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/animation_studios/warner_bros_animation.png',
};

export const ANIMATION_STUDIO_TMDB_IDS = {
    blueSkyAnimation: 9383,
    dreamworksAnimation: 521,
    illumination: 6704,
    pixar: 3,
    sonyPicturesAnimation: 2251,
    waltDisneyAnimation: 6125,
    warnerBrosAnimation: 2785,
};

export const DECADE_ASSETS = {
    1980: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/decades/1980.jpg',
    1990: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/decades/1990.jpg',
    2000: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/decades/2000.jpg',
    2010: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/decades/2010.jpg',
    2020: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/decades/2020.jpg',
};

export const ACTOR_ASSETS = {
    adamSandler: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/adam_sandler.jpg',
    arnoldSchwarzenegger: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/arnold_schwarzenegger.jpg',
    christianBale: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/christian_bale.jpg',
    clintEastwood: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/clint_eastwood.jpg',
    denzelWashington: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/denzel_washington.jpg',
    dwayneJohnson: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/dwayne_johnson.jpg',
    harrisonFord: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/harrison_ford.jpg',
    jackieChan: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/jackie_chan.jpg',
    jasonStatham: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/jason_statham.jpg',
    mattDamon: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/matt_damon.jpg',
    morganFreeman: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/morgan_freeman.jpg',
    nicolasCage: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/nicolas_cage.jpg',
    robertDowneyJr: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/robert_downey_jr.jpg',
    robinWilliams: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/robin_williams.jpg',
    ryanReynolds: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/ryan_reynolds.jpg',
    samuelLJackson: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/samuel_l_jackson.jpg',
    sylvesterStallone: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/sylvester_stallone.jpg',
    tomCruise: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/actors/tom_cruise.jpg',
};

// TMDB person IDs — resolved once so actor pages don't depend on name matching.
export const ACTOR_TMDB_IDS = {
    adamSandler: 19292,
    arnoldSchwarzenegger: 1100,
    christianBale: 3894,
    clintEastwood: 190,
    denzelWashington: 5292,
    dwayneJohnson: 18918,
    harrisonFord: 3,
    jackieChan: 18897,
    jasonStatham: 976,
    mattDamon: 1892,
    morganFreeman: 192,
    nicolasCage: 2963,
    robertDowneyJr: 3223,
    robinWilliams: 2157,
    ryanReynolds: 10859,
    samuelLJackson: 2231,
    sylvesterStallone: 16483,
    tomCruise: 500,
};

export const DIRECTOR_ASSETS = {
    alfredHitchcock: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/alfred_hitchcock.jpg',
    brianDePalma: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/brian_de_palma.jpg',
    christopherNolan: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/christopher_nolan.jpg',
    davidFincher: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/david_fincher.jpg',
    denisVilleneuve: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/denis_villeneuve.jpg',
    johnCarpenter: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/john_carpenter.jpg',
    martinScorsese: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/martin_scorsese.jpg',
    paulThomasAnderson: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/paul_thomas_anderson.jpg',
    stanleyKubrick: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/stanley_kubrick.jpg',
    stevenSpielberg: 'https://gitlab.com/DuckKota/omni-images/-/raw/main/directors/steven_speilberg.jpg',
};

// TMDB person IDs for directors.
export const DIRECTOR_TMDB_IDS = {
    alfredHitchcock: 2636,
    brianDePalma: 1150,
    christopherNolan: 525,
    davidFincher: 7467,
    denisVilleneuve: 137427,
    johnCarpenter: 11770,
    martinScorsese: 1032,
    paulThomasAnderson: 4762,
    stanleyKubrick: 240,
    stevenSpielberg: 488,
};

export default {
    providers: PROVIDER_ASSETS,
    providerSlugToAssetKey: PROVIDER_SLUG_TO_ASSET_KEY,
    genres: GENRE_ASSETS,
    genreSlugToAssetKey: GENRE_SLUG_TO_ASSET_KEY,
    collections: COLLECTION_ASSETS,
    collectionTmdbIds: COLLECTION_TMDB_IDS,
    studios: STUDIO_ASSETS,
    studioTmdbIds: STUDIO_TMDB_IDS,
    animationStudios: ANIMATION_STUDIO_ASSETS,
    animationStudioTmdbIds: ANIMATION_STUDIO_TMDB_IDS,
    decades: DECADE_ASSETS,
    actors: ACTOR_ASSETS,
    actorTmdbIds: ACTOR_TMDB_IDS,
    directors: DIRECTOR_ASSETS,
    directorTmdbIds: DIRECTOR_TMDB_IDS,
};
