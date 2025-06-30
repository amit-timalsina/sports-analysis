/**
 * Cricket Fitness Tracker - Mobile-First Dashboard
 * Provides modern, touch-friendly interface for activity logging and progress tracking
 */

class MobileDashboard {
    constructor() {
        this.currentUser = 'demo_user'; // TODO: Get from authentication
        this.todayEntries = new Map(); // Track today's logged activities
        this.isLoading = false;
        
        this.init();
    }

    async init() {
        console.log('🏏 Initializing Cricket Fitness Tracker Dashboard');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Setup periodic refresh
        this.setupPeriodicRefresh();
        
        console.log('✅ Dashboard initialized successfully');
    }

    setupEventListeners() {
        // Activity card clicks
        document.addEventListener('click', (e) => {
            const activityCard = e.target.closest('.activity-card');
            if (activityCard) {
                const activityType = activityCard.dataset.activity;
                this.startActivityLogging(activityType);
            }
        });

        // Tab navigation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-tab')) {
                this.switchTab(e.target.dataset.tab);
            }
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboardData());
        }

        // Pull to refresh (mobile)
        this.setupPullToRefresh();
    }

    async loadDashboardData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            // Load dashboard data
            const dashboardData = await this.fetchDashboardData();
            
            // Render components
            this.renderActivityCards(dashboardData);
            this.renderQuickStats(dashboardData);
            this.renderProgressIndicators(dashboardData);
            this.renderRecentActivity(dashboardData);
            
            console.log('✅ Dashboard data loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load dashboard data:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    async fetchDashboardData() {
        const response = await fetch('/api/dashboard');
        if (!response.ok) {
            throw new Error(`Failed to load dashboard: ${response.statusText}`);
        }
        return await response.json();
    }

    renderActivityCards(data) {
        const activityGrid = document.getElementById('activity-grid');
        if (!activityGrid) return;

        const today = new Date().toISOString().split('T')[0];
        const activities = [
            {
                type: 'fitness',
                icon: '🏃',
                title: 'Fitness',
                description: 'Log workout'
            },
            {
                type: 'cricket_coaching',
                icon: '🏏',
                title: 'Cricket',
                description: 'Practice session'
            },
            {
                type: 'cricket_match',
                icon: '🏆',
                title: 'Match',
                description: 'Game performance'
            },
            {
                type: 'rest_day',
                icon: '😴',
                title: 'Rest Day',
                description: 'Recovery tracking'
            }
        ];

        // Check which activities have been logged today
        const todayEntries = data.data?.recent_entries || {};

        activityGrid.innerHTML = activities.map(activity => {
            const hasEntry = this.hasEntryToday(todayEntries[activity.type] || [], today);
            const statusClass = hasEntry ? 'completed' : '';
            const statusText = hasEntry ? '✅ Logged' : 'Tap to log';

            return `
                <div class="activity-card ${statusClass}" data-activity="${activity.type}">
                    <div class="icon">${activity.icon}</div>
                    <div class="title">${activity.title}</div>
                    <div class="status">${statusText}</div>
                </div>
            `;
        }).join('');
    }

    renderQuickStats(data) {
        const quickStats = document.getElementById('quick-stats');
        if (!quickStats) return;

        const activitySummary = data.data?.activity_summary || {};
        
        const stats = [
            {
                label: 'This Week',
                value: `${activitySummary.fitness_sessions || 0}/7`,
                description: 'Fitness sessions'
            },
            {
                label: 'Cricket',
                value: activitySummary.cricket_coaching_sessions || 0,
                description: 'Sessions'
            },
            {
                label: 'Energy',
                value: `${activitySummary.average_energy_level || 0}/5`,
                description: 'Average level'
            },
            {
                label: 'Frequency',
                value: `${Math.round((activitySummary.weekly_frequency || 0) * 100)}%`,
                description: 'Weekly goal'
            }
        ];

        quickStats.innerHTML = stats.map(stat => `
            <div class="stat-item">
                <span class="stat-value">${stat.value}</span>
                <div class="stat-label">${stat.description}</div>
            </div>
        `).join('');
    }

    renderProgressIndicators(data) {
        const progressSection = document.getElementById('progress-section');
        if (!progressSection) return;

        const activitySummary = data.data?.activity_summary || {};
        
        // Fitness progress
        const fitnessProgress = (activitySummary.fitness_sessions || 0) / 7 * 100;
        const cricketProgress = (activitySummary.cricket_coaching_sessions || 0) / 5 * 100;

        progressSection.innerHTML = `
            <h3>📈 This Week's Progress</h3>
            
            <div class="progress-item">
                <div class="progress-text">
                    <span>Fitness Sessions</span>
                    <span>${activitySummary.fitness_sessions || 0}/7 days</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(fitnessProgress, 100)}%"></div>
                </div>
            </div>

            <div class="progress-item">
                <div class="progress-text">
                    <span>Cricket Practice</span>
                    <span>${activitySummary.cricket_coaching_sessions || 0}/5 sessions</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(cricketProgress, 100)}%"></div>
                </div>
            </div>
        `;
    }

    renderRecentActivity(data) {
        const recentActivity = document.getElementById('recent-activity');
        if (!recentActivity) return;

        const recentEntries = data.data?.recent_entries || {};
        const allEntries = [];

        // Combine all recent entries with timestamps
        Object.entries(recentEntries).forEach(([type, entries]) => {
            entries.forEach(entry => {
                allEntries.push({
                    ...entry,
                    type: type,
                    timestamp: new Date(entry.created_at)
                });
            });
        });

        // Sort by most recent
        allEntries.sort((a, b) => b.timestamp - a.timestamp);

        // Take only the most recent 5
        const recentItems = allEntries.slice(0, 5);

        if (recentItems.length === 0) {
            recentActivity.innerHTML = `
                <h3>📋 Recent Activity</h3>
                <div class="empty-state">
                    <p>No recent activities. Start logging your fitness and cricket sessions!</p>
                </div>
            `;
            return;
        }

        const activityIcons = {
            fitness: '🏃',
            cricket_coaching: '🏏',
            cricket_match: '🏆',
            rest_day: '😴'
        };

        recentActivity.innerHTML = `
            <h3>📋 Recent Activity</h3>
            <div class="recent-list">
                ${recentItems.map(item => `
                    <div class="recent-item">
                        <div class="recent-icon">${activityIcons[item.type] || '📝'}</div>
                        <div class="recent-content">
                            <div class="recent-title">${this.formatActivityTitle(item)}</div>
                            <div class="recent-time">${this.formatRelativeTime(item.timestamp)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    startActivityLogging(activityType) {
        console.log(`🎤 Starting voice logging for: ${activityType}`);
        
        // Set global variable and open modal
        window.currentEntryType = activityType;
        if (typeof openVoiceModal === 'function') {
            openVoiceModal(activityType);
        } else {
            // Direct modal opening if function not available yet
            setTimeout(() => {
                if (typeof openVoiceModal === 'function') {
                    openVoiceModal(activityType);
                } else {
                    alert(`Voice logging for ${activityType} - please wait for page to fully load!`);
                }
            }, 100);
        }
    }

    switchTab(tabName) {
        // Remove active class from all tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Add active class to clicked tab
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Show corresponding content
        this.showTabContent(tabName);
    }

    showTabContent(tabName) {
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected content
        const activeContent = document.getElementById(`${tabName}-tab`);
        if (activeContent) {
            activeContent.classList.remove('hidden');
            
            // Load tab-specific data
            this.loadTabData(tabName);
        }
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'entries':
                await this.loadEntriesData();
                break;
            case 'dashboard':
                await this.loadDashboardData();
                break;
        }
    }

    async loadAnalyticsData() {
        // Implementation for analytics loading
        console.log('📊 Loading analytics data...');
        // This will be enhanced with chart visualization
    }

    async loadEntriesData() {
        // Implementation for entries loading
        console.log('📋 Loading entries data...');
        // This will be enhanced with better entry display
    }

    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let isPulling = false;

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;
            
            if (pullDistance > 50) {
                // Show pull to refresh indicator
                this.showPullToRefreshIndicator();
            }
        });

        document.addEventListener('touchend', (e) => {
            if (!isPulling) return;
            
            const pullDistance = currentY - startY;
            isPulling = false;
            
            if (pullDistance > 100) {
                // Trigger refresh
                this.loadDashboardData();
            }
            
            this.hidePullToRefreshIndicator();
        });
    }

    setupPeriodicRefresh() {
        // Refresh dashboard data every 5 minutes
        setInterval(() => {
            if (!document.hidden) {
                this.loadDashboardData();
            }
        }, 5 * 60 * 1000);
    }

    // Utility methods
    hasEntryToday(entries, today) {
        return entries.some(entry => {
            const entryDate = new Date(entry.created_at).toISOString().split('T')[0];
            return entryDate === today;
        });
    }

    formatActivityTitle(item) {
        const titles = {
            fitness: `${item.fitness_type || 'Fitness'} - ${item.duration_minutes || 0}min`,
            cricket_coaching: `${item.session_type || 'Cricket'} Practice`,
            cricket_match: `${item.match_type || 'Match'} Performance`,
            rest_day: `${item.rest_type || 'Rest'} Day`
        };
        return titles[item.type] || 'Activity';
    }

    formatRelativeTime(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }

    showLoadingState() {
        const loadingEl = document.getElementById('loading-indicator');
        if (loadingEl) {
            loadingEl.classList.remove('hidden');
        }
    }

    hideLoadingState() {
        const loadingEl = document.getElementById('loading-indicator');
        if (loadingEl) {
            loadingEl.classList.add('hidden');
        }
    }

    showErrorState(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
    }

    showPullToRefreshIndicator() {
        // Implementation for pull to refresh visual feedback
        console.log('↓ Pull to refresh indicator shown');
    }

    hidePullToRefreshIndicator() {
        // Implementation for hiding pull to refresh
        console.log('↑ Pull to refresh indicator hidden');
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileDashboard = new MobileDashboard();
});

// Export for global access
window.MobileDashboard = MobileDashboard; 