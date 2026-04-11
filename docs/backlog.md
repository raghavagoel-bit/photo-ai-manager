# Photo Manager Backlog

This document tracks upcoming features, optimizations, and technical debt for the Antigravity Photos suite.

## 🚀 High Priority (V3.1)

### 1. Interactive Tactical Tags
**Objective**: Transform static metadata tags into interactive discovery vectors.
- **Backend**: Add `/api/tags/top` to return common AI and location tags.
- **Search UI**: Add a "Tactical Tags" cloud at the top of the Search section for one-tap filtering.
- **Modal UX**: Clickable tags in the photo inspector that trigger automated searches.
- **Aesthetics**: Styled `.tactical-tag` components with "Stealth Pro" hover effects.

## 🛠️ Infrastructure & Availability (V4 Expansion)

### 2. Private Remote Access (Stealth Pro)
**Objective**: Securely access the photo library from anywhere in the world without compromising privacy.
- **Tailscale Mesh**: Deploy private networking between phone and host PC.
- **Security**: Implement "Zero Trust" layer for any public-facing tunnels.

### 3. 24/7 Micro-Server Deployment
- **Hardware**: Migrate library to low-power dedicated hardware (Mini-PC/NAS).
- **Power Management**: Implement Wake-on-LAN for hybrid on-demand access from workstations.

## 🎞️ Format & Optimization

### 4. HEIC/HEIF Support
- Implement native support for Apple's HEIC format to support mobile-heavy libraries.

---
*Last Updated: 2026-04-11 (V3.3 Cartography)*