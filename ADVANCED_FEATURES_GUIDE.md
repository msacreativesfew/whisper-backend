# Whisper AI Assistant - Advanced Features Guide

This guide covers all advanced features that make Whisper more powerful than Alexa, Google Assistant, and Siri.

## Table of Contents
1. [Context Management & Conversation History](#context-management)
2. [Multi-Language Support (15+ Languages)](#multi-language-support)
3. [Integration Ecosystem](#integration-ecosystem)
4. [Personalization Engine](#personalization-engine)
5. [Analytics & Insights](#analytics--insights)
6. [Proactive Intelligence](#proactive-intelligence)
7. [Advanced API Reference](#advanced-api-reference)

---

## Context Management

### What It Does
Unlike Alexa or Google Assistant, Whisper maintains deep conversation context across multiple sessions, allowing it to:
- Remember previous conversations
- Understand cross-conversation references ("Like I mentioned last week...")
- Build on earlier statements without repeating context
- Provide more intelligent follow-up responses

### API Endpoints

#### Create Conversation
```bash
POST /api/advanced/conversations
Content-Type: application/json

{
  "title": "Meeting Planning"
}

Response:
{
  "id": 1,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Meeting Planning",
  "created_at": "2024-04-30T10:00:00Z"
}
```

#### Add Message
```bash
POST /api/advanced/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "role": "user",
  "content": "What did we discuss about the Q2 budget?",
  "language": "en"
}
```

#### Get Conversation History
```bash
GET /api/advanced/conversations/{conversation_id}
```

#### Add Context Items
```bash
POST /api/advanced/conversations/{conversation_id}/context
Content-Type: application/json

{
  "item_type": "previous_context",
  "key": "meeting_budget",
  "value": "Q2 budget: $500k allocation for marketing",
  "expires_at": null
}
```

### Database Storage
- Conversations stored in PostgreSQL
- Automatic compression and cleanup of old messages
- Full-text search for finding past conversations
- Context retention policies (archive old conversations)

---

## Multi-Language Support

### Supported Languages (15+)
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Japanese (ja)
- Chinese Simplified (zh)
- Korean (ko)
- Russian (ru)
- Arabic (ar)
- Hindi (hi)
- Dutch (nl)
- Polish (pl)
- Turkish (tr)

### Language Features
✓ **Real-time Language Detection** - Auto-detects input language
✓ **Speech-to-Text Localization** - Accurate transcription for all languages
✓ **Voice Output** - Native speakers for each language
✓ **Regional Formatting** - Dates, times, currency per locale
✓ **RTL Support** - Right-to-left languages (Arabic, Hebrew)

### API Endpoints

#### Get Available Languages
```bash
GET /api/i18n/languages

Response:
{
  "current": "en",
  "available": {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    ...
  }
}
```

#### Change Language
```bash
POST /api/i18n/language?language=es

Response:
{
  "status": "success",
  "language": "es"
}
```

#### Get Translations
```bash
GET /api/i18n/translations?language=ja

Response:
{
  "language": "ja",
  "translations": {
    "welcome": "Whisper AI アシスタントへようこそ",
    "listening": "リッスン中...",
    ...
  },
  "locale": {
    "currency": "JPY",
    "currency_symbol": "¥",
    "date_format": "%Y/%m/%d",
    ...
  }
}
```

### Python Usage
```python
from i18n import init_translator, get_translator

# Initialize
translator = init_translator("es")

# Translate
welcome = translator.t("welcome")  # "Bienvenido..."

# Format numbers and dates
amount = translator.format_currency(1234.56)  # "€1.234,56"
date_str = translator.format_date(datetime.now())  # "30/04/2024"
```

---

## Integration Ecosystem

### Supported Integrations

#### Google Services
- **Google Calendar** - Schedule meetings, check availability
- **Gmail** - Send/receive emails, smart replies
- **Google Drive** - Access documents during conversations

#### Productivity
- **Slack** - Send messages, post updates
- **Notion** - Query notes and databases
- **Todoist** - Create/manage tasks

#### Smart Home
- **Philips Hue** - Control smart lights
- **SmartThings** - Manage smart devices
- **OpenWeather** - Weather-aware responses

#### Media & Content
- **Spotify** - Play music, control playback
- **News API** - Get latest news and headlines

### Setup Integration

```bash
POST /api/advanced/integrations/google_calendar
Content-Type: application/json

{
  "access_token": "ya29.a0...",
  "refresh_token": "1//...",
  "expires_at": "2024-05-30T10:00:00Z"
}
```

### List Integrations

```bash
GET /api/advanced/integrations

Response:
{
  "total": 3,
  "integrations": [
    {
      "provider": "google_calendar",
      "is_enabled": true,
      "synced_at": "2024-04-30T09:30:00Z"
    },
    {
      "provider": "slack",
      "is_enabled": true,
      "synced_at": "2024-04-30T09:00:00Z"
    }
  ]
}
```

### Feature Examples
- "Schedule a meeting for tomorrow at 2 PM" → Creates Google Calendar event
- "Send a message to #marketing on Slack" → Posts message
- "What's on my schedule today?" → Checks Google Calendar
- "Turn off the living room lights" → Controls Philips Hue

---

## Personalization Engine

### User Preferences

#### Update Preferences
```bash
POST /api/advanced/users/{user_id}/preferences
Content-Type: application/json

{
  "preferred_language": "es",
  "voice_speed": 1.2,
  "response_length": "long",
  "privacy_mode": false
}
```

#### Voice Speed Control
- Range: 0.5x - 2.0x
- Default: 1.0x (normal speed)
- Use case: Faster responses for experienced users, slower for clarity

#### Response Length Options
- **short** - Brief, concise answers
- **medium** - Balanced (default)
- **long** - Detailed explanations with context

#### Privacy Mode
- When enabled: Doesn't store conversation history
- Useful for sensitive topics
- Data still used for real-time processing only

### Get Preferences
```bash
GET /api/advanced/users/{user_id}/preferences

Response:
{
  "user_id": "user@example.com",
  "preferred_language": "en",
  "voice_speed": 1.0,
  "response_length": "medium",
  "privacy_mode": false,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Analytics & Insights

### Usage Tracking
- Messages sent/received
- Conversation duration
- Tokens used per API
- Cost analysis
- Feature usage breakdown

### Get Analytics
```bash
GET /api/advanced/analytics/{user_id}?days=30

Response:
{
  "user_id": "user@example.com",
  "days": 30,
  "metrics": {
    "total_messages": 142,
    "total_tokens": 45230,
    "total_cost": "$2.13",
    "average_cost_per_day": "$0.07"
  },
  "daily_breakdown": [
    {
      "date": "2024-04-30",
      "messages_sent": 5,
      "messages_received": 5,
      "tokens_used": 1523,
      "cost": "$0.08"
    }
  ]
}
```

### Cost Breakdown by Provider
- Groq LLM tokens
- ElevenLabs text-to-speech characters
- Google API calls (Calendar, Gmail)
- Slack API calls

---

## Proactive Intelligence

### Scheduled Tasks & Reminders

#### Create Reminder
```bash
POST /api/advanced/tasks
Content-Type: application/json

{
  "task_type": "reminder",
  "title": "Team standup",
  "description": "Daily 10 AM standup call",
  "scheduled_time": "2024-04-30T10:00:00Z",
  "recurrence": "daily"
}
```

#### Supported Recurrence
- `daily` - Every day
- `weekly` - Every week on same day
- `monthly` - Every month on same date

#### List Upcoming Tasks
```bash
GET /api/advanced/tasks

Response:
{
  "total": 3,
  "tasks": [
    {
      "id": 1,
      "task_type": "reminder",
      "title": "Team standup",
      "scheduled_time": "2024-05-01T10:00:00Z",
      "recurrence": "daily"
    }
  ]
}
```

#### Complete Task
```bash
PUT /api/advanced/tasks/{task_id}/complete

Response:
{
  "status": "success",
  "task_id": 1,
  "completed_at": "2024-04-30T10:05:00Z"
}
```

### Features
- ✓ Proactive briefings ("Good morning, here's your schedule")
- ✓ Smart reminders with context
- ✓ Recurring tasks with smart rescheduling
- ✓ Integration with calendar events

---

## Advanced API Reference

### Base URL
```
https://your-railway-domain.up.railway.app/api/advanced
```

### Authentication
Include `user_id` in request headers or URL parameters:
```bash
# Option 1: Header
Authorization: Bearer {user_id}

# Option 2: Query parameter
?user_id=user@example.com
```

### Error Handling
```json
{
  "error": "Conversation not found",
  "status": 404,
  "timestamp": "2024-04-30T10:00:00Z"
}
```

### Rate Limits
- Default: 100 requests per minute per user
- Contact support for higher limits

### Pagination
```bash
GET /api/advanced/conversations?skip=0&limit=20
```

---

## Comparison with Other Assistants

| Feature | Whisper | Alexa | Google Assistant | Siri |
|---------|---------|-------|------------------|------|
| **Conversation Context** | ✓ Deep (stored) | Limited | Limited | Limited |
| **Languages** | 15+ | 15+ | 30+ | 35+ |
| **Integrations** | Custom (10+) | Limited | Extensive | Limited |
| **Personalization** | Advanced | Basic | Good | Basic |
| **Privacy** | Optional | Limited | Limited | Good |
| **Open Source** | Partial | No | No | No |
| **Self-Hosted** | Yes | No | No | No |
| **Custom Skills** | Yes | Yes | Yes | No |
| **Real-time Analytics** | Yes | Limited | Yes | No |
| **Multi-language in Conversation** | Yes | No | Limited | Limited |

---

## Getting Started with Advanced Features

### Step 1: Initialize Database
```bash
python -c "from models import init_db; init_db()"
```

### Step 2: Set User Language
```bash
curl -X POST "http://localhost:8000/api/i18n/language?language=es"
```

### Step 3: Create First Conversation
```bash
curl -X POST "http://localhost:8000/api/advanced/conversations" \
  -H "Content-Type: application/json" \
  -d '{"title": "General Chat"}'
```

### Step 4: Add Context
```bash
curl -X POST "http://localhost:8000/api/advanced/conversations/{conversation_id}/context" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "user_preference",
    "key": "timezone",
    "value": "America/New_York"
  }'
```

### Step 5: Start Chatting
Messages are automatically stored with context for intelligent responses.

---

## Next Steps

- [ ] Deploy to Railway with PostgreSQL
- [ ] Set up Google Calendar integration
- [ ] Enable Slack integration
- [ ] Configure custom intents
- [ ] Set up scheduled briefings
- [ ] Create user preferences interface

For more help, check individual feature documentation or contact support.
