# Photo Manager Automated QA Plan

This document outlines the systematic testing strategy for the Photo Manager project. These tests ensure that both the backend intelligence (AI, Atlas, Duplicate Detection) and the frontend navigation remain stable across releases.

## 🏗️ 4-Tier Testing Strategy

### Tier 1: Launch & Integrity (Critical)
*   **Goal**: Ensure the application is "Ready for Takeoff."
*   **Automated Checks**:
    *   Port 8000 accessibility.
    *   API `/api/health` returns status `ok`.
    *   AI Models (Facenet512 & RetinaFace) are validated via filesystem check.
*   **Manual Touch**: None.

### Tier 2: UI Functional (Tactical)
*   **Goal**: Verify the "Direct Navigation" handlers and modal responsiveness.
*   **Automated Checks (AI-Assisted)**:
    *   Verify the 'Scanner' tab is active by default.
    *   Click through all top-level tabs (Tagging, Search, Atlas) and confirm view isolation (no overlap).
    *   Verify that clicking a photo thumbnail launches the Pro Modal with metadata.
*   **Tools**: Browser Subagent / Playwright.

### Tier 3: Core API Services
*   **Goal**: Ensure data integrity and throughput.
*   **Automated Checks**:
    *   `/api/telemetry`: Validate real-time throughput (TPS) and system load reporting.
    *   `/api/search`: Multi-term case-insensitive filtering (e.g., "Kenya Lion").
    *   `/api/identities`: Validate DB join results for named people.

### Tier 4: Intelligence Verification (Advanced)
*   **Goal**: High-fidelity verification of AI-driven features.
*   **Automated Checks**:
    - **Atlas Temporal Inference**: Verify that photos without GPS correctly "inherit" coordinates from nearby temporal neighbors.
    - **V3 Geocoding Audit**: Verify `/api/tags/top` returns geocoded names (e.g., "Turkey") instead of raw country codes.
    - **Path Rescue**: Confirm that collection-level tags are correctly extracted from complex directory structures.
    - **Duplicate Detection**: Verify Hamming distance clustering in `/api/maintenance/duplicates`.

---

## 🛡️ The Reliability Engine (shield.py)

The `tools/shield.py` script is the primary automated enforcement tool. It should return a **100% (STABLE)** status before any code is committed.

### Usage
```bash
python tools/shield.py
```

*Last Updated: 2026-04-11 (V3 Intelligence Release)*
