"""Chat interaction handling service."""

import logging
import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from apex.interceptors import LLMMessageLoggingInterceptor
from apex.models.connection import Connection
from apex.repositories.agent_repository import AgentRepository
from apex.repositories.tool_repository import AgentToolRepository, ToolRepository
from apex.services.rag_tool_service import RAGToolService
from apex.storage.conversation_state import (
    ConversationState,
    ConversationStateMetadata,
)
from apex.storage.conversation_state_store import ConversationStateStore
from conduit.agent import make_agent
from conduit.providers.anthropic import AnthropicModel
from conduit.providers.groq import GroqModel
from conduit.providers.openai import OpenAIModel
from conduit.schema.messages import Message as ConduitMessage
from conduit.schema.options import ChatOptions
from conduit.schema.responses import ToolCall as ConduitToolCall

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions with agents."""

    def __init__(
        self,
        agent_repo: AgentRepository,
        tool_repo: ToolRepository,
        agent_tool_repo: AgentToolRepository,
        rag_tool_service: RAGToolService,
        conversation_state_store: ConversationStateStore | None = None,
    ):
        """Initialize chat service.

        Args:
            agent_repo: Agent repository
            tool_repo: Tool repository
            agent_tool_repo: AgentTool repository
            rag_tool_service: RAG tool service for creating conduit tools
            conversation_state_store: Optional Redis store for conversation state (messages + metadata)
        """
        self.agent_repo = agent_repo
        self.tool_repo = tool_repo
        self.agent_tool_repo = agent_tool_repo
        self.rag_tool_service = rag_tool_service
        self.conversation_state_store = conversation_state_store

    def _resolve_api_key(self, connection: Connection) -> str | None:
        """Resolve API key for a connection.

        Args:
            connection: Connection record

        Returns:
            API key string, or None if auth_type is 'none'

        Raises:
            ValueError: If a key is required but cannot be resolved
        """
        auth_type = (connection.auth_type or "").lower()
        if auth_type == "none":
            return None

        env_var = connection.api_key_env_var
        if not env_var:
            provider = (connection.provider or "").lower()
            env_var = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "groq": "GROQ_API_KEY",
                # Default for OpenAI-compatible self-hosted if user still wants auth via env
                "openai_compatible": "OPENAI_API_KEY",
            }.get(provider)

        if not env_var:
            raise ValueError("No api_key_env_var configured for connection")

        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"{env_var} environment variable not set for connection '{connection.name}'")

        return api_key

    def _create_model(self, connection: Connection, runtime_id: str):
        """Create a Conduit model instance from Connection + ModelRef runtime id."""
        provider = (connection.provider or "").lower()
        conn_type = (connection.connection_type or "").lower()
        base_url = connection.base_url
        api_key = self._resolve_api_key(connection)

        # Self-hosted OpenAI-compatible endpoints
        if conn_type == "openai_compatible" or provider == "openai_compatible":
            if not base_url:
                raise ValueError("base_url is required for openai_compatible connections")
            return OpenAIModel(api_key=api_key, model=runtime_id, base_url=base_url)

        # Vendor APIs
        if provider == "openai":
            if not api_key:
                raise ValueError("OPENAI_API_KEY (or api_key_env_var) must be set for OpenAI connections")
            return OpenAIModel(api_key=api_key, model=runtime_id, base_url=base_url or "https://api.openai.com/v1")

        if provider == "anthropic":
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY (or api_key_env_var) must be set for Anthropic connections")
            return AnthropicModel(api_key=api_key, model=runtime_id, base_url=base_url or "https://api.anthropic.com/v1")

        if provider == "groq":
            if not api_key:
                raise ValueError("GROQ_API_KEY (or api_key_env_var) must be set for Groq connections")
            return GroqModel(api_key=api_key, model=runtime_id, base_url=base_url or "https://api.groq.com/openai/v1")

        raise ValueError(f"Unsupported connection provider: {connection.provider}")

    @staticmethod
    def _stored_messages_to_conduit(messages: list[dict[str, Any]]) -> list[ConduitMessage]:
        """Convert stored message dicts to conduit Message list."""
        out: list[ConduitMessage] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                content = content  # Conduit allows list (content blocks)
            tool_calls_raw = m.get("tool_calls")
            tool_calls = (
                [ConduitToolCall(**tc) for tc in tool_calls_raw]
                if isinstance(tool_calls_raw, list) and tool_calls_raw
                else None
            )
            out.append(
                ConduitMessage(
                    role=role,
                    content=content,
                    name=m.get("name"),
                    tool_call_id=m.get("tool_call_id"),
                    tool_calls=tool_calls,
                )
            )
        return out

    @staticmethod
    def _conduit_message_to_stored(msg: ConduitMessage) -> dict[str, Any]:
        """Convert conduit Message to stored dict (JSON-serializable)."""
        d: dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.name is not None:
            d["name"] = msg.name
        if msg.tool_call_id is not None:
            d["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls is not None:
            d["tool_calls"] = [
                tc.model_dump() if hasattr(tc, "model_dump") else tc
                for tc in msg.tool_calls
            ]
        return d

    async def chat(
        self,
        agent_id: UUID,
        user_message: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
    ):
        """Chat with an agent.

        Args:
            agent_id: Agent ID
            user_message: User message
            organization_id: Organization ID (for authorization)
            user_id: Current user ID (for conversation state)
            conversation_id: Optional conversation ID for continuing a conversation

        Returns:
            Chat response with assistant message and metadata

        Raises:
            ValueError: If agent not found, unauthorized, or model creation fails
        """
        # Load conversation state when continuing a conversation
        state: ConversationState | None = None
        initial_messages: list[ConduitMessage] = []
        if conversation_id and self.conversation_state_store:
            state = await self.conversation_state_store.get(user_id, conversation_id)
            if state and state.messages:
                initial_messages = self._stored_messages_to_conduit(state.messages)

        # Get agent with tools
        agent = await self.agent_repo.get_with_tools(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        if agent.organization_id != organization_id:
            raise ValueError(f"Agent {agent_id} does not belong to organization {organization_id}")

        logger.info(f"Chatting with agent {agent_id} ({agent.name})")

        # Create model instance
        try:
            if not agent.model_ref or not agent.model_ref.connection:
                raise ValueError("Agent has no model_ref/connection configured")
            model = self._create_model(
                connection=agent.model_ref.connection,
                runtime_id=agent.model_ref.runtime_id,
            )
        except ValueError as e:
            logger.error(f"Failed to create model: {e}")
            raise

        # Load and convert tools
        conduit_tools = []
        if agent.agent_tools:
            for agent_tool in agent.agent_tools:
                tool_model = agent_tool.tool
                if tool_model.tool_type == "rag":
                    try:
                        conduit_tool = await self.rag_tool_service.create_conduit_tool_from_db(
                            tool_model, chat_model=model
                        )
                        conduit_tools.append(conduit_tool)
                        logger.info(f"Loaded RAG tool: {tool_model.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load tool {tool_model.name}: {e}")
                        # Continue with other tools
                else:
                    logger.warning(f"Tool type '{tool_model.tool_type}' not yet supported")

        # Create chat options
        chat_opts = ChatOptions()
        if agent.temperature is not None:
            chat_opts.temperature = agent.temperature
        if agent.max_tokens is not None:
            chat_opts.max_tokens = agent.max_tokens

        # Interceptor to log messages exchanged with the LLM (DEBUG for full exchange)
        llm_logger = logging.getLogger("apex.services.chat_service.llm")
        llm_logging_interceptor = LLMMessageLoggingInterceptor(
            logger=llm_logger,
            log_level=logging.DEBUG,
            content_max_len=500,
        )

        # Create agent and invoke
        try:
            logger.info(
                "Sending to LLM: %s",
                user_message[:300] + "..." if len(user_message) > 300 else user_message,
            )
            async with model:
                agent_instance = make_agent(
                    model=model,
                    tools=conduit_tools,
                    system_message=agent.system_message,
                    max_iterations=agent.max_iterations,
                    chat_opts=chat_opts,
                    interceptors=[llm_logging_interceptor],
                )
                result = await agent_instance.ainvoke(
                    user_message,
                    initial_messages=initial_messages if initial_messages else None,
                )
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            raise ValueError(f"Agent execution failed: {str(e)}")

        # Extract response content
        response_content = result.response.extract_content()
        logger.info(
            "LLM response received: %s",
            response_content[:300] + "..." if len(response_content) > 300 else response_content,
        )

        # Convert tool calls to response format
        tool_calls_response = None
        if result.tool_calls_made:
            tool_calls_response = [
                {
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "result": None,  # Tool results are in messages, not directly accessible here
                }
                for tool_call in result.tool_calls_made
            ]

        # Build usage response
        usage_response = None
        if result.response.usage:
            usage_response = {
                "input_tokens": result.response.usage.input_tokens,
                "output_tokens": result.response.usage.output_tokens,
                "total_tokens": result.response.usage.total_tokens,
                "cache_read_tokens": result.response.usage.cache_read_tokens,
                "cache_creation_tokens": result.response.usage.cache_creation_tokens,
            }

        # Generate message ID and timestamp
        message_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Persist conversation state when conversation_id and store are present
        if conversation_id and self.conversation_state_store:
            now = datetime.utcnow().isoformat() + "Z"
            # New messages from this turn: new user message + assistant/tool messages from result
            num_prior = len(initial_messages)
            new_from_result = result.messages[(num_prior + 2) :]  # skip system, prior, new user
            new_user_dict = {"role": "user", "content": user_message}
            new_stored = [new_user_dict] + [
                self._conduit_message_to_stored(m) for m in new_from_result
            ]
            if state is None:
                state = ConversationState(
                    messages=[],
                    metadata=ConversationStateMetadata(
                        conversation_id=str(conversation_id),
                        user_id=str(user_id),
                        agent_id=str(agent_id),
                        created_at=now,
                        last_activity_at=now,
                        message_count=0,
                    ),
                )
            state.messages.extend(new_stored)
            state.metadata.last_activity_at = now
            state.metadata.message_count = len(state.messages)
            await self.conversation_state_store.set(user_id, conversation_id, state)

        return {
            "id": message_id,
            "role": "assistant",
            "content": response_content,
            "timestamp": timestamp,
            "tool_calls": tool_calls_response,
            "iterations": result.iterations,
            "usage": usage_response,
        }
