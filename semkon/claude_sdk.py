import asyncio
import os
from pathlib import Path
from typing import Any, Literal, TypeVar

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from pydantic import BaseModel

from .data_models import CorrectnessExplanation, PropertyLocation
from .prompts import CORRECTNESS


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)

CLAUDE_CODE_OAUTH_TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

CLAUDE_CODE_OPUS_MODEL = "opus"
CLAUDE_CODE_HAIKU_MODEL = "haiku"

AnthropicAuthMode = Literal["oauth", "api_key"]


def anthropic_auth_mode() -> AnthropicAuthMode:
    if os.environ.get(CLAUDE_CODE_OAUTH_TOKEN_ENV):
        return "oauth"
    if os.environ.get(ANTHROPIC_API_KEY_ENV):
        return "api_key"
    raise RuntimeError(
        f"Set either {CLAUDE_CODE_OAUTH_TOKEN_ENV} or "
        f"{ANTHROPIC_API_KEY_ENV}."
    )


def anthropic_auth_description() -> str:
    mode = anthropic_auth_mode()
    if mode == "oauth":
        return "Anthropic via Claude Code OAuth"
    return "Anthropic API key"


def claude_agent_env_overrides() -> dict[str, str]:
    mode = anthropic_auth_mode()
    if mode == "oauth":
        return {ANTHROPIC_API_KEY_ENV: ""}
    return {}


def structured_output_format(model_type: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "schema": model_type.model_json_schema(),
    }


def _run_query_sync(prompt: str, options: ClaudeAgentOptions) -> Any:
    stderr_chunks: list[str] = []
    existing_stderr = options.stderr

    def capture_stderr(chunk: str) -> None:
        stderr_chunks.append(chunk)
        if existing_stderr is not None:
            existing_stderr(chunk)

    options.stderr = capture_stderr

    async def _inner() -> Any:
        ret = None
        error_result = None
        try:
            # Have to let the async generator run to completion to avoid errors.
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, ResultMessage):
                    if message.is_error:
                        error_result = message.result
                    else:
                        ret = message.structured_output
        except Exception as exc:
            if error_result:
                raise RuntimeError(f"Claude Code error: {error_result}") from exc
            raise

        if error_result:
            raise RuntimeError(f"Claude Code error: {error_result}")
        if ret is None:
            raise RuntimeError("No structured output received")
        return ret

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_inner())
    except Exception as exc:
        stderr = "".join(stderr_chunks).strip()
        if stderr:
            raise RuntimeError(
                f"{exc}\nClaude Code stderr:\n{stderr}"
            ) from exc
        raise
    finally:
        loop.close()


async def run_structured_query(
    prompt: str,
    options: ClaudeAgentOptions,
    model_type: type[TBaseModel],
) -> TBaseModel:
    # Have to use to_thread or there are errors.
    structured = await asyncio.to_thread(_run_query_sync, prompt, options)
    return model_type.model_validate(structured)


async def check_proof(
    directory: Path,
    property_location: PropertyLocation,
) -> CorrectnessExplanation:
    prompt = CORRECTNESS.format(
        rel_path=property_location.rel_path,
        line_num=property_location.line_num,
    )

    options = ClaudeAgentOptions(
        model=CLAUDE_CODE_OPUS_MODEL,
        output_format=structured_output_format(CorrectnessExplanation),
        cwd=directory,
        allowed_tools=["Read", "Bash", "WebFetch", "WebSearch"],
        env=claude_agent_env_overrides(),
        effort="high",
    )

    return await run_structured_query(
        prompt,
        options,
        CorrectnessExplanation,
    )
