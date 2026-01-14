var builder = DistributedApplication.CreateBuilder(args);

builder.AddAzureContainerAppEnvironment("env");

var pythonBackend = builder.AddExecutable(
    "backend", "python", "../AspireBackendService", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"
);

var apiService = builder.AddProject<Projects.AspireTrial_ApiService>("apiservice")
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.AspireTrial_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();
