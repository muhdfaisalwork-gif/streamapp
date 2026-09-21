import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_theme.dart';

class TvFocusNodeHistory {
  static final List<String> _historyStack = [];

  static void pushFocus(String nodeId) {
    _historyStack.add(nodeId);
  }

  static String? popFocus() {
    if (_historyStack.isNotEmpty) {
      return _historyStack.removeLast();
    }
    return null;
  }

  static String? peekFocus() {
    if (_historyStack.isNotEmpty) {
      return _historyStack.last;
    }
    return null;
  }

  static void clear() {
    _historyStack.clear();
  }
}

class TvFocusableCard extends StatefulWidget {
  final String id;
  final Widget child;
  final VoidCallback onSelect;
  final bool autofocus;
  final ValueChanged<bool>? onFocusChanged;

  const TvFocusableCard({
    Key? key,
    required this.id,
    required this.child,
    required this.onSelect,
    this.autofocus = false,
    this.onFocusChanged,
  }) : super(key: key);

  @override
  State<TvFocusableCard> createState() => _TvFocusableCardState();
}

class _TvFocusableCardState extends State<TvFocusableCard> {
  late FocusNode _focusNode;
  bool _isFocused = false;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(debugLabel: widget.id);
    _focusNode.addListener(_onFocusChange);

    // Check if this node was the previous focused node
    if (TvFocusNodeHistory.peekFocus() == widget.id) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          _focusNode.requestFocus();
          TvFocusNodeHistory.popFocus();
        }
      });
    }
  }

  void _onFocusChange() {
    setState(() {
      _isFocused = _focusNode.hasFocus;
    });
    widget.onFocusChanged?.call(_isFocused);
  }

  @override
  void dispose() {
    _focusNode.removeListener(_onFocusChange);
    _focusNode.dispose();
    super.dispose();
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.select ||
          event.logicalKey == LogicalKeyboardKey.enter ||
          event.logicalKey == LogicalKeyboardKey.space) {
        widget.onSelect();
        return KeyEventResult.handled;
      }
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      focusNode: _focusNode,
      autofocus: widget.autofocus,
      onKeyEvent: _handleKeyEvent,
      child: AnimatedScale(
        scale: _isFocused ? 1.08 : 1.0,
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOutCubic,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            border: Border.all(
              color: _isFocused ? AppTheme.brandPrimary : Colors.transparent,
              width: _isFocused ? 2.5 : 1.0,
            ),
            boxShadow: _isFocused
                ? [
                    BoxShadow(
                      color: AppTheme.brandPrimary.withOpacity(0.40),
                      blurRadius: 20,
                      spreadRadius: 2,
                      offset: const Offset(0, 8),
                    ),
                  ]
                : [],
          ),
          child: RepaintBoundary(child: widget.child),
        ),
      ),
    );
  }
}
