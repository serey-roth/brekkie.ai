# brekkie.ai

An AI-powered food and recipe assistant with real-time chat interface. Built with FastAPI backend (Python/LangChain/Google AI) and React frontend (TypeScript/Vite).

## Overview

brekkie.ai is a full-stack application that helps users discover recipes, get cooking guidance, and plan meals through natural conversation. Users can interact with an AI assistant to generate recipes, ask cooking questions, and receive structured recipe responses. The system features real-time WebSocket communication, user authentication, and a responsive web interface optimized for recipe discovery and cooking assistance.

## Architecture

The project consists of two main components:

- **Backend** (`/backend`): FastAPI service with AI integration, database persistence, and WebSocket communication
- **Frontend** (`/frontend/web`): React application with real-time chat interface and recipe display

## Quick Start

### Backend Setup

```bash
cd backend
poetry install
# Set up environment variables (see backend/README.md)
poetry run uvicorn src.api.main:app --reload
```

### Frontend Setup

```bash
cd frontend/web
pnpm install
pnpm dev
```

## Features

- Real-time AI chat interface for recipe discovery
- Recipe generation and display with ingredients and instructions
- User authentication and session management
- WebSocket-based communication
- Responsive design for mobile and desktop
- Database persistence with PostgreSQL
- Redis caching layer for performance
- Intelligent recipe recommendations

## Tech Stack

### Backend

- Python 3.13, FastAPI, LangChain, LangGraph
- Google Generative AI, PostgreSQL, Redis
- Poetry, pytest, mypy, ruff

### Frontend

- React 19, TypeScript 5.8, Vite 6.3
- Tailwind CSS, WebSocket, Zod validation
- pnpm, Vitest, Testing Library

## Documentation

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/web/README.md)

## Development

Each component has its own development setup and testing procedures. See the individual README files for detailed instructions.

## License

MIT
