# Agent Governance Platform - Customer Service Backend Setup

## 🎯 Project Overview

This project implements a **Customer Service Agent Backend** (second backend) that works alongside the primary AI Agent Governance Platform. The customer service backend handles customer scenarios and requests with governance approval from the primary backend.

## 📋 What Was Implemented

### 1. Customer Service Backend (New System - Port 8001)
A complete FastAPI application that:
- Handles customer service scenario simulations
- Connects to the frontend
- Forwards requests to the primary backend for governance
- Manages approval workflows with audit trails
- Provides real-time feedback on approval decisions

**Location**: `/customer-service-backend/`

### 2. Primary Backend Enhancement (Port 8000)
Added external integration routes that:
- Accept approval requests from customer service backend
- Return approval decisions
- Provide audit trail and findings
- Don't require admin authentication

**New File**: `backend/app/routes/external_integration.py`

### 3. Frontend Integration
Updated React frontend that:
- Connects to customer service backend instead of primary backend
- Displays customer service agent section
- Shows approval status and audit trails
- Provides scenario simulation testing

**New Component**: `frontend/src/components/CustomerService.jsx`

## 🏗️ System Architecture

```
┌─────────────────────────────────────┐
│    Frontend (React - Port 5173)      │
│  - Dashboard with CS Agent section   │
│  - Scenario simulation UI            │
│  - Audit trail display               │
└──────────────────┬──────────────────┘
                   │ HTTP
                   ▼
┌─────────────────────────────────────┐
│ Customer Service Backend (Port 8001) │
│ - Scenario simulation                │
│ - Request forwarding                 │
│ - Response enrichment                │
└──────────────────┬──────────────────┘
                   │ Internal HTTP
                   ▼
┌─────────────────────────────────────┐
│ Primary Backend (Port 8000)          │
│ - Governance & approvals             │
│ - Audit & tracking                   │
│ - Finding detection                  │
│ - Rule enforcement                   │
└──────────────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   PostgreSQL              LangGraph
   Database               Agent (9001)
```

## ✨ Key Features

### Scenario Simulations
- **Auto-Approval Scenarios**: Low-risk requests automatically approved
  - Small refunds ($50)
  - Order replacements
  - Priority support

- **Blocked-Approval Scenarios**: High-risk requests blocked with reasons
  - Large refunds ($5000+)
  - Account suspension
  - Data exports

- **Random Scenarios**: Mix of both for comprehensive testing

### Audit & Trace
Every request includes:
- **trace_id**: Unique identifier for tracking
- **audit_events**: Complete action log
- **findings**: Reasons for decisions
- **execution_time**: Performance metrics

### Real-Time Feedback
- Immediate approval/block decisions
- Detailed reasons for blocks
- Full audit trail visibility
- Performance metrics

## 🚀 Quick Start

### 1. Install Dependencies
```bash
make install
```

### 2. Start All Services
```bash
make dev
```

This starts:
- Primary Backend (Port 8000)
- Customer Service Backend (Port 8001)
- Frontend (Port 5173)
- LangGraph Agent (Port 9001)

### 3. Open Frontend
Navigate to: `http://localhost:5173`

### 4. Test the System
1. Log in to the dashboard
2. Scroll to "Customer Service Agent" section
3. Click "Test Auto-Approval"
4. Review the response and audit trail

### 5. Stop Services
```bash
make stop
```

## 📁 Project Structure

```
/home/aditya/agent-governance/
├── backend/                          # Primary backend
│   ├── app/
│   │   ├── routes/
│   │   │   └── external_integration.py  # ✨ NEW: CS backend endpoints
│   │   └── api.py                    # ✏️ UPDATED: Include CS routes
│   └── requirements.txt
├── customer-service-backend/         # ✨ NEW: Customer service backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app
│   │   ├── config.py                 # Configuration
│   │   ├── schemas.py                # Request/response models
│   │   ├── governance_client.py       # Primary backend client
│   │   ├── simulator.py               # Scenario simulation
│   │   └── routes/
│   │       ├── connect.py             # Connection endpoint
│   │       ├── simulate.py            # Simulation endpoint
│   │       └── docs.py                # Documentation (dev)
│   ├── run.py                        # Startup script
│   ├── requirements.txt               # Dependencies
│   ├── .env                          # Dev config
│   ├── .env.production               # Prod config
│   └── README.md                     # Documentation
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── CustomerService.jsx   # ✨ NEW: CS UI component
│   │   ├── services/
│   │   │   └── api.js                # ✏️ UPDATED: CS API functions
│   │   └── App.jsx                   # ✏️ UPDATED: Include CS component
│   └── package.json
├── docs/
├── Makefile                          # ✏️ UPDATED: CS targets
├── CUSTOMER_SERVICE_SETUP.md          # ✨ NEW: Setup guide
├── IMPLEMENTATION_SUMMARY.md          # ✨ NEW: Architecture overview
├── QUICK_REFERENCE.md                 # ✨ NEW: Quick commands
├── INSTALLATION_CHECKLIST.md          # ✨ NEW: Verification guide
└── quickstart.sh                      # ✨ NEW: Auto setup script
```

## 📡 API Reference

### Customer Service Backend (Port 8001)

#### Health Check
```bash
GET /health
```

#### Connect/Authenticate
```bash
POST /api/connect
{
  "client_id": "frontend-app",
  "client_secret": "secret123"
}
```

#### Simulate Scenario
```bash
POST /api/simulate
{
  "scenario_type": "auto_approval|blocked_approval|random",
  "customer_id": "CUST-001",
  "request_description": "Description of request"
}
```

