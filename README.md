# trial-and-error

Aspire trial project with .NET API service and Python backend service.

## Setup

**Install uv:**

```bash
brew install uv
```

**Create Python virtual environment:**

```bash
uv venv
source .venv/bin/activate
uv pip install -r src/AspireTrial/AspireBackendService/requirements.txt
```

**Run the application:**

```bash
aspire run
```

## Sample usage

Access endpoints:

- Web frontend: <http://localhost:5000>
- API service: <http://localhost:5001/weatherforecast>
- Python backend: <http://localhost:8000>
