using A2A;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

public class AgentCollaboration(BackendServiceClient backendServiceClient)
{

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

        return new A2aResult(question, "Nothing");
    }
    
    private static IEnumerable<AIFunction> CreateFunctionTools(AIAgent a2aAgent, AgentCard agentCard)
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
