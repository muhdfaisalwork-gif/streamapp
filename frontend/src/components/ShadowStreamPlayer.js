import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    View, Text, StyleSheet, TouchableOpacity,
    Platform, ActivityIndicator, useWindowDimensions, ScrollView
} from 'react-native';
import Hls from 'hls.js';
import { COLORS } from '../theme/colors';
import { availablePlayers } from '../utils/externalPlayer';

// Common ISO 639-1 language code to readable name mapping
const LANGUAGE_NAMES = {
    en: 'English',
    ja: 'Japanese',
    hi: 'Hindi',
    ur: 'Urdu',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    ko: 'Korean',
    zh: 'Chinese',
    ar: 'Arabic',
    it: 'Italian',
    pt: 'Portuguese',
    ru: 'Russian',
    tr: 'Turkish',
    ta: 'Tamil',
    te: 'Telugu',
    bn: 'Bengali',
    id: 'Indonesian',
    tl: 'Tagalog',
    th: 'Thai',
    vi: 'Vietnamese',
    fa: 'Persian',
    pa: 'Punjabi',
};

const COMMON_DUBS = [
    { code: 'en', label: 'English' },
    { code: 'ja', label: 'Japanese' },
    { code: 'hi', label: 'Hindi' },
    { code: 'es', label: 'Spanish' },
    { code: 'fr', label: 'French' },
    { code: 'de', label: 'German' },
    { code: 'ur', label: 'Urdu' },
    { code: 'ar', label: 'Arabic' },
    { code: 'ko', label: 'Korean' },
];

function normalizeDub(d) {
    if (!d) return null;
    if (typeof d === 'string') {
        const code = d.toLowerCase().trim();
        return {
            code,
            label: LANGUAGE_NAMES[code] || code.toUpperCase(),
        };
    }
    const code = String(d.code || d.iso || d.language || '').toLowerCase().trim();
    const label = d.label || d.name || LANGUAGE_NAMES[code] || (code ? code.toUpperCase() : 'Unknown');
    return { code, label };
}

