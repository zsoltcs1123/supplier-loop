from __future__ import annotations

import asyncio
import json
import threading
from concurrent.futures import Future
from contextlib import AsyncExitStack
from typing import Protocol

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent

_Job = tuple[str, dict[str, object] | None, Future[object]]


class ToolCaller(Protocol):
    def call_tool(self, name: str, arguments: dict[str, object] | None = None) -> object: ...


class ToolSession(ToolCaller, Protocol):
    def list_tool_names(self) -> list[str]: ...


class McpToolSession:
    def __init__(self, url: str, token: str) -> None:
        self._url = url
        self._token = token
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, name="mcp-session", daemon=True)
        self._ready = threading.Event()
        self._jobs: asyncio.Queue[_Job | None] | None = None
        self._start_error: BaseException | None = None

    def __enter__(self) -> McpToolSession:
        self._thread.start()
        if not self._ready.wait(timeout=60):
            raise RuntimeError("MCP session failed to start")
        if self._start_error is not None:
            raise self._start_error
        return self

    def __exit__(self, *_args: object) -> None:
        if self._jobs is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._jobs.put_nowait, None)
        self._thread.join(timeout=30)

    def list_tool_names(self) -> list[str]:
        names = self._submit("list_tools", None)
        return [str(name) for name in names] if isinstance(names, list) else []

    def call_tool(self, name: str, arguments: dict[str, object] | None = None) -> object:
        return self._submit(name, arguments)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._worker())

    async def _worker(self) -> None:
        self._jobs = asyncio.Queue()
        try:
            async with AsyncExitStack() as stack:
                http = httpx2.AsyncClient(
                    headers={"Authorization": f"Bearer {self._token}"},
                    timeout=httpx2.Timeout(30.0, read=300.0),
                    follow_redirects=True,
                )
                await stack.enter_async_context(http)
                transport = streamable_http_client(self._url, http_client=http)
                client = await stack.enter_async_context(Client(transport))
                self._ready.set()
                while True:
                    job = await self._jobs.get()
                    if job is None:
                        break
                    name, arguments, future = job
                    try:
                        future.set_result(await _run_job(client, name, arguments))
                    except BaseException as exc:
                        future.set_exception(exc)
        except BaseException as exc:
            self._start_error = exc
            self._ready.set()

    def _submit(self, name: str, arguments: dict[str, object] | None) -> object:
        if self._jobs is None:
            raise RuntimeError("MCP session is closed")
        future: Future[object] = Future()
        self._loop.call_soon_threadsafe(self._jobs.put_nowait, (name, arguments, future))
        return future.result(timeout=300)


async def _run_job(
    client: Client,
    name: str,
    arguments: dict[str, object] | None,
) -> object:
    if name == "list_tools":
        result = await client.list_tools()
        return [tool.name for tool in result.tools]
    return payload_from_result(await client.call_tool(name, arguments))


def payload_from_result(result: CallToolResult) -> object:
    if result.is_error:
        raise RuntimeError(_result_error_text(result))
    if result.structured_content is not None:
        return result.structured_content
    texts = [
        block.text for block in result.content if isinstance(block, TextContent) and block.text
    ]
    if not texts:
        return None
    if len(texts) == 1:
        return _parse_possible_json(texts[0])
    return texts


def _result_error_text(result: CallToolResult) -> str:
    texts = [block.text for block in result.content if isinstance(block, TextContent)]
    if texts:
        return " ".join(texts)
    return "MCP tool call failed"


def _parse_possible_json(text: str) -> object:
    try:
        parsed: object = json.loads(text)
    except json.JSONDecodeError:
        return text
    return parsed
