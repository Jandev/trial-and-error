var builder = DistributedApplication.CreateBuilder(args);

builder.AddAzureContainerAppEnvironment("env");

// Resolve Python backend paths (relative to AppHost project directory)
var pythonDir = Path.GetFullPath("../../python");
var pythonBackend = builder.AddUvicornApp("backend", pythonDir + "/src", "aspire_backend_service.main:app")
.WithExternalHttpEndpoints()
.WithUv()
.WithVirtualEnvironment(pythonDir + "/.venv")
.WithEnvironment("DEBUG", "true")
.WithEnvironment("LOG_LEVEL", "info")
.WithEnvironment(context =>
{
    // Dynamic environment variables
    context.EnvironmentVariables["START_TIME"] = DateTimeOffset.UtcNow.ToString();
});

var apiService = builder.AddProject<Projects.AspireTrial_ApiService>("apiservice")
    .WithReference(pythonBackend)
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.AspireTrial_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();
