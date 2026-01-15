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
}

public record BackendRootResponse(string Message);