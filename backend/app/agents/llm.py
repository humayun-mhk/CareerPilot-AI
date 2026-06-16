import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


def _copy_fallback(fallback: Any) -> Any:
    return json.loads(json.dumps(fallback)) if fallback is not None else {}


def _extract_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return json.loads(match.group(1))
    raise ValueError("LLM response did not contain valid JSON.")


def _openai_chat(prompt: str, input_data: dict[str, Any], json_mode: bool) -> str:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if provider != "openai" or not api_key or api_key == "your_api_key_here":
        raise RuntimeError("OpenAI API key is missing or provider is unsupported.")

    from langchain_openai import ChatOpenAI

    model = os.getenv("MODEL_NAME", "gpt-4o-mini")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "25"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "1"))
    llm = ChatOpenAI(
        model=model,
        temperature=0.2,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
    )
    if json_mode:
        llm = llm.bind(response_format={"type": "json_object"})

    message = (
        f"{prompt}\n\n"
        "Input data as JSON:\n"
        f"{json.dumps(input_data, indent=2, ensure_ascii=False)}"
    )
    response = llm.invoke(message)
    return str(response.content)


def call_llm_json(prompt: str, input_data: dict[str, Any], fallback: Any = None) -> Any:
    try:
        return _extract_json(_openai_chat(prompt, input_data, json_mode=True))
    except Exception:
        return _copy_fallback(fallback)


def call_llm_text(prompt: str, input_data: dict[str, Any], fallback: str = "") -> str:
    try:
        return _openai_chat(prompt, input_data, json_mode=False).strip()
    except Exception:
        return fallback
