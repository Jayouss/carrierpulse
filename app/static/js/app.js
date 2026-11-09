/**
 * Fresno Carrier Finder — Ronas IT Logistics Intelligence Dashboard Architecture
 * Interactive company selection, Hero inspection terminal, carrier analytics & CSV export
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    currentScreen: 'dashboard',
    settings: null,
    scanProgress: null,
    records: [],
    filteredRecords: [],
    selectedRecord: null,
    activeFilterStatus: 'Comcast Match',
    activeFilterCategory: 'all',
    searchQuery: '',
    sortCol: 'name',
    sortAsc: true,
    eventSource: null,
    customCsvContent: null,
  };

  // Views Cache
  const views = {
    dashboard: document.getElementById('view-dashboard'),
    newScan: document.getElementById('view-new-scan'),
    results: document.getElementById('view-results'),
    settings: document.getElementById('view-settings'),
  };

  const navPills = document.querySelectorAll('.nav-segmented-track .nav-pill');
  const navResultsCount = document.getElementById('nav-results-count');
  const topStatusText = document.getElementById('top-status-text');
  const btnTopQuickScan = document.getElementById('btn-top-quick-scan');

  // Hero Showcase Elements
  const heroCompanyId = document.getElementById('hero-company-id');
  const heroMatchBadge = document.getElementById('hero-match-badge');
  const heroCompanyName = document.getElementById('hero-company-name');
  const heroCompanyCategory = document.getElementById('hero-company-category');
  const heroCompanyAddress = document.getElementById('hero-company-address');
  const heroPhoneNational = document.getElementById('hero-phone-national');
  const heroPhoneE164 = document.getElementById('hero-phone-e164');
  const heroMiniBars = document.getElementById('hero-mini-bars');
  const heroComcastPct = document.getElementById('hero-comcast-pct');
  const heroLinkWebsite = document.getElementById('hero-link-website');
  const heroBtnCopyPhone = document.getElementById('hero-btn-copy-phone');
  const heroCenterCarrier = document.getElementById('hero-center-carrier');
  const heroLineType = document.getElementById('hero-line-type');
  const heroLineStatus = document.getElementById('hero-line-status');
  const gaugeArcPath = document.getElementById('gauge-arc-path');
  const heroConfidencePct = document.getElementById('hero-confidence-pct');
  const heroConfidenceTag = document.getElementById('hero-confidence-tag');
  const heroCostVal = document.getElementById('hero-cost-val');

  // Horizontal Company Rail
  const companyRailTrack = document.getElementById('company-rail-track');

  // Distribution Overview Elements
  const meterBarComcast = document.querySelector('.seg-comcast');
  const meterBarAtt = document.querySelector('.seg-att');
  const meterBarSpectrum = document.querySelector('.seg-spectrum');
  const meterBarOther = document.querySelector('.seg-other');
  const shareComcastCount = document.getElementById('share-comcast-count');
  const shareAttCount = document.getElementById('share-att-count');
  const shareSpectrumCount = document.getElementById('share-spectrum-count');
  const shareOtherCount = document.getElementById('share-other-count');

  // Table Elements
  const recordsTotalTag = document.getElementById('records-total-tag');
  const dashRecordsTbody = document.getElementById('dash-records-tbody');
  const fullResultsTbody = document.getElementById('full-results-tbody');
  const dashEmptyNotice = document.getElementById('dash-empty-notice');
  const dashSearchInput = document.getElementById('dash-search-input');
  const dashCategorySelect = document.getElementById('dash-category-select');
  const statusFilterTabs = document.querySelectorAll('#status-filter-tabs .status-tab');
  const tabCntComcast = document.getElementById('tab-cnt-comcast');
  const tabCntPossible = document.getElementById('tab-cnt-possible');
  const tabCntAll = document.getElementById('tab-cnt-all');
  const tabCntOther = document.getElementById('tab-cnt-other');

  // Export Modal Elements
  const exportModalBackdrop = document.getElementById('export-modal-backdrop');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const btnCancelExport = document.getElementById('btn-cancel-export');
  const btnConfirmExport = document.getElementById('btn-confirm-export');
  const btnExportCsvAction = document.getElementById('btn-export-csv-action');
  const btnOpenExportModalFull = document.getElementById('btn-open-export-modal-full');
  const exportComplianceWarning = document.getElementById('export-compliance-warning');

  // Scan Controls
  const inputMaxBiz = document.getElementById('input-max-biz');
  const inputMaxLookups = document.getElementById('input-max-lookups');
  const scanEstCostDisplay = document.getElementById('scan-est-cost-display');
  const costTwilioPart = document.getElementById('cost-twilio-part');
  const costGooglePart = document.getElementById('cost-google-part');
  const btnStartScan = document.getElementById('btn-start-scan');
  const btnStopScan = document.getElementById('btn-stop-scan');

  // Settings
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

    navPills.forEach((pill) => {
      if (pill.getAttribute('data-screen') === screenName) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    if (screenName === 'dashboard' && views.dashboard) views.dashboard.classList.add('active');
    if (screenName === 'new-scan' && views.newScan) views.newScan.classList.add('active');
    if (screenName === 'results' && views.results) {
      views.results.classList.add('active');
      renderFullResultsTable();
    }
    if (screenName === 'settings' && views.settings) views.settings.classList.add('active');
  }

  navPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const scr = pill.getAttribute('data-screen');
      if (scr) switchScreen(scr);
    });
  });

  btnTopQuickScan?.addEventListener('click', () => {
    switchScreen('dashboard');
    startScan('demo');
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
  // Hero Inspection Showcase & Selection Logic
  // ==========================================================================
  function selectCompany(record) {
    if (!record) return;
    state.selectedRecord = record;
    renderHeroShowcase(record);
    highlightActiveElements(record.id);
  }

  function renderHeroShowcase(rec) {
    if (!rec) return;

    const idx = state.records.findIndex((r) => r.id === rec.id);
    const codeId = `#FRESNO-${idx >= 0 ? idx + 1 : 1}`;

    if (heroCompanyId) heroCompanyId.textContent = codeId;
    if (heroCompanyName) heroCompanyName.textContent = rec.name || 'Unnamed Business';
    if (heroCompanyCategory) heroCompanyCategory.textContent = rec.category || 'Business';
    if (heroCompanyAddress) heroCompanyAddress.textContent = rec.address || 'Fresno, CA';

    // Phone & Verification Pipeline
    const nationalPhone = rec.formatted_phone || rec.phone || 'No phone listed';
    const e164Phone = rec.e164 || rec.phone || 'E.164 Pending';
    if (heroPhoneNational) heroPhoneNational.textContent = nationalPhone;
    if (heroPhoneE164) heroPhoneE164.textContent = e164Phone;

    // Website Link
    if (heroLinkWebsite) {
      if (rec.website) {
        heroLinkWebsite.href = rec.website;
        heroLinkWebsite.style.display = 'inline-flex';
      } else {
        heroLinkWebsite.style.display = 'none';
      }
    }

    // Match Status Badge
    if (heroMatchBadge) {
      heroMatchBadge.textContent = rec.match_status || 'Unknown';
      heroMatchBadge.className = 'badge';
      if (rec.match_status === 'Comcast Match') {
        heroMatchBadge.classList.add('badge-comcast');
      } else if (rec.match_status === 'Possible Match') {
        heroMatchBadge.classList.add('badge-possible');
      } else {
        heroMatchBadge.classList.add('badge-not-match');
      }
    }

    // Center Operating Carrier Callout
    if (heroCenterCarrier) {
      heroCenterCarrier.textContent = rec.carrier || 'Carrier Network Not Identified';
    }

    // Right Telemetry Card 1: Line Type & Classification
    if (heroLineType) heroLineType.textContent = rec.line_type || 'unknown';
    if (heroLineStatus) {
      if (rec.line_type === 'fixedVoip') {
        heroLineStatus.textContent = 'Business PBX / Cloud SIP';
      } else if (rec.line_type === 'landline') {
        heroLineStatus.textContent = 'Local PSTN Copper Loop';
      } else if (rec.line_type === 'mobile') {
        heroLineStatus.textContent = 'Cellular Mobile Interface';
      } else if (rec.line_type === 'tollFree') {
        heroLineStatus.textContent = 'Inbound Toll-Free Routing';
      } else {
        heroLineStatus.textContent = 'Enterprise Local Circuit';
      }
    }

    // Right Telemetry Card 2: Confidence Arc Gauge (RPM Meter Equivalent)
    renderConfidenceGauge(rec.match_status);

    // Right Telemetry Card 3: Session Cost
    if (heroCostVal) {
      const cost = state.scanProgress ? state.scanProgress.estimated_cost_dollars : 0.025;
      heroCostVal.textContent = `$${cost.toFixed(3)}`;
    }

    // Mini Bars Rate
    renderMiniBars();
  }

  function renderConfidenceGauge(matchStatus) {
    if (!gaugeArcPath || !heroConfidencePct || !heroConfidenceTag) return;

    // Total arc perimeter ~ 141.37
    const arcTotal = 141.37;
    let pct = 98;
    let label = 'Direct Alias';
    let strokeColor = '#236B59';

    if (matchStatus === 'Comcast Match') {
      pct = 98;
      label = 'Direct Alias';
      strokeColor = '#236B59';
    } else if (matchStatus === 'Possible Match') {
      pct = 65;
      label = 'Carrier Affiliate';
      strokeColor = '#B87A28';
    } else if (matchStatus === 'Not Match') {
      pct = 15;
      label = 'Alternate Network';
      strokeColor = '#6C7A87';
    } else {
      pct = 5;
      label = 'Unverified Signal';
      strokeColor = '#8E9BA6';
    }

    // dashoffset = arcTotal * (1 - pct / 100)
    const offset = Math.max(4, arcTotal * (1 - pct / 100));
    gaugeArcPath.setAttribute('stroke', strokeColor);
    gaugeArcPath.setAttribute('stroke-dashoffset', offset.toFixed(1));
    heroConfidencePct.textContent = `${pct}%`;
    heroConfidenceTag.textContent = label;
  }

  function renderMiniBars() {
    if (!heroMiniBars || !heroComcastPct) return;

    const total = state.records.length;
    const comcastCount = state.records.filter((r) => r.match_status === 'Comcast Match').length;
    const pct = total > 0 ? Math.round((comcastCount / total) * 100) : 0;
    heroComcastPct.textContent = `${pct}%`;

    const activeBars = Math.round((pct / 100) * 10);
    let barsHtml = '';
    for (let i = 0; i < 10; i++) {
      const h = 8 + (i % 5) * 3;
      const isActive = i < activeBars;
      barsHtml += `<div class="gauge-bar-slice ${isActive ? 'active' : ''}" style="height: ${h}px"></div>`;
    }
    heroMiniBars.innerHTML = barsHtml;
  }

  // Copy Phone Number
  heroBtnCopyPhone?.addEventListener('click', () => {
    if (!state.selectedRecord) return;
    const num = state.selectedRecord.formatted_phone || state.selectedRecord.phone;
    if (!num) return;

    navigator.clipboard.writeText(num).then(() => {
      const originalSpan = heroBtnCopyPhone.querySelector('span');
      if (originalSpan) {
        const orig = originalSpan.textContent;
        originalSpan.textContent = 'Copied!';
        setTimeout(() => {
          originalSpan.textContent = orig;
        }, 1500);
      }
    });
  });

  // ==========================================================================
  // Horizontal Company Selection Rail
  // ==========================================================================
  function renderCompanyRail() {
    if (!companyRailTrack) return;

    if (state.records.length === 0) {
      companyRailTrack.innerHTML = `
        <div style="padding: 12px 16px; font-size: 12px; color: var(--text-muted);">
          No businesses loaded yet. Click "Run Demo Scan" above to discover Fresno businesses.
        </div>
      `;
      return;
    }

    let html = '';
    state.records.forEach((rec, idx) => {
      const isActive = state.selectedRecord && state.selectedRecord.id === rec.id;
      const codeId = `#FRES-${idx + 1}`;
      let dotClass = 'dot-other';
      if (rec.match_status === 'Comcast Match') dotClass = 'dot-match';
      if (rec.match_status === 'Possible Match') dotClass = 'dot-possible';

      html += `
        <div class="rail-card ${isActive ? 'active' : ''}" data-id="${rec.id}">
          <div class="rail-card-head">
            <span class="rail-card-id mono">${codeId}</span>
            <span class="rail-status-dot ${dotClass}" title="${escapeHtml(rec.match_status)}"></span>
          </div>
          <div class="rail-card-name" title="${escapeHtml(rec.name)}">${escapeHtml(rec.name)}</div>
          <div class="rail-card-meta">
            <span>${escapeHtml(rec.category || 'Business')}</span>
            <span class="rail-card-phone mono">${escapeHtml(rec.formatted_phone || rec.phone || '—')}</span>
          </div>
        </div>
      `;
    });

    companyRailTrack.innerHTML = html;

    // Attach click listeners to rail cards
    companyRailTrack.querySelectorAll('.rail-card').forEach((card) => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-id');
        const found = state.records.find((r) => r.id === id);
        if (found) selectCompany(found);
      });
    });
  }

  function highlightActiveElements(activeId) {
    // Highlight in rail
    if (companyRailTrack) {
      companyRailTrack.querySelectorAll('.rail-card').forEach((c) => {
        if (c.getAttribute('data-id') === activeId) {
          c.classList.add('active');
        } else {
          c.classList.remove('active');
        }
      });
    }

    // Highlight in table
    if (dashRecordsTbody) {
      dashRecordsTbody.querySelectorAll('tr').forEach((tr) => {
        if (tr.getAttribute('data-id') === activeId) {
          tr.classList.add('tr-selected');
        } else {
          tr.classList.remove('tr-selected');
        }
      });
    }
  }

  // ==========================================================================
  // Distribution Overview (Fresno Carrier Share Breakdown)
  // ==========================================================================
  function renderDistribution() {
    const total = state.records.length;
    if (total === 0) {
      if (shareComcastCount) shareComcastCount.textContent = '0 (0%)';
      if (shareAttCount) shareAttCount.textContent = '0 (0%)';
      if (shareSpectrumCount) shareSpectrumCount.textContent = '0 (0%)';
      if (shareOtherCount) shareOtherCount.textContent = '0 (0%)';
      return;
    }

    let comcast = 0;
    let att = 0;
    let spectrum = 0;
    let other = 0;

    state.records.forEach((r) => {
      const c = (r.carrier || '').toLowerCase();
      if (r.match_status === 'Comcast Match' || c.includes('comcast') || c.includes('xfinity')) {
        comcast++;
      } else if (c.includes('at&t') || c.includes('pacific bell') || c.includes('sbc')) {
        att++;
      } else if (c.includes('charter') || c.includes('spectrum') || c.includes('time warner')) {
        spectrum++;
      } else {
        other++;
      }
    });

    const pctComcast = Math.round((comcast / total) * 100);
    const pctAtt = Math.round((att / total) * 100);
    const pctSpectrum = Math.round((spectrum / total) * 100);
    const pctOther = Math.max(0, 100 - pctComcast - pctAtt - pctSpectrum);

    if (meterBarComcast) meterBarComcast.style.width = `${pctComcast}%`;
    if (meterBarAtt) meterBarAtt.style.width = `${pctAtt}%`;
    if (meterBarSpectrum) meterBarSpectrum.style.width = `${pctSpectrum}%`;
    if (meterBarOther) meterBarOther.style.width = `${pctOther}%`;

    if (shareComcastCount) shareComcastCount.textContent = `${comcast} (${pctComcast}%)`;
    if (shareAttCount) shareAttCount.textContent = `${att} (${pctAtt}%)`;
    if (shareSpectrumCount) shareSpectrumCount.textContent = `${spectrum} (${pctSpectrum}% )`;
    if (shareOtherCount) shareOtherCount.textContent = `${other} (${pctOther}%)`;
  }

  // ==========================================================================
  // Results Table, Search, Status Tabs & Sorting
  // ==========================================================================
  async function fetchResults() {
    try {
      const res = await fetch('/api/scan/results');
      if (!res.ok) return;
      const data = await res.json();
      state.records = data.records || [];
      if (navResultsCount) navResultsCount.textContent = state.records.length;

      // Update Tab Counter Numbers
      updateTabCounts();

      // Default select first Comcast Match or first record
      if (!state.selectedRecord && state.records.length > 0) {
        const firstMatch = state.records.find((r) => r.match_status === 'Comcast Match') || state.records[0];
        selectCompany(firstMatch);
      }

      applyFiltersAndSort();
      renderCompanyRail();
      renderDistribution();
    } catch (e) {
      console.error('Error fetching results:', e);
    }
  }

  function updateTabCounts() {
    const comcastCount = state.records.filter((r) => r.match_status === 'Comcast Match').length;
    const possibleCount = state.records.filter((r) => r.match_status === 'Possible Match').length;
    const otherCount = state.records.filter((r) => r.match_status === 'Not Match' || r.match_status === 'Unknown').length;

    if (tabCntComcast) tabCntComcast.textContent = comcastCount;
    if (tabCntPossible) tabCntPossible.textContent = possibleCount;
    if (tabCntAll) tabCntAll.textContent = state.records.length;
    if (tabCntOther) tabCntOther.textContent = otherCount;
    if (recordsTotalTag) recordsTotalTag.textContent = `${state.records.length} businesses`;
  }

  function applyFiltersAndSort() {
    let filtered = [...state.records];

    // Filter by Status Tab
    if (state.activeFilterStatus && state.activeFilterStatus !== 'all') {
      if (state.activeFilterStatus === 'Not Match') {
        filtered = filtered.filter((r) => r.match_status === 'Not Match' || r.match_status === 'Unknown');
      } else {
        filtered = filtered.filter((r) => r.match_status === state.activeFilterStatus);
      }
    }

    // Filter by Category Dropdown
    if (state.activeFilterCategory && state.activeFilterCategory !== 'all') {
      filtered = filtered.filter(
        (r) => r.category === state.activeFilterCategory || r.category_id === state.activeFilterCategory
      );
    }

    // Text Search
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
    renderDashboardTable();
  }

  function renderDashboardTable() {
    if (!dashRecordsTbody) return;

    if (state.filteredRecords.length === 0) {
      dashRecordsTbody.innerHTML = '';
      if (dashEmptyNotice) dashEmptyNotice.style.display = 'flex';
      return;
    }

    if (dashEmptyNotice) dashEmptyNotice.style.display = 'none';

    let html = '';
    state.filteredRecords.forEach((r) => {
      const isSelected = state.selectedRecord && state.selectedRecord.id === r.id;
      const badgeClass = getBadgeClass(r.match_status);
      const websiteLink = r.website
        ? `<a href="${escapeHtml(r.website)}" target="_blank" rel="noopener noreferrer" class="tbl-link-web" onclick="event.stopPropagation()">Website ↗</a>`
        : `<span style="color: var(--text-muted)">—</span>`;

      html += `
        <tr data-id="${r.id}" class="${isSelected ? 'tr-selected' : ''}">
          <td><strong class="tbl-biz-name">${escapeHtml(r.name)}</strong></td>
          <td><span style="color: var(--text-secondary); font-size: 12px;">${escapeHtml(r.address || '—')}</span></td>
          <td><span class="mono" style="font-size: 12px;">${escapeHtml(r.formatted_phone || r.phone || '—')}</span></td>
          <td><strong>${escapeHtml(r.carrier || 'Unknown')}</strong></td>
          <td><span class="mono" style="font-size: 12px;">${escapeHtml(r.line_type || 'unknown')}</span></td>
          <td>${websiteLink}</td>
          <td><span class="badge ${badgeClass}">${escapeHtml(r.match_status || 'Unknown')}</span></td>
        </tr>
      `;
    });

    dashRecordsTbody.innerHTML = html;

    // Attach click handler to table rows for selecting into Hero Showcase
    dashRecordsTbody.querySelectorAll('tr').forEach((tr) => {
      tr.addEventListener('click', () => {
        const id = tr.getAttribute('data-id');
        const found = state.records.find((r) => r.id === id);
        if (found) {
          selectCompany(found);
          // Smooth scroll to top of dashboard if scrolled down
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }

  function renderFullResultsTable() {
    if (!fullResultsTbody) return;

    let html = '';
    state.records.forEach((r) => {
      const badgeClass = getBadgeClass(r.match_status);
      const websiteLink = r.website
        ? `<a href="${escapeHtml(r.website)}" target="_blank" rel="noopener noreferrer" class="tbl-link-web">Website ↗</a>`
        : `<span style="color: var(--text-muted)">—</span>`;

      html += `
        <tr>
          <td><strong>${escapeHtml(r.name)}</strong></td>
          <td><span style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(r.address || '—')}</span></td>
          <td><span class="mono">${escapeHtml(r.formatted_phone || r.phone || '—')}</span></td>
          <td>${escapeHtml(r.carrier || 'Unknown')}</td>
          <td><span class="mono">${escapeHtml(r.line_type || 'unknown')}</span></td>
          <td>${websiteLink}</td>
          <td>${escapeHtml(r.category || 'General')}</td>
          <td><span class="badge ${badgeClass}">${escapeHtml(r.match_status || 'Unknown')}</span></td>
        </tr>
      `;
    });

    fullResultsTbody.innerHTML = html;
  }

  function getBadgeClass(status) {
    if (status === 'Comcast Match') return 'badge-comcast';
    if (status === 'Possible Match') return 'badge-possible';
    if (status === 'Not Match') return 'badge-not-match';
    return 'badge-not-match';
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

  // Status Tab Clicks
  statusFilterTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      statusFilterTabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      state.activeFilterStatus = tab.getAttribute('data-status');
      applyFiltersAndSort();
    });
  });

  // Search & Category Dropdown
  dashSearchInput?.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.trim();
    applyFiltersAndSort();
  });

  dashCategorySelect?.addEventListener('change', (e) => {
    state.activeFilterCategory = e.target.value;
    applyFiltersAndSort();
  });

  // Table Column Sort
  document.querySelectorAll('.th-sortable').forEach((th) => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-col');
      if (state.sortCol === col) {
        state.sortAsc = !state.sortAsc;
      } else {
        state.sortCol = col;
        state.sortAsc = true;
      }
      applyFiltersAndSort();
    });
  });

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
    radio.addEventListener('change', updateCostEstimate);
  });

  // ==========================================================================
  // Scan Execution & SSE Streaming
  // ==========================================================================
  async function startScan(forcedProvider) {
    const selectedCats = Array.from(
      document.querySelectorAll('input[name="scan_category"]:checked')
    ).map((cb) => cb.value);

    const categories = selectedCats.length > 0 ? selectedCats : ['restaurant', 'dentist', 'auto_repair', 'plumber', 'law_firm'];
    const providerMode = forcedProvider || document.querySelector('input[name="provider_mode"]:checked')?.value || 'demo';
    const maxBiz = parseInt(inputMaxBiz?.value || 50, 10);
    const maxLookups = parseInt(inputMaxLookups?.value || 25, 10);

    const payload = {
      categories: categories,
      max_businesses: maxBiz,
      max_lookups: maxLookups,
      provider_mode: providerMode,
      max_spend_guard_dollars: 5.0,
      custom_csv_content: providerMode === 'licensed_dataset' ? state.customCsvContent : null,
    };

    if (topStatusText) topStatusText.textContent = 'Running Scan...';

    try {
      if (btnStartScan) btnStartScan.style.display = 'none';
      if (btnStopScan) btnStopScan.style.display = 'inline-flex';

      const res = await fetch('/api/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || 'Failed to start scan.');
        resetScanButtons();
        return;
      }

      const startData = await res.json();
      if (startData.status && startData.status.stage === 'Completed') {
        finishScan(startData.status);
      } else {
        setupSSE();
      }
    } catch (e) {
      console.error('Scan start error:', e);
      resetScanButtons();
    }
  }

  btnStartScan?.addEventListener('click', () => startScan());

  btnStopScan?.addEventListener('click', async () => {
    try {
      btnStopScan.disabled = true;
      btnStopScan.textContent = 'Stopping...';
      await fetch('/api/scan/stop', { method: 'POST' });
    } catch (e) {
      console.error('Scan stop error:', e);
    }
  });

  function setupSSE() {
    if (state.eventSource) state.eventSource.close();
    state.eventSource = new EventSource('/api/scan/stream');

    state.eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      updateProgressState(data);
    });

    state.eventSource.addEventListener('scan_completed', (e) => {
      const data = JSON.parse(e.data);
      finishScan(data);
    });

    state.eventSource.addEventListener('scan_stopped', (e) => {
      const data = JSON.parse(e.data);
      finishScan(data);
    });

    state.eventSource.addEventListener('scan_failed', (e) => {
      const data = JSON.parse(e.data);
      finishScan(data);
      alert(`Scan encountered an issue: ${data.error_message || 'Unknown error'}`);
    });

    state.eventSource.onerror = () => {
      checkProgressPolling();
    };
  }

  async function checkProgressPolling() {
    try {
      const res = await fetch('/api/scan/progress');
      if (res.ok) {
        const data = await res.json();
        updateProgressState(data);
        if (!data.is_running) finishScan(data);
      }
    } catch (e) {}
  }

  function updateProgressState(progress) {
    state.scanProgress = progress;
    if (topStatusText) {
      topStatusText.textContent = progress.is_running
        ? `${progress.stage} (${progress.numbers_checked} checked)`
        : `Ready · ${progress.provider_mode || 'Demo Mode'}`;
    }
  }

  async function finishScan(progress) {
    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }
    resetScanButtons();
    if (topStatusText) topStatusText.textContent = 'Ready · Scan Complete';
    await fetchResults();
  }

  function resetScanButtons() {
    if (btnStartScan) btnStartScan.style.display = 'inline-flex';
    if (btnStopScan) {
      btnStopScan.style.display = 'none';
      btnStopScan.disabled = false;
      btnStopScan.textContent = 'Stop Scan';
    }
  }

  // ==========================================================================
  // CSV Export Modal & Compliance
  // ==========================================================================
  function openExportModal() {
    if (state.records.length === 0) {
      alert('Please run a scan first to obtain records.');
      return;
    }
    const hasRestricted = state.records.some((r) => !r.allows_export);
    if (exportComplianceWarning) {
      exportComplianceWarning.style.display = hasRestricted ? 'block' : 'none';
    }
    if (exportModalBackdrop) exportModalBackdrop.classList.add('active');
  }

  btnExportCsvAction?.addEventListener('click', openExportModal);
  btnOpenExportModalFull?.addEventListener('click', openExportModal);

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
        alert(`${errorData.title || 'Export Restricted'}\n\n${errorData.detail}\n\n${errorData.recommendation}`);
        return;
      }

      if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || 'CSV export failed.');
        return;
      }

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
      alert('Network error during CSV download.');
    }
  });

  // ==========================================================================
  // Settings API
  // ==========================================================================
  async function loadSettings() {
    try {
      const res = await fetch('/api/settings');
      if (!res.ok) return;
      const data = await res.json();
      state.settings = data;
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
          settingTwilioSecret.placeholder = 'Configured (Secret stored)';
        }
      }
    } catch (e) {}
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
        showStatusBanner('success', data.message || 'Credentials stored securely.');
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
      showStatusBanner('error', 'Network error.');
    }
  });

  btnTestGoogle?.addEventListener('click', async () => {
    try {
      btnTestGoogle.disabled = true;
      btnTestGoogle.textContent = 'Testing...';
      const res = await fetch('/api/settings/test-google', { method: 'POST' });
      const data = await res.json();
      btnTestGoogle.disabled = false;
      btnTestGoogle.textContent = 'Test Google';
      showStatusBanner(data.success ? 'success' : 'error', data.message);
    } catch (e) {
      btnTestGoogle.disabled = false;
      btnTestGoogle.textContent = 'Test Google';
      showStatusBanner('error', 'Test connection failed.');
    }
  });

  btnTestTwilio?.addEventListener('click', async () => {
    try {
      btnTestTwilio.disabled = true;
      btnTestTwilio.textContent = 'Testing...';
      const res = await fetch('/api/settings/test-twilio', { method: 'POST' });
      const data = await res.json();
      btnTestTwilio.disabled = false;
      btnTestTwilio.textContent = 'Test Twilio';
      showStatusBanner(data.success ? 'success' : 'error', data.message);
    } catch (e) {
      btnTestTwilio.disabled = false;
      btnTestTwilio.textContent = 'Test Twilio';
      showStatusBanner('error', 'Test connection failed.');
    }
  });

  function showStatusBanner(type, message) {
    if (!settingsStatusBanner) return;
    settingsStatusBanner.className = `status-banner ${type}`;
    settingsStatusBanner.textContent = message;
    settingsStatusBanner.style.display = 'block';
  }

  // Initial Load
  loadSettings();
  updateCostEstimate();
  fetchResults();
});
