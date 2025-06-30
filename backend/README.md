# brekkie.ai Backend

A FastAPI-based backend service for an AI-powered food and recipe assistant. Built with Python 3.13, FastAPI, and Google's Generative AI.

## Description

This backend provides a comprehensive API for brekkie.ai, a food assistant that uses AI to generate recipes, help with cooking guidance, and provide recipe recommendations. It features real-time WebSocket communication, Redis caching, PostgreSQL persistence, and integration with Google's Generative AI for recipe generation and cooking assistance.

## Features

- AI Recipe Generation: Powered by Google's Generative AI with LangChain and LangGraph
- Recipe Recommendations: Intelligent recipe suggestions and cooking guidance
- Real-time Chat: WebSocket-based chat sessions with streaming responses
- User Authentication: JWT-based authentication with bcrypt password hashing
- Session Management: Redis-backed session storage with TTL
- Database Persistence: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- Caching Layer: Redis caching for threads, messages, recipes, and user access
- Rate Limiting: Message limits for authenticated and unauthenticated users
- Memory Management: Contextual memory using LangGraph checkpoints
- Recipe Parsing: Streaming XML recipe parser for structured recipe output

## Tech Stack

- **Framework**: FastAPI with Uvicorn
- **Language**: Python 3.13
- **AI/ML**: LangChain, LangGraph, Google Generative AI
- **Database**: PostgreSQL with SQLAlchemy
- **Caching**: Redis with async support
- **Authentication**: JWT with bcrypt
- **Testing**: pytest with coverage reporting
- **Code Quality**: mypy, ruff
- **Package Management**: Poetry

## Project Structure

```text
src/
├── ai/                    # AI agent implementation
│   ├── main.py           # AI agent entry point
│   ├── memory/           # Memory management
│   └── workflow/         # LangGraph workflows
├── api/                  # FastAPI application
│   ├── main.py          # Main API entry point
│   ├── deps.py          # Dependency injection
│   └── routes/          # API route handlers
├── database/            # Database configuration
│   ├── index.py         # Database connection
│   └── schema.py        # Database models
├── repositories/        # Data access layer
├── schemas/            # Pydantic models
├── services/           # Business logic
│   ├── ai_food_agent/  # AI agent services
│   ├── chat_services/  # Chat session management
│   ├── data_services/  # Data services with caching
│   ├── redis/          # Redis client configuration
│   └── streaming_recipe_parser/  # Recipe parsing
├── utils/              # Utility functions
└── main.py             # Application entry point
```

## API Endpoints

- WebSocket: `/ws` - Real-time chat communication
- Authentication: `/api/auth` - User signup, login, logout
- Access Tokens: `/api/access-token` - Token management
- Threads: `/api` - Thread management

## Development

### Prerequisites

- Python 3.13+
- Poetry
- PostgreSQL
- Redis

### Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Set up environment variables:

   ```bash
   DB_URL=postgresql://user:password@localhost/dbname
   REDIS_URL=redis://localhost:6379
   CHECKPOINT_DB_URL=postgresql://user:password@localhost/checkpoint_db
   GOOGLE_API_KEY=your_google_api_key
   ```

3. Run database migrations:

   ```bash
   alembic upgrade head
   ```

4. Start the development server:

   ```bash
   poetry run uvicorn src.api.main:app --reload
   ```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/services/test_ai_food_agent.py
```

### Code Quality

```bash
# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/

# Formatting
poetry run ruff format src/
```

## Configuration

### Environment Variables

- `DB_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CHECKPOINT_DB_URL`: LangGraph checkpoint database
- `GOOGLE_API_KEY`: Google Generative AI API key

### Cache TTL Settings

- Thread cache: 24 hours
- Message cache: 24 hours
- Recipe cache: 24 hours
- User access cache: 24 hours
- Session TTL: 30 minutes

### Rate Limits

- Authenticated users: 50 messages
- Unauthenticated users: 10 messages

## Architecture

The application follows a layered architecture:

1. API Layer: FastAPI routes and middleware
2. Service Layer: Business logic and orchestration
3. Repository Layer: Data access abstraction
4. Database Layer: SQLAlchemy models and migrations
5. Cache Layer: Redis-backed caching
6. AI Layer: LangChain/LangGraph integration

## Key Components

- ChatSessionOrchestrator: Manages real-time chat sessions
- GoogleAIFoodAgent: AI agent for recipe generation
- ServiceContainer: Dependency injection container
- StreamingRecipeParser: Parses AI-generated recipes
- WebSocketEventSender: Handles real-time communication
