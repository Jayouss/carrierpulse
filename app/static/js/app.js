/**
 * Fresno Carrier Finder - Frontend Application
 * Minimal Enterprise Utility interaction architecture
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    currentScreen: 'dashboard',
    settings: null,
    scanProgress: null,
    records: [],
    filteredRecords: [],
    activeFilterStatus: 'Comcast Match',
    activeFilterCategory: 'all',
    searchQuery: '',
    sortCol: 'name',
    sortAsc: true,
    currentPage: 1,
    pageSize: 15,
    eventSource: null,
    customCsvContent: null,
    selectedRecord: null,
  };

  // DOM Elements Cache
  const views = {
    dashboard: document.getElementById('view-dashboard'),
    newScan: document.getElementById('view-new-scan'),
    results: document.getElementById('view-results'),
    settings: document.getElementById('view-settings'),
  };

  const navButtons = document.querySelectorAll('.sidebar-nav .nav-item');
  const navResultsCount = document.getElementById('nav-results-count');
  const sidebarApiStatus = document.getElementById('sidebar-api-status');

  // Dashboard KPIs & Activity
  const dashKpiBusinesses = document.getElementById('kpi-dash-businesses');
  const dashKpiChecked = document.getElementById('kpi-dash-checked');
  const dashKpiComcast = document.getElementById('kpi-dash-comcast');
  const dashKpiPossible = document.getElementById('kpi-dash-possible');
  const dashEngineState = document.getElementById('dash-engine-state');
  const dashStageText = document.getElementById('dash-stage-text');
  const dashProgressFill = document.getElementById('dash-progress-fill');
  const dashProgressCounts = document.getElementById('dash-progress-counts');
  const dashCostTag = document.getElementById('dash-cost-tag');
  const btnDashViewResults = document.getElementById('btn-dash-view-results');

  // New Scan Controls
  const formScanConfig = document.getElementById('scan-config-form');
  const inputMaxBiz = document.getElementById('input-max-biz');
  const inputMaxLookups = document.getElementById('input-max-lookups');
  const scanEstCostDisplay = document.getElementById('scan-est-cost-display');
  const costTwilioPart = document.getElementById('cost-twilio-part');
  const costGooglePart = document.getElementById('cost-google-part');
  const btnStartScan = document.getElementById('btn-start-scan');
  const btnStopScan = document.getElementById('btn-stop-scan');
  const liveStageBadge = document.getElementById('live-stage-badge');
  const liveMetricFound = document.getElementById('live-metric-found');
  const liveMetricChecked = document.getElementById('live-metric-checked');
  const liveMetricComcast = document.getElementById('live-metric-comcast');
  const liveMetricPossible = document.getElementById('live-metric-possible');
  const liveProgressFill = document.getElementById('live-progress-fill');
  const liveStageDesc = document.getElementById('live-stage-description');
  const liveEstCostReadout = document.getElementById('live-est-cost-readout');
  const liveSourceAttribution = document.getElementById('live-source-attribution');
  const customCsvContainer = document.getElementById('custom-csv-upload-container');
  const customCsvFileInput = document.getElementById('custom-csv-file-input');
  const customCsvStatus = document.getElementById('custom-csv-status');

  // Results Table Elements
  const resultsTbody = document.getElementById('results-tbody');
  const resultsEmptyState = document.getElementById('results-empty-state');
  const resultsCountText = document.getElementById('results-count-text');
  const resultsSearchInput = document.getElementById('results-search-input');
  const filterMatchStatus = document.getElementById('filter-match-status');
  const filterCategory = document.getElementById('filter-category');
  const resultsAttributionText = document.getElementById('results-attribution-text');
  const paginationInfo = document.getElementById('pagination-info');
  const btnPrevPage = document.getElementById('btn-prev-page');
  const btnNextPage = document.getElementById('btn-next-page');

  // Drawer & Modal Elements
  const drawerOverlay = document.getElementById('record-drawer-overlay');
  const drawerCloseBtn = document.getElementById('drawer-close-btn');
  const drawerBizName = document.getElementById('drawer-biz-name');
  const drawerBizContent = document.getElementById('drawer-biz-content');

  const exportModalBackdrop = document.getElementById('export-modal-backdrop');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const btnCancelExport = document.getElementById('btn-cancel-export');
  const btnConfirmExport = document.getElementById('btn-confirm-export');
  const btnOpenExportModal = document.getElementById('btn-open-export-modal');
  const exportComplianceWarning = document.getElementById('export-compliance-warning');

  // Settings Elements
  const settingGoogleKey = document.getElementById('setting-google-key');
  const settingTwilioAccountSid = document.getElementById('setting-twilio-account-sid');
  const settingTwilioKeySid = document.getElementById('setting-twilio-key-sid');
  const settingTwilioSecret = document.getElementById('setting-twilio-secret');
  const btnSaveSettings = document.getElementById('btn-save-settings');
  const btnTestGoogle = document.getElementById('btn-test-google');
  const btnTestTwilio = document.getElementById('btn-test-twilio');
  const settingsStatusBanner = document.getElementById('settings-status-banner');

  // ==========================================================================
  // Navigation & Screen Management
  // ==========================================================================
  function switchScreen(screenName) {
    state.currentScreen = screenName;
    Object.keys(views).forEach((key) => {
      if (views[key]) views[key].classList.remove('active');
    });

    navButtons.forEach((btn) => {
      if (btn.getAttribute('data-screen') === screenName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    if (screenName === 'dashboard' && views.dashboard) views.dashboard.classList.add('active');
    if (screenName === 'new-scan' && views.newScan) views.newScan.classList.add('active');
    if (screenName === 'results' && views.results) {
      views.results.classList.add('active');
      refreshResultsTable();
    }
    if (screenName === 'settings' && views.settings) views.settings.classList.add('active');
  }

  navButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const scr = btn.getAttribute('data-screen');
      if (scr) switchScreen(scr);
    });
  });

  document.getElementById('btn-goto-new-scan')?.addEventListener('click', () => switchScreen('new-scan'));
  btnDashViewResults?.addEventListener('click', () => switchScreen('results'));

  // Quick Demo Run Button
  document.getElementById('btn-quick-demo')?.addEventListener('click', () => {
    switchScreen('new-scan');
    // Set radio to demo
    const demoRadio = document.querySelector('input[name="provider_mode"][value="demo"]');
    if (demoRadio) demoRadio.checked = true;
    updateCostEstimate();
    startScan();
  });

  // Password Visibility Toggles
  document.querySelectorAll('.btn-toggle-eye').forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
      }
    });
  });

  // ==========================================================================
  // Settings & Credential API Calls
  // ==========================================================================
  async function loadSettings() {
    try {
      const res = await fetch('/api/settings');
      if (!res.ok) return;
      const data = await res.json();
      state.settings = data;
      renderSettingsStatus(data);
    } catch (e) {
      console.error('Error loading settings:', e);
    }
  }

  function renderSettingsStatus(data) {
    if (!sidebarApiStatus) return;

    if (data.is_configured) {
      sidebarApiStatus.innerHTML = `
        <span class="status-dot status-configured"></span>
        <span class="status-text">APIs Connected</span>
      `;
    } else {
      sidebarApiStatus.innerHTML = `
        <span class="status-dot status-unconfigured"></span>
        <span class="status-text">Setup Required / Demo</span>
      `;
    }

    if (data.google && data.google.has_key && settingGoogleKey) {
      settingGoogleKey.placeholder = `Configured (${data.google.masked_key})`;
    }
    if (data.twilio && settingTwilioKeySid) {
      if (data.twilio.api_key_sid_masked) {
        settingTwilioKeySid.placeholder = `Configured (${data.twilio.api_key_sid_masked})`;
      }
      if (data.twilio.account_sid_masked && settingTwilioAccountSid) {
        settingTwilioAccountSid.placeholder = `Configured (${data.twilio.account_sid_masked})`;
      }
      if (data.twilio.has_secret && settingTwilioSecret) {
        settingTwilioSecret.placeholder = 'Configured (••••••••)';
      }
    }
  }

  btnSaveSettings?.addEventListener('click', async () => {
    const payload = {};
    if (settingGoogleKey.value.trim()) payload.google_places_api_key = settingGoogleKey.value.trim();
    if (settingTwilioAccountSid.value.trim()) payload.twilio_account_sid = settingTwilioAccountSid.value.trim();
    if (settingTwilioKeySid.value.trim()) payload.twilio_api_key_sid = settingTwilioKeySid.value.trim();
    if (settingTwilioSecret.value.trim()) payload.twilio_api_secret = settingTwilioSecret.value.trim();

    try {
      btnSaveSettings.disabled = true;
      btnSaveSettings.textContent = 'Saving...';
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      btnSaveSettings.disabled = false;
      btnSaveSettings.textContent = 'Save Credentials';

      if (res.ok) {
        showStatusBanner('success', data.message || 'Credentials saved securely.');
        // Clear plaintext inputs
        settingGoogleKey.value = '';
        settingTwilioAccountSid.value = '';
        settingTwilioKeySid.value = '';
        settingTwilioSecret.value = '';
        loadSettings();
      } else {
        showStatusBanner('error', data.detail || 'Failed to save settings.');
      }
    } catch (e) {
      btnSaveSettings.disabled = false;
      btnSaveSettings.textContent = 'Save Credentials';
      showStatusBanner('error', 'Network error saving settings.');
    }
  });

  btnTestGoogle?.addEventListener('click', async () => {
    try {
      btnTestGoogle.disabled = true;
      btnTestGoogle.textContent = 'Testing Google...';
      const res = await fetch('/api/settings/test-google', { method: 'POST' });
      const data = await res.json();
      btnTestGoogle.disabled = false;
      btnTestGoogle.textContent = 'Test Google Places';

      if (data.success) {
        showStatusBanner('success', data.message);
      } else {
        showStatusBanner('error', data.message);
      }
    } catch (e) {
      btnTestGoogle.disabled = false;
      btnTestGoogle.textContent = 'Test Google Places';
      showStatusBanner('error', 'Failed to connect to test endpoint.');
    }
  });

  btnTestTwilio?.addEventListener('click', async () => {
    try {
      btnTestTwilio.disabled = true;
      btnTestTwilio.textContent = 'Testing Twilio...';
      const res = await fetch('/api/settings/test-twilio', { method: 'POST' });
      const data = await res.json();
      btnTestTwilio.disabled = false;
      btnTestTwilio.textContent = 'Test Twilio';

      if (data.success) {
        showStatusBanner('success', data.message);
      } else {
        showStatusBanner('error', data.message);
      }
    } catch (e) {
      btnTestTwilio.disabled = false;
      btnTestTwilio.textContent = 'Test Twilio';
      showStatusBanner('error', 'Failed to connect to test endpoint.');
    }
  });

  function showStatusBanner(type, message) {
    if (!settingsStatusBanner) return;
    settingsStatusBanner.className = `status-banner ${type}`;
    settingsStatusBanner.textContent = message;
    settingsStatusBanner.style.display = 'block';
  }

  // ==========================================================================
  // Cost Calculator
  // ==========================================================================
  function updateCostEstimate() {
    const maxLookups = parseInt(inputMaxLookups?.value || 25, 10);
    const maxBiz = parseInt(inputMaxBiz?.value || 50, 10);
    const selectedProvider = document.querySelector('input[name="provider_mode"]:checked')?.value || 'demo';

    let twilioEst = maxLookups * 0.005;
    let googleEst = 0.0;

    if (selectedProvider === 'google_places') {
      const searches = Math.max(1, Math.ceil(maxBiz / 20));
      googleEst = searches * 0.032;
    } else if (selectedProvider === 'demo') {
      twilioEst = 0.0;
      googleEst = 0.0;
    }

    const total = twilioEst + googleEst;
    if (scanEstCostDisplay) scanEstCostDisplay.textContent = `$${total.toFixed(3)}`;
    if (costTwilioPart) costTwilioPart.textContent = `$${twilioEst.toFixed(3)}`;
    if (costGooglePart) costGooglePart.textContent = `$${googleEst.toFixed(3)}`;
  }

  inputMaxBiz?.addEventListener('input', updateCostEstimate);
  inputMaxLookups?.addEventListener('input', updateCostEstimate);
  document.querySelectorAll('input[name="provider_mode"]').forEach((radio) => {
    radio.addEventListener('change', (e) => {
      const mode = e.target.value;
      if (customCsvContainer) {
        customCsvContainer.style.display = mode === 'licensed_dataset' ? 'block' : 'none';
      }
      updateCostEstimate();
    });
  });

  // Custom CSV Upload Handler
  customCsvFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      customCsvStatus.textContent = 'Reading CSV...';
      const res = await fetch('/api/import/csv', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        // Read file content locally as text for the scan request
        const reader = new FileReader();
        reader.onload = (evt) => {
          state.customCsvContent = evt.target.result;
          customCsvStatus.textContent = `✓ Loaded ${data.row_count} businesses from ${file.name}`;
        };
        reader.readAsText(file);
      } else {
        customCsvStatus.textContent = `Error: ${data.detail || 'Upload failed'}`;
      }
    } catch (err) {
      customCsvStatus.textContent = 'Upload error.';
    }
  });

  // ==========================================================================
  // Scan Execution & SSE Streaming
  // ==========================================================================
  async function startScan() {
    const selectedCats = Array.from(
      document.querySelectorAll('input[name="scan_category"]:checked')
    ).map((cb) => cb.value);

    if (selectedCats.length === 0) {
      alert('Please select at least one business category.');
      return;
    }

    const providerMode = document.querySelector('input[name="provider_mode"]:checked')?.value || 'demo';
    const maxBiz = parseInt(inputMaxBiz.value, 10) || 50;
    const maxLookups = parseInt(inputMaxLookups.value, 10) || 25;

    const payload = {
      categories: selectedCats,
      max_businesses: maxBiz,
      max_lookups: maxLookups,
      provider_mode: providerMode,
      max_spend_guard_dollars: 5.0,
      custom_csv_content: providerMode === 'licensed_dataset' ? state.customCsvContent : null,
    };

    try {
      btnStartScan.style.display = 'none';
      btnStopScan.style.display = 'inline-flex';

      const res = await fetch('/api/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || 'Failed to start scan.');
        btnStartScan.style.display = 'inline-flex';
        btnStopScan.style.display = 'none';
        return;
      }

      const startData = await res.json();
      if (startData.status && startData.status.stage === 'Completed') {
        updateScanUI(startData.status);
        finishScan(startData.status);
      } else {
        setupSSE();
      }
    } catch (e) {
      console.error('Error starting scan:', e);
      btnStartScan.style.display = 'inline-flex';
      btnStopScan.style.display = 'none';
    }
  }

  btnStartScan?.addEventListener('click', startScan);

  btnStopScan?.addEventListener('click', async () => {
    try {
      btnStopScan.disabled = true;
      btnStopScan.textContent = 'Stopping...';
      await fetch('/api/scan/stop', { method: 'POST' });
    } catch (e) {
      console.error('Error stopping scan:', e);
    }
  });

  function setupSSE() {
    if (state.eventSource) {
      state.eventSource.close();
    }

    state.eventSource = new EventSource('/api/scan/stream');

    state.eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      updateScanUI(data);
    });

    state.eventSource.addEventListener('scan_completed', (e) => {
      const data = JSON.parse(e.data);
      updateScanUI(data);
      finishScan(data);
    });

    state.eventSource.addEventListener('scan_stopped', (e) => {
      const data = JSON.parse(e.data);
      updateScanUI(data);
      finishScan(data);
    });

    state.eventSource.addEventListener('scan_failed', (e) => {
      const data = JSON.parse(e.data);
      updateScanUI(data);
      finishScan(data);
      alert(`Scan stopped due to an error: ${data.error_message || 'Unknown error'}`);
    });

    state.eventSource.onerror = () => {
      // Fallback: poll progress once if SSE drops
      checkProgressPolling();
    };
  }

  async function checkProgressPolling() {
    try {
      const res = await fetch('/api/scan/progress');
      if (res.ok) {
        const data = await res.json();
        updateScanUI(data);
        if (!data.is_running) {
          finishScan(data);
        }
      }
    } catch (e) {}
  }

  function updateScanUI(progress) {
    state.scanProgress = progress;

    // Update Dashboard Metrics
    if (dashKpiBusinesses) dashKpiBusinesses.textContent = progress.businesses_discovered;
    if (dashKpiChecked) dashKpiChecked.textContent = progress.numbers_checked;
    if (dashKpiComcast) dashKpiComcast.textContent = progress.comcast_matches;
    if (dashKpiPossible) dashKpiPossible.textContent = progress.possible_matches;

    if (dashEngineState) {
      dashEngineState.textContent = progress.is_running ? 'Running' : progress.stage;
      dashEngineState.className = `badge ${progress.is_running ? 'badge-comcast' : 'badge-neutral'}`;
    }
    if (dashStageText) dashStageText.textContent = progress.stage;

    // Calculate percentage
    const maxLookups = parseInt(inputMaxLookups.value, 10) || 25;
    const pct = maxLookups > 0 ? Math.min(100, Math.round((progress.numbers_checked / maxLookups) * 100)) : 0;
    if (dashProgressFill) dashProgressFill.style.width = `${pct}%`;
    if (dashProgressCounts) dashProgressCounts.textContent = `${progress.numbers_checked} / ${maxLookups} numbers checked`;
    if (dashCostTag) dashCostTag.textContent = `Est. Cost: $${progress.estimated_cost_dollars.toFixed(3)}`;

    // Update New Scan Live Activity Cards
    if (liveStageBadge) liveStageBadge.textContent = progress.stage;
    if (liveMetricFound) liveMetricFound.textContent = progress.businesses_discovered;
    if (liveMetricChecked) liveMetricChecked.textContent = progress.numbers_checked;
    if (liveMetricComcast) liveMetricComcast.textContent = progress.comcast_matches;
    if (liveMetricPossible) liveMetricPossible.textContent = progress.possible_matches;

    if (liveProgressFill) liveProgressFill.style.width = `${pct}%`;
    if (liveStageDesc) liveStageDesc.textContent = `${progress.stage} (${progress.numbers_checked} checked)`;
    if (liveEstCostReadout) liveEstCostReadout.textContent = `Est. Cost: $${progress.estimated_cost_dollars.toFixed(3)}`;

    if (liveSourceAttribution && progress.attribution_text) {
      liveSourceAttribution.textContent = `Source: ${progress.attribution_text}`;
    }

    if (btnDashViewResults) {
      btnDashViewResults.style.display = progress.businesses_discovered > 0 ? 'inline-flex' : 'none';
    }
  }

  async function finishScan(progress) {
    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }

    btnStartScan.style.display = 'inline-flex';
    btnStopScan.style.display = 'none';
    btnStopScan.disabled = false;
    btnStopScan.textContent = 'Stop Scan';

    // Fetch and load results table
    await fetchResults();
  }

  // ==========================================================================
  // Results Table, Search, Filtering, Sorting, Pagination
  // ==========================================================================
  async function fetchResults() {
    try {
      const res = await fetch('/api/scan/results');
      if (!res.ok) return;
      const data = await res.json();
      state.records = data.records || [];
      if (navResultsCount) navResultsCount.textContent = state.records.length;

      if (resultsAttributionText && data.progress && data.progress.attribution_text) {
        resultsAttributionText.textContent = data.progress.attribution_text;
      }

      applyFiltersAndSort();
    } catch (e) {
      console.error('Error fetching results:', e);
    }
  }

  function applyFiltersAndSort() {
    let filtered = [...state.records];

    // Filter by match status
    if (state.activeFilterStatus && state.activeFilterStatus !== 'all') {
      filtered = filtered.filter((r) => r.match_status === state.activeFilterStatus);
    }

    // Filter by category
    if (state.activeFilterCategory && state.activeFilterCategory !== 'all') {
      filtered = filtered.filter(
        (r) => r.category === state.activeFilterCategory || r.category_id === state.activeFilterCategory
      );
    }

    // Search query
    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          (r.name && r.name.toLowerCase().includes(q)) ||
          (r.address && r.address.toLowerCase().includes(q)) ||
          (r.carrier && r.carrier.toLowerCase().includes(q)) ||
          (r.phone && r.phone.toLowerCase().includes(q)) ||
          (r.formatted_phone && r.formatted_phone.toLowerCase().includes(q))
      );
    }

    // Sorting
    filtered.sort((a, b) => {
      let valA = a[state.sortCol] || '';
      let valB = b[state.sortCol] || '';
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return state.sortAsc ? -1 : 1;
      if (valA > valB) return state.sortAsc ? 1 : -1;
      return 0;
    });

    state.filteredRecords = filtered;
    state.currentPage = 1;
    renderTable();
  }

  function renderTable() {
    if (!resultsTbody) return;

    const total = state.filteredRecords.length;
    if (resultsCountText) {
      resultsCountText.textContent = `Showing ${total} of ${state.records.length} records`;
    }

    if (total === 0) {
      resultsTbody.innerHTML = '';
      if (resultsEmptyState) resultsEmptyState.style.display = 'flex';
      if (paginationInfo) paginationInfo.textContent = 'Page 0 of 0';
      if (btnPrevPage) btnPrevPage.disabled = true;
      if (btnNextPage) btnNextPage.disabled = true;
      return;
    }

    if (resultsEmptyState) resultsEmptyState.style.display = 'none';

    // Pagination slice
    const totalPages = Math.ceil(total / state.pageSize);
    if (state.currentPage > totalPages) state.currentPage = totalPages;
    const startIdx = (state.currentPage - 1) * state.pageSize;
    const pageRecords = state.filteredRecords.slice(startIdx, startIdx + state.pageSize);

    if (paginationInfo) {
      paginationInfo.textContent = `Page ${state.currentPage} of ${totalPages} (${total} items)`;
    }
    if (btnPrevPage) btnPrevPage.disabled = state.currentPage <= 1;
    if (btnNextPage) btnNextPage.disabled = state.currentPage >= totalPages;

    let html = '';
    pageRecords.forEach((r, idx) => {
      const badgeClass = getBadgeClass(r.match_status);
      const websiteLink = r.website
        ? `<a href="${escapeHtml(r.website)}" target="_blank" rel="noopener noreferrer" class="table-link">Visit ↗</a>`
        : `<span class="text-muted">—</span>`;

      html += `
        <tr>
          <td>
            <span class="table-biz-name" data-id="${r.id}">${escapeHtml(r.name)}</span>
          </td>
          <td><span class="table-address">${escapeHtml(r.address || '—')}</span></td>
          <td><span class="table-phone">${escapeHtml(r.formatted_phone || r.phone || '—')}</span></td>
          <td><span class="table-carrier">${escapeHtml(r.carrier || 'Unknown')}</span></td>
          <td><span class="table-line-type">${escapeHtml(r.line_type || 'unknown')}</span></td>
          <td>${websiteLink}</td>
          <td>${escapeHtml(r.category || 'General')}</td>
          <td><span class="badge ${badgeClass}">${escapeHtml(r.match_status || 'Unknown')}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm btn-inspect-row" data-id="${r.id}" title="Inspect Details">
              Details
            </button>
          </td>
        </tr>
      `;
    });

    resultsTbody.innerHTML = html;

    // Attach row inspection handlers
    document.querySelectorAll('.table-biz-name, .btn-inspect-row').forEach((el) => {
      el.addEventListener('click', () => {
        const recordId = el.getAttribute('data-id');
        const found = state.records.find((item) => item.id === recordId);
        if (found) openRecordDrawer(found);
      });
    });
  }

  function getBadgeClass(status) {
    if (status === 'Comcast Match') return 'badge-comcast';
    if (status === 'Possible Match') return 'badge-possible';
    if (status === 'Not Match') return 'badge-not-match';
    return 'badge-unknown';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Filter Listeners
  filterMatchStatus?.addEventListener('change', (e) => {
    state.activeFilterStatus = e.target.value;
    applyFiltersAndSort();
  });

  filterCategory?.addEventListener('change', (e) => {
    state.activeFilterCategory = e.target.value;
    applyFiltersAndSort();
  });

  resultsSearchInput?.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.trim();
    applyFiltersAndSort();
  });

  // Table Sorting
  document.querySelectorAll('.th-sortable').forEach((th) => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-col');
      if (state.sortCol === col) {
        state.sortAsc = !state.sortAsc;
      } else {
        state.sortCol = col;
        state.sortAsc = true;
      }

      document.querySelectorAll('.sort-icon').forEach((si) => (si.textContent = '↕'));
      const activeIcon = th.querySelector('.sort-icon');
      if (activeIcon) activeIcon.textContent = state.sortAsc ? '↑' : '↓';

      applyFiltersAndSort();
    });
  });

  // Pagination Listeners
  btnPrevPage?.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      renderTable();
    }
  });

  btnNextPage?.addEventListener('click', () => {
    const totalPages = Math.ceil(state.filteredRecords.length / state.pageSize);
    if (state.currentPage < totalPages) {
      state.currentPage++;
      renderTable();
    }
  });

  function refreshResultsTable() {
    if (state.records.length === 0) {
      fetchResults();
    } else {
      applyFiltersAndSort();
    }
  }

  // ==========================================================================
  // Business Detail Inspection Drawer
  // ==========================================================================
  function openRecordDrawer(record) {
    state.selectedRecord = record;
    if (drawerBizName) drawerBizName.textContent = record.name;

    const badgeClass = getBadgeClass(record.match_status);

    let html = `
      <div class="detail-row">
        <div class="detail-label">Match Status</div>
        <div class="detail-value">
          <span class="badge ${badgeClass}">${escapeHtml(record.match_status)}</span>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Identified Carrier (Twilio Lookup v2)</div>
        <div class="detail-value"><strong>${escapeHtml(record.carrier || 'Unknown')}</strong></div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Line Type</div>
        <div class="detail-value mono">${escapeHtml(record.line_type || 'unknown')}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Match Classification Notes</div>
        <div class="detail-value">${escapeHtml(record.match_notes || 'Standard evaluation')}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Phone Number</div>
        <div class="detail-value mono">
          ${escapeHtml(record.formatted_phone || record.phone || '—')}
          ${record.e164 ? ` <span class="text-muted">(${escapeHtml(record.e164)})</span>` : ''}
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Physical Street Address</div>
        <div class="detail-value">${escapeHtml(record.address || '—')}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Business Category</div>
        <div class="detail-value">${escapeHtml(record.category || 'General')}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Official Website</div>
        <div class="detail-value">
          ${
            record.website
              ? `<a href="${escapeHtml(record.website)}" target="_blank" rel="noopener noreferrer" class="link-subtle">${escapeHtml(record.website)} ↗</a>`
              : '—'
          }
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Internal Place / Record Identifier</div>
        <div class="detail-value mono">${escapeHtml(record.place_id || record.id)}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Data Source & Export Licensing Rights</div>
        <div class="detail-value">
          ${escapeHtml(record.provider_source || 'default')}
          (${record.allows_export ? 'Export Allowed' : 'Export Restricted by ToS'})
        </div>
      </div>
    `;

    if (drawerBizContent) drawerBizContent.innerHTML = html;
    if (drawerOverlay) drawerOverlay.classList.add('active');
  }

  function closeRecordDrawer() {
    if (drawerOverlay) drawerOverlay.classList.remove('active');
    state.selectedRecord = null;
  }

  drawerCloseBtn?.addEventListener('click', closeRecordDrawer);
  drawerOverlay?.addEventListener('click', (e) => {
    if (e.target === drawerOverlay) closeRecordDrawer();
  });

  // ==========================================================================
  // CSV Export Modal & Compliance Guard (PRD Section 11 & AC-21)
  // ==========================================================================
  btnOpenExportModal?.addEventListener('click', () => {
    if (state.records.length === 0) {
      alert('No business records to export. Please run a scan first.');
      return;
    }

    // Check if the current records contain restricted Google Places items
    const hasRestricted = state.records.some((r) => !r.allows_export);

    if (exportComplianceWarning) {
      if (hasRestricted) {
        exportComplianceWarning.style.display = 'block';
      } else {
        exportComplianceWarning.style.display = 'none';
      }
    }

    if (exportModalBackdrop) exportModalBackdrop.classList.add('active');
  });

  function closeExportModal() {
    if (exportModalBackdrop) exportModalBackdrop.classList.remove('active');
  }

  modalCloseBtn?.addEventListener('click', closeExportModal);
  btnCancelExport?.addEventListener('click', closeExportModal);
  exportModalBackdrop?.addEventListener('click', (e) => {
    if (e.target === exportModalBackdrop) closeExportModal();
  });

  btnConfirmExport?.addEventListener('click', async () => {
    const filterMode = document.querySelector('input[name="export_filter"]:checked')?.value || 'confirmed_only';

    try {
      btnConfirmExport.disabled = true;
      btnConfirmExport.textContent = 'Generating CSV...';

      const res = await fetch('/api/export/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter_mode: filterMode }),
      });

      btnConfirmExport.disabled = false;
      btnConfirmExport.textContent = 'Download CSV';

      if (res.status === 403) {
        const errorData = await res.json();
        alert(
          `${errorData.title || 'Export Blocked'}\n\n${errorData.detail}\n\nRecommendation: ${errorData.recommendation}`
        );
        return;
      }

      if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || 'Failed to export CSV.');
        return;
      }

      // Download file blob
      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition') || '';
      let filename = 'fresno_comcast_businesses.csv';
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      closeExportModal();
    } catch (e) {
      btnConfirmExport.disabled = false;
      btnConfirmExport.textContent = 'Download CSV';
      alert('Network error during CSV export.');
    }
  });

  // ==========================================================================
  // Initialization
  // ==========================================================================
  loadSettings();
  updateCostEstimate();
  fetchResults();
});
