"""Example: Tool calling.

Demonstrates function calling with tools.
"""

import asyncio
import os

from conduit.providers.mock import MockModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message
from conduit.tools import Tool
from pydantic import BaseModel


# Define tool parameters
class WeatherParams(BaseModel):
    """Parameters for weather tool."""
    location: str


def get_weather(params: WeatherParams) -> str:
    """Get weather for a location."""
    return f"Weather in {params.location}: 72°F, sunny"


# Create tool
weather_tool = Tool(
    name="get_weather",
    description="Get current weather for a location",
    parameters=WeatherParams,
    fn=get_weather,
)


async def main() -> None:
    """Run tool calling example."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        model = OpenAIModel(api_key=api_key, model="gpt-4")
        from conduit.schema.options import ChatOptions
        options = ChatOptions(tools=[weather_tool.to_json_schema()])
        response = await model.chat(
            [Message(role="user", content="What's the weather in Tokyo?")],
            options=options,
        )
        
        # Check for tool calls
        if response.tool_calls:
            print("Model requested tool calls:")
            for tool_call in response.tool_calls:
                print(f"  - {tool_call.function.name}({tool_call.function.arguments})")
        else:
            print("Response:", response.extract_content())
    else:
        # Mock model with tool calling
        from conduit.schema.responses import Response, ToolCall, FunctionCall
        
        from conduit.schema.responses import Usage
        mock_response = Response(
            content="",
            usage=Usage(input_tokens=10, output_tokens=5),
            tool_calls=[
                ToolCall(
                    id="call_123",
                    type="function",
                    function=FunctionCall(
                        name="get_weather",
                        arguments={"location": "Tokyo"}
                    )
                )
            ]
        )
        model = MockModel(response=mock_response)
        response = await model.chat([
            Message(role="user", content="What's the weather in Tokyo?")
        ])
        
        if response.tool_calls:
            print("Model requested tool calls:")
            for tool_call in response.tool_calls:
                print(f"  - {tool_call.function.name}({tool_call.function.arguments})")
                # Execute tool
                result = await weather_tool.execute(tool_call.function.arguments)
                print(f"Tool result: {result}")
        print("(Using mock model - set OPENAI_API_KEY for real API)")


if __name__ == "__main__":
    asyncio.run(main())
