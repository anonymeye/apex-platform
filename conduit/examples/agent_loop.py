"""Example: Agent loop with tool execution.

Demonstrates autonomous agent that can use tools to complete tasks.
"""

import asyncio
import os

from conduit.agent import make_agent
from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.tools import Tool
from pydantic import BaseModel


# Define tools
class CalculatorParams(BaseModel):
    """Parameters for calculator tool."""
    expression: str


def calculate(params: CalculatorParams) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(params.expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


class SearchParams(BaseModel):
    """Parameters for search tool."""
    query: str


def search(params: SearchParams) -> str:
    """Search for information."""
    return f"Search results for: {params.query}"


calculator_tool = Tool(
    name="calculate",
    description="Evaluate a mathematical expression",
    parameters=CalculatorParams,
    fn=calculate,
)

search_tool = Tool(
    name="search",
    description="Search for information",
    parameters=SearchParams,
    fn=search,
)


async def main() -> None:
    """Run agent loop example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        agent = make_agent(
            model=model,
            tools=[calculator_tool, search_tool],
            system_message="You are a helpful assistant that can calculate and search.",
            max_iterations=5,
        )
        result = await agent.ainvoke("What is 15 * 23? Then search for Python programming.")
        print("Final response:", result.response.extract_content())
        print(f"Iterations: {result.iterations}")
    else:
        # Mock agent for demonstration
        model = MockModel(response_content="15 * 23 = 345. Here are search results for Python programming...")
        agent = make_agent(
            model=model,
            tools=[calculator_tool, search_tool],
            system_message="You are a helpful assistant.",
            max_iterations=5,
        )
        result = await agent.ainvoke("What is 15 * 23?")
        print("Final response:", result.response.extract_content())
        print("(Using mock model - set OPENAI_API_KEY for real agent)")


if __name__ == "__main__":
    asyncio.run(main())
