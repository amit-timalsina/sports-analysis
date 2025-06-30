# Personal Cricket & Fitness Tracker - PRD

## Overview
A comprehensive tracking and analytics platform designed for a 15-year-old cricket player in Nepal to monitor fitness activities, cricket coaching sessions, and match performance with AI-powered insights. **Core Innovation: Voice-based data entry with LLM conversion to structured data.**

## Target User
- **Primary User**: 15-year-old cricket player in Nepal (self-motivated, daily activities)
- **Use Case**: Personal development tracking, performance analysis, and progress monitoring

## Core Value Proposition
- **Effortless Tracking**: Voice-based logging with intelligent data structuring
- **Deep Insights**: AI-powered analytics with cricket knowledge base access
- **Tactical + Motivational**: Both encouragement and technical cricket advice
- **Local-First**: Works offline with local data storage

## Data Collection Strategy

### Voice Interface Approach - MVP Specifications
- **Structured Q&A Flow**: Sequential questions for fitness then cricket activities
- **Immediate Clarification**: Ask follow-up questions immediately for unclear input
- **Visual Data Validation**: Show structured data in user-friendly format + voice corrections
- **Flexible Session Length**: Support both quick (2-3 min) and detailed (5-10 min) sessions
- **Separate Activity Tracking**: Fitness and cricket as separate timestamped entries
- **Rest Day Logging**: Explicitly track and log rest days

### Data Collection Requirements

### Group 1: Fitness Tracking
**Core Data Points:**
- **Activity Type**: 
  - Running (distance, duration, pace, route)
  - Gym (exercises, sets, reps, weights, duration)
  - Other (free-text description for flexibility)
- **Performance Metrics**:
  - Duration
  - Intensity level (1-10 scale)
  - Physical fatigue level (1-10 scale)
- **Mental State**: 
  - Motivation level (1-10)
  - Focus level (1-10)
  - Overall mood (happy, neutral, frustrated, etc.)
  - Free-text notes

### Group 2: Cricket Coaching Sessions
**Core Data Points:**
- **Session Type**:
  - Batting drills (specific drills practiced)
  - Wicket keeping drills (specific techniques)
  - Netting sessions (focus areas)
  - Personal coaching (coach name, focus areas)
  - Team practice
  - Other (free-text)
- **Performance Assessment**:
  - What went well (free-text + tags)
  - Areas for improvement (free-text + tags)
  - Coach feedback (if available)
  - Self-assessment score (1-10)
- **Technical Focus**:
  - Skills practiced (dropdown + custom)
  - Time spent on each skill
  - Difficulty level of exercises
- **Mental State**:
  - Confidence level (1-10)
  - Focus during session (1-10)
  - Learning satisfaction (1-10)
  - Frustration points (free-text)

### Group 3: Cricket Match Performance
**Core Data Points:**
- **Match Context**:
  - Match type (practice, tournament, school, club)
  - Opposition strength (1-10)
  - Conditions (weather, pitch)
  - Role in team (batting order, keeping position)

- **Batting Statistics**:
  - Runs scored
  - Balls faced
  - Boundaries (4s/6s)
  - How out (if applicable)
  - Strike rate
  - Key shots played well
  - Mistakes made

- **Wicket Keeping Statistics**:
  - Catches taken/dropped
  - Stumpings
  - Byes conceded
  - Key moments (good saves, mistakes)
  - Communication with bowlers

- **Mental State**:
  - Pre-match nerves (1-10)
  - Focus during batting (1-10)
  - Focus during keeping (1-10)
  - Post-match satisfaction (1-10)
  - Key mental challenges faced

### Group 4: Rest Days
**Core Data Points:**
- **Rest Type**: Complete rest, active recovery, injury recovery
- **Mental State**: Mood, motivation levels, reflection on training
- **Physical State**: Soreness, fatigue levels, energy
- **Notes**: Thoughts about training, goals, concerns

## Core Features (MVP)

### 1. Voice-Based Data Entry
- **Structured Q&A**: Sequential voice prompts for fitness → cricket → rest days
- **Natural Language Processing**: Convert voice responses to structured data
- **Immediate Clarification**: Ask follow-up questions for unclear responses
- **Visual Confirmation**: Display structured data in user-friendly cards/forms
- **Voice Corrections**: Allow voice-based corrections to displayed data
- **Offline Processing**: Works without internet connection
- **Flexible Timing**: Support both quick and detailed logging sessions

### 2. Analytics Dashboard
- **Progress Tracking**: Visual charts showing improvement over time
- **Multi-Pattern Recognition**: 
  - Fitness-performance correlations
  - Mental state impact analysis
  - Skill progression tracking
  - Training load vs performance
- **Comparative Analysis**: Week-over-week, month-over-month comparisons
- **Rest Day Analysis**: Impact of rest on subsequent performance

### 3. AI Chat Interface with Comprehensive Knowledge Base
- **Knowledge Scope**: 
  - Basic to advanced cricket techniques
  - Tactical analysis and strategy
  - Biomechanics and movement patterns
  - Mental game and sports psychology
- **Knowledge Sources**:
  - Cricket coaching manuals
  - Professional player insights
  - Sports science research
  - Live web search for latest information
- **Recommendation Types**:
  - Technique adjustments
  - Training schedule modifications
  - Mental preparation strategies
  - Recovery and rest optimization

### 4. Insights & Reports
- **Comprehensive Pattern Analysis**:
  - Fitness-cricket performance correlations
  - Mental state impact on performance
  - Skill progression trends
  - Training load optimization
- **Actionable Recommendations**: 
  - Technical improvements
  - Training adjustments
  - Mental preparation
  - Recovery strategies
- **Weekly/Monthly Summaries**: Automated comprehensive reports

