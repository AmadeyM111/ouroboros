from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from gigachat import GigaChat


DEFAULT_PROMPT = "Привет! Ответь одним коротким предложением."


def env_bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().casefold() not in {"0", "false", "no", "off"}


def build_client(args: argparse.Namespace) -> GigaChat:
    credentials = args.credentials or os.environ.get("GIGACHAT_CREDENTIALS", "")
    user = args.user or os.environ.get("GIGACHAT_USER", "")
    password = args.password or os.environ.get("GIGACHAT_PASSWORD", "")

    if not credentials and not (user and password):
        raise RuntimeError(
            "Set GIGACHAT_CREDENTIALS or GIGACHAT_USER + GIGACHAT_PASSWORD before running."
        )

    kwargs: dict[str, Any] = {
        "scope": args.scope or os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        "model": args.model,
        "verify_ssl_certs": args.verify_ssl_certs,
    }
    if credentials:
        kwargs["credentials"] = credentials
    if user:
        kwargs["user"] = user
    if password:
        kwargs["password"] = password
    if args.base_url:
        kwargs["base_url"] = args.base_url
    if args.ca_bundle_file:
        kwargs["ca_bundle_file"] = args.ca_bundle_file

    return GigaChat(**kwargs)


def extract_text(response: Any) -> str:
    try:
        return response.choices[0].message.content or ""
    except Exception:
        return str(response)


def extract_usage(response: Any) -> str:
    usage = getattr(response, "usage", None)
    if usage is None:
        return ""
    return str(usage)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send one prompt to GigaChat API.")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT, help="Prompt text.")
    parser.add_argument("--model", default=os.environ.get("GIGACHAT_MODEL", "GigaChat"), help="Model name.")
    parser.add_argument("--scope", default=os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"))
    parser.add_argument("--base-url", default=os.environ.get("GIGACHAT_BASE_URL", ""))
    parser.add_argument("--credentials", default="", help="Authorization key. Prefer env GIGACHAT_CREDENTIALS.")
    parser.add_argument("--user", default="", help="Basic auth user. Prefer env GIGACHAT_USER.")
    parser.add_argument("--password", default="", help="Basic auth password. Prefer env GIGACHAT_PASSWORD.")
    parser.add_argument(
        "--ca-bundle-file",
        default=os.environ.get("GIGACHAT_CA_BUNDLE_FILE", ""),
        help="Path to CA bundle file.",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_false",
        dest="verify_ssl_certs",
        default=env_bool("GIGACHAT_VERIFY_SSL_CERTS", True),
        help="Disable TLS certificate verification. Use only for local diagnostics.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with build_client(args) as giga:
            response = giga.chat(args.prompt)
    except Exception as exc:
        print(f"GigaChat request failed: {exc}", file=sys.stderr)
        return 1

    text = extract_text(response)
    usage = extract_usage(response)
    print(text)
    if usage:
        print(f"\nUsage: {usage}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
