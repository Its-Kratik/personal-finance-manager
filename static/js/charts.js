/**
 * Personal Finance Manager Pro - Charts Module
 * ============================================
 * 
 * Chart rendering and management using Chart.js
 * Handles all financial data visualizations
 * 
 * Version: 1.0.0
 */

let chartInstances = {};

/**
 * Initialize all charts
 */
export function initCharts() {
    // Initialize Chart.js with global configurations
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#666';
        Chart.defaults.elements.line.borderWidth = 2;
        Chart.defaults.elements.point.radius = 4;
        Chart.defaults.elements.point.hoverRadius = 6;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        Chart.defaults.plugins.tooltip.titleColor = 'white';
        Chart.defaults.plugins.tooltip.bodyColor = 'white';
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
    }
}

/**
 * Update dashboard charts with new data
 */
export async function updateDashboardCharts(data) {
    if (!data) return;

    try {
        // Update monthly trends chart
        if (data.monthly_trends) {
            await renderMonthlyTrendsChart(data.monthly_trends);
        }

        // Update expense breakdown chart
        if (data.expense_breakdown) {
            await renderExpenseBreakdownChart(data.expense_breakdown);
        }

        // Update sparklines
        if (data.dashboard_stats) {
            updateSparklines(data.dashboard_stats);
        }

        console.log('Dashboard charts updated successfully');
    } catch (error) {
        console.error('Failed to update dashboard charts:', error);
    }
}

/**
 * Render monthly trends chart
 */
async function renderMonthlyTrendsChart(data) {
    const canvas = document.getElementById('monthly-trends-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (chartInstances.monthlyTrends) {
        chartInstances.monthlyTrends.destroy();
    }

    const chartData = {
        labels: data.months || [],
        datasets: [
            {
                label: 'Income',
                data: data.income || [],
                backgroundColor: 'rgba(56, 178, 123, 0.1)',
                borderColor: '#38B27B',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#38B27B',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            },
            {
                label: 'Expenses',
                data: data.expenses || [],
                backgroundColor: 'rgba(250, 115, 115, 0.1)',
                borderColor: '#FA7373',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#FA7373',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }
        ]
    };

    const config = {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: false
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: false
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.9)',
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = '$' + context.parsed.y.toLocaleString();
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            elements: {
                point: {
                    radius: 4,
                    hoverRadius: 8,
                    borderWidth: 2
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    chartInstances.monthlyTrends = new Chart(ctx, config);
}

/**
 * Render expense breakdown pie chart
 */
async function renderExpenseBreakdownChart(data) {
    const canvas = document.getElementById('expense-breakdown-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (chartInstances.expenseBreakdown) {
        chartInstances.expenseBreakdown.destroy();
    }

    if (!data || data.length === 0) {
        // Show no data message
        ctx.font = '16px Inter';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.textAlign = 'center';
        ctx.fillText('No expense data available', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Generate colors for categories
    const colors = generateColors(data.length);
    
    const chartData = {
        labels: data.map(item => item.category),
        datasets: [{
            data: data.map(item => item.amount),
            backgroundColor: colors,
            borderColor: colors.map(color => color.replace('0.8', '1')),
            borderWidth: 2,
            hoverBorderWidth: 3,
            hoverOffset: 10
        }]
    };

    const config = {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.9)',
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        generateLabels: function(chart) {
                            const original = Chart.defaults.plugins.legend.labels.generateLabels;
                            const labels = original.call(this, chart);
                            
                            labels.forEach((label, index) => {
                                const value = chart.data.datasets[0].data[index];
                                label.text += ` ($${value.toLocaleString()})`;
                            });
                            
                            return labels;
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = '$' + context.parsed.toLocaleString();
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            },
            onHover: (event, activeElements) => {
                canvas.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
            }
        }
    };

    chartInstances.expenseBreakdown = new Chart(ctx, config);
}

/**
 * Update sparkline charts
 */
function updateSparklines(data) {
    updateSparkline('income-sparkline', data.income_trend || [], '#38B27B');
    updateSparkline('expense-sparkline', data.expense_trend || [], '#FA7373');
}

/**
 * Update individual sparkline
 */
function updateSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Calculate points
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    
    const points = data.map((value, index) => ({
        x: (index / (data.length - 1)) * width,
        y: height - ((value - min) / range) * height
    }));
    
    // Draw line
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    points.forEach((point, index) => {
        if (index === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    });
    
    ctx.stroke();
    
    // Draw area under curve
    ctx.fillStyle = color.replace('1)', '0.1)');
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fill();
    
    // Draw points
    ctx.fillStyle = color;
    points.forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2, 0, 2 * Math.PI);
        ctx.fill();
    });
}

/**
 * Render reports trends chart
 */
export async function renderReportsTrendsChart(data, canvasId = 'reports-trends-chart') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    const chartKey = `reports_${canvasId}`;
    if (chartInstances[chartKey]) {
        chartInstances[chartKey].destroy();
    }

    const chartData = {
        labels: data.months || [],
        datasets: [
            {
                label: 'Income',
                data: data.income || [],
                backgroundColor: 'rgba(56, 178, 123, 0.1)',
                borderColor: '#38B27B',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Expenses',
                data: data.expenses || [],
                backgroundColor: 'rgba(250, 115, 115, 0.1)',
                borderColor: '#FA7373',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Net Balance',
                data: data.balance || [],
                backgroundColor: 'rgba(79, 138, 139, 0.1)',
                borderColor: '#4F8A8B',
                fill: false,
                tension: 0.4,
                borderDash: [5, 5]
            }
        ]
    };

    const config = {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.9)',
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = '$' + context.parsed.y.toLocaleString();
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    chartInstances[chartKey] = new Chart(ctx, config);
}

