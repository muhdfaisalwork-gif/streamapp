import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

class AnalyticsService {
  final ApiService apiService;
  bool isTelemetryEnabled;
  final List<Map<String, dynamic>> _queue = [];
  Timer? _flushTimer;
  final String sessionId;

  AnalyticsService({
    required this.apiService,
    this.isTelemetryEnabled = true,
  }) : sessionId = _generateSessionId() {
    // Flush batch telemetry every 30 seconds
    _flushTimer = Timer.periodic(const Duration(seconds: 30), (_) => flush());
  }

  static String _generateSessionId() {
    final rand = Random().nextInt(0xFFFFFF).toRadixString(16).padLeft(6, '0');
    return 'sess_${DateTime.now().millisecondsSinceEpoch}_$rand';
  }

  void recordPlaybackStart({
    required String mediaId,
    required String platform,
    required double startupTimeMs,
  }) {
    _enqueue({
      'sessionId': sessionId,
      'mediaId': mediaId,
      'platform': platform,
      'eventType': 'start',
      'startupTimeMs': startupTimeMs,
    });
  }

  void recordBufferStall({
    required String mediaId,
    required String platform,
    required double bufferDurationMs,
  }) {
    _enqueue({
      'sessionId': sessionId,
      'mediaId': mediaId,
      'platform': platform,
      'eventType': 'buffer_stall',
      'bufferDurationMs': bufferDurationMs,
    });
  }

  void recordBitrateShift({
    required String mediaId,
    required String platform,
    required int targetBitrateBps,
  }) {
    _enqueue({
      'sessionId': sessionId,
      'mediaId': mediaId,
      'platform': platform,
      'eventType': 'bitrate_shift',
      'targetBitrateBps': targetBitrateBps,
    });
  }

  void recordPlaybackError({
    required String mediaId,
    required String platform,
    required String errorCode,
  }) {
    _enqueue({
      'sessionId': sessionId,
      'mediaId': mediaId,
      'platform': platform,
      'eventType': 'error',
      'errorCode': errorCode,
    });
  }

  void _enqueue(Map<String, dynamic> event) {
    if (!isTelemetryEnabled) {
      // Immediate privacy drop: zero queuing, zero network payload
      return;
    }
    _queue.add(event);
    if (_queue.length >= 10) {
      flush();
    }
  }

  Future<void> flush() async {
    if (_queue.isEmpty || !isTelemetryEnabled) return;

    final batch = List<Map<String, dynamic>>.from(_queue);
    _queue.clear();

    try {
      await apiService.sendQoEEvents(batch, optOut: !isTelemetryEnabled);
    } catch (e) {
      if (kDebugMode) {
        debugPrint('[AnalyticsService] Failed to flush telemetry batch: $e');
      }
    }
  }

  void dispose() {
    _flushTimer?.cancel();
    flush();
  }
}
