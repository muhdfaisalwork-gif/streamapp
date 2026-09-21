# Ethical Monetization & Creator Support Framework

**Document ID**: TDR-P6-002  
**Author**: Agent 1 (Product Manager), Agent 12 (Analytics Specialist), Agent 3 (Frontend Engineer)  
**Status**: APPROVED  
**Date**: 2026-09-19  

---

## 1. Ethical Monetization Philosophy

Commercial streaming services increasingly rely on intrusive interstitial ads, surveillance ad-exchanges, and opaque tracking scripts that degrade device performance, consume user bandwidth, and compromise user privacy.

The Cross-Platform Streaming App adopts an **Ethical, Non-Intrusive Monetization Model** rooted in open-source principles:

1. **Zero Playback Interruptions**: No unskippable pre-rolls, mid-rolls, or post-rolls during video playback.
2. **Direct Creator & Archival Support**: Every licensed or open title prominently features direct donation and creator patronage links (e.g. Blender Studio Fund, Internet Archive Preservation Fund).
3. **Transparent Community Sponsorships**: Voluntary banner cards displayed below content details or in dedicated discovery sections, clearly tagged with `Creator Support`, `Public Domain Preservation`, or `Community Sponsor`.
4. **Zero Surveillance Targeting**: Sponsor cards are contextually mapped to content categories (e.g., Blender Studio campaigns displayed on Blender Open Movies) or served in random non-personalized rotation. No behavioral profiling is performed.

---

## 2. Sponsor Campaign Data Model

```sql
CREATE TABLE IF NOT EXISTS sponsor_campaigns (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  sponsor_name TEXT NOT NULL,
  message TEXT NOT NULL,
  cta_url TEXT NOT NULL,
  cta_label TEXT NOT NULL,
  badge_text TEXT NOT NULL,
  media_id TEXT, -- NULL for platform-wide, or bound to a specific movie
  impressions INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL
);
```

---

## 3. Presentation Standards & A11y Guidelines

### Component Specifications (`SponsorCard`)
- **Visual Contrast**: Meets WCAG 2.1 AA with high-contrast text (`#F0F4FC` on `#161F30` card surface, 11.2:1 contrast ratio).
- **Badge Indicator**: Distinct pill badge with `#00E5FF` primary color indicating nature of callout (`CREATOR SUPPORT`, `PUBLIC DOMAIN PRESERVATION`).
- **Focus & Remote Navigation**: Fully accessible on Android TV D-pad and desktop keyboard navigation with glowing 2px border and elevation transform on focus.
- **Screen Reader Semantics**: Decorated with `Semantics(label: "Sponsor Callout: ...", button: true)` for TalkBack and desktop screen readers.

---

## 4. Default Community Campaigns

| Campaign ID | Sponsor Name | Message | Target Link | Badge |
| :--- | :--- | :--- | :--- | :--- |
| `sp-blender-01` | Blender Foundation | Support open-source 3D animation and free creative tools at Blender Studio. | https://fund.blender.org | Creator Support |
| `sp-archive-02` | Internet Archive | Preserving classic cinema, cultural history, and public domain archives for the world. | https://archive.org/donate | Public Domain Preservation |
