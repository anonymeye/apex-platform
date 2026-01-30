"""Tests for tool system."""

import json
import pytest
from pydantic import BaseModel, Field
from typing import Literal

from conduit.errors import ToolExecutionError, ValidationError as ConduitValidationError
from conduit.schema.responses import FunctionCall, ToolCall
from conduit.tools import Tool, execute_tool_calls


class WeatherParams(BaseModel):
    """Weather tool parameters."""
    location: str = Field(..., description="City name")
    unit: Literal["celsius", "fahrenheit"] = "celsius"


class CalculatorParams(BaseModel):
    """Calculator tool parameters."""
    a: float
    b: float
    operation: Literal["add", "subtract", "multiply", "divide"]


def get_weather(params: WeatherParams) -> dict:
    """Mock weather function."""
    return {"temp": 72, "condition": "sunny", "location": params.location, "unit": params.unit}


def calculate(params: CalculatorParams) -> float:
    """Mock calculator function."""
    if params.operation == "add":
        return params.a + params.b
    elif params.operation == "subtract":
        return params.a - params.b
    elif params.operation == "multiply":
        return params.a * params.b
    elif params.operation == "divide":
        if params.b == 0:
            raise ValueError("Division by zero")
        return params.a / params.b
    else:
        raise ValueError(f"Unknown operation: {params.operation}")


def test_tool_creation():
    """Test creating a tool."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    assert tool.name == "get_weather"
    assert tool.description == "Get weather"
    assert tool.parameters == WeatherParams


def test_tool_name_validation():
    """Test tool name validation."""
    # Valid names
    Tool(name="valid_name", description="Test", parameters=WeatherParams, fn=get_weather)
    Tool(name="valid-name", description="Test", parameters=WeatherParams, fn=get_weather)
    Tool(name="valid_123", description="Test", parameters=WeatherParams, fn=get_weather)
    
    # Invalid names
    with pytest.raises(Exception):  # Pydantic validation error
        Tool(name="invalid name", description="Test", parameters=WeatherParams, fn=get_weather)
    with pytest.raises(Exception):
        Tool(name="invalid@name", description="Test", parameters=WeatherParams, fn=get_weather)


def test_tool_execute_success():
    """Test successful tool execution."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    result = tool.execute({"location": "Tokyo", "unit": "celsius"})
    assert result == {"temp": 72, "condition": "sunny", "location": "Tokyo", "unit": "celsius"}


def test_tool_execute_with_defaults():
    """Test tool execution with default parameters."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    result = tool.execute({"location": "Tokyo"})  # unit defaults to "celsius"
    assert result["unit"] == "celsius"


def test_tool_execute_validation_error():
    """Test tool execution with invalid arguments."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    with pytest.raises(ConduitValidationError):
        tool.execute({"location": "Tokyo", "unit": "invalid"})
    
    with pytest.raises(ConduitValidationError):
        tool.execute({"location": 123})  # Wrong type


def test_tool_execute_function_error():
    """Test tool execution when function raises error."""
    def failing_function(params: CalculatorParams) -> float:
        return params.a / params.b  # Will fail if b == 0
    
    tool = Tool(
        name="divide",
        description="Divide numbers",
        parameters=CalculatorParams,
        fn=failing_function
    )
    
    with pytest.raises(ToolExecutionError) as exc_info:
        tool.execute({"a": 10, "b": 0, "operation": "divide"})
    assert "divide" in str(exc_info.value)
    assert exc_info.value.tool_name == "divide"


def test_tool_to_json_schema():
    """Test converting tool to JSON Schema."""
    tool = Tool(
        name="get_weather",
        description="Get current weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    schema = tool.to_json_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "get_weather"
    assert schema["function"]["description"] == "Get current weather"
    assert "properties" in schema["function"]["parameters"]
    assert "location" in schema["function"]["parameters"]["properties"]
    assert "unit" in schema["function"]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_execute_tool_calls_success():
    """Test executing multiple tool calls successfully."""
    weather_tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    calc_tool = Tool(
        name="calculate",
        description="Calculate",
        parameters=CalculatorParams,
        fn=calculate
    )
    
    tool_calls = [
        ToolCall(
            id="call_1",
            function=FunctionCall(
                name="get_weather",
                arguments={"location": "Tokyo", "unit": "celsius"}
            )
        ),
        ToolCall(
            id="call_2",
            function=FunctionCall(
                name="calculate",
                arguments={"a": 10, "b": 5, "operation": "add"}
            )
        )
    ]
    
    results = await execute_tool_calls([weather_tool, calc_tool], tool_calls)
    
    assert len(results) == 2
    assert results[0]["role"] == "tool"
    assert results[0]["tool_call_id"] == "call_1"
    assert "Tokyo" in results[0]["content"]
    
    assert results[1]["role"] == "tool"
    assert results[1]["tool_call_id"] == "call_2"
    assert "15" in results[1]["content"]  # 10 + 5 = 15


@pytest.mark.asyncio
async def test_execute_tool_calls_missing_tool():
    """Test executing tool calls with missing tool."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    tool_calls = [
        ToolCall(
            id="call_1",
            function=FunctionCall(
                name="nonexistent_tool",
                arguments={"location": "Tokyo"}
            )
        )
    ]
    
    results = await execute_tool_calls([tool], tool_calls)
    
    assert len(results) == 1
    assert results[0]["role"] == "tool"
    assert "not found" in results[0]["content"].lower()


@pytest.mark.asyncio
async def test_execute_tool_calls_with_error():
    """Test executing tool calls when tool raises error."""
    calc_tool = Tool(
        name="calculate",
        description="Calculate",
        parameters=CalculatorParams,
        fn=calculate
    )
    
    tool_calls = [
        ToolCall(
            id="call_1",
            function=FunctionCall(
                name="calculate",
                arguments={"a": 10, "b": 0, "operation": "divide"}
            )
        )
    ]
    
    results = await execute_tool_calls([calc_tool], tool_calls)
    
    assert len(results) == 1
    assert results[0]["role"] == "tool"
    assert "Error" in results[0]["content"]


@pytest.mark.asyncio
async def test_execute_tool_calls_string_result():
    """Test tool execution with string result."""
    def string_tool(params: WeatherParams) -> str:
        return f"Weather in {params.location}: sunny"
    
    tool = Tool(
        name="weather_string",
        description="Get weather as string",
        parameters=WeatherParams,
        fn=string_tool
    )
    
    tool_calls = [
        ToolCall(
            id="call_1",
            function=FunctionCall(
                name="weather_string",
                arguments={"location": "Tokyo"}
            )
        )
    ]
    
    results = await execute_tool_calls([tool], tool_calls)
    assert results[0]["content"] == "Weather in Tokyo: sunny"


@pytest.mark.asyncio
async def test_execute_tool_calls_dict_result():
    """Test tool execution with dict result (converted to JSON)."""
    tool = Tool(
        name="get_weather",
        description="Get weather",
        parameters=WeatherParams,
        fn=get_weather
    )
    
    tool_calls = [
        ToolCall(
            id="call_1",
            function=FunctionCall(
                name="get_weather",
                arguments={"location": "Tokyo"}
            )
        )
    ]
    
    results = await execute_tool_calls([tool], tool_calls)
    # Dict should be converted to JSON string
    content = results[0]["content"]
    parsed = json.loads(content)
    assert parsed["location"] == "Tokyo"
    assert parsed["temp"] == 72