#### Quick Tests
```bash
GET /api/simulate/auto-approval?customer_id=CUST-001
GET /api/simulate/blocked-approval?customer_id=CUST-002
```

#### Documentation (Dev Only)
```bash
GET /api/docs/api          # API documentation
GET /api/docs/flows        # Workflow diagrams
```

### Primary Backend (Port 8000)

#### External Integration Endpoints
```bash
# Submit approval request
POST /api/external/approvals/request

# Get audit trail
GET /api/external/audit?trace_id=<trace_id>

# Get findings
GET /api/external/findings?trace_id=<trace_id>

# Check status
GET /api/external/approvals/{run_id}

# Health check
GET /api/external/health
```

## ⚙️ Configuration

### Development
```env
# customer-service-backend/.env
ENVIRONMENT=development
PORT=8001
PRIMARY_BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### Production
```env
# customer-service-backend/.env
ENVIRONMENT=production
PORT=8001
PRIMARY_BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast lookup guide
- **[CUSTOMER_SERVICE_SETUP.md](CUSTOMER_SERVICE_SETUP.md)** - Detailed setup
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Architecture
- **[INSTALLATION_CHECKLIST.md](INSTALLATION_CHECKLIST.md)** - Verification
- **[customer-service-backend/README.md](customer-service-backend/README.md)** - Backend docs

## 🧪 Testing

### Via Frontend
1. Navigate to "Customer Service Agent" section
2. Click "Test Auto-Approval"
3. Review response and audit trail

### Via API
```bash
# Test auto-approval
curl http://localhost:8001/api/simulate/auto-approval?customer_id=CUST-001

# Test blocked-approval
curl http://localhost:8001/api/simulate/blocked-approval?customer_id=CUST-002

# Custom simulation
curl -X POST http://localhost:8001/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_type": "auto_approval",
    "customer_id": "CUST-123",
    "request_description": "Test"
  }'
```

## 🛠️ Makefile Commands

```bash
# Setup
make install                    # Install all dependencies
make install-customer-service   # Install CS backend only

# Running
make dev                        # Start all services (dev)
make start-cs-dev              # Start CS backend only
make stop                       # Stop all services
make status                     # Show service status

# Production
make prod                       # Build + start (production)
```

## 📊 Workflow

### Request Flow
1. Frontend sends request to CS Backend
2. CS Backend receives request
3. CS Backend processes scenario
4. CS Backend calls Primary Backend's external endpoint
5. Primary Backend makes approval decision
6. Primary Backend creates audit trail
7. Primary Backend returns decision
8. CS Backend enriches response with audit data
9. CS Backend returns to frontend
10. Frontend displays result with audit trail

### Response Example
```json
{
  "success": true,
  "scenario_type": "auto_approval",
  "customer_id": "CUST-001",
  "approval_status": "approved",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "audit_events": [
    {
      "event_type": "CUSTOMER_SERVICE_REQUEST",
      "actor": "customer_service_backend",
      "timestamp": "2024-08-17T10:30:00Z"
    }
  ],
  "findings": [],
  "execution_time_ms": 45.23,
  "message": "Low-risk operation"
}
```

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process on port 8001
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Cannot Connect to Primary Backend
```bash
# Verify primary is running
curl http://localhost:8000/

# Check .env configuration
cat customer-service-backend/.env

# Check network connectivity
curl -v http://localhost:8000/api/external/health
```

### CORS Errors
```bash
# Ensure correct CORS origins in primary backend
# Check customer-service-backend/.env URLs
# Verify frontend URL is whitelisted
```

### See Logs
```bash
# All services
make status

# Specific service
tail -f logs/customer-service.log
tail -f logs/backend.log
tail -f logs/frontend.log
```

## 📖 Next Steps

1. **Customize Scenarios**
   - Edit `customer-service-backend/app/simulator.py`
   - Add your own approval scenarios

2. **Add Database Storage**
   - Persist customer requests and results
   - Track approval metrics

3. **Implement Production Auth**
   - JWT token validation
   - Customer authentication

4. **Set Up Monitoring**
   - Logging and alerting
   - Performance monitoring

5. **Create Analytics**
   - Approval trends
   - Customer insights
   - Performance metrics

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 📝 Files Changed Summary

### New Files Created (✨)
1. `customer-service-backend/` - Complete new backend
2. `frontend/src/components/CustomerService.jsx` - New UI component
3. `backend/app/routes/external_integration.py` - Integration endpoints
4. `CUSTOMER_SERVICE_SETUP.md` - Setup documentation
5. `IMPLEMENTATION_SUMMARY.md` - Architecture documentation
6. `QUICK_REFERENCE.md` - Quick lookup guide
7. `INSTALLATION_CHECKLIST.md` - Verification checklist
8. `quickstart.sh` - Automatic setup script

### Updated Files (✏️)
1. `backend/app/api.py` - Include external integration routes
2. `frontend/src/services/api.js` - Add CS backend functions
3. `frontend/src/App.jsx` - Include CustomerService component
4. `Makefile` - Add CS backend targets

## 🎉 You're All Set!

Your Customer Service Agent Backend is ready to use. Start with:

```bash
make dev
```

Then open `http://localhost:5173` and explore the "Customer Service Agent" section!

For questions or issues, refer to:
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
- [CUSTOMER_SERVICE_SETUP.md](CUSTOMER_SERVICE_SETUP.md) for detailed setup
- [INSTALLATION_CHECKLIST.md](INSTALLATION_CHECKLIST.md) for troubleshooting

Happy coding! 🚀
