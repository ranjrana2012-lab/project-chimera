// Chimera Monitoring Dashboard JavaScript
// Auto-refreshes every 5 seconds

const REFRESH_INTERVAL = 5000; // 5 seconds
let cpuChart = null;
let memoryChart = null;

// Initialize charts
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    color: '#374151'
                },
                ticks: {
                    color: '#9ca3af',
                    maxTicksLimit: 6
                }
            },
            y: {
                beginAtZero: true,
                max: 100,
                grid: {
                    color: '#374151'
                },
                ticks: {
                    color: '#9ca3af',
                    callback: value => value + '%'
                }
            }
        },
        elements: {
            line: {
                tension: 0.4
            },
            point: {
                radius: 2
            }
        }
    };

    // CPU Chart
    const cpuCtx = document.getElementById('cpuChart').getContext('2d');
    cpuChart = new Chart(cpuCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Usage',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'CPU Usage Over Time',
                    color: '#f9fafb'
                }
            }
        }
    });

    // Memory Chart
    const memoryCtx = document.getElementById('memoryChart').getContext('2d');
    memoryChart = new Chart(memoryCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'Memory Usage Over Time',
                    color: '#f9fafb'
                }
            }
        }
    });
}

// Update connection status
function updateConnectionStatus(status) {
    const statusDot = document.querySelector('#connectionStatus .status-dot');
    const statusText = document.querySelector('#connectionStatus .status-text');

    statusDot.classList.remove('connected', 'error');

    switch (status) {
        case 'connected':
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
            break;
        case 'error':
            statusDot.classList.add('error');
            statusText.textContent = 'Connection Error';
            break;
        default:
            statusText.textContent = 'Connecting...';
    }
}

// Update stat card
function updateStatCard(cardId, value, stale = false) {
    const valueEl = document.getElementById(`${cardId}Value`);
    const staleEl = document.getElementById(`${cardId}Stale`);

    if (valueEl) {
        valueEl.textContent = value;
    }
    if (staleEl) {
        if (stale) {
            staleEl.classList.remove('hidden');
        } else {
            staleEl.classList.add('hidden');
        }
    }
}

// Update chart with new data
function updateChart(chart, labels, data) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update('none'); // Update without animation for performance
}

// Fetch CPU metrics
async function fetchCPUMetrics() {
    try {
        const response = await fetch('/api/metrics/cpu');
        if (!response.ok) throw new Error('Failed to fetch CPU metrics');
        const data = await response.json();

        // Update stat card
        updateStatCard('cpu', `${data.usage_pct}%`, data.stale);

        // Update chart if we have history
        if (data.history && data.history.length > 0) {
            const labels = data.history.map(point => {
                const date = new Date(point.timestamp * 1000);
                return date.toLocaleTimeString();
            });
            const values = data.history.map(point => point.value);
            updateChart(cpuChart, labels, values);
        }

        return data;
    } catch (error) {
        console.error('Error fetching CPU metrics:', error);
        updateStatCard('cpu', '--%', true);
        return null;
    }
}

// Fetch GPU metrics
async function fetchGPUMetrics() {
    try {
        const response = await fetch('/api/metrics/gpu');
        if (!response.ok) throw new Error('Failed to fetch GPU metrics');
        const data = await response.json();

        updateStatCard('gpu', `${data.utilization_pct}%`, data.stale);
        return data;
    } catch (error) {
        console.error('Error fetching GPU metrics:', error);
        updateStatCard('gpu', '--%', true);
        return null;
    }
}

// Fetch memory metrics
async function fetchMemoryMetrics() {
    try {
        const response = await fetch('/api/metrics/memory');
        if (!response.ok) throw new Error('Failed to fetch memory metrics');
        const data = await response.json();

        // Update stat card
        updateStatCard('memory', `${data.usage_pct}%`, data.stale);

        // Update chart if we have history
        if (data.history && data.history.length > 0) {
            const labels = data.history.map(point => {
                const date = new Date(point.timestamp * 1000);
                return date.toLocaleTimeString();
            });
            const values = data.history.map(point => point.value);
            updateChart(memoryChart, labels, values);
        }

        return data;
    } catch (error) {
        console.error('Error fetching memory metrics:', error);
        updateStatCard('memory', '--%', true);
        return null;
    }
}

// Fetch container metrics
async function fetchContainerMetrics() {
    try {
        const response = await fetch('/api/metrics/containers');
        if (!response.ok) throw new Error('Failed to fetch container metrics');
        const data = await response.json();

        const tbody = document.getElementById('containersBody');
        if (!tbody) return;

        if (!data.containers || Object.keys(data.containers).length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No container data available</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        for (const [name, metrics] of Object.entries(data.containers)) {
            const row = document.createElement('tr');
            const statusClass = metrics.stale ? 'unknown' : 'healthy';
            const statusText = metrics.stale ? 'Stale' : 'Running';

            row.innerHTML = `
                <td>${name}</td>
                <td>${metrics.cpu_pct.toFixed(1)}%</td>
                <td>${metrics.memory_mb.toFixed(0)}</td>
                <td><span class="service-status ${statusClass}">${statusText}</span></td>
            `;
            tbody.appendChild(row);
        }
    } catch (error) {
        console.error('Error fetching container metrics:', error);
        const tbody = document.getElementById('containersBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="4">Error loading container data</td></tr>';
        }
    }
}

// Fetch application health
async function fetchAppHealth() {
    try {
        const response = await fetch('/api/metrics/summary');
        if (!response.ok) throw new Error('Failed to fetch app health');
        const data = await response.json();

        // Update services stat card
        const services = data.applications || {};
        const healthyCount = Object.values(services).filter(s => s.status === 'healthy').length;
        const totalCount = Object.keys(services).length;
        updateStatCard('services', `${healthyCount}/${totalCount}`);

        // Update services grid
        const grid = document.getElementById('servicesGrid');
        if (!grid) return;

        grid.innerHTML = '';
        for (const [name, info] of Object.entries(services)) {
            const card = document.createElement('div');
            card.className = 'service-card';
            card.innerHTML = `
                <div class="service-name">${name}</div>
                <div class="service-status ${info.status}">${info.status}</div>
                <div class="service-url">${info.url || 'N/A'}</div>
            `;
            grid.appendChild(card);
        }
    } catch (error) {
        console.error('Error fetching app health:', error);
        updateStatCard('services', '--/--');
    }
}

// Fetch all metrics
async function fetchAllMetrics() {
    try {
        await Promise.all([
            fetchCPUMetrics(),
            fetchGPUMetrics(),
            fetchMemoryMetrics(),
            fetchContainerMetrics(),
            fetchAppHealth()
        ]);
        updateConnectionStatus('connected');
    } catch (error) {
        console.error('Error fetching metrics:', error);
        updateConnectionStatus('error');
    }
}

// Initialize dashboard
async function init() {
    initCharts();
    await fetchAllMetrics();

    // Set up auto-refresh
    setInterval(fetchAllMetrics, REFRESH_INTERVAL);
}

// Start dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
