import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'widgets/responsive_layout.dart';

/// TV Detail Screen - shows TV series with season picker and episode list.
///
/// Mirrors the Expo TVDetailScreen. Uses the backend `/api/v1/tv/:tmdbId/episodes`
/// endpoint with fallback to synthetic 10-episode seasons if TMDB enrichment is
/// not configured.
class TvDetailScreen extends StatefulWidget {
  final MediaItem item;

  const TvDetailScreen({Key? key, required this.item}) : super(key: key);

  @override
  State<TvDetailScreen> createState() => _TvDetailScreenState();
}

class _TvDetailScreenState extends State<TvDetailScreen> {
  late ApiService _api;
  int _season = 1;
  List<TvEpisode> _episodes = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _api = ApiService();
    _loadEpisodes();
  }

  Future<void> _loadEpisodes() async {
    if (widget.item.tmdbId == null) {
      setState(() {
        _loading = false;
        _error = 'No TMDB ID available for this series';
      });
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final eps = await _api.getTvEpisodes(widget.item.tmdbId!, _season);
      setState(() {
        _episodes = eps;
        _loading = false;
      });
    } catch (err) {
      setState(() {
        _error = err.toString();
        _loading = false;
      });
    }
  }

  void _changeSeason(int s) {
    setState(() => _season = s);
    _loadEpisodes();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header / hero
              _buildHeader(context),
              const SizedBox(height: 24),

              // Season selector
              if (widget.item.seasons != null && widget.item.seasons! > 0) ...[
                Text('Seasons', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 12),
                SizedBox(
                  height: 40,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.item.seasons,
                    itemBuilder: (_, i) {
                      final s = i + 1;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text('Season $s'),
                          selected: _season == s,
                          selectedColor: AppTheme.brandPrimary,
                          labelStyle: TextStyle(
                            color: _season == s ? Colors.white : AppTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                          onSelected: (_) => _changeSeason(s),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Episodes
              Text(
                'Season $_season • ${_episodes.length} episodes',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),

              if (_loading)
                const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_error != null)
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppTheme.statusError),
                      const SizedBox(height: 12),
                      Text(_error!, style: const TextStyle(color: AppTheme.statusError)),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: _loadEpisodes, child: const Text('Retry')),
                    ],
                  ),
                )
              else
                ..._episodes.map((ep) => _buildEpisodeRow(context, ep)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          child: Image.network(
            widget.item.posterUrl,
            width: isPhone ? 120 : 180,
            height: isPhone ? 180 : 270,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              width: isPhone ? 120 : 180,
              height: isPhone ? 180 : 270,
              color: AppTheme.bgSurface2,
              child: const Icon(Icons.movie, size: 48, color: AppTheme.textMuted),
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.item.title,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 6),
              Text(
                '${widget.item.releaseYear} • ${widget.item.genres.join(', ')}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              Text(
                widget.item.description,
                maxLines: 6,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 6,
                children: [
                  _badge('TV SERIES', AppTheme.brandPrimary),
                  if (widget.item.imdbId != null) _badge('IMDb: ${widget.item.imdbId}', AppTheme.bgSurface3),
                  if (widget.item.sourceName.isNotEmpty) _badge(widget.item.sourceName, AppTheme.bgSurface3),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _badge(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3)),
        child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
      );

  Widget _buildEpisodeRow(BuildContext context, TvEpisode ep) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: AppTheme.bgSurface1,
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.brandPrimary,
          child: Text('${ep.episode}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
        title: Text(ep.title, style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
        subtitle: ep.overview != null && ep.overview!.isNotEmpty
            ? Text(ep.overview!, maxLines: 2, overflow: TextOverflow.ellipsis)
            : Text('${ep.runtime ?? 45} min • ${ep.sources.length} sources', style: const TextStyle(color: AppTheme.textMuted)),
        trailing: const Icon(Icons.play_circle_fill, color: AppTheme.brandPrimary, size: 32),
        onTap: () {
          Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => EpisodePlayerScreen(episode: ep, parentTitle: widget.item.title),
          ));
        },
      ),
    );
  }
}

/// Episode player screen - resolves the stream URL via the backend and shows it.
class EpisodePlayerScreen extends StatefulWidget {
  final TvEpisode episode;
  final String parentTitle;

  const EpisodePlayerScreen({Key? key, required this.episode, required this.parentTitle}) : super(key: key);

  @override
  State<EpisodePlayerScreen> createState() => _EpisodePlayerScreenState();
}

class _EpisodePlayerScreenState extends State<EpisodePlayerScreen> {
  late ApiService _api;
  String? _streamUrl;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _api = ApiService();
    _loadStream();
  }

  Future<void> _loadStream() async {
    try {
      // Use the first available source
      final src = widget.episode.sources.isNotEmpty ? widget.episode.sources.first : null;
      if (src == null) {
        setState(() { _error = 'No sources available'; _loading = false; });
        return;
      }
      final url = await _api.resolveStream(
        widget.parentTitle.toLowerCase().replaceAll(' ', '-'),
        src.provider ?? 'MovieBox',
        season: widget.episode.season,
        episode: widget.episode.episode,
      );
      setState(() {
        _streamUrl = url;
        _loading = false;
        if (url == null) _error = 'Backend returned no stream';
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text('S${widget.episode.season}E${widget.episode.episode} • ${widget.episode.title}'),
        backgroundColor: AppTheme.bgSurface1,
        foregroundColor: AppTheme.textPrimary,
      ),
      body: Center(
        child: _loading
            ? const CircularProgressIndicator(color: AppTheme.brandPrimary)
            : _error != null
                ? Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppTheme.statusError),
                      const SizedBox(height: 12),
                      Text(_error!, style: const TextStyle(color: AppTheme.statusError)),
                      const SizedBox(height: 16),
                      ElevatedButton(onPressed: () { setState(() { _loading = true; _error = null; }); _loadStream(); }, child: const Text('Retry')),
                    ],
                  )
                : Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.play_circle_outline, size: 64, color: AppTheme.brandPrimary),
                        const SizedBox(height: 16),
                        Text(
                          widget.episode.title,
                          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'Stream resolved. Open the URL below in VLC, MX Player, or your browser:',
                          style: TextStyle(color: Colors.white70),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        SelectableText(
                          _streamUrl ?? '',
                          style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontFamily: 'monospace'),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.open_in_new),
                          label: const Text('Open Stream'),
                          onPressed: () {
                            // launchUrl would go here
                          },
                        ),
                      ],
                    ),
                  ),
      ),
    );
  }
}
