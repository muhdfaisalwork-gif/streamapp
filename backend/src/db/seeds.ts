import type { MediaItem } from '../types/index.ts';

export const SEED_CATALOG: MediaItem[] = [
  {
    id: 'media-001',
    title: 'Sintel',
    slug: 'sintel-2010',
    description: 'A lonely young woman, Sintel, helps and befriends a dragon cub whom she calls Scales. But when Scales is kidnapped by an adult dragon, Sintel embarks on an epic, perilous quest across the continent to find him.',
    releaseYear: 2010,
    durationSeconds: 910,
    genres: ['Animation', 'Fantasy', 'Adventure'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Sintel_poster.jpg/800px-Sintel_poster.jpg',
    backdropUrl: 'https://durian.blender.org/wp-content/uploads/2010/09/sintel_desktop.png',
    rating: 'PG',
    attribution: {
      licenseType: 'CC-BY-3.0',
      creator: 'Blender Foundation & Ton Roosendaal',
      sourceUrl: 'https://durian.blender.org',
      licenseUrl: 'https://creativecommons.org/licenses/by/3.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-001-hls',
        format: 'hls',
        url: 'https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
        resolution: 'auto',
        bitrateBps: 2500000,
        fps: 24,
        isHealthVerified: true
      },
      {
        id: 'src-001-mp4',
        format: 'mp4',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
        resolution: '1080p',
        bitrateBps: 3000000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [
      {
        id: 'sub-001-en',
        language: 'en',
        label: 'English [CC]',
        src: 'https://durian.blender.org/subtitles/sintel_en.vtt',
        isDefault: true
      },
      {
        id: 'sub-001-es',
        language: 'es',
        label: 'Spanish',
        src: 'https://durian.blender.org/subtitles/sintel_es.vtt',
        isDefault: false
      }
    ],
    isFeatured: true,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-002',
    title: 'Tears of Steel',
    slug: 'tears-of-steel-2012',
    description: 'Set in a dystopian future Amsterdam, a group of warriors and scientists gather at the Oude Kerk to stage a crucial event from the past in a desperate bid to rescue the world from rampaging destructive robots.',
    releaseYear: 2012,
    durationSeconds: 734,
    genres: ['Sci-Fi', 'Action', 'VFX'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Tears_of_Steel_poster.jpg/800px-Tears_of_Steel_poster.jpg',
    backdropUrl: 'https://mango.blender.org/wp-content/uploads/2012/09/01_thom_celia_bridge.jpg',
    rating: 'PG-13',
    attribution: {
      licenseType: 'CC-BY-3.0',
      creator: 'Blender Foundation & Ian Hubert',
      sourceUrl: 'https://mango.blender.org',
      licenseUrl: 'https://creativecommons.org/licenses/by/3.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-002-hls',
        format: 'hls',
        url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
        resolution: 'auto',
        bitrateBps: 4500000,
        fps: 24,
        isHealthVerified: true
      },
      {
        id: 'src-002-mp4',
        format: 'mp4',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
        resolution: '1080p',
        bitrateBps: 4000000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [
      {
        id: 'sub-002-en',
        language: 'en',
        label: 'English',
        src: 'https://mango.blender.org/subtitles/tos_en.vtt',
        isDefault: true
      }
    ],
    isFeatured: true,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-003',
    title: 'Big Buck Bunny',
    slug: 'big-buck-bunny-2008',
    description: 'A large and lovable rabbit deals with bullying forest creatures in this groundbreaking open-source 3D animated comedy.',
    releaseYear: 2008,
    durationSeconds: 596,
    genres: ['Animation', 'Comedy', 'Family'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/800px-Big_buck_bunny_poster_big.jpg',
    backdropUrl: 'https://peach.blender.org/wp-content/uploads/bbb-splash.png',
    rating: 'G',
    attribution: {
      licenseType: 'CC-BY-3.0',
      creator: 'Blender Foundation & Sacha Goedegebure',
      sourceUrl: 'https://peach.blender.org',
      licenseUrl: 'https://creativecommons.org/licenses/by/3.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-003-hls',
        format: 'hls',
        url: 'https://test-streams.mux.dev/x36xhzz/url_0/1920_1080/index.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        resolution: 'auto',
        bitrateBps: 2000000,
        fps: 60,
        isHealthVerified: true
      },
      {
        id: 'src-003-mp4',
        format: 'mp4',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        resolution: '1080p',
        bitrateBps: 2500000,
        fps: 60,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: false,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-004',
    title: 'Cosmos Laundromat',
    slug: 'cosmos-laundromat-2015',
    description: 'On a desolate island, a suicidal sheep named Franck meets a quirky salesman who offers him the gift of a lifetime: a chance to live all the lives he never had through an otherworldly laundromat.',
    releaseYear: 2015,
    durationSeconds: 730,
    genres: ['Animation', 'Fantasy', 'Drama'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Cosmos_Laundromat_-_First_Cycle_-_Poster.png/800px-Cosmos_Laundromat_-_First_Cycle_-_Poster.png',
    backdropUrl: 'https://gooseberry.blender.org/wp-content/uploads/2015/08/CosmosLaundromat_screen_01.jpg',
    rating: 'PG-13',
    attribution: {
      licenseType: 'CC-BY-4.0',
      creator: 'Blender Institute & Mathieu Auvray',
      sourceUrl: 'https://gooseberry.blender.org',
      licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-004-hls',
        format: 'hls',
        url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4',
        resolution: 'auto',
        bitrateBps: 3500000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: false,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-005',
    title: 'Night of the Living Dead',
    slug: 'night-of-the-living-dead-1968',
    description: 'A ragtag group of Pennsylvanians barricade themselves in an old farmhouse to remain safe from a bloodthirsty, flesh-eating breed of reanimated corpses. The seminal masterwork that founded modern horror cinema.',
    releaseYear: 1968,
    durationSeconds: 5760,
    genres: ['Horror', 'Classic', 'Mystery'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Night_of_the_Living_Dead_%281968%29_theatrical_poster.jpg/800px-Night_of_the_Living_Dead_%281968%29_theatrical_poster.jpg',
    backdropUrl: 'https://ia800300.us.archive.org/27/items/night_of_the_living_dead/night_of_the_living_dead.thumbs/night_of_the_living_dead_000720.jpg',
    rating: 'Not Rated',
    attribution: {
      licenseType: 'Public Domain',
      creator: 'George A. Romero & John Russo',
      sourceUrl: 'https://archive.org/details/night_of_the_living_dead',
      licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-005-mp4',
        format: 'mp4',
        url: 'https://archive.org/download/night_of_the_living_dead/night_of_the_living_dead_512kb.mp4',
        backupUrl: 'https://ia800300.us.archive.org/27/items/night_of_the_living_dead/night_of_the_living_dead.mp4',
        resolution: '720p',
        bitrateBps: 1800000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [
      {
        id: 'sub-005-en',
        language: 'en',
        label: 'English Subtitles',
        src: 'https://archive.org/download/night_of_the_living_dead/notld_en.vtt',
        isDefault: true
      }
    ],
    isFeatured: true,
    category: 'Public Domain Classics',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-006',
    title: 'Metropolis',
    slug: 'metropolis-1927',
    description: 'In a futuristic city sharply divided between the working class and the city planners, the son of the city mastermind falls in love with a working-class prophet who predicts the coming of a savior to mediate their differences.',
    releaseYear: 1927,
    durationSeconds: 9180,
    genres: ['Sci-Fi', 'Classic', 'Drama'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Metropolisposter.jpg/800px-Metropolisposter.jpg',
    backdropUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Metropolis_1927_still.jpg/1280px-Metropolis_1927_still.jpg',
    rating: 'Not Rated',
    attribution: {
      licenseType: 'Public Domain',
      creator: 'Fritz Lang & Thea von Harbou (UFA)',
      sourceUrl: 'https://archive.org/details/Metropolis_1927',
      licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-006-mp4',
        format: 'mp4',
        url: 'https://archive.org/download/Metropolis_1927/Metropolis_1927_512kb.mp4',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackSeeTheWorld.mp4',
        resolution: '720p',
        bitrateBps: 1500000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: false,
    category: 'Public Domain Classics',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-007',
    title: 'Mars Perseverance: Seven Minutes of Terror',
    slug: 'nasa-mars-perseverance-landing',
    description: 'NASA entry, descent, and landing team documentary detailing the high-stakes atmospheric plunge and sky-crane landing of the Perseverance Rover on Mars Jezero Crater.',
    releaseYear: 2021,
    durationSeconds: 420,
    genres: ['Documentary', 'Science', 'Space'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/PIA24427-MarsPerseveranceRover-Landing-20210218.jpg/800px-PIA24427-MarsPerseveranceRover-Landing-20210218.jpg',
    backdropUrl: 'https://images-assets.nasa.gov/image/PIA24427/PIA24427~orig.jpg',
    rating: 'G',
    attribution: {
      licenseType: 'Public Domain',
      creator: 'NASA / Jet Propulsion Laboratory (JPL-Caltech)',
      sourceUrl: 'https://www.nasa.gov/perseverance',
      licenseUrl: 'https://www.nasa.gov/multimedia/guidelines/index.html',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-007-hls',
        format: 'hls',
        url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
        resolution: '1080p',
        bitrateBps: 3000000,
        fps: 30,
        isHealthVerified: true
      }
    ],
    subtitles: [
      {
        id: 'sub-007-en',
        language: 'en',
        label: 'English Audio & CC',
        src: 'https://images-assets.nasa.gov/captions/perseverance.vtt',
        isDefault: true
      }
    ],
    isFeatured: true,
    category: 'NASA & Science',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-008',
    title: 'Spring',
    slug: 'spring-2019',
    description: 'A poetic fantasy about a young shepherd girl and her dog who face ancient spirits in order to continue the cycle of life. A breathtaking 3D animated masterwork by Blender Studio.',
    releaseYear: 2019,
    durationSeconds: 464,
    genres: ['Animation', 'Fantasy', 'Family'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Spring_-_Poster.png/800px-Spring_-_Poster.png',
    backdropUrl: 'https://durian.blender.org/wp-content/uploads/2010/09/sintel_desktop.png',
    rating: 'PG',
    attribution: {
      licenseType: 'CC-BY-4.0',
      creator: 'Blender Animation Studio & Andy Goralczyk',
      sourceUrl: 'https://spring.blender.org',
      licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-008-hls',
        format: 'hls',
        url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        resolution: 'auto',
        bitrateBps: 3500000,
        fps: 24,
        isHealthVerified: true
      },
      {
        id: 'src-008-mp4',
        format: 'mp4',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        resolution: '1080p',
        bitrateBps: 3500000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: true,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-009',
    title: 'Charge',
    slug: 'charge-2022',
    description: 'An old, battle-weary robot breaks into an abandoned battery manufacturing plant seeking a high-energy recharge, only to trigger the plant automated defense systems.',
    releaseYear: 2022,
    durationSeconds: 210,
    genres: ['Action', 'Sci-Fi', 'Cyberpunk'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Charge_open_movie_poster.png/800px-Charge_open_movie_poster.png',
    backdropUrl: 'https://mango.blender.org/wp-content/uploads/2012/09/01_thom_celia_bridge.jpg',
    rating: 'PG-13',
    attribution: {
      licenseType: 'CC-BY-4.0',
      creator: 'Blender Studio & Hjalti Hjalmarsson',
      sourceUrl: 'https://studio.blender.org/films/charge/',
      licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-009-mp4',
        format: 'mp4',
        url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
        backupUrl: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        resolution: '1080p',
        bitrateBps: 4000000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: false,
    category: 'Blender Open Movies',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-010',
    title: 'The General',
    slug: 'the-general-1926',
    description: 'During the American Civil War, railroad engineer Johnnie Gray is rejected by the military. When enemy spies steal his beloved locomotive, he embarks on an unrelenting solo pursuit behind enemy lines.',
    releaseYear: 1926,
    durationSeconds: 4680,
    genres: ['Action', 'Adventure', 'Comedy', 'Classic'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/The_General_1926.jpg/800px-The_General_1926.jpg',
    backdropUrl: 'https://ia800300.us.archive.org/27/items/night_of_the_living_dead/night_of_the_living_dead.thumbs/night_of_the_living_dead_000720.jpg',
    rating: 'Passed',
    attribution: {
      licenseType: 'Public Domain',
      creator: 'Buster Keaton & Clyde Bruckman (United Artists)',
      sourceUrl: 'https://archive.org/details/TheGeneralBusterKeaton1926',
      licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-010-mp4',
        format: 'mp4',
        url: 'https://archive.org/download/TheGeneralBusterKeaton1926/TheGeneralBusterKeaton1926_512kb.mp4',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackSeeTheWorld.mp4',
        resolution: '720p',
        bitrateBps: 1800000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: true,
    category: 'Public Domain Classics',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  },
  {
    id: 'media-011',
    title: 'A Trip to the Moon',
    slug: 'a-trip-to-the-moon-1902',
    description: 'A group of intrepid Victorian astronomers journey to the moon in a cannon-propelled capsule, explore the lunar surface, and escape from underground Selenites in the founding masterpiece of science fiction cinema.',
    releaseYear: 1902,
    durationSeconds: 840,
    genres: ['Sci-Fi', 'Classic', 'Fantasy'],
    posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Le_Voyage_dans_la_lune.jpg/800px-Le_Voyage_dans_la_lune.jpg',
    backdropUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Metropolis_1927_still.jpg/1280px-Metropolis_1927_still.jpg',
    rating: 'Passed',
    attribution: {
      licenseType: 'Public Domain',
      creator: 'Georges Méliès (Star Film)',
      sourceUrl: 'https://archive.org/details/trip_to_the_moon',
      licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/',
      verificationDate: '2026-09-19T00:00:00Z'
    },
    sources: [
      {
        id: 'src-011-mp4',
        format: 'mp4',
        url: 'https://archive.org/download/night_of_the_living_dead/night_of_the_living_dead_512kb.mp4',
        backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
        resolution: '1080p',
        bitrateBps: 2000000,
        fps: 24,
        isHealthVerified: true
      }
    ],
    subtitles: [],
    isFeatured: false,
    category: 'Public Domain Classics',
    status: 'active',
    createdAt: '2026-09-19T00:00:00Z',
    updatedAt: '2026-09-19T00:00:00Z'
  }
];

