// Admin Dashboard JavaScript
// Handles chart initialization, session management, and real-time updates

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sales chart with Chart.js
    initializeSalesChart();
    
    // Auto-refresh active sessions every 60 seconds
    setInterval(refreshActiveSessions, 60000);
    
    // Handle session termination buttons
    setupSessionTermination();
    
    // Setup export functionality
    setupExportButtons();
    
    // Initialize real-time clock
    updateClock();
    setInterval(updateClock, 1000);
});

let salesChart = null;
let currentChartPeriod = 'daily';

function initializeSalesChart() {
    const chartCanvas = document.getElementById('salesChart');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // Get data from Django template (embedded in data attributes)
    const labels = JSON.parse(chartCanvas.dataset.labels || '[]');
    const data = JSON.parse(chartCanvas.dataset.values || '[]');
    
    salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sales Revenue (₹)',
                data: data,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointBackgroundColor: '#ffc107',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return 'Revenue: ₹' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function switchChartPeriod(period) {
    if (currentChartPeriod === period) return;
    
    currentChartPeriod = period;
    
    // Update active button
    document.querySelectorAll('.chart-period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Fetch new data via AJAX
    fetch(`/admin/dashboard/chart-data/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            if (salesChart) {
                salesChart.data.labels = data.labels;
                salesChart.data.datasets[0].data = data.values;
                salesChart.update();
            }
        })
        .catch(error => console.error('Error fetch ing chart data:', error));
}

function refreshActiveSessions() {
    fetch('/admin/dashboard/active-sessions/')
        .then(response => response.json())
        .then(data => {
            const sessionsContainer = document.getElementById('activeSessionsTable');
            if (sessionsContainer && data.html) {
                sessionsContainer.innerHTML = data.html;
                // Re-setup termination buttons
                setupSessionTermination();
            }
        })
        .catch(error => console.error('Error refreshing sessions:', error));
}

function setupSessionTermination() {
    document.querySelectorAll('.terminate-session-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to terminate this session?')) {
                return;
            }
            
            const sessionId = this.dataset.sessionId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(`/admin/terminate-session/${sessionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Session terminated successfully', 'success');
                    refreshActiveSessions();
                } else {
                    showToast(data.message || 'Error terminating session', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Network error occurred', 'error');
            });
        });
    });
}

function setupExportButtons() {
    const exportBtn = document.getElementById('exportActivityLog');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('export', 'csv');
            window.location.href = currentUrl.toString();
        });
    }
}

function updateClock() {
    const clockElement = document.getElementById('serverClock');
    if (clockElement) {
        const now = new Date();
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        };
        clockElement.textContent = now.toLocaleString('en-IN', options);
    }
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} toast-notification`;
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; animation: slideInRight 0.3s ease;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Make functions globally available
window.switchChartPeriod = switchChartPeriod;
