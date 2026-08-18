# Customer Service Agent Backend

Second backend for handling customer service requests with governance approval from the primary backend.

## Architecture

```
Frontend (React)
    ↓
Customer Service Backend (Port 8001)
    ↓
Primary Backend (Port 8000) - Governance & Approval
    ↓
Audit, Trace, and Findings
```

## Features

- **Connect Endpoint** (`/api/connect`): Authenticate and connect to the service
- **Simulate Endpoint** (`/api/simulate`): Test customer service scenarios with governance
  - `auto_approval`: Low-risk requests (auto-approved)
  - `blocked_approval`: High-risk requests (blocked with reasons)
  - `random`: Random scenario selection
- **Documentation** (`/api/docs/*`): API and workflow documentation (dev only)
- **Health Check** (`/health`): Service health status
- **Real-time Audit Trail**: Every request is audited, traced, and reasons for blocks are provided

## Setup

1. Copy `.env.example` to `.env` and update values:
   ```bash
   cd customer-service-backend
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the backend:
   ```bash
   python run.py
   ```

The service will start on `http://localhost:8001` by default.

## Environment Variables

- `ENVIRONMENT`: `development` or `production`
- `PORT`: Server port (default: 8001)
- `PRIMARY_BACKEND_URL`: URL of the primary governance backend (default: http://localhost:8000)
- `FRONTEND_URL`: URL of the frontend application (default: http://localhost:5173)

## API Endpoints

### Connect
```bash
POST /api/connect
{
  "client_id": "frontend-app",
  "client_secret": "secret123"
}
```

### Simulate Scenario
```bash
POST /api/simulate
{
  "scenario_type": "auto_approval|blocked_approval|random",
  "customer_id": "CUST-001",
  "request_description": "Customer service request"
}
```

### Quick Tests
```bash
GET /api/simulate/auto-approval?customer_id=CUST-001
GET /api/simulate/blocked-approval?customer_id=CUST-002
```

### Documentation (Dev only)
```bash
GET /api/docs/api
GET /api/docs/flows
```

## Production Considerations

- Set `ENVIRONMENT=production` to disable documentation endpoints
- Use HTTPS for all connections
- Implement proper authentication and authorization
- Use environment variables for sensitive data
- Set up monitoring and logging
- Configure proper CORS origins
