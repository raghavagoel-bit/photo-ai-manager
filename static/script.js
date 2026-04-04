document.addEventListener('DOMContentLoaded', () => {

    // --- Navigation Logic ---
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.page-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update buttons
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update sections
            sections.forEach(sec => sec.classList.remove('active'));
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // --- AI Health Logic ---
    const checkAIHealth = async () => {
        const healthDiv = document.getElementById('ai-health-status');
        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            if (data.all_ok) {
                healthDiv.innerHTML = '<span class="status-ok">●</span> AI Engine Ready';
                healthDiv.title = "Facenet & RetinaFace verified";
            } else {
                healthDiv.innerHTML = '<span class="status-error">●</span> AI Engine Error';
                healthDiv.title = "Models missing or corrupt. Check console.";
            }
        } catch (e) {
            healthDiv.innerHTML = '<span class="status-warn">●</span> Status Unknown';
        }
    };
    checkAIHealth();

    // --- Scanner Logic ---
    const startScanBtn = document.getElementById('start-scan-btn');
    const scanPathInput = document.getElementById('scan-path');
    const statusIndicator = document.getElementById('status-indicator');
    const scannedCount = document.getElementById('scanned-count');
    const faceCount = document.getElementById('face-count');
    
    let pollInterval;

    const pollStatus = async () => {
        try {
            const res = await fetch('/api/scan/status');
            const data = await res.json();
            
            scannedCount.textContent = data.scanned_count;
            faceCount.textContent = data.face_count;
            
            if (data.is_scanning) {
                statusIndicator.textContent = 'Scanning...';
                statusIndicator.className = 'scanning';
            } else {
                statusIndicator.textContent = 'Idle';
                statusIndicator.className = 'idle';
                clearInterval(pollInterval);
            }
        } catch (e) {
            console.error('Error polling status', e);
        }
    };

    startScanBtn.addEventListener('click', async () => {
        const path = scanPathInput.value;
        if (!path) return alert("Please enter a path");
        
        const formData = new FormData();
        formData.append('path', path);
        
        try {
            const res = await fetch('/api/scan', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                clearInterval(pollInterval);
                pollInterval = setInterval(pollStatus, 1000);
                pollStatus(); // initial call
            } else {
                alert(data.message);
            }
        } catch (e) {
            alert('Failed to start scanner');
        }
    });

    // --- Tagging Logic ---
    const loadUnknownFaces = async () => {
        const grid = document.getElementById('faces-grid');
        grid.innerHTML = '<p>Loading clustered faces from AI Engine...</p>';
        try {
            const res = await fetch('/api/faces?status=unknown&cluster=true');
            const clusters = await res.json();
            
            if(clusters.length === 0) {
                grid.innerHTML = '<p>No unknown faces found. Scan some photos!</p>';
                return;
            }
            
            grid.innerHTML = clusters.map(c => {
                const conf = c.confidence || 1.0;
                let confClass = 'conf-high';
                let cardClass = '';
                if (conf < 0.75) { confClass = 'conf-low'; cardClass = 'low-conf'; }
                else if (conf < 0.9) { confClass = 'conf-med'; cardClass = 'med-conf'; }
                
                return `
                    <div class="face-card ${cardClass}" id="face-${c.id}">
                        <div class="confidence-badge ${confClass}" title="Clustering Confidence: ${Math.round(conf*100)}%"></div>
                        <img src="/thumbnails/${c.thumbnail}" alt="Unknown face">
                        <input type="text" placeholder="Who is this? (${c.clone_ids.length} clones)" onchange="tagFace(${c.id}, this.value, '${c.clone_ids.join(',')}')">
                    </div>
                `;
            }).join('');
        } catch (e) {
            grid.innerHTML = '<p>Failed to load faces</p>';
        }
    };

    document.getElementById('refresh-faces-btn').addEventListener('click', loadUnknownFaces);
    
    // Auto load faces when activating tag tab
    document.querySelector('.nav-btn[data-target="tag-sec"]').addEventListener('click', loadUnknownFaces);

    window.tagFace = async (masterId, name, cloneIdsStr) => {
        if(!name) return;
        const formData = new FormData();
        formData.append('person_name', name);
        formData.append('face_ids', cloneIdsStr || masterId.toString());
        try {
            await fetch(`/api/faces/bulk_tag`, {
                method: 'POST',
                body: formData
            });
            // remove the card dynamically
            document.getElementById(`face-${masterId}`).style.opacity = '0';
            setTimeout(() => {
                document.getElementById(`face-${masterId}`).remove();
            }, 300);
        } catch(e) {
            console.error(e);
            alert("Failed to assign bulk tag");
        }
    };

    // --- Search Logic ---
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const resultsGrid = document.getElementById('search-results');
    const paginationCnt = document.getElementById('pagination-cnt');
    
    let currentSearchPage = 1;
    let lastQuery = "";

    const performSearch = async (page = 1) => {
        const query = searchInput.value.trim();
        if (!query) return;
        
        currentSearchPage = page;
        lastQuery = query;
        
        resultsGrid.innerHTML = '<p>Searching...</p>';
        paginationCnt.innerHTML = '';
        
        try {
            const res = await fetch(`/api/search?query=${encodeURIComponent(query)}&page=${page}&limit=40`);
            const data = await res.json();
            
            // Resilience: Handle both Array (Legacy) and Object (Paginated)
            let results = [];
            let totalPages = 1;
            let totalResults = 0;
            
            if (Array.isArray(data)) {
                results = data;
                totalResults = data.length;
            } else if (data && data.results) {
                results = data.results;
                totalPages = data.pages || 1;
                totalResults = data.total || results.length;
            }
            
            if(!results || results.length === 0) {
                resultsGrid.innerHTML = '<p>No results found</p>';
                return;
            }
            
            resultsGrid.innerHTML = results.map(photo => `
                <div class="gallery-item" onclick="openModal(${photo.id}, '${photo.location_tags}', '${photo.file_path.replace(/\\/g, '\\\\')}')">
                    <img src="/photo/${photo.id}" alt="Photo">
                    <div class="gallery-info">
                        <small>${photo.date_taken || 'Unknown Date'}</small>
                        <p>${photo.location_tags}</p>
                    </div>
                </div>
            `).join('');
            
            renderPagination(page, totalPages, totalResults);
            
        } catch(e) {
            resultsGrid.innerHTML = '<p>Search failed</p>';
        }
    };

    const renderPagination = (page, totalPages, totalResults) => {
        if (totalPages <= 1) return;
        
        paginationCnt.innerHTML = `
            <button class="pagination-btn" id="prev-page" ${page === 1 ? 'disabled' : ''}>Previous</button>
            <span class="page-info">Page ${page} of ${totalPages} <small>(${totalResults} total)</small></span>
            <button class="pagination-btn" id="next-page" ${page === totalPages ? 'disabled' : ''}>Next</button>
        `;
        
        document.getElementById('prev-page').addEventListener('click', () => performSearch(page - 1));
        document.getElementById('next-page').addEventListener('click', () => performSearch(page + 1));
    };

    searchBtn.onclick = () => performSearch(1);
    
    searchInput.onkeypress = (e) => {
        if(e.key === 'Enter') performSearch(1);
    };

    // --- Modal Logic ---
    const modal = document.getElementById("photo-modal");
    const modalImg = document.getElementById("full-resolution-img");
    const captionText = document.getElementById("caption");
    const span = document.getElementsByClassName("close-modal")[0];

    window.openModal = (photoId, loc, path) => {
        modal.style.display = "block";
        modalImg.src = `/photo/${photoId}`;
        captionText.innerHTML = `${loc} <br><small style="color:#666">${path}</small>`;
    };

    span.onclick = () => { modal.style.display = "none"; };
    
    // click anywhere to close
    modal.onclick = (e) => {
        if(e.target === modal) modal.style.display = "none";
    }

});
