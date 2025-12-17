/**
 * LLM Monitor - Dashboard Main Script
 * Handles real-time updates, API calls, and page interactions
 */

// ============================================================
// Global State
// ============================================================

const state = {
    currentPage: 1,
    pageSize: 25,
    refreshInterval: null,
    refreshRate: 30000, // 30 seconds
    isLoading: false,
    filters: {
        status: '',
        model: '',
        user: '',
        feature: '',
        start_date: '',
        end_date: ''
    }
};


// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Detect current page and initialize accordingly
    const path = window.location.pathname;
    
    if (path === '/' || path.includes('/dashboard')) {
        initDashboard();
    }
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize sidebar toggle
    initSidebarToggle();
});


/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
}


/**
 * Initialize sidebar toggle for mobile
 */
function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('show') && 
                !sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}


// ============================================================
// Dashboard Initialization
// ============================================================

function initDashboard() {
    // Load initial data
    loadDashboardOverview();
    loadDashboardCharts();
    loadRecentTraces();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Add event listeners
    setupDashboardEventListeners();
}


function setupDashboardEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshDashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
    
    // Filter form
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            applyFilters();
        });
    }
    
    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }
    
    // Export button
    const exportBtn = document.getElementById('exportTraces');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportTraces);
    }
}


// ============================================================
// Data Loading Functions
// ============================================================

/**
 * Load dashboard overview statistics
 */
async function loadDashboardOverview() {
    try {
        const data = await apiRequest('/api/analytics/overview/');
        updateDashboardStats(data);
    } catch (error) {
        console.error('Error loading overview:', error);
        showToast('Failed to load dashboard stats', 'danger');
    }
}


/**
 * Update dashboard stat cards
 */
function updateDashboardStats(data) {
    // Total requests
    const totalRequestsEl = document.getElementById('totalRequests');
    if (totalRequestsEl) {
        animateValue(totalRequestsEl, parseInt(totalRequestsEl.textContent.replace(/,/g, '')) || 0, data.total_requests_all);
    }
    
    // Requests 24h
    const requests24hEl = document.getElementById('requests24h');
    if (requests24hEl) {
        animateValue(requests24hEl, parseInt(requests24hEl.textContent.replace(/,/g, '')) || 0, data.total_requests_24h);
    }
    
    // Average latency
    const avgLatencyEl = document.getElementById('avgLatency');
    if (avgLatencyEl) {
        avgLatencyEl.textContent = `${data.average_latency_ms.toFixed(0)}ms`;
    }
    
    // Total tokens
    const totalTokensEl = document.getElementById('totalTokens');
    if (totalTokensEl) {
        totalTokensEl.textContent = formatNumber(data.total_tokens);
    }
    
    // Total cost
    const totalCostEl = document.getElementById('totalCost');
    if (totalCostEl) {
        totalCostEl.textContent = `$${data.total_cost_usd.toFixed(4)}`;
    }
    
    // Error rate
    const errorRateEl = document.getElementById('errorRate');
    if (errorRateEl) {
        errorRateEl.textContent = `${data.error_rate_percent.toFixed(1)}%`;
        
        // Update color based on error rate
        if (data.error_rate_percent > 5) {
            errorRateEl.classList.add('text-danger');
        } else if (data.error_rate_percent > 2) {
            errorRateEl.classList.add('text-warning');
        } else {
            errorRateEl.classList.add('text-success');
        }
    }
}


/**
 * Animate value change
 */
function animateValue(element, start, end, duration = 500) {
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + range * eased);
        
        element.textContent = formatNumber(current);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}


/**
 * Load dashboard chart data
 */
