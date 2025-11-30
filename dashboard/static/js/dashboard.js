// DogeAnalyze Dashboard JavaScript

let priceChart = null;
let selectedTimeframe = 'all'; // Current selected timeframe

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

// Format reasoning text with structured table format
// condensed: if true, show simplified version (for "All" view)
function formatReasoning(reasoning, condensed = false) {
    if (!reasoning) return '';
    
    // If condensed mode, show only key summary
    if (condensed) {
        return formatReasoningCondensed(reasoning);
    }
    
    // Split by pipe separator
    const parts = reasoning.split('|').map(p => p.trim()).filter(p => p);
    
    let html = '<div class="reasoning-parsed">';
    
    // Extract timeframe
    let timeframe = '';
    const timeframeMatch = reasoning.match(/Analysis for (.+?) timeframe:/);
    if (timeframeMatch) {
        timeframe = timeframeMatch[1];
    }
    
    // Start with indicators table
    html += '<div class="indicators-table-container">';
    html += '<table class="indicators-table">';
    html += '<thead><tr><th>Indicator</th><th>Value</th><th>Interpretation</th></tr></thead>';
    html += '<tbody>';
    
    // Parse each part and add to table
    parts.forEach((part) => {
        if (part.includes('Analysis for')) {
            // Skip, already handled
            return;
        }
        
        let indicator = '';
        let value = '';
        let interpretation = '';
        
        // Parse Current Price
        if (part.includes('Current price:')) {
            const match = part.match(/Current price: (.+)/);
            indicator = '<strong>Price</strong>';
            value = match ? match[1].trim() : '';
            interpretation = 'Current market price';
        }
        // Parse Predicted Price
        else if (part.includes('Predicted price:')) {
            const match = part.match(/Predicted price: (.+?) \((.+?)\)/);
            if (match) {
                indicator = '<strong>Predicted Price</strong>';
                value = match[1].trim();
                const change = match[2].trim();
                const isPositive = change.includes('increase') || change.includes('+');
                const changeClass = isPositive ? 'change-positive' : 'change-negative';
                interpretation = `<span class="${changeClass}">${change}</span>`;
            }
        }
        // Parse Trend
        else if (part.includes('Trend:')) {
            const match = part.match(/Trend: (.+)/);
            if (match) {
                const trend = match[1].trim();
                const trendLower = trend.toLowerCase();
                const trendClass = trendLower.includes('bullish') ? 'trend-bullish' : 
                                 trendLower.includes('bearish') ? 'trend-bearish' : 'trend-neutral';
                indicator = '<strong>Trend</strong>';
                value = `<span class="trend-badge ${trendClass}">${trend}</span>`;
                interpretation = trendLower.includes('bullish') ? 'Upward price movement expected' : 
                               trendLower.includes('bearish') ? 'Downward price movement expected' : 
                               'Neutral price movement';
            }
        }
        // Parse RSI
        else if (part.includes('RSI')) {
            const match = part.match(/RSI \(([\d.]+)\)/);
            const rsiValue = match ? match[1] : '';
            const rsiStatus = part.includes('neutral') ? 'neutral' : 
                            part.includes('overbought') ? 'overbought' : 
                            part.includes('oversold') ? 'oversold' : 'neutral';
            indicator = '<strong>RSI</strong>';
            value = rsiValue ? `<span class="indicator-value rsi-${rsiStatus}">${rsiValue}</span>` : '';
            // Extract interpretation after RSI value
            let rsiInterpretation = part.replace(/RSI[^(]*\([^)]*\)/, '').trim();
            if (!rsiInterpretation) {
                rsiInterpretation = rsiStatus === 'neutral' ? 'Neutral; not yet overbought, leaving room for further upside' : 
                                  rsiStatus === 'overbought' ? 'Overbought condition, potential reversal risk' : 
                                  'Oversold condition, potential bounce opportunity';
            }
            interpretation = rsiInterpretation;
        }
        // Parse MACD
        else if (part.includes('MACD')) {
            const macdClass = part.toLowerCase().includes('bullish') ? 'indicator-bullish' : 
                            part.toLowerCase().includes('bearish') ? 'indicator-bearish' : 'indicator-neutral';
            indicator = '<strong>MACD</strong>';
            // Try to extract MACD value if present
            const macdValueMatch = part.match(/([\d.]+)/);
            value = macdValueMatch ? `<span class="indicator-value ${macdClass}">${macdValueMatch[1]}</span>` : '';
            // Extract interpretation
            let macdInterpretation = part.replace('MACD', '').trim();
            if (!macdInterpretation || macdInterpretation.length < 10) {
                macdInterpretation = part.toLowerCase().includes('bullish') ? 
                    'Positive momentum; MACD is above signal line indicating bullish trend' :
                    part.toLowerCase().includes('bearish') ?
                    'Negative momentum; MACD is below signal line indicating bearish trend' :
                    'Neutral momentum; MACD and signal line are converging';
            }
            interpretation = `<span class="indicator-value ${macdClass}">${macdInterpretation}</span>`;
        }
        // Parse Volume
        else if (part.includes('Volume')) {
            const volumeClass = part.toLowerCase().includes('high') ? 'volume-high' : 
                              part.toLowerCase().includes('low') ? 'volume-low' : 'volume-normal';
            indicator = '<strong>Volume</strong>';
            // Try to extract volume multiplier if present (e.g., "0.47×")
            const volumeMatch = part.match(/([\d.]+)×/);
            value = volumeMatch ? `<span class="indicator-value ${volumeClass}">${volumeMatch[1]}×</span>` : '';
            // Extract interpretation
            let volumeInterpretation = part.replace('Volume', '').replace(/[\d.]+×/, '').trim();
            if (!volumeInterpretation || volumeInterpretation.length < 10) {
                volumeInterpretation = part.toLowerCase().includes('high') ? 
                    'High trading volume confirms strong market participation and trend strength' :
                    part.toLowerCase().includes('low') ?
                    'Low volume limits the strength of price moves; any breakout would need a subsequent surge in participation' :
                    'Normal volume levels indicate steady market activity';
            }
            interpretation = `<span class="indicator-value ${volumeClass}">${volumeInterpretation}</span>`;
        }
        
        // Add row if we have data
        if (indicator) {
            html += `<tr><td class="indicator-name">${indicator}</td><td class="indicator-value-cell">${value}</td><td class="indicator-interpretation">${interpretation}</td></tr>`;
        }
    });
    
    html += '</tbody></table>';
    html += '</div>';
    
    // Add summary sections
    html += '<div class="analysis-summary">';
    
    // Technical Context Section
    html += '<div class="summary-section">';
    html += '<h4 class="summary-title">📈 Technical Context</h4>';
    html += '<div class="summary-content">';
    
    const technicalPoints = [];
    
    // Extract trend information
    const trendMatch = reasoning.match(/Trend: ([^|]+)/);
    if (trendMatch) {
        const trend = trendMatch[1].trim().toLowerCase();
        if (trend.includes('bullish')) {
            technicalPoints.push('<strong>Momentum is positive:</strong> Indicators suggest upward price movement with bullish signals from multiple technical indicators.');
        } else if (trend.includes('bearish')) {
            technicalPoints.push('<strong>Momentum is negative:</strong> Indicators suggest downward price movement with bearish signals from multiple technical indicators.');
        } else {
            technicalPoints.push('<strong>Momentum is modest:</strong> Technical indicators show mixed signals, reflecting consolidation rather than a strong directional move.');
        }
    }
    
    // Extract RSI information
    const rsiMatch = reasoning.match(/RSI[^|]*/);
    if (rsiMatch) {
        const rsiText = rsiMatch[0].toLowerCase();
        if (rsiText.includes('neutral')) {
            technicalPoints.push('<strong>RSI Analysis:</strong> RSI is in neutral range, leaving room for further price movement without immediate reversal risk.');
        } else if (rsiText.includes('overbought')) {
            technicalPoints.push('<strong>RSI Analysis:</strong> RSI indicates overbought conditions, suggesting potential for price correction.');
        } else if (rsiText.includes('oversold')) {
            technicalPoints.push('<strong>RSI Analysis:</strong> RSI indicates oversold conditions, suggesting potential for price recovery.');
        }
    }
    
    // Extract MACD information
    const macdMatch = reasoning.match(/MACD[^|]*/);
    if (macdMatch) {
        const macdText = macdMatch[0].toLowerCase();
        if (macdText.includes('bullish')) {
            technicalPoints.push('<strong>MACD Signal:</strong> MACD is above signal line, indicating bullish momentum and potential upward continuation.');
        } else if (macdText.includes('bearish')) {
            technicalPoints.push('<strong>MACD Signal:</strong> MACD is below signal line, indicating bearish momentum and potential downward pressure.');
        }
    }
    
    // Extract Volume information
    const volumeMatch = reasoning.match(/Volume[^|]*/);
    if (volumeMatch) {
        const volumeText = volumeMatch[0].toLowerCase();
        if (volumeText.includes('low')) {
            technicalPoints.push('<strong>Volume Constraint:</strong> Low volume suggests price movements may be more susceptible to whipsaws; a sharp rally would likely need higher participation to confirm.');
        } else if (volumeText.includes('high')) {
            technicalPoints.push('<strong>Volume Confirmation:</strong> High volume validates the current price action and trend strength.');
        }
    }
    
    // Support & Resistance (generic)
    const priceMatch = reasoning.match(/Current price: ([^|]+)/);
    if (priceMatch) {
        technicalPoints.push('<strong>Support & Resistance:</strong> Monitor key price levels for potential support and resistance zones based on recent price action.');
    }
    
    if (technicalPoints.length > 0) {
        html += '<ul class="summary-list">';
        technicalPoints.forEach(point => {
            html += `<li>${point}</li>`;
        });
        html += '</ul>';
    } else {
        html += '<p>Technical analysis indicates current market conditions based on multiple indicators. Monitor key support and resistance levels for trading opportunities.</p>';
    }
    
    html += '</div>';
    html += '</div>';
    
    // Market Sentiment Section
    html += '<div class="summary-section">';
    html += '<h4 class="summary-title">💭 Market Sentiment & Catalysts</h4>';
    html += '<div class="summary-content">';
    
    const sentimentPoints = [];
    const trendSentiment = reasoning.match(/Trend: ([^|]+)/);
    if (trendSentiment) {
        const trend = trendSentiment[1].trim().toLowerCase();
        if (trend.includes('bullish')) {
            sentimentPoints.push('Market sentiment is <strong>positive</strong>, with technical indicators supporting upward momentum.');
        } else if (trend.includes('bearish')) {
            sentimentPoints.push('Market sentiment is <strong>cautious</strong>, with technical indicators suggesting downward pressure.');
        } else {
            sentimentPoints.push('Market sentiment is <strong>neutral</strong>, with mixed signals from technical indicators.');
        }
    }
    
    sentimentPoints.push('Monitor volume and momentum indicators for confirmation of trend direction. External catalysts such as news events, partnerships, or market developments can significantly impact price action.');
    
    if (sentimentPoints.length > 0) {
        html += '<ul class="summary-list">';
        sentimentPoints.forEach(point => {
            html += `<li>${point}</li>`;
        });
        html += '</ul>';
    } else {
        html += '<p>Market sentiment is influenced by technical indicators and current price action. Monitor volume and momentum for confirmation of trend direction.</p>';
    }
    
    html += '</div>';
    html += '</div>';
    
    html += '</div>'; // analysis-summary
    html += '</div>'; // reasoning-parsed
    
    return html;
}

