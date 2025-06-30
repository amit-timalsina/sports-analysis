# User Stories & Wireframes - Cricket Fitness Tracker

## Core User Personas

### Primary User: Arpan (15-year-old cricket player)
- **Goals**: Track progress, improve performance, get insights
- **Tech Comfort**: Moderate (smartphone user, social media savvy)
- **Usage Pattern**: Daily logging after activities, weekly review of progress
- **Motivation**: Wants to make it to district/national teams

## User Stories

### Epic 1: Daily Activity Logging

#### Story 1.1: Daily Fitness Logging
**As Ramesh, I want to log my daily fitness activities through voice so that I can track my physical preparation without spending much time typing.**

**Acceptance Criteria:**
- User can start a voice session with "Log Fitness" button
- System asks structured questions about fitness activity
- User can speak naturally in response to each question
- System asks clarifying questions if response is unclear
- System shows structured data for confirmation before saving
- User can make voice corrections to displayed data
- Session completes in 2-5 minutes

**User Journey:**
1. Opens app → Sees "Log Today's Activities" dashboard
2. Taps "Log Fitness" button
3. Hears: "What type of fitness activity did you do today?"
4. Speaks: "I went running for 30 minutes around the school ground"
5. System asks: "How would you rate your intensity level from 1 to 10?"
6. Speaks: "I'd say 7, it was pretty intense"
7. System asks: "How was your mental state during the run?"
8. Speaks: "I felt motivated and focused, maybe 8 out of 10"
9. System shows structured data card for confirmation
10. User says "Looks good" or makes corrections
11. Data saved with timestamp

#### Story 1.2: Cricket Coaching Session Logging
**As Ramesh, I want to log my cricket coaching sessions in detail so that I can track my skill development and identify areas for improvement.**

**Acceptance Criteria:**
- User can log different types of cricket sessions (batting, keeping, net practice)
- System captures technical details and performance assessment
- User can describe what went well and what needs improvement
- System stores coach feedback if available
- Mental state and confidence levels are tracked

**User Journey:**
1. Taps "Log Cricket Session"
2. System asks: "What type of cricket session did you have today?"
3. Speaks: "I had batting practice with coach Sharma"
4. System asks: "Which specific batting drills did you practice?"
5. Speaks: "We worked on front foot drives and pull shots for about 45 minutes"
6. System asks: "What went well in today's session?"
7. Speaks: "My timing on the drives was much better, I was hitting the ball cleanly"
8. System asks: "What areas need improvement?"
9. Speaks: "I'm still struggling with the pull shot, getting out of position"
10. System asks: "How confident did you feel during the session?"
11. Speaks: "Pretty confident, maybe 7 out of 10"
12. System shows structured summary for confirmation
13. Data saved with timestamp and linked to any fitness session from same day

#### Story 1.3: Match Performance Logging
**As Ramesh, I want to log my match performance in detail so that I can analyze my game and identify patterns in my performance.**

**Acceptance Criteria:**
- User can log both batting and wicket-keeping statistics
- System captures match context (opposition, conditions, etc.)
- Mental state before, during, and after match is recorded
- Key moments and decisions are captured

#### Story 1.4: Rest Day Logging
**As Ramesh, I want to log my rest days so that I can track how recovery affects my performance.**

**Acceptance Criteria:**
- User can explicitly log rest days
- System captures rest type (complete rest, active recovery, injury)
- Physical and mental state during rest is recorded
- User can add reflections about training and goals

### Epic 2: Data Validation & Correction

#### Story 2.1: Visual Data Confirmation
**As Ramesh, I want to see my spoken data in a clear, visual format so that I can verify the system understood me correctly.**

**Acceptance Criteria:**
- Structured data is displayed in easy-to-read cards
- Visual elements use icons and colors for quick comprehension
- Technical terms are explained with simple tooltips
- Data is grouped logically (activity details, performance metrics, mental state)

**UI Flow:**
```
┌─────────────────────────────────────┐
│  🏃 FITNESS SESSION SUMMARY         │
├─────────────────────────────────────┤
│  Activity: Running                  │
│  Duration: 30 minutes               │
│  Intensity: 7/10 ⭐⭐⭐⭐⭐⭐⭐      │
│  Location: School ground            │
├─────────────────────────────────────┤
│  💭 MENTAL STATE                    │
│  Motivation: 8/10                   │
│  Focus: 8/10                        │
│  Mood: Motivated                    │
├─────────────────────────────────────┤
│  [✅ Looks Good] [🎤 Make Changes]   │
└─────────────────────────────────────┘
```

#### Story 2.2: Voice-Based Corrections
**As Ramesh, I want to make corrections to my data using voice so that I don't have to type or navigate complex forms.**

**Acceptance Criteria:**
- User can tap "Make Changes" and speak corrections
- System identifies which field needs correction
- System applies correction and shows updated data
- User can make multiple corrections in one session

### Epic 3: Analytics & Insights