async function loadDashboardCharts() {
    try {
        const data = await apiRequest('/api/analytics/charts/?days=7');
        
        // Update each chart
        if (data.token_usage) {
            updateTokenUsageChart(data.token_usage);
        }
        
        if (data.model_distribution) {
            updateModelDistributionChart(data.model_distribution);
        }
        
        if (data.latency_trend) {
            updateLatencyTrendChart(data.latency_trend);
        }
        
        if (data.status_distribution) {
            updateStatusDistributionChart(data.status_distribution);
        }
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}


/**
 * Load recent traces table
 */
async function loadRecentTraces() {
    const tbody = document.getElementById('tracesTableBody');
    if (!tbody) return;
    
    // Show loading state
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-4">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading traces...</span>
            </td>
        </tr>
    `;
    
    try {
        let url = `/api/traces/?page=${state.currentPage}&page_size=${state.pageSize}`;
        
        // Apply filters
        if (state.filters.status) url += `&status=${state.filters.status}`;
        if (state.filters.model) url += `&model=${state.filters.model}`;
        if (state.filters.user) url += `&user=${state.filters.user}`;
        if (state.filters.start_date) url += `&start_date=${state.filters.start_date}`;
        if (state.filters.end_date) url += `&end_date=${state.filters.end_date}`;
        
        const data = await apiRequest(url);
        renderTracesTable(data);
        updatePagination(data);
    } catch (error) {
        console.error('Error loading traces:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to load traces
                </td>
            </tr>
        `;
    }
}


/**
 * Render traces table
 */
