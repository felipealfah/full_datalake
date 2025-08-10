# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Full Data-Lakehouse** - A production-ready Delta Lake-based data lakehouse with FastAPI ingestion layer, optimized for VPS deployment using uv package manager.

## Common Development Commands

### Package Management (uv)
- Install dependencies: `uv sync`
- Install exact versions: `uv sync --frozen`
- Add new dependency: `uv add <package>`
- Development dependencies: `uv sync --group dev`
- Run with uv: `uv run python api/main.py`

### Legacy pip (fallback)
- Install dependencies: `pip install -e ".[dev]"`

### Code Quality
- Format code: `black .`
- Sort imports: `isort .`
- Type checking: `mypy .`
- Linting: `flake8 .`

### Testing
- Run all tests: `pytest`
- Run with coverage: `pytest --cov=api --cov=config --cov-report=term-missing`
- Run only unit tests: `pytest -m unit`
- Run only integration tests: `pytest -m integration`
- Skip slow tests: `pytest -m "not slow"`

### API Server
- Development: `python api/main.py`
- Alternative: `uvicorn api.main:app --reload`
- Test configuration: `python scripts/test_config.py`

## Architecture Overview

Containerized Delta Lake-based data lakehouse following medallion architecture pattern, designed for high-performance data processing and analytics with Docker isolation.

### Docker Architecture

**Container Strategy**: Separate containers for distinct responsibilities with shared volumes for data flow.

1. **Landing Zone Container** (`landing-zone/`): Data ingestion and staging
   - File upload processing and validation
   - Temporary storage before Delta Lake processing
   - File system watchers for automatic detection
   - Volume: `./landing_zone/data:/data/raw`

2. **Delta Lake Container** (`delta-processing/`): Core data processing
   - Medallion architecture implementation (Bronze → Silver → Gold)
   - File system monitoring of Landing Zone
   - Delta Lake table management and optimization
   - Volume: `./dados:/data/delta`

3. **API Container** (`api/`): FastAPI-based data ingestion service
   - `main.py`: REST endpoints with Bearer token authentication
   - `models.py`: Pydantic models for request/response validation
   - Orchestrates data flow between containers

4. **Storage Container** (optional): MinIO/S3-compatible object storage
   - Centralized storage backend for Delta Lake
   - Backup and replication capabilities

### Core Components

1. **Configuration** (`config/`): Centralized settings management
   - `settings.py`: Project paths, API settings, directory structure setup
   - Docker environment configuration

2. **Data Layers** (`dados/`): Medallion architecture
   - `bronze/`: Initial Delta Lake tables (raw data with metadata)
   - `silver/`: Cleaned, validated, and structured data
   - `gold/`: Business-ready aggregated analytics data

3. **Landing Zone** (`landing_zone/`): Input staging area
   - `data/raw/`: Temporary storage for incoming files
   - File system watchers trigger Delta Lake processing
   - Automatic cleanup after successful ingestion

4. **Processing** (`processamento/`): Data transformation pipelines
5. **Analysis** (`analise/`): Analytics and reporting layer
6. **Notebooks** (`notebooks/`): Jupyter notebooks for data exploration

### Technology Stack

- **Package Manager**: uv (Rust-based, faster than pip)
- **Web Framework**: FastAPI with Bearer token authentication
- **Data Processing**: Polars (primary), DuckDB, Pandas
- **Storage**: Delta Lake (native Python/Rust implementation)
- **Validation**: Pydantic models
- **External APIs**: Google APIs integration ready

### Data Flow

1. External systems POST data to FastAPI endpoints
2. API validates data using Pydantic models and saves to Landing Zone container
3. File system watcher detects new files in Landing Zone
4. Delta Lake container processes files through Bronze → Silver → Gold layers
5. Analytics and reporting consume Gold data from Delta Lake container

## Docker Deployment

### Container Management
- **Orchestration**: Docker Compose
- **Development**: `docker-compose up -d`
- **Production**: `docker-compose -f docker-compose.prod.yml up -d`
- **Logs**: `docker-compose logs -f [service-name]`

### Container Communication
- **Shared Volumes**: Landing Zone ↔ Delta Lake data flow
- **Internal Network**: Containers communicate via Docker network
- **File Monitoring**: Delta Lake watches Landing Zone volume for new files

### File System Watchers
- **Primary**: Python `watchdog` library for cross-platform file monitoring
- **Linux Optimization**: Direct `inotify` integration for production VPS
- **Real-time Detection**: Sub-second latency for new file events
- **Event Types**: CREATE, MODIFY, MOVE events trigger processing
- **Efficiency**: Low CPU overhead, event-driven architecture
- **Implementation**: 
  - Landing Zone: Optional file validation on arrival
  - Delta Lake: Immediate processing trigger on file detection
  - Cleanup: Automatic file removal after successful Delta Lake ingestion


#### Production Configuration
- **User**: `delta-user`
- **Project Directory**: `/opt/delta-lake`
- **API Port**: 8000 (via Docker network)
- **Reverse Proxy**: Nginx (host level)
- **Process Manager**: Docker Compose + systemd
- **Monitoring**: Container health checks + cron
- **Backup**: Automated daily backups of volumes

#### Container Services
- **Management Commands**:
  - `docker-compose ps` - Check container status
  - `docker-compose restart [service]` - Restart specific service
  - `docker-compose logs -f [service]` - Follow service logs
  - `docker exec -it [container] bash` - Access container shell

#### Security Features
- UFW firewall configuration
- Nginx security headers
- Container isolation with Docker
- Resource limits per container
- Network segmentation

## Project Management

### Workflow Control
- **Project Plan**: See `workflow/plan.md` for detailed implementation roadmap
- **TODO Tracking**: Implementation phases and blocking issues documented
- **Status Overview**: Current system capabilities and missing components
- **Priority Tasks**: Critical path items for full data lakehouse functionality

### Development Notes

- Project renamed from "delta-lakehouse" to "full-lakehouse"
- Uses modern Python packaging with `pyproject.toml`
- Code style: Black formatter (88 char line length), isort for imports
- Type checking with mypy (strict configuration)
- Coverage reporting configured for core modules
- Known first-party modules: `["api", "config", "processamento", "analise"]`
- **Workflow Management**: Use `workflow/plan.md` for project planning and task tracking