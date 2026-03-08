// WebSocket connection
let ws = null;
let reconnectInterval = null;
const RECONNECT_DELAY = 3000;

// Charts
let cpuChart = null;
let memoryChart = null;
let requestChart = null;
let errorChart = null;

// Data storage for charts
const chartData = {
    labels: [],
    cpu: [],
    memory: [],
    requests: [],
    errors: []
};

// Maximum data points to keep
const MAX_DATA_POINTS = 30;

// Initialize WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    ws.onclose = function() {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        scheduleReconnect();
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Schedule reconnection attempt
function scheduleReconnect() {
    if (!reconnectInterval) {
        reconnectInterval = setInterval(function() {
            console.log('Attempting to reconnect...');
            initWebSocket();
        }, RECONNECT_DELAY);
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-text');

    if (connected) {
        statusDot.className = 'w-3 h-3 rounded-full status-online pulse';
        statusText.textContent = 'Connected';
        statusText.className = 'text-sm text-green-400';
    } else {
        statusDot.className = 'w-3 h-3 rounded-full status-offline';
        statusText.textContent = 'Disconnected';
        statusText.className = 'text-sm text-red-400';
    }
}

// Handle incoming WebSocket messages
function handleMessage(data) {
    switch(data.type) {
        case 'service_update':
            updateServiceStatus(data.services);
            break;
        case 'alert':
            addAlert(data.alert);
            break;
        case 'metrics':
            updateCharts(data.metrics);
            break;
        case 'event':
            addEvent(data.event);
            break;
        case 'init':
            initializeDashboard(data);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// Initialize dashboard with initial data
function initializeDashboard(data) {
    if (data.services) {
        updateServiceStatus(data.services);
    }
    if (data.metrics) {
        updateCharts(data.metrics);
    }
    if (data.alerts) {
        data.alerts.forEach(alert => addAlert(alert));
    }
    if (data.events) {
        data.events.forEach(event => addEvent(event));
    }
}

// Update service status display
function updateServiceStatus(services) {
    const container = document.getElementById('service-status');
    container.innerHTML = '';

    services.forEach(service => {
        const statusClass = service.status === 'online' ? 'status-online' :
                           service.status === 'degraded' ? 'status-degraded' : 'status-offline';
        const statusText = service.status.charAt(0).toUpperCase() + service.status.slice(1);

        const card = document.createElement('div');
        card.className = 'bg-gray-700 rounded-lg p-4 border border-gray-600';
        card.setAttribute('data-testid', `agent-${service.name.toLowerCase().replace(/\s+/g, '-')}-status`);
        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-semibold text-lg">${service.name}</h3>
                <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 rounded-full ${statusClass}"></div>
                    <span class="text-sm ${service.status === 'online' ? 'text-green-400' : service.status === 'degraded' ? 'text-yellow-400' : 'text-red-400'}">${statusText}</span>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                    <span class="text-gray-400">CPU:</span>
                    <span class="text-white ml-2">${service.cpu}%</span>
                </div>
                <div>
                    <span class="text-gray-400">Memory:</span>
                    <span class="text-white ml-2">${service.memory}MB</span>
                </div>
                <div>
                    <span class="text-gray-400">Requests:</span>
                    <span class="text-white ml-2">${service.requests}/s</span>
                </div>
                <div>
                    <span class="text-gray-400">Errors:</span>
                    <span class="text-white ml-2">${service.errors}%</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Add alert to the console
function addAlert(alert) {
    const container = document.getElementById('alerts-console');
    const alertClass = alert.severity === 'critical' ? 'alert-critical' :
                      alert.severity === 'warning' ? 'alert-warning' : 'alert-info';

    const alertDiv = document.createElement('div');
    alertDiv.className = `bg-gray-700 p-3 rounded ${alertClass}`;
    alertDiv.setAttribute('data-testid', `alert-${alert.severity}`);
    alertDiv.innerHTML = `
        <div class="flex items-center justify-between mb-1">
            <span class="font-semibold ${alert.severity === 'critical' ? 'text-red-400' : alert.severity === 'warning' ? 'text-yellow-400' : 'text-blue-400'}">
                ${alert.severity.toUpperCase()}
            </span>
            <span class="text-xs text-gray-400">${formatTimestamp(alert.timestamp)}</span>
        </div>
        <div class="text-sm">${alert.message}</div>
        <div class="text-xs text-gray-400 mt-1">Service: ${alert.service}</div>
    `;

    container.insertBefore(alertDiv, container.firstChild);

    // Keep only last 50 alerts
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }
}

// Add event to the feed
function addEvent(event) {
    const container = document.getElementById('event-feed');
    const eventDiv = document.createElement('div');
    eventDiv.className = 'py-1 border-b border-gray-700';

    const timestamp = formatTimestamp(event.timestamp);
    const levelClass = event.level === 'ERROR' ? 'text-red-400' :
                      event.level === 'WARN' ? 'text-yellow-400' : 'text-gray-300';

    eventDiv.innerHTML = `
        <span class="text-gray-500">[${timestamp}]</span>
        <span class="${levelClass}">[${event.level}]</span>
        <span class="text-cyan-400">${event.service}:</span>
        <span class="text-gray-300">${event.message}</span>
    `;

    container.insertBefore(eventDiv, container.firstChild);

    // Keep only last 100 events
    while (container.children.length > 100) {
        container.removeChild(container.lastChild);
    }
}

// Update charts with new metrics
function updateCharts(metrics) {
    // Add new data point
    const timestamp = formatTimestamp(metrics.timestamp);
    chartData.labels.push(timestamp);
    chartData.cpu.push(metrics.cpu);
    chartData.memory.push(metrics.memory);
    chartData.requests.push(metrics.requests);
    chartData.errors.push(metrics.errors);

    // Remove old data points
    if (chartData.labels.length > MAX_DATA_POINTS) {
        chartData.labels.shift();
        chartData.cpu.shift();
        chartData.memory.shift();
        chartData.requests.shift();
        chartData.errors.shift();
    }

    // Update all charts
    if (cpuChart) {
        cpuChart.data.labels = chartData.labels;
        cpuChart.data.datasets[0].data = chartData.cpu;
        cpuChart.update('none');
    }

    if (memoryChart) {
        memoryChart.data.labels = chartData.labels;
        memoryChart.data.datasets[0].data = chartData.memory;
        memoryChart.update('none');
    }

    if (requestChart) {
        requestChart.data.labels = chartData.labels;
        requestChart.data.datasets[0].data = chartData.requests;
        requestChart.update('none');
    }

    if (errorChart) {
        errorChart.data.labels = chartData.labels;
        errorChart.data.datasets[0].data = chartData.errors;
        errorChart.update('none');
    }
}

// Initialize charts
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        animation: false,
        scales: {
            x: {
                display: false
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#9ca3af'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    };

    // CPU Chart
    cpuChart = new Chart(document.getElementById('cpu-chart'), {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.cpu,
                borderColor: '#a855f7',
                backgroundColor: 'rgba(168, 85, 247, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: { ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y, max: 100 } } }
    });

    // Memory Chart
    memoryChart = new Chart(document.getElementById('memory-chart'), {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.memory,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });

    // Request Chart
    requestChart = new Chart(document.getElementById('request-chart'), {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.requests,
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });

    // Error Chart
    errorChart = new Chart(document.getElementById('error-chart'), {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.errors,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: { ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y, max: 100 } } }
    });
}

// Send command to server
function sendCommand(command) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'command',
            command: command,
            timestamp: new Date().toISOString()
        }));
        addEvent({
            timestamp: new Date().toISOString(),
            level: 'INFO',
            service: 'operator-console',
            message: `Command sent: ${command}`
        });
    } else {
        alert('WebSocket is not connected. Please wait for reconnection.');
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
}

// Update current time display
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    timeElement.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    initWebSocket();
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});
