# experiments/harness/providers.py
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = ""  # API-level tool call ID, needed for sending results back


@dataclass
class ToolResult:
    tool_call_id: str
    name: str
    content: str


@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    tool_calls: Optional[list[ToolCall]] = None
    tool_results: Optional[list[ToolResult]] = None  # for tool result messages


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict


class BaseProvider:
    def __init__(self, model: str):
        self.model = model

    @property
    def name(self) -> str:
        raise NotImplementedError

    def send(
        self,
        system_prompt: str,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> Message:
        raise NotImplementedError


class AnthropicProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "anthropic"

    def _build_messages(self, messages: list[Message]) -> list[dict]:
        """Convert Message list to Anthropic API format, handling tool results."""
        api_messages = []
        for msg in messages:
            if msg.tool_results:
                # Tool result message: Anthropic expects role=user with tool_result content blocks
                content = [
                    {
                        "type": "tool_result",
                        "tool_use_id": tr.tool_call_id,
                        "content": tr.content,
                    }
                    for tr in msg.tool_results
                ]
                api_messages.append({"role": "user", "content": content})
            elif msg.tool_calls:
                # Assistant message with tool calls: reconstruct content blocks
                content = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                api_messages.append({"role": "assistant", "content": content})
            else:
                api_messages.append({"role": msg.role, "content": msg.content})
        return api_messages

    def send(self, system_prompt, messages, tools=None):
        import anthropic

        client = anthropic.Anthropic()
        api_messages = self._build_messages(messages)

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": api_messages,
        }

        if tools:
            kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        response = client.messages.create(**kwargs)

        tool_calls = []
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(name=block.name, arguments=block.input, id=block.id))

        return Message(
            role="assistant",
            content="\n".join(text_parts),
            tool_calls=tool_calls if tool_calls else None,
        )


class OpenAIProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "openai"

    def _build_messages(self, system_prompt: str, messages: list[Message]) -> list[dict]:
        """Convert Message list to OpenAI API format, handling tool results."""
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            if msg.tool_results:
                # Each tool result is a separate message with role=tool
                for tr in msg.tool_results:
                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tr.tool_call_id,
                        "content": tr.content,
                    })
            elif msg.tool_calls:
                # Assistant message with tool calls
                tc_list = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
                api_messages.append({
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": tc_list,
                })
            else:
                api_messages.append({"role": msg.role, "content": msg.content})
        return api_messages

    def send(self, system_prompt, messages, tools=None):
        import openai

        client = openai.OpenAI()
        api_messages = self._build_messages(system_prompt, messages)

        kwargs = {"model": self.model, "messages": api_messages}

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    id=tc.id,
                )
                for tc in choice.tool_calls
            ]

        return Message(
            role="assistant",
            content=choice.content or "",
            tool_calls=tool_calls,
        )


class GoogleProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "google"

    def send(self, system_prompt, messages, tools=None):
        from google import genai
        from google.genai import types

        client = genai.Client()

        contents = []
        for msg in messages:
            if msg.tool_results:
                # Google uses function_response parts
                parts = [
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tr.name,
                            response={"result": tr.content},
                        )
                    )
                    for tr in msg.tool_results
                ]
                contents.append(types.Content(role="user", parts=parts))
            elif msg.tool_calls:
                # Assistant message with function calls
                parts = []
                if msg.content:
                    parts.append(types.Part(text=msg.content))
                for tc in msg.tool_calls:
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=tc.name, args=tc.arguments
                        )
                    ))
                contents.append(types.Content(role="model", parts=parts))
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )

        if tools:
            config.tools = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name,
                            description=t.description,
                            parameters=t.parameters,
                        )
                        for t in tools
                    ]
                )
            ]

        response = client.models.generate_content(
            model=self.model, contents=contents, config=config
        )

        tool_calls = None
        text = ""

        if response.candidates and response.candidates[0].content.parts:
            text_parts = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)
                if hasattr(part, "function_call") and part.function_call:
                    if tool_calls is None:
                        tool_calls = []
                    fc = part.function_call
                    tool_calls.append(
                        ToolCall(
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                            id=f"google-{fc.name}-{len(tool_calls or [])}",
                        )
                    )
            text = "\n".join(text_parts)

        return Message(role="assistant", content=text, tool_calls=tool_calls)


def _openai_compatible_build_messages(system_prompt: str, messages: list[Message]) -> list[dict]:
    """Shared message builder for OpenAI-compatible APIs (OpenAI, MiniMax, OpenRouter)."""
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        if msg.tool_results:
            for tr in msg.tool_results:
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": tr.tool_call_id,
                    "content": tr.content,
                })
        elif msg.tool_calls:
            tc_list = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in msg.tool_calls
            ]
            api_messages.append({
                "role": "assistant",
                "content": msg.content or None,
                "tool_calls": tc_list,
            })
        else:
            api_messages.append({"role": msg.role, "content": msg.content})
    return api_messages


class MiniMaxProvider(BaseProvider):
    """MiniMax uses OpenAI-compatible API."""

    @property
    def name(self) -> str:
        return "minimax"

    def send(self, system_prompt, messages, tools=None):
        import openai
        import os

        client = openai.OpenAI(
            api_key=os.environ.get("MINIMAX_API_KEY"),
            base_url="https://api.minimax.io/v1",
        )

        api_messages = _openai_compatible_build_messages(system_prompt, messages)
        kwargs = {"model": self.model, "messages": api_messages}

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    id=tc.id,
                )
                for tc in choice.tool_calls
            ]

        return Message(
            role="assistant",
            content=choice.content or "",
            tool_calls=tool_calls,
        )


class OpenRouterProvider(BaseProvider):
    """Routes to any model via OpenRouter (OpenAI-compatible API)."""

    def __init__(self, model: str):
        super().__init__(model)
        self._display_name = f"openrouter:{model}"

    @property
    def name(self) -> str:
        return self._display_name

    def send(self, system_prompt, messages, tools=None):
        import openai
        import os

        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        api_messages = _openai_compatible_build_messages(system_prompt, messages)
        kwargs = {"model": self.model, "messages": api_messages}

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    id=tc.id,
                )
                for tc in choice.tool_calls
            ]

        return Message(
            role="assistant",
            content=choice.content or "",
            tool_calls=tool_calls,
        )


_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "minimax": MiniMaxProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(provider_name: str, model: str) -> BaseProvider:
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_name}")
    return cls(model)