/**
 * Render category breakdown chart for reports
 */
export async function renderCategoryChart(data, canvasId = 'reports-category-chart') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    const chartKey = `category_${canvasId}`;
    if (chartInstances[chartKey]) {
        chartInstances[chartKey].destroy();
    }

    if (!data || data.length === 0) {
        ctx.font = '16px Inter';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
        return;
    }

    const colors = generateColors(data.length);
    
    const chartData = {
        labels: data.map(item => item.category),
        datasets: [{
            data: data.map(item => item.amount),
            backgroundColor: colors,
            borderColor: colors.map(color => color.replace('0.8', '1')),
            borderWidth: 2
        }]
    };

    const config = {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const value = '$' + context.parsed.y.toLocaleString();
                            return `Amount: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        maxRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    chartInstances[chartKey] = new Chart(ctx, config);
}

/**
 * Generate color palette for charts
 */
function generateColors(count) {
    const baseColors = [
        'rgba(79, 138, 139, 0.8)',
        'rgba(250, 115, 115, 0.8)',
        'rgba(56, 178, 123, 0.8)',
        'rgba(255, 182, 0, 0.8)',
        'rgba(171, 131, 161, 0.8)',
        'rgba(106, 183, 197, 0.8)',
        'rgba(255, 149, 0, 0.8)',
        'rgba(52, 199, 89, 0.8)',
        'rgba(88, 86, 214, 0.8)',
        'rgba(255, 59, 48, 0.8)'
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        if (i < baseColors.length) {
            colors.push(baseColors[i]);
        } else {
            // Generate additional colors
            const hue = (i * 137.508) % 360; // Golden angle approximation
            colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
        }
    }
    
    return colors;
}

/**
 * Render generic chart
 */
export function renderChart(canvasId, type, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                cornerRadius: 8
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    };

    const config = {
        type,
        data,
        options: { ...defaultOptions, ...options }
    };

    chartInstances[canvasId] = new Chart(ctx, config);
    return chartInstances[canvasId];
}

/**
 * Destroy chart
 */
export function destroyChart(canvasId) {
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
        delete chartInstances[canvasId];
    }
}

/**
 * Resize all charts
 */
export function resizeCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

/**
 * Export chart as image
 */
export function exportChart(canvasId, filename = 'chart.png') {
    const chart = chartInstances[canvasId];
    if (!chart) return;

    const link = document.createElement('a');
    link.download = filename;
    link.href = chart.toBase64Image();
    link.click();
}

// Initialize charts when module is loaded
document.addEventListener('DOMContentLoaded', initCharts);

// Handle window resize
window.addEventListener('resize', resizeCharts);
