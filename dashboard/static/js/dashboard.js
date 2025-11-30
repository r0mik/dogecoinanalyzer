// DogeAnalyze Dashboard JavaScript

let priceChart = null;
let accuracyChart = null;
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
    // Handle minute-based timeframes (e.g., '10m', '15m')
    if (timeframe.endsWith('m')) {
        const minutes = parseInt(timeframe.slice(0, -1));
        return minutes / 60.0;
    } else if (timeframe.endsWith('h')) {
        return parseInt(timeframe.slice(0, -1));
    } else if (timeframe.endsWith('d')) {
        return parseInt(timeframe.slice(0, -1)) * 24;
    }
    return 24; // Default fallback
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
        
        // Get available timeframes from API response
        const availableTimeframes = result.available_timeframes || null;
        
        // Update timeframe selector buttons if we have new data
        if (availableTimeframes && availableTimeframes.length > 0) {
            updateTimeframeSelector(availableTimeframes);
        }
        
        if (selectedTimeframe === 'all') {
            // Show all timeframes when "all" is selected
            updateAnalysisDisplay(result.by_timeframe || {}, availableTimeframes);
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
            updateAnalysisDisplay(singleTimeframe, availableTimeframes);
        }
    } catch (error) {
        console.error('Error fetching analysis:', error);
    }
}

