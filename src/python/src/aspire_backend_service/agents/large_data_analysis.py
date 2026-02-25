import logging
import os
from typing import Any, Protocol

from agent_framework import tool
from agent_framework.azure import AzureAIAgentsProvider
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import AzureCliCredential
from pydantic import BaseModel, ConfigDict

from aspire_backend_service.infrastructure.data_access import (
    get_customer_information,
)

logger = logging.getLogger(__name__)


# ============================================================
# Response Model
# ============================================================


class LargeDataAnalysisResponse(BaseModel):
    summary: str
    analysis_results: dict[str, Any]
    insights: list[str]
    algorithm_used: str
    model_config = ConfigDict(extra="allow")


# ============================================================
# Data Provider Abstraction
# ============================================================


class CustomerDataProvider(Protocol):
    async def get_records(self) -> list[dict[str, Any]]: ...


class DatabaseCustomerDataProvider:
    async def get_records(self) -> list[dict[str, Any]]:
        data = get_customer_information()
        return list(data)  # ensure concrete list for typing


# ============================================================
# Data Analysis Service (Request Scoped)
# ============================================================


class DataAnalysisService:
    def __init__(self, provider: CustomerDataProvider) -> None:
        self._provider = provider
        self._data: list[dict[str, Any]] | None = None

    async def _ensure_loaded(self) -> None:
        if self._data is None:
            self._data = await self._provider.get_records()

    async def _values(self, column: str) -> list[float]:
        await self._ensure_loaded()
        assert self._data is not None

        return [
            float(r[column])
            for r in self._data
            if column in r and isinstance(r[column], (int, float))
        ]

    async def mean(self, column: str) -> float:
        values = await self._values(column)
        if not values:
            return 0.0
        return sum(values) / len(values)

    async def median(self, column: str) -> float:
        values = await self._values(column)
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)

        if n % 2:
            return sorted_values[n // 2]

        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    async def std_dev(self, column: str) -> float:
        values = await self._values(column)

        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance**0.5

    async def find_outliers(self, column: str, threshold: float = 2.0) -> dict[str, Any]:
        values = await self._values(column)

        if len(values) < 2:
            return {"outliers": [], "threshold": threshold}

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        std_dev = variance**0.5

        if std_dev == 0:
            return {
                "outliers": [],
                "threshold": threshold,
                "mean": mean,
                "std_dev": std_dev,
            }

        outliers = [x for x in values if abs(x - mean) > threshold * std_dev]

        return {
            "outliers": outliers,
            "threshold": threshold,
            "mean": mean,
            "std_dev": std_dev,
            "outlier_count": len(outliers),
        }


# ============================================================
# Agent Orchestrator
# ============================================================


class large_data_analysis:
    async def run(self, query: str) -> LargeDataAnalysisResponse | None:
        async with (
            AzureCliCredential() as credential,
            AgentsClient(
                endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
                credential=credential,
            ) as agents_client,
            AzureAIAgentsProvider(credential=credential) as provider,
        ):
            instructions = """
You are a data analysis agent.

Customer data is preloaded server-side and cannot be accessed directly.
You MUST use the provided statistical tools.

Rules:
- NEVER fabricate values.
- ONLY use money columns 'FGPMedianValue' and 'GrossToNet'.
- Every metric MUST come from a tool call.
- Explain the exact sequence of tools used.
- Mention how many records have been processed (count)
"""

            analysis_agent = await agents_client.create_agent(
                model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
                name="DataAnalysisAgent",
                instructions=instructions,
            )

            try:
                service = DataAnalysisService(provider=DatabaseCustomerDataProvider())

                @tool(approval_mode="never_require")
                async def calculate_mean(column: str) -> float:
                    return await service.mean(column)

                @tool(approval_mode="never_require")
                async def calculate_median(column: str) -> float:
                    return await service.median(column)

                @tool(approval_mode="never_require")
                async def calculate_standard_deviation(column: str) -> float:
                    return await service.std_dev(column)

                @tool(approval_mode="never_require")
                async def find_outliers(column: str, threshold: float = 2.0) -> dict[str, Any]:
                    return await service.find_outliers(column, threshold)

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
                    query,
                    options={"response_format": LargeDataAnalysisResponse},
                )

                if not answer or not answer.value:
                    logger.error("Agent returned empty response")
                    return LargeDataAnalysisResponse(
                        summary="Agent failed to return structured output.",
                        analysis_results={},
                        insights=["No structured response produced."],
                        algorithm_used="unknown",
                    )

                return answer.value

            finally:
                await agents_client.delete_agent(analysis_agent.id)

        return None
