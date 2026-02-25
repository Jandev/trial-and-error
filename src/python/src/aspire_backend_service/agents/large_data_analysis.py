import logging
import os
from typing import Annotated, Any, cast

from agent_framework import tool
from agent_framework.azure import AzureAIAgentsProvider
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import AzureCliCredential
from pydantic import BaseModel, ConfigDict, Field

from aspire_backend_service.infrastructure.data_access import (
    get_customer_information,
)

logger = logging.getLogger(__name__)


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
            5. get_all_customer_data() - Retrieves all sanitized customer data from the database

            IMPORTANT: You MUST use these tools to solve data analysis problems. Follow these rules STRICTLY:
            - STEP 1 (MANDATORY): ALWAYS call get_all_customer_data() FIRST before performing ANY calculation.
            - Store the returned dataset and pass it as the 'records' argument into ALL other calculation tools.
            - STEP 2: After loading the data, call the appropriate calculation tools using the returned dataset.
            - For statistical analysis, use calculate_mean and calculate_standard_deviation in sequence.
            - Use calculate_median when median values are required.
            - For identifying unusual values, use find_outliers with an appropriate threshold.
            - NEVER guess, manually compute values, or fabricate data.
            - ONLY use the money columns 'FGPMedianValue' and 'GrossToNet' for ALL calculations.
            - Every metric in your final answer MUST come from a tool call.
            - In your final response, clearly explain the exact sequence of tools used (data load first, then calculations).
            - Provide a summary of key findings and recommend actions based strictly on computed results.
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
                        get_all_customer_data,
                        calculate_mean,
                        calculate_median,
                        calculate_standard_deviation,
                        find_outliers,
                    ],
                )

                answer = await agent.run(
                    query, options={"response_format": large_data_analysis_response}
                )
                if not answer or not answer.value:
                    logger.error(
                        "Analysis agent returned empty or invalid response",
                        extra={"query": query},
                    )
                    return large_data_analysis_response(
                        summary="Analysis agent failed to return structured output.",
                        analysis_results={},
                        insights=["No structured JSON response was produced by the agent."],
                        algorithm_used="unknown",
                    )

                return answer.value

            finally:
                await agents_client.delete_agent(analysis_agent.id)

        return None


@tool(approval_mode="never_require")
def get_all_customer_data() -> list[dict[str, Any]]:
    """Retrieve all sanitized customer data from the database"""
    data = get_customer_information()
    return cast(list[dict[str, Any]], data)


@tool(approval_mode="never_require")
def calculate_mean(
    records: Annotated[
        list[dict[str, Any]],
        Field(description="List of customer data records retrieved from get_all_customer_data"),
    ],
    column: Annotated[
        str,
        Field(
            description="Money column to calculate the mean for (e.g., FGPMedianValue, GrossToNet)"
        ),
    ],
) -> float:
    """Calculate the mean (average) of a list of numeric values"""
    values: list[float] = [
        float(r[column]) for r in records if column in r and isinstance(r[column], (int, float))
    ]
    if not values:
        return 0.0
    return sum(values) / len(values)


@tool(approval_mode="never_require")
def calculate_median(
    records: Annotated[
        list[dict[str, Any]],
        Field(description="List of customer data records retrieved from get_all_customer_data"),
    ],
    column: Annotated[
        str,
        Field(
            description="Money column to calculate the median for (e.g., FGPMedianValue, GrossToNet)"
        ),
    ],
) -> float:
    """Calculate the median of a list of numeric values"""
    values: list[float] = [
        float(r[column]) for r in records if column in r and isinstance(r[column], (int, float))
    ]
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
    records: Annotated[
        list[dict[str, Any]],
        Field(description="List of customer data records retrieved from get_all_customer_data"),
    ],
    column: Annotated[
        str,
        Field(
            description="Money column to calculate standard deviation for (e.g., FGPMedianValue, GrossToNet)"
        ),
    ],
) -> float:
    """Calculate the standard deviation of a list of numeric values"""
    values: list[float] = [
        float(r[column]) for r in records if column in r and isinstance(r[column], (int, float))
    ]
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance**0.5


@tool(approval_mode="never_require")
def find_outliers(
    records: Annotated[
        list[dict[str, Any]],
        Field(description="List of customer data records retrieved from get_all_customer_data"),
    ],
    column: Annotated[
        str,
        Field(description="Money column to find outliers in (e.g., FGPMedianValue, GrossToNet)"),
    ],
    threshold: Annotated[
        float,
        Field(
            description="Number of standard deviations from mean to consider as outlier (typically 2-3)"
        ),
    ] = 2.0,
) -> dict[str, Any]:
    """Identify outliers in a dataset using standard deviation threshold"""
    values: list[float] = [
        float(r[column]) for r in records if column in r and isinstance(r[column], (int, float))
    ]
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
