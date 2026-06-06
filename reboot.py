#!/usr/bin/env python3
"""Reboot IP-DECT bases from config with a delay between each."""

import argparse
import logging
import sys
import time

import urllib3

from dect.client import DectClient
from dect.config import AppConfig, BaseStation, load_config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def reboot_base(base: BaseStation, log: logging.Logger) -> None:
    log.info('[%s] connecting to %s as "%s" ...', base.name, base.url, base.username)
    client = DectClient(base.url, base.username, base.password)
    client.reboot()
    log.info("[%s] reboot command sent successfully", base.name)


def run(config: AppConfig, log: logging.Logger) -> int:
    total = len(config.bases)
    log.info(
        "starting reboot of %d base(s), interval between bases: %d s",
        total,
        config.interval_seconds,
    )

    failed = 0
    for index, base in enumerate(config.bases):
        try:
            reboot_base(base, log)
        except Exception as exc:
            failed += 1
            log.error("[%s] reboot failed: %s", base.name, exc)

        if index < total - 1 and config.interval_seconds > 0:
            log.info("waiting %d s before next base ...", config.interval_seconds)
            time.sleep(config.interval_seconds)

    if failed:
        log.error("finished with %d error(s) out of %d base(s)", failed, total)
        return 1

    log.info("all %d base(s) rebooted successfully", total)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reboot IP-DECT bases sequentially using config file"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to YAML config (default: config.yaml)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger(__name__)

    try:
        config = load_config(args.config)
    except (IOError, ValueError) as exc:
        log.error("%s", exc)
        return 1

    return run(config, log)


if __name__ == "__main__":
    raise SystemExit(main())
