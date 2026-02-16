import os
from math import sqrt
from typing import Annotated

from agent_framework import tool
from agent_framework.azure import AzureAIAgentsProvider
from azure.ai.agents.aio import AgentsClient
from azure.identity.aio import AzureCliCredential
from pydantic import BaseModel, ConfigDict, Field


class calculator_response(BaseModel):
    """Structured calculator response"""

    final_number: float
    reasoning: str
    chain_of_thought: str
    answer: str
    model_config = ConfigDict(extra="forbid")


class calculator:
    async def run(self, question: str) -> calculator_response | None:
        async with (
            AzureCliCredential() as credential,
            AgentsClient(
                endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], credential=credential
            ) as agents_client,
            AzureAIAgentsProvider(credential=credential) as provider,
        ):
            agent_instructions = """You are a calculator agent with access to the following tools:
            1. count_letters(character, phrase) - Counts how many times a specific character appears in a word or phrase
            2. calculate_square_root(number) - Calculates the square root of a number
            
            IMPORTANT: You MUST use these tools to solve problems. Follow these rules:
            - When asked to count characters/letters in a word or phrase, ALWAYS call the count_letters tool
            - When asked to calculate square roots, ALWAYS call the calculate_square_root tool
            - If a question requires multiple steps (e.g., "find the square root of the count"), call the tools in sequence:
              * First, call count_letters to get the count
              * Then, call calculate_square_root with the result from count_letters
            - NEVER guess or manually calculate - always use the provided tools
            - In your final response, explain which tools you used and show the chain of calculations
            """

            calculator_agent = await agents_client.create_agent(
                model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
                name="CalculatorAgent",
                instructions=agent_instructions,
                # Adding this yields in an error `TypeError: ClientSession._request() got an unexpected keyword argument 'default_options'`.
                # default_options={"response_format": calculator_response},
                # Adding tools over here yields in a `Object of type FunctionTool is not JSON serializable`-error.
                # tools= [count_letters]
            )

            try:
                agent = await provider.get_agent(
                    calculator_agent.id, tools=[count_letters, calculate_square_root]
                )

                answer = await agent.run(question, options={"response_format": calculator_response})
                return answer.value

            finally:
                await agents_client.delete_agent(calculator_agent.id)

        return None


@tool(approval_mode="never_require")
def count_letters(
    character: Annotated[
        str, Field(description="The character that needs to be counted in the string.")
    ],
    phrase: Annotated[
        str, Field(description="The word or phrase that needs its characters counted.")
    ],
) -> int:
    """Count the number of specified characters in a specific word or phrase"""
    counted_characters = phrase.count(character)
    return counted_characters


@tool(approval_mode="never_require")
def calculate_square_root(
    number: Annotated[
        float, Field(description="The number you want the square root to be calculated for.")
    ],
) -> float:
    """Calculate the square root of the provided number and return it."""
    square_root = sqrt(number)
    return square_root
