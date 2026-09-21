import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SponsorCampaignData {
  final String id;
  final String title;
  final String sponsorName;
  final String message;
  final String ctaUrl;
  final String ctaLabel;
  final String badgeText;

  const SponsorCampaignData({
    required this.id,
    required this.title,
    required this.sponsorName,
    required this.message,
    required this.ctaUrl,
    required this.ctaLabel,
    required this.badgeText,
  });

  factory SponsorCampaignData.fromJson(Map<String, dynamic> json) {
    return SponsorCampaignData(
      id: json['id'] as String,
      title: json['title'] as String,
      sponsorName: json['sponsorName'] as String,
      message: json['message'] as String,
      ctaUrl: json['ctaUrl'] as String,
      ctaLabel: json['ctaLabel'] as String,
      badgeText: json['badgeText'] as String,
    );
  }
}

class SponsorCard extends StatefulWidget {
  final SponsorCampaignData campaign;
  final VoidCallback? onCtaClick;
  final VoidCallback? onImpression;

  const SponsorCard({
    Key? key,
    required this.campaign,
    this.onCtaClick,
    this.onImpression,
  }) : super(key: key);

  @override
  State<SponsorCard> createState() => _SponsorCardState();
}

class _SponsorCardState extends State<SponsorCard> {
  bool _isFocused = false;

  @override
  void initState() {
    super.initState();
    widget.onImpression?.call();
  }

  @override
  void didUpdateWidget(covariant SponsorCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.campaign.id != widget.campaign.id) {
      widget.onImpression?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    return FocusableActionDetector(
      onShowFocusHighlight: (val) {
        setState(() => _isFocused = val);
      },
      child: Semantics(
        label: 'Sponsor Callout: ${widget.campaign.sponsorName}. ${widget.campaign.message}',
        button: true,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppTheme.bgSurface2,
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            border: Border.all(
              color: _isFocused ? AppTheme.focusDefault : AppTheme.bgSurface3,
              width: _isFocused ? 2.0 : 1.0,
            ),
            boxShadow: _isFocused
                ? [
                    BoxShadow(
                      color: AppTheme.focusDefault.withOpacity(0.4),
                      blurRadius: 10,
                      spreadRadius: 1,
                    )
                  ]
                : null,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.brandPrimary.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      widget.campaign.badgeText.toUpperCase(),
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.brandPrimary,
                        letterSpacing: 0.8,
                      ),
                    ),
                  ),
                  Text(
                    widget.campaign.sponsorName,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                widget.campaign.message,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppTheme.textPrimary,
                  height: 1.35,
                ),
              ),
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.volunteer_activism, size: 14),
                  label: Text(widget.campaign.ctaLabel),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.brandPrimary,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                    ),
                  ),
                  onPressed: widget.onCtaClick,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
