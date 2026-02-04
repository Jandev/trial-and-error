# trial-and-error

Aspire trial project with .NET API service and Python backend service.

## Setup

### Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) - Python package manager

### Configure Secrets

Add the AI Foundry endpoint to the AppHost project's secrets:

```bash
dotnet user-secrets set "Parameters:AiFoundryProjectEndpoint" "https://<your-project>.services.ai.azure.com/api/projects/<project-id>" --project src/dotnet/AspireTrial.AppHost
```

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
