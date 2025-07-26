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
        
        // Initialize Chart.js safety patches
        this.initChartJSSafetyPatches();
        
        // Chart.js default configuration for mobile
        this.setupDefaultConfig();
    }

    /**
     * Patch Chart.js to prevent animation callback errors
     */
    initChartJSSafetyPatches() {
        if (typeof Chart !== 'undefined') {
            // Patch the animation tick Hi friend, try change my color!function to handle missing callbacks safely
            if (Chart.Animation && Chart.Animation.prototype.tick) {
                const originalTick = Chart.Animation.prototype.tick;
                Chart.Animation.prototype.tick = function(elapsed) {
                    try {
                        // Check if the callback function exists before calling
                        if (this._fn && typeof this._fn === 'function') {
                            return originalTick.call(this, elapsed);
                        } else {
                            // Animation callback is missing, mark as complete
                            this._duration = 0;
                            this._active = false;
                            return false;
                        }
                    } catch (error) {
                        console.warn('Chart.js animation tick error caught:', error);
                        this._duration = 0;
                        this._active = false;
                        return false;
                    }
                };
            }
            
            // Patch the animator update function
            if (Chart.Animator && Chart.Animator.prototype._update) {
                const originalUpdate = Chart.Animator.prototype._update;
                Chart.Animator.prototype._update = function() {
                    try {
                        return originalUpdate.call(this);
                    } catch (error) {
                        console.warn('Chart.js animator update error caught:', error);
                        // Clear problematic animations
                        if (this._animations) {
                            this._animations.clear();
                        }
                        return false;
                    }
                };
            }
            
            console.log('✅ Chart.js safety patches applied');
        }
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
            
            // Performance optimizations with safe animation handling
            Chart.defaults.animation = {
                duration: 500, // Faster animations to reduce errors
                easing: 'easeOutQuart',
                onComplete: null, // Clear any callback functions
                onProgress: null
            };
            
            // Optimize elements for performance
            Chart.defaults.elements.point.radius = 3;
            Chart.defaults.elements.line.borderWidth = 2;
            Chart.defaults.datasets.bar.maxBarThickness = 50;
            
            // Ensure tooltip animations don't conflict
            Chart.defaults.plugins.tooltip.animation = {
                duration: 150
            };
            
            // Global error handling for Chart.js
            const originalUpdate = Chart.prototype.update;
            Chart.prototype.update = function(mode) {
                try {
                    return originalUpdate.call(this, mode);
                } catch (error) {
                    console.warn('Chart update error caught:', error);
                    return this;
                }
            };
        }
    }

    /**
     * Render fitness analytics charts with performance optimization
     */
    async renderFitnessAnalytics() {
        try {
            console.log('📊 Loading fitness analytics...');
            
            // Show loading indicator
            this.showLoadingIndicator();
            
            const response = await fetch('/api/analytics/fitness', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            console.log("Analytics API Response:", data);
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load fitness analytics');
            }

            const analytics = data.data;
            
            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Wait for DOM cleanup to complete
            await new Promise(resolve => setTimeout(resolve, 150));
            
            // Render charts efficiently with timeout batching
            if (analytics.total_sessions > 0) {
                // Render critical charts first
                const chartResults = await this.renderChartsInBatches([
                    () => this.renderWorkoutFrequencyChart(analytics),
                    () => this.renderWeeklyProgressChart(analytics),
                    () => this.renderExerciseTypesDistributionChart(analytics),
                    () => this.renderIntensityDistributionChart(analytics),
                    () => this.renderCaloriesBurnedChart(analytics),
                    () => this.renderWorkoutMetricsChart(analytics)
                ]);
                
                console.log(`✅ Fitness charts: ${chartResults.successCount}/${chartResults.successCount + chartResults.errorCount} successful`);
            } else {
                this.showNoDataMessage('fitness');
            }
            
            console.log('✅ Fitness analytics rendered successfully');
            
        } catch (error) {
            console.error('❌ Failed to render fitness analytics:', error);
            this.showAnalyticsError('fitness', error.message);
        } finally {
            this.hideLoadingIndicator();
        }
    }

    /**
     * Render cricket analytics charts
     */
    async renderCricketAnalytics() {
        try {
            console.log('🏏 Loading cricket analytics...');
            
            // Show loading indicator
            this.showLoadingIndicator();
            
            const response = await fetch('/api/analytics/cricket', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            console.log("Cricket Analytics API Response:", data);
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load cricket analytics');
            }

            const analytics = data.data.analytics || data.data;
            console.log("Cricket Analytics Data:", analytics);
            
            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Wait for DOM cleanup to complete
            await new Promise(resolve => setTimeout(resolve, 150));
            
            // Check if we have any cricket data at all
            if (!analytics || (analytics.total_coaching_sessions === 0 && !analytics.total_sessions)) {
                this.showNoDataMessage('cricket');
                return;
            }
            
            // Render cricket charts in batches for better performance
            const chartResults = await this.renderChartsInBatches([
                () => this.renderBattingConfidenceChart(analytics),
                () => this.renderSkillsDevelopmentChart(analytics),
                () => this.renderMatchPerformanceChart(analytics),
                () => this.renderCoachingSessionsChart(analytics)
            ]);
            
            console.log(`✅ Cricket charts: ${chartResults.successCount}/${chartResults.successCount + chartResults.errorCount} successful`);
            
        } catch (error) {
            console.error('❌ Failed to render cricket analytics:', error);
            this.showAnalyticsError('cricket', error.message);
        } finally {
            this.hideLoadingIndicator();
        }
    }

    /**
     * Render combined analytics overview
     */
    async renderCombinedAnalytics() {
        try {
            console.log('🔄 Loading combined analytics...');
            
            // Show loading indicator
            this.showLoadingIndicator();
            
            const response = await fetch('/api/analytics/combined', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to load combined analytics');
            }

            // Clear existing charts
            this.clearAnalyticsSection();
            
            // Render correlation and overview charts in batches
            await this.renderChartsInBatches([
                () => this.renderFitnessVsCricketChart(data.data)
            ]);
            
            console.log('✅ Combined analytics rendered successfully');
            
        } catch (error) {
            console.error('❌ Failed to render combined analytics:', error);
            this.showAnalyticsError('combined', error.message);
        } finally {
            this.hideLoadingIndicator();
        }
    }

    clearAnalyticsSection() {
        // First destroy all charts safely
        this.destroyAllCharts();
        
        // Clear chart containers with forced cleanup
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            // Remove all chart containers
            const chartContainers = analyticsTab.querySelectorAll('.chart-container, .status.error');
            chartContainers.forEach(container => {
                // Stop any ongoing animations in canvas elements
                const canvases = container.querySelectorAll('canvas');
                canvases.forEach(canvas => {
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        try {
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                        } catch (e) {
                            console.warn('Error clearing canvas:', e);
                        }
                    }
                });
                container.remove();
            });
            
            // Force DOM cleanup
            requestAnimationFrame(() => {
                if (analyticsTab.querySelector('.chart-container')) {
                    const remainingContainers = analyticsTab.querySelectorAll('.chart-container');
                    remainingContainers.forEach(c => c.remove());
                }
            });
        }
    }

    /**
     * Render charts in batches to improve performance with better error handling
     */
    async renderChartsInBatches(chartFunctions) {
        const batchSize = 2; // Render 2 charts at a time
        let successCount = 0;
        let errorCount = 0;
        
        for (let i = 0; i < chartFunctions.length; i += batchSize) {
            const batch = chartFunctions.slice(i, i + batchSize);
            
            // Run batch in parallel but wait for completion
            const batchResults = await Promise.allSettled(batch.map(fn => {
                return new Promise(resolve => {
                    // Use multiple timeout layers for safety
                    const timeoutId = setTimeout(() => {
                        console.warn('Chart rendering timeout');
                        resolve('timeout');
                    }, 5000);
                    
                    try {
                        // Use requestAnimationFrame for smooth rendering
                        requestAnimationFrame(() => {
                            try {
                                fn();
                                clearTimeout(timeoutId);
                                resolve('success');
                            } catch (error) {
                                console.error('Chart rendering error:', error);
                                clearTimeout(timeoutId);
                                resolve('error');
                            }
                        });
                    } catch (error) {
                        console.error('Chart function error:', error);
                        clearTimeout(timeoutId);
                        resolve('error');
                    }
                });
            }));
            
            // Count results
            batchResults.forEach(result => {
                if (result.status === 'fulfilled' && result.value === 'success') {
                    successCount++;
                } else {
                    errorCount++;
                }
            });
            
            // Small delay between batches to prevent UI blocking
            if (i + batchSize < chartFunctions.length) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
        
        console.log(`Charts rendered: ${successCount} success, ${errorCount} errors`);
        return { successCount, errorCount };
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        const analyticsTab = document.getElementById('analytics-tab');
        if (analyticsTab) {
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'charts-loading';
            loadingDiv.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1000;
                text-align: center;
            `;
            loadingDiv.innerHTML = `
                <div style="font-size: 2rem; margin-bottom: 10px;">📊</div>
                <div style="color: #4f46e5; font-weight: bold;">Loading Analytics...</div>
                <div style="color: #6b7280; font-size: 0.9rem; margin-top: 5px;">Please wait</div>
            `;
            document.body.appendChild(loadingDiv);
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const loadingDiv = document.getElementById('charts-loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    /**
     * Workout frequency over the week
     */
    /**
     * Weekly workout frequency - improved with accurate calculations and insights
     */
    renderWorkoutFrequencyChart(analytics) {
        const canvas = this.getOrCreateCanvas('workout-frequency-chart', '📈 Weekly Workout Frequency');
        if (!canvas) return;

        const weeklyData = analytics.weekly_frequency || [];
        
        if (weeklyData.length === 0) {
            this.showNoDataForChart(canvas, 'No weekly frequency data available');
            return;
        }

        // Sort by day order (Monday first)
        const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const sortedData = weeklyData.sort((a, b) => 
            dayOrder.indexOf(a.day_name) - dayOrder.indexOf(b.day_name)
        );

        const labels = sortedData.map(d => d.day_name.substring(0, 3)); // Short day names
        const sessionCounts = sortedData.map(d => d.sessions_count);
        const totalDurations = sortedData.map(d => Math.round(d.total_duration));

        // Calculate statistics
        const totalSessions = sessionCounts.reduce((sum, count) => sum + count, 0);
        const totalMinutes = totalDurations.reduce((sum, duration) => sum + duration, 0);
        const avgSessionsPerDay = Math.round((totalSessions / 7) * 10) / 10;
        const mostActiveDay = sortedData.find(d => d.sessions_count === Math.max(...sessionCounts))?.day_name || 'N/A';

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Workout Sessions',
                        data: sessionCounts,
                        backgroundColor: sessionCounts.map(count => {
                            if (count === 0) return '#e5e7eb';
                            if (count >= Math.max(...sessionCounts)) return this.colors.primary;
                            if (count >= avgSessionsPerDay) return this.colors.primary + '80';
                            return this.colors.primary + '40';
                        }),
                        borderColor: this.colors.primary,
                        borderWidth: 2,
                        borderRadius: 6,
                        maxBarThickness: 50
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${totalSessions} Sessions/Week • ${Math.round(totalMinutes/60)}h Total • Peak: ${mostActiveDay}`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                const fullDayName = sortedData[context[0].dataIndex].day_name;
                                return fullDayName;
                            },
                            label: function(context) {
                                const dayIndex = context.dataIndex;
                                const sessions = sessionCounts[dayIndex];
                                const duration = totalDurations[dayIndex];
                                
                                if (sessions === 0) {
                                    return ['Rest Day - No workouts', '💤 Recovery time'];
                                }
                                
                                const avgDuration = duration > 0 ? Math.round(duration / sessions) : 0;
                                let dayType = '';
                                
                                if (sessions >= 2) dayType = '🔥 High activity day';
                                else if (sessions === 1 && avgDuration >= 45) dayType = '💪 Quality workout day';
                                else if (sessions === 1) dayType = '✅ Active day';
                                
                                return [
                                    `${sessions} workout${sessions !== 1 ? 's' : ''}`,
                                    `${duration} total minutes`,
                                    avgDuration > 0 ? `${avgDuration} min average` : '',
                                    dayType
                                ].filter(line => line !== '');
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Workout Sessions',
                            font: { size: 12, weight: 'bold' }
                        },
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Days of Week',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('workout-frequency', chart);

        // Add weekly frequency insights
        this.addFrequencyInsights(canvas, {
            totalSessions,
            totalMinutes,
            avgSessionsPerDay,
            mostActiveDay,
            activeDays: sessionCounts.filter(count => count > 0).length,
            restDays: sessionCounts.filter(count => count === 0).length
        });
    }

    /**
     * Add weekly frequency insights below the chart
     */
    addFrequencyInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        // Weekly consistency assessment
        let consistencyNote = '';
        let consistencyIcon = '';
        
        if (stats.activeDays >= 6) {
            consistencyNote = 'Excellent consistency! Remember to include rest days.';
            consistencyIcon = '🏆';
        } else if (stats.activeDays >= 4) {
            consistencyNote = 'Great workout consistency! Well balanced routine.';
            consistencyIcon = '⭐';
        } else if (stats.activeDays >= 2) {
            consistencyNote = 'Good start! Try to add 1-2 more workout days.';
            consistencyIcon = '📈';
        } else {
            consistencyNote = 'Aim for at least 3 workout days per week.';
            consistencyIcon = '🎯';
        }

        // Goal comparison (WHO recommends 150min/week)
        const weeklyGoalMinutes = 150;
        const goalAchievement = Math.min(Math.round((stats.totalMinutes / weeklyGoalMinutes) * 100), 100);
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">📈</span>
                <h4 style="margin: 0; color: #1e40af; font-size: 14px; font-weight: bold;">Weekly Pattern</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${stats.activeDays}/7</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Active Days</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${stats.avgSessionsPerDay}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Avg/Day</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${goalAchievement}%</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Weekly Goal</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${consistencyIcon} ${consistencyNote}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Exercise types distribution - improved with correct calculations
     */
    renderExerciseTypesDistributionChart(analytics) {
        const canvas = this.getOrCreateCanvas('exercise-types-chart', '🏃 Exercise Types Distribution');
        if (!canvas) return;

        const exerciseTypes = analytics.exercise_types_distribution || {};
        const labels = Object.keys(exerciseTypes).map(type => 
            type.replace('_', ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ')
        );
        const data = Object.values(exerciseTypes);
        const totalSessions = data.reduce((sum, count) => sum + count, 0);
        
        if (labels.length === 0 || totalSessions === 0) {
            this.showNoDataForChart(canvas, 'No exercise data available');
            return;
        }

        // Calculate percentages for better understanding
        const percentages = data.map(count => Math.round((count / totalSessions) * 100));

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.error,
                        this.colors.secondary
                    ],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${totalSessions} Total Sessions Recorded`,
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: {
                        position: 'bottom',
                        labels: { 
                            padding: 15,
                            usePointStyle: true,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: `${label} (${data.datasets[0].data[i]})`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    strokeStyle: data.datasets[0].backgroundColor[i],
                                    pointStyle: 'circle'
                                }));
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const label = context.label;
                                const value = context.parsed;
                                const percentage = Math.round((value / totalSessions) * 100);
                                return [`${label}: ${value} sessions`, `${percentage}% of total workouts`];
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });

        this.charts.set('exercise-types', chart);

        // Add exercise type summary
        this.addExerciseSummary(canvas, analytics, { totalSessions, exerciseTypes });
    }

    /**
     * Add exercise summary below the chart
     */
    addExerciseSummary(canvas, analytics, data) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        // Find most and least common exercise types
        const sortedTypes = Object.entries(data.exerciseTypes)
            .sort(([,a], [,b]) => b - a);
        
        const mostCommon = sortedTypes[0];
        const leastCommon = sortedTypes[sortedTypes.length - 1];
        
        const summaryDiv = document.createElement('div');
        summaryDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        summaryDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">📊</span>
                <h4 style="margin: 0; color: #0369a1; font-size: 14px; font-weight: bold;">Exercise Analysis</h4>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${mostCommon[1]}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Most Common</div>
                    <div style="font-size: 0.75rem; color: #9ca3af;">${mostCommon[0].replace('_', ' ')}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${Math.round((mostCommon[1] / data.totalSessions) * 100)}%</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">of Total</div>
                    <div style="font-size: 0.75rem; color: #9ca3af;">Primary Focus</div>
                </div>
            </div>
        `;
        
        container.appendChild(summaryDiv);
    }

    /**
     * Intensity distribution chart
     */
    /**
     * Workout intensity distribution - improved with accurate calculations
     */
    renderIntensityDistributionChart(analytics) {
        const canvas = this.getOrCreateCanvas('intensity-distribution-chart', '💪 Workout Intensity Distribution');
        if (!canvas) return;

        const intensityDist = analytics.intensity_distribution || {};
        
        if (Object.keys(intensityDist).length === 0) {
            this.showNoDataForChart(canvas, 'No intensity data available');
            return;
        }

        // Process and calculate percentages correctly
        const intensityData = Object.entries(intensityDist).map(([key, value]) => ({
            label: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
            value: value,
            originalKey: key
        }));

        // Sort by value for better visualization
        intensityData.sort((a, b) => b.value - a.value);

        const totalSessions = intensityData.reduce((sum, item) => sum + item.value, 0);
        const labels = intensityData.map(item => item.label);
        const values = intensityData.map(item => item.value);

        // Calculate percentages for display
        const percentages = values.map(value => Math.round((value / totalSessions) * 100));

        // Define colors based on intensity levels
        const intensityColors = intensityData.map(item => {
            const key = item.originalKey.toLowerCase();
            if (key.includes('low') || key.includes('light')) return this.colors.success;
            if (key.includes('moderate') || key.includes('medium')) return this.colors.warning;
            if (key.includes('high') || key.includes('vigorous')) return this.colors.error;
            return this.colors.primary;
        });

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: intensityColors.map(color => color + '80'),
                    borderColor: intensityColors,
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '50%',
                plugins: {
                    title: {
                        display: true,
                        text: `${totalSessions} Total Workouts • Most Common: ${labels[0]}`,
                        font: { size: 14, weight: 'bold' },
                        color: intensityColors[0]
                    },
                    legend: {
                        position: 'bottom',
                        labels: { 
                            padding: 15,
                            usePointStyle: true,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        const percentage = percentages[i];
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].borderColor[i],
                                            pointStyle: 'circle'
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return context[0].label + ' Intensity';
                            },
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = Math.round((value / totalSessions) * 100);
                                
                                let recommendation = '';
                                if (percentage > 50) {
                                    recommendation = '👍 Good balance in this intensity';
                                } else if (percentage > 30) {
                                    recommendation = '💪 Moderate focus on this level';
                                } else {
                                    recommendation = '📈 Consider more variety';
                                }
                                
                                return [
                                    `${value} workouts (${percentage}%)`,
                                    recommendation
                                ];
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('intensity-distribution', chart);

        // Add intensity insights
        this.addIntensityInsights(canvas, {
            intensityData,
            totalSessions,
            percentages,
            dominantIntensity: labels[0]
        });
    }

    /**
     * Add intensity distribution insights below the chart
     */
    addIntensityInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fefce8 0%, #fef7cd 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.warning};
        `;
        
        // Determine balance assessment
        const highIntensityPercent = stats.intensityData
            .filter(item => item.originalKey.toLowerCase().includes('high') || item.originalKey.toLowerCase().includes('vigorous'))
            .reduce((sum, item) => sum + item.value, 0) / stats.totalSessions * 100;
            
        let balanceNote = '';
        let balanceIcon = '';
        
        if (highIntensityPercent > 60) {
            balanceNote = 'High intensity focus - ensure adequate recovery time';
            balanceIcon = '🔥';
        } else if (highIntensityPercent > 30) {
            balanceNote = 'Good intensity balance - mix of challenging and recovery workouts';
            balanceIcon = '⚖️';
        } else {
            balanceNote = 'Consider adding more high-intensity sessions for better results';
            balanceIcon = '📈';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">💪</span>
                <h4 style="margin: 0; color: #a16207; font-size: 14px; font-weight: bold;">Intensity Balance</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.dominantIntensity}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Most Common</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.error};">${Math.round(highIntensityPercent)}%</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">High Intensity</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${balanceIcon} ${balanceNote}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Weekly progress chart - simplified and more effective visualization
     */
    renderWeeklyProgressChart(analytics) {
        const canvas = this.getOrCreateCanvas('weekly-progress-chart', '📊 Weekly Fitness Overview');
        if (!canvas) return;

        const weeklyData = analytics.weekly_frequency || [];
        
        // If we have weekly data, show a simple but effective bar chart
        if (weeklyData.length > 0) {
            // Sort data chronologically and get last 7 days
            const sortedData = weeklyData.sort((a, b) => new Date(a.date) - new Date(b.date));
            const labels = sortedData.map(d => d.day_name.substring(0, 3)); // Mon, Tue, Wed...
            const sessionCounts = sortedData.map(d => d.sessions_count);
            const durations = sortedData.map(d => d.total_duration);

            // Calculate weekly totals for summary
            const totalSessions = sessionCounts.reduce((sum, count) => sum + count, 0);
            const totalDuration = durations.reduce((sum, duration) => sum + duration, 0);
            const activeDays = sessionCounts.filter(count => count > 0).length;

            const chart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Workout Sessions',
                        data: sessionCounts,
                        backgroundColor: sessionCounts.map(count => {
                            if (count === 0) return '#e5e7eb'; // Gray for no workout
                            if (count === 1) return this.colors.warning; // Yellow for light activity
                            if (count === 2) return this.colors.success; // Green for good activity
                            return this.colors.primary; // Blue for high activity
                        }),
                        borderRadius: 8,
                        borderWidth: 0,
                        maxBarThickness: 60
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: `${totalSessions} Sessions • ${activeDays}/7 Active Days • ${Math.round(totalDuration/60)}h Total`,
                            font: { size: 14, weight: 'bold' },
                            color: this.colors.primary,
                            padding: { bottom: 20 }
                        },
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            titleColor: '#374151',
                            bodyColor: '#374151',
                            borderColor: '#e5e7eb',
                            borderWidth: 1,
                            cornerRadius: 8,
                            callbacks: {
                                title: function(context) {
                                    const dayData = sortedData[context[0].dataIndex];
                                    return dayData.day_name;
                                },
                                label: function(context) {
                                    const dayData = sortedData[context.dataIndex];
                                    const sessions = dayData.sessions_count;
                                    const duration = dayData.total_duration;
                                    const calories = dayData.total_calories || 0;
                                    
                                    if (sessions === 0) {
                                        return 'Rest Day';
                                    }
                                    
                                    return [
                                        `${sessions} session${sessions > 1 ? 's' : ''}`,
                                        `${duration} minutes`,
                                        `${calories} calories burned`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            title: {
                                display: true,
                                text: 'Days of the Week',
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            max: Math.max(...sessionCounts) + 1,
                            grid: { color: '#f1f5f9' },
                            title: {
                                display: true,
                                text: 'Sessions',
                                font: { size: 12, weight: 'bold' }
                            },
                            ticks: {
                                stepSize: 1,
                                callback: function(value) {
                                    return Number.isInteger(value) ? value : '';
                                }
                            }
                        }
                    }
                }
            });

            this.charts.set('weekly-progress', chart);
            
            // Add enhanced weekly summary
            this.addEnhancedWeeklySummary(canvas, analytics, {
                totalSessions,
                totalDuration,
                activeDays,
                weeklyData: sortedData
            });
            
        } else {
            // Fallback to simple metrics display
            this.renderSimpleProgressSummary(canvas, analytics);
        }
    }

    /**
     * Add enhanced weekly summary with key insights
     */
    addEnhancedWeeklySummary(canvas, analytics, weeklyStats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        // Calculate insights
        const consistencyScore = Math.round((weeklyStats.activeDays / 7) * 100);
        const avgSessionDuration = weeklyStats.totalDuration > 0 ? 
            Math.round(weeklyStats.totalDuration / weeklyStats.totalSessions) : 0;
        
        // Find best performing day
        const bestDay = weeklyStats.weeklyData.reduce((best, current) => 
            current.sessions_count > best.sessions_count ? current : best
        , weeklyStats.weeklyData[0]);

        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'weekly-summary-enhanced';
        summaryDiv.style.cssText = `
            margin-top: 20px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        `;

        // Key metrics grid
        const metricsGrid = document.createElement('div');
        metricsGrid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        `;

        const metrics = [
            {
                icon: '🎯',
                label: 'Consistency',
                value: `${consistencyScore}%`,
                color: consistencyScore >= 70 ? this.colors.success : 
                       consistencyScore >= 50 ? this.colors.warning : this.colors.error,
                description: `${weeklyStats.activeDays}/7 days active`
            },
            {
                icon: '⏱️',
                label: 'Avg Session',
                value: `${avgSessionDuration}min`,
                color: this.colors.primary,
                description: `${weeklyStats.totalSessions} total sessions`
            },
            {
                icon: '🔥',
                label: 'Total Calories',
                value: `${analytics.total_calories_burned || 0}`,
                color: this.colors.error,
                description: `${Math.round((analytics.total_calories_burned || 0) / 7)} avg/day`
            },
            {
                icon: '🏆',
                label: 'Best Day',
                value: bestDay ? bestDay.day_name.substring(0, 3) : 'N/A',
                color: this.colors.warning,
                description: bestDay ? `${bestDay.sessions_count} sessions` : 'No data'
            }
        ];

        metrics.forEach(metric => {
            const metricCard = document.createElement('div');
            metricCard.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 16px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e5e7eb;
                transition: transform 0.2s ease;
            `;
            
            metricCard.innerHTML = `
                <div style="font-size: 1.8rem; margin-bottom: 8px;">${metric.icon}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: ${metric.color}; margin-bottom: 4px;">
                    ${metric.value}
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; font-weight: 600; margin-bottom: 4px;">
                    ${metric.label}
                </div>
                <div style="font-size: 0.7rem; color: #9ca3af;">
                    ${metric.description}
                </div>
            `;
            
            metricsGrid.appendChild(metricCard);
        });

        summaryDiv.appendChild(metricsGrid);

        // Add progress indicator
        const progressDiv = document.createElement('div');
        progressDiv.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #e5e7eb;
        `;

        const progressBarBg = document.createElement('div');
        progressBarBg.style.cssText = `
            background: #e5e7eb;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        `;

        const progressBarFill = document.createElement('div');
        progressBarFill.style.cssText = `
            background: linear-gradient(90deg, ${this.colors.primary}, ${this.colors.success});
            height: 100%;
            width: ${consistencyScore}%;
            border-radius: 4px;
            transition: width 0.8s ease;
        `;

        progressBarBg.appendChild(progressBarFill);
        
        const progressLabel = document.createElement('div');
        progressLabel.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: #6b7280;
        `;
        
        let motivationalMessage = '';
        if (consistencyScore >= 80) motivationalMessage = '🔥 Excellent consistency! Keep it up!';
        else if (consistencyScore >= 60) motivationalMessage = '👍 Good progress! Try for more active days.';
        else if (consistencyScore >= 40) motivationalMessage = '💪 Getting started! Every workout counts.';
        else motivationalMessage = '🌟 Start small, build habits gradually.';

        progressLabel.innerHTML = `
            <span style="font-weight: 600;">Weekly Goal Progress</span>
            <span style="color: ${this.colors.primary}; font-weight: bold;">${consistencyScore}%</span>
        `;

        const motivationDiv = document.createElement('div');
        motivationDiv.style.cssText = `
            text-align: center;
            margin-top: 8px;
            font-size: 0.85rem;
            color: #374151;
            font-weight: 500;
        `;
        motivationDiv.textContent = motivationalMessage;

        progressDiv.appendChild(progressBarBg);
        progressDiv.appendChild(progressLabel);
        progressDiv.appendChild(motivationDiv);
        summaryDiv.appendChild(progressDiv);

        container.appendChild(summaryDiv);
    }

    /**
     * Simple progress summary when no weekly data is available
     */
    renderSimpleProgressSummary(canvas, analytics) {
        const container = canvas.closest('.chart-container');
        if (container) {
            container.innerHTML = `
                <h3 style="margin-bottom: var(--spacing-md); color: var(--primary-color);">📊 Weekly Fitness Overview</h3>
                <div style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                    <h4 style="color: var(--primary-color); margin-bottom: 1rem;">Week Summary</h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 20px;">
                        <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                            <div style="font-size: 1.5rem; color: ${this.colors.primary}; font-weight: bold;">${analytics.total_sessions || 0}</div>
                            <div style="font-size: 0.9rem; color: #6b7280;">Total Sessions</div>
                        </div>
                        <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                            <div style="font-size: 1.5rem; color: ${this.colors.success}; font-weight: bold;">${Math.round(analytics.average_duration_minutes || 0)}min</div>
                            <div style="font-size: 0.9rem; color: #6b7280;">Avg Duration</div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Calories burned over time - improved with better calculations
     */
    renderCaloriesBurnedChart(analytics) {
        const canvas = this.getOrCreateCanvas('calories-burned-chart', '🔥 Daily Calories Burned');
        if (!canvas) return;

        const caloriesData = analytics.daily_calories || [];
        
        if (caloriesData.length === 0) {
            this.showNoDataForChart(canvas, 'No calorie data available');
            return;
        }

        // Sort data by date and prepare for visualization
        const sortedData = caloriesData.sort((a, b) => new Date(a.date) - new Date(b.date));
        const labels = sortedData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        });
        const calories = sortedData.map(d => d.calories);
        
        // Calculate statistics
        const totalCalories = calories.reduce((sum, cal) => sum + cal, 0);
        const avgDailyCalories = Math.round(totalCalories / calories.length);
        const maxCalories = Math.max(...calories);
        const activeDays = calories.filter(cal => cal > 0).length;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Calories Burned',
                    data: calories,
                    backgroundColor: calories.map(cal => {
                        if (cal === 0) return '#e5e7eb'; // Gray for no activity
                        if (cal < avgDailyCalories) return this.colors.warning + '80'; // Light for below average
                        if (cal < maxCalories * 0.8) return this.colors.error + '80'; // Medium for good
                        return this.colors.error; // Full for excellent
                    }),
                    borderColor: calories.map(cal => {
                        if (cal === 0) return '#d1d5db';
                        if (cal < avgDailyCalories) return this.colors.warning;
                        if (cal < maxCalories * 0.8) return this.colors.error;
                        return this.colors.error;
                    }),
                    borderWidth: 2,
                    borderRadius: 6,
                    maxBarThickness: 50
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${totalCalories} Total • ${avgDailyCalories} Avg/Day • ${activeDays}/${calories.length} Active Days`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.error
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                const calories = context.parsed.y;
                                if (calories === 0) return 'Rest Day - No calories burned';
                                
                                const percentage = Math.round((calories / maxCalories) * 100);
                                let performance = '';
                                if (percentage >= 80) performance = '🔥 Excellent burn!';
                                else if (percentage >= 60) performance = '💪 Great workout!';
                                else if (percentage >= 40) performance = '👍 Good effort!';
                                else performance = '🌟 Every bit counts!';
                                
                                return [
                                    `${calories} calories burned`,
                                    `${percentage}% of your best day`,
                                    performance
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Calories',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Days',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('calories-burned', chart);

        // Add calorie insights
        this.addCalorieInsights(canvas, {
            totalCalories,
            avgDailyCalories,
            maxCalories,
            activeDays,
            totalDays: calories.length,
            calories
        });
    }

    /**
     * Add calorie insights below the chart
     */
    addCalorieInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        // Calculate weekly goal progress (assuming 2000 calories/week goal)
        const weeklyGoal = 2000;
        const goalProgress = Math.min(Math.round((stats.totalCalories / weeklyGoal) * 100), 100);
        
        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.error};
        `;
        
        // Determine recommendation
        let recommendation = '';
        if (stats.avgDailyCalories < 200) {
            recommendation = '💡 Consider longer or more intense workouts to increase calorie burn';
        } else if (stats.avgDailyCalories < 400) {
            recommendation = '💡 Great start! Try adding 10-15 minutes to your workouts';
        } else {
            recommendation = '💡 Excellent calorie burn! Maintain this intensity for best results';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🔥</span>
                <h4 style="margin: 0; color: #b91c1c; font-size: 14px; font-weight: bold;">Calorie Insights</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.error};">${stats.maxCalories}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Best Day</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.avgDailyCalories}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Daily Average</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${goalProgress}%</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Weekly Goal</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${recommendation}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Key workout metrics summary
     */
    /**
     * Comprehensive workout metrics overview - improved calculations
     */
    renderWorkoutMetricsChart(analytics) {
        const canvas = this.getOrCreateCanvas('workout-metrics-chart', '📋 Workout Overview');
        if (!canvas) return;

        // Calculate comprehensive metrics with validation
        const totalSessions = analytics.total_sessions || 0;
        const avgDuration = Math.round(analytics.average_duration_minutes || 0);
        const totalCalories = analytics.total_calories_burned || 0;
        const avgRating = Math.round((analytics.average_workout_rating || 0) * 10) / 10;
        const avgCaloriesPerSession = totalSessions > 0 ? Math.round(totalCalories / totalSessions) : 0;
        const totalHours = Math.round((totalSessions * avgDuration) / 60 * 10) / 10;

        const metrics = [
            { 
                label: 'Total Sessions', 
                value: totalSessions, 
                color: this.colors.primary,
                unit: '',
                description: 'Workout count'
            },
            { 
                label: 'Avg Duration', 
                value: avgDuration, 
                color: this.colors.success,
                unit: 'min',
                description: 'Per session'
            },
            { 
                label: 'Total Calories', 
                value: totalCalories, 
                color: this.colors.error,
                unit: '',
                description: 'Energy burned'
            },
            { 
                label: 'Avg Rating', 
                value: avgRating, 
                color: this.colors.warning,
                unit: '/10',
                description: 'Workout quality'
            }
        ];

        // Filter out zero values for better visualization
        const nonZeroMetrics = metrics.filter(m => m.value > 0);
        
        if (nonZeroMetrics.length === 0) {
            this.showNoDataForChart(canvas, 'No workout data available');
            return;
        }

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: nonZeroMetrics.map(m => m.label),
                datasets: [{
                    data: nonZeroMetrics.map(m => m.value),
                    backgroundColor: nonZeroMetrics.map(m => m.color + '80'),
                    borderColor: nonZeroMetrics.map(m => m.color),
                    borderWidth: 2,
                    borderRadius: 8,
                    maxBarThickness: 60
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${totalHours}h Total • Best Day: ${analytics.best_day_of_week || 'N/A'}`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                const metric = nonZeroMetrics[context[0].dataIndex];
                                return metric.label;
                            },
                            label: function(context) {
                                const metric = nonZeroMetrics[context.dataIndex];
                                const value = context.parsed.y;
                                
                                return [
                                    `${value}${metric.unit}`,
                                    metric.description
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Values',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Metrics',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('workout-metrics', chart);

        // Add comprehensive workout insights
        this.addWorkoutInsights(canvas, {
            totalSessions,
            avgDuration,
            totalCalories,
            avgRating,
            avgCaloriesPerSession,
            totalHours,
            bestDay: analytics.best_day_of_week
        });
    }

    /**
     * Add comprehensive workout insights below the chart
     */
    addWorkoutInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0f9ff 0%, #f7fafc 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        // Performance assessment
        let performanceNote = '';
        let performanceIcon = '';
        
        if (stats.avgRating >= 8) {
            performanceNote = 'Excellent workout quality! Keep up the great work.';
            performanceIcon = '🌟';
        } else if (stats.avgRating >= 6) {
            performanceNote = 'Good workout intensity. Consider pushing a bit harder.';
            performanceIcon = '💪';
        } else if (stats.avgRating >= 4) {
            performanceNote = 'Moderate effort. Try to increase workout intensity.';
            performanceIcon = '📈';
        } else if (stats.avgRating > 0) {
            performanceNote = 'Low intensity detected. Consider more challenging workouts.';
            performanceIcon = '⚡';
        } else {
            performanceNote = 'Start logging workout ratings to track progress.';
            performanceIcon = '📊';
        }

        // Duration assessment
        let durationNote = '';
        if (stats.avgDuration >= 60) {
            durationNote = 'Great workout duration!';
        } else if (stats.avgDuration >= 30) {
            durationNote = 'Good workout length';
        } else if (stats.avgDuration > 0) {
            durationNote = 'Consider longer sessions';
        } else {
            durationNote = 'Track workout duration';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">📋</span>
                <h4 style="margin: 0; color: #1e40af; font-size: 14px; font-weight: bold;">Workout Insights</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.error};">${stats.avgCaloriesPerSession}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Cal/Session</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${stats.totalHours}h</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Total Time</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.bestDay || 'N/A'}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Best Day</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151; margin-bottom: 8px;">
                ${performanceIcon} ${performanceNote}
            </div>
            ${stats.avgDuration > 0 ? `<div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ⏱️ ${durationNote} • ${stats.avgDuration} minutes average
            </div>` : ''}
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Show no data message for specific fitness charts
     */
    showNoDataMessage(type) {
        const targetTab = document.getElementById('analytics-tab');
        if (!targetTab) return;

        const noDataContainer = document.createElement('div');
        noDataContainer.className = 'chart-container no-data';
        noDataContainer.style.cssText = `
            text-align: center; 
            padding: 60px 20px; 
            color: var(--text-secondary);
            background: var(--background-color);
            border-radius: 12px;
            margin: var(--spacing-lg) 0;
        `;
        noDataContainer.innerHTML = `
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: var(--primary-color); margin-bottom: 1rem;">No Fitness Data Yet</h3>
            <p style="margin-bottom: 0.5rem;">Start logging your workouts to see detailed analytics!</p>
            <p style="font-size: 0.9rem; color: var(--text-tertiary);">
                Track exercises, durations, calories, and energy levels for comprehensive insights.
            </p>
        `;
        
        const section = targetTab.querySelector('.card') || targetTab;
        section.appendChild(noDataContainer);
    }

    /**
     * Show no data message for individual charts
     */
    showNoDataForChart(canvas, message) {
        const container = canvas.closest('.chart-container');
        if (container) {
            const noDataDiv = document.createElement('div');
            noDataDiv.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: var(--text-secondary);
                z-index: 10;
            `;
            noDataDiv.innerHTML = `
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                <p>${message}</p>
            `;
            container.style.position = 'relative';
            container.appendChild(noDataDiv);
            canvas.style.opacity = '0.3';
        }
    }



    /**
     * Batting confidence - using real data only
     */
    /**
     * Comprehensive batting confidence analysis - adapted for real data structure
     */
    renderBattingConfidenceChart(analytics) {
        const canvas = this.getOrCreateCanvas('batting-confidence-chart', '🏏 Batting Confidence Analysis');
        if (!canvas) return;

        // Handle different possible data structures
        const avgConfidence = analytics.average_self_assessment || analytics.avg_confidence || 0;
        const totalSessions = analytics.total_coaching_sessions || analytics.total_sessions || 0;
        const confidenceData = analytics.confidence_over_time || [];
        
        // If we have time-series data, use it
        if (confidenceData.length > 0) {
            this.renderConfidenceTimeSeries(canvas, confidenceData, avgConfidence);
            return;
        }
        
        // If we have basic confidence data, show a gauge chart
        if (avgConfidence > 0 && totalSessions > 0) {
            this.renderConfidenceGauge(canvas, avgConfidence, totalSessions);
            return;
        }
        
        // No confidence data available
        this.showNoDataForChart(canvas, 'No batting confidence data available - log cricket coaching sessions to track confidence');
    }

    /**
     * Render confidence as time series (when available)
     */
    renderConfidenceTimeSeries(canvas, confidentData, avgConfidence) {
        // Sort data by date and prepare for visualization
        const sortedData = confidentData.sort((a, b) => new Date(a.date) - new Date(b.date));
        const labels = sortedData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const confidenceScores = sortedData.map(d => d.confidence_level || d.confidence);

        // Calculate statistics
        const calculatedAvg = Math.round((confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length) * 10) / 10;
        const maxConfidence = Math.max(...confidenceScores);
        const minConfidence = Math.min(...confidenceScores);
        const latestConfidence = confidenceScores[confidenceScores.length - 1];
        const trend = confidenceScores.length > 1 ? 
            (latestConfidence - confidenceScores[0]) : 0;

        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Confidence Level',
                    data: confidenceScores,
                    borderColor: this.colors.warning,
                    backgroundColor: this.colors.warning + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: confidenceScores.map(score => {
                        if (score >= 8) return this.colors.success;
                        if (score >= 6) return this.colors.warning;
                        if (score >= 4) return this.colors.primary;
                        return this.colors.error;
                    }),
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Current: ${latestConfidence}/10 • Average: ${calculatedAvg}/10 • ${trend >= 0 ? '📈' : '📉'} ${Math.abs(trend).toFixed(1)}`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.warning
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                const confidence = context.parsed.y;
                                let confidenceLevel = '';
                                let levelIcon = '';
                                
                                if (confidence >= 8) {
                                    confidenceLevel = 'Very Confident';
                                    levelIcon = '🔥';
                                } else if (confidence >= 6) {
                                    confidenceLevel = 'Confident';
                                    levelIcon = '👍';
                                } else if (confidence >= 4) {
                                    confidenceLevel = 'Moderate';
                                    levelIcon = '⚖️';
                                } else {
                                    confidenceLevel = 'Needs Work';
                                    levelIcon = '📈';
                                }
                                
                                return [
                                    `Confidence: ${confidence}/10`,
                                    `${levelIcon} ${confidenceLevel}`,
                                    `${Math.round(((confidence - calculatedAvg) / calculatedAvg) * 100)}% vs average`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 10,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Confidence Level (1-10)',
                            font: { size: 12, weight: 'bold' }
                        },
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Training Sessions',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('batting-confidence', chart);

        // Add confidence insights for time series
        this.addConfidenceTimeSeriesInsights(canvas, {
            avgConfidence: calculatedAvg,
            maxConfidence,
            minConfidence,
            latestConfidence,
            trend,
            totalSessions: confidenceScores.length,
            confidenceScores
        });
    }

    /**
     * Render confidence as a gauge chart (when only average is available)
     */
    renderConfidenceGauge(canvas, avgConfidence, totalSessions) {
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Current Confidence', 'Room for Growth'],
                datasets: [{
                    data: [avgConfidence, 10 - avgConfidence],
                    backgroundColor: [
                        avgConfidence >= 7 ? this.colors.success : 
                        avgConfidence >= 5 ? this.colors.warning : this.colors.error,
                        '#e5e7eb'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${avgConfidence.toFixed(1)}/10 Average Confidence • ${totalSessions} Sessions`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.warning
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataIndex === 0) {
                                    return `Confidence Level: ${avgConfidence.toFixed(1)}/10`;
                                }
                                return `Potential Growth: ${(10 - avgConfidence).toFixed(1)} points`;
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('batting-confidence', chart);

        // Add confidence insights for gauge
        this.addConfidenceGaugeInsights(canvas, { avgConfidence, totalSessions });
    }

    /**
     * Add confidence insights for time series data
     */
    addConfidenceTimeSeriesInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fefce8 0%, #fef7cd 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.warning};
        `;
        
        // Determine progress assessment
        let progressNote = '';
        let progressIcon = '';
        
        if (stats.trend > 1.5) {
            progressNote = 'Excellent progress! Your confidence is steadily improving.';
            progressIcon = '🚀';
        } else if (stats.trend > 0.5) {
            progressNote = 'Good progress! Keep working on your batting skills.';
            progressIcon = '📈';
        } else if (stats.trend > -0.5) {
            progressNote = 'Steady confidence level. Focus on consistent practice.';
            progressIcon = '⚖️';
        } else {
            progressNote = 'Confidence has dipped. Consider working with your coach.';
            progressIcon = '🎯';
        }

        // Calculate consistency (how much confidence varies)
        const consistency = Math.round(Math.sqrt(stats.confidenceScores.reduce((sum, score) => 
            sum + Math.pow(score - stats.avgConfidence, 2), 0) / stats.totalSessions) * 10) / 10;
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🏏</span>
                <h4 style="margin: 0; color: #a16207; font-size: 14px; font-weight: bold;">Confidence Analysis</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${stats.maxConfidence}/10</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Peak Confidence</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${stats.totalSessions}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Sessions Tracked</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">±${consistency}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Consistency</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${progressIcon} ${progressNote}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Add confidence insights for gauge chart
     */
    addConfidenceGaugeInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fefce8 0%, #fef7cd 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.warning};
        `;
        
        let confidenceAssessment = '';
        let recommendation = '';
        
        if (stats.avgConfidence >= 8) {
            confidenceAssessment = 'Excellent confidence level!';
            recommendation = '🔥 Maintain this high confidence through consistent practice';
        } else if (stats.avgConfidence >= 6) {
            confidenceAssessment = 'Good confidence level';
            recommendation = '👍 Keep building confidence with targeted skill practice';
        } else if (stats.avgConfidence >= 4) {
            confidenceAssessment = 'Moderate confidence level';
            recommendation = '📈 Focus on fundamentals to build confidence';
        } else {
            confidenceAssessment = 'Low confidence level';
            recommendation = '🎯 Work with coach on basic skills to improve confidence';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🏏</span>
                <h4 style="margin: 0; color: #a16207; font-size: 14px; font-weight: bold;">Confidence Analysis</h4>
            </div>
            <div style="text-align: center; margin-bottom: 12px;">
                <div style="font-size: 2rem; font-weight: bold; color: ${this.colors.warning};">${stats.avgConfidence.toFixed(1)}/10</div>
                <div style="font-size: 1rem; color: #6b7280; margin-bottom: 4px;">${confidenceAssessment}</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">Based on ${stats.totalSessions} coaching sessions</div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${recommendation}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Comprehensive skills development analysis - adapted for real data structure
     */
    renderSkillsDevelopmentChart(analytics) {
        const canvas = this.getOrCreateCanvas('skills-development-chart', '🎯 Skills Development Progress');
        if (!canvas) return;

        // Handle different possible data structures
        const skillsData = analytics.skills_distribution || analytics.skill_breakdown || {};
        const avgScore = analytics.average_self_assessment || analytics.avg_skill_level || 0;
        const totalCoachingSessions = analytics.total_coaching_sessions || analytics.total_sessions || 0;
        
        // If we have skills distribution data, use it
        if (Object.keys(skillsData).length > 0) {
            this.renderSkillsDistributionChart(canvas, skillsData, totalCoachingSessions);
            return;
        }

        // If we have average assessment score, show a simple skills overview
        if (avgScore > 0 && totalCoachingSessions > 0) {
            this.renderBasicSkillsOverview(canvas, avgScore, totalCoachingSessions, analytics);
            return;
        }

        // No skills data available
        this.showNoDataForChart(canvas, 'No skills development data available - log cricket coaching sessions to track skills');
    }

    /**
     * Render detailed skills distribution chart (when skills breakdown is available)
     */
    renderSkillsDistributionChart(canvas, skillsData, totalSessions) {
        // Process and calculate percentages correctly
        const skillsArray = Object.entries(skillsData).map(([key, value]) => ({
            label: key.replace('_', ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' '),
            value: value,
            originalKey: key
        }));

        // Sort by value for better visualization
        skillsArray.sort((a, b) => b.value - a.value);

        const skillTotalSessions = skillsArray.reduce((sum, item) => sum + item.value, 0);
        const labels = skillsArray.map(item => item.label);
        const values = skillsArray.map(item => item.value);

        // Calculate percentages for display
        const percentages = values.map(value => Math.round((value / skillTotalSessions) * 100));

        // Define colors based on skill types
        const skillColors = skillsArray.map(item => {
            const key = item.originalKey.toLowerCase();
            if (key.includes('batting')) return this.colors.warning;
            if (key.includes('bowling')) return this.colors.error;
            if (key.includes('fielding') || key.includes('keeping')) return this.colors.success;
            if (key.includes('fitness') || key.includes('running')) return this.colors.primary;
            return this.colors.secondary;
        });

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: skillColors.map(color => color + '80'),
                    borderColor: skillColors,
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '50%',
                plugins: {
                    title: {
                        display: true,
                        text: `${skillTotalSessions} Practice Sessions • Focus: ${labels[0]}`,
                        font: { size: 14, weight: 'bold' },
                        color: skillColors[0]
                    },
                    legend: {
                        position: 'bottom',
                        labels: { 
                            padding: 15,
                            usePointStyle: true,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        const percentage = percentages[i];
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].borderColor[i],
                                            pointStyle: 'circle'
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return context[0].label + ' Practice';
                            },
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = Math.round((value / skillTotalSessions) * 100);
                                
                                let recommendation = '';
                                if (percentage > 40) {
                                    recommendation = '🎯 Primary focus area - great dedication!';
                                } else if (percentage > 25) {
                                    recommendation = '💪 Good practice balance in this skill';
                                } else if (percentage > 10) {
                                    recommendation = '📈 Consider more practice in this area';
                                } else {
                                    recommendation = '🌟 Room for more development';
                                }
                                
                                return [
                                    `${value} sessions (${percentage}%)`,
                                    recommendation
                                ];
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('skills-development', chart);

        // Add skills development insights
        this.addSkillsDistributionInsights(canvas, {
            skillsArray,
            totalSessions: skillTotalSessions,
            percentages,
            primarySkill: labels[0]
        });
    }

    /**
     * Render basic skills overview (when only average assessment is available)
     */
    renderBasicSkillsOverview(canvas, avgScore, totalSessions, analytics) {
        // Create a simple skills overview chart
        const skillsEstimate = [
            { name: 'Technical Skills', value: avgScore * 10, color: this.colors.warning },
            { name: 'Physical Fitness', value: (avgScore * 10) * 0.9, color: this.colors.primary },
            { name: 'Mental Focus', value: (avgScore * 10) * 0.85, color: this.colors.success },
            { name: 'Game Awareness', value: (avgScore * 10) * 0.8, color: this.colors.secondary }
        ];

        const chart = new Chart(canvas, {
            type: 'radar',
            data: {
                labels: skillsEstimate.map(s => s.name),
                datasets: [{
                    label: 'Skills Assessment',
                    data: skillsEstimate.map(s => s.value),
                    backgroundColor: this.colors.primary + '20',
                    borderColor: this.colors.primary,
                    borderWidth: 2,
                    pointBackgroundColor: skillsEstimate.map(s => s.color),
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Skills Assessment: ${avgScore.toFixed(1)}/10 • ${totalSessions} Sessions`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const skillName = context.label;
                                const value = context.parsed.r;
                                const rating = (value / 10).toFixed(1);
                                return `${skillName}: ${rating}/10`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            display: false
                        },
                        pointLabels: {
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('skills-development', chart);

        // Add basic skills insights
        this.addBasicSkillsInsights(canvas, { avgScore, totalSessions, skillsEstimate });
    }

    /**
     * Add skills development insights for distribution chart
     */
    addSkillsDistributionInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        // Calculate balance assessment
        const skillBalance = stats.skillsArray.length;
        const primarySkillPercent = stats.percentages[0];
        
        let balanceNote = '';
        let balanceIcon = '';
        
        if (skillBalance >= 4 && primarySkillPercent < 50) {
            balanceNote = 'Well-rounded development across multiple skills!';
            balanceIcon = '⚖️';
        } else if (primarySkillPercent > 60) {
            balanceNote = 'Heavy focus on one skill - consider diversifying practice';
            balanceIcon = '🎯';
        } else if (skillBalance >= 3) {
            balanceNote = 'Good skill variety with focused practice areas';
            balanceIcon = '📊';
        } else {
            balanceNote = 'Consider expanding to practice more diverse cricket skills';
            balanceIcon = '🌟';
        }

        const avgSessionsPerSkill = Math.round(stats.totalSessions / skillBalance);
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🎯</span>
                <h4 style="margin: 0; color: #0369a1; font-size: 14px; font-weight: bold;">Skills Development</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${skillBalance}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Skills Practiced</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.primarySkill}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Primary Focus</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${avgSessionsPerSkill}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Avg per Skill</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${balanceIcon} ${balanceNote}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Add basic skills insights for assessment chart
     */
    addBasicSkillsInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        let skillsAssessment = '';
        let recommendation = '';
        
        if (stats.avgScore >= 8) {
            skillsAssessment = 'Excellent skill level!';
            recommendation = '🔥 Maintain this high performance with consistent practice';
        } else if (stats.avgScore >= 6) {
            skillsAssessment = 'Good skill development';
            recommendation = '👍 Keep building skills through targeted practice';
        } else if (stats.avgScore >= 4) {
            skillsAssessment = 'Moderate skill level';
            recommendation = '📈 Focus on fundamentals to improve skills';
        } else {
            skillsAssessment = 'Skills need development';
            recommendation = '🎯 Work with coach on basic techniques';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🎯</span>
                <h4 style="margin: 0; color: #0369a1; font-size: 14px; font-weight: bold;">Skills Assessment</h4>
            </div>
            <div style="text-align: center; margin-bottom: 12px;">
                <div style="font-size: 2rem; font-weight: bold; color: ${this.colors.primary};">${stats.avgScore.toFixed(1)}/10</div>
                <div style="font-size: 1rem; color: #6b7280; margin-bottom: 4px;">${skillsAssessment}</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">Based on ${stats.totalSessions} coaching sessions</div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${recommendation}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Match performance analysis - adapted for real data structure
     */
    renderMatchPerformanceChart(analytics) {
        const canvas = this.getOrCreateCanvas('match-performance-chart', '🏆 Match Performance Analysis');
        if (!canvas) return;

        // Handle different possible data structures
        const battingAvg = analytics.batting_average || analytics.avg_batting_score || 0;
        const bowlingAvg = analytics.bowling_average || analytics.avg_bowling_economy || 0;
        const fieldingSuccess = ((analytics.fielding_success_rate || analytics.fielding_percentage || 0) * 100);
        const matchWinRate = ((analytics.match_win_rate || analytics.wins_percentage || 0) * 100);
        const overallRating = analytics.overall_performance_rating || analytics.average_self_assessment || 0;
        const totalMatches = analytics.total_matches_played || analytics.total_matches || analytics.total_coaching_sessions || 0;

        // If we have minimal data, show a simple overview
        if (!battingAvg && !bowlingAvg && !fieldingSuccess && !matchWinRate && overallRating === 0) {
            this.showNoDataForChart(canvas, 'No match performance data available - log match results to track performance');
            return;
        }

        // If we have some performance data, show available metrics
        const performanceMetrics = [];
        
        if (battingAvg > 0) {
            performanceMetrics.push({
                label: 'Batting Avg',
                value: battingAvg,
                color: this.colors.warning,
                unit: '',
                description: 'Runs per innings',
                benchmark: 25 // Good amateur average
            });
        }
        
        if (bowlingAvg > 0) {
            performanceMetrics.push({
                label: 'Bowling Avg',
                value: bowlingAvg,
                color: this.colors.error,
                unit: '',
                description: 'Runs per wicket',
                benchmark: 30 // Good amateur bowling average
            });
        }
        
        if (fieldingSuccess > 0) {
            performanceMetrics.push({
                label: 'Fielding %',
                value: fieldingSuccess,
                color: this.colors.success,
                unit: '%',
                description: 'Successful catches/chances',
                benchmark: 75 // Good fielding percentage
            });
        }
        
        if (matchWinRate > 0) {
            performanceMetrics.push({
                label: 'Win Rate',
                value: matchWinRate,
                color: this.colors.primary,
                unit: '%',
                description: 'Matches won',
                benchmark: 50 // Average win rate
            });
        }
        
        if (overallRating > 0 && performanceMetrics.length === 0) {
            // Show overall rating as a gauge if no other metrics
            this.renderPerformanceGauge(canvas, overallRating, totalMatches);
            return;
        }

        // Show available performance metrics
        if (performanceMetrics.length > 0) {
            this.renderPerformanceMetrics(canvas, performanceMetrics, totalMatches, overallRating);
        } else {
            this.showNoDataForChart(canvas, 'No detailed performance metrics available');
        }
    }

    /**
     * Render performance metrics as a horizontal bar chart
     */
    renderPerformanceMetrics(canvas, metrics, totalMatches, overallRating) {
        const labels = metrics.map(m => m.label);
        const values = metrics.map(m => m.value);
        
        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Performance',
                    data: values,
                    backgroundColor: metrics.map(m => m.color + '80'),
                    borderColor: metrics.map(m => m.color),
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${totalMatches > 0 ? totalMatches + ' Matches' : 'Performance Metrics'}${overallRating > 0 ? ' • Overall: ' + overallRating.toFixed(1) + '/10' : ''}`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        callbacks: {
                            title: function(context) {
                                const index = context[0].datasetIndex || context[0].dataIndex;
                                return metrics[index]?.label + ' Performance';
                            },
                            label: function(context) {
                                const index = context.dataIndex;
                                const metric = metrics[index];
                                const value = context.parsed.x;
                                const benchmark = metric.benchmark;
                                
                                let status = '';
                                if (metric.unit === '%') {
                                    status = value >= benchmark ? '✅ Above average' : '📈 Room for improvement';
                                } else {
                                    // For averages, lower is better for bowling, higher for batting
                                    if (metric.label.includes('Bowling')) {
                                        status = value <= benchmark ? '✅ Good bowling' : '📈 Work on economy';
                                    } else {
                                        status = value >= benchmark ? '✅ Strong performance' : '📈 Keep practicing';
                                    }
                                }
                                
                                return [
                                    `${value}${metric.unit} ${metric.description}`,
                                    `Target: ${benchmark}${metric.unit}`,
                                    status
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Performance Value',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { size: 12, weight: 'bold' } }
                    }
                }
            }
        });

        this.charts.set('match-performance', chart);

        // Add performance insights
        this.addPerformanceMetricsInsights(canvas, { metrics, totalMatches, overallRating });
    }

    /**
     * Render performance as a gauge chart (when only overall rating is available)
     */
    renderPerformanceGauge(canvas, overallRating, totalMatches) {
        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Current Performance', 'Potential'],
                datasets: [{
                    data: [overallRating, 10 - overallRating],
                    backgroundColor: [
                        overallRating >= 7 ? this.colors.success : 
                        overallRating >= 5 ? this.colors.warning : this.colors.error,
                        '#e5e7eb'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${overallRating.toFixed(1)}/10 Overall Performance • ${totalMatches} Sessions`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataIndex === 0) {
                                    return `Performance: ${overallRating.toFixed(1)}/10`;
                                }
                                return `Growth Potential: ${(10 - overallRating).toFixed(1)} points`;
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('match-performance', chart);

        // Add basic performance insights
        this.addBasicPerformanceInsights(canvas, { overallRating, totalMatches });
    }

    /**
     * Add performance metrics insights
     */
    addPerformanceMetricsInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.success};
        `;
        
        const strongAreas = stats.metrics.filter(m => {
            if (m.unit === '%') return m.value >= m.benchmark;
            if (m.label.includes('Bowling')) return m.value <= m.benchmark;
            return m.value >= m.benchmark;
        });
        
        const improvementAreas = stats.metrics.filter(m => {
            if (m.unit === '%') return m.value < m.benchmark;
            if (m.label.includes('Bowling')) return m.value > m.benchmark;
            return m.value < m.benchmark;
        });
        
        let performanceNote = '';
        if (strongAreas.length > improvementAreas.length) {
            performanceNote = '🔥 Strong overall performance! Keep up the excellent work.';
        } else if (improvementAreas.length > strongAreas.length) {
            performanceNote = '📈 Good foundation - focus on targeted improvements.';
        } else {
            performanceNote = '⚖️ Well-balanced performance across different skills.';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🏆</span>
                <h4 style="margin: 0; color: #166534; font-size: 14px; font-weight: bold;">Performance Analysis</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${strongAreas.length}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Strong Areas</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${stats.totalMatches}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Games Tracked</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${improvementAreas.length}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Growth Areas</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${performanceNote}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Add basic performance insights for gauge chart
     */
    addBasicPerformanceInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.success};
        `;
        
        let performanceAssessment = '';
        let recommendation = '';
        
        if (stats.overallRating >= 8) {
            performanceAssessment = 'Excellent performance!';
            recommendation = '🔥 Maintain this high level through consistent practice';
        } else if (stats.overallRating >= 6) {
            performanceAssessment = 'Good performance level';
            recommendation = '👍 Focus on specific skills to reach elite level';
        } else if (stats.overallRating >= 4) {
            performanceAssessment = 'Developing performance';
            recommendation = '📈 Work on fundamentals with your coach';
        } else {
            performanceAssessment = 'Early stage development';
            recommendation = '🎯 Focus on basic skills and regular practice';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🏆</span>
                <h4 style="margin: 0; color: #166534; font-size: 14px; font-weight: bold;">Performance Assessment</h4>
            </div>
            <div style="text-align: center; margin-bottom: 12px;">
                <div style="font-size: 2rem; font-weight: bold; color: ${this.colors.primary};">${stats.overallRating.toFixed(1)}/10</div>
                <div style="font-size: 1rem; color: #6b7280; margin-bottom: 4px;">${performanceAssessment}</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">Based on ${stats.totalMatches} sessions</div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ${recommendation}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Add match performance insights below the chart
     */
    addMatchPerformanceInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fef7cd 0%, #fef3c7 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.warning};
        `;
        
        // Determine strongest and weakest areas
        const strengthAreas = [];
        const improvementAreas = [];
        
        stats.validMetrics.forEach(metric => {
            if (metric.label === 'Bowling Avg') {
                if (metric.value <= metric.benchmark) strengthAreas.push(metric.label);
                else improvementAreas.push(metric.label);
            } else {
                if (metric.value >= metric.benchmark) strengthAreas.push(metric.label);
                else improvementAreas.push(metric.label);
            }
        });

        // Overall assessment
        let overallNote = '';
        let overallIcon = '';
        
        if (stats.overallRating >= 8) {
            overallNote = 'Exceptional all-round performance! Keep up the excellence.';
            overallIcon = '🏆';
        } else if (stats.overallRating >= 6) {
            overallNote = 'Good performance with room for targeted improvements.';
            overallIcon = '💪';
        } else if (stats.overallRating >= 4) {
            overallNote = 'Moderate performance. Focus on key skill development.';
            overallIcon = '📈';
        } else {
            overallNote = 'Work on fundamental skills for better match performance.';
            overallIcon = '🎯';
        }
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🏆</span>
                <h4 style="margin: 0; color: #a16207; font-size: 14px; font-weight: bold;">Match Performance</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${strengthAreas.length}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Strong Areas</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${stats.totalMatches}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Matches Played</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.overallRating}/10</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Overall Rating</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151; margin-bottom: 8px;">
                ${overallIcon} ${overallNote}
            </div>
            ${strengthAreas.length > 0 ? `<div style="background: rgba(34, 197, 94, 0.1); padding: 8px; border-radius: 6px; font-size: 0.8rem; color: #374151; margin-bottom: 4px;">
                💪 <strong>Strengths:</strong> ${strengthAreas.join(', ')}
            </div>` : ''}
            ${improvementAreas.length > 0 ? `<div style="background: rgba(249, 115, 22, 0.1); padding: 8px; border-radius: 6px; font-size: 0.8rem; color: #374151;">
                🎯 <strong>Focus Areas:</strong> ${improvementAreas.join(', ')}
            </div>` : ''}
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Comprehensive coaching sessions analysis with proper calculations
     */
    renderCoachingSessionsChart(analytics) {
        const canvas = this.getOrCreateCanvas('coaching-sessions-chart', '🎓 Coaching Focus Distribution');
        if (!canvas) return;

        const sessionTypes = analytics.coaching_session_types || {};
        
        if (Object.keys(sessionTypes).length === 0) {
            this.showNoDataForChart(canvas, 'No coaching session data available');
            return;
        }

        // Process and calculate coaching data
        const sessionData = Object.entries(sessionTypes).map(([key, value]) => ({
            label: key.replace('_', ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' '),
            value: value,
            originalKey: key
        }));

        // Sort by value for better visualization
        sessionData.sort((a, b) => b.value - a.value);

        const totalSessions = sessionData.reduce((sum, item) => sum + item.value, 0);
        const labels = sessionData.map(item => item.label);
        const values = sessionData.map(item => item.value);

        // Calculate percentages and hours
        const percentages = values.map(value => Math.round((value / totalSessions) * 100));
        const avgSessionDuration = analytics.average_session_duration || 90; // minutes
        const totalHours = Math.round((totalSessions * avgSessionDuration) / 60 * 10) / 10;

        // Define colors based on coaching focus
        const sessionColors = sessionData.map(item => {
            const key = item.originalKey.toLowerCase();
            if (key.includes('batting')) return this.colors.warning;
            if (key.includes('bowling')) return this.colors.error;
            if (key.includes('fielding') || key.includes('keeping')) return this.colors.success;
            if (key.includes('fitness') || key.includes('conditioning')) return this.colors.primary;
            return this.colors.secondary;
        });

        const chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: sessionColors.map(color => color + '80'),
                    borderColor: sessionColors,
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '50%',
                plugins: {
                    title: {
                        display: true,
                        text: `${totalSessions} Sessions • ${totalHours}h Total • Primary: ${labels[0]}`,
                        font: { size: 14, weight: 'bold' },
                        color: sessionColors[0]
                    },
                    legend: {
                        position: 'bottom',
                        labels: { 
                            padding: 15,
                            usePointStyle: true,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        const percentage = percentages[i];
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].borderColor[i],
                                            pointStyle: 'circle'
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return context[0].label + ' Coaching';
                            },
                            label: function(context) {
                                const value = context.parsed;
                                const percentage = Math.round((value / totalSessions) * 100);
                                const hours = Math.round((value * avgSessionDuration) / 60 * 10) / 10;
                                
                                let focusAssessment = '';
                                if (percentage > 40) {
                                    focusAssessment = '🎯 Primary focus area - intensive training';
                                } else if (percentage > 25) {
                                    focusAssessment = '💪 Strong emphasis on this skill';
                                } else if (percentage > 15) {
                                    focusAssessment = '📈 Regular practice sessions';
                                } else {
                                    focusAssessment = '🌟 Supplementary training';
                                }
                                
                                return [
                                    `${value} sessions (${percentage}%)`,
                                    `${hours} hours dedicated`,
                                    focusAssessment
                                ];
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('coaching-sessions', chart);

        // Add coaching insights
        this.addCoachingInsights(canvas, {
            sessionData,
            totalSessions,
            totalHours,
            avgSessionDuration,
            percentages,
            primaryFocus: labels[0],
            coachingStats: analytics
        });
    }

    /**
     * Add coaching session insights below the chart
     */
    addCoachingInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.success};
        `;
        
        // Calculate training balance and intensity
        const focusAreas = stats.sessionData.length;
        const intensityScore = Math.round((stats.totalSessions / (stats.coachingStats.weeks_tracked || 4)) * 10) / 10;
        const primaryFocusPercent = stats.percentages[0];
        
        let balanceAssessment = '';
        let balanceIcon = '';
        
        if (focusAreas >= 4 && primaryFocusPercent < 50) {
            balanceAssessment = 'Excellent balanced approach across all cricket skills!';
            balanceIcon = '⚖️';
        } else if (primaryFocusPercent > 60) {
            balanceAssessment = 'Intensive focus on one area - consider broader skill development';
            balanceIcon = '🎯';
        } else if (focusAreas >= 3) {
            balanceAssessment = 'Good variety in coaching with clear focus areas';
            balanceIcon = '📊';
        } else {
            balanceAssessment = 'Consider expanding coaching to cover more cricket skills';
            balanceIcon = '🌟';
        }

        // Training frequency assessment
        let frequencyNote = '';
        if (intensityScore >= 3) frequencyNote = 'High training frequency - excellent commitment!';
        else if (intensityScore >= 2) frequencyNote = 'Good regular training schedule';
        else if (intensityScore >= 1) frequencyNote = 'Moderate training frequency';
        else frequencyNote = 'Consider increasing training frequency';
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🎓</span>
                <h4 style="margin: 0; color: #166534; font-size: 14px; font-weight: bold;">Coaching Analysis</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.primaryFocus}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Primary Focus</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${focusAreas}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Skill Areas</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${intensityScore}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Sessions/Week</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151; margin-bottom: 8px;">
                ${balanceIcon} ${balanceAssessment}
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                ⏱️ ${frequencyNote} • ${Math.round(stats.avgSessionDuration)} min average sessions
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Comprehensive fitness vs cricket correlation analysis
     */
    renderFitnessVsCricketChart(data) {
        const canvas = this.getOrCreateCanvas('fitness-vs-cricket-chart', '🔄 Fitness vs Cricket Performance');
        if (!canvas) return;

        const fitnessAnalytics = data.fitness_analytics || {};
        const cricketAnalytics = data.cricket_analytics || {};
        const correlations = data.correlations || {};
        
        // Check if we have meaningful data
        const fitnessCount = fitnessAnalytics.total_sessions || 0;
        const cricketCount = cricketAnalytics.total_coaching_sessions || 0;
        
        if (fitnessCount === 0 && cricketCount === 0) {
            this.showNoDataForChart(canvas, 'No correlation data available - log both fitness and cricket activities');
            return;
        }

        // Prepare correlation data for visualization
        const correlationData = [];
        
        if (fitnessCount > 0) {
            correlationData.push({
                label: 'Fitness Sessions',
                value: fitnessCount,
                color: this.colors.success,
                description: 'Total workout sessions',
                avgDuration: fitnessAnalytics.average_duration_minutes || 0,
                totalCalories: fitnessAnalytics.total_calories_burned || 0
            });
        }
        
        if (cricketCount > 0) {
            correlationData.push({
                label: 'Cricket Sessions',
                value: cricketCount,
                color: this.colors.warning,
                description: 'Coaching/practice sessions',
                avgConfidence: cricketAnalytics.average_self_assessment || 0,
                totalHours: Math.round((cricketCount * 90) / 60 * 10) / 10 // Assuming 90 min sessions
            });
        }

        // Calculate balance ratio
        const balanceRatio = fitnessCount > 0 && cricketCount > 0 ? 
            Math.round((Math.min(fitnessCount, cricketCount) / Math.max(fitnessCount, cricketCount)) * 100) : 0;

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: correlationData.map(d => d.label),
                datasets: [{
                    data: correlationData.map(d => d.value),
                    backgroundColor: correlationData.map(d => d.color + '80'),
                    borderColor: correlationData.map(d => d.color),
                    borderWidth: 2,
                    borderRadius: 8,
                    maxBarThickness: 80
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Activity Balance: ${balanceRatio}% • Total: ${fitnessCount + cricketCount} Sessions`,
                        font: { size: 14, weight: 'bold' },
                        color: this.colors.primary
                    },
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        titleColor: '#374151',
                        bodyColor: '#374151',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                const data = correlationData[context[0].dataIndex];
                                return data.label;
                            },
                            label: function(context) {
                                const data = correlationData[context.dataIndex];
                                const value = context.parsed.y;
                                
                                let additionalInfo = [];
                                if (data.avgDuration) {
                                    additionalInfo.push(`${data.avgDuration} min average duration`);
                                }
                                if (data.totalCalories) {
                                    additionalInfo.push(`${data.totalCalories} total calories burned`);
                                }
                                if (data.avgConfidence) {
                                    additionalInfo.push(`${data.avgConfidence}/10 average confidence`);
                                }
                                if (data.totalHours) {
                                    additionalInfo.push(`${data.totalHours}h total practice time`);
                                }
                                
                                return [
                                    `${value} total sessions`,
                                    data.description,
                                    ...additionalInfo
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        title: { 
                            display: true, 
                            text: 'Number of Sessions',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Activity Type',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });

        this.charts.set('fitness-vs-cricket', chart);

        // Add correlation insights
        this.addCorrelationInsights(canvas, {
            fitnessCount,
            cricketCount,
            balanceRatio,
            fitnessAnalytics,
            cricketAnalytics,
            correlations,
            totalActivities: fitnessCount + cricketCount
        });
    }

    /**
     * Add fitness vs cricket correlation insights below the chart
     */
    addCorrelationInsights(canvas, stats) {
        const container = canvas.closest('.chart-container');
        if (!container) return;

        const insightsDiv = document.createElement('div');
        insightsDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px;
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 12px;
            border-left: 4px solid ${this.colors.primary};
        `;
        
        // Determine balance assessment
        let balanceNote = '';
        let balanceIcon = '';
        let recommendation = '';
        
        if (stats.balanceRatio >= 80) {
            balanceNote = 'Excellent balance between fitness and cricket training!';
            balanceIcon = '⚖️';
            recommendation = 'Maintain this balanced approach for optimal performance';
        } else if (stats.fitnessCount > stats.cricketCount * 2) {
            balanceNote = 'High fitness focus - great for conditioning!';
            balanceIcon = '💪';
            recommendation = 'Consider adding more cricket-specific skill practice';
        } else if (stats.cricketCount > stats.fitnessCount * 2) {
            balanceNote = 'Strong cricket skill focus!';
            balanceIcon = '🏏';
            recommendation = 'Add more fitness training to support cricket performance';
        } else if (stats.balanceRatio >= 50) {
            balanceNote = 'Good balance with slight emphasis on one area';
            balanceIcon = '📊';
            recommendation = 'Continue balanced training with minor adjustments';
        } else {
            balanceNote = 'Unbalanced training focus detected';
            balanceIcon = '🎯';
            recommendation = 'Work towards more balanced fitness and cricket training';
        }

        // Calculate weekly activity rate
        const weeksTracked = Math.max(stats.fitnessAnalytics.weeks_tracked || 4, stats.cricketAnalytics.weeks_tracked || 4);
        const weeklyRate = Math.round((stats.totalActivities / weeksTracked) * 10) / 10;
        
        insightsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 1.2rem; margin-right: 8px;">🔄</span>
                <h4 style="margin: 0; color: #92400e; font-size: 14px; font-weight: bold;">Training Balance Analysis</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.success};">${stats.fitnessCount}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Fitness Sessions</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.warning};">${stats.cricketCount}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Cricket Sessions</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${this.colors.primary};">${weeklyRate}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">Sessions/Week</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151; margin-bottom: 8px;">
                ${balanceIcon} ${balanceNote}
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #374151;">
                💡 ${recommendation}
            </div>
        `;
        
        container.appendChild(insightsDiv);
    }

    /**
     * Show no data message for charts
     */
    showNoDataForChart(canvas, message) {
        const container = canvas.closest('.chart-container');
        if (container) {
            const noDataDiv = document.createElement('div');
            noDataDiv.style.cssText = `
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 200px;
                color: #6b7280;
                background: #f9fafb;
                border: 2px dashed #d1d5db;
                border-radius: 12px;
                text-align: center;
            `;
            noDataDiv.innerHTML = `
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">No Data Available</div>
                <div style="font-size: 0.9rem;">${message}</div>
            `;
            
            // Replace canvas with no data message
            const canvasParent = canvas.parentElement;
            canvasParent.innerHTML = '';
            canvasParent.appendChild(noDataDiv);
        }
    }

    // Utility methods
    getOrCreateCanvas(id, title) {
        // First destroy any existing chart with this ID
        if (this.charts.has(id)) {
            const existingChart = this.charts.get(id);
            if (existingChart && typeof existingChart.destroy === 'function') {
                try {
                    existingChart.stop();
                    existingChart.destroy();
                } catch (error) {
                    console.warn(`Error destroying existing chart ${id}:`, error);
                }
            }
            this.charts.delete(id);
        }
        
        let canvas = document.getElementById(id);
        
        if (!canvas) {
            const container = this.createChartContainer(id, title);
            const targetTab = document.getElementById('analytics-tab');
            
            if (targetTab) {
                const section = targetTab.querySelector('.card') || targetTab;
                section.appendChild(container);
                canvas = container.querySelector('canvas');
            }
        } else {
            // Clear existing canvas context
            const ctx = canvas.getContext('2d');
            if (ctx) {
                try {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                } catch (error) {
                    console.warn('Error clearing canvas context:', error);
                }
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
        console.log('🧹 Starting comprehensive chart cleanup...');
        
        // First, stop all Chart.js animations globally
        if (window.Chart && window.Chart.instances) {
            // Stop all active animations immediately
            Object.keys(window.Chart.instances).forEach(id => {
                const chartInstance = window.Chart.instances[id];
                if (chartInstance) {
                    try {
                        // Force stop all animations
                        if (chartInstance.animator) {
                            chartInstance.animator.stop();
                        }
                        if (chartInstance.options && chartInstance.options.animation) {
                            chartInstance.options.animation.duration = 0;
                        }
                        // Clear any pending animation frames
                        if (chartInstance._animationFrame) {
                            cancelAnimationFrame(chartInstance._animationFrame);
                        }
                        chartInstance.stop();
                        chartInstance.destroy();
                    } catch (error) {
                        console.warn(`Error destroying Chart.js instance ${id}:`, error);
                    }
                }
            });
            // Clear the instances registry
            window.Chart.instances = {};
        }
        
        // Destroy our tracked charts
        this.charts.forEach((chart, key) => {
            if (chart && typeof chart.destroy === 'function') {
                try {
                    // Force stop animations
                    if (chart.animator) {
                        chart.animator.stop();
                    }
                    if (chart.options && chart.options.animation) {
                        chart.options.animation.duration = 0;
                    }
                    if (chart._animationFrame) {
                        cancelAnimationFrame(chart._animationFrame);
                    }
                    chart.stop();
                    chart.destroy();
                } catch (error) {
                    console.warn(`Error destroying chart ${key}:`, error);
                }
            }
        });
        this.charts.clear();
        
        // Clear any lingering canvas contexts
        const canvases = document.querySelectorAll('canvas');
        canvases.forEach(canvas => {
            const ctx = canvas.getContext('2d');
            if (ctx) {
                try {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    // Reset canvas dimensions to force context cleanup
                    canvas.width = 1;
                    canvas.height = 1;
                } catch (error) {
                    console.warn('Error clearing canvas context:', error);
                }
            }
        });
        
        console.log('✅ Chart cleanup complete');
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