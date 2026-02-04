# Apex - Frontend Structure

## Overview

Frontend application built with Next.js 14+ (App Router), TypeScript, Tailwind CSS, and modern React patterns.

## Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI primitives)
- **Data Fetching**: TanStack Query (React Query)
- **State Management**: Zustand
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios or fetch
- **Icons**: Lucide React

## Directory Structure

```
frontend/
├── README.md
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── .env.local.example
├── .gitignore
│
├── public/                              # Static assets
│   ├── images/
│   └── favicon.ico
│
├── src/
│   ├── app/                            # Next.js App Router
│   │   ├── layout.tsx                  # Root layout
│   │   ├── page.tsx                    # Home/landing page
│   │   ├── (auth)/                     # Auth routes group
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (dashboard)/                # Dashboard routes group
│   │   │   ├── layout.tsx              # Dashboard layout (sidebar, header)
│   │   │   ├── agents/                 # Agent management
│   │   │   │   ├── page.tsx            # Agent list
│   │   │   │   ├── [id]/
│   │   │   │   │   ├── page.tsx        # Agent detail/edit
│   │   │   │   │   ├── chat/
│   │   │   │   │   │   └── page.tsx     # Chat interface
│   │   │   │   │   └── settings/
│   │   │   │   │       └── page.tsx     # Agent settings
│   │   │   │   └── new/
│   │   │   │       └── page.tsx         # Create new agent
│   │   │   │
│   │   │   ├── knowledge/              # Knowledge management
│   │   │   │   ├── page.tsx             # Knowledge list
│   │   │   │   ├── upload/
│   │   │   │   │   └── page.tsx         # Upload documents
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx         # Document detail
│   │   │   │
│   │   │   ├── schemas/                 # Schema management
│   │   │   │   ├── page.tsx             # Schema list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx         # Create schema
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx         # Schema detail/edit
│   │   │   │
│   │   │   ├── playbooks/               # Playbook management
│   │   │   │   ├── page.tsx             # Playbook list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx         # Create playbook
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx         # Playbook detail/edit
│   │   │   │
│   │   │   ├── tools/                   # Tool management
│   │   │   │   ├── page.tsx             # Tool list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx         # Create tool
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx         # Tool detail/edit
│   │   │   │
│   │   │   ├── fine-tuning/            # Fine-tuning
│   │   │   │   ├── page.tsx             # Fine-tuning jobs list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx         # Create fine-tuning job
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx         # Job detail/progress
│   │   │   │
│   │   │   ├── experiments/            # Experimentation
│   │   │   │   ├── page.tsx             # Experiment list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx         # Create experiment
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx         # Experiment detail
│   │   │   │       └── compare/
│   │   │   │           └── page.tsx     # Compare experiments
│   │   │   │
│   │   │   └── monitoring/             # Monitoring dashboard
│   │   │       ├── page.tsx             # Main dashboard
│   │   │       ├── metrics/
│   │   │       │   └── page.tsx         # Performance metrics
│   │   │       └── logs/
│   │   │           └── page.tsx         # Response logs
│   │   │
│   │   ├── api/                        # API routes (if needed)
│   │   │   └── auth/
│   │   │       └── callback/
│   │   │           └── route.ts
│   │   │
│   │   └── globals.css                 # Global styles
│   │
│   ├── components/                     # Reusable components
│   │   ├── ui/                         # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── form.tsx
│   │   │   ├── select.tsx
│   │   │   ├── textarea.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/                     # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Navbar.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   ├── agents/                     # Agent-specific components
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentForm.tsx
│   │   │   ├── AgentSettings.tsx
│   │   │   └── AgentStatusBadge.tsx
│   │   │
│   │   ├── chat/                       # Chat components
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── TypingIndicator.tsx
│   │   │
│   │   ├── knowledge/                  # Knowledge components
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentViewer.tsx
│   │   │   └── ProcessingStatus.tsx
│   │   │
│   │   ├── schemas/                     # Schema components
│   │   │   ├── SchemaEditor.tsx
│   │   │   ├── SchemaForm.tsx
│   │   │   └── SchemaVisualizer.tsx
│   │   │
│   │   ├── playbooks/                   # Playbook components
│   │   │   ├── PlaybookEditor.tsx
│   │   │   ├── PlaybookForm.tsx
│   │   │   └── ScenarioBuilder.tsx
│   │   │
│   │   ├── tools/                       # Tool components
│   │   │   ├── ToolCard.tsx
│   │   │   ├── ToolForm.tsx
│   │   │   └── ToolSchemaEditor.tsx
│   │   │
│   │   ├── fine-tuning/                 # Fine-tuning components
│   │   │   ├── FineTuningJobCard.tsx
│   │   │   ├── FineTuningForm.tsx
│   │   │   ├── TrainingProgress.tsx
│   │   │   └── ModelSelector.tsx
│   │   │
│   │   ├── experiments/                 # Experiment components
│   │   │   ├── ExperimentCard.tsx
│   │   │   ├── ExperimentForm.tsx
│   │   │   ├── ExperimentComparison.tsx
│   │   │   └── MetricsChart.tsx
│   │   │
│   │   ├── monitoring/                  # Monitoring components
│   │   │   ├── MetricsDashboard.tsx
│   │   │   ├── PerformanceChart.tsx
│   │   │   ├── ToolUsageChart.tsx
│   │   │   ├── ResponseLogs.tsx
│   │   │   └── ExperimentMetrics.tsx
│   │   │
│   │   └── shared/                      # Shared components
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── EmptyState.tsx
│   │       ├── ConfirmDialog.tsx
│   │       └── DataTable.tsx
│   │
│   ├── lib/                            # Utilities and configurations
│   │   ├── api/                        # API client
│   │   │   ├── client.ts               # Axios/fetch instance
│   │   │   ├── agents.ts                # Agent API calls
│   │   │   ├── chat.ts                  # Chat API calls
│   │   │   ├── knowledge.ts            # Knowledge API calls
│   │   │   ├── schemas.ts               # Schema API calls
│   │   │   ├── playbooks.ts             # Playbook API calls
│   │   │   ├── tools.ts                 # Tool API calls
│   │   │   ├── fine-tuning.ts           # Fine-tuning API calls
│   │   │   ├── experiments.ts           # Experiment API calls
│   │   │   └── monitoring.ts            # Monitoring API calls
│   │   │
│   │   ├── hooks/                       # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useAgent.ts
│   │   │   ├── useChat.ts
│   │   │   ├── useKnowledge.ts
│   │   │   └── useWebSocket.ts          # For real-time chat
│   │   │
│   │   ├── store/                      # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   ├── agentStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── uiStore.ts                # UI state (sidebar, modals)
│   │   │
│   │   ├── utils/                       # Utility functions
│   │   │   ├── cn.ts                     # className utility (shadcn)
│   │   │   ├── format.ts                 # Formatting utilities
│   │   │   ├── validation.ts             # Validation helpers
│   │   │   └── constants.ts              # Constants
│   │   │
│   │   └── types/                       # TypeScript types
│   │       ├── api.ts                    # API response types
│   │       ├── agent.ts
│   │       ├── chat.ts
│   │       ├── knowledge.ts
│   │       ├── schema.ts
│   │       ├── playbook.ts
│   │       ├── tool.ts
│   │       ├── fine-tuning.ts
│   │       └── experiment.ts
│   │
│   └── providers/                      # React context providers
│       ├── QueryProvider.tsx            # TanStack Query provider
│       ├── AuthProvider.tsx
│       └── ThemeProvider.tsx             # Dark/light mode
│
├── components.json                     # shadcn/ui config
│
└── .next/                              # Next.js build output (gitignored)
```

