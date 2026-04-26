# InventoryOS — Intelligent Supply Chain & Warehouse Management Platform

> **FAANG-level enterprise platform** demonstrating advanced DSA, full CRUD engineering, scalable backend architecture, and real-world operational intelligence.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        InventoryOS                              │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │  Next.js 15  │    │         FastAPI Backend               │  │
│  │  TypeScript  │◄──►│  ┌──────────┐   ┌────────────────┐  │  │
│  │  TailwindCSS │    │  │  API v1  │   │   Algorithms   │  │  │
│  │  Recharts    │    │  │  Routers │   │  ┌──────────┐  │  │  │
│  │  Zustand     │    │  └────┬─────┘   │  │ Dijkstra │  │  │  │
│  └──────────────┘    │       │         │  │ Trie     │  │  │  │
│                       │  ┌────▼─────┐  │  │ Heap     │  │  │  │
│                       │  │Services  │  │  │ Holt-W   │  │  │  │
│                       │  └────┬─────┘  │  │ Wgn-W DP │  │  │  │
│                       │       │        │  └──────────┘  │  │  │
│  ┌──────────────┐    │  ┌────▼─────┐  └────────────────┘  │  │
│  │   Redis      │◄──►│  │SQLAlchemy│                       │  │
│  │   Cache      │    │  │  Models  │   ┌────────────────┐  │  │
│  └──────────────┘    │  └────┬─────┘   │ Celery Workers │  │  │
│                       │       │         │ Background Jobs │  │  │
│  ┌──────────────┐    │  ┌────▼─────┐  └────────────────┘  │  │
│  │  PostgreSQL  │◄──►│  │   DB     │                       │  │
│  │   16 + idx   │    │  └──────────┘                       │  │
│  └──────────────┘    └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## DSA Implementations

### 1. Graph — Dijkstra's Route Optimization
**File:** `backend/app/algorithms/graph.py`

```
Complexity: O((V + E) log V)  using binary min-heap
Use case:   Warehouse-to-warehouse optimal shipping routes
            Supply chain bottleneck detection (articulation points)
Features:
  ✓ Haversine great-circle distance between geo-coordinates
  ✓ Dijkstra's shortest path (full implementation, no library)
  ✓ All-pairs from single source
  ✓ BFS reachability check
  ✓ Articulation point detection (bridge nodes)
```

**API Endpoint:** `POST /api/v1/warehouses/route/optimize`

---

### 2. Trie — Product Search Engine
**File:** `backend/app/algorithms/trie.py`

```
Complexity: Insert O(k), Prefix search O(k + output), Fuzzy O(k × Σ × n)
Use case:   Sub-millisecond SKU/product autocomplete
Features:
  ✓ Standard prefix trie with O(k) lookup
  ✓ Frequency-weighted result ranking
  ✓ Fuzzy (Levenshtein edit-distance ≤ 1) via DP row traversal
  ✓ Multi-token indexing (index by both SKU and name tokens)
  ✓ Module-level singleton with hot-rebuild
```

**API Endpoint:** `GET /api/v1/products/search?q={prefix}&fuzzy={bool}`

---

### 3. Binary Heap Priority Queues
**File:** `backend/app/algorithms/heap.py`

Three specialised heaps, all O(log n) push/pop:

| Heap | Ranks | Formula |
|------|-------|---------|
| **OrderHeap** | Orders by urgency | `priority_weight × (1 + days_overdue)² × log(1 + value)` |
| **RestockHeap** | SKUs by stockout risk | `1 / (days_to_stockout + 0.1)` |
| **ShipmentRiskHeap** | Shipments by delay risk | `days_delayed^1.5` |

All support lazy deletion for O(1) logical removal.

**API Endpoints:**
- `GET /api/v1/orders/priority-queue`
- `GET /api/v1/analytics/restock-queue`
- `GET /api/v1/shipments/delay-risk`

---

