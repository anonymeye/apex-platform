# Authentication & Authorization Implementation

## Overview

This document outlines the authentication and authorization system implemented for the Apex platform, supporting multi-organization (multi-tenant) access with role-based permissions.

## Architecture

### Backend-Driven Auth
- **Backend (Apex)** is the source of truth for all permissions
- **Frontend (Portal)** consumes permissions for UX optimization
- All permission checks are validated server-side
- Frontend checks are for UI rendering only (optimistic)

## User Roles

1. **Super Admin** - Platform-wide access
2. **Org Admin** - Full access within their organization
3. **Agent Builder** - Create and manage agents
4. **Content Manager** - Manage knowledge bases
5. **Analyst** - View-only access to analytics
6. **End User** - Chat-only access

## Permission System

### Permission Format
Permissions follow the pattern: `resource:action`
- Examples: `agents:create`, `agents:edit`, `agents:view`, `knowledge:delete`
- Wildcards: `agents:*` (all agent permissions), `*` (all permissions)

### Role Permissions
Each role has predefined permissions. See `apex/src/apex/core/security.py` for the complete mapping.

## Backend Implementation

### Database Models
- `User` - User accounts
- `Organization` - Multi-tenant organizations
- `OrganizationMember` - User-Organization relationship with roles

### JWT Token Structure
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "name": "John Doe",
  "is_super_admin": false,
  "org_id": "org_123",
  "org_role": "org_admin",
  "permissions": ["agents:create", "agents:edit", ...],
  "orgs": [
    {"id": "org_123", "name": "Acme Corp", "role": "org_admin"}
  ],
  "exp": 1234571490,
  "iat": 1234567890
}
```

### API Endpoints
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/switch-org` - Switch active organization

## Frontend Implementation

### Auth Store (`lib/store/authStore.ts`)
Zustand store managing:
- User information
- JWT token
- Authentication state
- Organization context

### Hooks
- `useAuth()` - Authentication actions (login, register, logout, switchOrg)
- `usePermissions()` - Permission checking utilities

### Components
- `ProtectedRoute` - Route-level permission/role protection
- `PermissionGate` - Component-level permission/role gating
- `OrganizationSwitcher` - Multi-org switching UI

### Pages
- `/login` - Login page
- `/register` - Registration page

## Usage Examples

### Protecting Routes
```tsx
<ProtectedRoute requiredPermission="agents:create">
  <AgentCreatePage />
</ProtectedRoute>
```

### Conditional UI Rendering
```tsx
<PermissionGate permission="agents:create">
  <Button>Create Agent</Button>
</PermissionGate>
```

### Checking Permissions in Components
```tsx
const { hasPermission } = usePermissions()
if (hasPermission('agents:edit')) {
  // Show edit button
}
```

### Switching Organizations
```tsx
const { switchOrg } = useAuth()
await switchOrg(organizationId)
```

## Next Steps

1. **Database Setup**: Configure database connection and run migrations
2. **Token Extraction**: Complete JWT token extraction from Authorization header in backend
3. **Organization Management**: Add endpoints for managing organizations and members
4. **Permission Middleware**: Implement permission decorators for route protection
5. **Testing**: Add unit and integration tests for auth flows

## Notes

- JWT secret key should be moved to environment variables
- Database session management needs to be implemented
- Token refresh endpoint is planned but not yet implemented
- Organization management endpoints are pending
