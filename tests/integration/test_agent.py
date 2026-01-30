"""Integration tests for agent loop."""

import pytest
from pydantic import BaseModel
from typing import Literal

from conduit.agent import AgentResult, make_agent, tool_loop
from conduit.errors import MaxIterationsError
from conduit.providers.mock import MockModel
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.schema.responses import Response, ToolCall, FunctionCall, Usage
from conduit.tools import Tool


class WeatherParams(BaseModel):
    """Weather tool parameters."""
    location: str
    unit: Literal["celsius", "fahrenheit"] = "celsius"


def get_weather(params: WeatherParams) -> dict:
    """Mock weather function."""
    return {"temp": 72, "condition": "sunny", "location": params.location}


@pytest.mark.asyncio
async def test_tool_loop_no_tools():
    """Test tool loop with no tool calls (direct response)."""
    model = MockModel(response_content="Hello!")
    
    result = await tool_loop(
        model=model,
        messages=[Message(role="user", content="Hi")],
        tools=[]
    )
    
    assert isinstance(result, AgentResult)
    assert result.iterations == 1
    assert result.response.extract_content() == "Hello!"
    assert len(result.tool_calls_made) == 0
    assert len(result.messages) == 2  # user + assistant


@pytest.mark.asyncio
async def test_tool_loop_with_tool_call():
    """Test tool loop with one tool call."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    # First response: tool call
    tool_call_response = Response(
        content="I'll check the weather.",
        usage=Usage(input_tokens=10, output_tokens=5),
        tool_calls=[
            ToolCall(
                id="call_1",
                function=FunctionCall(
                    name="get_weather",
                    arguments={"location": "Tokyo"}
                )
            )
        ]
    )
    
    # Second response: final answer
    final_response = Response(
        content="The weather in Tokyo is sunny, 72°F.",
        usage=Usage(input_tokens=15, output_tokens=10)
    )
    
    model = MockModel(
        responses=[tool_call_response, final_response]
    )
    
    result = await tool_loop(
        model=model,
        messages=[Message(role="user", content="What's the weather in Tokyo?")],
        tools=[weather_tool],
        max_iterations=5
    )
    
    assert result.iterations == 2
    assert "Tokyo" in result.response.extract_content()
    assert len(result.tool_calls_made) == 1
    assert result.tool_calls_made[0].function.name == "get_weather"
    # Should have: user, assistant (with tool call), tool result, assistant (final)
    assert len(result.messages) >= 3


@pytest.mark.asyncio
async def test_tool_loop_max_iterations():
    """Test tool loop exceeding max iterations."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    # Always return tool call (infinite loop)
    tool_call_response = Response(
        content="Checking...",
        usage=Usage(input_tokens=10, output_tokens=5),
        tool_calls=[
            ToolCall(
                id="call_1",
                function=FunctionCall(
                    name="get_weather",
                    arguments={"location": "Tokyo"}
                )
            )
        ]
    )
    
    model = MockModel(response=tool_call_response)
    
    with pytest.raises(MaxIterationsError) as exc_info:
        await tool_loop(
            model=model,
            messages=[Message(role="user", content="Test")],
            tools=[weather_tool],
            max_iterations=3
        )
    
    assert "3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_loop_callbacks():
    """Test tool loop with callbacks."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    tool_call_response = Response(
        content="Checking...",
        usage=Usage(input_tokens=10, output_tokens=5),
        tool_calls=[
            ToolCall(
                id="call_1",
                function=FunctionCall(
                    name="get_weather",
                    arguments={"location": "Tokyo"}
                )
            )
        ]
    )
    
    final_response = Response(
        content="Done!",
        usage=Usage(input_tokens=15, output_tokens=5)
    )
    
    model = MockModel(responses=[tool_call_response, final_response])
    
    tool_calls_received = []
    responses_received = []
    
    def on_tool_call(tool_call: ToolCall):
        tool_calls_received.append(tool_call)
    
    def on_response(response: Response, iteration: int):
        responses_received.append((response, iteration))
    
    result = await tool_loop(
        model=model,
        messages=[Message(role="user", content="Test")],
        tools=[weather_tool],
        on_tool_call=on_tool_call,
        on_response=on_response,
        max_iterations=5
    )
    
    assert len(tool_calls_received) == 1
    assert tool_calls_received[0].function.name == "get_weather"
    assert len(responses_received) == 2  # tool call response + final response
    assert responses_received[0][1] == 1  # First iteration
    assert responses_received[1][1] == 2  # Second iteration


@pytest.mark.asyncio
async def test_make_agent():
    """Test make_agent helper function."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    model = MockModel(response_content="Hello!")
    
    agent = make_agent(
        model=model,
        tools=[weather_tool],
        system_message="You are helpful.",
        max_iterations=5
    )
    
    result = await agent.ainvoke("What's the weather?")
    
    assert isinstance(result, AgentResult)
    assert len(result.messages) >= 2
    # Should have system message
    assert result.messages[0].role == "system"
    assert result.messages[0].content == "You are helpful."
    assert result.messages[1].role == "user"
    assert result.messages[1].content == "What's the weather?"


def test_make_agent_sync():
    """Test make_agent with synchronous invoke."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    model = MockModel(response_content="Hello!")
    
    agent = make_agent(
        model=model,
        tools=[weather_tool],
        system_message="You are helpful.",
        max_iterations=5
    )
    
    # Test synchronous invoke
    result = agent.invoke("What's the weather?")
    
    assert isinstance(result, AgentResult)
    assert len(result.messages) >= 2
    assert result.messages[0].role == "system"
    assert result.messages[0].content == "You are helpful."
    assert result.messages[1].role == "user"
    assert result.messages[1].content == "What's the weather?"


@pytest.mark.asyncio
async def test_tool_loop_multiple_tool_calls():
    """Test tool loop with multiple tool calls in one response."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    # Response with multiple tool calls
    multi_tool_response = Response(
        content="Let me check multiple locations.",
        usage=Usage(input_tokens=10, output_tokens=5),
        tool_calls=[
            ToolCall(
                id="call_1",
                function=FunctionCall(
                    name="get_weather",
                    arguments={"location": "Tokyo"}
                )
            ),
            ToolCall(
                id="call_2",
                function=FunctionCall(
                    name="get_weather",
                    arguments={"location": "Paris"}
                )
            )
        ]
    )
    
    final_response = Response(
        content="Both locations are sunny.",
        usage=Usage(input_tokens=15, output_tokens=5)
    )
    
    model = MockModel(responses=[multi_tool_response, final_response])
    
    result = await tool_loop(
        model=model,
        messages=[Message(role="user", content="Compare weather")],
        tools=[weather_tool],
        max_iterations=5
    )
    
    assert result.iterations == 2
    assert len(result.tool_calls_made) == 2
    assert result.tool_calls_made[0].function.arguments["location"] == "Tokyo"
    assert result.tool_calls_made[1].function.arguments["location"] == "Paris"
