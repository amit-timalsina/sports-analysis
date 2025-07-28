/**
 * Cricket Fitness Tracker - Analytics Charts
 * Rewritten from first principles for robust Chart.js management
 */

class AnalyticsCharts {
    constructor() {
        // Chart registry with proper lifecycle management
        this.chartRegistry = new Map();
        this.canvasRegistry = new Map();
        this.isRendering = false;
        
        // Color scheme
        this.colors = {
            primary: '#4f46e5',
            primaryLight: '#6366f1',
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            secondary: '#6b7280',
            background: '#f8fafc',
            chartColors: [
                '#4f46e5', '#10b981', '#f59e0b', '#ef4444', 
                '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
            ]
        };
        
        // Initialize Chart.js with safety measures
        this.initChartJS();
        
        // Setup global error handlers
        this.setupErrorHandlers();
    }

    /**
     * Initialize Chart.js with safety configurations
     */
    initChartJS() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js not loaded');
            return;
        }

        // Disable animations to prevent conflicts
        Chart.defaults.animation = false;
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.plugins.legend.position = 'bottom';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 15;
        Chart.defaults.elements.point.radius = 3;
        Chart.defaults.elements.line.borderWidth = 2;
        Chart.defaults.datasets.bar.maxBarThickness = 50;

        console.log('✅ Chart.js initialized with safety configurations');
    }

    /**
     * Setup global error handlers
     */
    setupErrorHandlers() {
        // Global error handler for Chart.js
        window.addEventListener('error', (event) => {
            if (event.error && event.error.message && event.error.message.includes('Canvas is already in use')) {
                console.warn('Canvas reuse error detected, cleaning up...');
                this.emergencyCleanup();
            }
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            if (event.reason && event.reason.message && event.reason.message.includes('Canvas')) {
                console.warn('Chart.js promise rejection:', event.reason);
                event.preventDefault();
            }
        });
    }

    /**
     * Emergency cleanup when canvas errors occur
     */
    emergencyCleanup() {
        console.log('🚨 Emergency chart cleanup initiated');
        
        // Force destroy all Chart.js instances
        if (window.Chart && window.Chart.instances) {
            Object.keys(window.Chart.instances).forEach(id => {
                try {
                    const chart = window.Chart.instances[id];
                    if (chart && typeof chart.destroy === 'function') {
                        chart.destroy();
                    }
                } catch (error) {
                    console.warn('Error in emergency cleanup:', error);
                }
            });
            window.Chart.instances = {};
        }

        // Clear our registry
        this.chartRegistry.clear();
        this.canvasRegistry.clear();

        // Clear all canvas elements
        document.querySelectorAll('canvas').forEach(canvas => {
            try {
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            } catch (error) {
                console.warn('Error clearing canvas:', error);
            }
        });
    }

    /**
     * Create a new chart with proper lifecycle management
     */
    createChart(canvasId, config) {
        // Ensure we don't have conflicts
        this.destroyChart(canvasId);
        
        const canvas = this.getOrCreateCanvas(canvasId);
        if (!canvas) {
            console.error(`Failed to get canvas for ${canvasId}`);
            return null;
        }

        try {
            // Create new chart
            const chart = new Chart(canvas, {
                ...config,
                options: {
                    ...config.options,
                    animation: false, // Disable animations to prevent conflicts
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            // Register the chart
            this.chartRegistry.set(canvasId, chart);
            this.canvasRegistry.set(canvasId, canvas);

            console.log(`✅ Chart created: ${canvasId}`);
            return chart;
        } catch (error) {
            console.error(`Failed to create chart ${canvasId}:`, error);
            this.destroyChart(canvasId);
            return null;
        }
    }

    /**
     * Destroy a specific chart
     */
    destroyChart(canvasId) {
        const chart = this.chartRegistry.get(canvasId);
        if (chart) {
            try {
                chart.destroy();
                console.log(`🗑️ Chart destroyed: ${canvasId}`);
            } catch (error) {
                console.warn(`Error destroying chart ${canvasId}:`, error);
            }
            this.chartRegistry.delete(canvasId);
            this.canvasRegistry.delete(canvasId);
        }
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        console.log('🧹 Destroying all charts...');
        
        // Destroy our tracked charts
        this.chartRegistry.forEach((chart, canvasId) => {
            this.destroyChart(canvasId);
        });

        // Force destroy any remaining Chart.js instances
        if (window.Chart && window.Chart.instances) {
            Object.keys(window.Chart.instances).forEach(id => {
                try {
                    const chart = window.Chart.instances[id];
                    if (chart && typeof chart.destroy === 'function') {
                        chart.destroy();
                    }
                } catch (error) {
                    console.warn(`Error destroying Chart.js instance ${id}:`, error);
                }
            });
            window.Chart.instances = {};
        }

        console.log('✅ All charts destroyed');
    }

    /**
     * Get or create canvas element
     */
    getOrCreateCanvas(canvasId) {
        let canvas = document.getElementById(canvasId);
        
        if (!canvas) {
            // Create new canvas container
            const container = this.createChartContainer(canvasId);
            const analyticsTab = document.getElementById('analytics-tab');
            
            if (analyticsTab) {
                const section = analyticsTab.querySelector('.card') || analyticsTab;
                section.appendChild(container);
                canvas = container.querySelector('canvas');
            }
        }

        if (canvas) {
            // Clear any existing content
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }

        return canvas;
    }

    /**
     * Create chart container
     */
    createChartContainer(canvasId) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.style.cssText = `
            margin-bottom: var(--spacing-lg);
            background: white;
            border-radius: 12px;
            padding: var(--spacing-md);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        `;
        
        const title = this.getChartTitle(canvasId);
        container.innerHTML = `
            <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color); font-size: 1.1rem;">
                ${title}
            </h3>
            <div style="position: relative; height: 250px;">
                <canvas id="${canvasId}"></canvas>
            </div>
        `;
        
        return container;
    }

    /**
     * Get chart title from canvas ID
     */
    getChartTitle(canvasId) {
        const titles = {
            'workout-frequency-chart': '📊 Workout Frequency',
            'weekly-progress-chart': '📈 Weekly Progress',
            'exercise-types-chart': '🏃 Exercise Types',
            'intensity-distribution-chart': '⚡ Intensity Distribution',
            'calories-burned-chart': '🔥 Calories Burned',
            'workout-metrics-chart': '📋 Workout Metrics',
            'batting-confidence-chart': '🏏 Batting Confidence',
            'skills-development-chart': '🎯 Skills Development',
            'match-performance-chart': '🏆 Match Performance',
            'coaching-sessions-chart': '👨‍🏫 Coaching Sessions',
            'fitness-vs-cricket-chart': '🔄 Fitness vs Cricket'
        };
        return titles[canvasId] || 'Chart';
    }

    /**
     * Clear analytics section
     */
    clearAnalyticsSection() {
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const section = analyticsTab.querySelector('.card');
            if (section) {
                // Remove all chart containers
                const chartContainers = section.querySelectorAll('.chart-container');
                chartContainers.forEach(container => container.remove());
                
                // Remove error messages
                const errorMessages = section.querySelectorAll('.status.error');
                errorMessages.forEach(error => error.remove());
            }
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        // First hide any existing loading indicator
        this.hideLoadingIndicator();
        
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'charts-loading';
            loadingDiv.style.cssText = `
                text-align: center;
                padding: var(--spacing-xl);
                color: var(--text-secondary);
                background: rgba(255, 255, 255, 0.9);
                border-radius: var(--border-radius);
                margin: var(--spacing-lg) 0;
                box-shadow: var(--shadow-md);
            `;
            loadingDiv.innerHTML = `
                <div class="loading" style="margin: 0 auto var(--spacing-md) auto;"></div>
                <p style="margin: 0; font-weight: 500;">Loading analytics...</p>
            `;
            
            const section = analyticsTab.querySelector('.card') || analyticsTab;
            section.appendChild(loadingDiv);
            
            console.log('📊 Loading indicator shown');
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const loadingDiv = document.getElementById('charts-loading');
        if (loadingDiv) {
            loadingDiv.remove();
            console.log('📊 Loading indicator hidden');
        }
    }

    /**
     * Render fitness analytics
     */
    async renderFitnessAnalytics() {
        if (this.isRendering) {
            console.log('⚠️ Already rendering, skipping...');
            return;
        }

        this.isRendering = true;
        this.clearAnalyticsSection();
        this.showLoadingIndicator();

        // Set a timeout to ensure loading indicator is hidden
        const loadingTimeout = setTimeout(() => {
            console.log('⚠️ Loading timeout reached, hiding indicator');
            this.hideLoadingIndicator();
        }, 30000); // 30 seconds timeout

        try {
            const response = await fetch('/api/analytics/fitness', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('📊 Fitness analytics data:', result);

            if (!result.success || !result.data) {
                throw new Error(result.message || 'Failed to load fitness analytics');
            }

            const analytics = result.data;
            
            // Render charts sequentially to avoid conflicts
            await this.renderFitnessCharts(analytics);

        } catch (error) {
            console.error('❌ Fitness analytics error:', error);
            this.showAnalyticsError('Fitness', error.message);
        } finally {
            clearTimeout(loadingTimeout);
            this.hideLoadingIndicator();
            this.isRendering = false;
        }
    }

    /**
     * Render fitness charts sequentially
     */
    async renderFitnessCharts(analytics) {
        const chartFunctions = [
            () => this.renderWorkoutFrequencyChart(analytics),
            () => this.renderWeeklyProgressChart(analytics),
            () => this.renderExerciseTypesChart(analytics),
            () => this.renderIntensityDistributionChart(analytics),
            () => this.renderCaloriesBurnedChart(analytics),
            () => this.renderWorkoutMetricsChart(analytics)
        ];

        let successCount = 0;
        let errorCount = 0;

        for (const chartFn of chartFunctions) {
            try {
                await new Promise(resolve => {
                    requestAnimationFrame(() => {
                        try {
                            chartFn();
                            successCount++;
                        } catch (error) {
                            console.error('Chart rendering error:', error);
                            errorCount++;
                        }
                        resolve();
                    });
                });
                
                // Small delay between charts
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (error) {
                console.error('Chart function error:', error);
                errorCount++;
            }
        }

        console.log(`📊 Fitness charts: ${successCount} success, ${errorCount} errors`);
        
        // Ensure loading indicator is hidden after all charts are processed
        this.hideLoadingIndicator();
    }

    /**
     * Render workout frequency chart
     */
    renderWorkoutFrequencyChart(analytics) {
        const canvasId = 'workout-frequency-chart';
        
        if (!analytics.weekly_frequency || analytics.weekly_frequency.length === 0) {
            this.showNoDataMessage(canvasId, 'No workout frequency data available');
            return;
        }

        const data = analytics.weekly_frequency;
        const labels = data.map(item => item.day_name || item.day);
        const values = data.map(item => item.sessions_count || item.count);

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Workouts',
                    data: values,
                    backgroundColor: this.colors.primary,
                    borderColor: this.colors.primaryLight,
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render weekly progress chart
     */
    renderWeeklyProgressChart(analytics) {
        const canvasId = 'weekly-progress-chart';
        
        // Use weekly frequency data for progress chart
        if (!analytics.weekly_frequency || analytics.weekly_frequency.length === 0) {
            this.showNoDataMessage(canvasId, 'No weekly progress data available');
            return;
        }

        const data = analytics.weekly_frequency;
        const labels = data.map(item => item.day_name || item.day);
        const values = data.map(item => item.sessions_count || item.count);

        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Weekly Workouts',
                    data: values,
                    borderColor: this.colors.success,
                    backgroundColor: this.colors.success + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render exercise types chart
     */
    renderExerciseTypesChart(analytics) {
        const canvasId = 'exercise-types-chart';
        
        if (!analytics.exercise_types_distribution || Object.keys(analytics.exercise_types_distribution).length === 0) {
            this.showNoDataMessage(canvasId, 'No exercise types data available');
            return;
        }

        const data = analytics.exercise_types_distribution;
        const labels = Object.keys(data).map(key => key.charAt(0).toUpperCase() + key.slice(1));
        const values = Object.values(data);

        const config = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: this.colors.chartColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render intensity distribution chart
     */
    renderIntensityDistributionChart(analytics) {
        const canvasId = 'intensity-distribution-chart';
        
        if (!analytics.intensity_distribution || Object.keys(analytics.intensity_distribution).length === 0) {
            this.showNoDataMessage(canvasId, 'No intensity distribution data available');
            return;
        }

        const data = analytics.intensity_distribution;
        const labels = Object.keys(data).map(key => key.charAt(0).toUpperCase() + key.slice(1));
        const values = Object.values(data);

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sessions',
                    data: values,
                    backgroundColor: [
                        this.colors.success,
                        this.colors.warning,
                        this.colors.error
                    ].slice(0, labels.length),
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render calories burned chart
     */
    renderCaloriesBurnedChart(analytics) {
        const canvasId = 'calories-burned-chart';
        
        if (!analytics.daily_calories || analytics.daily_calories.length === 0) {
            this.showNoDataMessage(canvasId, 'No calories data available');
            return;
        }

        const data = analytics.daily_calories;
        const labels = data.map(item => item.date || item.day);
        const values = data.map(item => item.calories || item.calories_burned);

        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Calories Burned',
                    data: values,
                    borderColor: this.colors.warning,
                    backgroundColor: this.colors.warning + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render workout metrics chart
     */
    renderWorkoutMetricsChart(analytics) {
        const canvasId = 'workout-metrics-chart';
        
        // Create metrics from available data
        const metrics = [];
        const labels = [];
        const values = [];
        
        if (analytics.total_sessions > 0) {
            labels.push('Total Sessions');
            values.push(analytics.total_sessions);
        }
        
        if (analytics.average_duration_minutes > 0) {
            labels.push('Avg Duration (min)');
            values.push(analytics.average_duration_minutes);
        }
        
        if (analytics.total_calories_burned > 0) {
            labels.push('Total Calories');
            values.push(analytics.total_calories_burned);
        }
        
        if (analytics.average_workout_rating > 0) {
            labels.push('Avg Rating');
            values.push(analytics.average_workout_rating);
        }
        
        if (labels.length === 0) {
            this.showNoDataMessage(canvasId, 'No workout metrics data available');
            return;
        }

        const config = {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Performance',
                    data: values,
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: Math.max(...values) * 1.2
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render cricket analytics
     */
    async renderCricketAnalytics() {
        if (this.isRendering) {
            console.log('⚠️ Already rendering, skipping...');
            return;
        }

        this.isRendering = true;
        this.clearAnalyticsSection();
        this.showLoadingIndicator();

        try {
            const response = await fetch('/api/analytics/cricket', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('🏏 Cricket analytics data:', result);

            if (!result.success || !result.data) {
                throw new Error(result.message || 'Failed to load cricket analytics');
            }

            const analytics = result.data;
            
            // Render cricket charts
            await this.renderCricketCharts(analytics);

        } catch (error) {
            console.error('❌ Cricket analytics error:', error);
            this.showAnalyticsError('Cricket', error.message);
        } finally {
            this.hideLoadingIndicator();
            this.isRendering = false;
        }
    }

    /**
     * Render cricket charts
     */
    async renderCricketCharts(analytics) {
        const chartFunctions = [
            () => this.renderBattingConfidenceChart(analytics),
            () => this.renderSkillsDevelopmentChart(analytics),
            () => this.renderMatchPerformanceChart(analytics),
            () => this.renderCoachingSessionsChart(analytics)
        ];

        let successCount = 0;
        let errorCount = 0;

        for (const chartFn of chartFunctions) {
            try {
                await new Promise(resolve => {
                    requestAnimationFrame(() => {
                        try {
                            chartFn();
                            successCount++;
                        } catch (error) {
                            console.error('Chart rendering error:', error);
                            errorCount++;
                        }
                        resolve();
                    });
                });
                
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (error) {
                console.error('Chart function error:', error);
                errorCount++;
            }
        }

        console.log(`🏏 Cricket charts: ${successCount} success, ${errorCount} errors`);
    }

    /**
     * Render batting confidence chart
     */
    renderBattingConfidenceChart(analytics) {
        const canvasId = 'batting-confidence-chart';
        
        // Use average self assessment from coaching data as confidence level
        if (!analytics.average_self_assessment || analytics.average_self_assessment === 0) {
            this.showNoDataMessage(canvasId, 'No batting confidence data available');
            return;
        }

        const confidenceLevel = analytics.average_self_assessment;
        const totalSessions = analytics.total_coaching_sessions || analytics.total_cricket_activities || 1;

        const config = {
            type: 'doughnut',
            data: {
                labels: ['Confidence Level', 'Room for Growth'],
                datasets: [{
                    data: [confidenceLevel, 10 - confidenceLevel],
                    backgroundColor: [
                        confidenceLevel >= 7 ? this.colors.success : 
                        confidenceLevel >= 5 ? this.colors.warning : this.colors.error,
                        '#e5e7eb'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: `${confidenceLevel.toFixed(1)}/10 Average Confidence • ${totalSessions} Sessions`,
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render skills development chart
     */
    renderSkillsDevelopmentChart(analytics) {
        const canvasId = 'skills-development-chart';
        
        // Create skills overview from available data
        const skills = [];
        const labels = [];
        const values = [];
        
        if (analytics.average_self_assessment > 0) {
            labels.push('Overall Skills');
            values.push(analytics.average_self_assessment);
        }
        
        if (analytics.total_coaching_sessions > 0) {
            labels.push('Coaching Sessions');
            values.push(Math.min(analytics.total_coaching_sessions, 10)); // Cap at 10 for scale
        }
        
        if (analytics.total_matches > 0) {
            labels.push('Matches Played');
            values.push(Math.min(analytics.total_matches, 10)); // Cap at 10 for scale
        }
        
        if (analytics.average_performance > 0) {
            labels.push('Match Performance');
            values.push(analytics.average_performance);
        }
        
        if (labels.length === 0) {
            this.showNoDataMessage(canvasId, 'No skills development data available');
            return;
        }

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Skill Score',
                    data: values,
                    backgroundColor: this.colors.primary,
                    borderColor: this.colors.primaryLight,
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render match performance chart
     */
    renderMatchPerformanceChart(analytics) {
        const canvasId = 'match-performance-chart';
        
        // Use average performance from match data
        if (!analytics.average_performance || analytics.average_performance === 0) {
            this.showNoDataMessage(canvasId, 'No match performance data available');
            return;
        }

        const performanceRating = analytics.average_performance;
        const totalMatches = analytics.total_matches || 1;

        const config = {
            type: 'doughnut',
            data: {
                labels: ['Performance Rating', 'Potential'],
                datasets: [{
                    data: [performanceRating, 10 - performanceRating],
                    backgroundColor: [
                        performanceRating >= 7 ? this.colors.success : 
                        performanceRating >= 5 ? this.colors.warning : this.colors.error,
                        '#e5e7eb'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: `${performanceRating.toFixed(1)}/10 Performance • ${totalMatches} Matches`,
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render coaching sessions chart
     */
    renderCoachingSessionsChart(analytics) {
        const canvasId = 'coaching-sessions-chart';
        
        // Create coaching overview from available data
        const labels = ['Coaching Sessions', 'Matches', 'Other Activities'];
        const coachingSessions = analytics.total_coaching_sessions || 0;
        const matches = analytics.total_matches || 0;
        const otherSessions = (analytics.total_cricket_activities || 0) - coachingSessions - matches;
        
        if (coachingSessions === 0 && matches === 0 && otherSessions === 0) {
            this.showNoDataMessage(canvasId, 'No coaching sessions data available');
            return;
        }

        const config = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: [coachingSessions, matches, otherSessions],
                    backgroundColor: this.colors.chartColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: `${coachingSessions} Coaching • ${matches} Matches • ${analytics.total_cricket_activities || 0} Total`,
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Render combined analytics
     */
    async renderCombinedAnalytics() {
        if (this.isRendering) {
            console.log('⚠️ Already rendering, skipping...');
            return;
        }

        this.isRendering = true;
        this.clearAnalyticsSection();
        this.showLoadingIndicator();

        try {
            const response = await fetch('/api/analytics/combined', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('🔄 Combined analytics data:', result);

            if (!result.success || !result.data) {
                throw new Error(result.message || 'Failed to load combined analytics');
            }

            const data = result.data;
            
            // Render combined chart
            this.renderFitnessVsCricketChart(data);

        } catch (error) {
            console.error('❌ Combined analytics error:', error);
            this.showAnalyticsError('Combined', error.message);
        } finally {
            this.hideLoadingIndicator();
            this.isRendering = false;
        }
    }

    /**
     * Render fitness vs cricket correlation chart
     */
    renderFitnessVsCricketChart(data) {
        const canvasId = 'fitness-vs-cricket-chart';
        
        // Create correlation data from available analytics
        const fitnessData = data.fitness_analytics || {};
        const cricketData = data.cricket_analytics || {};
        const restData = data.rest_analytics || {};
        
        if (!fitnessData.total_sessions && !cricketData.total_cricket_activities && !restData.total_rest_days) {
            this.showNoDataMessage(canvasId, 'No correlation data available');
            return;
        }

        const labels = ['Fitness Sessions', 'Cricket Matches', 'Cricket Coaching', 'Rest Days'];
        const fitnessSessions = fitnessData.total_sessions || 0;
        const cricketMatches = cricketData.total_matches || 0;
        const cricketCoaching = cricketData.total_coaching_sessions || 0;
        const restDays = restData.total_rest_days || 0;

        const config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Activity Sessions',
                    data: [fitnessSessions, cricketMatches, cricketCoaching, restDays],
                    backgroundColor: [this.colors.primary, this.colors.success, this.colors.warning, this.colors.error],
                    borderColor: [this.colors.primaryLight, this.colors.success, this.colors.warning, this.colors.error],
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Complete Activity Overview',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };

        this.createChart(canvasId, config);
    }

    /**
     * Show no data message
     */
    showNoDataMessage(canvasId, message) {
        const container = this.createChartContainer(canvasId, this.getChartTitle(canvasId));
        const canvas = container.querySelector('canvas');
        
        if (canvas) {
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.fillStyle = '#f3f4f6';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                ctx.fillStyle = '#6b7280';
                ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(message, canvas.width / 2, canvas.height / 2);
            }
        }

        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const section = analyticsTab.querySelector('.card') || analyticsTab;
            section.appendChild(container);
        }
    }

    /**
     * Show analytics error
     */
    showAnalyticsError(type, message) {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'status error';
        errorContainer.style.cssText = `
            margin: var(--spacing-lg) 0;
            padding: var(--spacing-md);
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            color: #dc2626;
        `;
        errorContainer.innerHTML = `
            <strong>Analytics Error (${type}):</strong><br>
            ${message}<br>
            <small>Try refreshing or check if you have logged activities.</small>
        `;
        
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const section = analyticsTab.querySelector('.card') || analyticsTab;
            section.appendChild(errorContainer);
        }
    }

    /**
     * Resize all charts
     */
    resizeAllCharts() {
        this.chartRegistry.forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                try {
                    chart.resize();
                } catch (error) {
                    console.warn('Error resizing chart:', error);
                }
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