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
     * Energy levels trend chart - using real data only
     */
    renderEnergyLevelsChart(analytics) {
        const canvas = this.getOrCreateCanvas('energy-levels-chart', '⚡ Energy Levels');
        if (!canvas) return;

        // Only show if we have real data
        if (!analytics.improvement_trends || Object.keys(analytics.improvement_trends).length === 0) {
            const noDataContainer = this.createChartContainer('energy-levels-no-data', '⚡ Energy Levels');
            noDataContainer.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">⚡ Energy Levels</h3>
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <p>No energy level data yet</p>
                    <p style="font-size: 0.9rem;">Log fitness activities to see your energy trends</p>
                </div>
            `;
            const targetTab = document.getElementById('analytics-tab');
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(noDataContainer);
            }
            return;
        }
        
        // Use actual average energy level only
        const avgEnergy = analytics.average_energy_level || 0;
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Current Level', 'Remaining'],
                datasets: [{
                    data: [avgEnergy, 5 - avgEnergy],
                    backgroundColor: [this.colors.primary, this.colors.background],
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
                        text: `${avgEnergy.toFixed(1)}/5 Average Energy`,
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('energy-levels', chart);
    }

    /**
     * Activity types distribution - using real data only
     */
    renderActivityTypesChart(analytics) {
        const canvas = this.getOrCreateCanvas('activity-types-chart', '🏃 Activity Types');
        if (!canvas) return;

        // Show actual activity type if available
        if (!analytics.most_common_activity || analytics.total_sessions === 0) {
            const noDataContainer = this.createChartContainer('activity-types-no-data', '🏃 Activity Types');
            noDataContainer.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">🏃 Activity Types</h3>
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🏃</div>
                    <p>No activity data yet</p>
                    <p style="font-size: 0.9rem;">Log fitness activities to see your activity breakdown</p>
                </div>
            `;
            const targetTab = document.getElementById('analytics-tab');
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(noDataContainer);
            }
            return;
        }

        // Show simple summary of actual data
        const totalSessions = analytics.total_sessions || 0;
        const mostCommon = analytics.most_common_activity || 'unknown';
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Total Sessions'],
                datasets: [{
                    data: [100],
                    backgroundColor: [this.colors.primary],
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
                        text: `${totalSessions} Total Sessions`,
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('activity-types', chart);
        
        // Add text summary below chart
        const chartContainer = canvas.closest('.chart-container');
        if (chartContainer) {
            const summaryDiv = document.createElement('div');
            summaryDiv.style.cssText = 'text-align: center; margin-top: 10px; color: var(--text-secondary);';
            summaryDiv.innerHTML = `
                <p><strong>Most Common:</strong> ${mostCommon.replace('_', ' ')}</p>
                <p><strong>Total Sessions:</strong> ${totalSessions}</p>
            `;
            chartContainer.appendChild(summaryDiv);
        }
    }



    /**
     * Batting confidence - using real data only
     */
    renderBattingConfidenceChart(analytics) {
        const canvas = this.getOrCreateCanvas('batting-confidence-chart', '🏏 Batting Confidence');
        if (!canvas) return;

        // Only show if we have real confidence data
        if (!analytics.average_self_assessment || analytics.total_coaching_sessions === 0) {
            const noDataContainer = this.createChartContainer('batting-confidence-no-data', '🏏 Batting Confidence');
            noDataContainer.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">🏏 Batting Confidence</h3>
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🏏</div>
                    <p>No confidence data yet</p>
                    <p style="font-size: 0.9rem;">Log cricket coaching sessions to track confidence</p>
                </div>
            `;
            const targetTab = document.getElementById('analytics-tab');
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(noDataContainer);
            }
            return;
        }
        
        const avgConfidence = analytics.average_self_assessment || 0;
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Current Level', 'Remaining'],
                datasets: [{
                    data: [avgConfidence, 10 - avgConfidence],
                    backgroundColor: [this.colors.warning, this.colors.background],
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
                        text: `${avgConfidence.toFixed(1)}/10 Avg Confidence`,
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('batting-confidence', chart);
    }

    /**
     * Skills development - simplified for real data
     */
    renderSkillsDevelopmentChart(analytics) {
        const canvas = this.getOrCreateCanvas('skills-development-chart', '🎯 Skills Development');
        if (!canvas) return;

        // Show only if we have meaningful data
        if (!analytics.most_practiced_skill || analytics.total_coaching_sessions === 0) {
            const noDataContainer = this.createChartContainer('skills-development-no-data', '🎯 Skills Development');
            noDataContainer.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">🎯 Skills Development</h3>
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                    <p>No skills data yet</p>
                    <p style="font-size: 0.9rem;">Log cricket coaching sessions to track skill development</p>
                </div>
            `;
            const targetTab = document.getElementById('analytics-tab');
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(noDataContainer);
            }
            return;
        }

        // Show summary of actual data
        const practiceCount = analytics.total_coaching_sessions || 0;
        const mostPracticed = analytics.most_practiced_skill || 'unknown';
        
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Training Sessions'],
                datasets: [{
                    data: [100],
                    backgroundColor: [this.colors.primary],
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
                        text: `${practiceCount} Training Sessions`,
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });

        this.charts.set('skills-development', chart);
        
        // Add skills summary
        const chartContainer = canvas.closest('.chart-container');
        if (chartContainer) {
            const summaryDiv = document.createElement('div');
            summaryDiv.style.cssText = 'text-align: center; margin-top: 10px; color: var(--text-secondary);';
            summaryDiv.innerHTML = `
                <p><strong>Most Practiced:</strong> ${mostPracticed.replace('_', ' ')}</p>
                <p><strong>Total Sessions:</strong> ${practiceCount}</p>
            `;
            chartContainer.appendChild(summaryDiv);
        }
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

        // Show correlation data if available
        const fitnessAnalytics = data.fitness_analytics || {};
        const cricketAnalytics = data.cricket_analytics || {};
        const correlations = data.correlations || {};
        
        if (!fitnessAnalytics.total_sessions && !cricketAnalytics.total_coaching_sessions) {
            const noDataContainer = this.createChartContainer('correlation-no-data', '🔄 Fitness vs Cricket');
            noDataContainer.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">🔄 Fitness vs Cricket</h3>
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔄</div>
                    <p>No correlation data yet</p>
                    <p style="font-size: 0.9rem;">Log both fitness and cricket activities to see correlations</p>
                </div>
            `;
            const targetTab = document.getElementById('analytics-tab');
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(noDataContainer);
            }
            return;
        }

        // Show actual correlation data
        const fitnessCount = fitnessAnalytics.total_sessions || 0;
        const cricketCount = cricketAnalytics.total_coaching_sessions || 0;
        
        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['Fitness Sessions', 'Cricket Sessions'],
                datasets: [{
                    label: 'Sessions',
                    data: [fitnessCount, cricketCount],
                    backgroundColor: [this.colors.success, this.colors.primary],
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
                        text: 'Activity Comparison',
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: { display: false }
                }
            }
        });

        this.charts.set('weekly-overview', chart);
        
        // Show correlation info if available
        if (Object.keys(correlations).length > 0) {
            const chartContainer = canvas.closest('.chart-container');
            if (chartContainer) {
                const corrDiv = document.createElement('div');
                corrDiv.style.cssText = 'text-align: center; margin-top: 10px; color: var(--text-secondary);';
                const corrValue = correlations.fitness_frequency_vs_cricket_confidence || 0;
                corrDiv.innerHTML = `
                    <p><strong>Correlation Score:</strong> ${(corrValue * 100).toFixed(0)}%</p>
                    <p style="font-size: 0.9rem;">Fitness consistency vs cricket confidence</p>
                `;
                chartContainer.appendChild(corrDiv);
            }
        }
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