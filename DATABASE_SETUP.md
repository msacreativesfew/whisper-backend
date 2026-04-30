# Database Setup for Whisper AI Assistant

## Overview

The advanced features require a database to store:
- Conversation history and context
- User preferences and personalization
- Integration configurations
- Analytics and usage data
- Scheduled tasks and reminders

## Database Options

### Option 1: PostgreSQL (Recommended for Production)

**Best for**: Railway, Vercel, production deployments

```bash
# Set environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/whisper_db"
```

**Railway Setup**:
1. Go to Railway dashboard
2. Add PostgreSQL plugin
3. Copy the connection string to `DATABASE_URL` variable

### Option 2: SQLite (Default for Local Development)

**Best for**: Local development, testing

No additional setup needed - automatically creates `whisper_assistant.db`

```bash
# This is the default
export DATABASE_URL="sqlite:///./whisper_assistant.db"
```

## Installation

### Step 1: Install Dependencies

```bash
# Using uv
uv pip install sqlalchemy psycopg2-binary alembic redis langchain cryptography

# Or using pip
pip install sqlalchemy psycopg2-binary alembic redis langchain cryptography
```

### Step 2: Initialize Database

```python
from models import init_db
init_db()  # Creates all tables
```

Or run in Python shell:

```bash
python -c "from models import init_db; init_db()"
```

### Step 3: Update cloud_api.py

Add this to the beginning of `cloud_api.py`:

```python
from models import init_db, get_db, User, Conversation, Message
from sqlalchemy.orm import Session

# Initialize database on startup
init_db()

# Add database dependency to FastAPI
from fastapi import Depends

def get_database():
    from models import engine, Session
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
```

## Database Schema

### Users Table
Stores user accounts and global preferences.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    preferred_language VARCHAR(10),
    voice_speed FLOAT,
    response_length VARCHAR(20),
    privacy_mode BOOLEAN
);
```

### Conversations Table
Manages conversation sessions.

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    conversation_id VARCHAR(255) UNIQUE,
    title VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    archived BOOLEAN,
    context_summary TEXT
);
```

### Messages Table
Stores individual messages.

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER FOREIGN KEY,
    role VARCHAR(20),  -- "user", "assistant", "system"
    content TEXT,
    timestamp TIMESTAMP,
    language VARCHAR(10),
    confidence_score FLOAT,
    tokens_used INTEGER
);
```

### Context Items Table
Maintains conversation context for better responses.

```sql
CREATE TABLE context_items (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER FOREIGN KEY,
    item_type VARCHAR(50),
    key VARCHAR(255),
    value TEXT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

### Integration Configs Table
Stores OAuth tokens and integration settings.

```sql
CREATE TABLE integration_configs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    provider VARCHAR(50),  -- "google_calendar", "gmail", "slack", etc.
    is_enabled BOOLEAN,
    access_token TEXT,  -- Encrypted
    refresh_token TEXT,  -- Encrypted
    expires_at TIMESTAMP,
    created_at TIMESTAMP,
    synced_at TIMESTAMP
);
```

### Analytics Table
Tracks usage metrics and costs.

```sql
CREATE TABLE user_analytics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    date TIMESTAMP,
    messages_sent INTEGER,
    messages_received INTEGER,
    total_conversation_time INTEGER,  -- seconds
    tokens_used INTEGER,
    api_cost FLOAT
);
```

## Migration with Alembic

For production, use Alembic for schema migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add conversation tables"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Environment Variables

Add to your `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/whisper_db

# Redis (for caching and sessions)
REDIS_URL=redis://localhost:6379

# Encryption key (for storing tokens)
ENCRYPTION_KEY=your-32-character-base64-encoded-key

# Optional: Vector database for semantic search
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-west-2
```

## Best Practices

### 1. Encryption for Sensitive Data

```python
from cryptography.fernet import Fernet
import os

# Generate key: Fernet.generate_key()
encryption_key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(encryption_key)

# Store encrypted
encrypted_token = cipher.encrypt(access_token.encode())

# Retrieve and decrypt
decrypted_token = cipher.decrypt(encrypted_token).decode()
```

### 2. Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
)
```

### 3. Query Optimization

- Add indexes on frequently searched columns (done automatically for foreign keys)
- Lazy-load related objects with `selectinload()` to avoid N+1 queries
- Archive old conversations instead of deleting

### 4. Backup Strategy

For PostgreSQL:
```bash
# Backup
pg_dump postgresql://user:password@host/whisper_db > backup.sql

# Restore
psql postgresql://user:password@host/whisper_db < backup.sql
```

For Railway PostgreSQL, use automated backups in settings.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Connection refused** | Check DATABASE_URL, ensure PostgreSQL is running |
| **Table doesn't exist** | Run `init_db()` to create tables |
| **Permission denied** | Verify database user has proper privileges |
| **Out of connections** | Increase `pool_size` or enable connection pooling |
| **Slow queries** | Add indexes on frequently queried columns |

## Next Steps

1. Set up the database with your preferred option
2. Initialize tables with `init_db()`
3. Update `cloud_api.py` to use database models
4. Implement conversation history endpoints
5. Add user preference management
