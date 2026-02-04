# Apex Portal

Frontend application for Apex - AI Agent Platform.

## Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Data Fetching**: TanStack Query
- **State Management**: Zustand
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your API URL

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

See [docs/FRONTEND_STRUCTURE.md](../apex/docs/FRONTEND_STRUCTURE.md) for detailed structure.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Development

This project uses:
- **App Router** for routing
- **Server Components** by default
- **Client Components** when needed (use "use client")

## API Integration

The frontend connects to the Apex backend API. Make sure the backend is running and configured in `.env.local`.
