#!/usr/bin/env python3
"""Test login to IP-DECT base web interface."""

import argparse
import logging
import os
import sys

import urllib3

from dect.client import DectClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main() -> int:
    parser = argparse.ArgumentParser(description="Login to IP-DECT base web interface")
    parser.add_argument("--url", default="https://localhost:8023", help="Base URL")
    parser.add_argument("--user", default="admin", help="Username")
    parser.add_argument("--password", default="", help="Password")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print response snippets")
    args = parser.parse_args()

    password = args.password or os.environ.get("DECT_PASSWORD", "")
    if not password:
        print("password is required (--password or DECT_PASSWORD env)", file=sys.stderr)
        return 1

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger(__name__)

    client = DectClient(args.url, args.user, password)

    log.info('logging in to %s as "%s" ...', args.url, args.user)
    try:
        client.login()
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    log.info("login successful")

    try:
        admin_resp = client.login_via_admin_redirect()
        log.info(
            "admin redirect: status %s, final url %s",
            admin_resp.status_code,
            admin_resp.url,
        )

        master = client.get_master_config()
        log.info("master config loaded (%d bytes)", len(master))
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1

    if args.verbose:
        print("\n--- master config snippet ---")
        snippet = master.decode("utf-8", errors="replace")
        print(snippet[:800] + ("..." if len(snippet) > 800 else ""))
        print("\n--- admin redirect body ---")
        admin_snippet = admin_resp.text
        print(admin_snippet[:400] + ("..." if len(admin_snippet) > 400 else ""))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
