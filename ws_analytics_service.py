#!/usr/bin/env python3
"""
Простой WebSocket-сервис-посредник.

Задача сервиса:
1. Получить от клиента JSON с задачей на расчет и аналитику.
2. Отправить эту задачу другому агенту по WebSocket.
3. Вернуть клиенту все сообщения агента.

Запуск:
  python3 ws_analytics_service.py --agent-url ws://127.0.0.1:8765/ws/agent

Пример сообщения от клиента:
  {
    "type": "analytics.request",
    "request_id": "task-001",
    "task": "Посчитай выручку по сегментам и подготовь аналитику",
    "context": {"period": "2026-Q2"},
    "params": {"format": "executive_brief"},
    "timeout_sec": 600
  }
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from typing import Any

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
except ImportError as error:
    websockets = None
    WEBSOCKETS_IMPORT_ERROR = error

    class ConnectionClosed(Exception):  # type: ignore[no-redef]
        code = None
        reason = None
else:
    WEBSOCKETS_IMPORT_ERROR = None


DONE_STATUSES = {"done", "completed", "complete", "success", "finished"}
ERROR_STATUSES = {"error", "failed", "failure", "cancelled", "canceled"}


def now_ms() -> int:
    return int(time.time() * 1000)


def need_websockets() -> Any:
    if websockets is None:
        raise RuntimeError(
            "Нет библиотеки websockets. Установи ее командой: python3 -m pip install websockets"
        ) from WEBSOCKETS_IMPORT_ERROR
    return websockets


async def send_json(socket: Any, message_type: str, request_id: str, **extra_fields: Any) -> None:
    """Отправляет одно JSON-сообщение в WebSocket."""
    message = {
        "type": message_type,
        "request_id": request_id,
        "ts_ms": now_ms(),
        **extra_fields,
    }
    await socket.send(json.dumps(message, ensure_ascii=False))


def read_client_json(raw_message: str | bytes, max_bytes: int) -> dict[str, Any]:
    """Преобразует сообщение клиента в dict и проверяет размер."""
    if isinstance(raw_message, bytes):
        if len(raw_message) > max_bytes:
            raise ValueError("сообщение слишком большое")
        raw_message = raw_message.decode("utf-8")

    if len(raw_message.encode("utf-8")) > max_bytes:
        raise ValueError("сообщение слишком большое")

    message = json.loads(raw_message)
    if not isinstance(message, dict):
        raise ValueError("сообщение должно быть JSON-объектом")
    return message


def make_request(message: dict[str, Any], default_timeout: int) -> dict[str, Any]:
    """Делает из входного JSON нормальную задачу для сервиса."""
    task = message.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("поле task обязательно и должно быть строкой")

    request_id = message.get("request_id") or str(uuid.uuid4())
    if not isinstance(request_id, str):
        raise ValueError("поле request_id должно быть строкой")

    timeout_sec = message.get("timeout_sec", default_timeout)
    if isinstance(timeout_sec, bool) or not isinstance(timeout_sec, int) or timeout_sec <= 0:
        raise ValueError("поле timeout_sec должно быть положительным числом")

    context = message.get("context", {})
    if not isinstance(context, dict):
        raise ValueError("поле context должно быть объектом")

    params = message.get("params", {})
    if not isinstance(params, dict):
        raise ValueError("поле params должно быть объектом")

    return {
        "request_id": request_id,
        "task": task.strip(),
        "context": context,
        "params": params,
        "timeout_sec": timeout_sec,
        "created_ts_ms": now_ms(),
    }


def make_message_for_agent(request: dict[str, Any]) -> dict[str, Any]:
    """Формат задачи, который мы отправляем второму агенту."""
    return {
        "type": "agent.task.request",
        "request_id": request["request_id"],
        "task": request["task"],
        "context": request["context"],
        "params": {
            "mode": "calculation_and_analytics",
            "expected_output": "calculations, assumptions, risks, conclusions, executive summary",
            **request["params"],
        },
        "metadata": {
            "source": "ws_analytics_service",
            "created_ts_ms": request["created_ts_ms"],
        },
    }


def token_from_client(socket: Any) -> str | None:
    """Достает токен клиента из Authorization или X-WS-Token."""
    headers = getattr(socket, "request_headers", None)
    if headers is None:
        request = getattr(socket, "request", None)
        headers = getattr(request, "headers", None)
    if headers is None:
        return None

    auth_header = headers.get("Authorization") or headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return headers.get("X-WS-Token") or headers.get("x-ws-token")


async def connect_websocket(url: str, token: str | None = None) -> Any:
    """Подключается к WebSocket. Поддерживает разные версии библиотеки websockets."""
    module = need_websockets()
    headers = {"Authorization": f"Bearer {token}"} if token else None

    try:
        return await module.connect(url, additional_headers=headers)
    except TypeError:
        return await module.connect(url, extra_headers=headers)


def wrap_agent_message(request_id: str, raw_message: str | bytes) -> dict[str, Any]:
    """Приводит любое сообщение агента к понятному формату для клиента."""
    if isinstance(raw_message, bytes):
        try:
            raw_message = raw_message.decode("utf-8")
        except UnicodeDecodeError:
            return {
                "type": "analytics.agent_event",
                "request_id": request_id,
                "agent_event_type": "binary",
                "data": {"bytes": len(raw_message)},
            }

    try:
        data = json.loads(raw_message)
    except json.JSONDecodeError:
        data = {"text": raw_message}

    if not isinstance(data, dict):
        data = {"value": data}

    return {
        "type": "analytics.agent_event",
        "request_id": request_id,
        "agent_event_type": data.get("type", "agent.event"),
        "data": data,
    }


def is_final_agent_message(event: dict[str, Any]) -> tuple[bool, bool]:
    """
    Возвращает:
      (True, False) если агент успешно закончил,
      (True, True) если агент закончил ошибкой,
      (False, False) если это обычный промежуточный статус.
    """
    data = event.get("data")
    if not isinstance(data, dict):
        return False, False

    event_type = str(data.get("type", "")).lower()
    status = str(data.get("status", "")).lower()

    if event_type in DONE_STATUSES or status in DONE_STATUSES:
        return True, False
    if event_type in ERROR_STATUSES or status in ERROR_STATUSES:
        return True, True
    return False, False


async def send_task_to_agent(client_socket: Any, request: dict[str, Any], args: argparse.Namespace) -> None:
    """Главная логика: отправить задачу агенту и вернуть клиенту ответ."""
    request_id = request["request_id"]
    agent_message = make_message_for_agent(request)

    await send_json(client_socket, "analytics.accepted", request_id, agent_url=args.agent_url)

    try:
        async with await connect_websocket(args.agent_url, args.agent_token) as agent_socket:
            await agent_socket.send(json.dumps(agent_message, ensure_ascii=False))
            await send_json(client_socket, "analytics.sent_to_agent", request_id)

            end_time = time.monotonic() + request["timeout_sec"]

            while True:
                seconds_left = end_time - time.monotonic()
                if seconds_left <= 0:
                    raise TimeoutError(f"агент не ответил за {request['timeout_sec']} секунд")

                raw_agent_message = await asyncio.wait_for(agent_socket.recv(), timeout=seconds_left)
                event = wrap_agent_message(request_id, raw_agent_message)

                await client_socket.send(json.dumps(event, ensure_ascii=False))

                is_final, is_error = is_final_agent_message(event)
                if not is_final:
                    continue

                if is_error:
                    await send_json(
                        client_socket,
                        "analytics.failed",
                        request_id,
                        reason="agent_returned_error",
                        final_event=event,
                    )
                else:
                    await send_json(
                        client_socket,
                        "analytics.completed",
                        request_id,
                        final_event=event,
                    )
                return

    except TimeoutError as error:
        await send_json(client_socket, "analytics.failed", request_id, reason="timeout", detail=str(error))
    except OSError as error:
        await send_json(
            client_socket,
            "analytics.failed",
            request_id,
            reason="agent_connection_error",
            detail=str(error),
        )
    except ConnectionClosed as error:
        await send_json(
            client_socket,
            "analytics.failed",
            request_id,
            reason="connection_closed",
            detail=f"code={error.code} reason={error.reason}",
        )


async def handle_client(client_socket: Any, args: argparse.Namespace) -> None:
    """Обрабатывает одного подключенного клиента."""
    if args.inbound_token and token_from_client(client_socket) != args.inbound_token:
        await client_socket.close(code=4401, reason="unauthorized")
        return

    logging.info("client connected: %s", getattr(client_socket, "remote_address", None))

    try:
        async for raw_message in client_socket:
            request_id = "unknown"
            try:
                message = read_client_json(raw_message, args.max_message_bytes)
                request = make_request(message, args.timeout_sec)
                request_id = request["request_id"]
                await send_task_to_agent(client_socket, request, args)
            except json.JSONDecodeError as error:
                await send_json(
                    client_socket,
                    "analytics.failed",
                    request_id,
                    reason="bad_json",
                    detail=error.msg,
                )
            except ValueError as error:
                await send_json(
                    client_socket,
                    "analytics.failed",
                    request_id,
                    reason="bad_request",
                    detail=str(error),
                )
            except Exception as error:
                logging.exception("unexpected error")
                await send_json(
                    client_socket,
                    "analytics.failed",
                    request_id,
                    reason="internal_error",
                    detail=str(error),
                )
    except ConnectionClosed:
        logging.info("client disconnected")


async def start_server(args: argparse.Namespace) -> None:
    """Запускает WebSocket-сервер и ждет Ctrl+C."""
    module = need_websockets()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_number = getattr(signal, signal_name, None)
        if signal_number is not None:
            loop.add_signal_handler(signal_number, stop_event.set)

    async def client_handler(client_socket: Any, *_unused: Any) -> None:
        await handle_client(client_socket, args)

    async with module.serve(
        client_handler,
        args.listen_host,
        args.listen_port,
        max_size=args.max_message_bytes,
        ping_interval=20,
        ping_timeout=20,
    ):
        logging.info(
            "service is listening: ws://%s:%s -> %s",
            args.listen_host,
            args.listen_port,
            args.agent_url,
        )
        await stop_event.wait()


async def run_demo_client(args: argparse.Namespace) -> None:
    """Мини-клиент для ручной проверки этого сервиса."""
    service_url = f"ws://{args.listen_host}:{args.listen_port}"
    demo_request = {
        "type": "analytics.request",
        "request_id": f"demo-{uuid.uuid4()}",
        "task": args.demo_task,
        "context": {"source": "demo-client"},
        "params": {"format": "executive_brief"},
        "timeout_sec": 120,
    }

    async with await connect_websocket(service_url, args.inbound_token) as socket:
        await socket.send(json.dumps(demo_request, ensure_ascii=False))
        async for raw_message in socket:
            print(raw_message)
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue
            if message.get("type") in {"analytics.completed", "analytics.failed"}:
                return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple WebSocket analytics bridge")

    parser.add_argument("--listen-host", default=os.getenv("WS_ANALYTICS_HOST", "127.0.0.1"))
    parser.add_argument("--listen-port", type=int, default=int(os.getenv("WS_ANALYTICS_PORT", "8787")))
    parser.add_argument("--agent-url", default=os.getenv("AGENT_WS_URL"))

    parser.add_argument("--inbound-token", default=os.getenv("WS_ANALYTICS_TOKEN"))
    parser.add_argument("--agent-token", default=os.getenv("AGENT_WS_TOKEN"))

    parser.add_argument("--timeout-sec", type=int, default=int(os.getenv("WS_ANALYTICS_TIMEOUT_SEC", "600")))
    parser.add_argument(
        "--max-message-bytes",
        type=int,
        default=int(os.getenv("WS_ANALYTICS_MAX_MESSAGE_BYTES", "1048576")),
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))

    parser.add_argument("--demo-client", action="store_true")
    parser.add_argument(
        "--demo-task",
        default="Посчитай выручку по сегментам и подготовь короткую аналитику для руководителя.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.demo_client:
        asyncio.run(run_demo_client(args))
        return 0

    if not args.agent_url:
        print("ERROR: укажи --agent-url или переменную AGENT_WS_URL", file=sys.stderr)
        return 2

    try:
        asyncio.run(start_server(args))
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
