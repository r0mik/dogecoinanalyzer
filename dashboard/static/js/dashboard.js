// DogeAnalyze Dashboard JavaScript

let priceChart = null;

// Format currency
function formatCurrency(value) {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 8
    }).format(value);
}

// Format large numbers
function formatLargeNumber(value) {
    if (value === null || value === undefined) return '0';
    if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B';
    if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M';
    if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K';
    return value.toFixed(2);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Fetch current market data
async function fetchCurrentData() {
    try {
        const response = await fetch('/api/current');
        if (!response.ok) throw new Error('Failed to fetch current data');
        const data = await response.json();
        updateCurrentData(data);
    } catch (error) {
        console.error('Error fetching current data:', error);
    }
}

// Update current data display
function updateCurrentData(data) {
    document.getElementById('current-price').textContent = formatCurrency(data.price_usd);
    
    if (data.volume_24h) {
        document.getElementById('volume-24h').textContent = '$' + formatLargeNumber(data.volume_24h);
    }
    
    if (data.market_cap) {
        document.getElementById('market-cap').textContent = '$' + formatLargeNumber(data.market_cap);
    }
    
    if (data.high_24h) {
        document.getElementById('high-24h').textContent = formatCurrency(data.high_24h);
    }
    
    if (data.low_24h) {
        document.getElementById('low-24h').textContent = formatCurrency(data.low_24h);
    }
    
    // Update price change
    const priceChangeEl = document.getElementById('price-change');
    if (data.price_change_24h !== null && data.price_change_24h !== undefined) {
        const change = data.price_change_24h;
        const sign = change >= 0 ? '+' : '';
        priceChangeEl.textContent = `${sign}${change.toFixed(2)}%`;
        priceChangeEl.className = 'stat-change ' + (change >= 0 ? 'positive' : 'negative');
    } else {
        priceChangeEl.textContent = '--';
    }
}

// Fetch and display price history
async function fetchHistory() {
    try {
        const response = await fetch('/api/history?hours=24&limit=100');
        if (!response.ok) throw new Error('Failed to fetch history');
        const result = await response.json();
        updatePriceChart(result.data);
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// Update price chart
function updatePriceChart(data) {
    if (!data || data.length === 0) return;
    
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString();
    });
    
    const prices = data.map(item => parseFloat(item.price_usd));
    
    if (priceChart) {
        priceChart.data.labels = labels;
        priceChart.data.datasets[0].data = prices;
        priceChart.update();
    } else {
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'DOGE Price (USD)',
                    data: prices,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
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
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
}

// Fetch and display analysis results
async function fetchAnalysis() {
    try {
        const response = await fetch('/api/analysis');
        if (!response.ok) throw new Error('Failed to fetch analysis');
        const result = await response.json();
        updateAnalysisDisplay(result.by_timeframe || {});
    } catch (error) {
        console.error('Error fetching analysis:', error);
    }
}

// Update analysis display
function updateAnalysisDisplay(analysisByTimeframe) {
    const grid = document.getElementById('analysis-grid');
    grid.innerHTML = '';
    
    const timeframes = ['1h', '4h', '24h'];
    
    timeframes.forEach(timeframe => {
        const analysis = analysisByTimeframe[timeframe];
        const card = document.createElement('div');
        card.className = 'analysis-card';
        
        if (analysis) {
            const trendClass = analysis.trend_direction === 'bullish' ? 'trend-bullish' :
                              analysis.trend_direction === 'bearish' ? 'trend-bearish' : 'trend-neutral';
            
            card.innerHTML = `
                <h3>${timeframe} Prediction</h3>
                <div class="analysis-item">
                    <div class="analysis-item-label">Predicted Price</div>
                    <div class="analysis-item-value">${formatCurrency(analysis.predicted_price)}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-item-label">Trend</div>
                    <div class="analysis-item-value ${trendClass}">${analysis.trend_direction || 'N/A'}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-item-label">Confidence</div>
                    <div class="analysis-item-value">${analysis.confidence_score || 0}%</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${analysis.confidence_score || 0}%"></div>
                    </div>
                </div>
                ${analysis.reasoning ? `
                <div class="analysis-item">
                    <div class="analysis-item-label">Reasoning</div>
                    <div class="analysis-item-value" style="font-size: 0.9em;">${analysis.reasoning}</div>
                </div>
                ` : ''}
            `;
        } else {
            card.innerHTML = `
                <h3>${timeframe} Prediction</h3>
                <div class="analysis-item">
                    <div class="analysis-item-value">No analysis available</div>
                </div>
            `;
        }
        
        grid.appendChild(card);
    });
}

// Fetch and display script status
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Failed to fetch status');
        const result = await response.json();
        updateStatusDisplay(result.data || []);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// Update status display
function updateStatusDisplay(statuses) {
    const grid = document.getElementById('status-grid');
    grid.innerHTML = '';
    
    if (statuses.length === 0) {
        grid.innerHTML = '<div class="status-card"><p>No status information available</p></div>';
        return;
    }
    
    statuses.forEach(status => {
        const card = document.createElement('div');
        const statusClass = status.status === 'success' ? 'success' :
                           status.status === 'error' ? 'error' :
                           status.status === 'running' ? 'running' : '';
        
        card.className = `status-card ${statusClass}`;
        
        card.innerHTML = `
            <h3>${status.script_name || 'Unknown'}</h3>
            <span class="status-badge ${status.status || ''}">${status.status || 'unknown'}</span>
            <div class="status-info">
                ${status.last_run ? `<p>Last run: ${formatDate(status.last_run)}</p>` : ''}
                ${status.next_run ? `<p>Next run: ${formatDate(status.next_run)}</p>` : ''}
                ${status.message ? `<p>${status.message}</p>` : ''}
            </div>
        `;
        
        grid.appendChild(card);
    });
}

// Fetch stats and update last update time
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        if (data.last_update) {
            document.getElementById('last-update').textContent = formatDate(data.last_update);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Refresh all data
async function refreshAll() {
    await Promise.all([
        fetchCurrentData(),
        fetchHistory(),
        fetchAnalysis(),
        fetchStatus(),
        fetchStats()
    ]);
}

// Initialize dashboard
async function init() {
    console.log('Initializing DogeAnalyze Dashboard...');
    await refreshAll();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshAll, 30000);
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

