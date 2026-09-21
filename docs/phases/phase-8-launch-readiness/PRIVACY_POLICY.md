# Privacy Policy

**Platform**: StreamApp — Cross-Platform Legal Streaming Platform  
**Version**: 1.0.0  
**Effective Date**: 2026-09-19  

---

## 1. Privacy Philosophy: Zero Surveillance

StreamApp respects user privacy as a fundamental human right. We reject invasive behavioral tracking, third-party advertising networks, data brokering, and hardware fingerprinting.

### Our Privacy Pledge
- **We DO NOT collect Personally Identifiable Information (PII)** unless you explicitly choose to create an account with an email address.
- **We DO NOT track you across the web** or across external applications.
- **We DO NOT sell, rent, or monetize your data** under any circumstances.
- **We DO NOT use advertising SDKs**, device fingerprinting algorithms, or telemetry beacons from third-party advertising brokers.

---

## 2. Information We Process

### A. Optional User Accounts
- If you register an account: we store your email address, an irreversible scrypt-hashed password digest, and display name.
- Guest mode is fully supported: you can browse, bookmark, and stream without providing any personal data.

### B. Diagnostic Quality of Experience (QoE) Telemetry (Optional)
To troubleshoot video playback failures and buffering issues, the client may send aggregated, anonymous diagnostic metrics:
- Time to First Frame (startup latency in ms)
- Rebuffer stall events and duration
- Adaptive bitrate switching metrics
- Client platform category (e.g. `android-tv`, `windows`)

**Privacy Safeguards**:
- Session IDs are ephemeral random strings rotated on every playback session.
- IP addresses are scrubbed immediately from memory and never written to our database.
- You can disable diagnostic telemetry at any time in Settings, or by enabling Do Not Track (DNT) or Global Privacy Control (GPC). When disabled, zero telemetry packets leave your device.

---

## 3. Local Data Storage & User Control

Bookmarks, playback progress, and UI preferences are stored locally on your device in SQLite/Shared Preferences. You can clear this data at any time by clearing application storage or uninstalling the app.

---

## 4. Compliance with International Privacy Regulations

- **GDPR / UK GDPR**: Full compliance with transparency and data minimization mandates.
- **CCPA / CPRA**: Zero sale or sharing of personal data.
- **COPPA**: StreamApp is suitable for general audiences and collects zero personal information from children.

---

## 5. Contact Information

For privacy inquiries or data erasure requests:  
Email: `privacy@streaming-app.local`
