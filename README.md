# XiaoCai 1.0 Development Workspace

**Local development workspace for XiaoCai 1.0 multi-repository project**

This directory serves as a local workspace containing multiple independent Git repositories for the XiaoCai 1.0 (小采 1.0) project - an AI-powered procurement requirement management system.

---

## Repository Architecture

This project uses a **multi-repository architecture** where each service is independently versioned and deployed:

``` 
procurement-agents/  (Local workspace, NOT a Git repository)
├── xiaocai-app/              → git@github.com:Dante-Vonarmia/xiaocai-app.git
├── xiaocai-api/              → git@github.com:Dante-Vonarmia/xiaocai-api.git
├── xiaocai-kernel/           → git@github.com:Dante-Vonarmia/xiaocai-kernel.git
├── xiaocai-engagement/       → git@github.com:Dante-Vonarmia/xiaocai-engagement.git (Private)
├── xiaocai-platform/         → git@github.com:Dante-Vonarmia/xiaocai-platform.git (Private)
├── domain-packs/             (Active instance domain assets: workflows/prompts/knowledge)
├── domain-pack/              (Legacy compatibility source; frozen)
├── docs/                     (Project documentation)
└── README.md
```

---

## Repository Overview

### Service Repositories (Public)

| Repository | Description | Tech Stack | Port |
|------------|-------------|------------|------|
| **xiaocai-app** | React frontend application | React 18 + Vite + Ant Design 5 | 3001 (dev) / 3000 (prod) |
| **xiaocai-api** | FastAPI backend gateway | FastAPI + GraphQL + PostgreSQL | 8001 |
| **xiaocai-kernel** | AI runtime kernel | LangGraph + Qdrant + FLARE adapter | 8002 |

### Configuration Repositories (Private)

| Repository | Description | Purpose |
|------------|-------------|---------|
| **xiaocai-engagement** | Deployment configurations and seed data | Customer-specific configurations |
| **xiaocai-platform** | DevOps orchestration | Docker Compose, deployment scripts, Nginx configs |

### Workspace Standard Directories (Non-Git)

