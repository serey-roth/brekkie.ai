# brekkie.ai Web Application

A React-based web application for an AI-powered food and recipe assistant. Built with TypeScript, Vite, and modern React patterns.

## Description

This frontend application provides a real-time chat interface for interacting with brekkie.ai, a food assistant. Users can have conversations with the AI to generate recipes, ask cooking questions, and receive structured recipe responses. The application features WebSocket communication, real-time message streaming, and a responsive design optimized for recipe discovery and cooking assistance.

## Features

- Real-time Chat Interface: WebSocket-based communication with typing indicators
- Recipe Display: Structured recipe viewing with ingredients, instructions, and metadata
- Recipe Discovery: Interactive recipe search and recommendations
- User Authentication: Login/signup with JWT token management
- Thread Management: Conversation history and thread organization
- Responsive Design: Mobile-friendly interface with Tailwind CSS
- Message Streaming: Real-time message generation with typing animations
- Connection Management: Automatic reconnection and connection status indicators
- Error Handling: Comprehensive error states and user feedback

## Tech Stack

- **Frontend**: React 19, TypeScript 5.8
- **Build Tool**: Vite 6.3
- **Styling**: Tailwind CSS 4.1
- **State Management**: React Context + Immer
- **HTTP Client**: Fetch API with custom typed clients
- **WebSocket**: react-use-websocket
- **Validation**: Zod schemas
- **Testing**: Vitest + Testing Library
- **Package Manager**: pnpm
- **Icons**: React Icons
- **Date Handling**: Luxon
- **Markdown**: React Markdown with GFM support
- **Animations**: Framer Motion

## Project Structure

```text
src/
├── api-clients/          # HTTP API clients (auth, threads, access-token)
├── components/           # React components
│   ├── auth/            # Authentication components
│   ├── chat/            # Chat interface components
│   ├── layout/          # Layout and navigation
│   ├── providers/       # Context providers
│   ├── recipes/         # Recipe display components
│   ├── test/            # Test components
│   └── ui/              # Reusable UI components
├── config/              # Environment configuration
├── context/             # React context definitions
├── data/                # Data schemas and test data
│   ├── constants/       # Application constants
│   ├── schemas/         # Zod schemas
│   └── tests/           # Test data fixtures
├── hooks/               # Custom React hooks
├── managers/            # State managers
├── utils/               # Utility functions
└── main.tsx            # Application entry point
```

## Development

### Prerequisites

- Node.js 18+
- pnpm

### Setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Start development server:

   ```bash
   pnpm dev
   ```

3. Run tests:

   ```bash
   pnpm test
   ```

4. Build for production:

   ```bash
   pnpm build
   ```

### Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm lint` - Run ESLint
- `pnpm lint:fix` - Fix ESLint issues
- `pnpm preview` - Preview production build
- `pnpm format` - Format code with Prettier
- `pnpm format:check` - Check code formatting
- `pnpm test` - Run tests in watch mode
- `pnpm test:ui` - Run tests with UI
- `pnpm test:run` - Run tests once
- `pnpm test:coverage` - Run tests with coverage

## Environment Variables

The application uses the following environment variables:

- `VITE_API_BASE_URL`: Override for API base URL (defaults to localhost:8000)
- `VITE_WEBSOCKET_URL`: Override for WebSocket URL (defaults to localhost:8000)

## Key Components

### Chat System

- ChatLayout: Main chat interface layout
- MessageList: Displays conversation messages
- ChatInput: Message input with suggestions
- MessageGroup: Groups messages by sender
- TypingIndicator: Shows when AI is responding

### Recipe System

- RecipePanel: Sidebar recipe display
- RecipeView: Full recipe viewing component
- RecipeMessageCard: Recipe display in chat

### Authentication

- AuthScreen: Login/signup interface
- AuthProvider: Authentication state management

### State Management

- ChatProvider: Chat state and WebSocket management
- AppProvider: Global application state
- ConnectionStateManager: WebSocket connection management
- MessageManager: Message state management
- RecipeManager: Recipe state management

## Data Flow

1. WebSocket Connection: Establishes real-time communication with backend
2. Message Handling: Processes incoming/outgoing messages with proper typing
3. Recipe Parsing: Parses AI-generated recipe responses into structured format
4. State Updates: Updates UI state through React Context and Immer
5. Error Handling: Manages connection errors and API failures

## Testing

The application includes comprehensive testing with:

- Unit Tests: Component and utility function testing
- Integration Tests: API client and state management testing
- Test Utilities: Custom test data and assertion helpers

## Build Output

After running `pnpm build`, the production-ready files are in the `dist/` directory:

- `index.html` - Main HTML file
- `assets/` - Compiled CSS and JavaScript bundles

## Browser Support

The application targets modern browsers with ES2020+ support, including:

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
