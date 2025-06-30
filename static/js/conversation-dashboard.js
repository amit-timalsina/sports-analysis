/**
 * Conversation Analytics Dashboard
 * 
 * Features:
 * - Conversation analytics visualization
 * - Turn-by-turn conversation history
 * - Question effectiveness insights
 * - Data quality metrics
 */

class ConversationDashboard {
    constructor() {
        this.apiBaseUrl = '/api';
        this.currentUser = 'demo_user'; // TODO: Get from authentication
        this.analytics = null;
        this.conversations = [];
    }

    async init() {
        console.log('🔄 Initializing Conversation Dashboard...');
        
        try {
            await this.loadAnalytics();
            await this.loadConversations();
            this.renderDashboard();
            console.log('✅ Conversation Dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize dashboard:', error);
            this.showError('Failed to load conversation dashboard');
        }
    }

    async loadAnalytics(daysBack = 30) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/conversations/analytics?user_id=${this.currentUser}&days_back=${daysBack}`);
            const data = await response.json();
            
            if (data.success) {
                this.analytics = data.data.analytics;
                console.log('📊 Analytics loaded:', this.analytics);
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
            // Fallback to mock data for development
            this.analytics = this.getMockAnalytics();
        }
    }

    async loadConversations(limit = 10) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/conversations?user_id=${this.currentUser}&limit=${limit}`);
            const data = await response.json();
            
            if (data.success) {
                this.conversations = data.data.conversations;
                console.log('💬 Conversations loaded:', this.conversations.length);
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
            // Fallback to mock data
            this.conversations = this.getMockConversations();
        }
    }

    renderDashboard() {
        const container = document.getElementById('conversation-dashboard');
        if (!container) {
            console.warn('Conversation dashboard container not found');
            return;
        }

        container.innerHTML = `
            <div class="conversation-dashboard">
                <div class="dashboard-header">
                    <h2>🤖 Conversation Analytics</h2>
                    <div class="time-range-selector">
                        <select id="time-range" onchange="conversationDashboard.handleTimeRangeChange()">
                            <option value="7">Last 7 days</option>
                            <option value="30" selected>Last 30 days</option>
                            <option value="90">Last 90 days</option>
                        </select>
                    </div>
                </div>

                <div class="analytics-grid">
                    ${this.renderAnalyticsCards()}
                </div>

                <div class="dashboard-sections">
                    <div class="section">
                        <h3>📈 Conversation Quality Trends</h3>
                        <div id="quality-chart" class="chart-container">
                            ${this.renderQualityChart()}
                        </div>
                    </div>

                    <div class="section">
                        <h3>💬 Recent Conversations</h3>
                        <div id="conversations-list" class="conversations-list">
                            ${this.renderConversationsList()}
                        </div>
                    </div>

                    <div class="section">
                        <h3>🎯 Conversation Insights</h3>
                        <div id="insights-panel" class="insights-panel">
                            ${this.renderInsights()}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderAnalyticsCards() {
        if (!this.analytics) return '<div class="loading">Loading analytics...</div>';

        return `
            <div class="analytics-card">
                <div class="card-header">
                    <h4>Total Conversations</h4>
                    <span class="card-icon">💬</span>
                </div>
                <div class="card-value">${this.analytics.total_conversations}</div>
                <div class="card-subtitle">
                    ${this.analytics.completed_conversations} completed 
                    (${Math.round(this.analytics.completion_rate * 100)}%)
                </div>
            </div>

            <div class="analytics-card">
                <div class="card-header">
                    <h4>Avg. Turns</h4>
                    <span class="card-icon">🔄</span>
                </div>
                <div class="card-value">
                    ${this.analytics.average_turns_per_conversation?.toFixed(1) || 'N/A'}
                </div>
                <div class="card-subtitle">per conversation</div>
            </div>

            <div class="analytics-card">
                <div class="card-header">
                    <h4>Data Quality</h4>
                    <span class="card-icon">⭐</span>
                </div>
                <div class="card-value">
                    ${this.analytics.average_data_quality ? (this.analytics.average_data_quality * 100).toFixed(0) + '%' : 'N/A'}
                </div>
                <div class="card-subtitle">average quality score</div>
            </div>

            <div class="analytics-card">
                <div class="card-header">
                    <h4>Efficiency</h4>
                    <span class="card-icon">⚡</span>
                </div>
                <div class="card-value">
                    ${this.analytics.average_efficiency ? (this.analytics.average_efficiency * 100).toFixed(0) + '%' : 'N/A'}
                </div>
                <div class="card-subtitle">conversation efficiency</div>
            </div>
        `;
    }

    renderQualityChart() {
        // Simplified chart - in production, use Chart.js or similar
        const qualityScore = this.analytics?.average_data_quality || 0;
        const efficiencyScore = this.analytics?.average_efficiency || 0;

        return `
            <div class="simple-chart">
                <div class="chart-bar">
                    <div class="bar-label">Data Quality</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: ${qualityScore * 100}%"></div>
                    </div>
                    <div class="bar-value">${(qualityScore * 100).toFixed(0)}%</div>
                </div>
                <div class="chart-bar">
                    <div class="bar-label">Efficiency</div>
                    <div class="bar-container">
                        <div class="bar-fill efficiency" style="width: ${efficiencyScore * 100}%"></div>
                    </div>
                    <div class="bar-value">${(efficiencyScore * 100).toFixed(0)}%</div>
                </div>
            </div>
        `;
    }

    renderConversationsList() {
        if (!this.conversations.length) {
            return '<div class="empty-state">No conversations found</div>';
        }

        return this.conversations.map(conv => `
            <div class="conversation-item" onclick="conversationDashboard.showConversationDetails('${conv.session_id}')">
                <div class="conversation-header">
                    <div class="conversation-type">
                        ${this.getActivityTypeIcon(conv.activity_type)} ${this.formatActivityType(conv.activity_type)}
                    </div>
                    <div class="conversation-status ${conv.state}">
                        ${this.formatStatus(conv.state)}
                    </div>
                </div>
                <div class="conversation-meta">
                    <span class="turns-count">${conv.total_turns} turns</span>
                    <span class="quality-score">
                        Quality: ${conv.data_quality_score ? (conv.data_quality_score * 100).toFixed(0) + '%' : 'N/A'}
                    </span>
                    <span class="conversation-date">
                        ${new Date(conv.started_at).toLocaleDateString()}
                    </span>
                </div>
            </div>
        `).join('');
    }

    renderInsights() {
        const activityBreakdown = this.analytics?.activity_breakdown || {};
        
        return `
            <div class="insights-grid">
                <div class="insight-card">
                    <h4>📊 Activity Breakdown</h4>
                    <div class="activity-breakdown">
                        ${Object.entries(activityBreakdown).map(([type, count]) => `
                            <div class="activity-item">
                                <span class="activity-type">${this.formatActivityType(type)}</span>
                                <span class="activity-count">${count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="insight-card">
                    <h4>💡 Recommendations</h4>
                    <div class="recommendations">
                        ${this.generateRecommendations().map(rec => `
                            <div class="recommendation">${rec}</div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    async showConversationDetails(sessionId) {
        try {
            // This would call the conversation details API
            console.log('Showing details for conversation:', sessionId);
            
            // For now, show a simple modal
            alert(`Conversation Details for ${sessionId}\n\nThis feature will show:\n- Turn-by-turn conversation flow\n- AI responses and questions\n- Data extraction quality\n- User interaction patterns`);
        } catch (error) {
            console.error('Failed to load conversation details:', error);
        }
    }

    handleTimeRangeChange() {
        const select = document.getElementById('time-range');
        const daysBack = parseInt(select.value);
        
        console.log(`Changing time range to ${daysBack} days`);
        this.loadAnalytics(daysBack).then(() => {
            this.renderDashboard();
        });
    }

    // Utility methods
    getActivityTypeIcon(type) {
        const icons = {
            'fitness': '🏃',
            'cricket_coaching': '🏏',
            'cricket_match': '🥇',
            'rest_day': '😴'
        };
        return icons[type] || '📝';
    }

    formatActivityType(type) {
        return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatStatus(state) {
        const statusMap = {
            'completed': 'Completed',
            'started': 'In Progress',
            'collecting_data': 'Collecting',
            'asking_followup': 'Follow-up',
            'error': 'Error'
        };
        return statusMap[state] || state;
    }

    generateRecommendations() {
        const recommendations = [];
        
        if (this.analytics) {
            if (this.analytics.completion_rate < 0.8) {
                recommendations.push('Focus on improving conversation completion rates');
            }
            
            if (this.analytics.average_turns_per_conversation > 6) {
                recommendations.push('Consider optimizing questions to reduce conversation length');
            }
            
            if (this.analytics.average_data_quality < 0.7) {
                recommendations.push('Review data extraction accuracy and improve question clarity');
            }
        }
        
        if (recommendations.length === 0) {
            recommendations.push('Conversation quality looks good! Keep up the great work.');
        }
        
        return recommendations;
    }

    // Mock data for development
    getMockAnalytics() {
        return {
            total_conversations: 45,
            completed_conversations: 38,
            completion_rate: 0.84,
            average_turns_per_conversation: 3.2,
            average_data_quality: 0.87,
            average_efficiency: 0.92,
            activity_breakdown: {
                'fitness': 18,
                'cricket_coaching': 12,
                'cricket_match': 8,
                'rest_day': 7
            }
        };
    }

    getMockConversations() {
        return [
            {
                id: 1,
                session_id: 'session-123',
                activity_type: 'fitness',
                state: 'completed',
                total_turns: 3,
                data_quality_score: 0.89,
                started_at: new Date().toISOString()
            },
            {
                id: 2,
                session_id: 'session-124',
                activity_type: 'cricket_match',
                state: 'completed',
                total_turns: 4,
                data_quality_score: 0.92,
                started_at: new Date(Date.now() - 86400000).toISOString()
            }
        ];
    }

    showError(message) {
        console.error('Dashboard Error:', message);
        const container = document.getElementById('conversation-dashboard');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <h3>⚠️ Error Loading Dashboard</h3>
                    <p>${message}</p>
                    <button onclick="conversationDashboard.init()" class="retry-btn">
                        Retry
                    </button>
                </div>
            `;
        }
    }
}

// Global instance
const conversationDashboard = new ConversationDashboard();

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('conversation-dashboard')) {
        conversationDashboard.init();
    }
}); 