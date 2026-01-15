var builder = DistributedApplication.CreateBuilder(args);

builder.AddAzureContainerAppEnvironment("env");

// Resolve Python backend paths (relative to AppHost project directory)
var pythonDir = Path.GetFullPath("../../python");
var pythonExe = Path.Combine(pythonDir, ".venv", "bin", "python");

var pythonBackend = builder.AddExecutable(
    "backend", pythonExe, pythonDir, "-m", "uvicorn", "aspire_backend_service.main:app", "--host", "0.0.0.0", "--port", "8000"
)
.WithHttpEndpoint(targetPort: 8000)
.WithEnvironment("DEBUG", "true")
.WithEnvironment("LOG_LEVEL", "info")
.WithEnvironment(context =>
{
    // Dynamic environment variables
    context.EnvironmentVariables["START_TIME"] = DateTimeOffset.UtcNow.ToString();
});

var apiService = builder.AddProject<Projects.AspireTrial_ApiService>("apiservice")
    .WithReference(pythonBackend.GetEndpoint("http"))
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.AspireTrial_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();