#### Story 3.1: Progress Dashboard
**As Ramesh, I want to see my progress over time so that I can stay motivated and identify improvements.**

**Acceptance Criteria:**
- Visual charts show fitness and cricket progress trends
- Weekly and monthly views available
- Key metrics highlighted (runs scored, fitness consistency, mental state trends)
- Achievements and milestones are celebrated

**Dashboard Layout:**
```
┌─────────────────────────────────────┐
│  📊 THIS WEEK'S OVERVIEW            │
├─────────────────────────────────────┤
│  🏃 Fitness: 5/7 days completed     │
│  🏏 Cricket: 4 sessions              │
│  😊 Avg Mental State: 7.2/10        │
├─────────────────────────────────────┤
│  📈 TRENDING UP                     │
│  • Batting confidence (+1.5)        │
│  • Fitness consistency (+2 days)    │
│                                     │
│  ⚠️  NEEDS ATTENTION                │
│  • Pull shot technique              │
│  • Recovery after intense sessions  │
└─────────────────────────────────────┘
```

#### Story 3.2: AI Chat Interface
**As Ramesh, I want to ask questions about my performance and get intelligent insights so that I can understand my data better.**

**Acceptance Criteria:**
- User can ask natural language questions about performance
- AI provides insights based on actual data
- AI offers cricket-specific advice and encouragement
- Responses include data visualizations when helpful

**Chat Flow:**
```
User: "How has my batting improved this month?"

AI: "Great question! Looking at your data, I can see some positive trends:

📈 Your batting confidence has increased from 6.2/10 to 7.8/10
🏏 You're scoring runs more consistently (avg 15 runs vs 8 last month) 
💪 Your fitness sessions are 85% consistent this month vs 60% last month

The data shows a clear correlation between your fitness consistency and batting performance. When you complete your fitness sessions, your batting confidence averages 8.1/10 vs 6.8/10 when you skip fitness.

💡 Suggestion: Keep up the fitness routine - it's clearly helping your batting!"
```

### Epic 4: System Navigation & Setup

#### Story 4.1: First-Time Setup
**As Ramesh, I want to set up my profile quickly so that I can start logging activities immediately.**

**Acceptance Criteria:**
- Simple onboarding with cricket position, fitness level, goals
- Voice test to ensure microphone works properly
- Sample data entry to demonstrate the process
- Privacy settings explanation

#### Story 4.2: Daily App Launch
**As Ramesh, I want to quickly access today's logging options so that I can record my activities without navigation delays.**

**Main Dashboard:**
```
┌─────────────────────────────────────┐
│  🏏 CRICKET FITNESS TRACKER         │
├─────────────────────────────────────┤
│  📅 Today - March 15, 2024          │
│                                     │
│  🎤 LOG TODAY'S ACTIVITIES           │
│  ┌─────────────┐ ┌─────────────┐    │
│  │ 🏃 FITNESS  │ │ 🏏 CRICKET  │    │
│  │ Not logged  │ │ Not logged  │    │
│  └─────────────┘ └─────────────┘    │
│  ┌─────────────┐ ┌─────────────┐    │
│  │ 😴 REST DAY │ │ 🏆 MATCH    │    │
│  │ Not logged  │ │ Not logged  │    │
│  └─────────────┘ └─────────────┘    │
├─────────────────────────────────────┤
│  📊 QUICK STATS                     │
│  This week: 🏃 4/7 days 🏏 3 sessions │
├─────────────────────────────────────┤
│  [📈 View Progress] [🤖 Ask AI]     │
└─────────────────────────────────────┘
```

## Technical User Stories

### Epic 5: Voice Processing

#### Story 5.1: Speech-to-Text Conversion
**As a system, I need to convert user's voice input to text accurately so that I can process their responses.**

**Technical Acceptance Criteria:**
- Integrates with OpenAI Whisper API for voice conversion
- Handles background noise and unclear speech
- Supports offline processing for future versions
- Provides confidence scores for transcription quality

#### Story 5.2: Structured Data Extraction
**As a system, I need to extract structured data from natural language responses so that I can store and analyze the information.**

**Technical Acceptance Criteria:**
- Uses OpenAI's structured output feature
- Defines JSON schemas for fitness, cricket, and rest day data
- Handles incomplete or ambiguous responses
- Generates appropriate follow-up questions

## UI Wireframes

