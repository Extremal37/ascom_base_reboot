"""Load reboot configuration from YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class BaseStation:
    url: str
    password: str
    username: str = "admin"
    name: str = ""


@dataclass(frozen=True)
class AppConfig:
    interval_seconds: int
    bases: list[BaseStation]
    default_username: str = "admin"
    default_port: int = 8023


def _require_mapping(data: Any, path: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping")
    return data


def _resolve_base_url(entry: dict[str, Any], defaults: AppConfig) -> str:
    if "url" in entry:
        url = str(entry["url"]).strip()
        if not url:
            raise ValueError("base entry: url must not be empty")
        return url

    host = str(entry.get("host") or entry.get("ip") or "").strip()
    if not host:
        raise ValueError("base entry: url, host or ip is required")

    port = entry.get("port", defaults.default_port)
    try:
        port = int(port)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"base entry: invalid port {port!r}") from exc

    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"https://{host}:{port}"


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"config not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data = _require_mapping(raw, "root")

    interval = data.get("interval_seconds", 0)
    try:
        interval_seconds = int(interval)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"interval_seconds: invalid value {interval!r}") from exc
    if interval_seconds < 0:
        raise ValueError("interval_seconds must be >= 0")

    default_username = str(data.get("default_username", "admin")).strip() or "admin"
    default_port = int(data.get("default_port", 8023))

    defaults = AppConfig(
        interval_seconds=interval_seconds,
        bases=[],
        default_username=default_username,
        default_port=default_port,
    )

    bases_raw = data.get("bases")
    if not isinstance(bases_raw, list) or not bases_raw:
        raise ValueError("bases: at least one base station is required")

    bases: list[BaseStation] = []
    for index, entry in enumerate(bases_raw, start=1):
        item = _require_mapping(entry, f"bases[{index}]")
        password = str(item.get("password", "")).strip()
        if not password:
            raise ValueError(f"bases[{index}]: password is required")

        username = str(item.get("username", default_username)).strip() or default_username
        name = str(item.get("name", "")).strip()
        url = _resolve_base_url(item, defaults)

        bases.append(
            BaseStation(
                url=url,
                password=password,
                username=username,
                name=name or url,
            )
        )

    return AppConfig(
        interval_seconds=interval_seconds,
        bases=bases,
        default_username=default_username,
        default_port=default_port,
    )
