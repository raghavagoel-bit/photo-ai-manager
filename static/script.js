document.addEventListener('DOMContentLoaded', () => {

    // --- State Management ---
    const state = {
        activeTab: 'scanner-sec',
        isScanning: false,
        selectedFaces: new Set(), // For Batch Tagging
        currentSearchPage: 1,
        totalSearchPages: 1,
        canLoadMore: true,
        isLoadingMore: false,
        map: null // Leaflet instance
    };

    // Listen for Global Tab Changes
    window.addEventListener('tabChange', (e) => {
        const targetId = e.detail.targetId;
        console.log("Domain loading triggered for:", targetId);
        
        try {
            if (targetId === 'tagging-sec') loadUnknownFaces();
            if (targetId === 'review-sec') loadIdentities();
            if (targetId === 'atlas-sec') {
                if (typeof L !== 'undefined') initAtlas();
                else console.error("Leaflet.js not loaded.");
            }
            if (targetId === 'maintenance-sec') loadMaintenance();
            if (targetId === 'search-sec') loadTagCloud();
        } catch (err) {
            console.error("Tab Initialization Failure:", err);
        }
    });

    // --- Telemetry & Health ---
    const telemetryLog = document.getElementById('telemetry-log');
    const aiHealth = document.getElementById('ai-health');

    const addLog = (msg, isFile = false) => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        const time = new Error().stack ? new Date().toLocaleTimeString() : ''; // Get current time
        entry.innerHTML = `
            <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
            <span class="log-msg">${msg}</span>
        `;
        if (isFile) entry.querySelector('.log-msg').classList.add('log-file');
        
        telemetryLog.prepend(entry);
        if (telemetryLog.children.length > 50) telemetryLog.lastChild.remove();
    };

    const updateTelemetry = async () => {
        try {
            const res = await fetch('/api/telemetry');
            const data = await res.json();

            // Update Dash Cards
            document.getElementById('scanned-count').textContent = data.is_scanning ? data.scanned_count : data.total_photos;
            document.getElementById('tps-value').textContent = data.tasks_per_second.toFixed(1);
            document.getElementById('ai-score').textContent = data.ai_score;
            document.getElementById('scan-status-text').textContent = data.is_scanning ? 'ACTIVE' : 'IDLE';
            document.getElementById('scan-card').classList.toggle('active-pulse', data.is_scanning);
            
            // Update Phase Indicator
            const phaseEl = document.getElementById('scan-phase');
            if (phaseEl) {
                phaseEl.textContent = data.phase || (data.is_scanning ? "Processing..." : "System Idle");
            }

            // Update Progress Bar (Placeholder logic for now)
            const progressBar = document.getElementById('scan-progress-bar');
            if (data.is_scanning) {
                // If scanned_count is increasing, we pulse the bar
                const width = (data.scanned_count % 100);
                progressBar.style.width = `${width}%`;
            } else {
                progressBar.style.width = '0%';
            }
            if (data.ai_score > 0) {
                aiHealth.textContent = "AI ENGINE ONLINE";
                aiHealth.className = "health-indicator status-ok";
            } else {
                aiHealth.textContent = "AI ENGINE OFFLINE";
                aiHealth.className = "health-indicator status-error";
            }

            if (data.is_scanning && !state.isScanning) {
                addLog("Scanning engine engaged.");
            } else if (!data.is_scanning && state.isScanning) {
                addLog("Scanning complete. System idle.");
            }
            state.isScanning = data.is_scanning;

        } catch (e) {
            console.error("Telemetry failure", e);
        }
    };

    setInterval(updateTelemetry, 2000);

    // --- Scanner Initialization ---
    const startScanBtn = document.getElementById('start-scan-btn');
    const scanPathInput = document.getElementById('scan-path');

    startScanBtn.addEventListener('click', async () => {
        const path = scanPathInput.value;
        if (!path) return alert("System requires a valid directory path.");
        
        const formData = new FormData();
        formData.append('path', path);
        
        try {
            const res = await fetch('/api/scan', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                addLog(`Path accepted: ${path}. Initializing worker...`);
            } else {
                addLog(`Scan Rejected: ${data.message}`);
                alert(data.message);
            }
        } catch (e) {
            addLog("Buffer connection error.");
        }
    });

    // --- Batch Tagging Logic ---
    const facesGrid = document.getElementById('faces-grid');
    const batchBar = document.getElementById('batch-bar');
    const selectionCount = document.getElementById('selection-count');
    const batchNameInput = document.getElementById('batch-name');

    const updateBatchUI = () => {
        const count = state.selectedFaces.size;
        selectionCount.textContent = `${count} clusters selected`;
        batchBar.classList.toggle('active', count > 0);
    };

    const toggleFaceSelection = (faceId, cardEl) => {
        if (state.selectedFaces.has(faceId)) {
            state.selectedFaces.delete(faceId);
            cardEl.classList.remove('selected');
        } else {
            state.selectedFaces.add(faceId);
            cardEl.classList.add('selected');
        }
        updateBatchUI();
    };

    const loadUnknownFaces = async () => {
        facesGrid.innerHTML = '<p class="log-msg">Decrypting unknown clusters...</p>';
        try {
            const res = await fetch('/api/faces?status=unknown&cluster=true');
            const clusters = await res.json();
            
            if (clusters.length === 0) {
                facesGrid.innerHTML = '<p class="log-msg">No unmapped clusters detected.</p>';
                return;
            }
            
            facesGrid.innerHTML = '';
            clusters.forEach(c => {
                const card = document.createElement('div');
                card.className = 'id-card';
                card.dataset.ids = c.clone_ids.join(',');
                card.innerHTML = `
                    <div class="sel-tick">✔</div>
                    <img src="/thumbnails/${c.thumbnail}" alt="Cluster">
                    <div class="name-tag">Cluster of ${c.clone_ids.length}</div>
                `;
                card.onclick = () => toggleFaceSelection(c.id, card);
                facesGrid.appendChild(card);
            });
        } catch (e) {
            facesGrid.innerHTML = '<p class="log-msg" style="color:red">Access denied to AI buffer.</p>';
        }
    };

    document.getElementById('batch-tag-btn').addEventListener('click', async () => {
        const name = batchNameInput.value.trim();
        if (!name) return alert("Identification name required.");
        
        // Collect all IDs from selected clusters
        let allIds = [];
        state.selectedFaces.forEach(masterId => {
            const card = [...facesGrid.children].find(c => c.onclick && c.onclick.toString().includes(masterId)); 
            // Better to use data attributes
        });
        
        // Refactored: get all IDs from data attributes of selected cards
        const selectedCards = document.querySelectorAll('.id-card.selected');
        selectedCards.forEach(card => {
            allIds.push(...card.dataset.ids.split(','));
        });

        const formData = new FormData();
        formData.append('person_name', name);
        formData.append('face_ids', allIds.join(','));

        try {
            const res = await fetch('/api/faces/bulk_tag', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                addLog(`Identified ${allIds.length} images as ${name}.`);
                state.selectedFaces.clear();
                updateBatchUI();
                loadUnknownFaces();
                batchNameInput.value = '';
            }
        } catch (e) {
            alert("Identification sync error.");
        }
    });

    document.getElementById('cancel-batch-btn').onclick = () => {
        state.selectedFaces.clear();
        document.querySelectorAll('.id-card').forEach(c => c.classList.remove('selected'));
        updateBatchUI();
    };

    // --- Identity Review Logic ---
    const identitiesList = document.getElementById('identities-list');

    const loadIdentities = async () => {
        identitiesList.innerHTML = '<p class="log-msg">Accessing Identity Manifest...</p>';
        identitiesList.style.display = 'flex';
        document.getElementById('review-detail').style.display = 'none';

        try {
            const res = await fetch('/api/identities');
            const data = await res.json();
            
            if (data.length === 0) {
                identitiesList.innerHTML = '<p class="log-msg">No identified citizens found.</p>';
                return;
            }
            
            identitiesList.innerHTML = data.map(person => `
                <div class="person-row">
                    <div style="display:flex; align-items:center; gap:20px">
                        <img src="/thumbnails/${person.sample_thumbnail}" style="width:40px; height:40px; object-fit:cover; border:1px solid var(--primary)">
                        <div class="person-info">
                            <h3>${person.name}</h3>
                            <span>Verified Presence: ${person.face_count} Vectors</span>
                        </div>
                    </div>
                    <button class="kinetic-btn secondary" onclick="reviewPerson(${person.id}, '${person.name}')">View Clusters</button>
                </div>
            `).join('');
        } catch (e) {
            identitiesList.innerHTML = '<p class="log-msg">Manifest retrieval failed.</p>';
        }
    };

    window.reviewPerson = async (id, name) => {
        identitiesList.style.display = 'none';
        const detailView = document.getElementById('review-detail');
        const grid = document.getElementById('cluster-faces-grid');
        const title = document.getElementById('review-person-name');
        
        detailView.style.display = 'block';
        title.textContent = `IDENTITY: ${name}`;
        grid.innerHTML = '<p class="log-msg">Loading identity vectors...</p>';

        try {
            const res = await fetch(`/api/identity/${id}/clusters`);
            const faces = await res.json();
            
            grid.innerHTML = faces.map(f => `
                <div class="id-card review-card" id="review-face-${f.id}">
                    <button class="remove-btn" onclick="untagFace(event, ${f.id})" title="Remove from identity">×</button>
                    <img src="/thumbnails/${f.thumbnail_path}" alt="Face">
                </div>
            `).join('');
        } catch (e) {
            grid.innerHTML = '<p class="log-msg">Error loading clusters.</p>';
        }
    };

    window.untagFace = async (event, faceId) => {
        if (event) event.stopPropagation();
        
        // Optimistic UI: Remove immediately from sight
        const el = document.getElementById(`review-face-${faceId}`);
        if (el) {
            el.style.opacity = '0';
            el.style.transform = 'scale(0.8)';
            setTimeout(() => { if(el) el.style.display = 'none'; }, 300);
        }

        try {
            const res = await fetch(`/api/faces/${faceId}/untag`, { method: 'POST' });
            if (res.ok) {
                addLog(`Vector ${faceId} detached from identity.`);
                // If we are currently searching for this person or others, refresh the results
                if (searchInput.value.trim().length > 0) {
                    performSearch(state.currentSearchPage);
                }
            } else {
                throw new Error("Sync failed");
            }
        } catch (e) {
            // Revert on failure
            if (el) {
                el.style.display = 'block';
                el.style.opacity = '1';
                el.style.transform = 'scale(1)';
            }
            alert("Sync failure: Identity vector could not be detached.");
        }
    };

    document.getElementById('back-to-identities').onclick = loadIdentities;

    // --- Advanced Search & Infinite Scroll ---
    const resultsGrid = document.getElementById('search-results');
    const searchInput = document.getElementById('search-input');
    const dateStartInput = document.getElementById('date-start');
    const dateEndInput = document.getElementById('date-end');
    const scrollTrigger = document.getElementById('infinite-scroll-trigger');
    const scrollSpinner = document.getElementById('infinite-spinner');

    const performSearch = async (page = 1, append = false) => {
        if (!append) {
            resultsGrid.innerHTML = '';
            state.currentSearchPage = 1;
            state.canLoadMore = true;
            // Add skeleton items
            for(let i=0; i<8; i++) {
                const skel = document.createElement('div');
                skel.className = 'gallery-item skeleton';
                skel.style.height = `${200 + Math.random() * 200}px`;
                resultsGrid.appendChild(skel);
            }
        }
        
        state.isLoadingMore = true;
        if (scrollSpinner) scrollSpinner.style.display = 'block';

        const query = searchInput.value;
        const dStart = dateStartInput.value;
        const dEnd = dateEndInput.value;
        
        let url = `/api/search?query=${encodeURIComponent(query)}&page=${page}&limit=100`;
        if (dStart) url += `&date_start=${dStart}`;
        if (dEnd) url += `&date_end=${dEnd}`;

        try {
            const res = await fetch(url);
            const data = await res.json();
            
            if (!append) resultsGrid.innerHTML = '';

            if (!data.results || data.results.length === 0) {
                if (!append) resultsGrid.innerHTML = '<p class="log-msg">No tactical matches found.</p>';
                state.canLoadMore = false;
                return;
            }
            
            data.results.forEach(photo => {
                const item = document.createElement('div');
                item.className = 'gallery-item';
                // Use tiered thumbnail if available, else full photo
                const imgSrc = photo.thumbnail_path ? `/thumbnails/${photo.thumbnail_path}` : `/photo/${photo.id}`;
                item.innerHTML = `
                    <img src="${imgSrc}" alt="Tactical Data" loading="lazy">
                    <div class="meta-overlay">
                        <div class="meta-text">${photo.date_taken || 'DATE: UNKNOWN'}</div>
                        <div class="meta-text">CAM: ${photo.camera_model || 'DEFAULT'}</div>
                    </div>
                `;
                item.onclick = () => openModal(photo.id);
                resultsGrid.appendChild(item);
            });

            state.currentSearchPage = page;
            state.totalSearchPages = data.pages;
            if (page >= data.pages) state.canLoadMore = false;

        } catch (e) {
            if (!append) resultsGrid.innerHTML = '<p class="log-msg" style="color:red">Search relay failed.</p>';
        } finally {
            state.isLoadingMore = false;
            if (scrollSpinner) scrollSpinner.style.display = 'none';
        }
    };

    // Intersection Observer for Infinite Scroll
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && state.canLoadMore && !state.isLoadingMore && state.activeTab === 'search-sec') {
            performSearch(state.currentSearchPage + 1, true);
        }
    }, { threshold: 0.1 });

    if (scrollTrigger) observer.observe(scrollTrigger);

    document.getElementById('search-btn').onclick = () => performSearch(1);
    
    // Trigger search on Enter key
    searchInput.onkeypress = (e) => {
        if (e.key === 'Enter') performSearch(1);
    };

    const loadTagCloud = async () => {
        const cloud = document.getElementById('tactical-cloud');
        if (!cloud) return;
        
        try {
            const res = await fetch('/api/tags/top');
            const tags = await res.json();
            
            // Clear but keep label
            cloud.innerHTML = '<div class="cloud-label">Intelligence Manifest</div>';
            
            tags.forEach(item => {
                const chip = document.createElement('div');
                chip.className = 'tactical-tag';
                chip.innerHTML = `${item.tag} <span class="tag-count">${item.count}</span>`;
                chip.onclick = () => {
                    searchInput.value = item.tag;
                    performSearch(1);
                };
                cloud.appendChild(chip);
            });
        } catch (e) {
            console.error("Cloud hydration failure", e);
        }
    };

    // --- Atlas (Map View) Logic ---
    const initAtlas = async () => {
        if (state.map) return; // Already init

        setTimeout(async () => {
            state.map = L.map('map').setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(state.map);

            await loadAtlasData();
        }, 300); // Small delay to ensure container is visible
    };

    const loadAtlasData = async () => {
        try {
            const res = await fetch('/api/atlas');
            const data = await res.json();
            
            document.getElementById('atlas-stats').textContent = `Satellite link stable. Synchronized ${data.length} geographic vectors.`;

            const markers = L.markerClusterGroup({
                chunkedLoading: true,
                maxClusterRadius: 50
            });

            data.forEach(p => {
                const marker = L.marker([p.latitude, p.longitude]);
                const color = p.is_inferred ? 'var(--accent)' : 'var(--primary)';
                const statusStr = p.is_inferred ? `INFERRED (${p.location_tags || 'Temporal'})` : 'EXPLICIT (EXIF)';
                
                marker.bindPopup(`
                    <div style="text-align:center">
                        <img src="/thumbnails/${p.thumbnail_path}" class="atlas-popup-img">
                        <div style="color:var(--primary); font-weight:bold; margin-top:5px; font-size:11px;">${p.location_tags || 'Unknown Sector'}</div>
                        <div style="color:${color}; font-size:10px; margin-top:2px; opacity:0.8;">${statusStr}</div>
                        <div style="font-size:10px; opacity:0.6">${p.date_taken}</div>
                        <button class="kinetic-btn secondary" style="padding:4px 8px; font-size:10px; margin-top:5px;" onclick="openModal(${p.id})">Inspect</button>
                    </div>
                `);
                markers.addLayer(marker);
            });
            
            state.map.addLayer(markers);
        } catch (e) {
            document.getElementById('atlas-stats').textContent = "Satellite link failed. Interference detected.";
        }
    };

    // --- Maintenance (Duplicates) Logic ---
    const loadMaintenance = () => {
        // Just UI prep
    };

    document.getElementById('find-duplicates-btn').addEventListener('click', async () => {
        const container = document.getElementById('duplicates-container');
        container.innerHTML = '<p class="log-msg">Calculating biometric distances and perceptual hashes...</p>';
        
        try {
            const res = await fetch('/api/maintenance/duplicates');
            const data = await res.json();
            
            if (data.length === 0) {
                container.innerHTML = '<p class="log-msg">No near-duplicates detected. Library integrity 100%.</p>';
                return;
            }
            
            container.innerHTML = data.map((group, idx) => `
                <div class="duplicate-group">
                    <h3>Group Delta-${idx} (${group.length} Similar Sectors)</h3>
                    <div class="pro-grid">
                        ${group.map(p => `
                            <div class="id-card" onclick="openModal(${p.id})">
                                <img src="/thumbnails/${p.thumbnail_path}">
                                <div class="name-tag">${p.date_taken || 'Unknown Date'}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
        } catch (e) {
            container.innerHTML = '<p class="log-msg" style="color:red">Maintenance protocol failure.</p>';
        }
    });

    // --- Pro Modal Logic ---
    const modal = document.getElementById('photo-modal');
    window.openModal = async (photoId) => {
        const modalImg = document.getElementById('full-img');
        modalImg.src = ''; // Clear old src
        modal.style.display = 'flex';
        
        // Fetch detailed meta for modal
        try {
            const res = await fetch(`/api/search?query=id:${photoId}`); 
            const data = await res.json();
            if (data.results && data.results.length > 0) {
                const p = data.results[0];
                modalImg.src = p.thumbnail_path ? `/thumbnails/${p.thumbnail_path}` : `/photo/${p.id}`;
                document.getElementById('meta-path').textContent = p.file_path;
                document.getElementById('meta-date').textContent = p.date_taken || "Unknown";
                document.getElementById('meta-camera').textContent = `${p.camera_model || "Unknown"} ${p.latitude ? `(${p.latitude.toFixed(4)}, ${p.longitude.toFixed(4)})` : "(No GPS)"}`;
                document.getElementById('meta-tags').textContent = p.ai_tags || "None detected";
            }
        } catch(e) {
            console.error("Modal sync failure", e);
        }
    };

    document.getElementById('close-modal-btn').onclick = () => modal.style.display = 'none';
    modal.onclick = (e) => { if(e.target === modal) modal.style.display = 'none'; };

    // Initialize with Persistent or Default Tab
    const savedTab = localStorage.getItem('activeTab_v2');
    switchTab(savedTab || 'scanner-sec');
});