### 1. Main Dashboard (Mobile-First Streamlit)
```
┌─────────────────────────────────────┐
│  ☰ Menu    🏏 Cricket Tracker   ⚙️   │
├─────────────────────────────────────┤
│                                     │
│  👋 Hi Ramesh!                      │
│  📅 Today is March 15, 2024         │
│                                     │
│  🎤 LOG TODAY'S ACTIVITIES           │
│                                     │
│  ┌─────────────┐ ┌─────────────┐    │
│  │    🏃       │ │    🏏       │    │
│  │  FITNESS    │ │  CRICKET    │    │
│  │ [TAP TO LOG]│ │ [TAP TO LOG]│    │
│  └─────────────┘ └─────────────┘    │
│                                     │
│  ┌─────────────┐ ┌─────────────┐    │
│  │    😴       │ │    🏆       │    │
│  │ REST DAY    │ │   MATCH     │    │
│  │ [TAP TO LOG]│ │ [TAP TO LOG]│    │
│  └─────────────┘ └─────────────┘    │
│                                     │
│  📊 THIS WEEK'S PROGRESS            │
│  ▓▓▓▓░░░ 4/7 Fitness Days          │
│  ▓▓▓░░░░ 3/7 Cricket Sessions      │
│                                     │
│  [📈 VIEW ANALYTICS] [🤖 ASK AI]    │
│                                     │
└─────────────────────────────────────┘
```

### 2. Voice Logging Interface
```
┌─────────────────────────────────────┐
│  ← Back      🏃 FITNESS LOGGING     │
├─────────────────────────────────────┤
│                                     │
│  🎤 LISTENING...                    │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │  "What type of fitness          │ │
│  │   activity did you do today?"   │ │
│  └─────────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │  🔴 [RECORDING]                 │ │
│  │  ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿   │ │
│  └─────────────────────────────────┘ │
│                                     │
│  💬 You said:                       │
│  "I went running for 30 minutes     │
│   around the school ground"         │
│                                     │
│  [🎤 RE-RECORD] [✅ CONTINUE]       │
│                                     │
│  Progress: ●●○○○ (2/5 questions)    │
│                                     │
└─────────────────────────────────────┘
```

### 3. Data Confirmation Screen
```
┌─────────────────────────────────────┐
│  ← Back    📝 CONFIRM YOUR DATA     │
├─────────────────────────────────────┤
│                                     │
│  🏃 FITNESS SESSION SUMMARY         │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ Activity: Running               │ │
│  │ Duration: 30 minutes            │ │
│  │ Location: School ground         │ │
│  │ Intensity: 7/10 ⭐⭐⭐⭐⭐⭐⭐     │ │
│  │ Physical Fatigue: 6/10          │ │
│  └─────────────────────────────────┘ │
│                                     │
│  💭 MENTAL STATE                    │
│  ┌─────────────────────────────────┐ │
│  │ Motivation: 8/10                │ │
│  │ Focus: 8/10                     │ │
│  │ Mood: Motivated                 │ │
│  │ Notes: "Felt great today!"      │ │
│  └─────────────────────────────────┘ │
│                                     │
│  [🎤 MAKE CHANGES] [✅ SAVE DATA]   │
│                                     │
└─────────────────────────────────────┘
```

### 4. Analytics Dashboard
```
┌─────────────────────────────────────┐
│  ← Back      📊 YOUR PROGRESS       │
├─────────────────────────────────────┤
│                                     │
│  📈 PERFORMANCE TRENDS              │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │     Batting Confidence          │ │
│  │  10│    ·                       │ │
│  │   8│  ·   ·                     │ │
│  │   6│·       ·                   │ │
│  │   4│                            │ │
│  │    └─────────────────────────    │ │
│  │     W1  W2  W3  W4  (This Month)│ │
│  └─────────────────────────────────┘ │
│                                     │
│  🏆 ACHIEVEMENTS THIS WEEK          │
│  ✅ 5 days fitness streak           │
│  ✅ Improved pull shot technique    │
│  ✅ Mental state avg above 7        │
│                                     │
│  ⚠️  AREAS TO FOCUS                 │
│  • Consistency in morning runs     │
│  • Wicket keeping concentration    │
│                                     │
│  [📊 DETAILED ANALYTICS]            │
│                                     │
└─────────────────────────────────────┘
```

### 5. AI Chat Interface
```
┌─────────────────────────────────────┐
│  ← Back        🤖 ASK AI            │
├─────────────────────────────────────┤
│                                     │
│  💬 CHAT HISTORY                    │
│                                     │
│  🤖: Hi Ramesh! I've analyzed your  │
│      data. How can I help you today?│
│                                     │
│  👤: How has my batting improved     │
│      this month?                    │
│                                     │
│  🤖: Great question! Your batting   │
│      confidence increased from 6.2  │
│      to 7.8 this month. I notice    │
│      your fitness consistency       │
│      correlates with better batting.│
│                                     │
│      [View Chart] [Tell me more]    │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ 🎤 Ask me anything about your   │ │
│  │    performance...               │ │
│  │ [TAP TO SPEAK]                  │ │
│  └─────────────────────────────────┘ │
│                                     │
│  Quick questions:                   │
│  • What should I focus on?          │
│  • How are my trends?               │
│  • Training tips for next week?     │
│                                     │
└─────────────────────────────────────┘
```

## Next Steps

1. **Implement core user stories** in order of priority
2. **Create Streamlit prototypes** for each major UI screen
3. **Test voice processing workflow** with sample data
4. **Design database schema** based on user stories
5. **Implement AI chat functionality** with cricket knowledge base

Would you like me to proceed with any specific user story implementation or technical architecture design? 