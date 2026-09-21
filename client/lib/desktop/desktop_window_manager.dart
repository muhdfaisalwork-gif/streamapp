import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_theme.dart';

class DesktopShortcutManager extends StatelessWidget {
  final Widget child;
  final VoidCallback onPlayPause;
  final VoidCallback onToggleFullscreen;
  final VoidCallback onSeekBackward;
  final VoidCallback onSeekForward;
  final VoidCallback onToggleMute;
  final VoidCallback onCycleSubtitles;
  final VoidCallback onFocusSearch;
  final VoidCallback onEscape;
  final VoidCallback? onQuit;

  const DesktopShortcutManager({
    Key? key,
    required this.child,
    required this.onPlayPause,
    required this.onToggleFullscreen,
    required this.onSeekBackward,
    required this.onSeekForward,
    required this.onToggleMute,
    required this.onCycleSubtitles,
    required this.onFocusSearch,
    required this.onEscape,
    this.onQuit,
  }) : super(key: key);

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;

    final isControl = HardwareKeyboard.instance.isControlPressed;

    // Search shortcut: Ctrl + F
    if (isControl && event.logicalKey == LogicalKeyboardKey.keyF) {
      onFocusSearch();
      return KeyEventResult.handled;
    }

    // Quit shortcut: Ctrl + Q
    if (isControl && event.logicalKey == LogicalKeyboardKey.keyQ) {
      onQuit?.call();
      return KeyEventResult.handled;
    }

    // Playback shortcuts
    if (event.logicalKey == LogicalKeyboardKey.space || event.logicalKey == LogicalKeyboardKey.keyK) {
      onPlayPause();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.keyF || event.logicalKey == LogicalKeyboardKey.f11) {
      onToggleFullscreen();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.keyJ || event.logicalKey == LogicalKeyboardKey.arrowLeft) {
      onSeekBackward();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.keyL || event.logicalKey == LogicalKeyboardKey.arrowRight) {
      onSeekForward();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.keyM) {
      onToggleMute();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.keyC) {
      onCycleSubtitles();
      return KeyEventResult.handled;
    } else if (event.logicalKey == LogicalKeyboardKey.escape) {
      onEscape();
      return KeyEventResult.handled;
    }

    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      autofocus: true,
      onKeyEvent: _handleKeyEvent,
      child: child,
    );
  }
}

class DesktopCustomTitleBar extends StatelessWidget {
  final String title;
  final VoidCallback onMinimize;
  final VoidCallback onMaximize;
  final VoidCallback onClose;

  const DesktopCustomTitleBar({
    Key? key,
    this.title = 'StreamApp Desktop',
    required this.onMinimize,
    required this.onMaximize,
    required this.onClose,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 36,
      color: AppTheme.bgSurface1,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Row(
        children: [
          const Icon(Icons.play_circle_fill, size: 18, color: AppTheme.brandPrimary),
          const SizedBox(width: 8),
          Text(
            title,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
          ),
          const Spacer(),
          // Minimize Button
          IconButton(
            icon: const Icon(Icons.remove, size: 14, color: AppTheme.textMuted),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            onPressed: onMinimize,
          ),
          // Maximize Button
          IconButton(
            icon: const Icon(Icons.crop_square, size: 13, color: AppTheme.textMuted),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            onPressed: onMaximize,
          ),
          // Close Button
          IconButton(
            icon: const Icon(Icons.close, size: 14, color: AppTheme.textMuted),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            hoverColor: Colors.red.withOpacity(0.8),
            onPressed: onClose,
          ),
        ],
      ),
    );
  }
}