// Format reasoning in condensed mode (for "All" view)
function formatReasoningCondensed(reasoning) {
    if (!reasoning) return '';
    
    const parts = reasoning.split('|').map(p => p.trim()).filter(p => p);
    let html = '<div class="reasoning-condensed">';
    
    // Extract key information only
    const keyInfo = [];
    
    // Get trend
    const trendMatch = reasoning.match(/Trend: ([^|]+)/);
    if (trendMatch) {
        const trend = trendMatch[1].trim();
        const trendLower = trend.toLowerCase();
        const trendClass = trendLower.includes('bullish') ? 'trend-bullish' : 
                         trendLower.includes('bearish') ? 'trend-bearish' : 'trend-neutral';
        keyInfo.push({
            label: 'Trend',
            value: `<span class="trend-badge ${trendClass}">${trend}</span>`
        });
    }
    
    // Get predicted price change
    const priceMatch = reasoning.match(/Predicted price: (.+?) \((.+?)\)/);
    if (priceMatch) {
        const change = priceMatch[2].trim();
        const isPositive = change.includes('increase') || change.includes('+');
        const changeClass = isPositive ? 'change-positive' : 'change-negative';
        keyInfo.push({
            label: 'Change',
            value: `<span class="${changeClass}">${change}</span>`
        });
    }
    
    // Get RSI value
    const rsiMatch = reasoning.match(/RSI \(([\d.]+)\)/);
    if (rsiMatch) {
        const rsiValue = rsiMatch[1];
        const rsiStatus = reasoning.includes('neutral') ? 'neutral' : 
                         reasoning.includes('overbought') ? 'overbought' : 
                         reasoning.includes('oversold') ? 'oversold' : 'neutral';
        keyInfo.push({
            label: 'RSI',
            value: `<span class="indicator-value rsi-${rsiStatus}">${rsiValue}</span>`
        });
    }
    
    // Get MACD status
    if (reasoning.includes('MACD')) {
        const macdClass = reasoning.toLowerCase().includes('bullish') ? 'indicator-bullish' : 
                         reasoning.toLowerCase().includes('bearish') ? 'indicator-bearish' : 'indicator-neutral';
        const macdStatus = reasoning.toLowerCase().includes('bullish') ? 'Bullish' : 
                          reasoning.toLowerCase().includes('bearish') ? 'Bearish' : 'Neutral';
        keyInfo.push({
            label: 'MACD',
            value: `<span class="indicator-value ${macdClass}">${macdStatus}</span>`
        });
    }
    
    // Display key info in a compact format
    if (keyInfo.length > 0) {
        html += '<div class="condensed-indicators">';
        keyInfo.forEach(info => {
            html += `<div class="condensed-item"><span class="condensed-label">${info.label}:</span> ${info.value}</div>`;
        });
        html += '</div>';
    } else {
        html += '<div class="condensed-summary">Technical analysis based on multiple indicators.</div>';
    }
    
    html += '</div>';
    return html;
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

// Get hours for timeframe
function getHoursForTimeframe(timeframe) {
    const hoursMap = {
        '1h': 1,
        '4h': 4,
        '24h': 24,
        '7d': 168,  // 7 * 24
        '30d': 720  // 30 * 24
    };
    return hoursMap[timeframe] || 24;
}

// Fetch and display price history
async function fetchHistory() {
    try {
        const hours = selectedTimeframe === 'all' ? 24 : getHoursForTimeframe(selectedTimeframe);
        const response = await fetch(`/api/history?hours=${hours}&limit=200`);
        if (!response.ok) throw new Error('Failed to fetch history');
        const result = await response.json();
        updatePriceChart(result.data, selectedTimeframe);
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// Update price chart
function updatePriceChart(data, timeframe) {
    if (!data || data.length === 0) return;
    
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Update chart title based on timeframe
    const chartTitle = document.querySelector('.chart-section h2');
    if (chartTitle) {
        if (timeframe === 'all') {
            chartTitle.textContent = 'Price History (Last 24 Hours)';
        } else {
            const timeframeLabels = {
                '1h': '1 Hour',
                '4h': '4 Hours',
                '24h': '24 Hours',
                '7d': '7 Days',
                '30d': '30 Days'
            };
            chartTitle.textContent = `Price History (Last ${timeframeLabels[timeframe] || timeframe})`;
        }
    }
    
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        // Use different format based on timeframe
        if (timeframe === '30d' || timeframe === '7d') {
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        } else {
            return date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
        }
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
        // Always fetch all analysis results to have complete data
        const response = await fetch('/api/analysis');
        if (!response.ok) throw new Error('Failed to fetch analysis');
        const result = await response.json();
        
        if (selectedTimeframe === 'all') {
            // Show all timeframes when "all" is selected
            updateAnalysisDisplay(result.by_timeframe || {});
        } else {
            // Show only selected timeframe
            const singleTimeframe = {};
            // Check both result.data and result.by_timeframe for the selected timeframe
            if (result.by_timeframe && result.by_timeframe[selectedTimeframe]) {
                singleTimeframe[selectedTimeframe] = result.by_timeframe[selectedTimeframe];
            } else if (result.data && result.data.length > 0) {
                // If by_timeframe doesn't have it, check data array
                const found = result.data.find(item => item.timeframe === selectedTimeframe);
                if (found) {
                    singleTimeframe[selectedTimeframe] = found;
                }
            }
            updateAnalysisDisplay(singleTimeframe);
        }
    } catch (error) {
        console.error('Error fetching analysis:', error);
    }
}

// Format timeframe label for display
function formatTimeframeLabel(timeframe) {
    const labels = {
        '1h': '1 Hour',
        '4h': '4 Hours',
        '24h': '24 Hours',
        '7d': '7 Days',
        '30d': '30 Days'
    };
    return labels[timeframe] || timeframe;
}

// Update analysis display
function updateAnalysisDisplay(analysisByTimeframe) {
    const grid = document.getElementById('analysis-grid');
    grid.innerHTML = '';
    
    // Update section subtitle based on selected timeframe
    const subtitle = document.querySelector('.analysis-section .section-subtitle');
    if (subtitle) {
        if (selectedTimeframe === 'all') {
            subtitle.textContent = 'Short-term (1h, 4h, 24h) and Long-term (7d, 30d) Forecasts';
        } else {
            const timeframeLabels = {
                '1h': '1 Hour',
                '4h': '4 Hours',
                '24h': '24 Hours',
                '7d': '7 Days',
                '30d': '30 Days'
            };
            subtitle.textContent = `${timeframeLabels[selectedTimeframe] || selectedTimeframe} Forecast`;
        }
    }
    
    // When "all" is selected, show all supported timeframes
    // When a specific timeframe is selected, show only that one
    const allSupportedTimeframes = ['1h', '4h', '24h', '7d', '30d'];
    const timeframes = selectedTimeframe === 'all' ? allSupportedTimeframes : [selectedTimeframe];
    
    // Display each timeframe
    timeframes.forEach(timeframe => {
        const analysis = analysisByTimeframe && analysisByTimeframe[timeframe] ? analysisByTimeframe[timeframe] : null;
        const card = document.createElement('div');
        card.className = 'analysis-card';
        
        if (analysis) {
            const trendClass = analysis.trend_direction === 'bullish' ? 'trend-bullish' :
                              analysis.trend_direction === 'bearish' ? 'trend-bearish' : 'trend-neutral';
            
            card.innerHTML = `
                <h3>${formatTimeframeLabel(timeframe)} Prediction</h3>
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
                <div class="analysis-item reasoning-item">
                    <div class="analysis-item-label">Reasoning</div>
                    <div class="reasoning-content">${formatReasoning(analysis.reasoning, selectedTimeframe === 'all')}</div>
                </div>
                ` : ''}
            `;
        } else {
            card.innerHTML = `
                <h3>${formatTimeframeLabel(timeframe)} Prediction</h3>
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

// Handle timeframe selection
function setupTimeframeSelector() {
    const buttons = document.querySelectorAll('.timeframe-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            buttons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Update selected timeframe
            selectedTimeframe = this.getAttribute('data-timeframe');
            // Refresh all data with new timeframe
            refreshAll();
        });
    });
}

// Initialize dashboard
async function init() {
    console.log('Initializing DogeAnalyze Dashboard...');
    
    // Setup timeframe selector
    setupTimeframeSelector();
    
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

