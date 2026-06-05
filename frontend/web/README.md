# brekkie.ai Web

React frontend for brekkie.ai — an AI meal planning assistant with multi-turn conversations.

## Tech Stack

- **Framework**: React 19, TypeScript 5.8
- **Build**: Vite 6.3
- **Styling**: Tailwind CSS 4.1
- **Auth**: Supabase (Google OAuth)
- **Validation**: Zod
- **Animations**: Framer Motion
- **Package Manager**: pnpm

## Project Structure

```text
src/
├── api-clients/     # Typed HTTP and auth clients
├── components/      # React components
│   ├── auth/        # Auth guard, callback, login screen
│   ├── chat/        # Chat interface and messages
│   ├── layout/      # Sidebar, main view
│   ├── providers/   # App and chat context providers
│   ├── recipes/     # Recipe display
│   └── ui/          # Reusable UI primitives
├── config/          # Environment configuration
├── context/         # React context definitions
├── data/schemas/    # Zod schemas
├── hooks/           # Custom hooks (auth, WebSocket, chat)
├── managers/        # State managers (user access, chat state)
└── utils/
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

2. Copy and configure environment variables:

   ```bash
   cp .env.example .env.development
   ```

   Required variables:
   - `VITE_API_BASE_URL` — e.g. `http://localhost:8000/api`
   - `VITE_WS_BASE_URL` — e.g. `ws://localhost:8000/ws`
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_API_KEY`

3. Start the dev server:

   ```bash
   pnpm dev
   ```

### Scripts

- `pnpm dev` — start dev server
- `pnpm build` — production build
- `pnpm lint` — run ESLint
- `pnpm format` — format with Prettier
- `pnpm test` — run tests
- `pnpm test:coverage` — run tests with coverage

## Deployment

Deployed to [Vercel](https://vercel.com). Configuration is in `vercel.json`. Set root directory to `frontend/web` in the Vercel project settings.
