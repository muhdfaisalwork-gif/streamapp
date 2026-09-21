import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'responsive_layout.dart';

class VideoPlayerView extends StatefulWidget {
  final MediaItem item;
  final StreamSource initialSource;
  final VoidCallback onBack;
  final Function(double positionSeconds, double durationSeconds)? onProgressUpdate;

  const VideoPlayerView({
    Key? key,
    required this.item,
    required this.initialSource,
    required this.onBack,
    this.onProgressUpdate,
  }) : super(key: key);

  @override
  State<VideoPlayerView> createState() => _VideoPlayerViewState();
}

class _VideoPlayerViewState extends State<VideoPlayerView> {
  late StreamSource _currentSource;
  bool _isPlaying = true;
  double _positionSeconds = 0.0;
  late double _durationSeconds;
  bool _showControls = true;
  Timer? _controlsTimer;
  Timer? _playbackTicker;
  bool _hasError = false;
  String? _errorMessage;
  String _selectedQuality = 'Auto (1080p)';
  SubtitleTrack? _selectedSubtitle;

  @override
  void initState() {
    super.initState();
    _currentSource = widget.initialSource;
    _durationSeconds = widget.item.durationSeconds.toDouble();
    if (widget.item.subtitles.isNotEmpty) {
      _selectedSubtitle = widget.item.subtitles.firstWhere(
        (s) => s.isDefault,
        orElse: () => widget.item.subtitles.first,
      );
    }
    _startPlaybackSimulation();
    _resetControlsTimer();
  }