// Helper to format seconds into HH:MM:SS or MM:SS
function formatTime(seconds) {
    if (!seconds || isNaN(seconds) || seconds < 0) return '00:00';
    const s = Math.floor(seconds);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    if (hrs > 0) {
        return `${hrs}:${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

export default function ShadowStreamPlayer({
    title,
    season,
    episode,
    streamUrl,
    streamKind = 'direct', // 'direct' = our HLS/MP4 engine, 'embed' = sandboxed provider iframe
    sourceName = 'ShadowStream Ultra HD',
    seasons = [],
    mirrorList = [],
    activeMirrorIdx = 0,
    subtitles = [],
    dubs = [],
    onSelectMirror,
    onSelectEpisode,
    onNextEpisode,
    onBack,
    mediaId,
    notice = null,
    posterUrl = null,
    renditions = [],
    onSelectRendition,
}) {
    const { width, height } = useWindowDimensions();
    const isMobile = width < 768;

    // Our own decoder is only in play for a resolved direct stream. Every other
    // provider renders inside a sandboxed iframe, but the chrome around it —
    // back, title, server switcher, episode drawer — is still ours in both modes.
    const isDirect = streamKind === 'direct';

    // --- Crop / stretch ------------------------------------------------------
    //
    // 'fit'     whole frame, letterboxed (never distorts)
    // 'fill'    crop the edges to remove black bars
    // 'stretch' force the frame to the container, distorting it
    //
    // Direct mode owns the <video>, so this is just objectFit. Embed mode does not:
    // the picture belongs to the provider page inside a cross-origin iframe and
    // cannot be reached. There we transform the frame itself, which crops and
    // stretches the picture just the same. ASSUMED_ASPECT is the ratio we assume
    // the provider renders at, since we cannot measure inside the frame.
    const ASSUMED_ASPECT = 16 / 9;
    const [viewMode, setViewMode] = useState('fit');
    const [frameSize, setFrameSize] = useState({ w: 0, h: 0 });

    const embedTransform = useMemo(() => {
        if (isDirect || viewMode === 'fit' || !frameSize.w || !frameSize.h) return null;
        const { w, h } = frameSize;
        const sx = w / (h * ASSUMED_ASPECT);
        const sy = h / (w / ASSUMED_ASPECT);
        if (viewMode === 'fill') {
            const k = Math.max(sx, sy, 1);
            return { transform: `scale(${k})` };
        }
        return { transform: `scale(${sx}, ${sy})` };
    }, [isDirect, viewMode, frameSize]);

    const videoObjectFit = viewMode === 'fill' ? 'cover' : viewMode === 'stretch' ? 'fill' : 'contain';

    const nextViewMode = useCallback(() => {
        setViewMode((m) => (m === 'fit' ? 'fill' : m === 'fill' ? 'stretch' : 'fit'));
    }, []);
    const VIEW_LABEL = { fit: 'Fit', fill: 'Crop', stretch: 'Stretch' };

    // Video & Playback State
    const videoRef = useRef(null);
    const iframeRef = useRef(null);
    const hlsRef = useRef(null);
    const containerRef = useRef(null);
    const cssFullscreenRef = useRef(false);
    const autoHideTimerRef = useRef(null);
    const bingeTimerRef = useRef(null);

    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [buffered, setBuffered] = useState(0);
    const [isBuffering, setIsBuffering] = useState(false);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [playbackRate, setPlaybackRate] = useState(1);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [fullscreenNote, setFullscreenNote] = useState(null);

    // Overlay & UI State
    const [controlsVisible, setControlsVisible] = useState(true);
    const [hoverTime, setHoverTime] = useState(null);
    const [hoverPos, setHoverPos] = useState(null);
    const [showSpeedMenu, setShowSpeedMenu] = useState(false);
    const [showQualityMenu, setShowQualityMenu] = useState(false);
    const [showSubtitleMenu, setShowSubtitleMenu] = useState(false);
    const [showDubMenu, setShowDubMenu] = useState(false);
    const [availableAudioTracks, setAvailableAudioTracks] = useState([]);
    const [showServerMenu, setShowServerMenu] = useState(false);
    const [showLoadServerMenu, setShowLoadServerMenu] = useState(false);
    const [showPlayerMenu, setShowPlayerMenu] = useState(false);
    const [playerHandoffFailed, setPlayerHandoffFailed] = useState(false);
    const playerApps = availablePlayers();

    // Embed failover.
    //
    // A cross-origin iframe gives us almost no signal: if a provider is down
    // or has changed its page, the frame either loads a dead page or a broken
    // player, and we cannot read inside it. What we can do is notice that it
    // loaded and then never became interactive, and offer the next mirror in
    // one tap rather than leaving the user on a black rectangle.
    const [embedState, setEmbedState] = useState('loading'); // loading | ready | stalled
    const embedTimer = useRef(null);

    const handleEmbedLoaded = useCallback(() => {
        setEmbedState('ready');
        if (embedTimer.current) { clearTimeout(embedTimer.current); embedTimer.current = null; }
    }, []);

    const handleEmbedFailed = useCallback(() => {
        setEmbedState('stalled');
    }, []);

    // Reset the watchdog whenever the active mirror changes.
    useEffect(() => {
        setEmbedState('loading');
        if (embedTimer.current) clearTimeout(embedTimer.current);
        embedTimer.current = setTimeout(() => {
            setEmbedState((prev) => (prev === 'loading' ? 'stalled' : prev));
        }, 6000);
        return () => { if (embedTimer.current) clearTimeout(embedTimer.current); };
    }, [streamUrl]);

    const tryNextMirror = useCallback(() => {
        if (!mirrorList || mirrorList.length < 2) return;
        setPlayerHandoffFailed(false);
        const next = (activeMirrorIdx + 1) % mirrorList.length;
        if (onSelectMirror) onSelectMirror(mirrorList[next], next);
    }, [mirrorList, activeMirrorIdx, onSelectMirror]);

    // True while the provider has not finished handing us a playable frame.
    // Covers both paths: our own decoder buffering, and the cross-origin
    // iframe still loading.
    //
    // The iframe's onLoad is NOT a readiness signal. Verified two ways: on Slow
    // 3G it fired while the provider was still showing "FETCHING DATA, PLEASE
    // WAIT", and with the network cut it fired for a chrome-error "No
    // internet" page. Neither tells us a frame ever arrived, and because the
    // frame is cross-origin we cannot read inside it to check. So the line is
    // driven by a fixed window on every source change rather than by a lie the
    // browser tells us.
    const [minLoading, setMinLoading] = useState(true);
    useEffect(() => {
        setMinLoading(true);
        // 6s matches the embed watchdog below so the two hand off cleanly: the
        // line owns the screen while we wait, the failover bar takes over the
        // instant we give up. Overlapping them put the failover bar (zIndex 35)
        // on top of this one (zIndex 30) and it swallowed the Change tap.
        const t = setTimeout(() => setMinLoading(false), 6000);
        return () => clearTimeout(t);
    }, [streamUrl]);

    // 'stalled' is deliberately excluded: that is the failover bar's job, and
    // showing both at once collided and blocked the Change button.
    const isLoadingContent = isDirect
        ? (isBuffering || minLoading)
        : (minLoading && embedState !== 'stalled');

    // The picker lives INSIDE this bar, so the bar has to outlive the 6s timer
    // once it is open — otherwise a menu opened at 5.9s unmounts itself a
    // tenth of a second later, mid-tap.
    const loadBarVisible = isLoadingContent || showLoadServerMenu;

    // Elapsed seconds, so the line says "Loading… 12s" instead of a spinner
    // that could mean anything. Resets every time the source changes.
    const [loadSeconds, setLoadSeconds] = useState(0);
    useEffect(() => {
        if (!isLoadingContent) {
            setLoadSeconds(0);
            return undefined;
        }
        setLoadSeconds(0);
        const t = setInterval(() => setLoadSeconds(s => s + 1), 1000);
        return () => clearInterval(t);
    }, [isLoadingContent, streamUrl]);

    // MUST be declared before the effect below reads it. It used to sit ~30
    // lines further down with the other player state, and because the effect's
    // DEPENDENCY ARRAY is evaluated during render, every mount hit the
    // temporal dead zone and threw "Cannot access 'selectedSubtitle' before
    // initialization" — which white-screened the entire player route. Hooks
    // that appear earlier in the body must not depend on state declared later.
    const [selectedSubtitle, setSelectedSubtitle] = useState('off');

    // Apply the chosen subtitle to the real media element.
    //
    // The menu sets `selectedSubtitle`, but without this the <video> keeps
    // showing whatever the browser picked by default — which is why the
    // Subtitles control looked like it did nothing.
    useEffect(() => {
        if (!isDirect) return;
        const video = videoRef.current;
        if (!video || !video.textTracks) return;

        const wanted = selectedSubtitle;
        for (let i = 0; i < video.textTracks.length; i++) {
            const t = video.textTracks[i];
            const match = wanted !== 'off' && (t.language === wanted || t.label === wanted);
            t.mode = match ? 'showing' : 'disabled';
        }
    }, [selectedSubtitle, isDirect, streamUrl, subtitles.length]);

    // Expose the Subtitle menu on embed too, but make it honest: the provider
    // owns the track list there, so we only show the hint.
    const canSelectSubtitles = isDirect && Array.isArray(subtitles) && subtitles.length > 0;

    // Dub (audio language) picker — combines detected title dubs with common options
    const normalizedDubs = useMemo(() => {
        if (!Array.isArray(dubs)) return [];
        return dubs.map(normalizeDub).filter(Boolean);
    }, [dubs]);

    const availableDubs = useMemo(() => {
        const seen = new Set();
        const list = [];
        for (const d of normalizedDubs) {
            if (!seen.has(d.code)) {
                seen.add(d.code);
                list.push(d);
            }
        }
        for (const c of COMMON_DUBS) {
            if (!seen.has(c.code)) {
                seen.add(c.code);
                list.push(c);
            }
        }
        return list;
    }, [normalizedDubs]);

    // Dead code removed deliberately.
    //
    // This used to build `<iframe src={streamUrl}&lang=<code>>` when a dub was
    // picked. It never worked. `lang` is not a parameter VidLink recognises —
    // its API takes `multiLang`, and that flag only governs SUBTITLES: the
    // response for this title is byte-identical with multiLang=0 and multiLang=1,
    // and contains no audio track array at all, just one file per resolution.
    // The picker was a menu that could not change anything.
    //
    // Real audio switching is possible in exactly one mode: direct, where the
    // <video> is ours and hls.js exposes the manifest's audio tracks. Embed mode
    // has no handle on the track list. See AUDIO_TRACKS below.

    const [activeAudioIdx, setActiveAudioIdx] = useState(0);

    const selectAudioTrack = useCallback((idx) => {
        setActiveAudioIdx(idx);
        const hls = hlsRef.current;
        if (hls && Array.isArray(hls.audioTracks) && hls.audioTracks.length) {
            hls.audioTrack = idx;
            return;
        }
        // Progressive MP4: only a handful of browsers expose audioTracks.
        const video = videoRef.current;
        if (video && video.audioTracks && video.audioTracks.length) {
            for (let i = 0; i < video.audioTracks.length; i++) {
                video.audioTracks[i].enabled = i === idx;
            }
        }
    }, []);

    const setAudioTrackList = useCallback((tracks) => {
        setAvailableAudioTracks(tracks);
        setActiveAudioIdx(0);
    }, []);

    // The provider notice is informational, not an error. Fade it out after a
    // few seconds so it never sits over the video like a stuck subtitle.
    const [noticeVisible, setNoticeVisible] = useState(true);
    useEffect(() => {
        setNoticeVisible(true);
        if (!notice && !playerHandoffFailed) return undefined;
        const t = setTimeout(() => setNoticeVisible(false), 4000);
        return () => clearTimeout(t);
    }, [notice, playerHandoffFailed, streamUrl]);
    const [showEpisodeDrawer, setShowEpisodeDrawer] = useState(false);
    const [activeDrawerSeason, setActiveDrawerSeason] = useState(season || 1);

    // The drawer's highlighted season used to be seeded once and then never
    // followed the player, so switching episode by any other route (Next
    // Episode, deep link) left the drawer on a stale season.
    useEffect(() => {
        if (season != null) setActiveDrawerSeason(season);
    }, [season]);

    // Season rows as the API actually returns them. Episodes carry no
    // `season_number` of their own, so the season has to be resolved from the
    // row that owns them. Episodes from different titles vary, so tolerate the
    // field being present as a fallback.
    const drawerSeasons = Array.isArray(seasons) ? seasons.filter(s => s && s.season_number != null) : [];
    const drawerActiveSeasonRow =
        drawerSeasons.find(s => s.season_number === activeDrawerSeason) || drawerSeasons[0] || null;
    const drawerActiveSeasonNumber = drawerActiveSeasonRow ? drawerActiveSeasonRow.season_number : (season || 1);
    const drawerEpisodes = (drawerActiveSeasonRow && Array.isArray(drawerActiveSeasonRow.episodes))
        ? drawerActiveSeasonRow.episodes.filter(ep => ep && ep.episode_number != null)
        : [];

    // HLS Quality levels
    const [qualityLevels, setQualityLevels] = useState([]);
    const [activeQualityIdx, setActiveQualityIdx] = useState(-1); // -1 = auto

    // Binge Next Episode state
    const [showBingeCard, setShowBingeCard] = useState(false);
    const [bingeCountdown, setBingeCountdown] = useState(10);
    const [bingeDismissed, setBingeDismissed] = useState(false);

    // Find next episode info
    const currentSeasonObj = seasons.find(s => s.season_number === (season || 1)) || seasons[0];
    const episodeList = currentSeasonObj?.episodes || [];
    const currentEpIdx = episodeList.findIndex(e => e.episode_number === episode);
    const hasNextEp = currentEpIdx !== -1 && currentEpIdx < episodeList.length - 1;
    const nextEpObj = hasNextEp ? episodeList[currentEpIdx + 1] : null;

    // Reset auto-hide timer for controls
    const resetAutoHide = useCallback(() => {
        setControlsVisible(true);
        if (autoHideTimerRef.current) {
            clearTimeout(autoHideTimerRef.current);
        }
        // Keep visible if paused or modal open
        if (!isPlaying || showSpeedMenu || showQualityMenu || showSubtitleMenu || showServerMenu || showEpisodeDrawer) {
            return;
        }
        autoHideTimerRef.current = setTimeout(() => {
            setControlsVisible(false);
        }, 3000);
    }, [isPlaying, showSpeedMenu, showQualityMenu, showSubtitleMenu, showServerMenu, showEpisodeDrawer]);

    // Handle Play / Pause
    const togglePlay = useCallback(() => {
        if (!videoRef.current) return;
        if (videoRef.current.paused) {
            videoRef.current.play().catch(e => console.warn('Play error:', e));
            setIsPlaying(true);
        } else {
            videoRef.current.pause();
            setIsPlaying(false);
        }
        resetAutoHide();
    }, [resetAutoHide]);

    // Seek by delta seconds
    const seekRelative = useCallback((delta) => {
        if (!videoRef.current) return;
        const newTime = Math.max(0, Math.min(videoRef.current.duration || 0, videoRef.current.currentTime + delta));
        videoRef.current.currentTime = newTime;
        setCurrentTime(newTime);
        resetAutoHide();
    }, [resetAutoHide]);

    // Set Volume
    const handleVolumeChange = useCallback((newVol) => {
        if (!videoRef.current) return;
        const clamped = Math.max(0, Math.min(1, newVol));
        videoRef.current.volume = clamped;
        setVolume(clamped);
        if (clamped === 0) {
            videoRef.current.muted = true;
            setIsMuted(true);
        } else if (isMuted) {
            videoRef.current.muted = false;
            setIsMuted(false);
        }
    }, [isMuted]);

    // Toggle Mute
    const toggleMute = useCallback(() => {
        if (!videoRef.current) return;
        const nextMute = !videoRef.current.muted;
        videoRef.current.muted = nextMute;
        setIsMuted(nextMute);
    }, []);

    // Set Playback Speed
    const handleSetRate = useCallback((rate) => {
        if (!videoRef.current) return;
        videoRef.current.playbackRate = rate;
        setPlaybackRate(rate);
        setShowSpeedMenu(false);
    }, []);

    // Set Quality Level
    const handleSetQuality = useCallback((idx) => {
        const lvl = qualityLevels[idx];
        if (lvl && lvl.isRendition) {
            const opt = (renditions || [])[idx];
            if (!opt) return;
            if (opt.browserPlayable === false) {
                // e.g. an .mkv original — a browser cannot decode it, so this
                // is a download, not a playback switch.
                if (typeof window !== 'undefined' && opt.url) window.open(opt.url, '_blank');
                setShowQualityMenu(false);
                return;
            }
            const video = videoRef.current;
            const wasPlaying = video && !video.paused ? video.currentTime : 0;
            if (video) {
                video.src = opt.url;
                video.load();
                if (wasPlaying) {
                    video.currentTime = wasPlaying;
                    video.play().catch(() => {});
                }
            }
            setActiveQualityIdx(idx);
            setShowQualityMenu(false);
            return;
        }
        if (hlsRef.current) {
            hlsRef.current.currentLevel = idx; // -1 for auto
            setActiveQualityIdx(idx);
        }
        setShowQualityMenu(false);
    }, []);

    // Fullscreen Toggle
    //
    // Three separate things used to break here, so the ladder is explicit:
    //
    // 1. iPhone Safari has no element fullscreen at all. `requestFullscreen()` on a
    //    <div> is simply absent there (Safari unprefixed it on macOS/iPadOS in 16.4,
    //    never on iPhone). The old code called `target.requestFullscreen().catch(warn)`,
    //    which silently did nothing on every phone.
    // 2. The only element iOS *will* fullscreen is a <video>, via webkitEnterFullscreen.
    // 3. Some browsers support none of it. A CSS fullscreen (fixed, 100vw/100vh, escaped
    //    out of the scroll containers) is the last resort so the button is never dead.
    const requestElementFullscreen = useCallback((el) => {
        if (!el) return false;
        try {
            if (typeof el.requestFullscreen === 'function') {
                el.requestFullscreen({ navigationUI: 'hide' }).catch(() => {});
                return true;
            }
            if (typeof el.webkitRequestFullscreen === 'function') {
                el.webkitRequestFullscreen();
                return true;
            }
        } catch (e) {
            return false;
        }
        return false;
    }, []);

    const toggleFullscreen = useCallback(() => {
        if (Platform.OS !== 'web' || typeof document === 'undefined') return;

        const video = videoRef.current;
        const frame = iframeRef.current;
        const elementFsSupported =
            typeof document.documentElement.requestFullscreen === 'function' ||
            typeof document.documentElement.webkitRequestFullscreen === 'function';

        setFullscreenNote(null);

        // --- Exit ------------------------------------------------------------
        // iOS video fullscreen is invisible to document.fullscreenElement, so it has to
        // be checked first or the exit path never runs on a phone.
        if (video && video.webkitDisplayingFullscreen) {
            if (typeof video.webkitExitFullscreen === 'function') video.webkitExitFullscreen();
            else setIsFullscreen(false);
            return;
        }
        if (document.fullscreenElement) {
            if (typeof document.exitFullscreen === 'function') document.exitFullscreen().catch(() => {});
            else if (typeof document.webkitExitFullscreen === 'function') document.webkitExitFullscreen();
            else setIsFullscreen(false);
            return;
        }
        // CSS fallback is holding the screen — nothing in the document API to exit.
        if (cssFullscreenRef.current) {
            cssFullscreenRef.current = false;
            setIsFullscreen(false);
            return;
        }

        // --- Enter ------------------------------------------------------------
        if (isDirect) {
            // Container keeps our custom controls (seek, quality, subtitles, server switcher).
            if (elementFsSupported && requestElementFullscreen(containerRef.current)) return;
            // iPhone: the video element is the only thing that can go fullscreen.
            if (video && typeof video.webkitEnterFullscreen === 'function') {
                video.webkitEnterFullscreen();
                return;
            }
        } else {
            // Embed mode: fullscreen OUR container, not the provider frame.
            // The iframe already fills 100%x100%, so it looks identical — but the
            // top bar (and therefore the exit button) stays on top and reachable.
            // Putting the iframe itself in fullscreen buries our own chrome behind
            // it, and a touch user has no Esc key to get back out.
            if (elementFsSupported && requestElementFullscreen(containerRef.current)) return;
            if (elementFsSupported && requestElementFullscreen(frame)) return;
            if (frame && typeof frame.webkitRequestFullscreen === 'function') {
                frame.webkitRequestFullscreen();
                return;
            }
            setFullscreenNote(isMobile
                ? 'iPhone only fullscreens the video itself — use the player inside the frame.'
                : 'Provider blocked fullscreen — using app fullscreen.');
        }

        // Universal fallback: pure CSS fullscreen. Works everywhere, needs no API.
        cssFullscreenRef.current = true;
        setIsFullscreen(true);
    }, [isDirect, isMobile, requestElementFullscreen]);

    // Clear the fallback notice on its own — it is a hint, not a permanent banner.
    useEffect(() => {
        if (!fullscreenNote) return undefined;
        const t = setTimeout(() => setFullscreenNote(null), 5000);
        return () => clearTimeout(t);
    }, [fullscreenNote]);

    // Fullscreen change listener
    //
    // cssFullscreenRef tracks whether our CSS fallback is what is currently holding
    // the screen, because that mode never touches document.fullscreenElement. Without
    // that distinction the exit event cannot tell "user left fullscreen" from "CSS
    // fallback still on", and the toggle icon goes stale.
    useEffect(() => {
        if (Platform.OS !== 'web') return undefined;

        const onFsChange = () => {
            const active = Boolean(document.fullscreenElement || document.webkitFullscreenElement);
            if (active) {
                cssFullscreenRef.current = false;
                setIsFullscreen(true);
                return;
            }
            if (!cssFullscreenRef.current) setIsFullscreen(false);
        };
        document.addEventListener('fullscreenchange', onFsChange);
        document.addEventListener('webkitfullscreenchange', onFsChange);
        return () => {
            document.removeEventListener('fullscreenchange', onFsChange);
            document.removeEventListener('webkitfullscreenchange', onFsChange);
        };
    }, []);

    // iOS video fullscreen fires its own events and never touches document.*.
    // Keyed on isDirect because the <video> only exists in direct mode.
    useEffect(() => {
        if (Platform.OS !== 'web' || !isDirect) return undefined;
        const video = videoRef.current;
        if (!video) return undefined;
        const onBegin = () => setIsFullscreen(true);
        const onEnd = () => setIsFullscreen(false);
        video.addEventListener('webkitbeginfullscreen', onBegin);
        video.addEventListener('webkitendfullscreen', onEnd);
        return () => {
            video.removeEventListener('webkitbeginfullscreen', onBegin);
            video.removeEventListener('webkitendfullscreen', onEnd);
        };
    }, [isDirect, streamUrl]);

    // NOTE: the global window.open guard lives in src/utils/adShield.js and is
    // installed once by App.js. This component used to install a second,
    // stricter override that blocked every popup including the app's own —
    // the duplicate is gone. The iframe `sandbox` attribute below is the
    // actual popup defence.

    // Restore saved playback position
    const storageKey = `shadowstream_pos_${mediaId || title}_s${season || 1}_e${episode || 1}`;
    useEffect(() => {
        if (Platform.OS === 'web' && typeof localStorage !== 'undefined') {
            try {
                const saved = localStorage.getItem(storageKey);
                if (saved && videoRef.current) {
                    const pos = parseFloat(saved);
                    if (pos > 10) {
                        videoRef.current.currentTime = pos;
                    }
                }
            } catch (_) {}
        }
    }, [storageKey, streamUrl]);

    // Save playback position periodically
    useEffect(() => {
        if (Platform.OS !== 'web' || typeof localStorage === 'undefined') return;
        if (currentTime > 5 && duration > 0 && currentTime < duration - 10) {
            try {
                localStorage.setItem(storageKey, String(Math.floor(currentTime)));
            } catch (_) {}
        }
    }, [currentTime, duration, storageKey]);

    // Keyboard Shortcuts
    useEffect(() => {
        if (Platform.OS !== 'web') return;
        const handleKeyDown = (e) => {
            // Ignore if active element is an input
            if (['input', 'textarea'].includes(document.activeElement?.tagName?.toLowerCase())) return;

            switch (e.key) {
                case ' ':
                case 'k':
                case 'K':
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'ArrowLeft':
                case 'j':
                case 'J':
                    e.preventDefault();
                    seekRelative(-10);
                    break;
                case 'ArrowRight':
                case 'l':
                case 'L':
                    e.preventDefault();
                    seekRelative(10);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    handleVolumeChange(volume + 0.1);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    handleVolumeChange(volume - 0.1);
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    toggleMute();
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    toggleFullscreen();
                    break;
                case 'n':
                case 'N':
                    e.preventDefault();
                    if (hasNextEp && onNextEpisode) onNextEpisode();
                    break;
                case 'Escape':
                    setShowSpeedMenu(false);
                    setShowQualityMenu(false);
                    setShowSubtitleMenu(false);
                    setShowServerMenu(false);
                    setShowEpisodeDrawer(false);
                    break;
                default:
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [togglePlay, seekRelative, handleVolumeChange, volume, toggleMute, toggleFullscreen, hasNextEp, onNextEpisode]);

    // Setup Video Engine (HLS or native MP4) — our own decoder, direct mode only.
    useEffect(() => {
        if (Platform.OS !== 'web' || streamKind !== 'direct' || !streamUrl) return;

        const video = videoRef.current;
        if (!video) return;

        setIsBuffering(true);

        const isHlsStream = streamUrl.includes('.m3u8') || streamUrl.includes('application/x-mpegURL');

        if (!isHlsStream) {
            // Progressive files have no HLS manifest, so no levels ever arrive
            // and the quality menu stayed empty even when the source shipped
            // several encodes. Fall back to the renditions recorded for the
            // title; selecting one swaps the media source.
            setQualityLevels(
                Array.isArray(renditions) && renditions.length > 1
                    ? renditions.map((r, idx) => ({
                        idx,
                        label: r.label || `Option ${idx + 1}`,
                        bitrate: 0,
                        isRendition: true,
                        playable: r.browserPlayable !== false,
                    }))
                    : []
            );
        }

        if (isHlsStream && Hls.isSupported()) {
            if (hlsRef.current) {
                hlsRef.current.destroy();
            }

            const hls = new Hls({
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90,
            });

            hlsRef.current = hls;
            hls.loadSource(streamUrl);
            hls.attachMedia(video);

            hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
                setIsBuffering(false);
                const levels = data.levels.map((lvl, idx) => ({
                    idx,
                    height: lvl.height,
                    label: lvl.height ? `${lvl.height}p` : `Level ${idx + 1}`,
                    bitrate: Math.round(lvl.bitrate / 1000)
                }));
                setQualityLevels(levels);
                video.play().catch(() => {});

                // Alternate audio tracks ship in the manifest, so they only
                // exist once MANIFEST_PARSED has fired. This is the one and only
                // place in this player where a genuine audio choice is real.
                const audioTracks = (data.audioTracks || []).map((t, i) => ({
                    idx: i,
                    label: t.name || t.lang || t.groupId || `Track ${i + 1}`,
                    lang: t.lang || '',
                }));
                setAudioTrackList(audioTracks);
            });

            hls.on(Hls.Events.AUDIO_TRACK_SWITCHED, (event, data) => {
                setActiveAudioIdx(data.id);
            });

            hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
                setActiveQualityIdx(hls.autoLevelEnabled ? -1 : data.level);
            });

            hls.on(Hls.Events.ERROR, (event, data) => {
                if (data.fatal) {
                    switch (data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.warn('[ShadowStreamPlayer] Fatal network error, recovering...');
                            hls.startLoad();
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.warn('[ShadowStreamPlayer] Fatal media error, recovering...');
                            hls.recoverMediaError();
                            break;
                        default:
                            console.warn('[ShadowStreamPlayer] Fatal unrecoverable error:', data);
                            hls.destroy();
                            break;
                    }
                }
            });
        } else {
            // Direct MP4 or Safari Native HLS
            video.src = streamUrl;
            video.load();
            video.play().catch(() => {});
        }

        // HTML5 Video Event Listeners
        const onPlay = () => setIsPlaying(true);
        const onPause = () => setIsPlaying(false);
        const onWaiting = () => setIsBuffering(true);
        const onPlaying = () => setIsBuffering(false);
        const onTimeUpdate = () => {
            setCurrentTime(video.currentTime);
            if (video.buffered.length > 0) {
                setBuffered(video.buffered.end(video.buffered.length - 1));
            }
        };
        const onLoadedMetadata = () => {
            setDuration(video.duration);
            setIsBuffering(false);
        };
        const onEnded = () => {
            setIsPlaying(false);
            if (hasNextEp && onNextEpisode) {
                onNextEpisode();
            }
        };

        video.addEventListener('play', onPlay);
        video.addEventListener('pause', onPause);
        video.addEventListener('waiting', onWaiting);
        video.addEventListener('playing', onPlaying);
        video.addEventListener('timeupdate', onTimeUpdate);
        video.addEventListener('loadedmetadata', onLoadedMetadata);
        video.addEventListener('ended', onEnded);

        return () => {
            if (hlsRef.current) {
                hlsRef.current.destroy();
                hlsRef.current = null;
            }
            video.removeEventListener('play', onPlay);
            video.removeEventListener('pause', onPause);
            video.removeEventListener('waiting', onWaiting);
            video.removeEventListener('playing', onPlaying);
            video.removeEventListener('timeupdate', onTimeUpdate);
            video.removeEventListener('loadedmetadata', onLoadedMetadata);
            video.removeEventListener('ended', onEnded);
        };
    }, [streamUrl, streamKind, hasNextEp, onNextEpisode]);

    // Binge Next Episode Countdown Detection (45s before end)
    useEffect(() => {
        if (!hasNextEp || bingeDismissed || duration <= 60) return;

        if (currentTime >= duration - 45 && !showBingeCard) {
            setShowBingeCard(true);
            setBingeCountdown(10);

            let remaining = 10;
            bingeTimerRef.current = setInterval(() => {
                remaining -= 1;
                setBingeCountdown(remaining);
                if (remaining <= 0) {
                    clearInterval(bingeTimerRef.current);
                    setShowBingeCard(false);
                    if (onNextEpisode) onNextEpisode();
                }
            }, 1000);
        }

        return () => {
            if (bingeTimerRef.current) clearInterval(bingeTimerRef.current);
        };
    }, [currentTime, duration, hasNextEp, bingeDismissed, showBingeCard, onNextEpisode]);

    // Scrubber click/drag handler
    const handleScrub = (e) => {
        if (!videoRef.current || duration <= 0) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const clientX = e.clientX || (e.touches && e.touches[0]?.clientX) || 0;
        const pos = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        const newTime = pos * duration;
        videoRef.current.currentTime = newTime;
        setCurrentTime(newTime);
        resetAutoHide();
    };

    // Scrubber hover preview
    const handleScrubHover = (e) => {
        if (duration <= 0) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        setHoverPos(pos * 100);
        setHoverTime(pos * duration);
    };

    return (
        <View
            ref={containerRef}
            style={[styles.container, isFullscreen && styles.containerFullscreen]}
            onMouseMove={resetAutoHide}
            onTouchStart={resetAutoHide}
            onLayout={(e) => {
                const { width: w, height: h } = e.nativeEvent.layout;
                setFrameSize((prev) => (prev.w === w && prev.h === h ? prev : { w, h }));
            }}
        >
            {/* Playback Area */}
            {isDirect ? (
                <div style={{ position: 'relative', width: '100%', height: '100%', backgroundColor: '#000000' }}>
                    <video
                        ref={videoRef}
                        playsInline
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: videoObjectFit,
                            backgroundColor: '#000000',
                            display: 'block',
                        }}
                    >
                        {/* Real subtitle tracks. These are what the Subtitles
                            menu switches between — previously the menu existed
                            and did nothing, because no <track> was ever added. */}
                        {subtitles.map((s) => (
                            <track
                                key={s.id || s.language}
                                kind="subtitles"
                                src={s.url}
                                srcLang={s.language}
                                label={s.label || s.language}
                                default={selectedSubtitle === s.language}
                            />
                        ))}
                    </video>
                </div>
            ) : (
                /* Embed Mode: the provider decodes, we keep the chrome.
                   The iframe is intentionally NOT sandboxed — providers refuse
                   to play inside one. Popup defence lives in adShield.js. */
                <View style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
                    <iframe
                        key={streamUrl}
                        ref={iframeRef}
                        src={streamUrl}
                        title="ShadowStream Built-in Player"
                        onLoad={handleEmbedLoaded}
                        onError={handleEmbedFailed}
                        style={{
                            width: '100%',
                            height: '100%',
                            border: 'none',
                            backgroundColor: '#000000',
                            // Crop / stretch for embed mode. transformOrigin is
                            // centred so cropping takes equal bites off both sides.
                            transform: embedTransform ? embedTransform.transform : 'none',
                            transformOrigin: 'center center',
                        }}
                        allowFullScreen
                        referrerPolicy="origin"
                        /*
                         * No sandbox attribute, deliberately.
                         *
                         * A strict sandbox made every provider render
                         * "Please Disable Sandbox" instead of the player, and
                         * widening it (allow-popups, allow-presentation, ...)
                         * did not help: vidlink rejects the *presence* of the attribute, not
                         * its contents. It was never much of a defence anyway —
                         * allow-scripts plus allow-same-origin lets a framed
                         * page strip its own sandbox.
                         *
                         * Popup and popunder abuse is handled one level up by
                         * src/utils/adShield.js, which owns the global
                         * window.open override and allow-lists only
                         * first-party origins.
                         */
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
                    />
                </View>
            )}

            {/* In-Player Episode Drawer */}
            {showEpisodeDrawer && (
                <View style={styles.episodeDrawer}>
                    <View style={styles.drawerHeader}>
                        <Text style={styles.drawerTitle}>Seasons & Episodes</Text>
                        <TouchableOpacity
                            style={styles.drawerCloseBtn}
                            onPress={() => setShowEpisodeDrawer(false)}
                        >
                            <Text style={styles.drawerCloseText}>✕</Text>
                        </TouchableOpacity>
                    </View>

                    {/* Season Tabs */}
                    {drawerSeasons.length > 1 && (
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.drawerSeasonTabs}>
                            {drawerSeasons.map(s => {
                                const active = s.season_number === drawerActiveSeasonNumber;
                                return (
                                    <TouchableOpacity
                                        key={s.season_number}
                                        style={[styles.drawerSeasonTab, active && styles.drawerSeasonTabActive]}
                                        onPress={() => setActiveDrawerSeason(s.season_number)}
                                    >
                                        <Text style={[styles.drawerSeasonTabText, active && styles.drawerSeasonTabTextActive]}>
                                            {s.season_number === 0 ? 'Specials' : `Season ${s.season_number}`}
                                            {Array.isArray(s.episodes) && s.episodes.length > 0
                                                ? `  (${s.episodes.length})`
                                                : ''}
                                        </Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>
                    )}

                    {/* Episodes List */}
                    <ScrollView style={styles.drawerEpisodeList}>
                        {drawerEpisodes.length === 0 ? (
                            <Text style={styles.drawerEmpty}>
                                No episode list came back for this season.
                            </Text>
                        ) : null}
                        {drawerEpisodes.map(ep => {
                            const epSeason = ep.season_number != null ? ep.season_number : drawerActiveSeasonNumber;
                            const isCurrent = epSeason === season && ep.episode_number === episode;
                            return (
                                <TouchableOpacity
                                    key={`${epSeason}-${ep.episode_number}`}
                                    style={[styles.drawerEpCard, isCurrent && styles.drawerEpCardActive]}
                                    onPress={() => {
                                        setShowEpisodeDrawer(false);
                                        if (onSelectEpisode) {
                                            onSelectEpisode(epSeason, ep.episode_number);
                                        }
                                    }}
                                >
                                    <View style={styles.drawerEpBadge}>
                                        <Text style={styles.drawerEpBadgeText}>EP {ep.episode_number}</Text>
                                    </View>
                                    <View style={{ flex: 1, paddingLeft: 10 }}>
                                        <Text style={[styles.drawerEpName, isCurrent && { color: COLORS.brand }]} numberOfLines={1}>
                                            {ep.name || `Episode ${ep.episode_number}`}
                                        </Text>
                                        {ep.overview ? (
                                            <Text style={styles.drawerEpOverview} numberOfLines={2}>
                                                {ep.overview}
                                            </Text>
                                        ) : null}
                                    </View>
                                    {isCurrent && <Text style={styles.nowPlayingText}>▶ Playing</Text>}
                                </TouchableOpacity>
                            );
                        })}
                    </ScrollView>
                </View>
            )}

            {/* Shared Top Bar — mounted in BOTH direct and embed mode so the
                server switcher and episode drawer are always reachable. */}
            <View
                style={[
                    styles.topControlBar,
                    isDirect && (controlsVisible ? styles.controlsOverlayVisible : styles.controlsOverlayHidden)
                ]}
                pointerEvents="box-none"
            >
                <TouchableOpacity style={styles.backBtn} onPress={onBack}>
                    <Text style={styles.backBtnText}>‹ Back</Text>
                </TouchableOpacity>

                <View style={styles.titleInfo}>
                    <Text style={styles.titleText} numberOfLines={1}>{title}</Text>
                    {season ? (
                        <Text style={styles.episodeBadge}>S{season}:E{episode}</Text>
                    ) : null}
                </View>

                <View style={styles.topRightControls}>
                    {/* Fullscreen lives in the SHARED top bar, not in the transport
                        controls. The transport bar is gated behind isDirect, and embed
                        mode is what nearly every title actually plays in — so the old
                        button was rendered for almost nobody, and phones have no
                        keyboard to fall back on the F shortcut. */}
                    <TouchableOpacity
                        style={styles.iconBtn}
                        onPress={toggleFullscreen}
                        accessibilityLabel="Toggle fullscreen"
                    >
                        <Text style={styles.iconBtnText}>{isFullscreen ? '⛷' : '⛶'}</Text>
                    </TouchableOpacity>

                    {/* Crop / stretch — cycles Fit → Crop → Stretch */}
                    <TouchableOpacity
                        style={[styles.pillButton, viewMode !== 'fit' && styles.pillButtonActive]}
                        onPress={nextViewMode}
                        accessibilityLabel={`Video fit: ${VIEW_LABEL[viewMode]}`}
                    >
                        <Text style={styles.pillButtonText}>⬚ {VIEW_LABEL[viewMode]}</Text>
                    </TouchableOpacity>

                    {/* Server Switcher */}
                    {mirrorList.length > 0 && (
                        <View style={{ position: 'relative' }}>
                            <TouchableOpacity
                                style={styles.pillButton}
                                onPress={() => setShowServerMenu(!showServerMenu)}
                            >
                                <Text style={styles.pillButtonText}>⚡ {sourceName || 'Server'}</Text>
                            </TouchableOpacity>
                            {showServerMenu && (
                                <View style={styles.popupMenu}>
                                    <Text style={styles.popupMenuHeader}>Select Stream Server</Text>
                                    {mirrorList.map((m, idx) => (
                                        <TouchableOpacity
                                            key={idx}
                                            style={[styles.popupMenuItem, idx === activeMirrorIdx && styles.popupMenuItemActive]}
                                            onPress={() => {
                                                setShowServerMenu(false);
                                                if (onSelectMirror) onSelectMirror(m, idx);
                                            }}
                                        >
                                            <Text style={[styles.popupMenuText, idx === activeMirrorIdx && styles.popupMenuTextActive]}>
                                                {idx === activeMirrorIdx ? '▶ ' : ''}{m.label} ({m.quality || 'HD'})
                                                {m.direct ? ' · direct' : ''}
                                            </Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            )}
                        </View>
                    )}

                    {/* Subtitles — only when the track list is real */}
                    {canSelectSubtitles && (
                        <View style={{ position: 'relative' }}>
                            <TouchableOpacity
                                style={styles.pillButton}
                                onPress={() => setShowSubtitleMenu(!showSubtitleMenu)}
                            >
                                <Text style={styles.pillButtonText}>💬 Subtitles</Text>
                            </TouchableOpacity>
                            {showSubtitleMenu && (
                                <View style={styles.popupMenu}>
                                    <Text style={styles.popupMenuHeader}>Subtitles</Text>
                                    <TouchableOpacity
                                        style={[styles.popupMenuItem, selectedSubtitle === 'off' && styles.popupMenuItemActive]}
                                        onPress={() => { setSelectedSubtitle('off'); setShowSubtitleMenu(false); }}
                                    >
                                        <Text style={styles.popupMenuText}>Off</Text>
                                    </TouchableOpacity>
                                    {subtitles.map(sub => (
                                        <TouchableOpacity
                                            key={sub.id || sub.language}
                                            style={[styles.popupMenuItem, selectedSubtitle === sub.language && styles.popupMenuItemActive]}
                                            onPress={() => { setSelectedSubtitle(sub.language); setShowSubtitleMenu(false); }}
                                        >
                                            <Text style={styles.popupMenuText}>{sub.label || sub.language}</Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            )}
                        </View>
                    )}

                    {/* Audio.
                        A real switcher appears only when the source genuinely
                        carries more than one audio track (direct mode, via the
                        HLS manifest). Embed mode gets the truth instead of a
                        list of languages it cannot act on. */}
                    <View style={{ position: 'relative' }}>
                        <TouchableOpacity
                            style={styles.pillButton}
                            onPress={() => setShowDubMenu(!showDubMenu)}
                        >
                            <Text style={styles.pillButtonText}>
                                🌐 Audio{availableAudioTracks.length > 1 ? ` (${availableAudioTracks.length})` : ''}
                            </Text>
                        </TouchableOpacity>
                        {showDubMenu && (
                            <View style={[styles.popupMenu, styles.audioPopupMenu]}>
                                <Text style={styles.popupMenuHeader}>Audio</Text>
                                <ScrollView style={{ maxHeight: 260 }}>
                                    {availableAudioTracks.length > 1 ? (
                                        <>
                                            {availableAudioTracks.map(t => (
                                                <TouchableOpacity
                                                    key={t.idx}
                                                    style={[styles.popupMenuItem, activeAudioIdx === t.idx && styles.popupMenuItemActive]}
                                                    onPress={() => selectAudioTrack(t.idx)}
                                                >
                                                    <Text style={[styles.popupMenuText, activeAudioIdx === t.idx && styles.popupMenuTextActive]}>
                                                        {activeAudioIdx === t.idx ? '▶ ' : ''}{t.label}
                                                    </Text>
                                                </TouchableOpacity>
                                            ))}
                                            <View style={styles.popupMenuDivider} />
                                            <Text style={styles.popupMenuHint}>
                                                Switching restarts audio on some browsers. Playback position is kept.
                                            </Text>
                                        </>
                                    ) : (
                                        <>
                                            <Text style={styles.popupMenuHint}>
                                                {isDirect
                                                    ? 'This stream carries a single audio track, so there is nothing to switch between.'
                                                    : 'This server streams one audio track. The language is baked into the file, so no dub can be selected here.'}
                                            </Text>
                                            <View style={styles.popupMenuDivider} />
                                            {normalizedDubs.length > 0 && (
                                                <>
                                                    <Text style={styles.popupMenuSubheader}>Languages recorded for this title</Text>
                                                    {normalizedDubs.map(d => (
                                                        <Text key={d.code} style={styles.popupMenuHint}>
                                                            • {d.label}
                                                        </Text>
                                                    ))}
                                                    <View style={styles.popupMenuDivider} />
                                                </>
                                            )}
                                            <Text style={styles.popupMenuHint}>
                                                These are catalogue facts, not playback options. Subtitles are separate — use
                                                the CC button in the player, or pick a different stream from ⚡ Server
                                                which may carry a different audio track.
                                            </Text>
                                        </>
                                    )}
                                </ScrollView>
                            </View>
                        )}
                    </View>

                    {/* External player handoff — VLC and friends */}
                    {isDirect && streamUrl ? (
                        <View style={{ position: 'relative' }}>
                            <TouchableOpacity
                                style={styles.pillButton}
                                onPress={() => setShowPlayerMenu(!showPlayerMenu)}
                            >
                                <Text style={styles.pillButtonText}>⏏ External</Text>
                            </TouchableOpacity>
                            {showPlayerMenu && (
                                <View style={styles.popupMenu}>
                                    <Text style={styles.popupMenuHeader}>Open in</Text>
                                    {playerApps.map((p) => (
                                        <TouchableOpacity
                                            key={p.id}
                                            style={styles.popupMenuItem}
                                            onPress={async () => {
                                                setShowPlayerMenu(false);
                                                const ok = await p.run(streamUrl, title);
                                                if (!ok) setPlayerHandoffFailed(true);
                                            }}
                                        >
                                            <Text style={styles.popupMenuText}>{p.label}</Text>
                                        </TouchableOpacity>
                                    ))}
                                    <TouchableOpacity
                                        style={styles.popupMenuItem}
                                        onPress={() => { setShowPlayerMenu(false); setShowPlayerMenu(false); }}
                                    >
                                        <Text style={[styles.popupMenuText, { color: COLORS.textMuted }]}>Cancel</Text>
                                    </TouchableOpacity>
                                </View>
                            )}
                        </View>
                    ) : null}

                    {/* Episodes Drawer */}
                    {seasons.length > 0 && (
                        <TouchableOpacity
                            style={styles.pillButton}
                            onPress={() => setShowEpisodeDrawer(true)}
                        >
                            <Text style={styles.pillButtonText}>📑 Episodes</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Honest feedback when the browser took the fallback path, instead of
                    the old behaviour where a rejected requestFullscreen vanished into a
                    console.warn and the button just looked broken. */}
                {fullscreenNote ? (
                    <View style={styles.fullscreenNoteWrap} pointerEvents="none">
                        <Text style={styles.fullscreenNote}>{fullscreenNote}</Text>
                    </View>
                ) : null}
            </View>

            {/* Loading line — sits directly under the title bar so a slow provider is
                never a silent black rectangle. It carries the switcher with it,
                so the user can bail to another server without waiting out the
                timeout or going back to the title bar. */}
            {loadBarVisible ? (
                <View style={styles.loadStatusBar} pointerEvents="box-none">
                    <View style={styles.loadStatusLeft}>
                        {isLoadingContent ? <ActivityIndicator size="small" color={COLORS.brand} /> : null}
                        <Text style={styles.loadStatusText} numberOfLines={1}>
                            {isLoadingContent
                                ? `Loading ${sourceName || 'stream'}… ${loadSeconds}s`
                                : `Playing via ${sourceName || 'this server'}`}
                        </Text>
                    </View>

                    {mirrorList.length > 1 ? (
                        <View style={styles.loadStatusMenuWrap}>
                            <TouchableOpacity
                                style={styles.loadStatusBtn}
                                onPress={() => setShowLoadServerMenu(v => !v)}
                                accessibilityLabel="Change stream server"
                            >
                                <Text style={styles.loadStatusBtnText}>
                                    {showLoadServerMenu ? 'Close' : 'Change'}
                                </Text>
                            </TouchableOpacity>

                            {showLoadServerMenu ? (
                                <View style={styles.popupMenu}>
                                    <Text style={styles.popupMenuHeader}>Change player</Text>
                                    {mirrorList.map((m, idx) => (
                                        <TouchableOpacity
                                            key={idx}
                                            style={[styles.popupMenuItem, idx === activeMirrorIdx && styles.popupMenuItemActive]}
                                            onPress={() => {
                                                setShowLoadServerMenu(false);
                                                if (onSelectMirror) onSelectMirror(m, idx);
                                            }}
                                        >
                                            <Text style={[styles.popupMenuText, idx === activeMirrorIdx && styles.popupMenuTextActive]}>
                                                {idx === activeMirrorIdx ? '▶ ' : ''}{m.label}
                                            </Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            ) : null}
                        </View>
                    ) : null}
                </View>
            ) : null}

            {!isDirect && embedState === 'stalled' && mirrorList && mirrorList.length > 1 ? (
                <View style={styles.failoverBar}>
                    <Text style={styles.failoverText}>
                        This server isn&apos;t responding.
                    </Text>
                    <TouchableOpacity style={styles.failoverBtn} onPress={tryNextMirror}>
                        <Text style={styles.failoverBtnText}>Try next server</Text>
                    </TouchableOpacity>
                    {onBack ? (
                        <TouchableOpacity style={styles.failoverBtn} onPress={onBack}>
                            <Text style={styles.failoverBtnText}>Back</Text>
                        </TouchableOpacity>
                    ) : null}
                </View>
            ) : null}

            {(notice || playerHandoffFailed) && noticeVisible ? (
                <View style={styles.noticeBar} pointerEvents="none">
                    <View style={styles.noticePill}>
                        <Text style={styles.noticeText}>
                            {playerHandoffFailed
                                ? "Couldn't find a player app for this stream."
                                : 'Provider player · no direct stream available'}
                        </Text>
                    </View>
                </View>
            ) : null}

            {/* Transport controls — only meaningful when we own the decode.
                A cross-origin iframe keeps its own controls. */}
            {isDirect && (
                <View
                    style={[
                        styles.controlsOverlay,
                        controlsVisible ? styles.controlsOverlayVisible : styles.controlsOverlayHidden
                    ]}
                >
                    {/* Center Action Controls */}
                    <View style={styles.centerControlArea}>
                        {isBuffering ? (
                            <ActivityIndicator size="large" color={COLORS.brand} style={{ transform: [{ scale: 1.5 }] }} />
                        ) : (
                            <View style={styles.centerButtonRow}>
                                <TouchableOpacity
                                    style={styles.skipButton}
                                    onPress={() => seekRelative(-10)}
                                    accessibilityLabel="Rewind 10 seconds"
                                >
                                    <Text style={styles.skipButtonText}>↺ 10</Text>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={styles.playPauseButton}
                                    onPress={togglePlay}
                                    accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
                                >
                                    <Text style={styles.playPauseIcon}>
                                        {isPlaying ? '❚❚' : '▶'}
                                    </Text>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={styles.skipButton}
                                    onPress={() => seekRelative(10)}
                                    accessibilityLabel="Fast forward 10 seconds"
                                >
                                    <Text style={styles.skipButtonText}>10 ↻</Text>
                                </TouchableOpacity>
                            </View>
                        )}
                    </View>

                    {/* Bottom Control Bar */}
                    <View style={styles.bottomControlBar}>
                        {/* Interactive Scrubber Bar */}
                        <div
                            style={{
                                width: '100%',
                                height: 24,
                                position: 'relative',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                            }}
                            onClick={handleScrub}
                            onMouseMove={handleScrubHover}
                            onMouseLeave={() => { setHoverTime(null); setHoverPos(null); }}
                        >
                            {/* Track background */}
                            <div style={{
                                width: '100%',
                                height: 4,
                                backgroundColor: 'rgba(255, 255, 255, 0.25)',
                                borderRadius: 2,
                                position: 'relative',
                            }}>
                                {/* Buffered Bar */}
                                <div style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: `${duration > 0 ? (buffered / duration) * 100 : 0}%`,
                                    backgroundColor: 'rgba(255, 255, 255, 0.4)',
                                    borderRadius: 2,
                                }} />

                                {/* Played Progress Bar */}
                                <div style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`,
                                    backgroundColor: COLORS.brand,
                                    borderRadius: 2,
                                }}>
                                    {/* Thumb Handle */}
                                    <div style={{
                                        position: 'absolute',
                                        right: -6,
                                        top: -4,
                                        width: 12,
                                        height: 12,
                                        borderRadius: '50%',
                                        backgroundColor: '#FFFFFF',
                                        boxShadow: '0 0 6px rgba(0, 0, 0, 0.8)',
                                    }} />
                                </div>
                            </div>

                            {/* Hover Tooltip */}
                            {hoverTime !== null && hoverPos !== null && (
                                <div style={{
                                    position: 'absolute',
                                    left: `${hoverPos}%`,
                                    transform: 'translateX(-50%)',
                                    bottom: 22,
                                    backgroundColor: 'rgba(20, 20, 20, 0.95)',
                                    color: '#FFFFFF',
                                    padding: '3px 8px',
                                    borderRadius: 4,
                                    fontSize: 11,
                                    fontWeight: 'bold',
                                    pointerEvents: 'none',
                                    border: '1px solid rgba(255, 255, 255, 0.2)',
                                }}>
                                    {formatTime(hoverTime)}
                                </div>
                            )}
                        </div>

                        {/* Controls Bottom Row */}
                        <View style={styles.bottomControlsRow}>
                            <View style={styles.bottomLeftControls}>
                                <TouchableOpacity onPress={togglePlay} style={styles.iconBtn}>
                                    <Text style={styles.iconBtnText}>{isPlaying ? '❚❚' : '▶'}</Text>
                                </TouchableOpacity>

                                <TouchableOpacity onPress={toggleMute} style={styles.iconBtn}>
                                    <Text style={styles.iconBtnText}>{isMuted ? '🔇' : volume > 0.5 ? '🔊' : '🔉'}</Text>
                                </TouchableOpacity>

                                {/* Volume Slider */}
                                <div style={{ width: 70, display: 'flex', alignItems: 'center', marginRight: 12 }}>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.05"
                                        value={isMuted ? 0 : volume}
                                        onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                                        style={{ width: '100%', accentColor: COLORS.brand, cursor: 'pointer' }}
                                    />
                                </div>

                                <Text style={styles.timeDisplay}>
                                    {formatTime(currentTime)} / {formatTime(duration)}
                                </Text>
                            </View>

                            <View style={styles.bottomRightControls}>
                                {/* Playback Speed Selector */}
                                <View style={{ position: 'relative' }}>
                                    <TouchableOpacity
                                        style={styles.textOptionBtn}
                                        onPress={() => setShowSpeedMenu(!showSpeedMenu)}
                                    >
                                        <Text style={styles.textOptionBtnText}>{playbackRate}x</Text>
                                    </TouchableOpacity>
                                    {showSpeedMenu && (
                                        <View style={[styles.popupMenu, { bottom: 40, right: 0 }]}>
                                            <Text style={styles.popupMenuHeader}>Playback Speed</Text>
                                            {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map(rate => (
                                                <TouchableOpacity
                                                    key={rate}
                                                    style={[styles.popupMenuItem, playbackRate === rate && styles.popupMenuItemActive]}
                                                    onPress={() => handleSetRate(rate)}
                                                >
                                                    <Text style={[styles.popupMenuText, playbackRate === rate && styles.popupMenuTextActive]}>
                                                        {rate === 1 ? '1.0x (Normal)' : `${rate}x`}
                                                    </Text>
                                                </TouchableOpacity>
                                            ))}
                                        </View>
                                    )}
                                </View>

                                {/* Quality Selector */}
                                {qualityLevels.length > 0 && (
                                    <View style={{ position: 'relative' }}>
                                        <TouchableOpacity
                                            style={styles.textOptionBtn}
                                            onPress={() => setShowQualityMenu(!showQualityMenu)}
                                        >
                                            <Text style={styles.textOptionBtnText}>
                                                {activeQualityIdx === -1 ? 'Auto' : `${qualityLevels[activeQualityIdx]?.height}p`}
                                            </Text>
                                        </TouchableOpacity>
                                        {showQualityMenu && (
                                            <View style={[styles.popupMenu, { bottom: 40, right: 0 }]}>
                                                <Text style={styles.popupMenuHeader}>Quality</Text>
                                                <TouchableOpacity
                                                    style={[styles.popupMenuItem, activeQualityIdx === -1 && styles.popupMenuItemActive]}
                                                    onPress={() => handleSetQuality(-1)}
                                                >
                                                    <Text style={[styles.popupMenuText, activeQualityIdx === -1 && styles.popupMenuTextActive]}>
                                                        Auto (Adaptive)
                                                    </Text>
                                                </TouchableOpacity>
                                                {qualityLevels.map(lvl => (
                                                    <TouchableOpacity
                                                        key={lvl.idx}
                                                        style={[styles.popupMenuItem, activeQualityIdx === lvl.idx && styles.popupMenuItemActive]}
                                                        onPress={() => handleSetQuality(lvl.idx)}
                                                    >
                                                        <Text style={[styles.popupMenuText, activeQualityIdx === lvl.idx && styles.popupMenuTextActive]}>
                                                            {lvl.label}
                                                        </Text>
                                                    </TouchableOpacity>
                                                ))}
                                            </View>
                                        )}
                                    </View>
                                )}

                                {/* Next Episode Button */}
                                {hasNextEp && (
                                    <TouchableOpacity
                                        style={styles.nextEpBtn}
                                        onPress={onNextEpisode}
                                    >
                                        <Text style={styles.nextEpBtnText}>Next Ep ⏭</Text>
                                    </TouchableOpacity>
                                )}
                            </View>
                        </View>
                    </View>
                </View>
            )}
            {/* Netflix-Style Binge Watch Next Episode Countdown Card */}
            {showBingeCard && nextEpObj && (
                <View style={styles.bingeCard}>
                    <View style={styles.bingeHeaderRow}>
                        <Text style={styles.bingeTag}>NEXT EPISODE IN {bingeCountdown}s</Text>
                        <TouchableOpacity onPress={() => { setShowBingeCard(false); setBingeDismissed(true); }}>
                            <Text style={styles.bingeDismissText}>✕</Text>
                        </TouchableOpacity>
                    </View>
                    <Text style={styles.bingeTitle} numberOfLines={1}>
                        S{nextEpObj.season_number || season}:E{nextEpObj.episode_number} - {nextEpObj.name || 'Next Episode'}
                    </Text>
                    <View style={styles.bingeBtnRow}>
                        <TouchableOpacity
                            style={styles.bingePlayNowBtn}
                            onPress={() => {
                                setShowBingeCard(false);
                                if (onNextEpisode) onNextEpisode();
                            }}
                        >
                            <Text style={styles.bingePlayNowText}>▶ Play Now</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={styles.bingeCreditsBtn}
                            onPress={() => {
                                setShowBingeCard(false);
                                setBingeDismissed(true);
                            }}
                        >
                            <Text style={styles.bingeCreditsText}>Watch Credits</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        width: '100%',
        height: '100%',
        backgroundColor: '#000000',
        position: 'relative',
        overflow: 'hidden',
    },
    containerFullscreen: {
        /* position:fixed is the point of this rule — the player normally sits inside
           several overflow:hidden navigation wrappers, so 100vw/100vh alone would be
           clipped. This is the fallback for browsers with no fullscreen API (iPhone). */
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 9999,
    },
    controlsOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.45)',
        justifyContent: 'space-between',
        padding: 20,
        transition: 'opacity 0.3s ease',
        zIndex: 10,
    },
    controlsOverlayVisible: {
        opacity: 1,
        pointerEvents: 'auto',
    },
    controlsOverlayHidden: {
        opacity: 0,
        pointerEvents: 'none',
    },
    failoverBar: {
        position: 'absolute',
        top: 60,
        left: 16,
        right: 16,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(20, 20, 24, 0.96)',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.2)',
        paddingVertical: 10,
        paddingHorizontal: 14,
        zIndex: 35,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.6)',
    },
    failoverText: { color: '#E6E6EC', fontSize: 13, flex: 1 },
    failoverBtn: {
        backgroundColor: COLORS.brand,
        borderRadius: 6,
        paddingHorizontal: 14,
        paddingVertical: 8,
        marginLeft: 8,
    },
    failoverBtnText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },

    // Slim line under the title bar. Deliberately not the failover bar: that
    // one is a modal-looking block that only appears on timeout, and it sits at
    // top:60 which collides with this. This is the "still working on it" line.
    loadStatusBar: {
        position: 'absolute',
        top: 56,
        left: 12,
        right: 12,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: 'rgba(16, 16, 20, 0.92)',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.14)',
        paddingVertical: 7,
        paddingLeft: 12,
        paddingRight: 7,
        zIndex: 30,
    },
    loadStatusLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
        minWidth: 0,
        marginRight: 10,
    },
    loadStatusText: {
        color: '#E6E6EC',
        fontSize: 12,
        fontWeight: '600',
        marginLeft: 8,
        flexShrink: 1,
    },
    loadStatusMenuWrap: {
        position: 'relative',
        flexShrink: 0,
    },
    loadStatusBtn: {
        backgroundColor: COLORS.brand,
        borderRadius: 6,
        paddingHorizontal: 12,
        paddingVertical: 6,
    },
    loadStatusBtnText: { color: '#FFFFFF', fontSize: 12, fontWeight: '800' },
    noticeBar: {
        position: 'absolute',
        top: 10,
        left: 0,
        right: 0,
        alignItems: 'center',
        zIndex: 25,
    },
    // A small pill rather than a full-width black bar. The old version spanned
    // the whole player and read as a broken subtitle track.
    noticePill: {
        backgroundColor: 'rgba(14, 14, 18, 0.72)',
        borderRadius: 999,
        paddingVertical: 5,
        paddingHorizontal: 12,
        borderWidth: StyleSheet.hairlineWidth,
        borderColor: 'rgba(255,255,255,0.14)',
    },
    noticeText: {
        color: '#B9B9C4',
        fontSize: 11,
        lineHeight: 15,
    },
    topControlBar: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 30,
        backgroundColor: 'rgba(10, 10, 14, 0.85)',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 12,
        paddingTop: 12,
        paddingBottom: 8,
    },
    backBtn: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        backgroundColor: 'rgba(20, 20, 20, 0.75)',
        borderRadius: 6,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
    },
    backBtnText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '700',
    },
    titleInfo: {
        flex: 1,
        /* Without minWidth:0 a long title refuses to shrink below its content
           width in a flex row and pushes the right-hand controls off. */
        minWidth: 0,
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        gap: 8,
    },
    titleText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '800',
        textShadowColor: 'rgba(0,0,0,0.8)',
        textShadowOffset: { width: 0, height: 1 },
        textShadowRadius: 4,
        flexShrink: 1,
    },
    episodeBadge: {
        color: COLORS.brand,
        backgroundColor: 'rgba(229, 9, 20, 0.15)',
        borderColor: 'rgba(229, 9, 20, 0.4)',
        borderWidth: 1,
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 4,
        fontSize: 12,
        fontWeight: '800',
    },
    fullscreenNoteWrap: {
        position: 'absolute',
        top: 64,
        left: 16,
        right: 16,
        alignItems: 'center',
        zIndex: 20,
    },
    fullscreenNote: {
        color: '#ffffff',
        backgroundColor: 'rgba(20, 20, 24, 0.92)',
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 8,
        fontSize: 12,
        overflow: 'hidden',
    },
    topRightControls: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        /* Never let the title squeeze these controls — this is what collapsed
           the fullscreen button to a sliver. */
        flexShrink: 0,
        marginLeft: 8,
    },
    pillButton: {
        backgroundColor: 'rgba(20, 20, 20, 0.75)',
        paddingHorizontal: 12,
        paddingVertical: 7,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
        flexShrink: 0,
    },
    pillButtonActive: {
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        borderColor: 'rgba(255, 255, 255, 0.5)',
    },
    pillButtonActive: {
        borderColor: COLORS.brand,
        backgroundColor: 'rgba(229, 9, 20, 0.25)',
    },
    pillButtonText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: '700',
    },
    popupMenu: {
        position: 'absolute',
        top: 40,
        right: 0,
        width: 200,
        backgroundColor: 'rgba(20, 20, 20, 0.95)',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
        padding: 8,
        zIndex: 50,
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
    },
    audioPopupMenu: {
        width: 250,
        maxHeight: 340,
    },
    popupMenuSubheader: {
        color: '#8A8A98',
        fontSize: 10,
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        paddingHorizontal: 8,
        paddingTop: 8,
        paddingBottom: 3,
    },
    popupMenuDivider: {
        height: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
        marginVertical: 6,
    },
    popupMenuHint: {
        color: '#8A8A98',
        fontSize: 10,
        fontStyle: 'italic',
        paddingHorizontal: 8,
        paddingVertical: 4,
        lineHeight: 14,
    },
    popupMenuHeader: {
        color: COLORS.textMuted,
        fontSize: 11,
        fontWeight: '700',
        textTransform: 'uppercase',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.1)',
        marginBottom: 4,
    },
    popupMenuItem: {
        paddingVertical: 8,
        paddingHorizontal: 8,
        borderRadius: 4,
    },
    popupMenuItemActive: {
        backgroundColor: 'rgba(229, 9, 20, 0.25)',
    },
    popupMenuText: {
        color: COLORS.textSecondary,
        fontSize: 12,
        fontWeight: '600',
    },
    popupMenuTextActive: {
        color: '#FFFFFF',
        fontWeight: '800',
    },
    centerControlArea: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    centerButtonRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 36,
    },
    skipButton: {
        width: 52,
        height: 52,
        borderRadius: 26,
        backgroundColor: 'rgba(20, 20, 20, 0.65)',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
    },
    skipButtonText: {
        color: '#FFFFFF',
        fontSize: 13,
        fontWeight: '800',
    },
    playPauseButton: {
        width: 72,
        height: 72,
        borderRadius: 36,
        backgroundColor: COLORS.brand,
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 20px rgba(229, 9, 20, 0.6)',
    },
    playPauseIcon: {
        color: '#FFFFFF',
        fontSize: 26,
        fontWeight: '900',
        marginLeft: 2,
    },
    bottomControlBar: {
        paddingHorizontal: 8,
        paddingBottom: 8,
    },
    bottomControlsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: 6,
    },
    bottomLeftControls: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    bottomRightControls: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    iconBtn: {
        /* Explicit size + flexShrink:0. Without these the button collapses to a
           few pixels wide inside topRightControls whenever the title is long —
           it was rendering, but crushed to an untappable sliver. */
        width: 36,
        height: 36,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.45)',
    },
    iconBtnText: {
        color: '#FFFFFF',
        fontSize: 16,
        lineHeight: 20,
        textAlign: 'center',
    },
    timeDisplay: {
        color: '#CCCCCC',
        fontSize: 12,
        fontWeight: '600',
        marginLeft: 6,
    },
    textOptionBtn: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    textOptionBtnText: {
        color: '#FFFFFF',
        fontSize: 11,
        fontWeight: '700',
    },
    nextEpBtn: {
        backgroundColor: COLORS.brand,
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 4,
    },
    nextEpBtnText: {
        color: '#FFFFFF',
        fontSize: 11,
        fontWeight: '800',
    },
    episodeDrawer: {
        position: 'absolute',
        top: 0,
        right: 0,
        bottom: 0,
        width: 340,
        backgroundColor: 'rgba(15, 15, 15, 0.96)',
        backdropFilter: 'blur(16px)',
        zIndex: 100,
        borderLeftWidth: 1,
        borderLeftColor: 'rgba(255, 255, 255, 0.12)',
        display: 'flex',
        flexDirection: 'column',
    },
    drawerHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.1)',
    },
    drawerTitle: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '800',
    },
    drawerCloseBtn: {
        padding: 6,
    },
    drawerCloseText: {
        color: COLORS.textMuted,
        fontSize: 18,
        fontWeight: '700',
    },
    drawerSeasonTabs: {
        flexDirection: 'row',
        paddingHorizontal: 12,
        paddingVertical: 10,
        gap: 8,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.08)',
    },
    drawerSeasonTab: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
    },
    drawerSeasonTabActive: {
        backgroundColor: COLORS.brand,
    },
    drawerSeasonTabText: {
        color: COLORS.textSecondary,
        fontSize: 12,
        fontWeight: '700',
    },
    drawerSeasonTabTextActive: {
        color: '#FFFFFF',
    },
    drawerEpisodeList: {
        flex: 1,
        padding: 12,
    },
    drawerEmpty: {
        color: COLORS.textMuted,
        fontSize: 12,
        paddingVertical: 18,
        textAlign: 'center',
    },
    drawerEpCard: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 12,
        borderRadius: 8,
        backgroundColor: 'rgba(255, 255, 255, 0.04)',
        marginBottom: 8,
        borderWidth: 1,
        borderColor: 'transparent',
    },
    drawerEpCardActive: {
        borderColor: COLORS.brand,
        backgroundColor: 'rgba(229, 9, 20, 0.12)',
    },
    drawerEpBadge: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    drawerEpBadgeText: {
        color: '#FFFFFF',
        fontSize: 11,
        fontWeight: '800',
    },
    drawerEpName: {
        color: '#FFFFFF',
        fontSize: 13,
        fontWeight: '700',
    },
    drawerEpOverview: {
        color: COLORS.textMuted,
        fontSize: 11,
        marginTop: 2,
    },
    nowPlayingText: {
        color: COLORS.brand,
        fontSize: 11,
        fontWeight: '800',
    },
    bingeCard: {
        position: 'absolute',
        bottom: 80,
        right: 24,
        width: 300,
        backgroundColor: 'rgba(15, 15, 15, 0.95)',
        borderRadius: 8,
        padding: 16,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.2)',
        zIndex: 50,
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.7)',
    },
    bingeHeaderRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 6,
    },
    bingeTag: {
        color: COLORS.brand,
        fontSize: 11,
        fontWeight: '800',
        letterSpacing: 0.5,
    },
    bingeDismissText: {
        color: COLORS.textMuted,
        fontSize: 14,
        fontWeight: '700',
    },
    bingeTitle: {
        color: '#FFFFFF',
        fontSize: 13,
        fontWeight: '700',
        marginBottom: 12,
    },
    bingeBtnRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    bingePlayNowBtn: {
        flex: 1,
        backgroundColor: COLORS.brand,
        paddingVertical: 8,
        borderRadius: 4,
        alignItems: 'center',
    },
    bingePlayNowText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: '800',
    },
    bingeCreditsBtn: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    bingeCreditsText: {
        color: COLORS.textSecondary,
        fontSize: 11,
        fontWeight: '600',
    },
});
