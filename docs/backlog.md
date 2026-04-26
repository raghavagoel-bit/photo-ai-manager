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

## 🧠 AI Intelligence & Vision (V3.4)

### 5. Two-Pass Vision LLM Geocoder
**Impact**: High | **Effort**: Medium
- **Concept**: Fallback geocoding for photos without GPS or iconic CLIP matches.
- **Implementation**: Send low-confidence photos to a local Ollama Vision LLM (e.g., Qwen2.5-VL or Llama-3.2-Vision). Perform background OCR (reading street signs/menus) and zero-shot geographic deduction to hydrate the database.

### 6. Reverse Image / Similarity Search
**Impact**: High | **Effort**: Low
- **Concept**: "Find photos visually similar to this one" without keyword reliance.
- **Implementation**: Run vector cosine similarity search against the already stored 512-d FaceNet or CLIP embeddings in the SQLite database.

### 7. Duplicate Detection & Pruning
**Impact**: High | **Effort**: Low
- **Concept**: Identify and clear exact or near-duplicates (e.g., burst shots) to save disk space.
- **Implementation**: Use perceptual hashing (pHash) or existing AI embeddings (e.g., >0.99 cosine similarity + temporal proximity < 5 seconds) to cluster duplicates for review.

## 🗃️ Library Management

### 8. Bulk Metadata & Tag Management
**Impact**: Medium | **Effort**: High
- **Concept**: Correct AI mistakes across multiple photos simultaneously.
- **Implementation**: Add a multi-select mode to the Stealth UI. Create API endpoints for batch overrides of tags, GPS coordinates, or timestamps.

---
*Last Updated: 2026-04-23 (Immich Evaluation & Vision LLM Integration)*