  void _startPlaybackSimulation() {
    _playbackTicker = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_isPlaying && !_hasError) {
        setState(() {
          if (_positionSeconds < _durationSeconds) {
            _positionSeconds += 1.0;
            widget.onProgressUpdate?.call(_positionSeconds, _durationSeconds);
          } else {
            _isPlaying = false;
          }
        });
      }
    });
  }

  void _resetControlsTimer() {
    _controlsTimer?.cancel();
    if (_showControls) {
      _controlsTimer = Timer(const Duration(milliseconds: 3500), () {
        if (mounted && _isPlaying) {
          setState(() => _showControls = false);
        }
      });
    }
  }

  void _togglePlayPause() {
    setState(() {
      _isPlaying = !_isPlaying;
      _showControls = true;
    });
    _resetControlsTimer();
  }

  void _seekBy(double deltaSeconds) {
    setState(() {
      _positionSeconds = (_positionSeconds + deltaSeconds).clamp(0.0, _durationSeconds);
      _showControls = true;
    });
    widget.onProgressUpdate?.call(_positionSeconds, _durationSeconds);
    _resetControlsTimer();
  }

  void _openTrackSelector(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);

    if (isPhone) {
      // Mobile (<600dp): ModalBottomSheet
      showModalBottomSheet(
        context: context,
        backgroundColor: AppTheme.bgSurface1,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(AppTheme.radiusLg)),
        ),
        builder: (ctx) => _buildTrackSelectorContent(ctx),
      );
    } else {
      // TV / Desktop / Tablet (>=600dp): Right SlideOverDrawer
      showGeneralDialog(
        context: context,
        barrierDismissible: true,
        barrierLabel: 'Tracks',
        transitionDuration: const Duration(milliseconds: 250),
        pageBuilder: (ctx, anim1, anim2) {
          return Align(
            alignment: Alignment.centerRight,
            child: Material(
              color: AppTheme.bgSurface1,
              child: Container(
                width: 360,
                height: double.infinity,
                padding: const EdgeInsets.all(AppTheme.space4),
                child: _buildTrackSelectorContent(ctx),
              ),
            ),
          );
        },
        transitionBuilder: (ctx, anim1, anim2, child) {
          return SlideTransition(
            position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(anim1),
            child: child,
          );
        },
      );
    }
  }

  Widget _buildTrackSelectorContent(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('Audio & Subtitles', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
            IconButton(
              icon: const Icon(Icons.close, color: AppTheme.textSecondary),
              onPressed: () => Navigator.pop(context),
            ),
          ],
        ),
        const Divider(color: AppTheme.bgSurface3),
        const Text('Subtitles', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.brandPrimary)),
        ListTile(
          title: const Text('Off', style: TextStyle(color: AppTheme.textPrimary)),
          trailing: _selectedSubtitle == null ? const Icon(Icons.check, color: AppTheme.brandPrimary) : null,
          onTap: () {
            setState(() => _selectedSubtitle = null);
            Navigator.pop(context);
          },
        ),
        ...widget.item.subtitles.map((sub) => ListTile(
          title: Text(sub.label, style: const TextStyle(color: AppTheme.textPrimary)),
          trailing: _selectedSubtitle?.id == sub.id ? const Icon(Icons.check, color: AppTheme.brandPrimary) : null,
          onTap: () {
            setState(() => _selectedSubtitle = sub);
            Navigator.pop(context);
          },
        )),
      ],
    );
  }

  String _formatTime(double seconds) {
    final s = seconds.toInt();
    final m = s ~/ 60;
    final remS = s % 60;
    return '${m.toString().padLeft(2, '0')}:${remS.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _controlsTimer?.cancel();
    _playbackTicker?.cancel();
    super.dispose();
  }

  KeyEventResult _handleRemoteKeyEvent(FocusNode node, KeyEvent event) {
    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.space ||
          event.logicalKey == LogicalKeyboardKey.select ||
          event.logicalKey == LogicalKeyboardKey.enter ||
          event.logicalKey == LogicalKeyboardKey.mediaPlayPause ||
          event.logicalKey == LogicalKeyboardKey.mediaPlay ||
          event.logicalKey == LogicalKeyboardKey.mediaPause) {
        _togglePlayPause();
        return KeyEventResult.handled;
      } else if (event.logicalKey == LogicalKeyboardKey.arrowLeft ||
          event.logicalKey == LogicalKeyboardKey.mediaRewind) {
        _seekBy(-10);
        return KeyEventResult.handled;
      } else if (event.logicalKey == LogicalKeyboardKey.arrowRight ||
          event.logicalKey == LogicalKeyboardKey.mediaFastForward) {
        _seekBy(10);
        return KeyEventResult.handled;
      } else if (event.logicalKey == LogicalKeyboardKey.escape) {
        widget.onBack();
        return KeyEventResult.handled;
      }
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);

    return Scaffold(
      backgroundColor: Colors.black,
      body: Focus(
        autofocus: true,
        onKeyEvent: _handleRemoteKeyEvent,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () {
            setState(() {
              if (!_showControls) {
                _showControls = true;
              } else {
                _showControls = false;
              }
            });
            _resetControlsTimer();
          },
          child: Stack(
            fit: StackFit.expand,
            children: [
            // 1. Simulated Video Canvas with Poster Backdrop
            Image.network(
              widget.item.backdropUrl.isNotEmpty ? widget.item.backdropUrl : widget.item.posterUrl,
              fit: BoxFit.contain,
              errorBuilder: (ctx, err, stack) => const Center(
                child: Icon(Icons.videocam_off, size: 64, color: AppTheme.textMuted),
              ),
            ),

            // Active Subtitle Overlay
            if (_selectedSubtitle != null && _isPlaying)
              Positioned(
                bottom: isPhone ? 80 : 100,
                left: 20,
                right: 20,
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.75),
                      borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                    ),
                    child: Text(
                      '(${_selectedSubtitle!.label}) [Dialog audio playing]',
                      style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500),
                    ),
                  ),
                ),
              ),

            // 2. Playback Error State Overlay (Player Resilience & WCAG 2.1 AA Live Region)
            if (_hasError)
              Semantics(
                liveRegion: true,
                label: 'Playback alert: ${_errorMessage ?? "Playback error encountered"}. Retry available.',
                child: Container(
                  color: Colors.black.withOpacity(0.85),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline, size: 54, color: AppTheme.statusError),
                        const SizedBox(height: AppTheme.space3),
                        Text(
                          _errorMessage ?? 'Playback error encountered',
                          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 16),
                        ),
                        const SizedBox(height: AppTheme.space4),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            ElevatedButton.icon(
                              icon: const Icon(Icons.refresh),
                              label: const Text('Retry Stream'),
                              onPressed: () => setState(() => _hasError = false),
                            ),
                            const SizedBox(width: AppTheme.space3),
                            if (_currentSource.backupUrl != null)
                              OutlinedButton.icon(
                                icon: const Icon(Icons.swap_horiz),
                                label: const Text('Switch to Backup'),
                                onPressed: () {
                                  setState(() {
                                    _hasError = false;
                                    _currentSource = StreamSource(
                                      id: '${_currentSource.id}-backup',
                                      format: 'mp4',
                                      url: _currentSource.backupUrl!,
                                      resolution: '720p',
                                    );
                                  });
                                },
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),

            // 3. On-Screen Display (OSD) Overlay Controls
            if (_showControls && !_hasError)
              Container(
                color: Colors.black.withOpacity(0.45),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Top Bar
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
                      child: Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
                            onPressed: widget.onBack,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(widget.item.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary), overflow: TextOverflow.ellipsis),
                                Text('${widget.item.releaseYear} • ${_currentSource.format.toUpperCase()} • ${widget.item.attribution.licenseType}', style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                              ],
                            ),
                          ),
                          // Subtitles / Audio Selector
                          IconButton(
                            icon: const Icon(Icons.subtitles_outlined, color: AppTheme.textPrimary),
                            tooltip: 'Subtitles & Audio',
                            onPressed: () => _openTrackSelector(context),
                          ),
                          // Quality Selector
                          TextButton(
                            onPressed: () {
                              setState(() {
                                _selectedQuality = _selectedQuality == 'Auto (1080p)' ? '720p HD' : 'Auto (1080p)';
                              });
                            },
                            child: Text(_selectedQuality, style: const TextStyle(color: AppTheme.brandPrimary, fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                    ),

                    // Center Canvas (Large Play/Pause & Dual 10s Seek)
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        IconButton(
                          iconSize: 48,
                          icon: const Icon(Icons.replay_10, color: AppTheme.textPrimary),
                          onPressed: () => _seekBy(-10),
                        ),
                        const SizedBox(width: 32),
                        IconButton(
                          iconSize: 64,
                          icon: Icon(
                            _isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled,
                            color: AppTheme.brandPrimary,
                          ),
                          onPressed: _togglePlayPause,
                        ),
                        const SizedBox(width: 32),
                        IconButton(
                          iconSize: 48,
                          icon: const Icon(Icons.forward_10, color: AppTheme.textPrimary),
                          onPressed: () => _seekBy(10),
                        ),
                      ],
                    ),

                    // Bottom Bar (Seekbar & Counters)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                      child: Column(
                        children: [
                          SliderTheme(
                            data: SliderTheme.of(context).copyWith(
                              activeTrackColor: AppTheme.brandPrimary,
                              inactiveTrackColor: AppTheme.bgSurface3,
                              thumbColor: AppTheme.brandPrimary,
                              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
                              trackHeight: 4,
                            ),
                            child: Slider(
                              value: _positionSeconds.clamp(0.0, _durationSeconds),
                              min: 0.0,
                              max: _durationSeconds > 0 ? _durationSeconds : 1.0,
                              onChanged: (val) {
                                setState(() => _positionSeconds = val);
                                widget.onProgressUpdate?.call(_positionSeconds, _durationSeconds);
                              },
                            ),
                          ),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(_formatTime(_positionSeconds), style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13)),
                              Text('-${_formatTime(_durationSeconds - _positionSeconds)}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    ),
  );
  }
}
