using System.ComponentModel.DataAnnotations;

namespace AspireTrial.ApiService.Options;

/// <summary>
/// Configuration options for Azure AI Foundry
/// </summary>
public class AzureAIOptions
{
    public const string SectionName = "AzureAI";

    /// <summary>
    /// The Azure AI Project endpoint URL
    /// Format: https://your-project.services.ai.azure.com/api/projects/project-id
    /// </summary>
    [Required]
    [Url]
    public required string ProjectEndpoint { get; set; }

    /// <summary>
    /// The model deployment name to use for AI operations
    /// </summary>
    [Required]
    public required string ModelDeploymentName { get; set; }
}