function renderTracesTable(data) {
    const tbody = document.getElementById('tracesTableBody');
    if (!tbody) return;
    
    if (!data.results || data.results.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-4 d-block mb-2"></i>
                    No traces found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = data.results.map(trace => `
        <tr class="trace-row" data-trace-id="${trace.id}" onclick="showTraceDetail(${trace.id})">
            <td>
                <small class="text-muted">${formatRelativeTime(trace.timestamp)}</small>
            </td>
            <td>
                <span class="badge bg-secondary">${getModelShortName(trace.model_name)}</span>
            </td>
            <td>
                <small>${escapeHtml(truncateString(trace.user_identifier, 20))}</small>
            </td>
            <td>
                <small>${escapeHtml(trace.feature_name)}</small>
            </td>
            <td>
                <span class="text-info">${formatNumber(trace.input_tokens)}</span>
                <span class="text-muted mx-1">/</span>
                <span class="text-success">${formatNumber(trace.output_tokens)}</span>
            </td>
            <td>
                <span class="latency-indicator ${trace.latency_status}">
                    <span class="dot"></span>
                    ${trace.latency_ms.toFixed(0)}ms
                </span>
            </td>
            <td>
                <small>$${parseFloat(trace.cost_usd).toFixed(6)}</small>
            </td>
            <td>
                <span class="status-badge ${trace.status}">${trace.status}</span>
            </td>
        </tr>
    `).join('');
}


/**
 * Update pagination controls
 */
function updatePagination(data) {
    const paginationEl = document.getElementById('pagination');
    if (!paginationEl) return;
    
    const totalPages = Math.ceil(data.count / state.pageSize);
    
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let html = `
        <li class="page-item ${state.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${state.currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, state.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="goToPage(1); return false;">1</a>
            </li>
        `;
        if (startPage > 2) {
            html += `
                <li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>
            `;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${state.currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" onclick="goToPage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `
                <li class="page-item disabled">
                    <span class="page-link">...</span>
                </li>
            `;
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="goToPage(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    html += `
        <li class="page-item ${state.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${state.currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationEl.innerHTML = html;
    
    // Update showing count
    const showingStart = (state.currentPage - 1) * state.pageSize + 1;
    const showingEnd = Math.min(state.currentPage * state.pageSize, data.count);
    const showingEl = document.getElementById('showingCount');
    if (showingEl) {
        showingEl.textContent = `Showing ${showingStart}-${showingEnd} of ${data.count}`;
    }
}


/**
 * Navigate to page
 */
function goToPage(page) {
    state.currentPage = page;
    loadRecentTraces();
}


// ============================================================
// Trace Detail
// ============================================================

/**
 * Show trace detail modal
 */
async function showTraceDetail(traceId) {
    const modal = new bootstrap.Modal(document.getElementById('traceDetailModal'));
    
    try {
        const trace = await apiRequest(`/api/traces/${traceId}/`);
        
        document.getElementById('traceDetailContent').innerHTML = `
            <div class="row g-3">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="badge bg-secondary">${trace.model_name}</span>
                        <span class="status-badge ${trace.status}">${trace.status}</span>
                    </div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Timestamp</div>
                    <div>${formatTimestamp(trace.timestamp)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">User</div>
                    <div>${escapeHtml(trace.user_identifier)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Feature</div>
                    <div>${escapeHtml(trace.feature_name)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Input Tokens</div>
                    <div class="text-info">${formatNumber(trace.input_tokens)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Output Tokens</div>
                    <div class="text-success">${formatNumber(trace.output_tokens)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Total Tokens</div>
                    <div>${formatNumber(trace.total_tokens)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Latency</div>
                    <div>
                        <span class="latency-indicator ${trace.latency_status}">
                            <span class="dot"></span>
                            ${trace.latency_ms.toFixed(2)}ms
                        </span>
                    </div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Cost</div>
                    <div class="text-warning">$${parseFloat(trace.cost_usd).toFixed(6)}</div>
                </div>
                
                <div class="col-6 col-md-4">
                    <div class="text-muted small">Request ID</div>
                    <div class="text-truncate" style="max-width: 150px;" title="${trace.request_id || 'N/A'}">${trace.request_id || 'N/A'}</div>
                </div>
                
                ${trace.prompt_preview ? `
                <div class="col-12 mt-3">
                    <div class="text-muted small mb-1">Prompt Preview</div>
                    <div class="bg-dark p-3 rounded" style="max-height: 200px; overflow-y: auto;">
                        <pre class="text-light mb-0" style="white-space: pre-wrap;">${escapeHtml(trace.prompt_preview)}</pre>
                    </div>
                </div>
                ` : ''}
                
                ${trace.response_preview ? `
                <div class="col-12 mt-2">
                    <div class="text-muted small mb-1">Response Preview</div>
                    <div class="bg-dark p-3 rounded" style="max-height: 200px; overflow-y: auto;">
                        <pre class="text-light mb-0" style="white-space: pre-wrap;">${escapeHtml(trace.response_preview)}</pre>
                    </div>
                </div>
                ` : ''}
                
                ${trace.error_message ? `
                <div class="col-12 mt-2">
                    <div class="text-muted small mb-1">Error Message</div>
                    <div class="alert alert-danger mb-0">
                        ${escapeHtml(trace.error_message)}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        
        modal.show();
    } catch (error) {
        console.error('Error loading trace detail:', error);
        showToast('Failed to load trace details', 'danger');
    }
}


// ============================================================
// Filters
// ============================================================

function applyFilters() {
    const statusEl = document.getElementById('filterStatus');
    const modelEl = document.getElementById('filterModel');
    const startDateEl = document.getElementById('filterStartDate');
    const endDateEl = document.getElementById('filterEndDate');
    
    state.filters = {
        status: statusEl ? statusEl.value : '',
        model: modelEl ? modelEl.value : '',
        start_date: startDateEl ? startDateEl.value : '',
        end_date: endDateEl ? endDateEl.value : ''
    };
    
    state.currentPage = 1;
    loadRecentTraces();
    
    showToast('Filters applied', 'info');
}


function clearFilters() {
    state.filters = {
        status: '',
        model: '',
        user: '',
        feature: '',
        start_date: '',
        end_date: ''
    };
    
    // Reset form elements
    const statusEl = document.getElementById('filterStatus');
    const modelEl = document.getElementById('filterModel');
    const startDateEl = document.getElementById('filterStartDate');
    const endDateEl = document.getElementById('filterEndDate');
    
    if (statusEl) statusEl.value = '';
    if (modelEl) modelEl.value = '';
    if (startDateEl) startDateEl.value = '';
    if (endDateEl) endDateEl.value = '';
    
    state.currentPage = 1;
    loadRecentTraces();
    
    showToast('Filters cleared', 'info');
}


// ============================================================
// Export
// ============================================================

function exportTraces() {
    let url = '/api/traces/export/?';
    const params = [];
    
    if (state.filters.status) params.push(`status=${state.filters.status}`);
    if (state.filters.model) params.push(`model=${state.filters.model}`);
    if (state.filters.start_date) params.push(`start_date=${state.filters.start_date}`);
    if (state.filters.end_date) params.push(`end_date=${state.filters.end_date}`);
    
    window.location.href = url + params.join('&');
    showToast('Export started...', 'info');
}


// ============================================================
// Auto Refresh
// ============================================================

function startAutoRefresh() {
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
    }
    
    state.refreshInterval = setInterval(() => {
        refreshDashboard();
    }, state.refreshRate);
}


function stopAutoRefresh() {
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
        state.refreshInterval = null;
    }
}


async function refreshDashboard() {
    if (state.isLoading) return;
    
    state.isLoading = true;
    
    const refreshBtn = document.getElementById('refreshDashboard');
    if (refreshBtn) {
        refreshBtn.classList.add('rotating');
    }
    
    try {
        await Promise.all([
            loadDashboardOverview(),
            loadDashboardCharts(),
            loadRecentTraces()
        ]);
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    } finally {
        state.isLoading = false;
        if (refreshBtn) {
            refreshBtn.classList.remove('rotating');
        }
    }
}


// ============================================================
// Feedback Modal
// ============================================================

function showFeedbackModal(traceId) {
    const modal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    document.getElementById('feedbackTraceId').value = traceId;
    document.getElementById('feedbackRating').value = '';
    document.getElementById('feedbackComment').value = '';
    
    // Reset stars to empty state
    document.querySelectorAll('.star-rating i').forEach(star => {
        star.classList.remove('bi-star-fill');
        star.classList.add('bi-star');
        star.style.color = '#d1d5db';
    });
    
    // Reset rating text
    const ratingText = document.getElementById('ratingText');
    if (ratingText) {
        ratingText.textContent = '';
    }
    
    modal.show();
}


async function submitFeedback() {
    const traceId = document.getElementById('feedbackTraceId').value;
    const rating = document.getElementById('feedbackRating').value;
    const comment = document.getElementById('feedbackComment').value;
    
    if (!rating) {
        showToast('Please select a rating', 'warning');
        return;
    }
    
    const submitBtn = document.getElementById('submitFeedbackBtn');
    showLoading(submitBtn, 'Submitting...');
    
    try {
        await apiRequest('/api/feedback/', {
            method: 'POST',
            body: JSON.stringify({
                trace: traceId,
                rating: parseInt(rating),
                comment: comment
            })
        });
        
        bootstrap.Modal.getInstance(document.getElementById('feedbackModal')).hide();
        showToast('Feedback submitted successfully', 'success');
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showToast('Failed to submit feedback', 'danger');
    } finally {
        hideLoading(submitBtn);
    }
}


// Star rating click handler
document.addEventListener('click', function(e) {
    if (e.target.closest('.star-rating i')) {
        const star = e.target.closest('.star-rating i');
        const rating = star.dataset.rating;
        
        document.getElementById('feedbackRating').value = rating;
        
        // Update visual state
        document.querySelectorAll('.star-rating i').forEach((s, index) => {
            if (index < rating) {
                s.classList.add('active');
            } else {
                s.classList.remove('active');
            }
        });
    }
});


// ============================================================
// Keyboard Shortcuts
// ============================================================

document.addEventListener('keydown', function(e) {
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
    
    // R to refresh (when not in input)
    if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
        const activeEl = document.activeElement;
        if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(activeEl.tagName)) {
            e.preventDefault();
            refreshDashboard();
        }
    }
});


// ============================================================
// CSS Animation for Refresh Button
// ============================================================

const style = document.createElement('style');
style.textContent = `
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .rotating {
        animation: rotate 1s linear infinite;
    }
`;
document.head.appendChild(style);
