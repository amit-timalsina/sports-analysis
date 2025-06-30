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
                apiKey: 'cricket_matches'
            },
            {
                type: 'rest_day',
                icon: '😴',
                title: 'Rest Day',
                description: 'Recovery tracking',
                apiKey: 'rest_days'
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
    }

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
        const averageEnergy = summary.average_energy_level || 0;
        const improvementTrend = insights.fitness_improvement_trends?.overall_trend || 0;
        
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
            {
                label: 'Energy',
                value: `${averageEnergy.toFixed(1)}/5`,
                description: 'Average level',
                trend: averageEnergy >= 4 ? '⚡' : averageEnergy >= 3 ? '👌' : ''
            },
            {
                label: 'Form',
                value: improvementTrend >= 0 ? `+${improvementTrend.toFixed(1)}%` : `${improvementTrend.toFixed(1)}%`,
                description: 'Improvement',
                trend: improvementTrend > 0 ? '📈' : improvementTrend < -5 ? '📉' : '➡️'
            }
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
            cricket_matches: '🏆',
            rest_days: '😴'
        };

        recentActivity.innerHTML = `
            <h3>📋 Recent Activity</h3>
            <div class="recent-list">
                ${recentItems.map(item => this.createRecentActivityCard(item, activityIcons)).join('')}
                        </div>
        `;
    }

    createRecentActivityCard(item, activityIcons) {
        const icon = activityIcons[item.type] || '📝';
        const timeAgo = this.formatRelativeTime(new Date(item.created_at));
        const confidence = Math.round((item.confidence_score || 0) * 100);
        
        // Get transcript preview (first 60 characters)
        const getTranscriptPreview = (transcript) => {
            if (!transcript) return 'No transcript available';
            
            // Handle multi-turn transcripts - extract first meaningful content
            if (transcript.includes('Turn ') && transcript.includes('(conf:')) {
                const turns = transcript.split('\n\n').filter(turn => turn.trim());
                if (turns.length > 0) {
                    const firstTurn = turns[0];
                    const lines = firstTurn.split('\n');
                    const contentLines = lines.slice(1); // Skip header
                    const content = contentLines.join(' ').trim();
                    return content.length > 60 ? content.substring(0, 60) + '...' : content;
                }
            }
            
            // Single transcript
            return transcript.length > 60 ? transcript.substring(0, 60) + '...' : transcript;
        };
        
        const transcriptPreview = getTranscriptPreview(item.transcript);
        const transcriptTurnCount = item.transcript && item.transcript.includes('Turn ') ? 
            (item.transcript.match(/Turn \d+/g) || []).length : 1;

        // Get key metrics based on activity type
        const getKeyMetrics = (item) => {
            switch (item.type) {
                case 'fitness':
                    return [
                        item.duration_minutes ? `${item.duration_minutes}min` : null,
                        item.intensity ? item.intensity.charAt(0).toUpperCase() + item.intensity.slice(1) : null,
                        item.energy_level ? `Energy: ${item.energy_level}/5` : null
                    ].filter(Boolean);
                
                case 'cricket_coaching':
                    return [
                        item.duration_minutes ? `${item.duration_minutes}min` : null,
                        item.confidence_level ? `Confidence: ${item.confidence_level}/10` : null,
                        item.focus_level ? `Focus: ${item.focus_level}/10` : null
                    ].filter(Boolean);
                
                case 'cricket_matches':
                    return [
                        item.runs_scored !== null ? `${item.runs_scored} runs` : null,
                        item.balls_faced !== null ? `${item.balls_faced} balls` : null,
                        (item.runs_scored && item.balls_faced) ? `SR: ${Math.round((item.runs_scored / item.balls_faced) * 100)}%` : null
                    ].filter(Boolean);
                
                case 'rest_days':
                    return [
                        item.energy_level ? `Energy: ${item.energy_level}/10` : null,
                        item.fatigue_level ? `Fatigue: ${item.fatigue_level}/10` : null,
                        item.rest_type ? item.rest_type.replace(/_/g, ' ') : null
                    ].filter(Boolean);
                
                default:
                    return [];
            }
        };

        const metrics = getKeyMetrics(item);
        const activityTitle = this.formatActivityTitle(item);

        return `
            <div class="recent-activity-card ${item.type}" onclick="window.mobileDashboard.showActivityDetails(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                <div class="activity-card-header">
                    <div class="activity-icon-container">
                        <span class="activity-icon">${icon}</span>
                    </div>
                    <div class="activity-main-info">
                        <div class="activity-title">${activityTitle}</div>
                        <div class="activity-meta">
                            <span class="activity-time">${timeAgo}</span>
                            <span class="activity-confidence" title="Speech Recognition Confidence">${confidence}%</span>
                            ${transcriptTurnCount > 1 ? `<span class="turn-indicator" title="Multi-turn conversation">💬 ${transcriptTurnCount} turns</span>` : ''}
                        </div>
                    </div>
                </div>
                
                ${metrics.length > 0 ? `
                    <div class="activity-quick-metrics">
                        ${metrics.slice(0, 3).map(metric => `<span class="quick-metric">${metric}</span>`).join('')}
                    </div>
                ` : ''}
                
                <div class="activity-transcript-preview">
                    <div class="transcript-preview-header">
                        <span class="transcript-icon">🎤</span>
                        <span class="transcript-label">What you said:</span>
                    </div>
                    <div class="transcript-preview-content" title="${item.transcript || 'No transcript'}">${transcriptPreview}</div>
                </div>
                
                <div class="activity-card-footer">
                    <span class="activity-id">ID: ${item.id}</span>
                    <div class="click-indicator">
                        <span>👆 Tap for full details</span>
                    </div>
                </div>
            </div>
        `;
    }

    showActivityDetails(item) {
        const modal = document.getElementById('activityModal');
        const modalContent = document.getElementById('activityModalContent');
        
        const icon = this.getActivityIcon(item.type);
        const title = this.formatActivityTitle(item);
        
        // Format transcript to handle multiple turns
        const formatTranscript = (transcript) => {
            if (!transcript) return '<div class="no-transcript">No transcript available</div>';
            
            // Check if transcript contains multiple turns (has "Turn X (conf:" pattern)
            if (transcript.includes('Turn ') && transcript.includes('(conf:')) {
                // Split by double newline and format each turn
                const turns = transcript.split('\n\n').filter(turn => turn.trim());
                
                if (turns.length > 1) {
                    // Multiple turns - show conversation flow
                    const conversationHeader = `
                        <div class="conversation-summary">
                            <div class="conversation-stats">
                                <span class="turn-count">💬 ${turns.length} conversation turns</span>
                                <span class="conversation-flow">🔄 Multi-turn interaction</span>
                            </div>
                        </div>
                    `;
                    
                    const formattedTurns = turns.map((turn, index) => {
                        const lines = turn.split('\n');
                        const headerLine = lines[0];
                        const contentLines = lines.slice(1);
                        
                        // Extract confidence from header like "Turn 1 (conf: 0.95):"
                        const confMatch = headerLine.match(/conf:\s*([\d.]+)/);
                        const confidence = confMatch ? (parseFloat(confMatch[1]) * 100).toFixed(0) : 'N/A';
                        const turnNumber = index + 1;
                        
                        return `
                            <div class="transcript-turn" data-turn="${turnNumber}">
                                <div class="turn-header">
                                    <div class="turn-info">
                                        <span class="turn-number">Turn ${turnNumber}</span>
                                        <span class="turn-confidence" title="Speech Recognition Confidence">
                                            ${confidence}% confidence
                                        </span>
                                    </div>
                                    ${index === 0 ? '<span class="turn-badge initial">Initial</span>' : 
                                      index === turns.length - 1 ? '<span class="turn-badge final">Final</span>' : 
                                      '<span class="turn-badge follow-up">Follow-up</span>'}
                                </div>
                                <div class="turn-content">
                                    ${contentLines.length > 0 ? contentLines.join('<br>') : 'No additional content'}
                                </div>
                            </div>
                        `;
                    }).join('');
                    
                    return conversationHeader + '<div class="conversation-turns">' + formattedTurns + '</div>';
                } else {
                    // Single turn from multi-turn format
                    const lines = turns[0].split('\n');
                    const headerLine = lines[0];
                    const contentLines = lines.slice(1);
                    const confMatch = headerLine.match(/conf:\s*([\d.]+)/);
                    const confidence = confMatch ? (parseFloat(confMatch[1]) * 100).toFixed(0) : 'N/A';
                    
                    return `
                        <div class="single-turn-conversation">
                            <div class="turn-header single">
                                <span class="turn-number">Single Turn</span>
                                <span class="turn-confidence">${confidence}% confidence</span>
                            </div>
                            <div class="turn-content single">
                                ${contentLines.length > 0 ? contentLines.join('<br>') : 'No additional content'}
                            </div>
                        </div>
                    `;
                }
            } else {
                // Legacy single transcript format
                return `
                    <div class="transcript-single legacy">
                        <div class="single-transcript-header">
                            <span class="transcript-type">📝 Direct Transcript</span>
                            <span class="transcript-note">Single recording</span>
                        </div>
                        <div class="single-transcript-content">${transcript}</div>
                    </div>
                `;
            }
        };
        
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
                            <span class="detail-value">${item.session_id || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Confidence Score:</span>
                            <span class="detail-value">${Math.round((item.confidence_score || 0) * 100)}%</span>
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
                        ${formatTranscript(item.transcript)}
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
                            <span class="detail-value">${item.type}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">User ID:</span>
                            <span class="detail-value">${item.user_id || 'demo_user'}</span>
                        </div>
                        ${item.updated_at ? `
                        <div class="detail-item">
                            <span class="detail-label">Last Updated:</span>
                            <span class="detail-value">${this.formatDateTime(item.updated_at)}</span>
                        </div>
                        ` : ''}
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
            case 'fitness':
                const metrics = [];
                if (item.duration_minutes) {
                    metrics.push({ label: 'Duration', value: `${item.duration_minutes} min` });
                }
                if (item.intensity) {
                    metrics.push({ label: 'Intensity', value: item.intensity.charAt(0).toUpperCase() + item.intensity.slice(1) });
                }
                if (item.energy_level) {
                    metrics.push({ label: 'Energy Level', value: `${item.energy_level}/5` });
                }
                if (item.distance_km) {
                    metrics.push({ label: 'Distance', value: `${item.distance_km} km` });
                }
                return metrics;
            
            case 'cricket_coaching':
                const coachingMetrics = [];
                if (item.duration_minutes) {
                    coachingMetrics.push({ label: 'Session Length', value: `${item.duration_minutes} min` });
                }
                if (item.focus_level) {
                    coachingMetrics.push({ label: 'Focus Level', value: `${item.focus_level}/10` });
                }
                if (item.confidence_level) {
                    coachingMetrics.push({ label: 'Confidence', value: `${item.confidence_level}/10` });
                }
                if (item.self_assessment_score) {
                    coachingMetrics.push({ label: 'Self Rating', value: `${item.self_assessment_score}/10` });
                }
                return coachingMetrics;
            
            case 'cricket_matches':
                const matchMetrics = [];
                if (item.runs_scored !== null && item.runs_scored !== undefined) {
                    matchMetrics.push({ label: 'Runs Scored', value: `${item.runs_scored}` });
                }
                if (item.balls_faced !== null && item.balls_faced !== undefined) {
                    matchMetrics.push({ label: 'Balls Faced', value: `${item.balls_faced}` });
                }
                if (item.runs_scored && item.balls_faced) {
                    const strikeRate = Math.round((item.runs_scored / item.balls_faced) * 100);
                    matchMetrics.push({ label: 'Strike Rate', value: `${strikeRate}%` });
                }
                if (item.opposition_strength) {
                    matchMetrics.push({ label: 'Opposition', value: `${item.opposition_strength}/10` });
                }
                return matchMetrics;
            
            case 'rest_days':
                const restMetrics = [];
                if (item.energy_level) {
                    restMetrics.push({ label: 'Energy Level', value: `${item.energy_level}/10` });
                }
                if (item.fatigue_level) {
                    restMetrics.push({ label: 'Fatigue Level', value: `${item.fatigue_level}/10` });
                }
                if (item.motivation_level) {
                    restMetrics.push({ label: 'Motivation', value: `${item.motivation_level}/10` });
                }
                if (item.rest_type) {
                    const restTypeFormatted = item.rest_type.replace(/_/g, ' ').split(' ').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' ');
                    restMetrics.push({ label: 'Rest Type', value: restTypeFormatted });
                }
                return restMetrics;
            
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
            
            case 'cricket_matches':
                const strikeRate = item.runs_scored && item.balls_faced ? 
                    (item.runs_scored / item.balls_faced) * 100 : 0;
                if (strikeRate >= 150) return { icon: '🚀', text: 'Explosive batting!' };
                if (item.runs_scored >= 50) return { icon: '🏏', text: 'Half century!' };
                if (item.post_match_satisfaction >= 8) return { icon: '😊', text: 'Great match!' };
                break;
            
            case 'rest_days':
                if (item.energy_level >= 8) return { icon: '🔋', text: 'Well rested!' };
                if (item.motivation_level >= 8) return { icon: '🎯', text: 'Motivated!' };
                break;
        }
        return null;
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

            const response = await fetch(`${endpoints[type]}?limit=${limit}`);
            if (!response.ok) {
                throw new Error(`Failed to load ${type} entries: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            return data.data?.entries || [];
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
            'rest_day': '😴'
        };

        const icon = icons[entry.type] || '📝';
        const title = this.formatActivityTitle(entry);
        const timeAgo = this.formatRelativeTime(new Date(entry.created_at));
        
        // Get key metrics based on activity type
        const metrics = this.getActivityMetrics(entry);
        const highlight = this.getActivityHighlight(entry);

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
                    <div class="entry-confidence">
                        ${Math.round((entry.confidence_score || 0) * 100)}%
                    </div>
                </div>
                
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
        const type = (entry.fitness_type || 'fitness').replace(/_/g, ' ');
        return `${type.charAt(0).toUpperCase() + type.slice(1)} Session`;
    }

    formatCoachingTitle(entry) {
        const type = (entry.session_type || 'cricket').replace(/_/g, ' ');
        return `${type.charAt(0).toUpperCase() + type.slice(1)} Practice`;
    }

    formatMatchTitle(entry) {
        const type = (entry.match_type || 'match').charAt(0).toUpperCase() + (entry.match_type || 'match').slice(1);
        return `${type} Performance`;
    }

    formatRestDayTitle(entry) {
        const type = (entry.rest_type || 'rest').replace(/_/g, ' ');
        return `${type.charAt(0).toUpperCase() + type.slice(1)} Day`;
    }

    getMainInfo(entry) {
        switch (entry.type) {
            case 'fitness':
                return [
                    { label: 'Duration', value: `${entry.duration_minutes || 0}min` },
                    { label: 'Intensity', value: entry.intensity || 'N/A' },
                    { label: 'Energy', value: `${entry.energy_level || 0}/5` },
                    { label: 'Distance', value: entry.distance_km ? `${entry.distance_km}km` : 'N/A' }
                ];
            
            case 'cricket_coaching':
                return [
                    { label: 'Duration', value: `${entry.duration_minutes || 0}min` },
                    { label: 'Confidence', value: `${entry.confidence_level || 0}/10` },
                    { label: 'Focus', value: `${entry.focus_level || 0}/10` },
                    { label: 'Self Rating', value: `${entry.self_assessment_score || 0}/10` }
                ];
            
            case 'cricket_match':
                return [
                    { label: 'Runs', value: entry.runs_scored !== null ? entry.runs_scored : 'N/A' },
                    { label: 'Balls', value: entry.balls_faced !== null ? entry.balls_faced : 'N/A' },
                    { label: 'Opposition', value: `${entry.opposition_strength || 0}/10` },
                    { label: 'Satisfaction', value: `${entry.post_match_satisfaction || 0}/10` }
                ];
            
            case 'rest_day':
                return [
                    { label: 'Energy', value: `${entry.energy_level || 0}/10` },
                    { label: 'Fatigue', value: `${entry.fatigue_level || 0}/10` },
                    { label: 'Motivation', value: `${entry.motivation_level || 0}/10` },
                    { label: 'Soreness', value: entry.soreness_level ? `${entry.soreness_level}/10` : 'N/A' }
                ];
            
            default:
                return [];
        }
    }

    getEntryDescription(entry) {
        switch (entry.type) {
            case 'fitness':
                return entry.details || entry.transcript?.substring(0, 100) || '';
            case 'cricket_coaching':
                return entry.what_went_well || entry.transcript?.substring(0, 100) || '';
            case 'cricket_match':
                return entry.key_shots_played || entry.transcript?.substring(0, 100) || '';
            case 'rest_day':
                return entry.mood_description || entry.physical_state || entry.transcript?.substring(0, 100) || '';
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
        
        // Type-specific tags
        switch (entry.type) {
            case 'fitness':
                if (entry.duration_minutes) {
                    tags.push({ text: `${entry.duration_minutes}min`, class: 'duration' });
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
                if (entry.match_type) {
                    tags.push({ text: entry.match_type, class: 'match-type' });
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
        if (this.currentSearchTerm) {
            filteredEntries = filteredEntries.filter(entry => {
                const searchableText = [
                    entry.transcript || '',
                    entry.details || '',
                    entry.what_went_well || '',
                    entry.key_shots_played || '',
                    entry.mood_description || '',
                    entry.physical_state || '',
                    entry.mental_state || '',
                    entry.fitness_type || '',
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
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileDashboard = new MobileDashboard();
});

// Export for global access
window.MobileDashboard = MobileDashboard; 