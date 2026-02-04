"""Example: Synchronous agent usage.

Demonstrates how to use the agent in synchronous contexts (scripts, notebooks).
"""

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


calculator_tool = Tool(
    name="calculate",
    description="Evaluate a mathematical expression",
    parameters=CalculatorParams,
    fn=calculate,
)


def main() -> None:
    """Run synchronous agent example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        agent = make_agent(
            model=model,
            tools=[calculator_tool],
            system_message="You are a helpful calculator assistant.",
            max_iterations=5,
        )
        # Use synchronous invoke() method
        result = agent.invoke("What is 15 * 23 + 100?")
        print("Final response:", result.response.extract_content())
        print(f"Iterations: {result.iterations}")



    else:
        # Mock agent for demonstration
        model = MockModel(response_content="15 * 23 + 100 = 445")
        agent = make_agent(
            model=model,
            tools=[calculator_tool],
            system_message="You are a helpful assistant.",
            max_iterations=5,
        )
        result = agent.invoke("What is 15 * 23?")
        print("Final response:", result.response.extract_content())
        print("(Using mock model - set OPENAI_API_KEY for real agent)")


if __name__ == "__main__":
    # Note: This is synchronous - no asyncio.run() needed!
    main()
