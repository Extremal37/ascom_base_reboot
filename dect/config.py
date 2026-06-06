"""Load reboot configuration from YAML."""

import io
import os

import yaml


class BaseStation(object):
    __slots__ = ("url", "password", "username", "name")

    def __init__(self, url, password, username="admin", name=""):
        self.url = url
        self.password = password
        self.username = username
        self.name = name


class AppConfig(object):
    __slots__ = ("interval_seconds", "bases", "default_username", "default_port")

    def __init__(
        self,
        interval_seconds,
        bases,
        default_username="admin",
        default_port=8023,
    ):
        self.interval_seconds = interval_seconds
        self.bases = bases
        self.default_username = default_username
        self.default_port = default_port


def _require_mapping(data, path):
    if not isinstance(data, dict):
        raise ValueError("{0}: expected mapping".format(path))
    return data


def _resolve_base_url(entry, defaults):
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
    except (TypeError, ValueError):
        raise ValueError("base entry: invalid port {0!r}".format(port))

    if host.startswith("http://") or host.startswith("https://"):
        return host
    return "https://{0}:{1}".format(host, port)


def load_config(path):
    config_path = os.path.abspath(path)
    if not os.path.isfile(config_path):
        raise IOError("config not found: {0}".format(config_path))

    with io.open(config_path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    data = _require_mapping(raw, "root")

    interval = data.get("interval_seconds", 0)
    try:
        interval_seconds = int(interval)
    except (TypeError, ValueError):
        raise ValueError("interval_seconds: invalid value {0!r}".format(interval))
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

    bases = []
    for index, entry in enumerate(bases_raw, start=1):
        item = _require_mapping(entry, "bases[{0}]".format(index))
        password = str(item.get("password", "")).strip()
        if not password:
            raise ValueError("bases[{0}]: password is required".format(index))

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
