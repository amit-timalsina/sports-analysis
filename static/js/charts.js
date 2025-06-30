/**
 * Cricket Fitness Tracker - Analytics Charts
 * Comprehensive data visualization using Chart.js for mobile-first design
 */

class AnalyticsCharts {
    constructor() {
        this.charts = new Map(); // Store chart instances for cleanup
        this.colors = {
            primary: '#4f46e5',
            primaryLight: '#6366f1',
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            secondary: '#6b7280',
            background: '#f8fafc'
        };
        
        // Chart.js default configuration for mobile
        this.setupDefaultConfig();
    }

    setupDefaultConfig() {
        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif';
            Chart.defaults.font.size = 12;
            Chart.defaults.responsive = true;
            Chart.defaults.maintainAspectRatio = false;
            Chart.defaults.interaction.intersect = false;
            Chart.defaults.plugins.legend.position = 'bottom';
            Chart.defaults.plugins.legend.labels.usePointStyle = true;
            Chart.defaults.plugins.legend.labels.padding = 15;
        }
    }

    /**
     * Render fitness analytics charts
     */
    async renderFitnessAnalytics() {
        try {
            console.log('📊 Loading fitness analytics...');
            
            const response = await fetch('/api/analytics/fitness');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load fitness analytics');
            }

            const analytics = data.data.analytics;
            
            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Render multiple fitness charts
            this.renderFitnessFrequencyChart(analytics);
            this.renderEnergyLevelsChart(analytics);
            this.renderActivityTypesChart(analytics);
            this.renderFitnessProgressChart(analytics);
            
            console.log('✅ Fitness analytics rendered successfully');
            
        } catch (error) {
            console.error('❌ Failed to render fitness analytics:', error);
            this.showAnalyticsError('fitness', error.message);
        }
    }

    /**
     * Render cricket analytics charts
     */
    async renderCricketAnalytics() {
        try {
            console.log('🏏 Loading cricket analytics...');
            
            const response = await fetch('/api/analytics/cricket');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load cricket analytics');
            }

            const analytics = data.data.analytics;
            
            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Render multiple cricket charts
            this.renderBattingConfidenceChart(analytics);
            this.renderSkillsDevelopmentChart(analytics);
            this.renderMatchPerformanceChart(analytics);
            this.renderCoachingSessionsChart(analytics);
            
            console.log('✅ Cricket analytics rendered successfully');
            
        } catch (error) {
            console.error('❌ Failed to render cricket analytics:', error);
            this.showAnalyticsError('cricket', error.message);
        }
    }

    /**
     * Render combined analytics overview
     */
    async renderCombinedAnalytics() {
        try {
            console.log('🔄 Loading combined analytics...');
            
            const response = await fetch('/api/analytics/combined');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load combined analytics');
            }

            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Render correlation and overview charts
            this.renderFitnessVsCricketChart(data.data);
            this.renderWeeklyOverviewChart(data.data);
            
            console.log('✅ Combined analytics rendered successfully');
            
        } catch (error) {
            console.error('❌ Failed to render combined analytics:', error);
            this.showAnalyticsError('combined', error.message);
        }
    }

    clearAnalyticsSection() {
        // Destroy existing charts
        this.destroyAllCharts();
        
        // Clear chart containers
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const chartContainers = analyticsTab.querySelectorAll('.chart-container, .status.error');
            chartContainers.forEach(container => container.remove());
        }
    }

    /**
     * Fitness frequency chart - shows weekly consistency
     */
    renderFitnessFrequencyChart(analytics) {
        const canvas = this.getOrCreateCanvas('fitness-frequency-chart', '📈 Fitness Frequency');
        if (!canvas) return;

        const weeklyData = analytics.weekly_frequency || 0.5;
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Remaining'],
                datasets: [{
                    data: [weeklyData * 100, (1 - weeklyData) * 100],
                    backgroundColor: [this.colors.success, this.colors.background],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: `${Math.round(weeklyData * 100)}% Weekly Goal`,
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('fitness-frequency', chart);
    }

    /**
     * Energy levels trend chart
     */
    renderEnergyLevelsChart(analytics) {
        const canvas = this.getOrCreateCanvas('energy-levels-chart', '⚡ Energy Levels');
        if (!canvas) return;

        // Generate sample data based on analytics
        const energyData = this.generateTrendData(analytics.average_energy_level || 3.5, 7);
        
        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Energy Level',
                    data: energyData,
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.primary,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        grid: { color: '#f1f5f9' },
                        ticks: { stepSize: 1 }
                    },
                    x: { grid: { display: false } }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'This Week',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('energy-levels', chart);
    }

    /**
     * Activity types distribution
     */
    renderActivityTypesChart(analytics) {
        const canvas = this.getOrCreateCanvas('activity-types-chart', '🏃 Activity Types');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['Running', 'Strength', 'Cricket', 'Cardio'],
                datasets: [{
                    label: 'Sessions',
                    data: [8, 5, 6, 3],
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.secondary
                    ],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'This Month',
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: { display: false }
                }
            }
        });

        this.charts.set('activity-types', chart);
    }

    /**
     * Fitness progress over time
     */
    renderFitnessProgressChart(analytics) {
        const canvas = this.getOrCreateCanvas('fitness-progress-chart', 'Fitness Progress');
        if (!canvas) return;

        const progressData = this.generateProgressData(analytics);
        
        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Fitness Score',
                    data: progressData,
                    borderColor: this.colors.success,
                    backgroundColor: this.colors.success + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.success,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Progress',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('fitness-progress', chart);
    }

    /**
     * Batting confidence trend
     */
    renderBattingConfidenceChart(analytics) {
        const canvas = this.getOrCreateCanvas('batting-confidence-chart', '🏏 Batting Confidence');
        if (!canvas) return;

        const confidenceData = this.generateTrendData(analytics.average_self_assessment || 7, 7);
        
        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Confidence (1-10)',
                    data: confidenceData,
                    borderColor: this.colors.warning,
                    backgroundColor: this.colors.warning + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.warning,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        grid: { color: '#f1f5f9' },
                        ticks: { stepSize: 2 }
                    },
                    x: { grid: { display: false } }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'This Week',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('batting-confidence', chart);
    }

    /**
     * Skills development radar chart
     */
    renderSkillsDevelopmentChart(analytics) {
        const canvas = this.getOrCreateCanvas('skills-development-chart', '🎯 Skills Development');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'radar',
            data: {
                labels: ['Batting', 'Bowling', 'Fielding', 'Keeping', 'Mental', 'Fitness'],
                datasets: [{
                    label: 'Skill Level',
                    data: [8, 6, 7, 5, 8, 6],
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '30',
                    pointBackgroundColor: this.colors.primary,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 10,
                        grid: { color: '#f1f5f9' },
                        angleLines: { color: '#e2e8f0' },
                        pointLabels: { font: { size: 11 } }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Current Level',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('skills-development', chart);
    }

    /**
     * Match performance chart
     */
    renderMatchPerformanceChart(analytics) {
        const canvas = this.getOrCreateCanvas('match-performance-chart', 'Match Performance');
        if (!canvas) return;

        const battingAvg = analytics.batting_average || 25;
        const keepingRate = analytics.keeping_success_rate || 0.85;
        
        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['Batting Avg', 'Keeping %', 'Confidence', 'Match Wins'],
                datasets: [{
                    label: 'Performance',
                    data: [battingAvg, keepingRate * 100, 75, 60],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.primary,
                        this.colors.warning,
                        this.colors.secondary
                    ],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Match Performance Metrics',
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: { display: false }
                }
            }
        });

        this.charts.set('match-performance', chart);
    }

    /**
     * Coaching sessions distribution
     */
    renderCoachingSessionsChart(analytics) {
        const canvas = this.getOrCreateCanvas('coaching-sessions-chart', 'Coaching Sessions');
        if (!canvas) return;

        const sessionData = [
            analytics.total_coaching_sessions * 0.4 || 5,  // Batting
            analytics.total_coaching_sessions * 0.3 || 3,  // Keeping
            analytics.total_coaching_sessions * 0.2 || 2,  // Netting
            analytics.total_coaching_sessions * 0.1 || 1   // Other
        ];
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Batting', 'Keeping', 'Netting', 'Other'],
                datasets: [{
                    data: sessionData,
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.secondary
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Coaching Focus Areas',
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: {
                        position: 'bottom',
                        labels: { padding: 15 }
                    }
                }
            }
        });

        this.charts.set('coaching-sessions', chart);
    }

    /**
     * Fitness vs Cricket correlation
     */
    renderFitnessVsCricketChart(data) {
        const canvas = this.getOrCreateCanvas('fitness-vs-cricket-chart', '🔄 Fitness vs Cricket');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [
                    {
                        label: 'Fitness',
                        data: [1, 0, 1, 1, 0, 1, 0],
                        borderColor: this.colors.success,
                        backgroundColor: this.colors.success + '30',
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'Cricket',
                        data: [0, 1, 0, 1, 1, 0, 1],
                        borderColor: this.colors.primary,
                        backgroundColor: this.colors.primary + '30',
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: { color: '#f1f5f9' },
                        ticks: { 
                            stepSize: 1,
                            callback: function(value) {
                                return value === 1 ? 'Active' : 'Rest';
                            }
                        }
                    },
                    x: { grid: { display: false } }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Weekly Activity Pattern',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('weekly-overview', chart);
    }

    /**
     * Weekly overview chart
     */
    renderWeeklyOverviewChart(data) {
        const canvas = this.getOrCreateCanvas('weekly-overview-chart', 'Weekly Overview');
        if (!canvas) return;

        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [
                    {
                        label: 'Fitness',
                        data: [1, 0, 1, 1, 0, 1, 0],
                        borderColor: this.colors.success,
                        backgroundColor: this.colors.success + '30',
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'Cricket',
                        data: [0, 1, 0, 1, 1, 0, 1],
                        borderColor: this.colors.primary,
                        backgroundColor: this.colors.primary + '30',
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: { color: '#f1f5f9' },
                        ticks: { 
                            stepSize: 1,
                            callback: function(value) {
                                return value === 1 ? 'Active' : 'Rest';
                            }
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Weekly Activity Pattern',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('weekly-overview', chart);
    }

    // Utility methods
    getOrCreateCanvas(id, title) {
        let canvas = document.getElementById(id);
        
        if (!canvas) {
            const container = this.createChartContainer(id, title);
            const targetTab = document.getElementById('analytics-tab');
            
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(container);
                canvas = container.querySelector('canvas');
            }
        }
        
        return canvas;
    }

    createChartContainer(canvasId, title) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.style.marginBottom = 'var(--spacing-lg)';
        
        container.innerHTML = `
            <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">${title}</h3>
            <div style="position: relative; height: 250px;">
                <canvas id="${canvasId}"></canvas>
            </div>
        `;
        
        return container;
    }

    generateTrendData(average, days) {
        const data = [];
        for (let i = 0; i < days; i++) {
            const variation = (Math.random() - 0.5) * 2;
            data.push(Math.max(1, Math.min(10, average + variation)));
        }
        return data;
    }

    generateProgressData(analytics) {
        const baseScore = (analytics.average_energy_level || 3.5) * 15;
        return [
            baseScore,
            baseScore + 5,
            baseScore + 12,
            baseScore + 18
        ];
    }

    showAnalyticsError(type, message) {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'status error';
        errorContainer.style.margin = 'var(--spacing-lg) 0';
        errorContainer.innerHTML = `
            <strong>Analytics Error (${type}):</strong><br>
            ${message}<br>
            <small>Try refreshing or check if you have logged activities.</small>
        `;
        
        const targetTab = document.getElementById('analytics-tab');
        if (targetTab) {
            const section = targetTab.querySelector('.card');
            if (section) {
                section.appendChild(errorContainer);
            }
        }
    }

    destroyAllCharts() {
        this.charts.forEach((chart, key) => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts.clear();
    }

    resizeAllCharts() {
        this.charts.forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }
}

// Global instance
window.analyticsCharts = new AnalyticsCharts();

// Auto-resize charts on window resize
window.addEventListener('resize', () => {
    if (window.analyticsCharts) {
        window.analyticsCharts.resizeAllCharts();
    }
});

// Export for global access
window.AnalyticsCharts = AnalyticsCharts; 