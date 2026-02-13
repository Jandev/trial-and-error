var builder = WebApplication.CreateBuilder(args);

// Add service defaults & Aspire client integrations.
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddProblemDetails();

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

builder.Services.AddHttpClient<BackendServiceClient>(
    static client => client.BaseAddress = new("https+http://backend"));

builder.Services.AddScoped<AgentCollaboration>();


var app = builder.Build();

// Configure the HTTP request pipeline.
app.UseExceptionHandler();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
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

app.MapDefaultEndpoints();

app.Run();

record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}

record AskRequest(string Question);
