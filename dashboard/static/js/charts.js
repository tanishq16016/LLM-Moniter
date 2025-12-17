/**
 * LLM Monitor - Chart Configuration
 * Light theme Chart.js configurations
 */

// Light theme defaults
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#e2e8f0';
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

// Global plugin configuration
Chart.defaults.plugins.legend.labels.padding = 15;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.95)';
Chart.defaults.plugins.tooltip.titleColor = '#1e293b';
Chart.defaults.plugins.tooltip.bodyColor = '#64748b';
Chart.defaults.plugins.tooltip.borderColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;

// Color palette for light theme
const chartColors = {
    primary: '#4f46e5',
    success: '#059669',
    warning: '#d97706',
    danger: '#dc2626',
    purple: '#7c3aed',
    teal: '#0d9488',
    orange: '#ea580c',
    pink: '#db2777',
    blue: '#2563eb',
    gray: '#64748b'
};

const chartPalette = [
    chartColors.primary,
    chartColors.success,
    chartColors.warning,
    chartColors.purple,
    chartColors.teal,
    chartColors.orange,
    chartColors.pink,
    chartColors.blue
];

/**
 * Create gradient for charts
 */
function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, hexToRgba(color, 0.2));
    gradient.addColorStop(1, hexToRgba(color, 0.02));
    return gradient;
}

/**
 * Convert hex to rgba
 */
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Create line chart
 */
function createLineChart(canvasId, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: options.labels || [],
            datasets: [{
                label: options.label || 'Data',
                data: options.data || [],
                borderColor: options.color || chartColors.primary,
                backgroundColor: createGradient(ctx.getContext('2d'), options.color || chartColors.primary),
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b' }
                },
                y: {
                    grid: { color: '#e2e8f0' },
                    ticks: { color: '#64748b' }
                }
            }
        }
    });
}

/**
 * Create bar chart
 */
function createBarChart(canvasId, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: options.labels || [],
            datasets: [{
                label: options.label || 'Data',
                data: options.data || [],
                backgroundColor: options.color || chartColors.primary,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b' }
                },
                y: {
                    grid: { color: '#e2e8f0' },
                    ticks: { color: '#64748b' }
                }
            }
        }
    });
}

/**
 * Create doughnut chart
 */
function createDoughnutChart(canvasId, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: options.labels || [],
            datasets: [{
                data: options.data || [],
                backgroundColor: chartPalette.slice(0, (options.data || []).length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#64748b' }
                }
            }
        }
    });
}

/**
 * Update chart data
 */
function updateChart(chart, labels, data) {
    if (!chart) return;
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
}

/**
 * Format large numbers
 */
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// Export for use
window.ChartUtils = {
    createLineChart,
    createBarChart,
    createDoughnutChart,
    updateChart,
    formatNumber,
    colors: chartColors,
    palette: chartPalette
};
