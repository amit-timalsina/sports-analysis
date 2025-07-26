// The dashboard expects the authentication token to be present in localStorage['token'].
// The login form (authentication.html) stores the token there after successful login.
/**
 * Cricket Fitness Tracker - Mobile-First Dashboard
 * Provides modern, touch-friendly interface for activity logging and progress tracking
 */

class MobileDashboard {
    constructor() {
        this.currentUser = 'demo_user'; // TODO: Get from authentication
        this.todayEntries = new Map(); // Track today's logged activities
        this.isLoading = false;
        this.allEntries = null; // Store all entries for filtering/searching
        this.currentFilter = 'all'; // Current activity type filter
        this.currentSearchTerm = ''; // Current search term
        this.filtersSetup = false; // Track if filters have been set up
        
        this.init();
    }

    async init() {
        console.log('🏏 Initializing Cricket Fitness Tracker Dashboard');
        
        // Setup global error handlers for Chart.js
        this.setupGlobalChartErrorHandlers();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup analytics tab listeners if they exist
        this.setupAnalyticsTabListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Setup periodic refresh
        this.setupPeriodicRefresh();
        
        console.log('✅ Dashboard initialized successfully');
    }

    /**
     * Setup global error handlers to catch Chart.js animation errors
     */
    setupGlobalChartErrorHandlers() {
        // Catch any uncaught Chart.js errors
        const originalRequestAnimationFrame = window.requestAnimationFrame;
        window.requestAnimationFrame = function(callback) {
            return originalRequestAnimationFrame(function(timestamp) {
                try {
                    callback(timestamp);
                } catch (error) {
                    if (error.message && error.message.includes('_fn is not a function')) {
                        console.warn('Chart.js animation error caught and suppressed:', error);
                        return;
                    }
                    throw error;
                }
            });
        };
        
        // Listen for global errors and suppress Chart.js animation errors
        window.addEventListener('error', function(event) {
            if (event.error && event.error.message && 
                (event.error.message.includes('_fn is not a function') ||
                 event.error.message.includes('core.animation.js') ||
                 event.error.message.includes('core.animator.js'))) {
                console.warn('Chart.js animation error suppressed:', event.error);
                event.preventDefault();
                return false;
            }
        });
        
        console.log('✅ Global Chart.js error handlers setup');
    }

