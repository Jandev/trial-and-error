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
})
.WithEnvironment("AZURE_AI_PROJECT_ENDPOINT", "https://spp-smartpricing-dev-ai-foundry.services.ai.azure.com/api/projects/spp-smartpricing-dev-project")
.WithEnvironment("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
;


/*
export AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
*/
var apiService = builder.AddProject<Projects.AspireTrial_ApiService>("apiservice")
    .WithReference(pythonBackend)
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.AspireTrial_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithHttpHealthCheck("/health")
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();