### 4. Dynamic Programming — Inventory Optimization
**File:** `backend/app/algorithms/forecasting.py`

#### a) Holt-Winters Triple Exponential Smoothing
```
State variables: Level (L), Trend (T), Seasonality (S)
Updates each period:
  L_t = α(y_t - S_{t-L}) + (1-α)(L_{t-1} + T_{t-1})
  T_t = β(L_t - L_{t-1}) + (1-β)T_{t-1}
  S_t = γ(y_t - L_t) + (1-γ)S_{t-L}
Output: forecast + 95% confidence interval + RMSE + MAPE
```

#### b) Wagner-Whitin DP Lot-Sizing
```
State:       dp[t] = min cost to satisfy demand periods 1..t
Transition:  dp[t] = min_{j≤t} { dp[j-1] + setup_cost + Σ holding[j..t] }
Complexity:  O(T²) — globally optimal vs. heuristic approaches
```

#### c) Economic Order Quantity (EOQ)
```
Q* = sqrt(2DS / H)    [Wilson's formula]
Balances ordering cost vs. holding cost optimally.
```

#### d) Safety Stock
```
SS = Z × sqrt(L×σ_d² + d²×σ_L²)
Where Z is the service-level z-score (e.g. 1.645 for 95%)
```

---

### 5. Merge Sort — Supplier Ranking
**File:** `backend/app/algorithms/forecasting.py` (rank_suppliers)

```
Multi-factor weighted scoring with custom merge sort:
  Weight: on_time_delivery(0.35) + quality(0.30) + price(0.20) + lead_time(0.15)
  Normalised per dimension before scoring.
  O(n log n) guaranteed, stable sort.
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI 0.115, Python 3.12 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 (LRU policy, 256MB) |
| **Auth** | JWT (HS256), bcrypt |
| **Queue** | Celery + Redis Broker |
| **Frontend** | Next.js 15, TypeScript, TailwindCSS |
| **Charts** | Recharts |
| **State** | TanStack Query + Zustand |
| **Deploy** | Docker Compose |

---

## API Reference

### Authentication
```
POST /api/v1/auth/register    Register new user
POST /api/v1/auth/login       Login → JWT tokens
POST /api/v1/auth/refresh     Refresh access token
GET  /api/v1/auth/me          Get current user
```

### Products (CRUD + Search)
```
GET    /api/v1/products                    List with pagination
POST   /api/v1/products                    Create product
GET    /api/v1/products/{id}               Get by ID
PATCH  /api/v1/products/{id}               Update
DELETE /api/v1/products/{id}               Soft delete
GET    /api/v1/products/search?q=          Trie prefix/fuzzy search
GET    /api/v1/products/{id}/eoq           EOQ calculation
GET    /api/v1/products/{id}/safety-stock  Safety stock calc
```

### Warehouses
```
GET    /api/v1/warehouses                  List all
POST   /api/v1/warehouses                  Create
PATCH  /api/v1/warehouses/{id}             Update
GET    /api/v1/warehouses/{id}/stock       Stock levels
PUT    /api/v1/warehouses/{id}/stock/{pid} Update stock
POST   /api/v1/warehouses/route/optimize   Dijkstra route finder
```

### Analytics (Intelligence Layer)
```
GET  /api/v1/analytics/dashboard           KPI dashboard
GET  /api/v1/analytics/revenue-trend       Revenue chart data
GET  /api/v1/analytics/warehouse-utilization
GET  /api/v1/analytics/top-products
GET  /api/v1/analytics/restock-queue       RestockHeap
GET  /api/v1/analytics/supplier-rankings   Merge sort ranked
GET  /api/v1/analytics/forecast/{pid}      Holt-Winters
POST /api/v1/analytics/replenishment-plan  Wagner-Whitin DP
GET  /api/v1/analytics/supply-chain-health
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose

### 1. Clone and configure
```bash
git clone <repo>
cd inventoryos
cp .env.example .env
```

