"""Agent creation utilities."""

from conduit.agent.loop import AgentResult, tool_loop
from conduit.core.protocols import ChatModel
from conduit.interceptors.base import Interceptor
from conduit.schema.messages import Message
from conduit.schema.options import ChatOptions
from conduit.tools import Tool
from conduit.utils.async_utils import run_sync


class Agent:
    """Agent with sync and async support.
    
    Examples:
        Async usage (recommended for async contexts):
        >>> from conduit.providers.openai import OpenAIModel
        >>> model = OpenAIModel(api_key="sk-...")
        >>> agent = Agent(model, tools=[weather_tool])
        >>> result = await agent.ainvoke("What's the weather?")
        
        Sync usage (for scripts and notebooks without event loop):
        >>> result = agent.invoke("What's the weather?")
    """
    
    def __init__(
        self,
        model: ChatModel,
        tools: list[Tool],
        *,
        system_message: str | None = None,
        max_iterations: int = 10,
        chat_opts: ChatOptions | None = None,
        interceptors: list[Interceptor] | None = None,
    ):
        """Initialize agent.
        
        Args:
            model: ChatModel instance
            tools: Available tools for the agent
            system_message: Optional system message to prepend to all conversations
            max_iterations: Maximum number of loop iterations (default: 10)
            chat_opts: Optional chat options
            interceptors: Optional list of interceptors to apply to model calls
        """
        self.model = model
        self.tools = tools
        self.system_message = system_message
        self.max_iterations = max_iterations
        self.chat_opts = chat_opts
        self.interceptors = interceptors
    
    def _prepare_messages(self, user_message: str) -> list[Message]:
        """Prepare messages with optional system message."""
        messages: list[Message] = []
        if self.system_message:
            messages.append(Message(role="system", content=self.system_message))
        messages.append(Message(role="user", content=user_message))
        return messages
    
    async def ainvoke(self, user_message: str) -> AgentResult:
        """Invoke agent asynchronously.
        
        Args:
            user_message: User message to process
            
        Returns:
            AgentResult with response and metadata
        """
        messages = self._prepare_messages(user_message)
        return await tool_loop(
            model=self.model,
            messages=messages,
            tools=self.tools,
            max_iterations=self.max_iterations,
            chat_opts=self.chat_opts,
            interceptors=self.interceptors,
        )
    
    def invoke(self, user_message: str) -> AgentResult:
        """Invoke agent synchronously.
        
        Args:
            user_message: User message to process
            
        Returns:
            AgentResult with response and metadata
            
        Raises:
            RuntimeError: If called from async context (use ainvoke instead)
        """
        return run_sync(self.ainvoke(user_message))


def make_agent(
    model: ChatModel,
    tools: list[Tool],
    *,
    system_message: str | None = None,
    max_iterations: int = 10,
    chat_opts: ChatOptions | None = None,
    interceptors: list[Interceptor] | None = None,
) -> Agent:
    """Create an agent.

    This function creates an Agent instance that supports both sync and async invocation.

    Args:
        model: ChatModel instance
        tools: Available tools for the agent
        system_message: Optional system message to prepend to all conversations
        max_iterations: Maximum number of loop iterations (default: 10)
        chat_opts: Optional chat options
        interceptors: Optional list of interceptors to apply to model calls
                     (e.g., RetryInterceptor, CacheInterceptor, LoggingInterceptor)

    Returns:
        Agent instance with invoke() and ainvoke() methods

    Examples:
        Async usage:
        >>> from conduit.providers.openai import OpenAIModel
        >>> from conduit.interceptors.retry import RetryInterceptor
        >>>
        >>> model = OpenAIModel(api_key="sk-...")
        >>> agent = make_agent(
        ...     model=model,
        ...     tools=[weather_tool, search_tool],
        ...     system_message="You are a helpful assistant.",
        ...     max_iterations=5,
        ...     interceptors=[RetryInterceptor(max_attempts=3)],
        ... )
        >>> result = await agent.ainvoke("What's the weather in Tokyo?")
        >>> print(result.response.extract_content())
        
        Sync usage:
        >>> result = agent.invoke("What's the weather in Tokyo?")
        >>> print(result.response.extract_content())
    """
    return Agent(
        model=model,
        tools=tools,
        system_message=system_message,
        max_iterations=max_iterations,
        chat_opts=chat_opts,
        interceptors=interceptors,
    )