## Technical Specifications

### Technology Stack (MVP)

#### Core Stack
- **Backend Framework**: FastAPI (modern, async Python web framework)
- **Frontend Technology**: HTMX (for interactive, server-driven UI)
- **Template Engine**: Jinja2 (for server-side HTML rendering)
- **Future Migration**: Native mobile app post-MVP

#### Voice Processing Pipeline
- **Speech-to-Text**: OpenAI Whisper API (primary)
- **Local STT Evaluation**: Planned for v1 (offline capability)
- **Real-time Audio**: WebSocket connections for streaming voice data
- **Voice Activity Detection**: Custom VAD for optimal voice processing

#### AI/LLM Integration
- **Primary LLM**: OpenAI GPT models with structured output feature
- **Structured Data Extraction**: OpenAI's JSON mode for consistent data formatting
- **Knowledge Base**: RAG (Retrieval Augmented Generation) with cricket knowledge
- **Chat Interface**: WebSocket-based conversational AI with streaming responses

#### Database Options
- **Recommendation**: **PostgreSQL** for better long-term analytics capabilities
  - Pros: Strong ACID compliance, excellent for analytics, JSON support
  - Cons: More complex setup, but worth it for data integrity
- **Alternative**: MongoDB for rapid prototyping
  - Pros: Flexible schema, natural JSON storage
  - Cons: Less mature analytics ecosystem

#### Architecture Pattern
- **Local-First Design**: Data stored locally with optional cloud sync
- **Real-time Communication**: WebSocket connections for voice and data
- **Progressive Enhancement**: Offline-capable with online enhancements

### Voice Processing Architecture
- **Structured Q&A Engine**: Guided conversation flow for data collection
- **LLM Integration**: Convert natural language responses to structured data
- **Clarification System**: Immediate follow-up question generation
- **Context Awareness**: Understand cricket and fitness terminology

### Data Storage Strategy
- **Local-First Architecture**: Primary storage on device
- **Separate Entity Structure**: Fitness, cricket, rest days as distinct timestamped entries
- **Structured Data**: Optimized for analytics and pattern recognition
- **Historical Preservation**: Long-term data retention for trend analysis

### AI/ML Components
- **Natural Language Processing**: Voice-to-data conversion with clarification
- **Comprehensive Cricket Knowledge Base**: All levels of cricket information
- **Multi-Source Knowledge Integration**: Manuals, research, web search
- **Advanced Pattern Recognition**: Multiple correlation analysis
- **Comprehensive Recommendation Engine**: Technical, tactical, and mental advice

### Knowledge Base Sources
- Cricket coaching manuals and certifications
- Professional player interviews and insights
- Sports science and biomechanics research
- Sports psychology and mental game resources
- Live web search for current cricket trends and techniques
- Fitness and training methodology research

## Implementation Roadmap

### Phase 1: Core MVP (Weeks 1-4)
1. **Streamlit Frontend Setup**
   - Basic dashboard with logging buttons
   - Audio recording components
   - Data display cards

2. **Voice Processing Pipeline**
   - OpenAI Whisper API integration
   - Structured Q&A flow implementation
   - Basic data validation interface

3. **Database Setup**
   - PostgreSQL schema design
   - Local-first storage with SQLite fallback
   - Basic CRUD operations

4. **Core User Stories Implementation**
   - Daily fitness logging (Story 1.1)
   - Cricket session logging (Story 1.2)
   - Data confirmation interface (Story 2.1)

### Phase 2: Analytics & AI (Weeks 5-8)
1. **Analytics Dashboard**
   - Progress visualization
   - Basic pattern recognition
   - Weekly/monthly summaries

2. **AI Chat Interface**
   - OpenAI integration with structured output
   - Cricket knowledge base setup
   - Basic conversational insights

### Phase 3: Advanced Features (Weeks 9-12)
1. **Match Performance Logging**
2. **Rest Day Tracking**
3. **Advanced Analytics**
4. **Knowledge Base Enhancement**

## User Experience Flow

### Primary User Journey (Daily Logging)
*Reference: See detailed user stories in `User_Stories_and_Wireframes.md`*

1. **App Launch** → Dashboard shows today's logging status
2. **Activity Selection** → Tap fitness/cricket/match/rest day
3. **Voice Logging** → Structured Q&A with natural responses
4. **Data Confirmation** → Visual summary with voice corrections
5. **Save & Insights** → Data stored, immediate feedback provided

### Secondary User Journey (Analytics Review)
1. **Progress Review** → Weekly/monthly dashboard view
2. **AI Chat** → Ask questions about performance patterns
3. **Recommendations** → Receive actionable advice
4. **Goal Setting** → Adjust focus areas based on insights

## Success Metrics
- **Data Quality**: Accuracy of voice-to-data conversion
- **User Engagement**: Frequency and consistency of voice logging
- **Insight Value**: Usefulness of generated analytics and recommendations
- **Knowledge Accuracy**: Factual correctness of cricket advice
- **Pattern Recognition**: Accuracy of identified correlations and trends
- **MVP Adoption**: Daily active usage and session completion rates

---

## Next Phase: Technical Implementation

### Immediate Next Steps:
1. **Environment Setup**: Python virtual environment, Streamlit installation
2. **Database Schema Design**: PostgreSQL tables for fitness/cricket/rest data
3. **Voice Processing Prototype**: OpenAI Whisper integration test
4. **Streamlit UI Prototype**: Basic dashboard and voice recording interface
5. **User Story Implementation**: Start with Story 1.1 (Daily Fitness Logging)

### File References:
- **Detailed User Stories**: `User_Stories_and_Wireframes.md`
- **UI Wireframes**: Referenced in user stories document
- **Technical Implementation**: Ready to begin with defined tech stack 