import os
from typing import Annotated, Any

from agent_framework import tool
from agent_framework.azure import AzureAIAgentsProvider
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import AzureCliCredential
from pydantic import BaseModel, ConfigDict, Field


class large_data_analysis_response(BaseModel):
    """Structured large data analysis response"""

    summary: str
    analysis_results: dict[str, Any]
    insights: list[str]
    algorithm_used: str
    model_config = ConfigDict(extra="allow")


class large_data_analysis:
    async def run(self, query: str) -> large_data_analysis_response | None:
        async with (
            AzureCliCredential() as credential,
            AgentsClient(
                endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential
            ) as agents_client,
            AzureAIAgentsProvider(credential=credential) as provider,
        ):
            agent_instructions = """You are a data analysis agent with access to the following tools:
            1. calculate_mean(values) - Calculates the mean (average) of a list of numeric values
            2. calculate_median(values) - Calculates the median of a list of numeric values
            3. calculate_standard_deviation(values) - Calculates the standard deviation of numeric values
            4. find_outliers(values, threshold) - Identifies outliers in a dataset using a threshold

            IMPORTANT: You MUST use these tools to solve data analysis problems. Follow these rules:
            - When asked to analyze data, ALWAYS call the appropriate analysis tools
            - For statistical analysis, use calculate_mean and calculate_standard_deviation in sequence
            - For identifying unusual values, use find_outliers with an appropriate threshold
            - NEVER guess or manually calculate - always use the provided tools
            - In your final response, explain which tools you used and what insights were discovered
            - Provide a summary of key findings and recommend actions based on the analysis
            """

            analysis_agent = await agents_client.create_agent(
                model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
                name="DataAnalysisAgent",
                instructions=agent_instructions,
            )

            try:
                agent = await provider.get_agent(
                    analysis_agent.id,
                    tools=[
                        calculate_mean,
                        calculate_median,
                        calculate_standard_deviation,
                        find_outliers,
                    ],
                )

                answer = await agent.run(
                    query, options={"response_format": large_data_analysis_response}
                )
                return answer.value

            finally:
                await agents_client.delete_agent(analysis_agent.id)

        return None


@tool(approval_mode="never_require")
def calculate_mean(
    values: Annotated[
        list[float], Field(description="List of numeric values to calculate the mean for")
    ],
) -> float:
    """Calculate the mean (average) of a list of numeric values"""
    if not values:
        return 0.0
    return sum(values) / len(values)


@tool(approval_mode="never_require")
def calculate_median(
    values: Annotated[
        list[float], Field(description="List of numeric values to calculate the median for")
    ],
) -> float:
    """Calculate the median of a list of numeric values"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 1:
        return sorted_values[n // 2]
    else:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2


@tool(approval_mode="never_require")
def calculate_standard_deviation(
    values: Annotated[
        list[float], Field(description="List of numeric values to calculate standard deviation for")
    ],
) -> float:
    """Calculate the standard deviation of a list of numeric values"""
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance**0.5


@tool(approval_mode="never_require")
def find_outliers(
    values: Annotated[list[float], Field(description="List of numeric values to find outliers in")],
    threshold: Annotated[
        float,
        Field(
            description="Number of standard deviations from mean to consider as outlier (typically 2-3)"
        ),
    ] = 2.0,
) -> dict[str, Any]:
    """Identify outliers in a dataset using standard deviation threshold"""
    if not values or len(values) < 2:
        return {"outliers": [], "threshold": threshold}

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std_dev = variance**0.5

    if std_dev == 0:
        return {"outliers": [], "threshold": threshold, "mean": mean, "std_dev": std_dev}

    outliers = [x for x in values if abs(x - mean) > threshold * std_dev]
    return {
        "outliers": outliers,
        "threshold": threshold,
        "mean": mean,
        "std_dev": std_dev,
        "outlier_count": len(outliers),
    }