    setupEventListeners() {
        // Activity card clicks
        document.addEventListener('click', async (e) => {
            const activityCard = e.target.closest('.activity-card');
            if (activityCard) {
                const activityType = activityCard.dataset.activity;
                await this.startActivityLogging(activityType);
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

    setupAnalyticsTabListeners() {
        // Listen for analytics sub-tab changes
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('analytics-nav-btn') || 
                e.target.closest('.analytics-nav-btn')) {
                
                const btn = e.target.classList.contains('analytics-nav-btn') ? 
                           e.target : e.target.closest('.analytics-nav-btn');
                
                if (btn && btn.dataset.analytics) {
                    this.switchAnalyticsTab(btn.dataset.analytics);
                }
            }
        });
    }

    async switchAnalyticsTab(analyticsType) {
        try {
            console.log(`🔄 Switching to ${analyticsType} analytics...`);
            
            // Clean up existing charts first
            this.cleanupChartsOnTabSwitch();
            
            // Update active state for analytics nav
            document.querySelectorAll('.analytics-nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            const targetBtn = document.querySelector(`[data-analytics="${analyticsType}"]`);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }
            
            // Wait for cleanup to complete
            await new Promise(resolve => setTimeout(resolve, 250));
            
            // Load new analytics
            if (window.analyticsCharts) {
                switch (analyticsType) {
                    case 'fitness':
                        await window.analyticsCharts.renderFitnessAnalytics();
                        break;
                    case 'cricket':
                        await window.analyticsCharts.renderCricketAnalytics();
                        break;
                    case 'combined':
                        await window.analyticsCharts.renderCombinedAnalytics();
                        break;
                    default:
                        console.warn(`Unknown analytics type: ${analyticsType}`);
                }
            }
            
        } catch (error) {
            console.error(`❌ Failed to switch to ${analyticsType} analytics:`, error);
        }
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
            // this.renderRecentActivity(dashboardData); // REMOVE THIS LINE
            // Fetch and render recent entries for dashboard
            await this.fetchRecentEntriesForDashboard().then(entries => this.renderRecentActivity(entries));
            
            console.log('✅ Dashboard data loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load dashboard data:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    // Add this new method to MobileDashboard
    async fetchRecentEntriesForDashboard() {
        // Fetch a small number of each type for dashboard
        const results = await Promise.allSettled([
            this.fetchEntries('fitness', 2),
            this.fetchEntries('cricket_coaching', 2),
            this.fetchEntries('cricket_match', 2),
            this.fetchEntries('rest_day', 2)
        ]);
        const [fitnessResult, coachingResult, matchResult, restResult] = results;
        const fitnessEntries = fitnessResult.status === 'fulfilled' ? fitnessResult.value : [];
        const coachingEntries = coachingResult.status === 'fulfilled' ? coachingResult.value : [];
        const matchEntries = matchResult.status === 'fulfilled' ? matchResult.value : [];
        const restEntries = restResult.status === 'fulfilled' ? restResult.value : [];
        // Combine and sort by date
        const allEntries = [
            ...fitnessEntries.map(e => ({ ...e, type: 'fitness' })),
            ...coachingEntries.map(e => ({ ...e, type: 'cricket_coaching' })),
            ...matchEntries.map(e => ({ ...e, type: 'cricket_match' })),
            ...restEntries.map(e => ({ ...e, type: 'rest_day' }))
        ];
        allEntries.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        return allEntries.slice(0, 5); // Only show 5 most recent
    }

    async fetchDashboardData() {
        const response = await fetch('/api/dashboard', {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
        });
        if (!response.ok) {
            throw new Error(`Failed to load dashboard: ${response.statusText}`);
        }
        const data = await response.json();
        // Adapt the backend response to the legacy format used throughout the dashboard
        return this.transformDashboardResponse(data);
    }

    /**
     * Transforms the newer backend dashboard response into the legacy structure
     * that the rest of the dashboard rendering logic expects. This avoids large-
     * scale refactors across the file while we progressively migrate the API.
     *
     * @param {object} data Raw response from /api/dashboard
     * @returns {object} Transformed response with legacy keys (activity_summary, recent_entries, quick_insights)
     */
    transformDashboardResponse(data) {
        if (!data || !data.data) return data;

        const d = data.data;

        // 1. Map the new "this_week" block -> legacy "activity_summary"
        if (d.this_week) {
            d.activity_summary = {
                fitness_sessions: d.this_week.fitness_sessions || 0,
                cricket_coaching_sessions: d.this_week.coaching_sessions || 0,
                cricket_match_sessions: d.this_week.cricket_match_sessions || 0,
                rest_day_sessions: d.this_week.rest_day_sessions || 0,
            };
        }

        // 2. Map the new "recent_activities" block -> legacy "recent_entries"
        if (d.recent_activities) {
            // Helper to normalize each entry type string
            const normalizeType = (raw, fallback) => {
                if (!raw || typeof raw !== 'string') return fallback;
                return raw.toLowerCase();
            };

            const normalizeEntries = (entries, expectedType) =>
                (entries || []).map((e) => ({
                    ...e,
                    type: expectedType, // ensure consistent type string for frontend
                }));

            d.recent_entries = {
                fitness: normalizeEntries(d.recent_activities.fitness, 'fitness'),
                cricket_coaching: normalizeEntries(d.recent_activities.coaching, 'cricket_coaching'),
                cricket_match: normalizeEntries(d.recent_activities.cricket_match, 'cricket_match'),
                rest_day: normalizeEntries(d.recent_activities.rest_day, 'rest_day'),
            };
        }

        // 3. Provide an empty quick_insights placeholder to prevent undefined errors
        if (!d.quick_insights) {
            d.quick_insights = {};
        }

        return data;
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
                description: 'Log workout',
                apiKey: 'fitness'
            },
            {
                type: 'cricket_coaching',
                icon: '🏏',
                title: 'Cricket',
                description: 'Practice session',
                apiKey: 'cricket_coaching'
            },
            {
                type: 'cricket_match',
                icon: '🏆',
                title: 'Match',
                description: 'Game performance',
                apiKey: 'cricket_match'
            },
            {
                type: 'rest_day',
                icon: '😴',
                title: 'Rest Day',
                description: 'Recovery tracking',
                apiKey: 'rest_day'
            }
        ];

        // Check which activities have been logged today
        const todayEntries = data.data?.recent_entries || {};

        activityGrid.innerHTML = activities.map(activity => {
            const hasEntry = this.hasEntryToday(todayEntries[activity.apiKey] || [], today);
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
    }matches

    renderQuickStats(data) {
        const quickStats = document.getElementById('quick-stats');
        if (!quickStats) return;

        const summary = data.data?.activity_summary || {};
        const insights = data.data?.quick_insights || {};
        
        // Calculate more meaningful stats
        const totalActivities = (summary.fitness_sessions || 0) + 
                               (summary.cricket_coaching_sessions || 0) + 
                               (summary.matches_played || 0) + 
                               (summary.rest_days || 0);
        
        const fitnessGoalProgress = Math.min(Math.round((summary.fitness_sessions || 0) / 4 * 100), 100); // 4 sessions per week target
        
        const stats = [
            {
                label: 'Activities',
                value: totalActivities,
                description: 'This period',
                trend: totalActivities > 0 ? '+' : ''
            },
            {
                label: 'Fitness',
                value: `${fitnessGoalProgress}%`,
                description: 'Weekly goal',
                trend: fitnessGoalProgress >= 75 ? '🔥' : fitnessGoalProgress >= 50 ? '👍' : ''
            },
        ];

        quickStats.innerHTML = stats.map(stat => `
            <div class="stat-item">
                <div class="stat-value-container">
                <span class="stat-value">${stat.value}</span>
                    ${stat.trend ? `<span class="stat-trend">${stat.trend}</span>` : ''}
                </div>
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
        const cricketMatchProgress = (activitySummary.cricket_match_sessions || 0) / 5 * 100;
        const restDayProgress = (activitySummary.rest_day_sessions || 0) / 5 * 100;

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
                    <span>${activitySummary.cricket_coaching_sessions || 0}/7 sessions</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(cricketProgress, 100)}%"></div>
                </div>
            </div>

            <div class="progress-item">
                <div class="progress-text">
                    <span>Cricket Match</span>
                    <span>${activitySummary.cricket_match_sessions || 0}/7 sessions</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(cricketMatchProgress, 100)}%"></div>
                </div>
            </div>

            <div class="progress-item">
                <div class="progress-text">
                    <span>Rest Day</span>
                    <span>${activitySummary.rest_day_sessions || 0}/7 sessions</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(restDayProgress, 100)}%"></div>
                </div>
            </div>
        `;
    }

    renderRecentActivity(entries) {
        const recentActivity = document.getElementById('recent-activity');
        if (!recentActivity) return;
        if (!entries || entries.length === 0) {
            recentActivity.innerHTML = `
                <h3>📋 Recent Activity</h3>
                <div class="empty-state">
                    <p>No recent activities. Start logging your fitness and cricket sessions!</p>
                </div>
            `;
            return;
        }
        recentActivity.innerHTML = `
            <h3>📋 Recent Activity</h3>
            <div class="recent-list">
                ${entries.map(entry => this.createEntryCard(entry)).join('')}
            </div>
        `;
    }

 

    showActivityDetails(item) {
        console.log('🔍 Showing details for activity:', item);
        const modal = document.getElementById('activityModal');
        const modalContent = document.getElementById('activityModalContent');
        
        const icon = this.getActivityIcon(item.type);
        const title = this.formatActivityTitle(item);
        
        // If we have the new transcription format (array of messages), display each as a block
        let transcriptHtml = '';
        if (item.transcription && Array.isArray(item.transcription) && item.transcription.length > 0) {
            transcriptHtml = `<div class="conversation-turns">${item.transcription.map((msg, idx) => `
                <div class="conv-turn">
                    <div class="conv-a"><strong>🗣️ ${idx + 1}:</strong> ${msg}</div>
                </div>
            `).join('')}</div>`;
        } else if (item.transcript) {
            // Fallback to legacy logic
            const formatTranscript = (transcript) => {
                if (!transcript) return '<div class="no-transcript">No transcript available</div>';
                try {
                    const parsed = JSON.parse(transcript);
                    if (Array.isArray(parsed)) {
                        return `
                            <div class="conversation-turns">
                                ${parsed.map((turn, idx) => `
                                    <div class="conv-turn">
                                        <div class="conv-q"><strong>🤖 Q${idx + 1}:</strong> ${turn.question || ''}</div>
                                        <div class="conv-a"><strong>🗣️ A${idx + 1}:</strong> ${turn.answer || ''}</div>
                                    </div>
                                `).join('')}
                            </div>`;
                    }
                } catch (e) { /* fallback */ }
                if (transcript.includes('Turn ') && transcript.includes('(conf:')) {
                    const turns = transcript.split('\n\n').filter(t => t.trim());
                    const html = turns.map((block, idx) => {
                        const lines = block.split('\n');
                        const header = lines[0];
                        const content = lines.slice(1).join(' ');
                        return `
                            <div class="conv-turn">
                                <div class="conv-a"><strong>🗣️ A${idx + 1}:</strong> ${content}</div>
                            </div>`;
                    }).join('');
                    return `<div class="conversation-turns">${html}</div>`;
                }
                return `<div class="transcript-single">${transcript}</div>`;
            };
            let transcriptToShow = item.transcript || '';
            transcriptHtml = formatTranscript(transcriptToShow);
        } else {
            transcriptHtml = '<div class="no-transcript">No transcript available</div>';
        }
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <div class="modal-title">
                    <span class="modal-icon">${icon}</span>
                    <span>${title}</span>
                </div>
                <span class="close-modal" onclick="window.mobileDashboard.closeActivityModal()">&times;</span>
            </div>
            
            <div class="modal-body">
                <div class="detail-section">
                    <h4>📅 Activity Information</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">Date & Time:</span>
                            <span class="detail-value">${this.formatDateTime(item.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Session ID:</span>
                            <span class="detail-value">${item.conversation_id || 'N/A'}</span>
                        </div>
                        ${item.processing_duration ? `
                        <div class="detail-item">
                            <span class="detail-label">Processing Time:</span>
                            <span class="detail-value">${item.processing_duration.toFixed(2)}s</span>
                        </div>
                        ` : ''}
                    </div>
                </div>

                <div class="detail-section">
                    <h4>🎤 Voice Transcription</h4>
                    <div class="transcript-container">
                        ${transcriptHtml}
                    </div>
                </div>

                ${this.formatActivitySpecificDetails(item)}

                ${item.notes ? `
                <div class="detail-section">
                    <h4>📝 Notes</h4>
                    <p class="notes-text">${item.notes}</p>
                </div>
                ` : ''}

                <div class="detail-section">
                    <h4>🔧 Technical Information</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">Entry ID:</span>
                            <span class="detail-value">#${item.id}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Activity Type:</span>
                            <span class="detail-value">${item.activity_type || item.type}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Conversation ID:</span>
                            <span class="detail-value">${item.conversation_id || 'N/A'}</span>
                        </div>
                        ${item.updated_at ? `
                        <div class="detail-item">
                            <span class="detail-label">Last Updated:</span>
                            <span class="detail-value">${this.formatDateTime(item.updated_at)}</span>
                        </div>
                        ` : ''}
                        
                        ${this.formatTechnicalFields(item)}
                    </div>
                </div>

                <div class="detail-section">
                    <h4>🔍 Raw JSON Data</h4>
                    <div class="json-container">
                        <pre class="json-display">${JSON.stringify(item, null, 2)}</pre>
                    </div>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    getActivityIcon(type) {
        const icons = {
            fitness: '🏃',
            cricket_coaching: '🏏',
            cricket_match: '🏆',
            cricket_matches: '🏆',
            rest_day: '😴'
        };
        return icons[type] || '📝';
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

    formatTechnicalFields(item) {
        let fieldsHtml = '';
        
        switch (item.type) {
            case 'cricket_coaching':
                // Session Structure
                if (item.warm_up_minutes !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Warm-up Duration:</span>
                        <span class="detail-value">${item.warm_up_minutes} minutes</span>
                    </div>`;
                }
                if (item.skill_work_minutes !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Skill Work Duration:</span>
                        <span class="detail-value">${item.skill_work_minutes} minutes</span>
                    </div>`;
                }
                if (item.game_simulation_minutes !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Game Simulation:</span>
                        <span class="detail-value">${item.game_simulation_minutes} minutes</span>
                    </div>`;
                }
                if (item.cool_down_minutes !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Cool-down Duration:</span>
                        <span class="detail-value">${item.cool_down_minutes} minutes</span>
                    </div>`;
                }
                
                // Training Details
                if (item.primary_focus) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Primary Focus:</span>
                        <span class="detail-value">${item.primary_focus.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.secondary_focus) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Secondary Focus:</span>
                        <span class="detail-value">${item.secondary_focus.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.discipline_focus) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Discipline Focus:</span>
                        <span class="detail-value">${item.discipline_focus.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                
                // Skills and Equipment
                if (item.skills_practiced && Array.isArray(item.skills_practiced) && item.skills_practiced.length > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Skills Practiced:</span>
                        <span class="detail-value">${item.skills_practiced.join(', ')}</span>
                    </div>`;
                }
                if (item.equipment_used && Array.isArray(item.equipment_used) && item.equipment_used.length > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Equipment Used:</span>
                        <span class="detail-value">${item.equipment_used.join(', ')}</span>
                    </div>`;
                }
                
                // Ratings and Assessment
                if (item.technique_rating !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Technique Rating:</span>
                        <span class="detail-value">${item.technique_rating}/10</span>
                    </div>`;
                }
                if (item.effort_level !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Effort Level:</span>
                        <span class="detail-value">${item.effort_level}/10</span>
                    </div>`;
                }
                
                // Session Goals and Achievement
                if (item.session_goals && Array.isArray(item.session_goals) && item.session_goals.length > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Session Goals:</span>
                        <span class="detail-value">${item.session_goals.join(', ')}</span>
                    </div>`;
                }
                if (item.goals_achieved && Array.isArray(item.goals_achieved) && item.goals_achieved.length > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Goals Achieved:</span>
                        <span class="detail-value">${item.goals_achieved.join(', ')}</span>
                    </div>`;
                }
                if (item.improvement_areas && Array.isArray(item.improvement_areas) && item.improvement_areas.length > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Improvement Areas:</span>
                        <span class="detail-value">${item.improvement_areas.join(', ')}</span>
                    </div>`;
                }
                
                // Coach and Facility Info
                if (item.coach_name) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Coach Name:</span>
                        <span class="detail-value">${item.coach_name}</span>
                    </div>`;
                }
                if (item.facility_name) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Facility:</span>
                        <span class="detail-value">${item.facility_name}</span>
                    </div>`;
                }
                if (item.indoor_outdoor) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Environment:</span>
                        <span class="detail-value">${item.indoor_outdoor.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                
                // Session Logistics
                if (item.start_time) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Start Time:</span>
                        <span class="detail-value">${item.start_time}</span>
                    </div>`;
                }
                if (item.end_time) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">End Time:</span>
                        <span class="detail-value">${item.end_time}</span>
                    </div>`;
                }
                if (item.group_size !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Group Size:</span>
                        <span class="detail-value">${item.group_size} ${item.group_size === 1 ? 'person' : 'people'}</span>
                    </div>`;
                }
                if (item.session_cost !== undefined && item.session_cost > 0) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Session Cost:</span>
                        <span class="detail-value">$${item.session_cost}</span>
                    </div>`;
                }
                
                // Coach Feedback and Next Steps
                if (item.coach_feedback) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Coach Feedback:</span>
                        <span class="detail-value">${item.coach_feedback}</span>
                    </div>`;
                }
                if (item.next_session_focus) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Next Session Focus:</span>
                        <span class="detail-value">${item.next_session_focus}</span>
                    </div>`;
                }
                break;
                
            case 'fitness':
                // Exercise Details
                if (item.exercise_name) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Exercise Name:</span>
                        <span class="detail-value">${item.exercise_name}</span>
                    </div>`;
                }
                if (item.exercise_type) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Exercise Type:</span>
                        <span class="detail-value">${item.exercise_type}</span>
                    </div>`;
                }
                if (item.duration_minutes !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Duration:</span>
                        <span class="detail-value">${item.duration_minutes} minutes</span>
                    </div>`;
                }
                if (item.intensity) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Intensity Level:</span>
                        <span class="detail-value">${item.intensity}</span>
                    </div>`;
                }
                
                // Physical Metrics
                if (item.calories_burned !== undefined && item.calories_burned !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Calories Burned:</span>
                        <span class="detail-value">${item.calories_burned} cal</span>
                    </div>`;
                }
                if (item.distance_km !== undefined && item.distance_km !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Distance:</span>
                        <span class="detail-value">${item.distance_km} km</span>
                    </div>`;
                }
                if (item.weight_kg !== undefined && item.weight_kg !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Weight Used:</span>
                        <span class="detail-value">${item.weight_kg} kg</span>
                    </div>`;
                }
                
                // Sets and Reps
                if (item.sets !== undefined && item.sets !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Sets:</span>
                        <span class="detail-value">${item.sets}</span>
                    </div>`;
                }
                if (item.reps !== undefined && item.reps !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Reps:</span>
                        <span class="detail-value">${item.reps}</span>
                    </div>`;
                }
                
                // Heart Rate Data
                if (item.heart_rate_avg !== undefined && item.heart_rate_avg !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Average Heart Rate:</span>
                        <span class="detail-value">${item.heart_rate_avg} bpm</span>
                    </div>`;
                }
                if (item.heart_rate_max !== undefined && item.heart_rate_max !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Max Heart Rate:</span>
                        <span class="detail-value">${item.heart_rate_max} bpm</span>
                    </div>`;
                }
                
                // Mental and Physical State
                if (item.mental_state) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Mental State:</span>
                        <span class="detail-value">${item.mental_state}</span>
                    </div>`;
                }
                if (item.energy_level !== undefined && item.energy_level !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Energy Level:</span>
                        <span class="detail-value">${item.energy_level}/10</span>
                    </div>`;
                }
                if (item.workout_rating !== undefined && item.workout_rating !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Workout Rating:</span>
                        <span class="detail-value">${item.workout_rating}/10</span>
                    </div>`;
                }
                
                // Location and Environment
                if (item.location) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Location:</span>
                        <span class="detail-value">${item.location}</span>
                    </div>`;
                }
                if (item.gym_name) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Gym/Facility:</span>
                        <span class="detail-value">${item.gym_name}</span>
                    </div>`;
                }
                if (item.weather_conditions) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Weather:</span>
                        <span class="detail-value">${item.weather_conditions}</span>
                    </div>`;
                }
                if (item.temperature !== undefined && item.temperature !== null) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Temperature:</span>
                        <span class="detail-value">${item.temperature}°C</span>
                    </div>`;
                }
                
                // Equipment and Social
                if (item.equipment_used) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Equipment Used:</span>
                        <span class="detail-value">${item.equipment_used}</span>
                    </div>`;
                }
                if (item.workout_partner) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Workout Partner:</span>
                        <span class="detail-value">${item.workout_partner}</span>
                    </div>`;
                }
                if (item.trainer_name) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Trainer:</span>
                        <span class="detail-value">${item.trainer_name}</span>
                    </div>`;
                }
                
                // Timing
                if (item.start_time) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Start Time:</span>
                        <span class="detail-value">${item.start_time}</span>
                    </div>`;
                }
                if (item.end_time) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">End Time:</span>
                        <span class="detail-value">${item.end_time}</span>
                    </div>`;
                }
                break;
                
            case 'cricket_match':
                // Add cricket match-specific technical fields
                if (item.match_type) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Match Type:</span>
                        <span class="detail-value">${item.match_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.runs_scored !== null && item.runs_scored !== undefined) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Runs Scored:</span>
                        <span class="detail-value">${item.runs_scored}</span>
                    </div>`;
                }
                break;
                
            case 'rest_day':
                // Add rest day-specific technical fields
                if (item.rest_type) {
                    fieldsHtml += `<div class="detail-item">
                        <span class="detail-label">Rest Type:</span>
                        <span class="detail-value">${item.rest_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                break;
        }
        
        return fieldsHtml;
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'Today';
        } else if (diffDays === 2) {
            return 'Yesterday';
        } else if (diffDays <= 7) {
            return `${diffDays - 1} days ago`;
        } else {
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
            });
        }
    }

    formatActivitySpecificDetails(item) {
        let detailsHtml = `<div class="detail-section">
            <h4>📊 Activity Details</h4>
            <div class="detail-grid">`;

        switch (item.type) {
            case 'fitness':
                if (item.fitness_type) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Fitness Type:</span>
                        <span class="detail-value">${item.fitness_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.duration_minutes) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Duration:</span>
                        <span class="detail-value">${item.duration_minutes} minutes</span>
                    </div>`;
                }
                if (item.intensity) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Intensity:</span>
                        <span class="detail-value">${item.intensity}</span>
                    </div>`;
                }
                if (item.energy_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Energy Level:</span>
                        <span class="detail-value">${item.energy_level}/5</span>
                    </div>`;
                }
                if (item.mental_state) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Mental State:</span>
                        <span class="detail-value">${item.mental_state}</span>
                    </div>`;
                }
                break;

            case 'cricket_coaching':
                if (item.session_type) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Session Type:</span>
                        <span class="detail-value">${item.session_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.duration_minutes) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Duration:</span>
                        <span class="detail-value">${item.duration_minutes} minutes</span>
                    </div>`;
                }
                if (item.focus_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Focus Level:</span>
                        <span class="detail-value">${item.focus_level}/10</span>
                    </div>`;
                }
                if (item.confidence_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value">${item.confidence_level}/10</span>
                    </div>`;
                }
                if (item.self_assessment_score) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Self Assessment:</span>
                        <span class="detail-value">${item.self_assessment_score}/10</span>
                    </div>`;
                }
                break;

            case 'cricket_match':
            case 'cricket_matches':
                if (item.match_type) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Match Type:</span>
                        <span class="detail-value">${item.match_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.runs_scored !== null && item.runs_scored !== undefined) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Runs Scored:</span>
                        <span class="detail-value">${item.runs_scored}</span>
                    </div>`;
                }
                if (item.balls_faced !== null && item.balls_faced !== undefined) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Balls Faced:</span>
                        <span class="detail-value">${item.balls_faced}</span>
                    </div>`;
                }
                if (item.runs_scored && item.balls_faced) {
                    const strikeRate = Math.round((item.runs_scored / item.balls_faced) * 100);
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Strike Rate:</span>
                        <span class="detail-value">${strikeRate}%</span>
                    </div>`;
                }
                break;

            case 'rest_day':
            case 'rest_days':
                if (item.rest_type) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Rest Type:</span>
                        <span class="detail-value">${item.rest_type.replace(/_/g, ' ')}</span>
                    </div>`;
                }
                if (item.energy_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Energy Level:</span>
                        <span class="detail-value">${item.energy_level}/10</span>
                    </div>`;
                }
                if (item.fatigue_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Fatigue Level:</span>
                        <span class="detail-value">${item.fatigue_level}/10</span>
                    </div>`;
                }
                if (item.motivation_level) {
                    detailsHtml += `<div class="detail-item">
                        <span class="detail-label">Motivation:</span>
                        <span class="detail-value">${item.motivation_level}/10</span>
                    </div>`;
                }
                break;
        }

        detailsHtml += `</div></div>`;
        return detailsHtml;
    }

    getActivityMetrics(item) {
        switch (item.type) {
            case 'fitness': {
                const metrics = [];
                if (item.duration_minutes) metrics.push({ label: 'Duration', value: `${item.duration_minutes} min` });
                if (item.intensity) metrics.push({ label: 'Intensity', value: item.intensity });
                if (item.energy_level) metrics.push({ label: 'Energy', value: `${item.energy_level}/10` });
                if (item.distance_km) metrics.push({ label: 'Distance', value: `${item.distance_km} km` });
                return metrics;
            }
            case 'cricket_coaching': {
                const m = [];
                if (item.duration_minutes) m.push({ label: 'Duration', value: `${item.duration_minutes} min` });
                if (item.confidence_level) m.push({ label: 'Confidence', value: `${item.confidence_level}/10` });
                if (item.focus_level) m.push({ label: 'Focus', value: `${item.focus_level}/10` });
                if (item.self_assessment_score) m.push({ label: 'Self Rating', value: `${item.self_assessment_score}/10` });
                return m;
            }
            case 'cricket_match':
            case 'cricket_matches': {
                const m = [];
                if (item.runs_scored != null) m.push({ label: 'Runs', value: `${item.runs_scored}` });
                if (item.balls_faced != null) m.push({ label: 'Balls', value: `${item.balls_faced}` });
                if (item.runs_scored && item.balls_faced) {
                    const sr = Math.round((item.runs_scored / item.balls_faced) * 100);
                    m.push({ label: 'Strike Rate', value: `${sr}%` });
                }
                if (item.opposition_team) m.push({ label: 'Opposition', value: item.opposition_team });
                return m;
            }
            case 'rest_day':
            case 'rest_days': {
                const m = [];
                if (item.energy_level) m.push({ label: 'Energy', value: `${item.energy_level}/10` });
                if (item.fatigue_level) m.push({ label: 'Fatigue', value: `${item.fatigue_level}/10` });
                if (item.motivation_level) m.push({ label: 'Motivation', value: `${item.motivation_level}/10` });
                return m;
            }
            default:
                return [];
        }
    }

    getActivityHighlight(item) {
        switch (item.type) {
            case 'fitness':
                if (item.duration_minutes >= 60) return { icon: '🔥', text: 'Long session!' };
                if (item.intensity === 'high') return { icon: '💪', text: 'High intensity!' };
                if (item.energy_level >= 4) return { icon: '⚡', text: 'High energy!' };
                break;
            
            case 'cricket_coaching':
                if (item.duration_minutes >= 90) return { icon: '🎯', text: 'Extended practice!' };
                if (item.focus_level >= 8) return { icon: '🧠', text: 'Great focus!' };
                if (item.self_assessment_score >= 8) return { icon: '⭐', text: 'Excellent session!' };
                break;
            
            case 'cricket_match':
            case 'cricket_matches':
                const strikeRate = item.runs_scored && item.balls_faced ? 
                    (item.runs_scored / item.balls_faced) * 100 : 0;
                if (strikeRate >= 150) return { icon: '🚀', text: 'Explosive batting!' };
                if (item.runs_scored >= 50) return { icon: '🏏', text: 'Half century!' };
                if (item.post_match_satisfaction >= 8) return { icon: '😊', text: 'Great match!' };
                break;
            
            case 'rest_day':
            case 'rest_days':
                if (item.energy_level >= 8) return { icon: '🔋', text: 'Well rested!' };
                if (item.motivation_level >= 8) return { icon: '🎯', text: 'Motivated!' };
                break;
        }
        return null;
    }

    async startActivityLogging(activityType) {
        console.log(`🎤 Starting voice logging for: ${activityType}`);
        
        // Prevent multiple simultaneous calls
        if (window.isCreatingConversation) {
            console.log('⚠️ Voice logging already in progress, skipping...');
            return;
        }
        
        // Set global variable and open modal
        window.currentEntryType = activityType;
        if (typeof openVoiceModal === 'function') {
            try {
                await openVoiceModal(activityType);
            } catch (error) {
                console.error('Failed to open voice modal:', error);
                alert(`Failed to start voice logging: ${error.message}`);
            }
        } else {
            // Direct modal opening if function not available yet
            setTimeout(async () => {
                if (typeof openVoiceModal === 'function') {
                    try {
                        await openVoiceModal(activityType);
                    } catch (error) {
                        console.error('Failed to open voice modal:', error);
                        alert(`Failed to start voice logging: ${error.message}`);
                    }
                } else {
                    alert(`Voice logging for ${activityType} - please wait for page to fully load!`);
                }
            }, 100);
        }
    }

    switchTab(tabName) {
        // First, destroy any existing charts to prevent animation errors
        this.cleanupChartsOnTabSwitch();
        
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

    /**
     * Clean up Chart.js instances when switching tabs to prevent animation errors
     */
    cleanupChartsOnTabSwitch() {
        try {
            console.log('🧹 Starting comprehensive chart cleanup...');
            
            // Use the new chart system's cleanup method
            if (window.analyticsCharts && typeof window.analyticsCharts.destroyAllCharts === 'function') {
                window.analyticsCharts.destroyAllCharts();
            }
            
            console.log('✅ Chart cleanup complete');
            
        } catch (error) {
            console.warn('Error during chart cleanup:', error);
        }
    }

    async showTabContent(tabName) {
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Wait a brief moment for cleanup to complete
        await new Promise(resolve => setTimeout(resolve, 100));

        // Show selected content
        const activeContent = document.getElementById(`${tabName}-tab`);
        if (activeContent) {
            activeContent.classList.remove('hidden');
            
            // Load tab-specific data with a slight delay
            setTimeout(() => {
                this.loadTabData(tabName);
            }, 150);
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
        try {
            console.log('📊 Loading analytics data...');
            
            // Ensure charts are clean before loading
            if (window.analyticsCharts && typeof window.analyticsCharts.clearAnalyticsSection === 'function') {
                window.analyticsCharts.clearAnalyticsSection();
            }
            
            // Wait for DOM to be ready
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // Determine which analytics to load based on current selection
            const activeAnalyticsTab = document.querySelector('.analytics-nav .active');
            const analyticsType = activeAnalyticsTab ? activeAnalyticsTab.dataset.analytics : 'fitness';
            
            // Load appropriate analytics
            if (window.analyticsCharts) {
                switch (analyticsType) {
                    case 'fitness':
                        await window.analyticsCharts.renderFitnessAnalytics();
                        break;
                    case 'cricket':
                        await window.analyticsCharts.renderCricketAnalytics();
                        break;
                    case 'combined':
                        await window.analyticsCharts.renderCombinedAnalytics();
                        break;
                    default:
                        await window.analyticsCharts.renderFitnessAnalytics();
                }
            } else {
                console.warn('Analytics charts not available yet');
            }
            
        } catch (error) {
            console.error('❌ Failed to load analytics:', error);
        }
    }

    async loadEntriesData() {
        console.log('📋 Loading entries data...');
        
        try {
            const container = document.getElementById('entries-container');
            if (!container) return;

            // Show loading state
            container.innerHTML = `
                <div class="entries-loading">
                    <div class="loading"></div>
                    <p>Loading your activities...</p>
                </div>
            `;

            // Load all entry types in parallel with individual error handling
            const results = await Promise.allSettled([
                this.fetchEntries('fitness', 10),
                this.fetchEntries('cricket_coaching', 10),
                this.fetchEntries('cricket_match', 10),
                this.fetchEntries('rest_day', 10)
            ]);

            console.log("Processed results:", results);

            // Extract successful results
            const [fitnessResult, coachingResult, matchResult, restResult] = results;
            
            const fitnessEntries = fitnessResult.status === 'fulfilled' ? fitnessResult.value : [];
            const coachingEntries = coachingResult.status === 'fulfilled' ? coachingResult.value : [];
            const matchEntries = matchResult.status === 'fulfilled' ? matchResult.value : [];
            const restEntries = restResult.status === 'fulfilled' ? restResult.value : [];

            // Combine and sort all entries
            const allEntries = [
                ...fitnessEntries.map(entry => ({ ...entry, type: 'fitness' })),
                ...coachingEntries.map(entry => ({ ...entry, type: 'cricket_coaching' })),
                ...matchEntries.map(entry => ({ ...entry, type: 'cricket_match' })),
                ...restEntries.map(entry => ({ ...entry, type: 'rest_day' }))
            ];

            console.log(`✅ Loaded ${allEntries.length} total entries`);

            // Sort by creation date (newest first)
            allEntries.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            // Store entries for filtering
            this.allEntries = allEntries;
            this.currentFilter = 'all';
            this.currentSearchTerm = '';

            // Display entries
            this.displayEntries(allEntries);

            // Setup filter event listeners (only once)
            if (!this.filtersSetup) {
                this.setupEntryFilters();
                this.filtersSetup = true;
            }

        } catch (error) {
            console.error('❌ Failed to load entries:', error);
            this.showEntriesError(error.message);
        }
    }

  


    async fetchEntries(type, limit = 10) {
        try {
            const endpoints = {
                'fitness': '/api/entries/fitness',
                'cricket_coaching': '/api/entries/cricket/coaching',
                'cricket_match': '/api/entries/cricket/matches',
                'rest_day': '/api/entries/rest-days'
            };

            const response = await fetch(`${endpoints[type]}?limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            if (!response.ok) {
                throw new Error(`Failed to load ${type} entries: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log("Raw response data:", data);
            
            // Handle new response format with transcriptions
            if (data.entries && Array.isArray(data.entries)) {
                // New format: entries are directly in data.entries
                const entries = data.entries;
                const transcriptions = data.transcriptions || [];
                
                // Merge transcriptions with entries (transcriptions is now list[list[str]])
                return entries.map((entry, index) => ({
                    ...entry,
                    transcription: transcriptions[index] || []
                }));
            } else if (data.data?.entries) {
                // Legacy format: entries are in data.data.entries
                return data.data.entries || [];
            } else {
                return [];
            }
        } catch (error) {
            console.error(`❌ Error fetching ${type} entries:`, error);
            return [];
        }
    }

    displayEntries(entries) {
        const container = document.getElementById('entries-container');
        if (!container) return;

        if (entries.length === 0) {
            container.innerHTML = `
                <div class="empty-entries">
                    <div class="empty-icon">📭</div>
                    <h3>No entries found</h3>
                    <p>Start logging your activities to see them here!</p>
                </div>
            `;
            return;
        }

        const entriesHTML = entries.map(entry => this.createEntryCard(entry)).join('');
        
        container.innerHTML = `
            <div class="entries-grid">
                ${entriesHTML}
            </div>
        `;

        // Update statistics (only when showing all entries)
        if (!this.currentSearchTerm && this.currentFilter === 'all') {
            this.updateEntryStatistics();
        }

        // Animate entry cards
        this.animateEntryCards();
    }

    updateEntryStatistics() {
        if (!this.allEntries) return;

        const stats = {
            total: this.allEntries.length,
            fitness: this.allEntries.filter(e => e.type === 'fitness').length,
            cricket_coaching: this.allEntries.filter(e => e.type === 'cricket_coaching').length,
            cricket_match: this.allEntries.filter(e => e.type === 'cricket_match').length,
            rest_day: this.allEntries.filter(e => e.type === 'rest_day').length
        };

        // Update stat displays
        const totalEl = document.getElementById('total-entries');
        const fitnessEl = document.getElementById('fitness-count');
        const cricketEl = document.getElementById('cricket-count');
        const matchEl = document.getElementById('match-count');
        const restEl = document.getElementById('rest-count');

        if (totalEl) totalEl.textContent = stats.total;
        if (fitnessEl) fitnessEl.textContent = stats.fitness;
        if (cricketEl) cricketEl.textContent = stats.cricket_coaching;
        if (matchEl) matchEl.textContent = stats.cricket_match;
        if (restEl) restEl.textContent = stats.rest_day;

        // Show stats container
        const statsContainer = document.getElementById('entry-stats');
        if (statsContainer && stats.total > 0) {
            statsContainer.classList.remove('hidden');
        }

        // Add click handlers to stat cards for filtering
        this.setupStatCardFilters();
    }

    setupStatCardFilters() {
        const statCards = document.querySelectorAll('.stat-card');
        
        statCards.forEach((card, index) => {
            card.style.cursor = 'pointer';
            card.onclick = () => {
                const filters = ['all', 'fitness', 'cricket_coaching', 'cricket_match', 'rest_day'];
                const targetFilter = filters[index];
                
                // Update filter button active state
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.dataset.filter === targetFilter) {
                        btn.classList.add('active');
                    }
                });
                
                // Apply filter
                this.filterEntries(targetFilter);
            };
        });
    }

    createEntryCard(entry) {
        const icons = {
            'fitness': '🏃',
            'cricket_coaching': '🏏',
            'cricket_match': '🏆',
            'cricket_matches': '🏆',
            'rest_day': '😴'
        };

        const icon = icons[entry.type] || '📝';
        const title = this.formatActivityTitle(entry);
        const timeAgo = this.formatRelativeTime(new Date(entry.created_at));
        
        // Get key metrics based on activity type
        const metrics = this.getActivityMetrics(entry);
        const highlight = this.getActivityHighlight(entry);
        
        // Show transcription if available - take the first message for preview
        const transcriptionPreview = entry.transcription && entry.transcription.length > 0 
            ? this.getTranscriptPreview(entry.transcription[0]) 
            : '';

        return `
            <div class="entry-card ${entry.type}" onclick="window.mobileDashboard.showActivityDetails(${JSON.stringify(entry).replace(/"/g, '&quot;')})">
                <div class="entry-card-header">
                    <div class="entry-icon-container">
                        <span class="entry-icon">${icon}</span>
                    </div>
                    <div class="entry-main-info">
                        <div class="entry-title">${title}</div>
                        <div class="entry-time">${timeAgo}</div>
                    </div>
                </div>
                
                ${transcriptionPreview ? `
                    <div class="entry-transcript-preview">
                        <div class="transcript-preview-header">
                            <span class="transcript-icon">🎤</span>
                            <span class="transcript-label">What you said:</span>
                        </div>
                        <div class="transcript-preview-content">
                            "${transcriptionPreview}"
                        </div>
                    </div>
                ` : ''}
                
                ${metrics.length > 0 ? `
                    <div class="entry-metrics">
                        ${metrics.map(metric => `
                            <div class="entry-metric">
                                <span class="metric-label">${metric.label}</span>
                                <span class="metric-value">${metric.value}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${highlight ? `
                    <div class="entry-highlight">
                        <span class="highlight-icon">${highlight.icon}</span>
                        <span class="highlight-text">${highlight.text}</span>
                    </div>
                ` : ''}
                
                <div class="entry-footer">
                    <span class="entry-id">ID: ${entry.id}</span>
                    <div class="click-indicator">
                        <span>👆 Tap for details</span>
                    </div>
                </div>
            </div>
        `;
    }

    formatFitnessTitle(entry) {
        // Prefer specific exercise name, otherwise fall back to exercise_type or generic label
        const name = entry.exercise_name || entry.exercise_type || entry.fitness_type || 'Fitness';
        const formatted = name.toString().replace(/_/g, ' ');
        return `${formatted.charAt(0).toUpperCase() + formatted.slice(1)} Session`;
    }

    formatCoachingTitle(entry) {
        const type = (entry.session_type || 'Cricket').toString().replace(/_/g, ' ');
        return `${type.charAt(0).toUpperCase() + type.slice(1)} Practice`;
    }

    formatMatchTitle(entry) {
        const fmt = (entry.match_format || entry.match_type || 'Match').toString().replace(/_/g, ' ');
        return `${fmt.charAt(0).toUpperCase() + fmt.slice(1)} Performance`;
    }

    formatRestDayTitle(entry) {
        const type = (entry.rest_type || 'Rest').toString().replace(/_/g, ' ');
        return `${type.charAt(0).toUpperCase() + type.slice(1)} Day`;
    }

    getEntryDescription(entry) {
        switch (entry.type) {
            case 'fitness':
                return entry.details || entry.notes || entry.transcript?.substring(0, 100) || '';
            case 'cricket_coaching':
                return entry.what_went_well || entry.notes || entry.transcript?.substring(0, 100) || '';
            case 'cricket_match':
            case 'cricket_matches':
                return (
                    entry.key_moments?.join(', ') ||
                    entry.key_shots_played ||
                    entry.notes ||
                    entry.transcript?.substring(0, 100) || ''
                );
            case 'rest_day':
                return (
                    entry.mood_description ||
                    entry.physical_state ||
                    entry.notes ||
                    entry.transcript?.substring(0, 100) || ''
                );
            default:
                return '';
        }
    }

    getEntryTags(entry) {
        const tags = [];

        // Mental state tag
        if (entry.mental_state) {
            tags.push({ text: entry.mental_state, class: 'mental-state' });
        }

        switch (entry.type) {
            case 'fitness':
                if (entry.exercise_type) {
                    tags.push({ text: entry.exercise_type.replace(/_/g, ' '), class: 'exercise-type' });
                }
                if (entry.intensity) {
                    tags.push({ text: entry.intensity, class: 'intensity' });
                }
                break;

            case 'cricket_coaching':
                if (entry.session_type) {
                    tags.push({ text: entry.session_type.replace(/_/g, ' '), class: 'session-type' });
                }
                break;

            case 'cricket_match':
            case 'cricket_matches':
                if (entry.match_format || entry.match_type) {
                    const label = (entry.match_format || entry.match_type).toString().replace(/_/g, ' ');
                    tags.push({ text: label, class: 'match-format' });
                }
                break;

            case 'rest_day':
                if (entry.rest_type) {
                    tags.push({ text: entry.rest_type.replace(/_/g, ' '), class: 'rest-type' });
                }
                break;
        }

        return tags;
    }

    setupEntryFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Filter entries
                const filter = button.dataset.filter;
                this.filterEntries(filter);
            });
        });
        
        // Setup search functionality
        const searchInput = document.getElementById('entry-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchEntries(e.target.value);
            });
            
            // Clear search when focus is lost and input is empty
            searchInput.addEventListener('blur', (e) => {
                if (e.target.value.trim() === '') {
                    this.currentSearchTerm = '';
                    this.applyFilters();
                }
            });
        }
    }

    searchEntries(searchTerm) {
        this.currentSearchTerm = searchTerm.toLowerCase().trim();
        this.applyFilters();
    }

    filterEntries(filter) {
        this.currentFilter = filter;
        this.applyFilters();
    }

    applyFilters() {
        if (!this.allEntries) return;
        
        let filteredEntries = this.allEntries;
        
        // Apply type filter
        if (this.currentFilter !== 'all') {
            filteredEntries = filteredEntries.filter(entry => entry.type === this.currentFilter);
        }
        
        // Apply search filter
        console.log("filteredEntries", filteredEntries);
        console.log("this.currentSearchTerm", this.currentSearchTerm);
        if (this.currentSearchTerm) {
            filteredEntries = filteredEntries.filter(entry => {
                const searchableText = [
                    Array.isArray(entry.transcription) ? entry.transcription.join(' ') : entry.transcription || '',
                    entry.details || '',
                    entry.what_went_well || '',
                    entry.key_shots_played || '',
                    entry.mood_description || '',
                    entry.physical_state || '',
                    entry.mental_state || '',
                    entry.activity_type || '',
                    entry.session_type || '',
                    entry.match_type || '',
                    entry.rest_type || '',
                    entry.skills_practiced || '',
                    entry.notes || ''
                ].join(' ').toLowerCase();
                
                return searchableText.includes(this.currentSearchTerm);
            });
        }
        
        this.displayEntries(filteredEntries);
        
        // Show search results count if searching
        if (this.currentSearchTerm) {
            this.showSearchResults(filteredEntries.length, this.allEntries.length);
        }
    }

    showSearchResults(filteredCount, totalCount) {
        const searchInput = document.getElementById('entry-search-input');
        if (!searchInput) return;
        
        // Create or update search results indicator
        let resultsIndicator = document.getElementById('search-results-indicator');
        if (!resultsIndicator) {
            resultsIndicator = document.createElement('div');
            resultsIndicator.id = 'search-results-indicator';
            resultsIndicator.style.cssText = `
                font-size: 0.8rem;
                color: var(--text-secondary);
                margin-top: var(--spacing-xs);
                text-align: center;
                font-style: italic;
            `;
            searchInput.parentNode.appendChild(resultsIndicator);
        }
        
        if (filteredCount === 0) {
            resultsIndicator.textContent = `No results found for "${this.currentSearchTerm}"`;
            resultsIndicator.style.color = 'var(--error-color)';
        } else {
            resultsIndicator.textContent = `Found ${filteredCount} of ${totalCount} entries`;
            resultsIndicator.style.color = 'var(--success-color)';
        }
        
        resultsIndicator.style.display = 'block';
        
        // Hide indicator after 3 seconds if no search term
        if (!this.currentSearchTerm) {
            setTimeout(() => {
                if (resultsIndicator) {
                    resultsIndicator.style.display = 'none';
                }
            }, 3000);
        }
    }

    animateEntryCards() {
        const cards = document.querySelectorAll('.entry-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'Today';
        } else if (diffDays === 2) {
            return 'Yesterday';
        } else if (diffDays <= 7) {
            return `${diffDays - 1} days ago`;
        } else {
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
            });
        }
    }

    showEntriesError(message) {
        const container = document.getElementById('entries-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="empty-entries">
                <div class="empty-icon">❌</div>
                <h3>Error Loading Entries</h3>
                <p>${message}</p>
                <button class="btn" onclick="window.mobileDashboard.loadEntriesData()">🔄 Try Again</button>
            </div>
        `;
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

    closeActivityModal() {
        const modal = document.getElementById('activityModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    getTranscriptPreview(transcript) {
        if (!transcript || transcript.length === 0) return '';
        
        // Truncate to 100 characters and add ellipsis if longer
        const maxLength = 100;
        if (transcript.length <= maxLength) {
            return transcript;
        }
        
        return transcript.substring(0, maxLength) + '...';
    }

    getMainInfo(entry) {
        switch (entry.type) {
            case 'fitness':
                return [
                    { label: 'Duration', value: `${entry.duration_minutes || 0}min` },
                    { label: 'Intensity', value: entry.intensity || 'N/A' },
                    { label: 'Energy', value: entry.energy_level != null ? `${entry.energy_level}/10` : 'N/A' },
                    { label: 'Distance', value: entry.distance_km != null ? `${entry.distance_km}km` : 'N/A' }
                ];

            case 'cricket_coaching':
                return [
                    { label: 'Duration', value: `${entry.duration_minutes || 0}min` },
                    { label: 'Confidence', value: entry.confidence_level != null ? `${entry.confidence_level}/10` : 'N/A' },
                    { label: 'Focus', value: entry.focus_level != null ? `${entry.focus_level}/10` : 'N/A' },
                    { label: 'Self Rating', value: entry.self_assessment_score != null ? `${entry.self_assessment_score}/10` : 'N/A' }
                ];

            case 'cricket_match':
            case 'cricket_matches':
                return [
                    { label: 'Runs', value: entry.runs_scored != null ? entry.runs_scored : 'N/A' },
                    { label: 'Balls', value: entry.balls_faced != null ? entry.balls_faced : 'N/A' },
                    { label: 'Strike Rate', value: (entry.runs_scored && entry.balls_faced) ? `${Math.round((entry.runs_scored/entry.balls_faced)*100)}%` : 'N/A' },
                    { label: 'Opposition', value: entry.opposition_team || 'N/A' }
                ];

            case 'rest_day':
                return [
                    { label: 'Energy', value: entry.energy_level != null ? `${entry.energy_level}/10` : 'N/A' },
                    { label: 'Fatigue', value: entry.fatigue_level != null ? `${entry.fatigue_level}/10` : 'N/A' },
                    { label: 'Motivation', value: entry.motivation_level != null ? `${entry.motivation_level}/10` : 'N/A' },
                    { label: 'Rest Type', value: entry.rest_type ? entry.rest_type.replace(/_/g, ' ') : 'N/A' }
                ];

            default:
                return [];
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileDashboard = new MobileDashboard();
});

// Export for global access
window.MobileDashboard = MobileDashboard; 