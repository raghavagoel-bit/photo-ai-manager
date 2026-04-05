document.addEventListener('DOMContentLoaded', () => {

    // --- State Management ---
    const state = {
        activeTab: 'scanner-sec',
        isScanning: false,
        selectedFaces: new Set(), // For Batch Tagging
        currentSearchPage: 1,
        totalSearchPages: 1
    };

    // --- Navigation Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.page-section');

    const switchTab = (targetId) => {
        state.activeTab = targetId;
        localStorage.setItem('activeTab_v2', targetId);
        
        // UI Updates
        tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-target') === targetId);
        });
        
        sections.forEach(sec => {
            sec.classList.toggle('active', sec.id === targetId);
        });

        // Context-specific loading
        if (targetId === 'tagging-sec') loadUnknownFaces();
        if (targetId === 'review-sec') loadIdentities();
    };

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-target')));
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

    // --- Advanced Search & Filters ---
    const resultsGrid = document.getElementById('search-results');
    const searchInput = document.getElementById('search-input');
    const dateStartInput = document.getElementById('date-start');
    const dateEndInput = document.getElementById('date-end');

    const performSearch = async (page = 1) => {
        const query = searchInput.value;
        const dStart = dateStartInput.value;
        const dEnd = dateEndInput.value;

        resultsGrid.innerHTML = '<p class="log-msg">Running multi-dimensional query...</p>';
        
        let url = `/api/search?query=${encodeURIComponent(query)}&page=${page}&limit=40`;
        if (dStart) url += `&date_start=${dStart}`;
        if (dEnd) url += `&date_end=${dEnd}`;

        try {
            const res = await fetch(url);
            const data = await res.json();
            
            if (!data.results || data.results.length === 0) {
                resultsGrid.innerHTML = '<p class="log-msg">No temporal or tactical matches found.</p>';
                return;
            }
            
            resultsGrid.innerHTML = data.results.map(photo => `
                <div class="gallery-item" onclick="openModal(${photo.id})">
                    <img src="/photo/${photo.id}" alt="TACTICAL DATA">
                    <div class="meta-overlay">
                        <div class="meta-text">${photo.date_taken || 'DATE: UNKNOWN'}</div>
                        <div class="meta-text">CAM: ${photo.camera_model || 'DEFAULT'}</div>
                    </div>
                </div>
            `).join('');

            renderPagination(data.page, data.pages, data.total);
        } catch (e) {
            resultsGrid.innerHTML = '<p class="log-msg" style="color:red">Search relay failed.</p>';
        }
    };

    const renderPagination = (page, totalPages, totalResults) => {
        const pagCnt = document.getElementById('pagination');
        if (totalPages <= 1) { pagCnt.innerHTML = ''; return; }
        
        pagCnt.innerHTML = `
            <button class="kinetic-btn secondary" ${page === 1 ? 'disabled' : ''} id="prev-btn">Prev</button>
            <span style="font-family:'JetBrains Mono'; margin: 0 20px;">PAGE ${page} / ${totalPages}</span>
            <button class="kinetic-btn secondary" ${page === totalPages ? 'disabled' : ''} id="next-btn">Next</button>
        `;
        
        document.getElementById('prev-btn').onclick = () => performSearch(page - 1);
        document.getElementById('next-btn').onclick = () => performSearch(page + 1);
    };

    document.getElementById('search-btn').onclick = () => performSearch(1);

    // --- Pro Modal Logic ---
    const modal = document.getElementById('photo-modal');
    window.openModal = async (photoId) => {
        // In a real app, we might fetch detail data first, but searching already provides some.
        // For V2, we'll just show the image and standard meta from the search result or a new detail API
        document.getElementById('full-img').src = `/photo/${photoId}`;
        modal.style.display = 'flex';
        
        // Fetch detailed meta for modal
        try {
            const res = await fetch(`/api/search?query=id:${photoId}`); // Or a specific metadata endpoint
            // For now, satisfy with placeholders or pull from gallery-item attributes
        } catch(e) {}
    };

    document.getElementById('close-modal-btn').onclick = () => modal.style.display = 'none';
    modal.onclick = (e) => { if(e.target === modal) modal.style.display = 'none'; };

    // Initialize with Persistent or Default Tab
    const savedTab = localStorage.getItem('activeTab_v2');
    switchTab(savedTab || 'scanner-sec');
});