### 2. Start all services
```bash
docker compose up -d
```

### 3. Run migrations and seed
```bash
make migrate
make seed
```

### 4. Access the platform
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

### Demo Credentials
```
Admin:   admin@inventoryos.com     / admin123456
Manager: manager@inventoryos.com   / manager123
```

---

## Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
inventoryos/
├── backend/
│   ├── app/
│   │   ├── algorithms/          # DSA implementations
│   │   │   ├── graph.py         # Dijkstra + BFS + DFS
│   │   │   ├── trie.py          # Prefix trie + fuzzy search
│   │   │   ├── heap.py          # Priority queues (3 variants)
│   │   │   └── forecasting.py   # Holt-Winters, DP, EOQ, ranking
│   │   ├── api/v1/              # FastAPI routers
│   │   ├── core/                # Config, DB, security, Redis
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic layer
│   │   └── scripts/             # Seed data generator
│   ├── tests/                   # 40+ unit tests
│   └── alembic/                 # Database migrations
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (app)/           # Authenticated pages
│       │   │   ├── dashboard/   # KPI dashboard
│       │   │   ├── inventory/   # Product management + Trie search
│       │   │   ├── warehouses/  # Warehouse + Dijkstra route UI
│       │   │   ├── suppliers/   # Supplier management + rankings
│       │   │   ├── orders/      # Orders + Priority Queue UI
│       │   │   ├── shipments/   # Shipments + Delay Risk UI
│       │   │   └── analytics/   # Forecasting + charts
│       │   └── auth/            # Login page
│       ├── components/          # Reusable UI components
│       ├── lib/                 # API client, auth store, utils
│       └── types/               # TypeScript type definitions
│
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## Performance Design

| Concern | Solution |
|---------|----------|
| **Sub-200ms search** | Trie O(k) vs SQL ILIKE O(n) |
| **DB indexing** | Composite indexes on status, category, score columns |
| **Cache layer** | Redis with key-pattern invalidation; 30–300s TTL |
| **Pagination** | Cursor-based with configurable page size (max 100) |
| **Connection pool** | SQLAlchemy async pool: 20 base + 10 overflow |
| **Compression** | GZip middleware on responses >1KB |
| **API latency** | X-Process-Time-Ms header; 500ms slow-query warnings |

---

## Running Tests

```bash
# All tests
make test

# Just algorithm unit tests (no DB required)
cd backend
pytest tests/test_algorithms.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

Test coverage: **40+ unit tests** across all DSA modules, including:
- Dijkstra correctness on triangle graphs + geo distances
- Trie exact/prefix/fuzzy lookup
- Heap ordering and lazy deletion
- Holt-Winters forecast length, CI ordering, MAPE bounds
- Wagner-Whitin DP demand satisfaction
- EOQ formula verification
- Safety stock service level monotonicity
- Supplier ranking stability

---

## Resume Signals

This project demonstrates:

| Skill | Evidence |
|-------|---------|
| **CRUD Mastery** | 6 domain entities, full lifecycle APIs |
| **Advanced DSA** | Dijkstra, Trie, Heap×3, Holt-Winters, Wagner-Whitin DP, Merge Sort |
| **Backend Architecture** | Layered (Router→Service→Repository), DI, middleware |
| **Database Design** | 8 normalized tables, FK constraints, composite indexes |
| **Caching Strategy** | Redis pattern-based invalidation, TTL tuning |
| **Auth & Security** | JWT (access+refresh), bcrypt, role-based access control |
| **Async Python** | FastAPI + SQLAlchemy async throughout |
| **Frontend** | Next.js 15, TypeScript strict, TanStack Query |
| **DevOps** | Docker Compose, Celery workers, Alembic migrations |
| **Testing** | 40+ pure unit tests, integration test fixtures |
| **Analytics** | Real-time KPIs, forecasting, demand prediction |