// Format timeframe label for display
function formatTimeframeLabel(timeframe) {
    // Handle minute-based timeframes
    if (timeframe.endsWith('m')) {
        const minutes = parseInt(timeframe.slice(0, -1));
        return `${minutes} Minute${minutes > 1 ? 's' : ''}`;
    } else if (timeframe.endsWith('h')) {
        const hours = parseInt(timeframe.slice(0, -1));
        return `${hours} Hour${hours > 1 ? 's' : ''}`;
    } else if (timeframe.endsWith('d')) {
        const days = parseInt(timeframe.slice(0, -1));
        return `${days} Day${days > 1 ? 's' : ''}`;
    }
    
    // Fallback to predefined labels
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
function updateAnalysisDisplay(analysisByTimeframe, availableTimeframes = null) {
    const grid = document.getElementById('analysis-grid');
    grid.innerHTML = '';
    
    // Update section subtitle based on selected timeframe
    const subtitle = document.querySelector('.analysis-section .section-subtitle');
    if (subtitle) {
        if (selectedTimeframe === 'all') {
            subtitle.textContent = 'All Available Forecasts';
        } else {
            subtitle.textContent = `${formatTimeframeLabel(selectedTimeframe)} Forecast`;
        }
    }
    
    // When "all" is selected, show all available timeframes from database
    // When a specific timeframe is selected, show only that one
    let timeframes;
    if (selectedTimeframe === 'all') {
        // Use available timeframes from API if provided, otherwise fallback to standard ones
        if (availableTimeframes && availableTimeframes.length > 0) {
            // Sort timeframes: minutes first, then hours, then days
            timeframes = availableTimeframes.sort((a, b) => {
                const aVal = parseTimeframeValue(a);
                const bVal = parseTimeframeValue(b);
                return aVal - bVal;
            });
        } else {
            // Fallback to standard timeframes
            timeframes = ['1h', '4h', '24h', '7d', '30d'];
        }
    } else {
        timeframes = [selectedTimeframe];
    }
    
    // Helper function to parse timeframe value for sorting
    function parseTimeframeValue(tf) {
        if (tf.endsWith('m')) return parseInt(tf.slice(0, -1));
        if (tf.endsWith('h')) return parseInt(tf.slice(0, -1)) * 60;
        if (tf.endsWith('d')) return parseInt(tf.slice(0, -1)) * 60 * 24;
        return 0;
    }
    
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

// Fetch and display prediction accuracy
async function fetchAccuracy() {
    try {
        let url = '/api/accuracy?limit=50';
        if (selectedTimeframe !== 'all') {
            url += `&timeframe=${selectedTimeframe}`;
        }
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch accuracy data');
        const result = await response.json();
        updateAccuracyChart(result.data || [], result.stats || {});
    } catch (error) {
        console.error('Error fetching accuracy:', error);
    }
}

// Update accuracy chart
function updateAccuracyChart(data, stats) {
    // Update chart title based on timeframe
    const chartTitle = document.getElementById('accuracy-chart-title');
    if (chartTitle) {
        if (selectedTimeframe === 'all') {
            chartTitle.textContent = 'Prediction Accuracy (All Timeframes)';
        } else {
            const timeframeLabels = {
                '1h': '1 Hour',
                '4h': '4 Hours',
                '24h': '24 Hours',
                '7d': '7 Days',
                '30d': '30 Days'
            };
            chartTitle.textContent = `Prediction Accuracy (${timeframeLabels[selectedTimeframe] || selectedTimeframe})`;
        }
    }

    if (!data || data.length === 0) {
        // Show message if no data
        const chartContainer = document.querySelector('#accuracy-chart').parentElement;
        if (chartContainer && !chartContainer.querySelector('.no-data-message')) {
            const msg = document.createElement('div');
            msg.className = 'no-data-message';
            msg.textContent = 'No accuracy data available yet. Predictions need time to be validated.';
            msg.style.textAlign = 'center';
            msg.style.padding = '40px';
            msg.style.color = '#666';
            chartContainer.appendChild(msg);
        }
        return;
    }

    // Remove no-data message if it exists
    const noDataMsg = document.querySelector('.no-data-message');
    if (noDataMsg) noDataMsg.remove();

    // Update stats display
    updateAccuracyStats(stats);

    const ctx = document.getElementById('accuracy-chart').getContext('2d');
    
    // Prepare data
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    });
    
    const predictedPrices = data.map(item => parseFloat(item.predicted_price));
    const actualPrices = data.map(item => parseFloat(item.actual_price));
    const accuracyScores = data.map(item => parseFloat(item.accuracy));
    
    // Create datasets
    const datasets = [
        {
            label: 'Predicted Price',
            data: predictedPrices,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.4,
            yAxisID: 'y'
        },
        {
            label: 'Actual Price',
            data: actualPrices,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.4,
            yAxisID: 'y'
        },
        {
            label: 'Accuracy %',
            data: accuracyScores,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.4,
            yAxisID: 'y1',
            borderDash: [5, 5]
        }
    ];
    
    if (accuracyChart) {
        accuracyChart.data.labels = labels;
        accuracyChart.data.datasets = datasets;
        accuracyChart.update();
    } else {
        accuracyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                const item = data[index];
                                if (context.datasetIndex === 0) {
                                    return `Accuracy: ${item.accuracy}% | Error: ${item.error_percentage}%`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Price (USD)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        title: {
                            display: true,
                            text: 'Accuracy %'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
}

// Update accuracy statistics display
function updateAccuracyStats(stats) {
    const statsContainer = document.getElementById('accuracy-stats');
    if (!statsContainer) return;
    
    if (stats && stats.total_predictions > 0) {
        statsContainer.innerHTML = `
            <div class="accuracy-stat-card">
                <div class="accuracy-stat-label">Average Accuracy</div>
                <div class="accuracy-stat-value">${stats.average_accuracy}%</div>
            </div>
            <div class="accuracy-stat-card">
                <div class="accuracy-stat-label">Success Rate</div>
                <div class="accuracy-stat-value">${stats.success_rate}%</div>
            </div>
            <div class="accuracy-stat-card">
                <div class="accuracy-stat-label">Correct Predictions</div>
                <div class="accuracy-stat-value">${stats.correct_predictions}/${stats.total_predictions}</div>
            </div>
        `;
    } else {
        statsContainer.innerHTML = '<div class="accuracy-stat-card"><div class="accuracy-stat-label">No accuracy data available yet</div></div>';
    }
}

// Fetch and display analysis timeline
async function fetchAnalysisTimeline() {
    try {
        let url = '/api/analysis/timeline?limit=50';
        if (selectedTimeframe !== 'all') {
            url += `&timeframe=${selectedTimeframe}`;
        }
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch timeline');
        const result = await response.json();
        updateTimelineDisplay(result.timeline || {}, result.latest_analysis || {}, result.sync_time);
    } catch (error) {
        console.error('Error fetching timeline:', error);
    }
}

// Update timeline display
function updateTimelineDisplay(timeline, latestAnalysis, syncTime) {
    const container = document.getElementById('timeline-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Show sync time
    if (syncTime) {
        const syncInfo = document.createElement('div');
        syncInfo.className = 'timeline-sync-info';
        syncInfo.innerHTML = `
            <span class="sync-icon">🔄</span>
            <span>Last synced: ${formatDate(syncTime)}</span>
        `;
        container.appendChild(syncInfo);
    }
    
    // If no data
    if (Object.keys(timeline).length === 0) {
        const noData = document.createElement('div');
        noData.className = 'timeline-no-data';
        noData.textContent = 'No analysis timeline data available yet.';
        container.appendChild(noData);
        return;
    }
    
    // Display timeline for each timeframe
    // Get available timeframes from timeline data, or use defaults
    const availableTimeframes = Object.keys(timeline);
    const timeframes = selectedTimeframe === 'all' ? 
        (availableTimeframes.length > 0 ? availableTimeframes.sort((a, b) => {
            const aVal = parseTimeframeValue(a);
            const bVal = parseTimeframeValue(b);
            return aVal - bVal;
        }) : ['1h', '4h', '24h', '7d', '30d']) : 
        [selectedTimeframe];
    
    timeframes.forEach(timeframe => {
        const timeframeData = timeline[timeframe] || [];
        if (timeframeData.length === 0) return;
        
        const timeframeSection = document.createElement('div');
        timeframeSection.className = 'timeline-timeframe-section';
        
        const header = document.createElement('div');
        header.className = 'timeline-header';
        header.innerHTML = `
            <h3>${formatTimeframeLabel(timeframe)}</h3>
            <span class="timeline-count">${timeframeData.length} analyses</span>
            ${latestAnalysis[timeframe] ? `<span class="timeline-latest">Latest: ${formatDate(latestAnalysis[timeframe])}</span>` : ''}
        `;
        timeframeSection.appendChild(header);
        
        const timelineList = document.createElement('div');
        timelineList.className = 'timeline-list';
        
        // Show recent analyses (last 10)
        timeframeData.slice(0, 10).forEach((item, index) => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';
            
            const timeAgo = getTimeAgo(item.timestamp);
            const trendClass = item.trend_direction === 'bullish' ? 'trend-bullish' : 
                             item.trend_direction === 'bearish' ? 'trend-bearish' : 'trend-neutral';
            
            // Build validation info
            let validationInfo = '';
            if (item.validation_time) {
                const validationAgo = getTimeAgo(item.validation_time);
                const isFuture = new Date(item.validation_time) > new Date();
                
                if (item.is_validated && item.actual_price !== null && item.actual_price !== undefined) {
                    // Prediction has been validated
                    const accuracyClass = item.accuracy >= 95 ? 'accuracy-excellent' : 
                                       item.accuracy >= 85 ? 'accuracy-good' : 
                                       item.accuracy >= 70 ? 'accuracy-fair' : 'accuracy-poor';
                    const priceDiff = item.actual_price - item.predicted_price;
                    const diffClass = priceDiff >= 0 ? 'change-positive' : 'change-negative';
                    const diffSign = priceDiff >= 0 ? '+' : '';
                    
                    validationInfo = `
                        <div class="timeline-validation validated">
                            <div class="validation-label">Validated at: ${formatDate(item.validation_time)}</div>
                            <div class="validation-prices">
                                <span class="validation-predicted">Predicted: ${formatCurrency(item.predicted_price)}</span>
                                <span class="validation-actual">Actual: ${formatCurrency(item.actual_price)}</span>
                                <span class="validation-diff ${diffClass}">${diffSign}${formatCurrency(Math.abs(priceDiff))}</span>
                            </div>
                            <div class="validation-accuracy">
                                <span class="accuracy-badge ${accuracyClass}">Accuracy: ${item.accuracy}%</span>
                                <span class="error-percentage">Error: ${item.error_percentage}%</span>
                            </div>
                        </div>
                    `;
                } else if (isFuture) {
                    // Prediction is still pending
                    validationInfo = `
                        <div class="timeline-validation pending">
                            <div class="validation-label">Expected validation: ${formatDate(item.validation_time)} <span class="time-ago">(${validationAgo})</span></div>
                            <div class="validation-status">⏳ Pending validation</div>
                        </div>
                    `;
                } else {
                    // Validation time passed but no actual price found
                    validationInfo = `
                        <div class="timeline-validation no-data">
                            <div class="validation-label">Validation time: ${formatDate(item.validation_time)} <span class="time-ago">(${validationAgo})</span></div>
                            <div class="validation-status">No price data available at validation time</div>
                        </div>
                    `;
                }
            }
            
            timelineItem.innerHTML = `
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <div class="timeline-header-row">
                        <div class="timeline-time">Prediction created: ${formatDate(item.timestamp)} <span class="time-ago">(${timeAgo})</span></div>
                    </div>
                    <div class="timeline-details">
                        <div class="timeline-prediction-info">
                            <span class="timeline-price">Predicted: ${formatCurrency(item.predicted_price)}</span>
                            <span class="timeline-trend ${trendClass}">${item.trend_direction || 'N/A'}</span>
                            <span class="timeline-confidence">${item.confidence_score || 0}% confidence</span>
                        </div>
                        ${validationInfo}
                    </div>
                </div>
            `;
            timelineList.appendChild(timelineItem);
        });
        
        timeframeSection.appendChild(timelineList);
        container.appendChild(timeframeSection);
    });
}

// Get time ago string
function getTimeAgo(timestamp) {
    if (!timestamp) return 'unknown';
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// Refresh all data
async function refreshAll() {
    await Promise.all([
        fetchCurrentData(),
        fetchHistory(),
        fetchAnalysis(),
        fetchStatus(),
        fetchStats(),
        fetchAccuracy(),
        fetchAnalysisTimeline()
    ]);
}

// Update timeframe selector buttons dynamically based on available timeframes
function updateTimeframeSelector(availableTimeframes) {
    const buttonsContainer = document.querySelector('.timeframe-buttons');
    if (!buttonsContainer) return;
    
    // Keep "All" button, remove others
    const allButton = buttonsContainer.querySelector('[data-timeframe="all"]');
    buttonsContainer.innerHTML = '';
    if (allButton) {
        buttonsContainer.appendChild(allButton);
    }
    
    // Add buttons for available timeframes
    if (availableTimeframes && availableTimeframes.length > 0) {
        // Sort timeframes: minutes first, then hours, then days
        const sortedTimeframes = [...availableTimeframes].sort((a, b) => {
            const aVal = parseTimeframeValue(a);
            const bVal = parseTimeframeValue(b);
            return aVal - bVal;
        });
        
        sortedTimeframes.forEach(tf => {
            const button = document.createElement('button');
            button.className = 'timeframe-btn';
            button.setAttribute('data-timeframe', tf);
            button.textContent = formatTimeframeLabel(tf);
            buttonsContainer.appendChild(button);
        });
    } else {
        // Fallback to standard timeframes if none available
        const standardTimeframes = ['1h', '4h', '24h', '7d', '30d'];
        standardTimeframes.forEach(tf => {
            const button = document.createElement('button');
            button.className = 'timeframe-btn';
            button.setAttribute('data-timeframe', tf);
            button.textContent = formatTimeframeLabel(tf);
            buttonsContainer.appendChild(button);
        });
    }
    
    // Re-attach event listeners
    setupTimeframeSelector();
}

// Helper function to parse timeframe value for sorting
function parseTimeframeValue(tf) {
    if (tf.endsWith('m')) return parseInt(tf.slice(0, -1));
    if (tf.endsWith('h')) return parseInt(tf.slice(0, -1)) * 60;
    if (tf.endsWith('d')) return parseInt(tf.slice(0, -1)) * 60 * 24;
    return 0;
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

