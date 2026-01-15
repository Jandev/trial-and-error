# trial-and-error

Aspire trial project with .NET API service and Python backend service.

## Project Structure

```text
src/
├── dotnet/                            # .NET projects
│   ├── AspireTrial.sln
│   ├── AspireTrial.ApiService/        # .NET API service
│   ├── AspireTrial.AppHost/           # .NET Aspire orchestrator
│   ├── AspireTrial.ServiceDefaults/   # Shared .NET defaults
│   ├── AspireTrial.Tests/             # .NET integration tests
│   └── AspireTrial.Web/               # Blazor frontend
├── python/                            # Python projects
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── ruff.toml                      # Linting/formatting config
│   ├── .venv/                         # Virtual environment (git-ignored)
│   ├── src/
│   │   └── aspire_backend_service/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       └── telemetry.py
│   └── tests/
│       └── test_main.py
└── shared/                            # Cross-language assets
```

## Setup

### Prerequisites

-   [.NET 9 SDK](https://dotnet.microsoft.com/download)
-   [Python 3.12+](https://www.python.org/downloads/)
-   [uv](https://docs.astral.sh/uv/) - Python package manager

### Install uv

```bash
brew install uv
```

### Setup Python Backend Service

```bash
cd src/python
uv sync --all-groups
```

> **Note:** `uv sync` automatically creates the `.venv` virtual environment and installs all dependencies.
> The `--all-groups` flag includes dev dependencies (pytest, ruff, mypy).

### Run the Application

```bash
aspire run
```

Or use the VS Code task: **Run Aspire**

## Development

### Python Backend Service

**Add dependencies:**

```bash
cd src/python
uv add <package-name>
```

**Update all dependencies:**

```bash
uv sync --upgrade --all-groups
```

**Run tests:**

```bash
uv run pytest
```

**Lint code:**

```bash
uv run ruff check .
```

**Format code:**

```bash
uv run ruff format .
```

**Type checking:**

```bash
uv run mypy src/
```

### .NET Services

**Build solution:**

```bash
cd src/dotnet
dotnet build
```

**Run tests:**

```bash
dotnet test
```

### VS Code Tasks

| Task                            | Description                        |
| ------------------------------- | ---------------------------------- |
| Run Aspire                      | Start the full application         |
| Python: Install/Update Packages | Install/update Python dependencies |
| Python: Run Tests               | Run pytest                         |
| Python: Lint (Ruff)             | Run linter                         |
| Python: Format (Ruff)           | Format code                        |
| .NET: Build Solution            | Build all .NET projects            |
| .NET: Run Tests                 | Run .NET tests                     |

## Endpoints

| Service          | URL                                     | Description                     |
| ---------------- | --------------------------------------- | ------------------------------- |
| Web Frontend     | <http://localhost:5000>                 | Blazor web application          |
| API Service      | <http://localhost:5001/weatherforecast> | .NET API service                |
| Python Backend   | <http://localhost:8000>                 | FastAPI backend service         |
| Aspire Dashboard | <http://localhost:15888>                | Service orchestration dashboard |
