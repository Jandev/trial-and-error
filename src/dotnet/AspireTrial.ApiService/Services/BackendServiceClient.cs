public class BackendServiceClient(HttpClient httpClient)
{
    public async Task<BackendRootResponse> GetRoot()
    {
        var result = await httpClient.GetFromJsonAsync<BackendRootResponse>("/");
        if (result == null)
        {
            throw new InvalidOperationException("Failed to get root: response was null.");
        }
        return result;
    }

    public async Task<CountLettersResponse> GetCountLetters(string question)
    {
        var request = new CountLettersRequest(question);
        var result = await httpClient.PostAsJsonAsync("/agents/count-letters", request);
        if (result == null)
        {
            throw new InvalidOperationException("Failed to count letters: response was null.");
        }

        var response = await result.Content.ReadFromJsonAsync<CountLettersResponse>()
                            ?? new CountLettersResponse(0, string.Empty, string.Empty, string.Empty);
        return response;
    }

    public async Task<Tuple<string, HttpClient>> GetCountLettersAgentCardEndpoint()
    {
        var endpoint = "agents/count-letters/";
        return new Tuple<string, HttpClient>(httpClient.BaseAddress + endpoint, httpClient);
    }
}

public record BackendRootResponse(string Message);

public record CountLettersRequest(string Question);
public record CountLettersResponse(float FinalNumber, string Reasoning, string ChainOfThought, string Answer);
