# Dagster RBAC Authentication System

This module provides Role-Based Access Control (RBAC) authentication for Dagster's open-source webserver using OAuth providers.

## Features

- 🔐 **GitHub OAuth Integration** - Secure authentication with GitHub
- 👥 **Role-Based Access Control** - 4 hierarchical roles (Admin, Editor, Launcher, Viewer)
- 🔑 **Granular Permissions** - Fine-grained control over operations
- 🍪 **Secure Sessions** - HTTP-only cookies with CSRF protection
- 🎯 **Configurable** - Easy setup through `dagster.yaml`
- 🔒 **Thread-Safe** - Safe for concurrent use

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Middleware     │────│  Auth Backend   │
│   (React)       │    │  (Auth Check)    │    │  (GitHub OAuth) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                          │
                               │                          │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Session Manager  │    │   User Store    │
                       │ (HTTP Sessions)  │    │ (JSON Storage)  │
                       └──────────────────┘    └─────────────────┘
```

## Roles & Permissions

### Role Hierarchy

- **Admin** (Level 4): Full system access
- **Editor** (Level 3): Can manage schedules, sensors, and workspace
- **Launcher** (Level 2): Can launch and manage runs
- **Viewer** (Level 1): Read-only access

### Permission Matrix

| Permission | Viewer | Launcher | Editor | Admin |
|------------|---------|----------|---------|-------|
| View runs, assets, logs | ✅ | ✅ | ✅ | ✅ |
| Launch/terminate runs | ❌ | ✅ | ✅ | ✅ |
| Manage schedules/sensors | ❌ | ❌ | ✅ | ✅ |
| Manage users/permissions | ❌ | ❌ | ❌ | ✅ |

## Configuration

### 1. GitHub OAuth Setup

1. Create a GitHub OAuth App:
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - Set Authorization callback URL to: `http://localhost:3000/auth/callback`

2. Get your Client ID and Client Secret

### 2. Dagster Configuration

Add to your `dagster.yaml`:

```yaml
authentication:
  enabled: true
  provider: github
  default_role: viewer
  session_timeout: 86400  # 24 hours in seconds
  
  github:
    client_id: "your-github-client-id"
    client_secret: "your-github-client-secret"
    redirect_uri: "http://localhost:3000/auth/callback"
  
  role_assignments:
    # Assign roles by GitHub username or email
    "admin-user": admin
    "editor@company.com": editor
    "launcher-user": launcher
    # Users not listed get default_role
  
  public_paths:
    # Additional paths that don't require auth
    - "/health"
    - "/metrics"
```

### 3. Environment Variables

Set a secure session secret:

```bash
export DAGSTER_SESSION_SECRET="your-secure-random-secret-key"
```

## Usage

### Starting Dagster with Authentication

```bash
dagster-webserver -h 0.0.0.0 -p 3000
```

### Programmatic Access

```python
from dagster_webserver.auth import (
    User, UserRole, has_permission, Permission
)

# Check if user has permission
user = User(username="john", role=UserRole.EDITOR, ...)
can_launch = has_permission(user, Permission.LAUNCH_RUNS)

# Use permission decorators
from dagster_webserver.auth.permissions import require_permission

@require_permission(Permission.MANAGE_SCHEDULES)
async def schedule_endpoint(request):
    # Only editors and admins can access this
    pass
```

### Frontend Integration

The system provides several endpoints:

- `GET /auth/login` - Login page
- `GET /auth/logout` - Logout user
- `GET /auth/user` - Current user info
- `GET /auth/status` - Authentication status

## Security Features

### CSRF Protection

- OAuth state parameter validation
- Secure session cookies (HttpOnly, Secure, SameSite)

### Session Management

- Automatic session cleanup
- Configurable timeouts
- Thread-safe operations

### Permission Enforcement

- Middleware-level authentication checks
- Route-level permission decorators
- Context-aware permissions

## File Structure

```
dagster_webserver/auth/
├── __init__.py           # Module exports
├── models.py             # User and role models
├── auth_backend.py       # OAuth backend implementations
├── middleware.py         # Authentication middleware
├── permissions.py        # Permission system
├── session_manager.py    # Session handling
├── user_store.py         # User data storage
├── routes.py             # Authentication endpoints
├── context.py            # Authenticated workspace context
└── auth_manager.py       # Main coordinator
```

## Extending the System

### Adding New OAuth Providers

1. Create a new backend class:

```python
class CustomOAuthBackend(AuthBackend):
    def get_authorization_url(self, state: str) -> str:
        # Implementation
        pass
    
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        # Implementation
        pass
```

2. Register in `auth_manager.py`

### Adding New Roles

1. Update `UserRole` enum in `models.py`
2. Add permissions in `RolePermissions.ROLE_PERMISSIONS`
3. Update role hierarchy levels

### Custom Permission Checks

```python
from dagster_webserver.auth.permissions import Permission

# Define new permission
class CustomPermission(Enum):
    CUSTOM_ACTION = "custom_action"

# Use in code
@require_permission(CustomPermission.CUSTOM_ACTION)
async def custom_endpoint(request):
    pass
```

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check GitHub OAuth configuration
   - Verify redirect URI matches exactly
   - Check client ID/secret

2. **"Invalid state parameter"**
   - CSRF protection triggered
   - Clear browser cookies and try again

3. **Session not persisting**
   - Check cookie security settings
   - Verify DAGSTER_SESSION_SECRET is set

### Debug Mode

Set environment variable for detailed logs:

```bash
export DAGSTER_LOG_LEVEL=DEBUG
```

## Production Deployment

### Security Checklist

- ✅ Set secure `DAGSTER_SESSION_SECRET`
- ✅ Use HTTPS in production
- ✅ Configure proper GitHub OAuth redirect URI
- ✅ Review role assignments
- ✅ Set appropriate session timeouts
- ✅ Monitor authentication logs

### Performance Considerations

- Session cleanup runs automatically
- User data is cached in memory
- JSON storage is suitable for small teams
- Consider database storage for large deployments

## Migration Guide

This authentication system is designed to be:

- **Backward Compatible**: Existing Dagster instances work unchanged
- **Optional**: Authentication can be enabled/disabled
- **Non-Breaking**: No changes to existing APIs when auth is disabled

To enable authentication on an existing instance:

1. Add configuration to `dagster.yaml`
2. Set up GitHub OAuth
3. Restart Dagster webserver
