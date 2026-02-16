# trial-and-error

Aspire trial project with .NET API service and Python backend service.

## Setup

### Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) - Python package manager

### Configure Secrets

Configure Azure AI Foundry settings in the AppHost project's secrets:

```bash
# AI Foundry Project Endpoint
dotnet user-secrets set "Parameters:AiFoundryProjectEndpoint" "https://<your-project>.services.ai.azure.com/api/projects/<project-id>" --project src/dotnet/AspireTrial.AppHost

# Model Deployment Name (e.g., gpt-4o, gpt-35-turbo)
dotnet user-secrets set "Parameters:ModelDeploymentName" "gpt-4o" --project src/dotnet/AspireTrial.AppHost
```

> See [AzureAIOptions.cs](src/dotnet/AspireTrial.ApiService/Options/AzureAIOptions.cs) for configuration details.

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

## Features

### A2A Protocol Implementation

The project implements the [Agent-to-Agent (A2A) protocol](https://github.com/microsoft/agents) for agent collaboration:

- **Python Agent**: `CountLettersAgent` provides letter counting functionality via A2A
  - Endpoint: `/agents/count-letters-a2a` (JSON-RPC 2.0)
  - Agent card: `/agents/count-letters/.well-known/agent-card.json`
  - Implementation: [agents.py](src/python/src/aspire_backend_service/routers/agents.py)

- **.NET Orchestrator**: Discovers and uses the Python agent via A2A
  - Implementation: [AgentCollaboration.cs](src/dotnet/AspireTrial.ApiService/Services/AgentCollaboration.cs)
  - Uses Azure AI Foundry for orchestration
  - Endpoint: `/countLetters-a2a`

See [api-tests.http](src/shared/api-tests.http) for usage examples.