## Key Features & Pages

### 1. Authentication
- Login/Register pages
- JWT token management
- Protected routes

### 2. Agent Management
- Agent list with search/filter
- Agent creation wizard
- Agent configuration (persona, tone, guardrails)
- Agent testing interface (chat)
- Agent settings

### 3. Knowledge Management
- Document upload (drag & drop)
- Document list with search
- Processing status tracking
- Document viewer
- Schema-aware document organization

### 4. Schema Management
- Schema editor (JSON/YAML)
- Schema visualization
- Schema validation
- LLM analysis results display

### 5. Playbook Management
- Playbook editor
- Scenario builder
- Training data preview
- Playbook templates

### 6. Tool Management
- Tool list
- Tool creation form
- Schema editor for tool parameters
- Tool testing interface

### 7. Fine-tuning
- Fine-tuning job creation
- Model selection
- Training progress tracking
- Job history
- Model comparison

### 8. Experimentation
- Experiment creation
- A/B test configuration
- Experiment comparison dashboard
- Metrics visualization
- Results analysis

### 9. Monitoring
- Performance metrics dashboard
- Response logs
- Tool usage analytics
- Experiment tracking
- Real-time updates

## Component Patterns

### Data Fetching
```typescript
// Using TanStack Query
const { data, isLoading, error } = useQuery({
  queryKey: ['agents'],
  queryFn: () => api.agents.list()
});
```

### State Management
```typescript
// Zustand store example
const useAgentStore = create((set) => ({
  selectedAgent: null,
  setSelectedAgent: (agent) => set({ selectedAgent: agent })
}));
```

### Forms
```typescript
// React Hook Form + Zod
const form = useForm<AgentFormData>({
  resolver: zodResolver(agentSchema)
});
```

## Styling Approach

- **Tailwind CSS** for utility-first styling
- **shadcn/ui** for consistent component design
- **CSS Variables** for theming (dark/light mode)
- **Responsive Design** with mobile-first approach

## API Integration

- **Base URL**: Configured via environment variables
- **Authentication**: JWT tokens in Authorization header
- **Error Handling**: Centralized error handling with toast notifications
- **Loading States**: Skeleton loaders and spinners
- **Optimistic Updates**: For better UX

## Real-time Features

- **Chat**: WebSocket connection for real-time messages
- **Fine-tuning Progress**: Server-Sent Events (SSE) for job updates
- **Monitoring**: Polling or WebSocket for live metrics

## Next Steps

1. Set up Next.js project with TypeScript
2. Install and configure Tailwind CSS
3. Set up shadcn/ui components
4. Configure TanStack Query
5. Set up Zustand stores
6. Create API client layer
7. Build authentication flow
8. Implement core pages (agents, chat, knowledge)
9. Add monitoring dashboard
10. Implement fine-tuning and experimentation UIs
