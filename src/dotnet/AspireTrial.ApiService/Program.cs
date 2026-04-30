using AspireTrial.ApiService.Options;
using AspireTrial.ApiService.Services;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Hosting.AGUI.AspNetCore;
using Microsoft.Extensions.Options;

const string DevAguiCorsPolicy = "DevAguiOpen";

var builder = WebApplication.CreateBuilder(args);

// Add service defaults & Aspire client integrations.
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddProblemDetails();

// Configure Azure AI options using the Options pattern
builder.Services.AddOptions<AzureAIOptions>()
    .BindConfiguration(AzureAIOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

builder.Services.AddHttpClient<BackendServiceClient>(
    static client => client.BaseAddress = new("https+http://backend"));

builder.Services.AddScoped<AgentCollaboration>();

// AG-UI hosting infrastructure (registers the SSE serializers, etc.)
builder.Services.AddAGUI();

// Frontend-demo agent: synchronous singleton built from AzureAIOptions.
// Pattern matches the official MS sample (external-context/01 lines 67-74) and
// the user's confirmed pattern from another solution. NO hosted service,
// NO async pre-warm — AIProjectClient.AsAIAgent is synchronous and returns a
// non-versioned ChatClientAgent backed by the project's Responses API.
builder.Services.AddSingleton<AIAgent>(sp =>
{
    var opts = sp.GetRequiredService<IOptions<AzureAIOptions>>().Value;
    var projectClient = new AIProjectClient(
        new Uri(opts.ProjectEndpoint),
        new DefaultAzureCredential());
    return projectClient.AsAIAgent(
        model: opts.ModelDeploymentName,
        instructions: FrontendDemoAgent.Instructions,
        name: "FrontendDemoAgent",
        tools: [FrontendDemoAgent.GetServerTimeTool()]);
});

// Dev-only CORS for the /agui browser direct-connect (CopilotKit's
// agents__unsafe_dev_only). NOT registered in production — public deployments
// would put a reverse proxy / auth layer in front of MapAGUI instead.
if (builder.Environment.IsDevelopment())
{
    builder.Services.AddCors(options =>
    {
        options.AddPolicy(DevAguiCorsPolicy, policy => policy
            .AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader());
    });
}

var app = builder.Build();

// Configure the HTTP request pipeline.
app.UseExceptionHandler();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.UseCors(DevAguiCorsPolicy);
}

string[] summaries = ["Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"];

app.MapGet("/", () => "API service is running. Navigate to /weatherforecast to see sample data.");

app.MapGet("/weatherforecast", async (BackendServiceClient backendServiceClient) =>
{
    var response = await backendServiceClient.GetRoot();
    var forecast = Enumerable.Range(1, 5).Select(index =>
        new WeatherForecast
        (
            DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
            Random.Shared.Next(-20, 55),
            summaries[Random.Shared.Next(summaries.Length)]
        ))
        .ToList();
    forecast.Add(new WeatherForecast(
        DateOnly.FromDateTime(DateTime.Now),
        30,
        response.Message
    ));
    return forecast;
})
.WithName("GetWeatherForecast");

app.MapPost("/countLetters", async (AskRequest ask, BackendServiceClient backendServiceClient) =>
{
    var question = ask.Question;
    var response = await backendServiceClient.GetCountLetters(question);
    return response;
});

app.MapPost("/countLetters-a2a", async (AskRequest ask, AgentCollaboration agentCollaboration) =>
{
    var question = ask.Question;
    var response = await agentCollaboration.Ask(question);
    return response;
});

// AG-UI endpoint: resolve the singleton AIAgent and map it.
var frontendDemoAgent = app.Services.GetRequiredService<AIAgent>();
app.MapAGUI("/agui", frontendDemoAgent);

app.MapDefaultEndpoints();

app.Run();

record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}

record AskRequest(string Question);