| Directory | Description |
|-----------|-------------|
| **frame (logical)** | Merged into `xiaocai-app` + `xiaocai-api` + `xiaocai-kernel` |
| **xiaocai-domain-pack/** | Domain workflows, prompts, knowledge, subagents |
| **xiaocai-platform/deploy/** | Single source of release/rollback artifacts |
| **docs/templates/** | Reserved templates (non-runtime placeholders) |
| **docs/** | Governance, delivery, project execution documents |

---

## Directory Ownership Baseline (Authoritative)

- `domain-packs/`: instance domain assets 主源（新增只允许放这里）
- `domain-pack/`: 兼容层（冻结，不再新增）
- `pack-registry/`: base profile 清单与入口索引（registry only）
- `tenant-config/`: tenant overrides only
- `bindings/`: tenant private data bindings descriptor only

## Standard Profile vs Tenant Override vs Private Data

For procurement product scaling, this repository now follows a three-layer model:

1. **Standard product profiles**:
- Stored in `pack-registry/`.
- Maintained as a small, versioned set (`profile_id + version`).
- Count should remain far smaller than tenant count.

2. **Tenant overrides**:
- Stored in `tenant-config/`.
- Each tenant must reference `base_profile_id` and only carry overrides.
- Do not copy a full profile per tenant.

3. **Tenant private data bindings**:
- Descriptors stored in `bindings/`.
- Private data body must stay in data layer systems (DB/object store/external service), not in repo config files.

Compatibility note:
- Existing `domain-pack/` remains as frozen compatibility source during migration.
- New domain assets must go to `domain-packs/`.

---

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+
- Git

### Clone All Repositories

```bash
# Create workspace directory
mkdir -p ~/Development/xiaocai
cd ~/Development/xiaocai

# Clone service repositories
git clone git@github.com:Dante-Vonarmia/xiaocai-app.git
git clone git@github.com:Dante-Vonarmia/xiaocai-api.git
git clone git@github.com:Dante-Vonarmia/xiaocai-kernel.git
git clone git@github.com:Dante-Vonarmia/xiaocai-engagement.git
git clone git@github.com:Dante-Vonarmia/xiaocai-platform.git
```

### Start Development Environment

```bash
# Enter platform directory
cd xiaocai-platform

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Start all services
./xiaocai.sh start
```

**Access services**:
- Frontend: http://localhost:3001 (dev) / http://localhost:3000 (prod)
- API: http://localhost:8001
- GraphQL Playground: http://localhost:8001/graphql

### Service Management

```bash
# Check service status
./xiaocai.sh status

# Restart services
./xiaocai.sh restart

# Stop services
./xiaocai.sh stop

# Clean up (WARNING: removes volumes)
./xiaocai.sh clean
```

---

## Development Workflow

### Working on a Service

```bash
# Navigate to service directory
cd xiaocai-app

# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/new-feature

# Create pull request on GitHub
```

### Updating All Repositories

```bash
# Update all repositories
cd xiaocai-app && git pull origin main && cd ..
cd xiaocai-api && git pull origin main && cd ..
cd xiaocai-kernel && git pull origin main && cd ..
cd xiaocai-engagement && git pull origin main && cd ..
cd xiaocai-platform && git pull origin main && cd ..
```

---

## Project Documentation

### Global Documentation (This Workspace)

- **docs/** - Architecture and design documents
- **frame (logical)** - implemented by xiaocai-app / xiaocai-api / xiaocai-kernel
- **xiaocai-domain-pack/** - Standard domain-pack assets
- **xiaocai-platform/deploy/** - Manifest/version-lock/runbooks (single source)
- **docs/templates/** - Optional templates, not production runtime

### Service-Specific Documentation

Each repository contains its own README.md and CLAUDE.md:

- **xiaocai-app/README.md** - Frontend documentation
- **xiaocai-api/README.md** - Backend API documentation
- **xiaocai-kernel/README.md** - Kernel runtime documentation
- **xiaocai-platform/README.md** - DevOps documentation

---

## Architecture

### System Architecture

```
User → Nginx → xiaocai-app (React 18)
              ↓
        xiaocai-api (FastAPI + GraphQL)
              ↓
        xiaocai-kernel (LangGraph + FLARE adapter)
              ↓
        PostgreSQL / Redis / Qdrant
```

### Data Flow

1. User interacts with React frontend
2. Frontend sends GraphQL requests to API
3. API orchestrates kernel runtime
4. Kernel processes workflow and knowledge retrieval
5. Results stream back via SSE (Server-Sent Events)

### Technology Stack

**Frontend (xiaocai-app)**:
- React 18 + Vite
- Ant Design 5
- GraphQL with Apollo Client
- Less for styling

**Backend API (xiaocai-api)**:
- FastAPI
- Strawberry GraphQL
- PostgreSQL (session management)
- Redis (caching)

**Kernel Runtime (xiaocai-kernel)**:
- LangGraph (agent orchestration)
- Qdrant (vector database)
- FLARE core adapter entry (`app.flare.*`)

**DevOps (xiaocai-platform)**:
- Docker + Docker Compose
- Nginx reverse proxy
- Automated deployment scripts
- Health monitoring and backup

---

## Sprint Management

This workspace uses project documents under `docs/project/` for execution tracking.

### Execution Files

- **docs/project/instance-master-migration-plan.md** - 主计划与阶段状态
- **docs/project/instance-repo-separation-execution-checklist.md** - 执行检查清单
- **docs/project/instance-repo-separation-kit/migration-commands.md** - 迁移命令集

### Task Traceability

Tasks are tracked with IDs:
- `APP-###-description.md` (Frontend issues)
- `API-###-description.md` (Backend issues)
- `KERNEL-###-description.md` (Kernel runtime issues)
- `INFRA-###-description.md` (Infrastructure issues)

---

## Environment Configuration

### Local Development

Copy `.env.example` to `.env` in xiaocai-platform:

```bash
cd xiaocai-platform
cp .env.example .env
```

Key configurations:
- `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` (for LLM)
- `POSTGRES_PASSWORD` (database password)
- `REDIS_PASSWORD` (cache password)

### Production Deployment

See **xiaocai-platform/docs/quick-start.md** for complete production deployment guide.

---

## Common Tasks

### Database Operations

```bash
# Access PostgreSQL
docker exec -it xiaocai-postgres psql -U xiaocai -d xiaocai_db

# Run migrations
cd xiaocai-platform
./xiaocai.sh migrate
```

### Viewing Logs

```bash
# All services
docker compose -f xiaocai-platform/docker-compose.yml logs -f

# Specific service
docker logs -f xiaocai-api
docker logs -f xiaocai-app
docker logs -f xiaocai-kernel
```

### Health Check

```bash
cd xiaocai-platform
./scripts/health-check.sh
```

### Backup

```bash
cd xiaocai-platform
./scripts/backup.sh
```

---

## Troubleshooting

### Services Not Starting

1. Check if ports are available:
```bash
lsof -i :3000  # Frontend
lsof -i :3001  # Frontend (dev)
lsof -i :8001  # API
lsof -i :8002  # Kernel
lsof -i :5432  # PostgreSQL
```

2. Check Docker status:
```bash
docker ps
docker logs xiaocai-api
```

3. Restart services:
```bash
cd xiaocai-platform
./xiaocai.sh restart
```

### Git Issues

Each repository is independent. Make sure you're in the correct repository:

```bash
# Check current repository
git remote -v

# Should see the specific repository URL
```

### Port Conflicts

If ports are in use, update `.env` in xiaocai-platform to use different ports.

---

## Contributing

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch (if needed)
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Production hotfixes

### Commit Message Convention

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

### Pull Request Process

1. Create feature branch
2. Make changes and commit
3. Push to GitHub
4. Create pull request
5. Wait for review and approval
6. Merge to main

---

## Project Status

**Current Phase**: Phase 0 MVP
**Sprint**: 2026-W06-Phase0
**Status**: In Development

### Completed Milestones

- ✅ Multi-repo architecture setup
- ✅ Frontend application (React + Vite)
- ✅ Backend API (FastAPI + GraphQL)
- ✅ Kernel runtime (LangGraph + FLARE adapter)
- ✅ DevOps orchestration (Docker + scripts)
- ✅ Development environment
- ✅ Production deployment configuration

### In Progress

- 🔄 Testing coverage
- 🔄 Knowledge import API
- 🔄 Documentation completion

---

## License

Proprietary - Internal use only

---

## Contact

**Project Lead**: Dante Von Alcatraz
**Repository**: https://github.com/Dante-Vonarmia/

---

**Last Updated**: 2026-03-24
**Version**: 2.1.0 (Instance workspace structure)
**Architecture**: KDAS (Knowledge-Driven Agent System)
