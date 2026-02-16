# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Structure

```
.
├── src/
│   ├── dotnet/               # .NET Aspire services
│   │   ├── AspireTrial.ApiService/        # REST API with A2A orchestration
│   │   ├── AspireTrial.AppHost/           # Aspire AppHost
│   │   └── AspireTrial.ServiceDefaults/   # Shared service defaults
│   ├── python/               # Python backend service
│   │   └── src/aspire_backend_service/    # FastAPI with A2A agents
│   └── shared/               # Shared resources (api-tests.http)
├── .vscode/                  # VS Code tasks and settings
└── docs/                     # Documentation (README.md, etc.)
```

## Key Technologies

- .NET 10 + Aspire
- Python 3.12+ + FastAPI
- Azure AI Foundry
- A2A (Agent-to-Agent) Protocol

## Development Workflow

Before making changes:
1. Discuss proposed changes via an issue first (per contributing.md)
2. Ensure changes work locally and pass tests
3. Update README.md if adding new features or changing setup
4. Test A2A protocol endpoints if modifying agent collaboration
5. Wait for PR review and approval before merging

## Version Control

When creating commits, include: `Co-Authored-By: Warp <agent@warp.dev>`
