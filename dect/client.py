"""HTTP client for Ostec/Ascom IP-DECT web interface."""

from __future__ import annotations

import ssl
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth

DEFAULT_VERIFY_PATH = "/GW-DECT/MASTER/mod_cmd.xml?xsl=dectmaster.xsl"
ADMIN_REDIRECT_PATH = "/GW-DECT/mod_cmd.xml?redirect=/admin.xml?xsl=admin.xsl"
REBOOT_PATH = "/CMD0/mod_cmd.xml?cmd=reset&xsl=reset.xsl&reset=OK"


class LegacyTLSAdapter(HTTPAdapter):
    """Allow TLS 1.0–1.2 and legacy ciphers used by IP-DECT bases."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class DectClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 30.0):
        parsed = urlparse(base_url if "://" in base_url else f"https://{base_url}")
        if not parsed.scheme:
            parsed = parsed._replace(scheme="https")
        self.base_url = parsed.geturl().rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

        self.session = requests.Session()
        self.session.verify = False
        self.session.auth = HTTPDigestAuth(username, password)
        self.session.mount("https://", LegacyTLSAdapter())

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _get(self, path: str) -> requests.Response:
        return self.session.get(self._url(path), timeout=self.timeout)

    @staticmethod
    def _unauthorized(response: requests.Response) -> bool:
        if response.status_code == 401:
            return True
        text = response.text.lower()
        return "401 unauthorized" in text or "not authorized" in text

    @staticmethod
    def _request_failed(response: requests.Response) -> bool:
        if DectClient._unauthorized(response):
            return True
        return response.status_code >= 400

    def login(self) -> None:
        """Verify credentials against a protected GW-DECT endpoint."""
        response = self._get(DEFAULT_VERIFY_PATH)
        if self._unauthorized(response):
            raise RuntimeError(
                f"login failed: invalid credentials (status {response.status_code})"
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"login failed: unexpected status {response.status_code}"
            )
        if not response.content:
            raise RuntimeError("login failed: empty response")

    def login_via_admin_redirect(self) -> requests.Response:
        """Same flow as the web UI: redirect to admin.xml after login."""
        return self._get(ADMIN_REDIRECT_PATH)

    def get_master_config(self) -> bytes:
        response = self._get(DEFAULT_VERIFY_PATH)
        if self._request_failed(response):
            raise RuntimeError(f"not authorized (status {response.status_code})")
        return response.content

    def reboot(self) -> None:
        """Reboot the base station via CMD0/mod_cmd.xml reset command."""
        self.login()
        response = self._get(REBOOT_PATH)
        if self._request_failed(response):
            raise RuntimeError(
                f"reboot failed: unexpected status {response.status_code}"
            )
        if 'reset="true"' not in response.text and "reset='true'" not in response.text:
            snippet = response.text[:300].replace("\n", " ")
            raise RuntimeError(f"reboot failed: unexpected response: {snippet}")
