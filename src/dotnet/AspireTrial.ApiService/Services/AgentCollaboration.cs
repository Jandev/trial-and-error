using A2A;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.Options;
using AspireTrial.ApiService.Options;

public class AgentCollaboration(
    BackendServiceClient backendServiceClient,
    IOptions<AzureAIOptions> azureAIOptions)
{
    private const string Instructions =
    @"Your job is to orchestrate the use of agents made available to you.
    You will receive a question that needs to be solved and require the use of these agents.
    If an agent can't answer or provides the wrong answer, feel free to ask it again with an updated question and remarks on
    why it should try again.
    ";

    public record A2aResult(string Question, string Answer);

    public async Task<A2aResult> Ask(string question)
    {
        (string endpoint, HttpClient httpClient) = await backendServiceClient.GetCountLettersAgentCardEndpoint();

        // Get the agent card from the A2A endpoint
        var agentCardResolver = new A2ACardResolver(new Uri(endpoint), httpClient);
        var agentCard = await agentCardResolver.GetAgentCardAsync();

        // Create the A2A agent from the card
        var agent = agentCard.AsAIAgent();

        // Create function tools from the agent's skills
        var tools = CreateFunctionTools(agent, agentCard).ToList();

        // Use Azure AI configuration from options
        var aiOptions = azureAIOptions.Value;
        AIProjectClient aiProjectClient = new(new Uri(aiOptions.ProjectEndpoint), new DefaultAzureCredential());
        var newAgent = await aiProjectClient.CreateAIAgentAsync(
            name: "A2ATestClient",
            model: aiOptions.ModelDeploymentName,
            instructions: Instructions,
            tools: tools);

        var session = await newAgent.CreateSessionAsync();

        var answer = await newAgent.RunAsync(question, session);

        return new A2aResult(question, answer.Text);
    }

    private static IEnumerable<AITool> CreateFunctionTools(AIAgent a2aAgent, AgentCard agentCard)
    {
        foreach (var skill in agentCard.Skills)
        {
            AIFunctionFactoryOptions options = new()
            {
                Name = skill.Name,
                Description = $$"""
                {
                    "description": "{{skill.Description}}",
                    "tags": "[{{string.Join(", ", skill.Tags ?? [])}}]",
                    "examples": "[{{string.Join(", ", skill.Examples ?? [])}}]",
                    "inputModes": "[{{string.Join(", ", skill.InputModes ?? [])}}]",
                    "outputModes": "[{{string.Join(", ", skill.OutputModes ?? [])}}]"
                }
                """,
            };

            yield return AIFunctionFactory.Create(RunAgentAsync, options);
        }

        async Task<string> RunAgentAsync(string input, CancellationToken cancellationToken)
        {
            var response = await a2aAgent.RunAsync(input, cancellationToken: cancellationToken).ConfigureAwait(false);
            return response.Text;
        }
    }
}
